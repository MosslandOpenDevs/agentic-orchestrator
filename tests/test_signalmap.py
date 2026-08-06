"""Tests for the SignalMap export-feed adapter.

The properties pinned here are the ones whose failure is SILENT — a wrong
answer that looks like a right one:

- an epoch change that does not reset the cursor stops ingest forever, while
  every poll still returns 200 with zero new records
- paging on a timestamp when every record shares one either loops or skips
- a mid-publish read splices two releases together and looks like data
- a political-safety record that gets re-summarized is a policy breach that
  produces perfectly plausible output
- a frozen upstream watermark is invisible in every count we hold

Fixtures use the shapes of real records fetched from the live export on
2026-08-06 (release 2026-08-06T140035.659Z).
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

import httpx
import pytest

from agentic_orchestrator.adapters import signalmap as sm
from agentic_orchestrator.adapters.base import SignalData
from agentic_orchestrator.adapters.signalmap import (
    FeedState,
    SignalMapAdapter,
    SignalMapConfig,
    feed_report,
)
from agentic_orchestrator.db.models import Signal
from agentic_orchestrator.signals.aggregator import SignalAggregator

EPOCH = "2026-08-06T14:00:35.659Z"
NEW_EPOCH = "2026-08-07T14:00:35.659Z"
NOW = datetime(2026, 8, 6, 15, 0, 0)


# --------------------------------------------------------------------- helpers


def video_record(
    rec_id="youtube:abc123",
    *,
    updated_at=EPOCH,
    revision=1,
    political_safety=False,
    occurred_at="2026-08-05T21:00:25.000Z",
    topic_id=None,
    entity_ids=None,
    title="트럼프 관세 발표 이후 반도체 공급망이 어떻게 재편되는가",
):
    """A video.summary record shaped like the live export's."""
    return {
        "id": rec_id,
        "schemaVersion": 1,
        "kind": "video.summary",
        "sourceType": "youtube",
        "externalId": rec_id.split(":", 1)[1],
        "source": {
            "name": "뉴스TVCHOSUN",
            "id": "UCWlV3Lz_55UaX4JsMj-z__Q",
            "url": "https://www.youtube.com/channel/UCWlV3Lz_55UaX4JsMj-z__Q",
            "category": "news",
            "channelStance": "right",
        },
        "occurredAt": occurred_at,
        "title": title,
        "summary": "요약 본문",
        "lang": "ko",
        "visibility": "public",
        "policy": {"politicalSafety": political_safety},
        "evidence": {
            "url": f"https://www.youtube.com/watch?v={rec_id.split(':', 1)[1]}",
            "quotes": [{"text": "인용문", "tsSeconds": 0, "url": "https://example.com/t=0"}],
            "claims": [] if political_safety else [{"text": "주장 하나"}],
            "references": [],
        },
        "raw": {
            "topic": {"label": "미국-이란 군사 충돌", "description": "설명"},
            "entities": [{"name": "트럼프", "type": "person"}],
            "events": [{"name": "공격", "dateHint": "2026-06-11"}],
        },
        "canonical": {
            "topicId": topic_id,
            # Nulls are placeholders aligned with the raw list, not ids.
            "entityIds": entity_ids if entity_ids is not None else ["donald-trump", None],
            "eventIds": [None],
        },
        "video": {
            "durationS": 140,
            "viewCount": 152,
            "thumbnailUrl": "https://i.ytimg.com/vi/x/hqdefault.jpg",
            "stance": "observe",
            "stanceReason": "명확한 입장을 드러내지 않음",
        },
        "market": None,
        "observedAt": "2026-08-06T06:30:11.902Z",
        "updatedAt": updated_at,
        "revision": revision,
        "contentHash": "28ea8d58",
    }


def market_record(rec_id="market:2026-08-05-btc-drop", *, occurred_at="2026-08-05T19:35:00.000Z"):
    return {
        "id": rec_id,
        "kind": "market.pulse",
        "sourceType": "market",
        "source": {"name": "SignalMap Pulse", "id": "signalmap-pulse", "url": "https://x/pulse"},
        "occurredAt": occurred_at,
        "title": "비트코인 -1.90% · 5분",
        "summary": "급락 요약",
        "lang": "ko",
        "visibility": "public",
        "policy": {"politicalSafety": False},
        "evidence": {"url": "https://x/pulse/1", "quotes": [], "claims": [], "references": []},
        "raw": {"topic": None, "entities": [], "events": []},
        "canonical": {"topicId": None, "entityIds": [None], "eventIds": []},
        "video": None,
        "market": {"asset": "BTC", "direction": "down", "magnitudePct": 1.9},
        "observedAt": occurred_at,
        "updatedAt": EPOCH,
        "revision": 1,
        "contentHash": "9f87288a",
    }


def manifest(*, epoch=EPOCH, watermark="2026-08-06T06:20:39.000Z", quality="passed"):
    return {
        "schemaVersion": 1,
        "exportVersion": "v1",
        "epoch": epoch,
        "generatedAt": epoch,
        "releaseId": "2026-08-06T140035.659Z",
        "sourceWatermark": watermark,
        "counts": {"signals": 6747, "pulses": 5112},
        "quality": {"status": quality, "notes": []},
    }


def page(records, *, next_cursor=None, has_more=False, verified=True, epoch=EPOCH):
    return {
        "exportVersion": "v1",
        "epoch": epoch,
        "generatedAt": epoch,
        "verified": verified,
        "count": len(records),
        "hasMore": has_more,
        "cursor": {"since": None, "next": next_cursor},
        "records": records,
    }


class FakeClient:
    """Stands in for httpx.AsyncClient; serves scripted manifest + pages.

    Records every ``since``/``limit`` it was asked for, which is what the
    cursor tests actually assert on.
    """

    manifest_body = None
    pages = []
    headers_by_page = []
    requests = []

    def __init__(self, **kwargs):
        FakeClient.init_kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, params=None):
        params = params or {}
        FakeClient.requests.append({"url": url, "params": dict(params)})
        request = httpx.Request("GET", url)

        if url.endswith("/manifest"):
            return httpx.Response(200, json=FakeClient.manifest_body, request=request)

        index = len([r for r in FakeClient.requests if r["url"].endswith("/signals")]) - 1
        if index >= len(FakeClient.pages):
            return httpx.Response(200, json=page([]), request=request)

        headers = {}
        if index < len(FakeClient.headers_by_page):
            headers = FakeClient.headers_by_page[index] or {}
        return httpx.Response(200, json=FakeClient.pages[index], headers=headers, request=request)


def fake_load_config(section):
    """Stand in for utils.config.load_config, serving one `signalmap` section."""

    class _Config:
        @staticmethod
        def get(*keys, default=None):
            return section

    return lambda: _Config()


@pytest.fixture
def fake_client(monkeypatch):
    FakeClient.manifest_body = manifest()
    FakeClient.pages = []
    FakeClient.headers_by_page = []
    FakeClient.requests = []
    FakeClient.init_kwargs = {}
    monkeypatch.setattr("agentic_orchestrator.adapters.signalmap.httpx.AsyncClient", FakeClient)
    return FakeClient


@pytest.fixture
def frozen_now(monkeypatch):
    monkeypatch.setattr("agentic_orchestrator.adapters.signalmap.utcnow", lambda: NOW)
    return NOW


@pytest.fixture
def cfg(tmp_path):
    return SignalMapConfig(
        base_url="https://signalmap.test",
        state_file=str(tmp_path / "signalmap_state.json"),
        page_limit=2,
        max_pages_per_run=5,
        max_age_days=30,
    )


def make_adapter(cfg):
    return SignalMapAdapter(signalmap_config=cfg)


# ------------------------------------------------------------- epoch handling


class TestEpochGate:
    """A new epoch means the publisher recreated its revision ledger.

    Every record comes back at revision 1. A consumer that keeps its old cursor
    (or gates on "incoming revision > stored") never sees another update, and
    reports success the whole time.
    """

    def test_epoch_change_drops_cursor_and_forces_resync(self, cfg, frozen_now):
        adapter = make_adapter(cfg)
        state = FeedState(epoch=EPOCH, cursor=f"{EPOCH}|youtube:xyz", backfilling=False)

        adapter._apply_manifest(manifest(epoch=NEW_EPOCH), state)

        assert state.cursor is None, "a stale cursor against a new epoch skips records forever"
        assert state.backfilling is True
        assert state.epoch == NEW_EPOCH
        assert state.resyncs == 1

    def test_same_epoch_keeps_the_cursor(self, cfg, frozen_now):
        adapter = make_adapter(cfg)
        cursor = f"{EPOCH}|youtube:xyz"
        state = FeedState(epoch=EPOCH, cursor=cursor, backfilling=False)

        adapter._apply_manifest(manifest(epoch=EPOCH), state)

        assert state.cursor == cursor
        assert state.backfilling is False
        assert state.resyncs == 0

    def test_first_sync_records_the_epoch_without_counting_a_resync(self, cfg, frozen_now):
        adapter = make_adapter(cfg)
        state = FeedState()

        adapter._apply_manifest(manifest(), state)

        assert state.epoch == EPOCH
        assert state.resyncs == 0

    async def test_epoch_change_mid_walk_stops_the_run(self, cfg, fake_client, frozen_now):
        """A republish between the manifest read and a page must not be spliced."""
        state = FeedState(epoch=EPOCH, cursor=None)
        state.save(sm.Path(cfg.state_file))

        fake_client.pages = [
            page([video_record("youtube:a")], next_cursor=f"{EPOCH}|youtube:a", has_more=True),
            page([video_record("youtube:b")], has_more=True, epoch=NEW_EPOCH),
        ]

        result = await make_adapter(cfg).fetch()

        assert result.success
        assert [s.external_id for s in result.signals] == ["youtube:a"]
        assert result.metadata["pages_fetched"] == 1
        assert result.metadata["aborted"] == "epoch_changed"

    async def test_a_mid_walk_epoch_change_does_not_throttle_out_the_resync(
        self, cfg, fake_client, frozen_now
    ):
        """The break promises "next run will resync". In steady state a stamped
        success would make that promise false for min_interval_minutes: the
        next tick returns early and never re-reads the manifest, so the epoch
        gate cannot fire."""
        FeedState(
            epoch=EPOCH,
            cursor=None,
            backfilling=False,
            last_success_at=(NOW - timedelta(hours=5)).isoformat(),
        ).save(sm.Path(cfg.state_file))
        fake_client.pages = [page([video_record("youtube:a")], epoch=NEW_EPOCH, has_more=True)]

        await make_adapter(cfg).fetch()

        persisted = FeedState.load(sm.Path(cfg.state_file))
        assert persisted.last_success_at != NOW.isoformat()
        assert persisted.backfilling is True, "a pending resync must not be throttled"


# ------------------------------------------------------------------- paging


class TestCursorPaging:
    async def test_walks_every_page_exactly_once(self, cfg, fake_client, frozen_now):
        """The whole reason the cursor carries an id tiebreak.

        On the first publish all 11,859 records share one ``updatedAt``. Paging
        on the timestamp alone either returns page 1 forever or skips the rest
        of the tie; the adapter must send back exactly the opaque cursor the
        server gave it, never a timestamp it reconstructed.
        """
        records = [video_record(f"youtube:{i}") for i in range(6)]
        fake_client.pages = [
            page(records[0:2], next_cursor=f"{EPOCH}|youtube:1", has_more=True),
            page(records[2:4], next_cursor=f"{EPOCH}|youtube:3", has_more=True),
            page(records[4:6], next_cursor=f"{EPOCH}|youtube:5", has_more=False),
        ]

        result = await make_adapter(cfg).fetch()

        emitted = [s.external_id for s in result.signals]
        assert emitted == [f"youtube:{i}" for i in range(6)]
        assert len(emitted) == len(set(emitted)), "a record was served twice"

        signal_calls = [r for r in fake_client.requests if r["url"].endswith("/signals")]
        assert [c["params"].get("since") for c in signal_calls] == [
            None,
            f"{EPOCH}|youtube:1",
            f"{EPOCH}|youtube:3",
        ]

        persisted = FeedState.load(sm.Path(cfg.state_file))
        assert persisted.cursor == f"{EPOCH}|youtube:5"
        assert persisted.backfilling is False

    async def test_page_budget_bounds_a_run_and_stays_in_backfill(
        self, cfg, fake_client, frozen_now
    ):
        cfg.max_pages_per_run = 2
        fake_client.pages = [
            page([video_record("youtube:a")], next_cursor=f"{EPOCH}|youtube:a", has_more=True),
            page([video_record("youtube:b")], next_cursor=f"{EPOCH}|youtube:b", has_more=True),
            page([video_record("youtube:c")], has_more=False),
        ]

        result = await make_adapter(cfg).fetch()

        assert result.metadata["pages_fetched"] == 2
        assert (
            result.metadata["backfilling"] is True
        ), "an unfinished backfill must not be throttled on the next tick"
        assert FeedState.load(sm.Path(cfg.state_file)).cursor == f"{EPOCH}|youtube:b"

    async def test_has_more_without_an_advancing_cursor_stops_instead_of_spinning(
        self, cfg, fake_client, frozen_now
    ):
        fake_client.pages = [
            page([video_record("youtube:a")], next_cursor=None, has_more=True),
            page([video_record("youtube:b")], next_cursor=None, has_more=True),
        ]

        result = await make_adapter(cfg).fetch()

        assert result.metadata["pages_fetched"] == 1

    async def test_cursor_is_persisted_per_page(self, cfg, fake_client, frozen_now):
        """A timeout or OOM kill mid-walk must resume, not restart."""
        fake_client.pages = [
            page([video_record("youtube:a")], next_cursor=f"{EPOCH}|youtube:a", has_more=True),
            page([video_record("youtube:b")], next_cursor=f"{EPOCH}|youtube:b", has_more=True),
        ]
        cfg.max_pages_per_run = 2

        await make_adapter(cfg).fetch()

        assert FeedState.load(sm.Path(cfg.state_file)).cursor == f"{EPOCH}|youtube:b"

    def test_configured_limit_is_clamped_to_the_published_maximum(self, monkeypatch):
        """The server clamps silently; a request we know will be reduced is one
        we should not write, because it makes the logs lie about page size."""
        monkeypatch.setattr(
            "agentic_orchestrator.adapters.signalmap.load_config",
            fake_load_config({"page_limit": 5000}),
        )

        assert SignalMapConfig.load().page_limit == sm.MAX_PAGE_LIMIT == 2000


# ------------------------------------------------------------ verified guard


class TestMidPublishGuard:
    async def test_unverified_body_aborts_without_advancing_the_cursor(
        self, cfg, fake_client, frozen_now
    ):
        FeedState(epoch=EPOCH, cursor=f"{EPOCH}|youtube:start", backfilling=False).save(
            sm.Path(cfg.state_file)
        )
        fake_client.pages = [
            page([video_record("youtube:a")], next_cursor=f"{EPOCH}|youtube:a", verified=False)
        ]

        result = await make_adapter(cfg).fetch()

        assert result.metadata["unverified"] is True
        assert result.signals == []
        assert FeedState.load(sm.Path(cfg.state_file)).cursor == f"{EPOCH}|youtube:start"

    async def test_unverified_run_does_not_count_as_a_successful_poll(
        self, cfg, fake_client, frozen_now
    ):
        """Otherwise the retry the contract asks for waits out min_interval."""
        fake_client.pages = [page([video_record("youtube:a")], verified=False)]

        await make_adapter(cfg).fetch()

        assert FeedState.load(sm.Path(cfg.state_file)).last_success_at is None

    async def test_header_vetoes_even_when_the_body_claims_verified(
        self, cfg, fake_client, frozen_now
    ):
        fake_client.pages = [page([video_record("youtube:a")], verified=True)]
        fake_client.headers_by_page = [{sm.VERIFIED_HEADER: "false"}]

        result = await make_adapter(cfg).fetch()

        assert result.metadata["unverified"] is True
        assert result.signals == []

    async def test_missing_header_defers_to_the_body(self, cfg, fake_client, frozen_now):
        fake_client.pages = [page([video_record("youtube:a")])]

        result = await make_adapter(cfg).fetch()

        assert result.metadata["unverified"] is False
        assert len(result.signals) == 1


# ---------------------------------------------------------- publisher rules


class TestPublisherRules:
    def test_political_safety_records_are_dropped_by_default(self, cfg, frozen_now):
        adapter = make_adapter(cfg)

        signal, reason = adapter._record_to_signal(video_record(political_safety=True))

        assert signal is None
        assert reason == "political_safety"

    def test_claims_are_never_carried_for_political_safety_records(self, cfg, frozen_now):
        """Even opted in, and even if upstream ever sends claims by mistake."""
        cfg.include_political_safety = True
        adapter = make_adapter(cfg)
        record = video_record(political_safety=True)
        # Upstream ships these empty; simulate a regression on their side.
        record["evidence"]["claims"] = [{"text": "이 채널의 주장"}]

        signal, _ = adapter._record_to_signal(record)

        assert signal is not None
        assert signal.raw_data["claims"] == []
        assert signal.raw_data["claims_withheld"] is True
        assert signal.metadata["political_safety"] is True

    def test_non_political_records_keep_their_claims(self, cfg, frozen_now):
        signal, _ = make_adapter(cfg)._record_to_signal(video_record(political_safety=False))

        assert signal.raw_data["claims"] == [{"text": "주장 하나"}]
        assert signal.raw_data["claims_withheld"] is False

    def test_only_canonical_ids_become_foreign_keys(self, cfg, frozen_now):
        signal, _ = make_adapter(cfg)._record_to_signal(
            video_record(topic_id="us-iran-conflict", entity_ids=["donald-trump", None, "iran"])
        )

        assert signal.metadata["topics"] == ["us-iran-conflict"]
        assert signal.metadata["entities"] == ["donald-trump", "iran"], "nulls are not ids"
        assert signal.raw_data["canonical"]["event_ids"] == []

    def test_raw_labels_are_kept_but_named_unstable(self, cfg, frozen_now):
        signal, _ = make_adapter(cfg)._record_to_signal(video_record())

        assert signal.raw_data["unstable_labels"]["topic"] == "미국-이란 군사 충돌"
        assert "topic" not in signal.raw_data["canonical"]
        assert signal.metadata["topics"] == [], "a raw label must never pose as a canonical id"

    def test_stance_is_stored_flagged_as_axis_relative(self, cfg, frozen_now):
        signal, _ = make_adapter(cfg)._record_to_signal(video_record())

        video = signal.raw_data["video"]
        assert video["stance"] == "observe"
        assert (
            video["stance_axis_required"] is True
        ), "stance is a position on a cluster axis; without axis.statement it is not comparable"


# ----------------------------------------------------------- record mapping


class TestRecordMapping:
    def test_collected_at_is_the_upstream_event_time(self, cfg, frozen_now):
        """A backfill must not present six months of video as collected today."""
        signal, _ = make_adapter(cfg)._record_to_signal(
            video_record(occurred_at="2026-08-01T10:00:00.000Z")
        )

        assert signal.collected_at == datetime(2026, 8, 1, 10, 0, 0)

    def test_records_past_the_age_window_are_walked_but_not_stored(self, cfg, frozen_now):
        signal, reason = make_adapter(cfg)._record_to_signal(
            video_record(occurred_at="2026-01-01T10:00:00.000Z")
        )

        assert signal is None
        assert reason == "too_old"

    def test_kinds_not_configured_are_dropped(self, cfg, frozen_now):
        cfg.kinds = ["video.summary"]

        signal, reason = make_adapter(cfg)._record_to_signal(market_record())

        assert signal is None
        assert reason == "kind_filtered"

    def test_non_public_records_are_dropped(self, cfg, frozen_now):
        record = video_record()
        record["visibility"] = "private"

        signal, reason = make_adapter(cfg)._record_to_signal(record)

        assert signal is None
        assert reason == "not_public"

    def test_a_null_visibility_is_treated_as_public(self, cfg, frozen_now):
        """This publisher ships nulls as placeholders throughout; a get()
        default would only fire for an absent key and drop every record."""
        record = video_record()
        record["visibility"] = None

        signal, reason = make_adapter(cfg)._record_to_signal(record)

        assert signal is not None, reason

    def test_the_epoch_travels_with_the_revision(self, cfg, frozen_now):
        signal, _ = make_adapter(cfg)._record_to_signal(video_record(revision=3), EPOCH)

        assert signal.metadata["epoch"] == EPOCH
        assert signal.raw_data["epoch"] == EPOCH
        assert signal.metadata["revision"] == 3

    def test_market_pulse_titles_get_a_date_discriminator(self, cfg, frozen_now):
        """The title "비트코인 -1.90% · 5분" repeats across hundreds of pulses.

        Without a discriminator the aggregator's Jaccard dedup collapses
        distinct market events into one.
        """
        signal, _ = make_adapter(cfg)._record_to_signal(market_record())

        assert signal.title == "비트코인 -1.90% · 5분 (2026-08-05)"
        assert signal.category == "crypto"

    def test_video_category_maps_from_the_channel(self, cfg, frozen_now):
        record = video_record()
        record["source"]["category"] = "economy"

        signal, _ = make_adapter(cfg)._record_to_signal(record)

        assert signal.category == "finance"

    def test_unknown_channel_category_falls_back_to_other(self, cfg, frozen_now):
        record = video_record()
        record["source"]["category"] = "vlog"

        signal, _ = make_adapter(cfg)._record_to_signal(record)

        assert signal.category == "other"

    def test_malformed_records_do_not_take_the_run_down(self, cfg, frozen_now):
        adapter = make_adapter(cfg)

        assert adapter._record_to_signal("not a dict") == (None, "malformed")
        assert adapter._record_to_signal({"kind": "video.summary", "title": ""})[1] in (
            "no_title",
            "kind_filtered",
        )

    async def test_drop_reasons_are_reported_not_swallowed(self, cfg, fake_client, frozen_now):
        fake_client.pages = [
            page(
                [
                    video_record("youtube:keep"),
                    video_record("youtube:pol", political_safety=True),
                    video_record("youtube:old", occurred_at="2025-01-01T00:00:00.000Z"),
                ]
            )
        ]

        result = await make_adapter(cfg).fetch()

        assert result.metadata["records_scanned"] == 3
        assert result.metadata["records_emitted"] == 1
        assert result.metadata["dropped"] == {"political_safety": 1, "too_old": 1}


# --------------------------------------------------------------- identity


class TestStableIdentity:
    def test_external_id_survives_an_upstream_title_edit(self):
        """The revision ledger is worthless if a retitle forks the row."""
        before = SignalData(
            source="signalmap",
            category="crypto",
            title="Original title",
            url="https://x/1",
            external_id="youtube:abc",
        )
        after = SignalData(
            source="signalmap",
            category="crypto",
            title="Edited title",
            url="https://x/1",
            external_id="youtube:abc",
        )

        assert before.id == after.id

    def test_content_hashing_is_unchanged_for_sources_without_ids(self):
        signal = SignalData(source="rss", category="crypto", title="T", url="https://x/1")
        same = SignalData(source="rss", category="crypto", title="T", url="https://x/1")
        different = SignalData(source="rss", category="crypto", title="T2", url="https://x/1")

        assert signal.id == same.id
        assert signal.id != different.id

    def test_external_id_is_namespaced_by_source(self):
        a = SignalData(source="signalmap", category="c", title="t", external_id="1")
        b = SignalData(source="other", category="c", title="t", external_id="1")

        assert a.id != b.id

    def test_dedup_uses_external_id_when_present(self):
        # __new__ rather than __init__: _deduplicate touches no instance state,
        # and SignalAggregator() would construct all twelve adapters (and read
        # config.yaml) to exercise one pure function.
        aggregator = SignalAggregator.__new__(SignalAggregator)
        signals = [
            SignalData(
                source="signalmap",
                category="crypto",
                title="비트코인 급락에 대한 심층 분석 리포트 하나",
                external_id="youtube:abc",
            ),
            SignalData(
                source="signalmap",
                category="crypto",
                title="완전히 다른 제목이지만 같은 레코드입니다 실제로",
                external_id="youtube:abc",
            ),
        ]

        deduped = aggregator._deduplicate(signals)

        assert len(deduped) == 1

    def test_dedup_keeps_the_newer_revision_of_a_collapsed_record(self):
        """Keying on a publisher id collapses two *versions* of one record;
        first-seen-wins would keep the staler one."""
        aggregator = SignalAggregator.__new__(SignalAggregator)
        old = SignalData(
            source="signalmap",
            category="crypto",
            title="비트코인 급락에 대한 심층 분석 리포트 하나",
            external_id="youtube:abc",
            metadata={"revision": 1},
        )
        new = SignalData(
            source="signalmap",
            category="crypto",
            title="비트코인 급락에 대한 심층 분석 리포트 하나",
            external_id="youtube:abc",
            metadata={"revision": 2},
        )

        deduped = aggregator._deduplicate([old, new])

        assert len(deduped) == 1
        assert deduped[0].metadata["revision"] == 2

    def test_dedup_without_revisions_still_keeps_the_first(self):
        """Every existing adapter must keep its exact behaviour."""
        aggregator = SignalAggregator.__new__(SignalAggregator)
        first = SignalData(
            source="rss", category="crypto", title="Bitcoin surges past all records today"
        )
        second = SignalData(
            source="rss", category="crypto", title="Bitcoin surges past all records today"
        )

        deduped = aggregator._deduplicate([first, second])

        assert deduped == [first]


class TestRevisionRefresh:
    def _stored(self, revision, *, epoch=EPOCH):
        return Signal(
            id="abc",
            source="signalmap",
            category="crypto",
            title="Old title",
            summary="Old summary",
            url="https://x/old",
            raw_data={"revision": revision, "epoch": epoch},
            topics=["old-topic"],
        )

    def _incoming(self, revision, *, topics=None, entities=None, epoch=EPOCH):
        return SignalData(
            source="signalmap",
            category="crypto",
            title="New title",
            summary="New summary",
            url="https://x/new",
            raw_data={"revision": revision, "epoch": epoch},
            metadata={
                "revision": revision,
                "epoch": epoch,
                "topics": topics if topics is not None else ["new-topic"],
                "entities": entities if entities is not None else ["e1"],
            },
            external_id="youtube:abc",
        )

    def test_higher_revision_refreshes_the_row(self):
        stored = self._stored(1)

        assert SignalAggregator._apply_revision_update(stored, self._incoming(2)) is True
        assert stored.title == "New title"
        assert stored.topics == ["new-topic"]
        assert stored.entities == ["e1"]

    def test_equal_or_lower_revision_is_ignored(self):
        stored = self._stored(3)

        assert SignalAggregator._apply_revision_update(stored, self._incoming(3)) is False
        assert SignalAggregator._apply_revision_update(stored, self._incoming(2)) is False
        assert stored.title == "Old title"

    def test_sources_without_a_revision_keep_first_write_wins(self):
        stored = self._stored(1)
        incoming = SignalData(source="rss", category="crypto", title="New", metadata={})

        assert SignalAggregator._apply_revision_update(stored, incoming) is False
        assert stored.title == "Old title"

    def test_a_revision_without_a_canonical_topic_does_not_erase_one(self):
        """Canonical links only ever gain ground."""
        stored = self._stored(1)

        SignalAggregator._apply_revision_update(stored, self._incoming(2, topics=[]))

        assert stored.topics == ["old-topic"]

    def test_a_new_epoch_makes_a_lower_revision_win(self):
        """The failure the module docstring warns about, one level down.

        A recreated ledger sends every record back at revision 1. Comparing
        that against a stored 5 refuses the update — and every update after it,
        forever, while each poll keeps returning 200 and looking healthy. The
        cursor resync rewinds where we read from; it does nothing about
        revisions already stored.
        """
        stored = self._stored(5, epoch=EPOCH)

        applied = SignalAggregator._apply_revision_update(
            stored, self._incoming(1, epoch=NEW_EPOCH)
        )

        assert applied is True
        assert stored.title == "New title"

    def test_the_same_epoch_still_compares_revisions_strictly(self):
        stored = self._stored(5, epoch=EPOCH)

        incoming = self._incoming(1, epoch=EPOCH)

        assert SignalAggregator._apply_revision_update(stored, incoming) is False
        assert stored.title == "Old title"


# -------------------------------------------------------------- watermark


class TestWatermark:
    def test_age_is_measured_from_the_watermark_value_not_from_when_we_noticed(
        self, cfg, frozen_now
    ):
        """Otherwise deleting the state file buys a dead upstream a fresh
        silent window, and a first sync against an already-frozen feed looks
        new."""
        adapter = make_adapter(cfg)
        state = FeedState(
            epoch=EPOCH,
            source_watermark="2026-08-05T06:00:00.000Z",
            watermark_changed_at=(NOW - timedelta(hours=40)).isoformat(),
        )

        adapter._apply_manifest(manifest(watermark="2026-08-06T06:00:00.000Z"), state)

        assert state.source_watermark == "2026-08-06T06:00:00.000Z"
        # NOW is 2026-08-06T15:00, the watermark says 06:00 -> 9 hours old,
        # regardless of watermark_changed_at having just been rewritten.
        assert state.watermark_age_hours(NOW) == 9.0

    def test_a_first_sync_against_a_frozen_feed_still_warns(self, cfg, frozen_now, caplog):
        adapter = make_adapter(cfg)
        state = FeedState()  # nothing seen before

        with caplog.at_level(logging.WARNING):
            adapter._apply_manifest(manifest(watermark="2026-08-01T06:00:00.000Z"), state)

        assert any("sourceWatermark is" in r.message for r in caplog.records)

    def test_an_advanced_but_still_old_watermark_warns(self, cfg, frozen_now, caplog):
        adapter = make_adapter(cfg)
        state = FeedState(epoch=EPOCH, source_watermark="2026-07-20T06:00:00.000Z")

        with caplog.at_level(logging.WARNING):
            adapter._apply_manifest(manifest(watermark="2026-08-01T06:00:00.000Z"), state)

        assert any("sourceWatermark is" in r.message for r in caplog.records)

    def test_frozen_watermark_warns(self, cfg, frozen_now, caplog):
        """The failure no record count can show: it keeps publishing, stops collecting."""
        adapter = make_adapter(cfg)
        watermark = "2026-08-04T06:00:00.000Z"
        state = FeedState(
            epoch=EPOCH,
            source_watermark=watermark,
            watermark_changed_at=(NOW - timedelta(hours=40)).isoformat(),
        )

        with caplog.at_level(logging.WARNING):
            adapter._apply_manifest(manifest(watermark=watermark), state)

        assert any("sourceWatermark is" in r.message for r in caplog.records)

    def test_fresh_watermark_does_not_warn(self, cfg, frozen_now, caplog):
        adapter = make_adapter(cfg)
        watermark = "2026-08-06T06:00:00.000Z"
        state = FeedState(
            epoch=EPOCH,
            source_watermark=watermark,
            watermark_changed_at=(NOW - timedelta(hours=3)).isoformat(),
        )

        with caplog.at_level(logging.WARNING):
            adapter._apply_manifest(manifest(watermark=watermark), state)

        assert not any("sourceWatermark" in r.message for r in caplog.records)

    def test_degraded_quality_is_reported_but_not_fatal(self, cfg, frozen_now, caplog):
        adapter = make_adapter(cfg)
        state = FeedState(epoch=EPOCH)

        with caplog.at_level(logging.WARNING):
            adapter._apply_manifest(manifest(quality="degraded"), state)

        assert any("quality=degraded" in r.message for r in caplog.records)


# ------------------------------------------------------------------ state


class TestFeedStatePersistence:
    def test_roundtrip(self, tmp_path):
        path = tmp_path / "nested" / "state.json"
        state = FeedState(epoch=EPOCH, cursor="c", records_emitted=7, backfilling=False)

        state.save(path)

        assert FeedState.load(path) == state

    def test_missing_file_starts_a_fresh_sync(self, tmp_path):
        state = FeedState.load(tmp_path / "absent.json")

        assert state.epoch is None
        assert state.backfilling is True, "no cursor means resync, never skip"

    def test_corrupt_file_starts_a_fresh_sync_instead_of_wedging(self, tmp_path, caplog):
        path = tmp_path / "state.json"
        path.write_text("{not json", encoding="utf-8")

        with caplog.at_level(logging.WARNING):
            state = FeedState.load(path)

        assert state == FeedState()

    def test_unknown_keys_from_a_future_version_are_ignored(self, tmp_path):
        path = tmp_path / "state.json"
        path.write_text(json.dumps({"epoch": EPOCH, "invented_later": 1}), encoding="utf-8")

        assert FeedState.load(path).epoch == EPOCH

    def test_save_is_atomic(self, tmp_path):
        """A half-written cursor is worse than an old one."""
        path = tmp_path / "state.json"
        FeedState(epoch=EPOCH, cursor="one").save(path)
        FeedState(epoch=EPOCH, cursor="two").save(path)

        assert FeedState.load(path).cursor == "two"
        assert not list(tmp_path.glob("*.tmp"))


# --------------------------------------------------------------- throttling


class TestThrottling:
    async def test_recent_success_skips_the_poll(self, cfg, fake_client, frozen_now):
        FeedState(
            epoch=EPOCH,
            backfilling=False,
            last_success_at=(NOW - timedelta(minutes=30)).isoformat(),
        ).save(sm.Path(cfg.state_file))

        result = await make_adapter(cfg).fetch()

        assert result.success
        assert result.metadata["skipped"] == "throttled"
        assert fake_client.requests == [], "a throttled run must not touch the network"

    async def test_an_unfinished_backfill_ignores_the_throttle(self, cfg, fake_client, frozen_now):
        FeedState(
            epoch=EPOCH,
            backfilling=True,
            last_success_at=(NOW - timedelta(minutes=1)).isoformat(),
        ).save(sm.Path(cfg.state_file))
        fake_client.pages = [page([video_record("youtube:a")])]

        result = await make_adapter(cfg).fetch()

        assert result.metadata.get("skipped") is None
        assert len(result.signals) == 1

    async def test_elapsed_interval_allows_the_poll(self, cfg, fake_client, frozen_now):
        FeedState(
            epoch=EPOCH,
            backfilling=False,
            last_success_at=(NOW - timedelta(hours=5)).isoformat(),
        ).save(sm.Path(cfg.state_file))
        fake_client.pages = [page([video_record("youtube:a")])]

        result = await make_adapter(cfg).fetch()

        assert result.metadata.get("skipped") is None

    async def test_disabled_adapter_makes_no_requests(self, cfg, fake_client):
        cfg.enabled = False

        result = await make_adapter(cfg).fetch()

        assert result.success
        assert result.metadata["skipped"] == "disabled"
        assert fake_client.requests == []


# ------------------------------------------------------------------ errors


class TestProgressIsNeverSilentlyLost:
    """The cursor may only ever sit past records the aggregator actually got.

    Every failure here is a *silent* skip if handled wrongly: the run reports
    something, the next run resumes past the gap, and `cursor.next` being
    exclusive means those records are never offered again.
    """

    async def test_records_walked_before_a_mid_walk_failure_are_still_returned(
        self, cfg, fake_client, frozen_now, monkeypatch
    ):
        """Page 1 converted and advanced the cursor; page 2 then 503s.

        Discarding page 1 here loses those records for good.
        """
        page_one = page(
            [video_record("youtube:a"), video_record("youtube:b")],
            next_cursor=f"{EPOCH}|youtube:b",
            has_more=True,
        )

        class HalfFailing(FakeClient):
            async def get(self, url, params=None):
                FakeClient.requests.append({"url": url, "params": dict(params or {})})
                request = httpx.Request("GET", url)
                if url.endswith("/manifest"):
                    return httpx.Response(200, json=manifest(), request=request)
                signal_calls = [r for r in FakeClient.requests if r["url"].endswith("/signals")]
                if len(signal_calls) == 1:
                    return httpx.Response(200, json=page_one, request=request)
                return httpx.Response(503, json={"error": "down"}, request=request)

        monkeypatch.setattr(
            "agentic_orchestrator.adapters.signalmap.httpx.AsyncClient", HalfFailing
        )

        result = await make_adapter(cfg).fetch()

        assert [s.external_id for s in result.signals] == ["youtube:a", "youtube:b"]
        assert result.success is True, "collect_all only stores signals from successful results"
        assert result.error, "a partial run still reports what went wrong"
        assert result.metadata["partial"] is True
        assert FeedState.load(sm.Path(cfg.state_file)).cursor == f"{EPOCH}|youtube:b"

    async def test_cancellation_rolls_the_cursor_back(
        self, cfg, fake_client, frozen_now, monkeypatch
    ):
        """asyncio.wait_for's expiry arrives as CancelledError, which derives
        from BaseException — `except Exception` cannot see it, and nothing is
        returned, so the cursor must not stay advanced."""
        page_one = page(
            [video_record("youtube:a")], next_cursor=f"{EPOCH}|youtube:a", has_more=True
        )

        class CancelOnSecondPage(FakeClient):
            async def get(self, url, params=None):
                FakeClient.requests.append({"url": url, "params": dict(params or {})})
                request = httpx.Request("GET", url)
                if url.endswith("/manifest"):
                    return httpx.Response(200, json=manifest(), request=request)
                signal_calls = [r for r in FakeClient.requests if r["url"].endswith("/signals")]
                if len(signal_calls) == 1:
                    return httpx.Response(200, json=page_one, request=request)
                raise asyncio.CancelledError()

        monkeypatch.setattr(
            "agentic_orchestrator.adapters.signalmap.httpx.AsyncClient", CancelOnSecondPage
        )
        FeedState(epoch=EPOCH, cursor="entry-cursor").save(sm.Path(cfg.state_file))

        with pytest.raises(asyncio.CancelledError):
            await make_adapter(cfg).fetch()

        persisted = FeedState.load(sm.Path(cfg.state_file))
        assert persisted.cursor == "entry-cursor", "re-reading is cheap; skipping is permanent"
        assert "cancelled" in (persisted.last_error or "")

    async def test_cancellation_after_an_epoch_reset_does_not_restore_the_dead_cursor(
        self, cfg, fake_client, frozen_now, monkeypatch
    ):
        """The rollback target is taken after the epoch gate, not before.

        A cursor from a ledger that no longer exists is worse than no cursor:
        the resync would resume from a dead generation's position.
        """

        class CancelOnFirstPage(FakeClient):
            async def get(self, url, params=None):
                request = httpx.Request("GET", url)
                if url.endswith("/manifest"):
                    return httpx.Response(200, json=manifest(epoch=NEW_EPOCH), request=request)
                raise asyncio.CancelledError()

        monkeypatch.setattr(
            "agentic_orchestrator.adapters.signalmap.httpx.AsyncClient", CancelOnFirstPage
        )
        FeedState(epoch=EPOCH, cursor=f"{EPOCH}|youtube:old").save(sm.Path(cfg.state_file))

        with pytest.raises(asyncio.CancelledError):
            await make_adapter(cfg).fetch()

        persisted = FeedState.load(sm.Path(cfg.state_file))
        assert persisted.cursor is None, "the epoch reset must survive the rollback"
        assert persisted.epoch == NEW_EPOCH

    async def test_a_non_advancing_cursor_is_recorded_not_reported_as_success(
        self, cfg, fake_client, frozen_now
    ):
        """Breaking stops the in-run spin. Without recording it, every tick
        re-reads the same page forever and /status keeps saying healthy."""
        fake_client.pages = [page([video_record("youtube:a")], next_cursor=None, has_more=True)]

        result = await make_adapter(cfg).fetch()

        assert result.metadata["aborted"] == "cursor_stalled"
        persisted = FeedState.load(sm.Path(cfg.state_file))
        assert persisted.last_success_at is None
        assert "cursor_stalled" in (persisted.last_error or "")

    async def test_an_empty_page_with_more_pending_stays_in_backfill(
        self, cfg, fake_client, frozen_now
    ):
        """A sparse region of the ledger is a pending tail, not the end — the
        same state as running out of page budget."""
        FeedState(epoch=EPOCH, backfilling=False).save(sm.Path(cfg.state_file))
        fake_client.pages = [page([], next_cursor=f"{EPOCH}|gap", has_more=True)]

        result = await make_adapter(cfg).fetch()

        assert result.metadata["backfilling"] is True

    async def test_a_future_last_success_does_not_wedge_the_feed(
        self, cfg, fake_client, frozen_now
    ):
        """A timestamp ahead of now is a clock that moved, not a poll that
        happened; treating it as one stops collection for the whole skew."""
        FeedState(
            epoch=EPOCH,
            backfilling=False,
            last_success_at=(NOW + timedelta(days=2)).isoformat(),
        ).save(sm.Path(cfg.state_file))
        fake_client.pages = [page([video_record("youtube:a")])]

        result = await make_adapter(cfg).fetch()

        assert result.metadata.get("skipped") is None
        assert len(result.signals) == 1


class TestFailureHandling:
    async def test_http_failure_reports_without_advancing_the_cursor(
        self, cfg, fake_client, frozen_now, monkeypatch
    ):
        FeedState(epoch=EPOCH, cursor="keep-me").save(sm.Path(cfg.state_file))

        class Failing(FakeClient):
            async def get(self, url, params=None):
                request = httpx.Request("GET", url)
                return httpx.Response(503, json={"error": "down"}, request=request)

        monkeypatch.setattr("agentic_orchestrator.adapters.signalmap.httpx.AsyncClient", Failing)

        result = await make_adapter(cfg).fetch()

        assert result.success is False
        assert result.error
        assert FeedState.load(sm.Path(cfg.state_file)).cursor == "keep-me"

    async def test_failure_is_recorded_for_the_status_endpoint(
        self, cfg, fake_client, frozen_now, monkeypatch
    ):
        class Failing(FakeClient):
            async def get(self, url, params=None):
                raise httpx.ConnectError("no route to host")

        monkeypatch.setattr("agentic_orchestrator.adapters.signalmap.httpx.AsyncClient", Failing)

        await make_adapter(cfg).fetch()

        assert "ConnectError" in (FeedState.load(sm.Path(cfg.state_file)).last_error or "")


# ------------------------------------------------------------------ report


class TestFeedReport:
    @pytest.fixture(autouse=True)
    def _reset(self):
        sm.reset_report_cache()
        yield
        sm.reset_report_cache()

    def test_never_synced_is_unknown_not_healthy(self, cfg, tmp_path, monkeypatch, frozen_now):
        monkeypatch.setattr(sm, "_report_config", cfg)

        report = feed_report(tmp_path / "absent.json")

        assert report["status"] == "unknown"
        assert report["reason"] == "never synced"

    def test_healthy_when_the_watermark_is_moving(self, cfg, tmp_path, monkeypatch, frozen_now):
        monkeypatch.setattr(sm, "_report_config", cfg)
        path = tmp_path / "state.json"
        FeedState(
            epoch=EPOCH,
            source_watermark="2026-08-06T06:00:00.000Z",
            watermark_changed_at=(NOW - timedelta(hours=2)).isoformat(),
            last_success_at=NOW.isoformat(),
        ).save(path)

        assert feed_report(path)["status"] == "healthy"

    def test_frozen_watermark_degrades(self, cfg, tmp_path, monkeypatch, frozen_now):
        monkeypatch.setattr(sm, "_report_config", cfg)
        path = tmp_path / "state.json"
        FeedState(
            epoch=EPOCH,
            source_watermark="2026-08-01T06:00:00.000Z",
            watermark_changed_at=(NOW - timedelta(hours=48)).isoformat(),
        ).save(path)

        report = feed_report(path)

        assert report["status"] == "degraded"
        assert "watermark" in report["reason"]

    def test_disabled_is_not_degraded(self, cfg, tmp_path, monkeypatch):
        cfg.enabled = False
        monkeypatch.setattr(sm, "_report_config", cfg)

        assert feed_report(tmp_path / "x.json")["status"] == "disabled"

    def test_report_makes_no_network_call(self, cfg, tmp_path, monkeypatch, frozen_now):
        """GET /status is public and hot; it must stay config + local file."""
        monkeypatch.setattr(sm, "_report_config", cfg)

        def explode(*args, **kwargs):
            raise AssertionError("feed_report must not open an HTTP client")

        monkeypatch.setattr("agentic_orchestrator.adapters.signalmap.httpx.AsyncClient", explode)

        assert feed_report(tmp_path / "x.json")["status"] in ("unknown", "healthy", "degraded")


# ------------------------------------------------------------------ config


class TestConfigLoading:
    def test_defaults_are_conservative(self):
        cfg = SignalMapConfig()

        assert cfg.include_political_safety is False
        assert cfg.max_pages_per_run >= 1
        assert cfg.page_limit <= sm.MAX_PAGE_LIMIT

    def test_env_overrides_the_base_url(self, monkeypatch):
        monkeypatch.setenv("SIGNALMAP_BASE_URL", "https://staging.example/")
        monkeypatch.setattr(
            "agentic_orchestrator.adapters.signalmap.load_config",
            fake_load_config({"enabled": True}),
        )

        assert SignalMapConfig.load().base_url == "https://staging.example"

    def test_a_malformed_section_falls_back_instead_of_raising(self, monkeypatch):
        """A hand-edited config.yaml must not take SignalAggregator construction down."""
        monkeypatch.setattr(
            "agentic_orchestrator.adapters.signalmap.load_config",
            fake_load_config(["not", "a", "map"]),
        )

        assert SignalMapConfig.load() == SignalMapConfig()

    def test_bearer_token_only_sent_when_configured(self, monkeypatch):
        monkeypatch.delenv("SIGNALMAP_EXPORT_TOKEN", raising=False)
        assert SignalMapAdapter._auth_headers() == {}

        monkeypatch.setenv("SIGNALMAP_EXPORT_TOKEN", "secret")
        assert SignalMapAdapter._auth_headers() == {"Authorization": "Bearer secret"}


class TestAdapterRegistration:
    def test_the_aggregator_collects_from_signalmap(self, monkeypatch):
        monkeypatch.setattr(
            "agentic_orchestrator.adapters.signalmap.SignalMapConfig.load",
            classmethod(lambda cls: SignalMapConfig()),
        )

        names = [a.name for a in SignalAggregator()._default_adapters()]

        assert "signalmap" in names

    def test_adapter_exposes_its_kinds_for_the_adapters_endpoint(self, cfg):
        adapter = make_adapter(cfg)

        assert adapter.TRACKED_KINDS == cfg.kinds

"""Signal identity must not follow volatile numbers in titles.

Recurring status-report signals (GitHub trending, Coingecko movers, onchain
TVL) embed values that move every poll — star counts, percentages, prices.
SignalData.id is a content hash of the title unless external_id is set, so a
moving number made every 30-minute tick a "new" signal and the cross-run dedup
in ``_save_to_db`` never matched. Measured over 7 days of production
(2026-08-14): coingecko 88.2%, onchain 94.8%, github 23.8% of rows were the
same subject re-inserted (deepseek-ai/deepseek-harness alone: 36 rows/day).

These tests pin the fix: such signals carry a synthesized ``external_id`` —
subject (+ direction) + UTC day bucket — so identity is stable within a day
while the volatile numbers stay in the title as information.
"""

from datetime import datetime, timedelta, timezone

import pytest

import agentic_orchestrator.adapters.base as base_module
from agentic_orchestrator.adapters.base import SignalData, recurring_key
from agentic_orchestrator.adapters.coingecko import CoingeckoAdapter
from agentic_orchestrator.adapters.github_events import GitHubEventsAdapter
from agentic_orchestrator.adapters.onchain import OnChainAdapter

DAY1 = datetime(2026, 8, 14, 3, 0, 0, tzinfo=timezone.utc)
DAY1_LATER = datetime(2026, 8, 14, 21, 30, 0, tzinfo=timezone.utc)
DAY2 = datetime(2026, 8, 15, 3, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def clock(monkeypatch):
    """Freeze recurring_key's clock; tests move it explicitly."""

    state = {"now": DAY1}
    monkeypatch.setattr(base_module, "utcnow", lambda: state["now"])
    return state


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class _FakeClient:
    """Stands in for httpx.AsyncClient; serves one payload per URL fragment."""

    def __init__(self, routes):
        self._routes = routes

    def __call__(self, *args, **kwargs):  # httpx.AsyncClient(timeout=...) call
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, **kwargs):
        for fragment, payload in self._routes.items():
            if fragment in url:
                return _FakeResponse(payload)
        raise AssertionError(f"unrouted url in test: {url}")


def _patch_client(monkeypatch, module_path, routes):
    monkeypatch.setattr(f"{module_path}.httpx.AsyncClient", _FakeClient(routes))


class TestRecurringKey:
    def test_appends_utc_day_bucket(self, clock):
        assert recurring_key("trending", "a/b") == "trending:a/b:2026-08-14"

    def test_same_day_same_key(self, clock):
        first = recurring_key("mover", "bitcoin", "up")
        clock["now"] = DAY1_LATER
        assert recurring_key("mover", "bitcoin", "up") == first

    def test_day_rollover_changes_key(self, clock):
        first = recurring_key("mover", "bitcoin", "up")
        clock["now"] = DAY2
        assert recurring_key("mover", "bitcoin", "up") != first


class TestGitHubIdentity:
    def _trending_payload(self, stars):
        return {
            "search/repositories": {
                "items": [
                    {
                        "full_name": "deepseek-ai/deepseek-harness",
                        "stargazers_count": stars,
                        "forks_count": 10,
                        "html_url": "https://github.com/deepseek-ai/deepseek-harness",
                        "description": "harness",
                        "language": "Python",
                        "topics": [],
                        "created_at": "2026-08-10T00:00:00Z",
                    }
                ]
            }
        }

    async def _fetch_trending(self, monkeypatch, stars):
        _patch_client(
            monkeypatch,
            "agentic_orchestrator.adapters.github_events",
            self._trending_payload(stars),
        )
        adapter = GitHubEventsAdapter(github_token="t")
        return await adapter._fetch_trending_repos()

    @pytest.mark.asyncio
    async def test_star_count_change_keeps_identity(self, clock, monkeypatch):
        # Production reality: 22822 -> 36557 stars over one day = 36 rows.
        (first,) = await self._fetch_trending(monkeypatch, 22822)
        (later,) = await self._fetch_trending(monkeypatch, 36557)
        assert first.title != later.title  # numbers still informative
        assert first.id == later.id  # identity no longer follows them

    @pytest.mark.asyncio
    async def test_day_rollover_is_a_new_signal(self, clock, monkeypatch):
        (first,) = await self._fetch_trending(monkeypatch, 100)
        clock["now"] = DAY2
        (next_day,) = await self._fetch_trending(monkeypatch, 100)
        assert first.id != next_day.id

    @pytest.mark.asyncio
    async def test_release_identity_is_repo_tag_without_day(self, clock, monkeypatch):
        published = (datetime.now().astimezone() - timedelta(days=1)).isoformat()
        routes = {
            "releases": [
                {
                    "tag_name": "v1.2.3",
                    "published_at": published,
                    "html_url": "https://github.com/o/r/releases/v1.2.3",
                    "body": "notes",
                    "name": "v1.2.3",
                    "prerelease": False,
                }
            ]
        }
        _patch_client(monkeypatch, "agentic_orchestrator.adapters.github_events", routes)
        adapter = GitHubEventsAdapter(github_token="t")

        client = _FakeClient(routes)
        (first,) = await adapter._fetch_repo_releases(client, "o/r")
        clock["now"] = DAY2
        (later,) = await adapter._fetch_repo_releases(client, "o/r")
        assert first.external_id == "release:o/r:v1.2.3"
        assert first.id == later.id  # one-time event: no day bucket

    @pytest.mark.asyncio
    async def test_topic_repos_keyed_per_repo_and_topic(self, clock, monkeypatch):
        repo = {
            "full_name": "zenml-io/kitaru",
            "stargazers_count": 5,
            "html_url": "https://github.com/zenml-io/kitaru",
            "description": "d",
            "updated_at": "2026-08-14T00:00:00Z",
        }
        _patch_client(
            monkeypatch,
            "agentic_orchestrator.adapters.github_events",
            {"search/repositories": {"items": [repo]}},
        )
        adapter = GitHubEventsAdapter(github_token="t")
        signals = await adapter._fetch_topic_repos()
        # Same repo may legitimately appear under several topics; each
        # (repo, topic) pair must be a distinct, stable identity.
        ids = [s.id for s in signals]
        assert len(ids) == len(set(ids))
        assert all(s.external_id for s in signals)


class TestCoingeckoIdentity:
    def _markets_payload(self, change_24h):
        return {
            "coins/markets": [
                {
                    "id": "audiera",
                    "symbol": "beat",
                    "name": "Audiera",
                    "price_change_percentage_24h": change_24h,
                    "market_cap": 200_000_000,
                    "market_cap_rank": 120,
                    "current_price": 1.23,
                    "total_volume": 10_000_000,  # below spike threshold
                    "price_change_percentage_7d_in_currency": 5.0,
                }
            ]
        }

    async def _fetch_movers(self, monkeypatch, change_24h):
        _patch_client(
            monkeypatch,
            "agentic_orchestrator.adapters.coingecko",
            self._markets_payload(change_24h),
        )
        return await CoingeckoAdapter(api_key="")._fetch_top_movers()

    @pytest.mark.asyncio
    async def test_percentage_change_keeps_identity(self, clock, monkeypatch):
        # Production reality: "Audiera (BEAT) N% in 24h" x65 in one week.
        (first,) = await self._fetch_movers(monkeypatch, 12.0)
        (later,) = await self._fetch_movers(monkeypatch, 15.3)
        assert first.id == later.id

    @pytest.mark.asyncio
    async def test_direction_flip_is_a_new_signal(self, clock, monkeypatch):
        (gainer,) = await self._fetch_movers(monkeypatch, 12.0)
        (loser,) = await self._fetch_movers(monkeypatch, -12.0)
        assert gainer.id != loser.id

    @pytest.mark.asyncio
    async def test_trending_coin_recurs_daily(self, clock, monkeypatch):
        payload = {
            "search/trending": {
                "coins": [
                    {
                        "item": {
                            "id": "moss-coin",
                            "name": "Moss Coin",
                            "symbol": "moc",
                            "market_cap_rank": 500,
                            "price_btc": 0.00000012,
                        }
                    }
                ],
                "nfts": [],
            }
        }
        _patch_client(monkeypatch, "agentic_orchestrator.adapters.coingecko", payload)
        adapter = CoingeckoAdapter(api_key="")
        (first,) = await adapter._fetch_trending()
        (same_day,) = await adapter._fetch_trending()
        clock["now"] = DAY2
        (next_day,) = await adapter._fetch_trending()
        assert first.id == same_day.id
        assert first.id != next_day.id  # still trending tomorrow = new signal


class TestOnchainIdentity:
    @pytest.mark.asyncio
    async def test_chain_stats_tvl_change_keeps_identity(self, clock, monkeypatch):
        # Production reality: "Chain Stats: Ethereum TVL $N" x60 in one week.
        async def fetch(tvl):
            _patch_client(
                monkeypatch,
                "agentic_orchestrator.adapters.onchain",
                {"v2/chains": [{"name": "Ethereum", "tvl": tvl, "gecko_id": "ethereum"}]},
            )
            return await OnChainAdapter()._fetch_chain_stats()

        (first,) = await fetch(62.1e9)
        (later,) = await fetch(63.8e9)
        assert first.id == later.id

    @pytest.mark.asyncio
    async def test_dex_volume_direction_split(self, clock, monkeypatch):
        async def fetch(change_1d):
            _patch_client(
                monkeypatch,
                "agentic_orchestrator.adapters.onchain",
                {
                    "overview/dexs": {
                        "protocols": [
                            {
                                "name": "SushiSwap",
                                "slug": "sushiswap",
                                "total24h": 60_000_000,
                                "total7d": 400_000_000,
                                "change_1d": change_1d,
                                "change_7d": 1.0,
                                "chains": ["Ethereum"],
                            }
                        ]
                    }
                },
            )
            return await OnChainAdapter()._fetch_dex_volume()

        (up_a,) = await fetch(25.0)
        (up_b,) = await fetch(30.0)
        (down,) = await fetch(-25.0)
        assert up_a.id == up_b.id
        assert up_a.id != down.id

    @pytest.mark.asyncio
    async def test_whale_identity_is_the_transaction_hash(self, clock, monkeypatch):
        tx = {
            "blockchain": "ethereum",
            "symbol": "eth",
            "amount": 1000,
            "amount_usd": 3_000_000,
            "hash": "0xabc123",
            "timestamp": 1765000000,
            "from": {"owner_type": "unknown"},
            "to": {"owner_type": "exchange"},
        }
        _patch_client(
            monkeypatch,
            "agentic_orchestrator.adapters.onchain",
            {"transactions": {"transactions": [tx]}},
        )
        adapter = OnChainAdapter(whale_alert_api_key="k")
        (first,) = await adapter._fetch_whale_transactions()
        clock["now"] = DAY2
        (later,) = await adapter._fetch_whale_transactions()
        assert first.external_id == "whale:ethereum:0xabc123"
        assert first.id == later.id  # one-time event: no day bucket


class TestExistingIdentityUnchanged:
    """Sources without external_id must keep their content-hash identity."""

    def test_title_hash_signals_still_split_on_title(self):
        a = SignalData(source="rss", category="ai", title="A story", url="https://x/1")
        b = SignalData(source="rss", category="ai", title="Another story", url="https://x/1")
        assert a.id != b.id

    def test_external_id_still_wins_over_title(self):
        a = SignalData(source="signalmap", category="ai", title="v1", external_id="rec-1")
        b = SignalData(source="signalmap", category="ai", title="v2 edited", external_id="rec-1")
        assert a.id == b.id


class TestSaveDedupEndToEnd:
    """The production save path drops the churned re-insert."""

    @pytest.mark.asyncio
    async def test_churned_title_is_one_row(self, clock, tmp_path, monkeypatch):
        import agentic_orchestrator.signals.aggregator as aggregator_module
        from agentic_orchestrator.db import connection as db_connection
        from agentic_orchestrator.db.connection import Database
        from agentic_orchestrator.db.models import Signal
        from agentic_orchestrator.signals.aggregator import SignalAggregator

        db = Database(f"sqlite:///{tmp_path / 'orchestrator.db'}")
        db.create_tables()
        monkeypatch.setattr(db_connection, "db", db)
        monkeypatch.setattr(aggregator_module, "db", db)

        aggregator = SignalAggregator(adapters=[])

        def trending(stars):
            return SignalData(
                source="github",
                category="dev",
                external_id=recurring_key("trending", "deepseek-ai/deepseek-harness"),
                title=f"Trending: deepseek-ai/deepseek-harness ({stars} stars)",
                url="https://github.com/deepseek-ai/deepseek-harness",
            )

        await aggregator._save_to_db([trending(22822)])
        await aggregator._save_to_db([trending(36557)])  # next tick, more stars

        session = db.get_session()
        rows = session.query(Signal).all()
        session.close()
        assert len(rows) == 1
        assert "22822" in rows[0].title  # first sighting wins; not re-churned

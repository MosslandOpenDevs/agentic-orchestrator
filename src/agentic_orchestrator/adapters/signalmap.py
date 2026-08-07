"""
SignalMap adapter for signal collection.

Consumes SignalMap's export layer (``/api/signal/v1/*``) — the canonical
entity/topic/event store that also feeds MOSS Media, Alpha and the map itself.
AO is one consumer among several, which is why the endpoints are named
``signal`` rather than ``ao``; the older ``/api/ao/v1/*`` paths still serve the
same bytes but new integrations use the ``signal`` prefix.

Five properties of that feed drive nearly every decision in this file:

1. **Records are revised in place.** A record keeps its ``id`` and bumps
   ``revision`` when a canonical topic/entity is attached to it later. Identity
   must therefore follow the publisher's id, not our content hash — see
   ``SignalData.external_id``.
2. **The cursor needs its tiebreak.** The wire cursor is
   ``"<updatedAt>|<id>"``. On the 2026-08-06 first publish all 11,859 records
   carry the *same* ``updatedAt`` (the epoch), so paging on the timestamp alone
   either loops forever or skips records. Verified against the live feed:
   ``cursor.next`` is exclusive and paging by it walks the corpus exactly once.
3. **A new epoch invalidates stored revisions.** The revision ledger is
   per-server; when the publisher re-creates it, every record comes back at
   ``revision: 1``. A consumer gating writes on "incoming revision > stored
   revision" would then ignore every future update forever. So an epoch change
   drops the cursor and forces a full resync.
4. **Data files are written before the manifest.** A read that lands mid-publish
   can splice two releases together; the feed reports that as
   ``verified: false`` (also the ``x-signalmap-export-verified`` header). We
   abort the run without advancing the cursor and retry on the next tick.
5. **`sourceWatermark` is the only liveness signal that matters.** It is the
   newest upstream item's timestamp. ``generatedAt`` moves on every republish
   whether or not collection is working, and record counts do not fall when a
   collector dies — they simply stop rising, which is indistinguishable from a
   quiet day. A frozen watermark is not.

Three rules from the publisher are enforced here rather than trusted downstream:

- **Only canonical IDs are foreign keys.** ``canonical.topicId`` /
  ``entityIds`` / ``eventIds`` are stable; cluster ids in ``clusters.json`` are
  not (they change on re-clustering) and raw labels never were. Raw labels are
  still carried, under a key that says so.
- **Political-safety records are not reconstructed.** Records with
  ``policy.politicalSafety`` (left/right news channels) ship with
  ``evidence.claims`` empty *by design*. Re-deriving positions from the
  title/summary is exactly what that flag forbids, and AO's whole pipeline is
  "hand text to a model and ask what it means" — so by default these records
  are dropped at ingest, where the rule is one line instead of an invariant
  spread over trends, debates and plans.
- **`stance` is a position on a cluster's axis, not a like/dislike.** It means
  nothing without ``axis.statement`` from ``clusters.json``, and nothing
  aggregable at all when ``axis.comparable`` is false. It is stored as an
  opaque label flagged ``axis_required``; nothing in AO may sum it.

See ``docs/signalmap.md`` for the full consumer contract.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ..timeutil import utcnow
from ..utils.config import load_config
from .base import AdapterConfig, AdapterResult, BaseAdapter, SignalData

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://signalmap.moss.land"
DEFAULT_PATH_PREFIX = "/api/signal/v1"

# Publisher-documented ceiling. Asking for more is clamped server-side, so this
# is a local guard against writing a request we know will be silently reduced.
MAX_PAGE_LIMIT = 2000

VERIFIED_HEADER = "x-signalmap-export-verified"

KIND_VIDEO = "video.summary"
KIND_MARKET = "market.pulse"

# SignalMap channel categories -> AO signal categories. AO's `category` column
# is a free-form string (db.models.SignalCategory is advisory — existing
# adapters already emit "web3"/"social"), but keeping to the established set
# means the dashboard filters and category counts stay meaningful.
_CATEGORY_MAP = {
    "crypto": "crypto",
    "blockchain": "crypto",
    "economy": "finance",
    "finance": "finance",
    "market": "finance",
    "tech": "dev",
    "it": "dev",
    "ai": "ai",
    "security": "security",
    "news": "other",
    "politics": "other",
}


def _parse_iso(value: Any) -> Optional[datetime]:
    """Parse an ISO-8601 instant into a *naive* UTC datetime.

    Naive on purpose: the SQLAlchemy DateTime columns store naive UTC (see
    ``timeutil.utcnow``), and mixing the two raises on every comparison.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


@dataclass
class SignalMapConfig:
    """Consumer-side settings, from config.yaml's top-level ``signalmap`` section."""

    enabled: bool = True
    base_url: str = DEFAULT_BASE_URL
    path_prefix: str = DEFAULT_PATH_PREFIX
    # Which record kinds are turned into AO signals. Filtered client-side on
    # purpose: the API's `kind` parameter would give each kind its own cursor,
    # and two cursors over one revision ledger is two things to keep in sync
    # and two ways to lose a record. One cursor walks everything; this list
    # decides what is kept.
    kinds: List[str] = field(default_factory=lambda: [KIND_VIDEO, KIND_MARKET])
    page_limit: int = 1000
    # Bounds one run. The backfill spreads across runs instead of pulling 19 MB
    # in a single 30-minute signal tick.
    max_pages_per_run: int = 3
    # Records older than this are walked (the cursor must pass over them to
    # reach the tail) but not stored. The corpus reaches back months; AO's
    # trend window is hours.
    max_age_days: int = 30
    include_political_safety: bool = False
    # The publisher republishes a few times a day; polling harder than this
    # only buys empty responses. Ignored while backfilling.
    min_interval_minutes: int = 240
    # daily-ingest runs 06:00 KST. A watermark that has not moved in more than
    # a day plus slack means upstream collection stopped.
    watermark_stale_hours: int = 30
    state_file: str = "data/signalmap_state.json"

    @classmethod
    def load(cls) -> "SignalMapConfig":
        """Read config.yaml's ``signalmap`` section, falling back to defaults."""
        defaults = cls()
        try:
            raw = load_config().get("signalmap", default=None)
        except Exception as exc:  # pragma: no cover - config is optional
            logger.warning(f"Could not read signalmap config, using defaults: {exc}")
            return defaults

        if not raw:
            return defaults
        if not isinstance(raw, dict):
            logger.warning(
                "`signalmap` in config.yaml must be a mapping, got "
                f"{type(raw).__name__}; using defaults"
            )
            return defaults

        kinds = raw.get("kinds", defaults.kinds)
        if not isinstance(kinds, list) or not all(isinstance(k, str) for k in kinds):
            logger.warning("`signalmap.kinds` must be a list of strings; using defaults")
            kinds = defaults.kinds

        def _int(key: str, fallback: int, minimum: int = 1) -> int:
            value = raw.get(key, fallback)
            try:
                return max(minimum, int(value))
            except (TypeError, ValueError):
                logger.warning(f"`signalmap.{key}` must be an integer; using {fallback}")
                return fallback

        base_url = os.environ.get("SIGNALMAP_BASE_URL") or raw.get("base_url", defaults.base_url)

        return cls(
            enabled=bool(raw.get("enabled", defaults.enabled)),
            base_url=str(base_url).rstrip("/"),
            path_prefix=str(raw.get("path_prefix", defaults.path_prefix)),
            kinds=list(kinds),
            page_limit=min(MAX_PAGE_LIMIT, _int("page_limit", defaults.page_limit)),
            max_pages_per_run=_int("max_pages_per_run", defaults.max_pages_per_run),
            max_age_days=_int("max_age_days", defaults.max_age_days, minimum=0),
            include_political_safety=bool(
                raw.get("include_political_safety", defaults.include_political_safety)
            ),
            min_interval_minutes=_int(
                "min_interval_minutes", defaults.min_interval_minutes, minimum=0
            ),
            watermark_stale_hours=_int(
                "watermark_stale_hours", defaults.watermark_stale_hours, minimum=1
            ),
            state_file=str(raw.get("state_file", defaults.state_file)),
        )


@dataclass
class FeedState:
    """What must survive a process restart for the cursor to mean anything.

    A file rather than a table: the scheduler runs each task as a fresh process
    against a SQLite file that has been restored from backup more than once, and
    a lost cursor must degrade to "resync", never to "silently skip". Losing
    this file does exactly that — the next run rediscovers the epoch, walks from
    the beginning, and the publisher's ids make the re-ingest idempotent.
    """

    epoch: Optional[str] = None
    cursor: Optional[str] = None
    release_id: Optional[str] = None
    source_watermark: Optional[str] = None
    watermark_changed_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_error: Optional[str] = None
    backfilling: bool = True
    records_emitted: int = 0
    resyncs: int = 0

    @classmethod
    def load(cls, path: Path) -> "FeedState":
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return cls()
        except (OSError, ValueError) as exc:
            # A corrupt state file must not wedge collection: resyncing costs a
            # few minutes of paging, refusing to run costs the feed entirely.
            logger.warning(f"SignalMap state file unreadable ({exc}); starting a fresh sync")
            return cls()

        if not isinstance(data, dict):
            logger.warning("SignalMap state file is not an object; starting a fresh sync")
            return cls()

        # Unknown keys are dropped rather than passed through: a state file
        # written by a newer build must not crash an older one on rollback.
        known = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self, path: Path) -> None:
        """Write atomically; a half-written cursor is worse than an old one."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as handle:
                json.dump(asdict(self), handle, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
        except OSError as exc:
            logger.warning(f"Could not persist SignalMap state to {path}: {exc}")

    def watermark_age_hours(self, now: Optional[datetime] = None) -> Optional[float]:
        """How stale the upstream watermark is, measured from its own value.

        Measured from the timestamp itself, not from when we first saw it
        change. "When we noticed" has two holes the value does not: losing this
        state file would reset the clock and buy a dead upstream a fresh silent
        window, and a first sync against an already-frozen feed would look new.
        ``watermark_changed_at`` is kept for diagnostics and as a fallback when
        the value will not parse.
        """
        observed = _parse_iso(self.source_watermark) or _parse_iso(self.watermark_changed_at)
        if observed is None:
            return None
        return max(0.0, ((now or utcnow()) - observed).total_seconds() / 3600.0)


class SignalMapAdapter(BaseAdapter):
    """Pulls SignalMap's published signal feed into AO's signal table."""

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        signalmap_config: Optional[SignalMapConfig] = None,
    ):
        # 180s because one run pages up to max_pages_per_run x page_limit
        # records over the network, and fetch_with_retry wraps the whole fetch()
        # in this timeout.
        #
        # max_retries=1 is honest rather than pessimistic: fetch_with_retry only
        # re-runs when fetch() *raises*, and this fetch() returns its partial
        # results instead of raising (throwing them away would skip them for
        # good — the cursor is already past them). A higher number here would
        # read as "we retry" while retrying nothing. The real retry is the next
        # scheduler tick, which a failed run does not throttle because it never
        # stamps last_success_at.
        super().__init__(config or AdapterConfig(timeout=180, max_retries=1))
        self.cfg = signalmap_config or SignalMapConfig.load()
        # Named for the TRACKED_* convention GET /adapters uses to describe what
        # an adapter watches; configurable here, so it is set per instance.
        self.TRACKED_KINDS = list(self.cfg.kinds)

    @property
    def name(self) -> str:
        return "signalmap"

    @property
    def state_path(self) -> Path:
        return Path(self.cfg.state_file)

    # ------------------------------------------------------------------ HTTP

    def _url(self, path: str) -> str:
        return f"{self.cfg.base_url}{self.cfg.path_prefix}{path}"

    @staticmethod
    def _auth_headers() -> Dict[str, str]:
        """Bearer token, only if one is configured.

        The export is open today (the publisher has not set its export token)
        because it carries nothing that is not already public on the site. When
        that changes, setting SIGNALMAP_EXPORT_TOKEN is the whole migration.
        """
        token = os.environ.get("SIGNALMAP_EXPORT_TOKEN", "").strip()
        return {"Authorization": f"Bearer {token}"} if token else {}

    @staticmethod
    def _is_verified(response: httpx.Response, payload: Dict[str, Any]) -> bool:
        """False when the response may splice two releases together.

        Both channels are consulted and either one may veto: the body field is
        what the current export emits, the header is what the contract names.
        """
        body_ok = payload.get("verified", True) is not False
        header = response.headers.get(VERIFIED_HEADER)
        header_ok = True
        if header is not None:
            header_ok = header.strip().lower() not in ("false", "0", "no")
        return body_ok and header_ok

    async def _get_json(
        self, client: httpx.AsyncClient, path: str, **params: Any
    ) -> httpx.Response:
        response = await client.get(self._url(path), params=params or None)
        response.raise_for_status()
        return response

    # ------------------------------------------------------------------ fetch

    async def fetch(self) -> AdapterResult:
        start_time = time.time()
        cfg = self.cfg

        if not cfg.enabled:
            return AdapterResult(
                adapter_name=self.name,
                success=True,
                signals=[],
                duration_ms=(time.time() - start_time) * 1000,
                metadata={"skipped": "disabled"},
            )

        state = FeedState.load(self.state_path)

        throttled_for = self._throttle_remaining_minutes(state)
        if throttled_for is not None:
            return AdapterResult(
                adapter_name=self.name,
                success=True,
                signals=[],
                duration_ms=(time.time() - start_time) * 1000,
                metadata={
                    "skipped": "throttled",
                    "next_poll_in_minutes": round(throttled_for),
                },
            )

        signals: List[SignalData] = []
        dropped: Dict[str, int] = {}
        pages = 0
        scanned = 0
        # Why an abort *reason* rather than a bare flag: three different mid-walk
        # stops all need the same two effects — do not stamp last_success_at (so
        # the retry is the next tick, not four hours later) and report what
        # happened. Only one of them originally got them, and the other two were
        # the ones that could commit zero pages.
        abort_reason: Optional[str] = None
        # The cursor this run started from. Restored if the run is cancelled, so
        # a cancelled walk never leaves the cursor past records it never handed
        # back. Re-reading pages is cheap and idempotent (the publisher's record
        # ids make re-ingest a no-op); skipping them is permanent.
        entry_cursor = state.cursor

        try:
            async with httpx.AsyncClient(
                timeout=60,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Agentic-Orchestrator/1.0 (+https://ao.moss.land)",
                    **self._auth_headers(),
                },
                follow_redirects=True,
            ) as client:
                manifest = (await self._get_json(client, "/manifest")).json()
                self._apply_manifest(manifest, state)
                # Re-taken AFTER the epoch gate. If the manifest just reset the
                # cursor, the pre-manifest value belongs to a ledger that no
                # longer exists, and rolling back to it on cancellation would
                # resume a resync from a dead generation's position.
                entry_cursor = state.cursor

                while pages < cfg.max_pages_per_run:
                    response = await self._get_json(
                        client,
                        "/signals",
                        limit=cfg.page_limit,
                        **({"since": state.cursor} if state.cursor else {}),
                    )
                    payload = response.json()

                    if not self._is_verified(response, payload):
                        # Do NOT advance the cursor: the page may hold records
                        # from two different releases.
                        logger.warning(
                            "SignalMap export reported unverified mid-publish state; "
                            "abandoning this run without advancing the cursor"
                        )
                        abort_reason = "unverified"
                        break

                    page_epoch = payload.get("epoch")
                    if page_epoch and state.epoch and page_epoch != state.epoch:
                        # A republish landed between our manifest read and this
                        # page. Stop and let the next run's manifest read resync
                        # — which requires that the next run actually happen, so
                        # this counts as an abort and forces backfill mode. In
                        # steady state a stamped success here would throttle the
                        # promised resync out for min_interval_minutes.
                        logger.warning(
                            f"SignalMap epoch changed mid-walk ({state.epoch} -> {page_epoch}); "
                            "stopping this run, next run will resync"
                        )
                        abort_reason = "epoch_changed"
                        state.backfilling = True
                        break

                    records = payload.get("records") or []
                    scanned += len(records)
                    for record in records:
                        signal, reason = self._record_to_signal(record, state.epoch)
                        if signal is not None:
                            signals.append(signal)
                        elif reason:
                            dropped[reason] = dropped.get(reason, 0) + 1

                    pages += 1
                    next_cursor = (payload.get("cursor") or {}).get("next")
                    has_more = bool(payload.get("hasMore"))

                    if next_cursor and next_cursor != state.cursor:
                        state.cursor = next_cursor
                        # Persisted per page — but only ever past records this
                        # run will hand back (conversion happens above), so an
                        # advanced cursor and a returned record set stay in step.
                        state.save(self.state_path)
                    elif has_more:
                        # hasMore with no advancing cursor. Breaking stops the
                        # in-run spin; recording it as an abort stops the
                        # cross-run one, where every tick re-reads the same page
                        # and /status keeps saying healthy. Deliberately NOT
                        # deriving a cursor from the last record: a derived
                        # cursor that disagrees with the server's ordering would
                        # skip records, and re-reading a page costs nothing
                        # because re-ingest is idempotent.
                        logger.warning(
                            "SignalMap reported hasMore with no advancing cursor; stopping. "
                            "The walk is not making progress and will retry from the same cursor."
                        )
                        abort_reason = "cursor_stalled"
                        break

                    if not has_more:
                        if state.backfilling:
                            logger.info(
                                f"SignalMap backfill complete at epoch {state.epoch} "
                                f"({state.records_emitted + len(signals)} records stored)"
                            )
                        state.backfilling = False
                        break

                    if not records:
                        # An empty page with hasMore still set: a sparse region
                        # of the ledger, not the end. Same pending-tail state as
                        # running out of page budget, so the same flag.
                        state.backfilling = True
                        break
                else:
                    # Ran out of page budget with more to fetch: stay in
                    # backfill mode so the next tick is not throttled.
                    state.backfilling = True

        except asyncio.CancelledError:
            # fetch_with_retry wraps this whole coroutine in asyncio.wait_for,
            # and its expiry arrives as CancelledError — which derives from
            # BaseException, NOT Exception, so the handler below can never see
            # it. Without this arm the one failure the per-page cursor exists to
            # survive is the one that leaves no trace: no last_error, /status
            # still healthy, and the cursor sitting past records that were
            # walked but never handed to the aggregator.
            state.cursor = entry_cursor
            state.last_error = "cancelled mid-walk (adapter timeout); cursor rolled back"
            state.save(self.state_path)
            logger.warning(
                "SignalMap fetch cancelled mid-walk; cursor rolled back to "
                f"{entry_cursor!r} so the next run re-reads rather than skips"
            )
            raise

        except Exception as exc:
            state.last_error = f"{type(exc).__name__}: {exc}"
            state.records_emitted += len(signals)
            state.save(self.state_path)
            logger.warning(f"SignalMap fetch failed: {state.last_error}")
            return AdapterResult(
                adapter_name=self.name,
                # Hand back the pages already walked. The cursor is already past
                # them on disk, and cursor.next is exclusive, so discarding them
                # here would skip them permanently — the exact thing FeedState's
                # docstring promises cannot happen. Same shape as RSSAdapter:
                # partial success carries an error alongside its signals.
                success=bool(signals),
                signals=signals,
                error=state.last_error,
                duration_ms=(time.time() - start_time) * 1000,
                metadata={
                    "pages_fetched": pages,
                    "records_scanned": scanned,
                    "records_emitted": len(signals),
                    "partial": bool(signals),
                },
            )

        state.records_emitted += len(signals)
        if abort_reason is None:
            state.last_error = None
            # An aborted walk is not a successful poll; leaving the old
            # timestamp lets the next tick retry instead of waiting out
            # min_interval_minutes.
            state.last_success_at = utcnow().isoformat()
        else:
            state.last_error = f"aborted mid-walk: {abort_reason}"
        state.save(self.state_path)

        return AdapterResult(
            adapter_name=self.name,
            success=True,
            signals=signals,
            duration_ms=(time.time() - start_time) * 1000,
            metadata={
                "epoch": state.epoch,
                "release_id": state.release_id,
                "pages_fetched": pages,
                "records_scanned": scanned,
                "records_emitted": len(signals),
                "dropped": dropped,
                "backfilling": state.backfilling,
                "aborted": abort_reason,
                "unverified": abort_reason == "unverified",
                "source_watermark": state.source_watermark,
                "watermark_age_hours": state.watermark_age_hours(),
            },
        )

    def _throttle_remaining_minutes(self, state: FeedState) -> Optional[float]:
        """Minutes still to wait, or None when the run should proceed."""
        if state.backfilling or not self.cfg.min_interval_minutes:
            return None
        last = _parse_iso(state.last_success_at)
        if last is None:
            return None
        elapsed = (utcnow() - last).total_seconds() / 60.0
        if elapsed < 0:
            # A timestamp in the future is a clock that moved, not a poll that
            # happened. Without this the wait becomes interval + skew and the
            # feed stops collecting for as long as the skew lasts, reporting
            # success on every tick.
            logger.warning(
                f"SignalMap last_success_at is {-elapsed:.0f} minutes in the future "
                "(clock skew?); polling anyway"
            )
            return None
        remaining = self.cfg.min_interval_minutes - elapsed
        return remaining if remaining > 0 else None

    def _apply_manifest(self, manifest: Dict[str, Any], state: FeedState) -> None:
        """Fold the manifest into state: epoch gate, watermark, quality."""
        epoch = manifest.get("epoch")

        if epoch and state.epoch and epoch != state.epoch:
            logger.warning(
                f"SignalMap epoch changed ({state.epoch} -> {epoch}): dropping the stored cursor "
                "and resyncing from the start. Stored revisions no longer compare — the "
                "publisher's revision ledger was recreated and every record is back at 1."
            )
            state.cursor = None
            state.backfilling = True
            state.resyncs += 1
        elif epoch and not state.epoch:
            logger.info(f"SignalMap first sync against epoch {epoch}")

        if epoch:
            state.epoch = epoch
        release_id = manifest.get("releaseId")
        if release_id:
            state.release_id = release_id

        watermark = manifest.get("sourceWatermark")
        if watermark and watermark != state.source_watermark:
            state.source_watermark = watermark
            state.watermark_changed_at = utcnow().isoformat()

        # Checked whether or not the value moved: a watermark that advanced but
        # is still three days old is just as dead as one that did not move.
        age = state.watermark_age_hours()
        if age is not None and age > self.cfg.watermark_stale_hours:
            # The one failure no count can show: generatedAt keeps moving,
            # record totals keep looking healthy, and nothing new is being
            # collected upstream.
            logger.warning(
                f"SignalMap sourceWatermark is {age:.1f}h old (threshold "
                f"{self.cfg.watermark_stale_hours}h, watermark={state.source_watermark}). "
                "The upstream collector may have stopped; record counts will not show this."
            )

        quality = manifest.get("quality") or {}
        status = quality.get("status")
        if status and status != "passed":
            notes = quality.get("notes") or []
            logger.warning(
                f"SignalMap release {state.release_id} published with quality={status}; "
                f"joins may be incomplete. Notes: {notes}"
            )

    # ------------------------------------------------------------- conversion

    def _record_to_signal(
        self, record: Any, epoch: Optional[str] = None
    ) -> Tuple[Optional[SignalData], Optional[str]]:
        """Convert one export record, or explain why it was dropped.

        ``epoch`` is carried onto the signal because ``revision`` is only
        meaningful *within* one ledger generation — see
        ``SignalAggregator._apply_revision_update``.
        """
        if not isinstance(record, dict):
            return None, "malformed"

        kind = record.get("kind")
        if kind not in self.cfg.kinds:
            return None, "kind_filtered"

        # `or`, not a get() default: this publisher ships nulls as placeholders
        # (see canonical.entityIds, video, market), and an explicit null here
        # would otherwise drop every record as non-public.
        if (record.get("visibility") or "public") != "public":
            return None, "not_public"

        policy = record.get("policy") or {}
        political_safety = bool(policy.get("politicalSafety"))
        if political_safety and not self.cfg.include_political_safety:
            # Dropped, not sanitized. The rule is "do not reconstruct what this
            # channel argued", and every downstream stage of AO is a model being
            # asked what some text means. Not ingesting is the only version of
            # that rule which cannot be violated by a later prompt change.
            return None, "political_safety"

        title = (record.get("title") or "").strip()
        if not title:
            return None, "no_title"

        occurred_at = _parse_iso(record.get("occurredAt")) or _parse_iso(record.get("observedAt"))
        if self.cfg.max_age_days and occurred_at is not None:
            if occurred_at < utcnow() - timedelta(days=self.cfg.max_age_days):
                return None, "too_old"

        source_info = record.get("source") or {}
        evidence = record.get("evidence") or {}
        canonical = record.get("canonical") or {}
        raw_labels = record.get("raw") or {}
        video = record.get("video") or {}
        market = record.get("market") or {}

        # Nulls mean "no canonical match yet" and are placeholders aligned with
        # the raw list; they are not ids. Stripping them here keeps every
        # downstream consumer from having to know that.
        topic_id = canonical.get("topicId")
        entity_ids = [e for e in (canonical.get("entityIds") or []) if e]
        event_ids = [e for e in (canonical.get("eventIds") or []) if e]

        display_title = title
        if kind == KIND_MARKET and occurred_at is not None:
            # "비트코인 -1.90% · 5분" repeats across hundreds of pulses; without a
            # discriminator the aggregator's Jaccard dedup collapses distinct
            # market events into one.
            display_title = f"{title} ({occurred_at.date().isoformat()})"

        raw_data: Dict[str, Any] = {
            "signalmap_id": record.get("id"),
            "kind": kind,
            "source_type": record.get("sourceType"),
            "external_id": record.get("externalId"),
            "revision": record.get("revision"),
            # Stored beside the revision, never apart from it: a revision
            # number without its epoch is not comparable to anything.
            "epoch": epoch,
            "content_hash": record.get("contentHash"),
            "updated_at": record.get("updatedAt"),
            "occurred_at": record.get("occurredAt"),
            "observed_at": record.get("observedAt"),
            "lang": record.get("lang"),
            "channel": {
                "id": source_info.get("id"),
                "name": source_info.get("name"),
                "url": source_info.get("url"),
                "category": source_info.get("category"),
                "stance": source_info.get("channelStance"),
            },
            # The only stable foreign keys in the whole payload.
            "canonical": {
                "topic_id": topic_id,
                "entity_ids": entity_ids,
                "event_ids": event_ids,
            },
            # Deliberately named so nobody joins on it. Raw labels are the
            # summarizer's per-record wording: 6,301 of them collapse to 3,424
            # semantic clusters and 31 canonical topics.
            "unstable_labels": {
                "topic": (raw_labels.get("topic") or {}).get("label"),
                "topic_description": (raw_labels.get("topic") or {}).get("description"),
                "entities": raw_labels.get("entities") or [],
                "events": raw_labels.get("events") or [],
            },
            # Verbatim quotes are the sanctioned way to represent what was said,
            # including for political-safety records.
            "quotes": evidence.get("quotes") or [],
            "references": evidence.get("references") or [],
            "political_safety": political_safety,
        }

        if political_safety:
            # Upstream already ships these empty; asserting it locally means a
            # future upstream change cannot quietly hand us claims we are not
            # allowed to have.
            raw_data["claims"] = []
            raw_data["claims_withheld"] = True
        else:
            raw_data["claims"] = evidence.get("claims") or []
            raw_data["claims_withheld"] = False

        if video:
            raw_data["video"] = {
                "duration_s": video.get("durationS"),
                "view_count": video.get("viewCount"),
                "thumbnail_url": video.get("thumbnailUrl"),
                # A position on the cluster's dividing axis, not approval.
                # Meaningless without clusters.json's axis.statement, and not
                # aggregable at all when axis.comparable is false.
                "stance": video.get("stance"),
                "stance_reason": video.get("stanceReason"),
                "stance_axis_required": True,
            }
        if market:
            raw_data["market"] = market

        return (
            SignalData(
                source=self.name,
                category=self._category_for(kind, source_info),
                title=display_title,
                summary=(record.get("summary") or "").strip() or None,
                url=evidence.get("url") or source_info.get("url"),
                raw_data=raw_data,
                # The upstream event time, not our poll time. A backfill would
                # otherwise present six months of video as signals collected
                # today, and every time-windowed query downstream would believe
                # it.
                collected_at=occurred_at or utcnow(),
                metadata={
                    "external_id": record.get("id"),
                    "revision": record.get("revision"),
                    "epoch": epoch,
                    "kind": kind,
                    "channel_name": source_info.get("name"),
                    "political_safety": political_safety,
                    # Signal.topics / Signal.entities get canonical ids only.
                    "topics": [topic_id] if topic_id else [],
                    "entities": entity_ids,
                },
                external_id=record.get("id"),
            ),
            None,
        )

    @staticmethod
    def _category_for(kind: Optional[str], source_info: Dict[str, Any]) -> str:
        if kind == KIND_MARKET:
            return "crypto"
        channel_category = (source_info.get("category") or "").strip().lower()
        return _CATEGORY_MAP.get(channel_category, "other")

    # ------------------------------------------------------------------ health

    async def health_check(self) -> Dict[str, Any]:
        """Static health: config plus stored state. Never touches the network.

        ``GET /adapters`` calls this on every cache miss for every adapter; a
        network probe here would make a public endpoint a fan-out amplifier.
        """
        base_health = await super().health_check()
        state = FeedState.load(self.state_path)
        base_health.update(
            {
                "base_url": self.cfg.base_url,
                "kinds": self.cfg.kinds,
                "authenticated": bool(os.environ.get("SIGNALMAP_EXPORT_TOKEN", "").strip()),
                "epoch": state.epoch,
                "release_id": state.release_id,
                "cursor_set": bool(state.cursor),
                "backfilling": state.backfilling,
                "records_emitted": state.records_emitted,
                "resyncs": state.resyncs,
                "source_watermark": state.source_watermark,
                "watermark_age_hours": state.watermark_age_hours(),
                "last_success_at": state.last_success_at,
                "last_error": state.last_error,
            }
        )
        return base_health


# --------------------------------------------------------------------- report

# GET /status is public, uncached and hot, and load_config() re-parses ~24 KB of
# YAML. The paid-tier report hit the same wall and solved it the same way: parse
# once per process, read the small state file live so an operator sees a fixed
# feed on the next request rather than the next restart.
_report_config: Optional[SignalMapConfig] = None


def _report_config_cached() -> SignalMapConfig:
    global _report_config
    if _report_config is None:
        _report_config = SignalMapConfig.load()
    return _report_config


def reset_report_cache() -> None:
    """Test hook: drop the memoized config."""
    global _report_config
    _report_config = None


def _short_error(message: str, limit: int = 180) -> str:
    """One-line, bounded form of a stored error for a public JSON field.

    httpx errors are multi-line and carry a documentation URL; /status is a
    public endpoint and its `reason` is meant to be read at a glance. The full
    text stays in the state file and in /adapters' health block.
    """
    collapsed = " ".join(message.split())
    return collapsed if len(collapsed) <= limit else collapsed[: limit - 1] + "…"


def feed_report(state_path: Optional[Path] = None) -> Dict[str, Any]:
    """Config- and state-level view of the SignalMap feed for ``GET /status``.

    No network, no database. Answers the one question no record count can:
    is the upstream collector still producing?
    """
    try:
        cfg = _report_config_cached()
    except Exception:  # pragma: no cover - defensive
        return {"status": "unknown", "reason": "configuration unreadable"}

    if not cfg.enabled:
        return {"status": "disabled", "enabled": False}

    state = FeedState.load(state_path or Path(cfg.state_file))
    age = state.watermark_age_hours()

    report: Dict[str, Any] = {
        "status": "healthy",
        "enabled": True,
        "epoch": state.epoch,
        "release_id": state.release_id,
        "backfilling": state.backfilling,
        "cursor_set": bool(state.cursor),
        "source_watermark": state.source_watermark,
        "watermark_age_hours": round(age, 1) if age is not None else None,
        "last_success_at": state.last_success_at,
        "records_emitted": state.records_emitted,
    }

    # Order matters, and it is the operator's order: what is broken RIGHT NOW
    # before what is merely stale.
    #
    # `last_error` is checked FIRST, ahead of the never-synced case, because
    # the two are not alternatives — a feed whose every poll is failing has no
    # epoch either. Reporting that as "never synced" makes a feed that is down
    # look exactly like one whose first tick has not fired yet, which is the
    # precise failure this module was written to eliminate. It reproduced here
    # on the first live deploy: the upstream manifest returned a transient 504,
    # /adapters showed the error, and /status said "never synced".
    if state.last_error:
        report["status"] = "degraded"
        detail = _short_error(state.last_error)
        report["reason"] = (
            f"last poll failed: {detail}"
            if state.epoch
            else f"never synced; last attempt failed: {detail}"
        )
    elif state.epoch is None:
        report["status"] = "unknown"
        report["reason"] = "never synced"
    elif age is not None and age > cfg.watermark_stale_hours:
        report["status"] = "degraded"
        report["reason"] = (
            f"source watermark frozen for {age:.0f}h "
            f"(threshold {cfg.watermark_stale_hours}h) — upstream collection may have stopped"
        )

    return report

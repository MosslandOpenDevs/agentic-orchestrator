"""SignalStorage reads must be usable after the session closes.

`db.session()` commits and closes on exit and the session expires instances on
commit, so returning ORM rows handed callers a detached object whose first
attribute access raised DetachedInstanceError. Every read path -- and the
backup/export built on them -- was affected.
"""

import csv
import json

import pytest

from agentic_orchestrator.db import connection as db_connection
from agentic_orchestrator.db.connection import Database
from agentic_orchestrator.signals.storage import SignalStorage
from agentic_orchestrator.timeutil import utcnow


@pytest.fixture
def storage(tmp_path, monkeypatch):
    db = Database(f"sqlite:///{tmp_path / 'orchestrator.db'}")
    db.create_tables()
    # SignalStorage reaches for the module-level `db` singleton.
    monkeypatch.setattr(db_connection, "db", db)
    import agentic_orchestrator.signals.storage as storage_module

    monkeypatch.setattr(storage_module, "db", db)

    session = db.get_session()
    from agentic_orchestrator.db.models import Signal

    for i in range(3):
        session.add(
            Signal(
                id=f"sig-{i}",
                source="rss" if i < 2 else "github",
                category="ai",
                title=f"Signal {i}",
                summary="s",
                url=f"https://example.com/{i}",
                score=0.9,
                collected_at=utcnow(),
                raw_data={"secret": "payload"},
            )
        )
    session.commit()
    session.close()

    return SignalStorage(backup_dir=tmp_path / "signals")


class TestReadsSurviveTheSession:
    def test_get_recent_is_readable(self, storage):
        signals = storage.get_recent(hours=24, limit=10)

        assert len(signals) == 3
        # The access that used to raise DetachedInstanceError.
        assert {s["title"] for s in signals} == {"Signal 0", "Signal 1", "Signal 2"}

    def test_get_by_source_is_readable(self, storage):
        assert len(storage.get_by_source("rss", limit=10)) == 2

    def test_get_by_category_is_readable(self, storage):
        assert len(storage.get_by_category("ai", limit=10)) == 3

    def test_search_is_readable(self, storage):
        assert len(storage.search("Signal", limit=10)) >= 1


class TestBackupAndExport:
    def test_backup_writes_readable_json(self, storage):
        path = storage.backup_signals(hours=24)

        data = json.loads(path.read_text())
        assert len(data) == 3
        # raw_data is dropped unless asked for.
        assert all("raw_data" not in row for row in data)

    def test_backup_can_include_raw_data(self, storage):
        path = storage.backup_signals(hours=24, include_raw=True)

        data = json.loads(path.read_text())
        assert any(row.get("raw_data") for row in data)

    def test_json_export_is_readable(self, storage):
        path = storage.export_for_analysis(hours=24, format="json")

        assert len(json.loads(path.read_text())) == 3

    def test_csv_export_is_readable(self, storage):
        path = storage.export_for_analysis(hours=24, format="csv")

        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 3
        assert rows[0]["source"] in {"rss", "github"}

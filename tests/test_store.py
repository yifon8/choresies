import json
import pytest
from datetime import date, timedelta
from pathlib import Path

from chores.model import Chore
from chores.store import load_chores, save_chores, check_recurring_returns


@pytest.fixture
def tmp_store(tmp_path, monkeypatch):
    """Redirect DATA_FILE to a temp directory for each test."""
    import chores.store as store_module
    data_file = tmp_path / "chores.json"
    monkeypatch.setattr(store_module, "DATA_FILE", data_file)
    return data_file


# ------------------------------------------------------------------
# load / save
# ------------------------------------------------------------------

def test_load_returns_empty_when_no_file(tmp_store):
    assert load_chores() == []


def test_save_creates_file(tmp_store):
    chores = [Chore(name="Dishes")]
    save_chores(chores)
    assert tmp_store.exists()


def test_roundtrip(tmp_store):
    original = [Chore(name="Dishes"), Chore(name="Laundry")]
    save_chores(original)
    loaded = load_chores()
    assert len(loaded) == 2
    assert loaded[0].name == "Dishes"
    assert loaded[1].name == "Laundry"


def test_roundtrip_preserves_ids(tmp_store):
    c = Chore(name="Mop")
    save_chores([c])
    loaded = load_chores()
    assert loaded[0].id == c.id


def test_roundtrip_preserves_dates(tmp_store):
    c = Chore(name="Vacuum", recurring=True, interval_days=7)
    c.mark_done()
    save_chores([c])
    loaded = load_chores()
    assert loaded[0].last_done == date.today()
    assert loaded[0].next_due == date.today() + timedelta(days=7)


def test_save_creates_data_dir(tmp_path, monkeypatch):
    import chores.store as store_module
    nested = tmp_path / "sub" / "data" / "chores.json"
    monkeypatch.setattr(store_module, "DATA_FILE", nested)
    save_chores([Chore(name="Test")])
    assert nested.exists()


# ------------------------------------------------------------------
# check_recurring_returns
# ------------------------------------------------------------------

def test_overdue_chore_returns_to_undone():
    c = Chore(
        name="Test",
        status="done",
        recurring=True,
        interval_days=1,
        next_due=date.today() - timedelta(days=1),
    )
    changed = check_recurring_returns([c])
    assert changed is True
    assert c.status == "undone"


def test_future_chore_stays_done():
    c = Chore(
        name="Test",
        status="done",
        recurring=True,
        interval_days=7,
        next_due=date.today() + timedelta(days=3),
    )
    changed = check_recurring_returns([c])
    assert changed is False
    assert c.status == "done"


def test_nonrecurring_done_chore_unchanged():
    c = Chore(name="Test", status="done", recurring=False)
    check_recurring_returns([c])
    assert c.status == "done"


def test_returns_true_only_if_something_changed():
    chores = [
        Chore(name="A", status="done", recurring=True,
              interval_days=1, next_due=date.today() - timedelta(days=1)),
        Chore(name="B", status="done", recurring=True,
              interval_days=7, next_due=date.today() + timedelta(days=3)),
    ]
    changed = check_recurring_returns(chores)
    assert changed is True
    assert chores[0].status == "undone"
    assert chores[1].status == "done"


def test_empty_list_returns_false():
    assert check_recurring_returns([]) is False

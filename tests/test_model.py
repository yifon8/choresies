import pytest
from datetime import date, timedelta
from chores.model import Chore


def make_chore(**kwargs) -> Chore:
    kwargs.setdefault("name", "Test")
    return Chore(**kwargs)


# ------------------------------------------------------------------
# mark_done
# ------------------------------------------------------------------

def test_mark_done_sets_status():
    c = make_chore()
    c.mark_done()
    assert c.status == "done"


def test_mark_done_increments_completions():
    c = make_chore()
    c.mark_done()
    c.mark_done()
    assert c.completions == 2


def test_mark_done_sets_last_done_today():
    c = make_chore()
    c.mark_done()
    assert c.last_done == date.today()


def test_mark_done_sets_next_due_for_recurring():
    c = make_chore(recurring=True, interval_days=7)
    c.mark_done()
    assert c.next_due == date.today() + timedelta(days=7)


def test_mark_done_clears_next_due_for_nonrecurring():
    c = make_chore()
    c.mark_done()
    assert c.next_due is None


# ------------------------------------------------------------------
# redo
# ------------------------------------------------------------------

def test_redo_sets_undone():
    c = make_chore()
    c.mark_done()
    c.redo()
    assert c.status == "undone"


def test_redo_preserves_completions():
    c = make_chore()
    c.mark_done()
    original = c.completions
    c.redo()
    assert c.completions == original


def test_redo_preserves_last_done():
    c = make_chore()
    c.mark_done()
    last = c.last_done
    c.redo()
    assert c.last_done == last


def test_redo_preserves_interval_days():
    c = make_chore(recurring=True, interval_days=3)
    c.mark_done()
    c.redo()
    assert c.interval_days == 3


# ------------------------------------------------------------------
# set_recurrence
# ------------------------------------------------------------------

def test_set_recurrence_marks_recurring():
    c = make_chore()
    c.mark_done()
    c.set_recurrence(7)
    assert c.recurring is True
    assert c.interval_days == 7


def test_set_recurrence_calculates_next_due():
    c = make_chore()
    c.mark_done()
    c.set_recurrence(5)
    assert c.next_due == c.last_done + timedelta(days=5)


def test_set_recurrence_no_next_due_without_last_done():
    c = make_chore()
    c.set_recurrence(7)
    assert c.next_due is None


# ------------------------------------------------------------------
# is_due
# ------------------------------------------------------------------

def test_is_due_true_when_overdue():
    c = make_chore(
        status="done",
        recurring=True,
        interval_days=1,
        next_due=date.today() - timedelta(days=1),
    )
    assert c.is_due() is True


def test_is_due_true_when_due_today():
    c = make_chore(
        status="done",
        recurring=True,
        interval_days=1,
        next_due=date.today(),
    )
    assert c.is_due() is True


def test_is_due_false_when_future():
    c = make_chore(
        status="done",
        recurring=True,
        interval_days=1,
        next_due=date.today() + timedelta(days=1),
    )
    assert c.is_due() is False


def test_is_due_false_when_undone():
    c = make_chore(
        status="undone",
        recurring=True,
        next_due=date.today() - timedelta(days=1),
    )
    assert c.is_due() is False


def test_is_due_false_when_not_recurring():
    c = make_chore(
        status="done",
        recurring=False,
        next_due=date.today() - timedelta(days=1),
    )
    assert c.is_due() is False


# ------------------------------------------------------------------
# serialisation round-trip
# ------------------------------------------------------------------

def test_roundtrip_undone():
    c = make_chore(name="Dishes")
    assert Chore.from_dict(c.to_dict()).name == "Dishes"
    assert Chore.from_dict(c.to_dict()).status == "undone"


def test_roundtrip_done_recurring():
    c = make_chore(name="Laundry", recurring=True, interval_days=7)
    c.mark_done()
    c2 = Chore.from_dict(c.to_dict())
    assert c2.last_done == c.last_done
    assert c2.next_due == c.next_due
    assert c2.completions == 1


# ------------------------------------------------------------------
# due_label
# ------------------------------------------------------------------

def test_due_label_one_time():
    c = make_chore()
    assert c.due_label() == "One-time"


def test_due_label_overdue():
    c = make_chore(
        recurring=True, interval_days=1,
        next_due=date.today() - timedelta(days=2),
    )
    assert c.due_label() == "Overdue"


def test_due_label_today():
    c = make_chore(recurring=True, interval_days=1, next_due=date.today())
    assert c.due_label() == "Due today"


def test_due_label_tomorrow():
    c = make_chore(recurring=True, interval_days=1, next_due=date.today() + timedelta(days=1))
    assert c.due_label() == "Due tomorrow"

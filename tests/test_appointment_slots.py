"""
tests/test_appointment_slots.py — Unit tests for agent/slots.py

Covers: FALLBACK_PHRASE constant, compute_next_slots time math,
format_slot_tagalog Tagalog formatting, get_available_slots empty-URI path.

asyncio_mode = "auto" in pyproject.toml — no @pytest.mark.asyncio needed.
"""

import datetime
import pytest

from agent.slots import (
    FALLBACK_PHRASE,
    compute_next_slots,
    format_slot_tagalog,
    get_available_slots,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def test_fallback_phrase_constant():
    assert FALLBACK_PHRASE == "Tatawagan ka namin para mag-ayos ng oras"


# ---------------------------------------------------------------------------
# compute_next_slots
# ---------------------------------------------------------------------------

PH_TZ = datetime.timezone(datetime.timedelta(hours=8))


def test_compute_next_slots_empty():
    """Empty availability returns empty list."""
    result = compute_next_slots([])
    assert result == []


def test_compute_next_slots_buffer():
    """Slot < 2h from now is excluded; slot > 2h from now is included."""
    # Fix 'now' to a known time: Monday 10:00 PH
    now = datetime.datetime(2026, 6, 15, 10, 0, 0, tzinfo=PH_TZ)  # Monday

    # Row 1: Monday (weekday 0), start at 11:00 — only 1h from now → excluded
    row_too_soon = {
        "day_of_week": 0,
        "start_time": datetime.time(11, 0),
        "end_time": datetime.time(12, 0),
    }
    # Row 2: Monday (weekday 0), start at 14:00 — 4h from now → included
    row_ok = {
        "day_of_week": 0,
        "start_time": datetime.time(14, 0),
        "end_time": datetime.time(15, 0),
    }

    result = compute_next_slots([row_too_soon, row_ok], now=now)
    assert len(result) == 1
    assert result[0].hour == 14


def test_compute_next_slots_cap():
    """5 qualifying rows → at most 2 returned."""
    now = datetime.datetime(2026, 6, 15, 6, 0, 0, tzinfo=PH_TZ)  # Monday 06:00

    # Create 5 rows: Monday through Friday, each starting at 10:00
    rows = [
        {"day_of_week": i, "start_time": datetime.time(10, 0), "end_time": datetime.time(11, 0)}
        for i in range(5)  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri
    ]

    result = compute_next_slots(rows, now=now)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# format_slot_tagalog
# ---------------------------------------------------------------------------

def _make_dt(hour: int) -> datetime.datetime:
    """Make a timezone-aware PH datetime on a known weekday (Monday 2026-06-15)."""
    return datetime.datetime(2026, 6, 15, hour, 0, 0, tzinfo=PH_TZ)


def test_tagalog_format_morning():
    result = format_slot_tagalog(_make_dt(9))
    assert "ika-9 ng umaga" in result


def test_tagalog_format_noon():
    result = format_slot_tagalog(_make_dt(12))
    assert "tanghaling tapat" in result


def test_tagalog_format_afternoon():
    result = format_slot_tagalog(_make_dt(14))
    assert "ika-2 ng hapon" in result


def test_tagalog_format_prefix():
    result = format_slot_tagalog(_make_dt(10))
    assert "Mayroon kaming bakante sa" in result


# ---------------------------------------------------------------------------
# get_available_slots — empty URI graceful degradation
# ---------------------------------------------------------------------------

async def test_get_available_slots_empty_uri(monkeypatch):
    """With no DB env vars set, get_available_slots returns [] without raising."""
    monkeypatch.delenv("SUPABASE_DIRECT_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URI", raising=False)
    result = await get_available_slots("00000000-0000-4000-a000-000000000001")
    assert result == []

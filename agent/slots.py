"""
agent/slots.py — Slot math, Tagalog formatting, and Supabase availability query.

Exports: get_available_slots, compute_next_slots, format_slot_tagalog,
         FALLBACK_PHRASE, DAYS_PH

Security: db_uri read from env at call time — never logged. All SQL uses
parameterized queries (%s placeholders). (T-02-02 mitigation)
"""

import logging
import os
from datetime import datetime, date, time, timezone, timedelta

import psycopg

from api.db import db_uri

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FALLBACK_PHRASE: str = "Tatawagan ka namin para mag-ayos ng oras"

DAYS_PH: list[str] = [
    "Lunes",       # 0 = Monday
    "Martes",      # 1 = Tuesday
    "Miyerkules",  # 2 = Wednesday
    "Huwebes",     # 3 = Thursday
    "Biyernes",    # 4 = Friday
    "Sabado",      # 5 = Saturday
    "Linggo",      # 6 = Sunday
]

_PH_TZ = timezone(timedelta(hours=8))

# ---------------------------------------------------------------------------
# Tagalog formatting
# ---------------------------------------------------------------------------


def format_slot_tagalog(dt: datetime) -> str:
    """Return a Tagalog natural-language string for a slot datetime.

    Examples:
        hour=9  → "Mayroon kaming bakante sa Lunes ng June 15 sa ika-9 ng umaga"
        hour=12 → "... sa tanghaling tapat"
        hour=14 → "... sa ika-2 ng hapon"
    """
    day_name = DAYS_PH[dt.weekday()]
    date_str = dt.strftime("%B %d")
    hour = dt.hour
    if hour < 12:
        time_str = f"ika-{hour} ng umaga"
    elif hour == 12:
        time_str = "tanghaling tapat"
    else:
        time_str = f"ika-{hour - 12} ng hapon"
    return f"Mayroon kaming bakante sa {day_name} ng {date_str} sa {time_str}"


# ---------------------------------------------------------------------------
# Slot computation
# ---------------------------------------------------------------------------


def compute_next_slots(
    availability_rows: list[dict],
    now: datetime | None = None,
    max_count: int = 2,
) -> list[datetime]:
    """Return up to max_count qualifying slot datetimes from availability_rows.

    Each row must have:
        day_of_week: int (0=Monday … 6=Sunday)
        start_time: datetime.time or str "HH:MM"
        end_time: datetime.time or str "HH:MM"

    A slot qualifies when candidate_dt > now + 2h (Pitfall 3 guard).
    Iterates today through today+6 (7 days).

    Returns [] if availability_rows is empty or no slots qualify.
    """
    if not availability_rows:
        return []

    if now is None:
        now = datetime.now(tz=_PH_TZ)

    buffer = now + timedelta(hours=2)
    results: list[datetime] = []
    today = now.date()

    for day_offset in range(7):
        candidate_date: date = today + timedelta(days=day_offset)
        target_weekday = candidate_date.weekday()

        for row in availability_rows:
            if row["day_of_week"] != target_weekday:
                continue

            # Normalise start_time — accept both datetime.time and "HH:MM" str
            st = row["start_time"]
            if isinstance(st, str):
                parts = st.split(":")
                st = time(int(parts[0]), int(parts[1]))

            candidate_dt = datetime(
                candidate_date.year,
                candidate_date.month,
                candidate_date.day,
                st.hour,
                st.minute,
                tzinfo=_PH_TZ,
            )

            if candidate_dt <= buffer:
                continue

            results.append(candidate_dt)
            if len(results) >= max_count:
                return results

    return results


# ---------------------------------------------------------------------------
# Supabase query
# ---------------------------------------------------------------------------


async def get_available_slots(business_id: str, days_ahead: int = 7) -> list[dict]:
    """Fetch business_availability rows from Supabase via psycopg.

    Returns list of dicts with keys: day_of_week, start_time, end_time.
    Returns [] if DATABASE_URL is not set
    (graceful degradation for unit tests without a DB). (T-02-02: uri never logged)

    Parameterized query — business_id is never string-interpolated. (T-02-01)
    """
    uri = db_uri()
    if not uri:
        return []

    # A dead/unreachable DB must degrade to "no slots" (the agent then offers a
    # call-back) rather than raise — an uncaught error here would crash the live
    # WebSocket conversation at the propose_appointment stage.
    try:
        async with await psycopg.AsyncConnection.connect(uri) as conn:
            cur = await conn.execute(
                """
                SELECT day_of_week, start_time, end_time
                FROM business_availability
                WHERE business_id = %s
                ORDER BY day_of_week, start_time
                """,
                (business_id,),
            )
            rows = await cur.fetchall()
    except (psycopg.OperationalError, psycopg.DatabaseError) as exc:
        logger.warning("Availability lookup failed — degrading to no slots: %s", type(exc).__name__)
        return []

    return [{"day_of_week": r[0], "start_time": r[1], "end_time": r[2]} for r in rows]

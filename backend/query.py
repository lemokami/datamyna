from datetime import date, timedelta

from fastapi import APIRouter, Query

from db import get_conn

router = APIRouter()


# ── Aggregate time-series endpoints ───────────────────────────────────────────

@router.get("/dau")
def get_dau(days: int = Query(30, ge=1, le=365)):
    """Daily unique users for a date range."""
    end   = date.today()
    start = end - timedelta(days=days - 1)
    conn  = get_conn()
    cur   = conn.cursor()
    cur.execute(
        """
        SELECT date, unique_users, session_count, total_events
        FROM dau_summary
        WHERE date BETWEEN %s AND %s
        ORDER BY date ASC
        """,
        (start, end),
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [
        {"date": str(r[0]), "unique_users": r[1], "session_count": r[2], "total_events": r[3]}
        for r in rows
    ]


@router.get("/wau")
def get_wau(weeks: int = Query(12, ge=1, le=52)):
    """Weekly unique users — summed from dau_summary (approx: may double-count cross-day users)."""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        f"""
        SELECT
            DATE_TRUNC('week', date)::date AS week,
            SUM(unique_users)              AS users,
            SUM(session_count)             AS sessions,
            SUM(total_events)              AS events
        FROM dau_summary
        WHERE date >= CURRENT_DATE - INTERVAL '{int(weeks)} weeks'
        GROUP BY week
        ORDER BY week ASC
        """
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [
        {"week": str(r[0]), "unique_users": r[1], "session_count": r[2], "total_events": r[3]}
        for r in rows
    ]


@router.get("/mau")
def get_mau(months: int = Query(6, ge=1, le=24)):
    """Monthly unique users — summed from dau_summary (same approximation as WAU)."""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        f"""
        SELECT
            DATE_TRUNC('month', date)::date AS month,
            SUM(unique_users)               AS users,
            SUM(session_count)              AS sessions,
            SUM(total_events)               AS events
        FROM dau_summary
        WHERE date >= CURRENT_DATE - INTERVAL '{int(months)} months'
        GROUP BY month
        ORDER BY month ASC
        """
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [
        {"month": str(r[0]), "unique_users": r[1], "session_count": r[2], "total_events": r[3]}
        for r in rows
    ]


@router.get("/top-pages")
def get_top_pages(days: int = Query(7, ge=1, le=90)):
    """Top 10 pages by view count over a date range."""
    end   = date.today()
    start = end - timedelta(days=days - 1)
    conn  = get_conn()
    cur   = conn.cursor()
    cur.execute(
        """
        SELECT page_path, SUM(view_count) AS total_views
        FROM top_pages_summary
        WHERE date BETWEEN %s AND %s
        GROUP BY page_path
        ORDER BY total_views DESC
        LIMIT 10
        """,
        (start, end),
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [{"page_path": r[0], "view_count": r[1]} for r in rows]


@router.get("/events/timeline")
def get_event_timeline(
    event_name: str,
    days: int = Query(30, ge=1, le=90),
):
    """Daily count of a specific named event over a date range."""
    end   = date.today()
    start = end - timedelta(days=days - 1)
    conn  = get_conn()
    cur   = conn.cursor()
    cur.execute(
        """
        SELECT date, count
        FROM event_summary
        WHERE event_name = %s AND date BETWEEN %s AND %s
        ORDER BY date ASC
        """,
        (event_name, start, end),
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [{"date": str(r[0]), "count": r[1]} for r in rows]


@router.get("/stats/today")
def get_stats_today():
    """Single-object KPI snapshot for today."""
    today = date.today()
    conn  = get_conn()
    cur   = conn.cursor()

    cur.execute(
        "SELECT unique_users, session_count, total_events FROM dau_summary WHERE date = %s",
        (today,),
    )
    row = cur.fetchone()

    cur.execute(
        """
        SELECT page_path FROM top_pages_summary
        WHERE date = %s ORDER BY view_count DESC LIMIT 1
        """,
        (today,),
    )
    top_page = cur.fetchone()

    cur.close(); conn.close()
    return {
        "unique_users":  row[0] if row else 0,
        "session_count": row[1] if row else 0,
        "total_events":  row[2] if row else 0,
        "top_page":      top_page[0] if top_page else None,
    }


# ── User journey endpoints ─────────────────────────────────────────────────────

@router.get("/sessions")
def get_sessions(
    days:    int          = Query(7, ge=1, le=90),
    user_id: str | None   = Query(None),
    limit:   int          = Query(50, ge=1, le=200),
):
    """
    List recent sessions from the sessions summary table.
    Optionally filter by user_id.
    """
    start = date.today() - timedelta(days=days - 1)
    conn  = get_conn()
    cur   = conn.cursor()

    if user_id:
        cur.execute(
            """
            SELECT session_id, user_id, started_at, ended_at,
                   first_page, last_page, event_count, duration_seconds
            FROM sessions
            WHERE user_id = %s AND started_at::date >= %s
            ORDER BY started_at DESC
            LIMIT %s
            """,
            (user_id, start, limit),
        )
    else:
        cur.execute(
            """
            SELECT session_id, user_id, started_at, ended_at,
                   first_page, last_page, event_count, duration_seconds
            FROM sessions
            WHERE started_at::date >= %s
            ORDER BY started_at DESC
            LIMIT %s
            """,
            (start, limit),
        )

    rows = cur.fetchall()
    cur.close(); conn.close()

    return [
        {
            "session_id":       r[0],
            "user_id":          r[1],
            "started_at":       r[2].isoformat() if r[2] else None,
            "ended_at":         r[3].isoformat() if r[3] else None,
            "first_page":       r[4],
            "last_page":        r[5],
            "event_count":      r[6],
            "duration_seconds": r[7],
        }
        for r in rows
    ]


@router.get("/sessions/{session_id}/events")
def get_session_events(session_id: str):
    """
    Full event sequence for one session, ordered by timestamp.
    This is the ONE place that reads raw_events directly — it's a narrow
    indexed lookup on session_id, not a full table scan.
    """
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        """
        SELECT timestamp, event_type, event_name, page_path, properties
        FROM raw_events
        WHERE session_id = %s
        ORDER BY timestamp ASC
        """,
        (session_id,),
    )
    rows = cur.fetchall()
    cur.close(); conn.close()

    return [
        {
            "timestamp":  r[0].isoformat() if r[0] else None,
            "event_type": r[1],
            "event_name": r[2],
            "page_path":  r[3],
            "properties": r[4],
        }
        for r in rows
    ]

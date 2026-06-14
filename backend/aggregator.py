from datetime import date, timedelta
from db import get_conn


def run_aggregator(target: date = None):
    """
    Aggregates raw events for `target` date into all summary tables.
    Defaults to yesterday. Safe to re-run — all inserts use ON CONFLICT DO UPDATE.
    """
    if target is None:
        target = date.today() - timedelta(days=1)

    conn = get_conn()
    cur = conn.cursor()

    print(f"[aggregator] Aggregating {target}")

    # ── DAU summary ────────────────────────────────────────────────────────────
    cur.execute("""
        INSERT INTO dau_summary (date, unique_users, session_count, total_events)
        SELECT
            %s::date,
            COUNT(DISTINCT user_id),
            COUNT(DISTINCT session_id),
            COUNT(*)
        FROM raw_events
        WHERE timestamp::date = %s
        ON CONFLICT (date) DO UPDATE SET
            unique_users  = EXCLUDED.unique_users,
            session_count = EXCLUDED.session_count,
            total_events  = EXCLUDED.total_events
    """, (target, target))

    # ── Top pages summary ──────────────────────────────────────────────────────
    cur.execute("""
        INSERT INTO top_pages_summary (date, page_path, view_count)
        SELECT
            %s::date,
            page_path,
            COUNT(*) AS view_count
        FROM raw_events
        WHERE timestamp::date = %s
          AND event_type = 'page_view'
          AND page_path IS NOT NULL
        GROUP BY page_path
        ON CONFLICT (date, page_path) DO UPDATE SET
            view_count = EXCLUDED.view_count
    """, (target, target))

    # ── Event summary ──────────────────────────────────────────────────────────
    cur.execute("""
        INSERT INTO event_summary (date, event_name, count)
        SELECT
            %s::date,
            event_name,
            COUNT(*) AS count
        FROM raw_events
        WHERE timestamp::date = %s
        GROUP BY event_name
        ON CONFLICT (date, event_name) DO UPDATE SET
            count = EXCLUDED.count
    """, (target, target))

    # ── Sessions summary ───────────────────────────────────────────────────────
    # Groups raw events by session_id for sessions that STARTED on target date.
    # first_page / last_page pulled with ORDER BY inside ARRAY_AGG.
    cur.execute("""
        INSERT INTO sessions (
            session_id, user_id, started_at, ended_at,
            first_page, last_page, event_count, duration_seconds
        )
        SELECT
            session_id,
            MAX(user_id),
            MIN(timestamp)                                                  AS started_at,
            MAX(timestamp)                                                  AS ended_at,
            (ARRAY_AGG(page_path ORDER BY timestamp ASC  NULLS LAST))[1]   AS first_page,
            (ARRAY_AGG(page_path ORDER BY timestamp DESC NULLS LAST))[1]   AS last_page,
            COUNT(*)                                                        AS event_count,
            EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp)))::int      AS duration_seconds
        FROM raw_events
        WHERE session_id IN (
            SELECT DISTINCT session_id
            FROM raw_events
            WHERE timestamp::date = %s
        )
        GROUP BY session_id
        ON CONFLICT (session_id) DO UPDATE SET
            ended_at         = EXCLUDED.ended_at,
            last_page        = EXCLUDED.last_page,
            event_count      = EXCLUDED.event_count,
            duration_seconds = EXCLUDED.duration_seconds
    """, (target,))

    conn.commit()
    cur.close()
    conn.close()
    print(f"[aggregator] Done {target}")


def backfill(days: int = 90):
    """Run aggregator for the last N days — used after seeding."""
    today = date.today()
    for i in range(days, -1, -1):
        run_aggregator(today - timedelta(days=i))

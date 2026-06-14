import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/datamyna")


def get_conn():
    return psycopg2.connect(DB_URL)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # ── Raw events ────────────────────────────────────────────────────────────
    # Append-only source of truth. Never updated or deleted.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_events (
            id          BIGSERIAL PRIMARY KEY,
            timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            session_id  TEXT        NOT NULL,
            user_id     TEXT,
            event_type  TEXT        NOT NULL,
            event_name  TEXT        NOT NULL,
            page_path   TEXT,
            properties  JSONB       NOT NULL DEFAULT '{}'
        )
    """)

    # Descending index → fast "give me events between A and B" without full scan
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_events_ts
        ON raw_events (timestamp DESC)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_events_session
        ON raw_events (session_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_events_user
        ON raw_events (user_id)
    """)

    # ── Summary tables (the data mart) ────────────────────────────────────────
    # Dashboard reads ONLY these. Never raw_events (except session drill-in).

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dau_summary (
            date          DATE PRIMARY KEY,
            unique_users  INT NOT NULL DEFAULT 0,
            session_count INT NOT NULL DEFAULT 0,
            total_events  INT NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS top_pages_summary (
            date       DATE NOT NULL,
            page_path  TEXT NOT NULL,
            view_count INT  NOT NULL DEFAULT 0,
            PRIMARY KEY (date, page_path)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS event_summary (
            date        DATE NOT NULL,
            event_name  TEXT NOT NULL,
            count       INT  NOT NULL DEFAULT 0,
            PRIMARY KEY (date, event_name)
        )
    """)

    # ── Sessions table ─────────────────────────────────────────────────────────
    # One row per session. Powers the user journey list.
    # Raw events are still the source of truth for the drill-in view.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id       TEXT PRIMARY KEY,
            user_id          TEXT,
            started_at       TIMESTAMPTZ NOT NULL,
            ended_at         TIMESTAMPTZ NOT NULL,
            first_page       TEXT,
            last_page        TEXT,
            event_count      INT NOT NULL DEFAULT 0,
            duration_seconds INT NOT NULL DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_user
        ON sessions (user_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_started
        ON sessions (started_at DESC)
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("[db] Tables initialised")

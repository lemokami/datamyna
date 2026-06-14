"""
Run this once after `docker compose up` to populate the database:
    docker compose exec backend python seed.py
Then run the aggregator to populate summary tables:
    docker compose exec backend python -c "from aggregator import backfill; backfill(90)"
"""

import json
import random
import uuid
from datetime import datetime, timedelta

from faker import Faker

from db import get_conn, init_db

fake = Faker()

PAGES = [
    "/",
    "/pricing",
    "/features",
    "/blog",
    "/blog/getting-started",
    "/blog/analytics-tips",
    "/register",
    "/login",
    "/dashboard",
    "/about",
]

NAMED_EVENTS = [
    "signup_click",
    "pricing_cta",
    "blog_read",
    "form_submitted",
    "upgrade_click",
    "demo_request",
    "newsletter_subscribe",
]

USERS = [f"u_{i:03d}" for i in range(1, 501)]


def make_session(user_id: str, base_time: datetime):
    """Generate a single realistic session as a list of events."""
    session_id = f"s_{uuid.uuid4().hex[:10]}"
    events     = []
    offset     = 0
    page       = random.choice(PAGES)
    num_events = random.randint(2, 18)

    for i in range(num_events):
        ts         = base_time + timedelta(seconds=offset)
        event_type = "page_view" if (i == 0 or random.random() < 0.25) else "click"
        if event_type == "page_view":
            page       = random.choice(PAGES)
            event_name = "page_view"
        elif random.random() < 0.3:
            event_name = random.choice(NAMED_EVENTS)
            event_type = "custom"
        else:
            event_name = "click"

        events.append((
            ts,
            session_id,
            user_id,
            event_type,
            event_name,
            page,
            json.dumps({"index": i, "source": "seed"}),
        ))

        # Realistic dwell time between events
        offset += random.randint(5, 180)

    return events


def seed(target_events: int = 120_000):
    init_db()
    conn = get_conn()
    cur  = conn.cursor()

    now    = datetime.utcnow()
    batch  = []
    count  = 0

    print(f"Seeding ~{target_events:,} events …")

    while count < target_events:
        user_id   = random.choice(USERS)
        days_ago  = random.randint(0, 89)
        hour      = random.randint(7, 23)
        base_time = now - timedelta(days=days_ago, hours=now.hour - hour, minutes=random.randint(0, 59))

        session_events = make_session(user_id, base_time)
        batch.extend(session_events)
        count += len(session_events)

        if len(batch) >= 5000:
            cur.executemany(
                """
                INSERT INTO raw_events
                    (timestamp, session_id, user_id, event_type, event_name, page_path, properties)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                batch,
            )
            conn.commit()
            print(f"  inserted {count:,} events")
            batch = []

    if batch:
        cur.executemany(
            """
            INSERT INTO raw_events
                (timestamp, session_id, user_id, event_type, event_name, page_path, properties)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            batch,
        )
        conn.commit()

    cur.close()
    conn.close()
    print(f"Done — {count:,} events seeded.")


if __name__ == "__main__":
    seed()

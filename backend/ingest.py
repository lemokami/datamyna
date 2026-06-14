import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from db import get_conn

router = APIRouter()


class Event(BaseModel):
    timestamp:  Optional[datetime] = None
    session_id: str
    user_id:    Optional[str] = None
    event_type: str
    event_name: str
    page_path:  Optional[str] = None
    properties: Optional[Dict[str, Any]] = {}


@router.post("/ingest")
def ingest(events: List[Event]):
    if not events:
        return {"ok": True, "inserted": 0}

    rows = [
        (
            e.timestamp or datetime.utcnow(),
            e.session_id,
            e.user_id,
            e.event_type,
            e.event_name,
            e.page_path,
            json.dumps(e.properties or {}),
        )
        for e in events
    ]

    conn = get_conn()
    cur = conn.cursor()

    # One round-trip for the whole batch — not one INSERT per event
    cur.executemany(
        """
        INSERT INTO raw_events
            (timestamp, session_id, user_id, event_type, event_name, page_path, properties)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"ok": True, "inserted": len(rows)}

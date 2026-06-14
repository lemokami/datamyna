from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler

from db import init_db
from ingest import router as ingest_router
from query import router as query_router
from aggregator import run_aggregator

app = FastAPI(title="DataMyna API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(query_router)


@app.get("/tracker.js", include_in_schema=False)
def serve_tracker():
    return FileResponse("tracker/tracker.js", media_type="application/javascript")


scheduler = BackgroundScheduler()


@app.on_event("startup")
def startup():
    init_db()
    scheduler.add_job(run_aggregator, "interval", hours=1, id="aggregator")
    scheduler.start()
    print("[main] Scheduler started")


@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown()

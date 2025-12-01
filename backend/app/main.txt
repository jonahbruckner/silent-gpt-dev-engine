from fastapi import FastAPI
from app.db import init_db
from app.jobs.scheduler import start_scheduler

app = FastAPI(title="SilentGPT Dev Engine")

@app.on_event("startup")
async def startup_event():
    init_db()
    start_scheduler()

@app.get("/")
def root():
    return {"status": "running", "message": "SilentGPT Engine Operational"}

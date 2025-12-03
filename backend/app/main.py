from fastapi import FastAPI
from .api import payments, webhooks
from .db import init_db
# from .jobs.scheduler import start_scheduler  # falls du später einen internen Scheduler nutzt

app = FastAPI(title="SilentGPT Dev Engine")
app.include_router(payments.router)
app.include_router(webhooks.router)


@app.on_event("startup")
async def startup_event():
    init_db()
    # start_scheduler()  # optional


@app.get("/")
def root():
    return {"status": "running", "message": "SilentGPT Engine Operational"}

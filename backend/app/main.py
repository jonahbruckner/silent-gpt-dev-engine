from fastapi import FastAPI
from .api import payments
from .db import init_db
# from .jobs.scheduler import start_scheduler  # if you have this, else comment it out

app = FastAPI(title="SilentGPT Dev Engine")
app.include_router(payments.router)

@app.on_event("startup")
async def startup_event():
    init_db()
    # If you haven't implemented the scheduler yet, comment the next line:
    # start_scheduler()


@app.get("/")
def root():
    return {"status": "running", "message": "SilentGPT Engine Operational"}

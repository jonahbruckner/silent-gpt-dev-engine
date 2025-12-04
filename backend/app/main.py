import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import payments, webhooks, metrics   # <- metrics dazu
from .db import init_db

app = FastAPI(title="SilentGPT Dev Engine")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router registrieren
app.include_router(payments.router)
app.include_router(webhooks.router)
app.include_router(metrics.router)  # <- NEU


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
def root():
    return {"status": "running", "message": "SilentGPT Engine Operational"}

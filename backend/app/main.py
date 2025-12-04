import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import payments, webhooks
from .db import init_db

app = FastAPI(title="SilentGPT Dev Engine")

# ------------------------------------------------------
# CORS – für Netlify-Frontend + lokale Entwicklung
# ------------------------------------------------------
# Wenn du es enger machen willst:
# origins = ["https://steady-lollipop-79396b.netlify.app"]
# Fürs erste: alles erlauben, damit Preflight sicher durchgeht.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, OPTIONS, alles
    allow_headers=["*"],
)

# ------------------------------------------------------
# Router registrieren
# ------------------------------------------------------
app.include_router(payments.router)
app.include_router(webhooks.router)


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
def root():
    return {"status": "running", "message": "SilentGPT Engine Operational"}

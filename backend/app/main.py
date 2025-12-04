from fastapi import FastAPI
from .api import payments, webhooks
from .db import init_db

app = FastAPI(title="SilentGPT Dev Engine")

# CORS-Konfiguration
frontend_origin = os.getenv("FRONTEND_ORIGIN", "").rstrip("/")

allowed_origins = []

# falls in ENV gesetzt (empfohlen auf Render)
if frontend_origin:
    allowed_origins.append(frontend_origin)

# lokale Dev-Origins
allowed_origins.extend([
    "http://localhost:1313",  # Hugo
    "http://localhost:3000",  # falls du später ein SPA hast
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],  # notfalls alles, wenn nix gesetzt
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments.router)
app.include_router(webhooks.router)


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
def root():
    return {"status": "running", "message": "SilentGPT Engine Operational"}

"""FastAPI Main Application Entrypoint for AI Academic Early-Warning Engine."""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router as api_router
from memory.init_db import seed_database

# Root directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="AI Agent Coordination & Decision Engine",
    description="AI Academic Early-Warning & Intervention Decision Engine with multi-agent LangGraph coordination and deterministic risk scoring.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    """Ensure database schema is created and synthetic data is seeded on server start."""
    try:
        seed_database()
    except Exception as e:
        # Prevent serverless cold-start failure if seeding cannot complete
        import logging
        logging.getLogger("api.main").warning("Database seeding during startup notice: %s", e)



# Mount frontend static directory if exists
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serve the enterprise dashboard frontend."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {
        "message": "AI Agent Coordination & Decision Engine API",
        "health": "/health",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("api.main:app", host=host, port=port, reload=True)

"""
Main entry point for the CaRMS Platform API.
Configures lifespan events, middleware, and router synchronization.
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.carms.db.engine import engine
from sqlmodel import SQLModel
from src.carms.api.routers import programs, analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Ensures database tables are created before the API starts accepting requests.
    """
    from src.carms.db import models
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(
    title="CaRMS Program Explorer API",
    description="Backend API providing access to processed CaRMS residency program data.",
    version="0.1.0",
    lifespan=lifespan
)

# Register API routes
app.include_router(programs.router, prefix="/api/v1", tags=["programs"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])

@app.get("/health")
def health_check():
    """Simple health check endpoint to verify API availability."""
    return {"status": "ok"}

from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.carms.db.engine import engine
from sqlmodel import SQLModel
from src.carms.api.routers import programs, analytics

# Lifecycle event to create tables if they don't exist (useful for dev)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retrieve models to ensure they are registered
    from src.carms.db import models
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(
    title="CaRMS Program Explorer API",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(programs.router, prefix="/api/v1", tags=["programs"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

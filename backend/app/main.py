# backend/app/main.py
# FastAPI application entry point.

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.database import engine, init_db
from app.routers import analytics, books, dashboard, events, operations, sensor


# ---------------------------------------------------------------------------
# Lifespan: create DB tables on startup (no Alembic needed for dev)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Smart Library API",
    version="1.0.0",
    description="Backend for Smart Library Automation — Arduino sensor data & book events",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server (and any origins listed in .env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(sensor.router)
app.include_router(books.router)
app.include_router(dashboard.router)
app.include_router(events.router)
app.include_router(analytics.router)
app.include_router(operations.router)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred"},
    )


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "Smart Library API"}

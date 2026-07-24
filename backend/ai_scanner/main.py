from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_scanner.app.routers import audit, auth, dashboard, reports, scans
from ai_scanner.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from ai_scanner.app.db.database import engine, Base
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Smart Consumable Scanner AI API",
    description="Enterprise AI inspection system backend.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(scans.router, prefix="/scans", tags=["scans"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(audit.router, prefix="/admin", tags=["admin"])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

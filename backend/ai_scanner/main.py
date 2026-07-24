# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from ai_scanner.app.limiter import limiter

from ai_scanner.app.routers import (
    admin,
    analytics,
    audit,
    auth,
    dashboard,
    model_registry,
    monitoring,
    pilot_profiles,
    products,
    reports,
    reviews,
    scans,
)
from ai_scanner.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from ai_scanner.app.db.database import Base, engine
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Smart Consumable Scanner AI API",
    description="Enterprise AI inspection system backend.",
    version="0.6.0-rc1",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS is intentionally permissive for Expo development. In production, set
# CORS_ORIGINS to the exact mobile/dashboard domains.
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
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
app.include_router(audit.router, prefix="/admin", tags=["admin"])
app.include_router(pilot_profiles.router, prefix="/pilot-profiles", tags=["pilot"])
app.include_router(model_registry.router, prefix="/model-registry", tags=["models"])
app.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])


@app.get("/health", tags=["health"])
@limiter.limit("60/minute")
def health_check(request: Request):
    return {"status": "ok"}

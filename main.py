# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Ensure backend and ai-service packages are importable.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.path.insert(0, os.path.join(BASE_DIR, "ai-service"))

from ai_scanner.main import app as backend_app
from ai_service.main import app as ai_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise backend database tables.
    from ai_scanner.app.db.database import Base, engine
    Base.metadata.create_all(bind=engine)
    # Warm up AI classifier.
    from ai_service.app.models.classifier import classifier
    if hasattr(classifier, "warm_up"):
        classifier.warm_up()
    yield


app = FastAPI(
    title="Smart Consumable Scanner AI Pilot",
    description="Combined backend and AI inference service for private pilot.",
    version="0.1.9-rc1",
    lifespan=lifespan,
)

# AI inference mounted under /ai so the backend can call it internally.
app.mount("/ai", ai_app)
app.mount("/", backend_app)

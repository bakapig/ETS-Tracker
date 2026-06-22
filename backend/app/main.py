from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.services.state import app_state


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await app_state.load_static(force_download=False)
    await app_state.start_background_tasks()
    yield
    await app_state.stop_background_tasks()


app = FastAPI(
    title="ETS Live Malaysia API",
    description="Real-time ETS train arrivals for Malaysia (KTMB GTFS)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "ETS Live Malaysia API",
        "docs": "/docs",
        "health": "/api/health",
    }

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ml_command_center import router as ml_command_center_router
from app.api.router import api_router
from app.database.connection import create_database_tables


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_database_tables()
    yield


app = FastAPI(
    title="SurakshaAI Backend",
    description=(
        "AI-powered industrial safety intelligence platform "
        "for compound-risk detection"
    ),
    version="0.2.0",
    lifespan=lifespan,
)

cors_origins = [
    value.strip()
    for value in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if value.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(ml_command_center_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "SurakshaAI backend is running"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SurakshaAI Backend",
        "database": "connected",
    }

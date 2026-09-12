from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import init_db
from app.db.seed import seed_database
from app.api.v1 import dashboard, leaderboard, benchmark_analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize and seed database on startup
    init_db()
    seed_database()
    yield

app = FastAPI(
    title="VerifAI - Trust Dashboard, Leaderboard & Benchmark Analytics API",
    description="Read-only analytics layer for VerifAI core verification system.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register V1 Routers
app.include_router(dashboard.router)
app.include_router(leaderboard.router)
app.include_router(benchmark_analytics.router)

@app.get("/")
def root():
    return {
        "status": "healthy",
        "module": "VERIFAI - Trust Dashboard, Model Leaderboard & Benchmark Analytics",
        "documentation": "/docs"
    }

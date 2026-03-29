import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import health, analysis, labs, billing, wearables, history, chat, export, extraction
from routers import users as users_router
from routers import notifications as notifications_router
from database import connect_db, disconnect_db
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx

load_dotenv()

# Background Scheduler for Wearables Sync
scheduler = AsyncIOScheduler()

async def fetch_daily_wearables():
    """
    Cron job firing at 08:00 UTC. Iterates over Pro users to proactively 
    fetch their daily Oura readiness scores without requiring a dashboard login.
    """
    print("[Cron] Firing daily 08:00 UTC Oura sync for active Pro users...")
    # Production: await db.user.find_many(where={"is_pro": True, "oura_token": {"not": None}})
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    
    # Eagerly load ML Models into memory (250MB+)
    from engine.inference import predictor
    
    # Schedule wearable sync daily at 8 AM UTC
    scheduler.add_job(fetch_daily_wearables, 'cron', hour=8, minute=0)
    scheduler.start()
    print("[Cron] Wearable sync scheduler started.")
    yield
    await disconnect_db()
    scheduler.shutdown()

app = FastAPI(
    title="EIRION API",
    description="AI-Powered Precision Longevity Platform — Phase 0 Prototype",
    version="0.3.0",
    lifespan=lifespan,
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(users_router.router, prefix="/users", tags=["Auth"])
app.include_router(notifications_router.router, prefix="/notifications", tags=["Notifications"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(labs.router, prefix="/labs", tags=["Labs"])
app.include_router(billing.router, prefix="/billing", tags=["Billing"])
app.include_router(wearables.router, prefix="/wearables", tags=["Wearables"])
app.include_router(history.router, prefix="/history", tags=["History"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(export.router, prefix="/export", tags=["Export"])
app.include_router(extraction.router, prefix="/extraction", tags=["Extraction"])

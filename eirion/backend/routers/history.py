from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from auth import get_current_user

router = APIRouter()

@router.get("/my-progress")
async def get_longitudinal_history(user: dict = Depends(get_current_user)):
    """
    Fetches the historical record of a user's biological age / liver index scores
    to visualize progressive improvement over time.
    """
    # Phase 2: In production, query PostgreSQL
    # records = await db.trajectoryhistory.find_many(
    #     where={"user_id": user["user_id"]},
    #     order={"created_at": "asc"}
    # )
    
    # For Phase 0/1 stubbing without real DB row injection, we simulate 
    # a user who has been using Eirion for 6 months and improving:
    records = [
        {"created_at": "2025-09-01T10:00:00Z", "score": 72},
        {"created_at": "2025-10-01T10:00:00Z", "score": 74},
        {"created_at": "2025-11-01T10:00:00Z", "score": 77},
        {"created_at": "2025-12-01T10:00:00Z", "score": 79},
        {"created_at": "2026-01-01T10:00:00Z", "score": 83},
        {"created_at": "2026-02-01T10:00:00Z", "score": 84},
        # March depends on current run
    ]
    
    return {"status": "success", "history": records}

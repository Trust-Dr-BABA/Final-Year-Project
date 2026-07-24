"""
history.py — Scan history and statistics endpoints.

TODO (Phase 4.3): Implement database queries.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/history", summary="List scan history")
async def get_history(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns paginated scan records, newest first.
    TODO (Phase 4.3): Query scans table with ORDER BY created_at DESC.
    """
    # STUB
    return {"scans": [], "total": 0, "limit": limit, "offset": offset}


@router.get("/stats", summary="Aggregate scan statistics")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    Returns aggregate counts by verdict.
    TODO (Phase 4.3): Run COUNT grouped by verdict.
    """
    # STUB
    return {
        "total_scans": 0,
        "phishing_count": 0,
        "suspicious_count": 0,
        "legitimate_count": 0,
        "avg_confidence_pct": 0,
    }


@router.get("/scan/{scan_id}", summary="Get single scan detail")
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns full scan detail including SHAP values and all signal data.
    TODO (Phase 4.3): Query by scan_id UUID.
    """
    # STUB
    return {"error": "not implemented yet"}

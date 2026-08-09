"""
history.py — Scan history and statistics endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.scan import Scan

router = APIRouter()


@router.get("/history", summary="List scan history")
async def get_history(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Scan).order_by(Scan.created_at.desc()).limit(limit).offset(offset)
    )
    scans = [scan.to_dict() for scan in result.scalars().all()]

    total = await db.scalar(select(func.count()).select_from(Scan)) or 0

    return {"scans": scans, "total": int(total), "limit": limit, "offset": offset}


@router.get("/stats", summary="Aggregate scan statistics")
async def get_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan.verdict, func.count()).group_by(Scan.verdict)
    )
    counts = {verdict: count for verdict, count in result.all()}

    total = await db.scalar(select(func.count()).select_from(Scan)) or 0
    avg_confidence = await db.scalar(select(func.avg(Scan.confidence_pct))) or 0

    return {
        "total_scans": int(total),
        "phishing_count": int(counts.get("phishing", 0)),
        "suspicious_count": int(counts.get("suspicious", 0)),
        "legitimate_count": int(counts.get("legitimate", 0)),
        "avg_confidence_pct": round(float(avg_confidence), 2),
    }


@router.get("/scan/{scan_id}", summary="Get single scan detail")
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    try:
        scan_uuid = uuid.UUID(scan_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scan_id")

    scan = await db.get(Scan, scan_uuid)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return scan.to_dict()

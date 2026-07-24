"""
scan.py — SQLAlchemy ORM model for scan records.
Each row represents one analysis of a URL by the /analyze endpoint.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Scan(Base):
    """Stores one phishing analysis result per URL visit."""

    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    verdict: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "phishing" | "suspicious" | "legitimate"
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_pct: Mapped[int] = mapped_column(Integer, nullable=False)

    # Raw feature dictionaries stored as JSONB
    url_features: Mapped[dict] = mapped_column(JSONB, nullable=True)
    network_signals: Mapped[dict] = mapped_column(JSONB, nullable=True)
    permission_signals: Mapped[dict] = mapped_column(JSONB, nullable=True)

    # SHAP output — list of {feature, value, shap_impact, human_readable}
    shap_values: Mapped[list] = mapped_column(JSONB, nullable=True)

    # Rule-based flags from heuristics engine
    flagged_rules: Mapped[list] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Serialize to a plain dict for API responses."""
        return {
            "scan_id": str(self.id),
            "url": self.url,
            "verdict": self.verdict,
            "risk_score": self.risk_score,
            "confidence_pct": self.confidence_pct,
            "url_features": self.url_features,
            "network_signals": self.network_signals,
            "permission_signals": self.permission_signals,
            "shap_values": self.shap_values,
            "flagged_rules": self.flagged_rules,
            "created_at": self.created_at.isoformat(),
        }

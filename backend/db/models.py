from datetime import datetime
from sqlalchemy import Integer, Text, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Check(Base):
    __tablename__ = "verifyit_ds_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    input_text: Mapped[str] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer)
    verdict: Mapped[str] = mapped_column(Text)
    reasons: Mapped[str] = mapped_column(Text)
    official_source: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    entities: Mapped[str] = mapped_column(Text, default="[]")
    ml_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

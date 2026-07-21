from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PlantZone(Base):
    __tablename__ = "plant_zones"

    __table_args__ = (
        UniqueConstraint(
            "plant_id",
            "zone_id",
            name="uq_plant_zone",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    plant_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    zone_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    zone_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    zone_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    geometry: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    floor_level: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
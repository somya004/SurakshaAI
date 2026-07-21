from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlantZoneBase(BaseModel):
    plant_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    zone_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    zone_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )

    zone_type: str | None = Field(
        default=None,
        max_length=100,
    )

    geometry: dict[str, Any] | None = None

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    floor_level: int | None = None

    description: str | None = None


class PlantZoneCreate(PlantZoneBase):
    pass


class PlantZoneUpdate(BaseModel):
    zone_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    zone_type: str | None = Field(
        default=None,
        max_length=100,
    )

    geometry: dict[str, Any] | None = None

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    floor_level: int | None = None

    description: str | None = None


class PlantZoneResponse(PlantZoneBase):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    created_at: datetime
    updated_at: datetime
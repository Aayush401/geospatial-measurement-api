from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class Measurement(BaseModel):
    supported: bool
    area_sq_m: float | None = None
    area_hectares: float | None = None
    length_m: float | None = None
    perimeter_m: float | None = None
    geodesic_area_sq_m: float | None = None
    geodesic_length_m: float | None = None
    projected_crs: str | None = None
    note: str | None = None

class FeatureResponse(BaseModel):
    index: int
    geometry_type: str | None
    crs: str | None
    properties: dict[str, Any]
    geometry: dict[str, Any] | None = None
    measurement: Measurement

    model_config = ConfigDict(from_attributes=True)

class MeasurementsResponse(BaseModel):
    file_id: str
    crs: str | None
    feature_count: int
    total: int
    features: list[FeatureResponse]

class FileInfo(BaseModel):
    id: str
    filename: str
    feature_count: int | None
    crs: str | None
    status: str
    error: str | None = None
    created_at: datetime
    supported_feature_count: int | None = None
    unsupported_feature_count: int | None = None

    model_config = ConfigDict(from_attributes=True)

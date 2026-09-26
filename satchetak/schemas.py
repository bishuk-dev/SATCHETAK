from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class Sector(StrEnum):
    AGRICULTURE = "agriculture"
    URBAN_LAND = "urban_land"


class DataMode(StrEnum):
    DEMO = "demo"
    LIVE = "live"


class Workflow(StrEnum):
    OBSERVATION_DISCOVERY = "observation_discovery"
    VEGETATION_CHANGE = "vegetation_change"
    GENERIC_LAND_CHANGE = "generic_land_change"


class PolygonGeometry(BaseModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[list[float]]]

    @model_validator(mode="after")
    def validate_polygon(self) -> "PolygonGeometry":
        if not self.coordinates or len(self.coordinates[0]) < 4:
            raise ValueError("AOI exterior ring requires at least four positions")
        ring = self.coordinates[0]
        if ring[0] != ring[-1]:
            raise ValueError("AOI exterior ring must be closed")
        for position in ring:
            if len(position) < 2:
                raise ValueError("every AOI position must contain longitude and latitude")
            lon, lat = position[:2]
            if not -180 <= lon <= 180 or not -90 <= lat <= 90:
                raise ValueError("AOI coordinate is outside WGS84 bounds")
        signed_area = sum(
            ring[index][0] * ring[index + 1][1] - ring[index + 1][0] * ring[index][1]
            for index in range(len(ring) - 1)
        )
        if abs(signed_area) < 1e-12:
            raise ValueError("AOI polygon must enclose a non-zero area")
        return self


class Period(BaseModel):
    start: date = Field(alias="from")
    end: date = Field(alias="to")

    model_config = {"populate_by_name": True, "serialize_by_alias": True}

    @model_validator(mode="after")
    def validate_period(self) -> "Period":
        if self.start >= self.end:
            raise ValueError("period.from must be before period.to")
        if self.end > date.today():
            raise ValueError("period.to cannot be in the future")
        return self


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    sector: Sector = Sector.AGRICULTURE
    aoi: PolygonGeometry
    period: Period


class MonitoredLocation(LocationCreate):
    id: str
    created_at: datetime


class Observation(BaseModel):
    provider: str
    provider_scene_id: str
    satellite: str
    sensor: str
    acquisition_time: datetime
    cloud_cover: float | None
    product_level: str
    bands: list[str]
    crs: str | None
    asset_references: dict[str, str]
    quality_state: str
    source_mode: str


class ObservationSearchRequest(BaseModel):
    aoi: PolygonGeometry
    period: Period
    mode: DataMode = DataMode.DEMO
    max_cloud_cover: float = Field(default=30, ge=0, le=100)


class SelectedPair(BaseModel):
    t1: Observation
    t2: Observation


class ObservationSearchResponse(BaseModel):
    mode: DataMode
    candidates: list[Observation]
    selected: SelectedPair


class AnalysisCreate(BaseModel):
    location_id: str = Field(min_length=1)
    mode: DataMode = DataMode.DEMO
    workflow: Workflow = Workflow.VEGETATION_CHANGE
    assessment_purpose: Literal["agriculture_purchase", "development_purchase"] | None = None


class AnalysisArtifact(BaseModel):
    id: str
    role: Literal["t1", "t2", "change"]
    kind: Literal["true_color", "change_overlay"]
    title: str
    url: str
    media_type: Literal["image/png"] = "image/png"
    coordinates: list[list[float]]
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    acquisition_time: datetime | None = None
    source_mode: str
    description: str
    legend: list[dict[str, str]] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    id: str
    location_id: str
    created_at: datetime
    workflow: Literal["vegetation_change", "generic_land_change"]
    t1: Observation
    t2: Observation
    metrics: dict[str, float | int]
    evidence: dict[str, Any]
    warnings: list[str]
    explanation: str
    explanation_source: str
    interpretation: dict[str, Any] | None = None
    assessment: dict[str, Any] | None = None
    artifacts: list[AnalysisArtifact] = Field(default_factory=list)


class AnalysisList(BaseModel):
    analyses: list[AnalysisResult]


class LocationList(BaseModel):
    locations: list[MonitoredLocation]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str


class QueryPlanRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)


class QueryPlan(BaseModel):
    query: str
    sector: Sector
    workflow: Workflow
    confidence: Literal["high", "medium", "low"]
    recognized_terms: list[str]
    required_bands: list[str]
    requested_outputs: list[str]
    claim_limitations: list[str]
    rationale: str
    assessment_purpose: Literal["agriculture_purchase", "development_purchase"] | None = None


class MonitoringCheckRequest(BaseModel):
    mode: DataMode = DataMode.LIVE


class MonitoringCheckResult(BaseModel):
    location_id: str
    status: Literal["new_observation_available", "up_to_date", "no_previous_analysis"]
    checked_at: datetime
    previous_latest_date: date | None = None
    latest_available_date: date | None = None
    candidate_count: int = 0
    message: str


class PriceComparableCreate(BaseModel):
    transaction_date: date
    total_price: float = Field(gt=0)
    area_ha: float = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    source: str = Field(min_length=2, max_length=200)
    source_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=500)


class PriceComparable(PriceComparableCreate):
    id: str
    location_id: str
    price_per_ha: float
    created_at: datetime


class PriceSummary(BaseModel):
    location_id: str
    comparable_count: int
    currency: str | None = None
    median_price_per_ha: float | None = None
    min_price_per_ha: float | None = None
    max_price_per_ha: float | None = None
    first_to_latest_change_pct: float | None = None
    trend_direction: Literal["up", "down", "flat", "insufficient_data"]
    comparables: list[PriceComparable]
    caveat: str

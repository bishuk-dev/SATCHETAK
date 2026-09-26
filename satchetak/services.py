from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import httpx
import numpy as np
from fastapi import HTTPException

from .analysis import (
    demo_multispectral_bands,
    demo_vegetation_bands,
    generic_land_change,
    real_generic_land_change,
    real_vegetation_change,
    vegetation_change,
)
from .artifacts import ArtifactStore, aoi_image_coordinates, create_raster_artifacts
from .assessment import build_assessment
from .config import settings
from .imagery import demo_observations, search_bhoonidhi, search_copernicus, search_planetary_computer, select_pair
from .interpretation import build_interpretation, build_observation_summary
from .language import explain_with_qwen
from .processing import ProcessingConfigurationError, credentials_configured, fetch_multispectral, fetch_ndvi
from .schemas import AnalysisCreate, AnalysisResult, DataMode, LocationCreate, MonitoredLocation, ObservationSearchRequest, ObservationSearchResponse, Sector, Workflow
from .storage import Store
from .tls import TLSVerificationError


def _temporal_support_candidates(search: ObservationSearchResponse, limit: int = 2):
    """Use quality-qualified intermediate scenes, preferring those nearest T2."""
    candidates = sorted(
        (item for item in search.candidates if item.quality_state == "candidate"),
        key=lambda item: item.acquisition_time,
    )
    return candidates[-limit:]


def create_location(store: Store, request: LocationCreate) -> MonitoredLocation:
    location = MonitoredLocation(**request.model_dump(), id=uuid.uuid4().hex, created_at=datetime.now(UTC))
    store.put("location", location.id, location.model_dump(mode="json", by_alias=True))
    return location


def check_for_new_observations(store: Store, location_id: str, mode: DataMode) -> dict:
    stored = store.get("location", location_id)
    if not stored:
        raise HTTPException(status_code=404, detail="monitored location not found")
    analyses = [item for item in store.list("analysis") if item.get("location_id") == location_id]
    if not analyses:
        return {"location_id": location_id, "status": "no_previous_analysis", "checked_at": datetime.now(UTC), "message": "Run the first analysis before checking for newer observations."}
    previous = max(datetime.fromisoformat(item["t2"]["acquisition_time"].replace("Z", "+00:00")) for item in analyses)
    start = previous.date() + timedelta(days=1)
    today = date.today()
    if start >= today:
        return {"location_id": location_id, "status": "up_to_date", "checked_at": datetime.now(UTC), "previous_latest_date": previous.date(), "latest_available_date": previous.date(), "message": "The saved analysis already uses the latest eligible date."}
    location = MonitoredLocation.model_validate(stored)
    request = ObservationSearchRequest(aoi=location.aoi, period={"from": start, "to": today}, mode=mode)
    try:
        search = search_observations(request)
    except HTTPException as exc:
        if exc.status_code == 422:
            return {"location_id": location_id, "status": "up_to_date", "checked_at": datetime.now(UTC), "previous_latest_date": previous.date(), "message": "No newer quality-qualified observation was found."}
        raise
    latest = search.selected.t2.acquisition_time.date()
    result = {
        "location_id": location_id, "status": "new_observation_available", "checked_at": datetime.now(UTC),
        "previous_latest_date": previous.date(), "latest_available_date": latest,
        "candidate_count": len(search.candidates),
        "message": f"A newer eligible observation is available for {latest.isoformat()}. Run a new analysis to compare it with the saved baseline.",
    }
    store.put("monitoring_check", uuid.uuid4().hex, {key: value.isoformat() if isinstance(value, (date, datetime)) else value for key, value in result.items()})
    return result


def search_observations(request: ObservationSearchRequest) -> ObservationSearchResponse:
    aoi = request.aoi.model_dump()
    period = request.period.model_dump(mode="json", by_alias=True)
    try:
        if request.mode == DataMode.LIVE:
            candidates = []
            errors = []
            try:
                candidates = search_copernicus(aoi, period, request.max_cloud_cover)
            except (RuntimeError, TLSVerificationError) as exc:
                errors.append(str(exc))
            if (
                not candidates and settings.bhoonidhi_user_id and settings.bhoonidhi_password
                and settings.bhoonidhi_collection and "sentinel-2" in settings.bhoonidhi_collection.lower()
            ):
                try:
                    candidates = search_bhoonidhi(aoi, period, settings.bhoonidhi_user_id, settings.bhoonidhi_password, settings.bhoonidhi_collection, request.max_cloud_cover)
                except (RuntimeError, TLSVerificationError) as exc:
                    errors.append(str(exc))
            if not candidates and settings.planetary_computer_enabled:
                try:
                    candidates = search_planetary_computer(aoi, period, request.max_cloud_cover)
                except (RuntimeError, TLSVerificationError) as exc:
                    errors.append(str(exc))
            if not candidates and errors:
                raise RuntimeError("; ".join(errors))
        else:
            candidates = demo_observations(period)
        t1, t2 = select_pair(candidates)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ObservationSearchResponse(mode=request.mode, candidates=candidates, selected={"t1": t1, "t2": t2})


def create_analysis(store: Store, request: AnalysisCreate) -> AnalysisResult:
    stored = store.get("location", request.location_id)
    if not stored:
        raise HTTPException(status_code=404, detail="monitored location not found")
    location = MonitoredLocation.model_validate(stored)
    if request.assessment_purpose:
        required = Workflow.VEGETATION_CHANGE if request.assessment_purpose == "agriculture_purchase" else Workflow.GENERIC_LAND_CHANGE
        if request.workflow != required:
            raise HTTPException(status_code=422, detail="assessment purpose does not match the analysis workflow")
    if request.workflow == Workflow.OBSERVATION_DISCOVERY:
        raise HTTPException(status_code=422, detail="observation discovery does not create an analysis")
    if request.workflow == Workflow.VEGETATION_CHANGE and location.sector != Sector.AGRICULTURE:
        raise HTTPException(status_code=422, detail="vegetation_change requires an agriculture location")
    if request.workflow == Workflow.GENERIC_LAND_CHANGE and location.sector != Sector.URBAN_LAND:
        raise HTTPException(status_code=422, detail="generic_land_change requires an urban_land location")
    if request.mode == DataMode.LIVE and not credentials_configured(settings):
        raise HTTPException(
            status_code=503,
            detail="real pixel analysis requires server-side CDSE_CLIENT_ID and CDSE_CLIENT_SECRET",
        )
    search = search_observations(ObservationSearchRequest(aoi=location.aoi, period=location.period, mode=request.mode))
    t1 = search.selected.t1.model_dump(mode="json")
    t2 = search.selected.t2.model_dump(mode="json")
    analysis_id = uuid.uuid4().hex
    coordinates = aoi_image_coordinates(location.aoi.model_dump())
    if request.mode == DataMode.LIVE:
        try:
            if request.workflow == Workflow.VEGETATION_CHANGE:
                raster1 = fetch_ndvi(location.aoi.model_dump(), search.selected.t1.acquisition_time.isoformat(), settings)
                raster2 = fetch_ndvi(location.aoi.model_dump(), search.selected.t2.acquisition_time.isoformat(), settings)
                result = real_vegetation_change(
                    t1, t2, raster1.ndvi, raster1.valid, raster2.ndvi, raster2.valid,
                    raster1.pixel_area_m2, raster1.crs, raster1.resolution_m,
                )
                bands1, valid1, bands2, valid2 = raster1.bands, raster1.valid, raster2.bands, raster2.valid
                coordinates = raster1.coordinates
            else:
                raster1 = fetch_multispectral(location.aoi.model_dump(), search.selected.t1.acquisition_time.isoformat(), settings)
                raster2 = fetch_multispectral(location.aoi.model_dump(), search.selected.t2.acquisition_time.isoformat(), settings)
                support_rasters = [
                    (
                        observation.acquisition_time.isoformat(),
                        fetch_multispectral(location.aoi.model_dump(), observation.acquisition_time.isoformat(), settings),
                    )
                    for observation in _temporal_support_candidates(search)
                ]
                result = real_generic_land_change(
                    t1, t2, raster1.bands, raster1.valid, raster2.bands, raster2.valid,
                    raster1.pixel_area_m2, raster1.crs, raster1.resolution_m,
                    support_observations=[(date, raster.bands, raster.valid) for date, raster in support_rasters],
                )
                bands1, valid1, bands2, valid2 = raster1.bands, raster1.valid, raster2.bands, raster2.valid
                coordinates = raster1.coordinates
        except ProcessingConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except TLSVerificationError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Copernicus processing request failed: {exc}") from exc
    else:
        if request.workflow == Workflow.VEGETATION_CHANGE:
            result = vegetation_change(location.aoi.model_dump(), t1, t2)
            bands1, bands2 = demo_vegetation_bands(1), demo_vegetation_bands(2)
        else:
            result = generic_land_change(
                location.aoi.model_dump(), t1, t2,
                [item.acquisition_time.isoformat() for item in _temporal_support_candidates(search)],
            )
            bands1, bands2 = demo_multispectral_bands(1), demo_multispectral_bands(2)
        valid1 = np.ones(bands1.shape[1:], dtype=bool)
        valid2 = np.ones(bands2.shape[1:], dtype=bool)
    artifact_store = ArtifactStore(store.path.parent / "artifacts")
    result["evidence"]["observation_summary"] = build_observation_summary(search, request.workflow.value)
    result["interpretation"] = explain_with_qwen(build_interpretation(result), settings)
    result["artifacts"] = create_raster_artifacts(
        store=artifact_store,
        analysis_id=analysis_id,
        result=result,
        bands1=bands1,
        valid1=valid1,
        bands2=bands2,
        valid2=valid2,
        coordinates=coordinates,
    )
    if request.assessment_purpose:
        result["assessment"] = build_assessment(result, request.assessment_purpose)
    analysis = AnalysisResult(**result, id=analysis_id, location_id=location.id, created_at=datetime.now(UTC))
    store.put("analysis", analysis.id, analysis.model_dump(mode="json"))
    return analysis

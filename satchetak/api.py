from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from .artifacts import ArtifactStore
from .config import settings
from .planning import plan_query
from .pricing import add_comparable, price_summary
from .imagery import search_bhoonidhi, search_planetary_computer
from .geocoding import search_places
from .schemas import AnalysisCreate, AnalysisList, AnalysisResult, HealthResponse, LocationCreate, LocationList, MonitoredLocation, MonitoringCheckRequest, MonitoringCheckResult, ObservationSearchRequest, ObservationSearchResponse, PriceComparable, PriceComparableCreate, PriceSummary, QueryPlan, QueryPlanRequest
from .services import check_for_new_observations, create_analysis, create_location, search_observations
from .storage import Store

router = APIRouter(prefix="/api/v1")
store = Store(settings.data_dir / "satchetak.db")


def get_store() -> Store:
    return store


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(version="0.2.0")


@router.get("/capabilities")
def capabilities() -> dict:
    return {
        "analysis": ["vegetation_change", "generic_land_change", "temporal_support"],
        "catalogue_provider_order": ["copernicus_dataspace", "bhoonidhi", "planetary_computer"],
        "copernicus_processing_configured": bool(settings.cdse_client_id and settings.cdse_client_secret),
        "bhoonidhi_configured": bool(settings.bhoonidhi_user_id and settings.bhoonidhi_password and settings.bhoonidhi_collection),
        "planetary_computer_enabled": settings.planetary_computer_enabled,
        "bhuvan_reference_layer_configured": bool(settings.bhuvan_wms_url and settings.bhuvan_wms_layer),
        "qwen_configured": bool(settings.qwen_base_url),
        "qwen_model": settings.qwen_model if settings.qwen_base_url else None,
        "monitoring_check": True,
        "verified_price_comparables": True,
    }


@router.post("/requests/plan", response_model=QueryPlan)
def post_request_plan(request: QueryPlanRequest) -> QueryPlan:
    return plan_query(request.query)


@router.post("/locations", response_model=MonitoredLocation, status_code=status.HTTP_201_CREATED)
def post_location(request: LocationCreate, repository: Store = Depends(get_store)) -> MonitoredLocation:
    return create_location(repository, request)


@router.get("/locations", response_model=LocationList)
def list_locations(repository: Store = Depends(get_store)) -> LocationList:
    return LocationList(locations=repository.list("location"))


@router.get("/geocoding/search")
def search_locations(q: str = Query(min_length=2, max_length=200)) -> dict:
    try:
        return {"results": search_places(q)}
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/locations/{location_id}", response_model=MonitoredLocation)
def get_location(location_id: str, repository: Store = Depends(get_store)) -> MonitoredLocation:
    value = repository.get("location", location_id)
    if not value:
        raise HTTPException(status_code=404, detail="monitored location not found")
    return MonitoredLocation.model_validate(value)


@router.get("/locations/{location_id}/analyses", response_model=AnalysisList)
def list_location_analyses(location_id: str, repository: Store = Depends(get_store)) -> AnalysisList:
    if not repository.get("location", location_id):
        raise HTTPException(status_code=404, detail="monitored location not found")
    analyses = [AnalysisResult.model_validate(value) for value in repository.list("analysis") if value.get("location_id") == location_id]
    return AnalysisList(analyses=analyses)


@router.post("/locations/{location_id}/monitor/check", response_model=MonitoringCheckResult)
def post_monitoring_check(location_id: str, request: MonitoringCheckRequest, repository: Store = Depends(get_store)) -> MonitoringCheckResult:
    return MonitoringCheckResult.model_validate(check_for_new_observations(repository, location_id, request.mode))


@router.post("/locations/{location_id}/price-comparables", response_model=PriceComparable, status_code=status.HTTP_201_CREATED)
def post_price_comparable(location_id: str, request: PriceComparableCreate, repository: Store = Depends(get_store)) -> PriceComparable:
    return add_comparable(repository, location_id, request)


@router.get("/locations/{location_id}/price-summary", response_model=PriceSummary)
def get_price_summary(location_id: str, repository: Store = Depends(get_store)) -> PriceSummary:
    return price_summary(repository, location_id)


@router.post("/observations/search", response_model=ObservationSearchResponse)
def post_observation_search(request: ObservationSearchRequest) -> ObservationSearchResponse:
    return search_observations(request)


@router.post("/providers/{provider}/search")
def post_provider_search(provider: str, request: ObservationSearchRequest) -> dict:
    aoi = request.aoi.model_dump()
    period = request.period.model_dump(mode="json", by_alias=True)
    if provider == "planetary_computer":
        candidates = search_planetary_computer(aoi, period, request.max_cloud_cover)
    elif provider == "bhoonidhi":
        if not (settings.bhoonidhi_user_id and settings.bhoonidhi_password and settings.bhoonidhi_collection):
            raise HTTPException(status_code=503, detail="Bhoonidhi requires BHOONIDHI_USER_ID, BHOONIDHI_PASSWORD, and BHOONIDHI_COLLECTION")
        candidates = search_bhoonidhi(aoi, period, settings.bhoonidhi_user_id, settings.bhoonidhi_password, settings.bhoonidhi_collection, request.max_cloud_cover)
    else:
        raise HTTPException(status_code=404, detail="unknown imagery provider")
    return {"provider": provider, "candidate_count": len(candidates), "candidates": candidates}


@router.post("/analyses", response_model=AnalysisResult, status_code=status.HTTP_201_CREATED)
def post_analysis(request: AnalysisCreate, repository: Store = Depends(get_store)) -> AnalysisResult:
    return create_analysis(repository, request)


@router.get("/analyses/{analysis_id}", response_model=AnalysisResult)
def get_analysis(analysis_id: str, repository: Store = Depends(get_store)) -> AnalysisResult:
    value = repository.get("analysis", analysis_id)
    if not value:
        raise HTTPException(status_code=404, detail="analysis not found")
    return AnalysisResult.model_validate(value)


@router.get("/analyses/{analysis_id}/artifacts/{artifact_id}", response_class=FileResponse)
def get_analysis_artifact(analysis_id: str, artifact_id: str, repository: Store = Depends(get_store)) -> FileResponse:
    value = repository.get("analysis", analysis_id)
    if not value:
        raise HTTPException(status_code=404, detail="analysis not found")
    artifact = next((item for item in value.get("artifacts", []) if item.get("id") == artifact_id), None)
    if not artifact:
        raise HTTPException(status_code=404, detail="analysis artifact not found")
    path = ArtifactStore(repository.path.parent / "artifacts").path(analysis_id, artifact_id)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="analysis artifact file not found")
    return FileResponse(path, media_type=artifact["media_type"], headers={"Cache-Control": "public, max-age=31536000, immutable"})

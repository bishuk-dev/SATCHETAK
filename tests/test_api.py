from pathlib import Path

from fastapi.testclient import TestClient

from satchetak.api import get_store
from satchetak.main import app
from satchetak.storage import Store

AOI = {"type": "Polygon", "coordinates": [[[77.55, 12.92], [77.565, 12.92], [77.565, 12.932], [77.55, 12.932], [77.55, 12.92]]]}
PERIOD = {"from": "2025-01-01", "to": "2025-06-30"}


def test_location_to_analysis_http_flow(tmp_path: Path):
    app.dependency_overrides[get_store] = lambda: Store(tmp_path / "api.db")
    try:
        with TestClient(app) as client:
            location_response = client.post("/api/v1/locations", json={"name": "Test farm", "sector": "agriculture", "aoi": AOI, "period": PERIOD})
            assert location_response.status_code == 201
            analysis_response = client.post("/api/v1/analyses", json={"location_id": location_response.json()["id"], "mode": "demo"})
            assert analysis_response.status_code == 201
            assert analysis_response.json()["metrics"]["decline_pixel_count"] == 90
            history = client.get(f"/api/v1/locations/{location_response.json()['id']}/analyses")
            assert history.status_code == 200
            assert history.json()["analyses"][0]["id"] == analysis_response.json()["id"]
    finally:
        app.dependency_overrides.clear()


def test_geocoded_location_name_can_use_full_display_name(tmp_path: Path):
    app.dependency_overrides[get_store] = lambda: Store(tmp_path / "geocoded.db")
    try:
        with TestClient(app) as client:
            long_name = "SelaQui International School, NH7, Hasanpur, Central Hope Town, Vikasnagar, Dehradun, Uttarakhand, 248197, India"
            response = client.post("/api/v1/locations", json={"name": long_name, "sector": "agriculture", "aoi": AOI, "period": PERIOD})
            assert response.status_code == 201
            assert response.json()["name"] == long_name
    finally:
        app.dependency_overrides.clear()


def test_openapi_exposes_core_routes():
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
    assert "/api/v1/locations" in schema["paths"]
    assert "/api/v1/geocoding/search" in schema["paths"]
    assert "/api/v1/observations/search" in schema["paths"]
    assert "/api/v1/analyses" in schema["paths"]
    assert "/api/v1/locations/{location_id}/analyses" in schema["paths"]
    assert "/api/v1/locations/{location_id}/monitor/check" in schema["paths"]
    assert "/api/v1/locations/{location_id}/price-summary" in schema["paths"]


def test_monitoring_and_verified_price_evidence(tmp_path: Path):
    app.dependency_overrides[get_store] = lambda: Store(tmp_path / "decision.db")
    try:
        with TestClient(app) as client:
            location = client.post("/api/v1/locations", json={"name": "Tracked land", "sector": "urban_land", "aoi": AOI, "period": PERIOD}).json()
            client.post("/api/v1/analyses", json={"location_id": location["id"], "mode": "demo", "workflow": "generic_land_change"})
            monitoring = client.post(f"/api/v1/locations/{location['id']}/monitor/check", json={"mode": "demo"})
            assert monitoring.status_code == 200
            assert monitoring.json()["status"] == "new_observation_available"
            for when, price in [("2025-01-01", 10_000_000), ("2025-06-01", 12_000_000)]:
                response = client.post(f"/api/v1/locations/{location['id']}/price-comparables", json={
                    "transaction_date": when, "total_price": price, "area_ha": 2, "currency": "INR", "source": "Verified registry fixture",
                })
                assert response.status_code == 201
            summary = client.get(f"/api/v1/locations/{location['id']}/price-summary").json()
            assert summary["comparable_count"] == 2
            assert summary["median_price_per_ha"] == 5_500_000
            assert summary["first_to_latest_change_pct"] == 20
            assert summary["trend_direction"] == "up"
            capabilities = client.get("/api/v1/capabilities").json()
            assert capabilities["verified_price_comparables"] is True
            assert capabilities["catalogue_provider_order"] == ["copernicus_dataspace", "bhoonidhi", "planetary_computer"]
    finally:
        app.dependency_overrides.clear()


def test_live_analysis_requires_server_credentials_before_network(tmp_path: Path):
    app.dependency_overrides[get_store] = lambda: Store(tmp_path / "live.db")
    try:
        with TestClient(app) as client:
            location = client.post("/api/v1/locations", json={"name": "Test farm", "sector": "agriculture", "aoi": AOI, "period": PERIOD}).json()
            response = client.post("/api/v1/analyses", json={"location_id": location["id"], "mode": "live"})
        assert response.status_code == 503
        assert "CDSE_CLIENT_ID" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_query_planned_generic_land_change_demo(tmp_path: Path):
    app.dependency_overrides[get_store] = lambda: Store(tmp_path / "land.db")
    try:
        with TestClient(app) as client:
            plan = client.post("/api/v1/requests/plan", json={"query": "Where has urban land changed?"})
            assert plan.status_code == 200
            assert plan.json()["workflow"] == "generic_land_change"
            location = client.post("/api/v1/locations", json={"name": "Urban edge", "sector": "urban_land", "aoi": AOI, "period": PERIOD}).json()
            analysis = client.post("/api/v1/analyses", json={"location_id": location["id"], "mode": "demo", "workflow": "generic_land_change"})
            assert analysis.status_code == 201
            body = analysis.json()
            assert body["workflow"] == "generic_land_change"
            assert body["metrics"]["changed_area_ha"] > 0
            assert body["metrics"]["changed_share_pct"] > 0
            assert body["evidence"]["bands"] == ["B02", "B03", "B04", "B08", "B11", "B12"]
            assert body["metrics"]["vegetation_to_bare_area_ha"] > 0
            assert body["metrics"]["built_up_like_area_ha"] > 0
            assert body["metrics"]["change_region_count"] >= 2
            assert body["metrics"]["temporal_observation_count"] == 4
            assert body["metrics"]["repeat_observed_area_ha"] > 0
            assert body["metrics"]["latest_only_area_ha"] > 0
            assert "meaningful change regions" in body["explanation"]
            assert body["evidence"]["change_regions"][0]["location"]
            assert {region["temporal_status"] for region in body["evidence"]["change_regions"]} == {"repeated", "latest_only"}
            assert len(body["evidence"]["observation_dates"]) == 4
            assert any(effect["area_ha"] > 0 for effect in body["evidence"]["observable_effects"])
            assert body["evidence"]["observation_summary"]["qualified_count"] == 4
            assert body["evidence"]["observation_summary"]["rejected_count"] == 1
            assert body["evidence"]["observation_summary"]["intermediate_support_count"] == 2
            assert body["interpretation"]["source"] == "deterministic_verified_evidence"
            assert "41.23 ha" in body["interpretation"]["direct_answer"]
            assert body["interpretation"]["evidence_points"]
            assert body["interpretation"]["decision_relevance"]
            assert [artifact["role"] for artifact in body["artifacts"]] == ["t1", "t2", "change"]
            overlay = client.get(body["artifacts"][2]["url"])
            assert overlay.status_code == 200
            assert overlay.headers["content-type"] == "image/png"
            assert overlay.content.startswith(b"\x89PNG\r\n\x1a\n")
            assert client.get(f"/api/v1/analyses/{body['id']}/artifacts/not-present").status_code == 404
    finally:
        app.dependency_overrides.clear()

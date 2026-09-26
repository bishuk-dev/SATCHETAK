import numpy as np
import pytest
from fastapi.testclient import TestClient

from satchetak.api import get_store
from satchetak.main import app
from satchetak.analysis import real_vegetation_change
from satchetak.assessment import build_assessment
from satchetak.planning import plan_query
from satchetak.storage import Store

AOI = {"type": "Polygon", "coordinates": [[[77.55, 12.92], [77.565, 12.92], [77.565, 12.932], [77.55, 12.932], [77.55, 12.92]]]}


@pytest.mark.parametrize("query,purpose,sector", [
    ("Is this land worth buying for agricultural purpose?", "agriculture_purchase", "agriculture"),
    ("Assess this land purchase for commercial development", "development_purchase", "urban_land"),
])
def test_purchase_screen_reachable_and_persisted(tmp_path, query, purpose, sector):
    app.dependency_overrides[get_store] = lambda: Store(tmp_path / "assessment.db")
    try:
        with TestClient(app) as client:
            plan = client.post('/api/v1/requests/plan', json={"query": query}).json()
            assert plan['assessment_purpose'] == purpose
            assert plan['sector'] == sector
            location = client.post('/api/v1/locations', json={"name": "Purchase screen", "sector": sector, "aoi": AOI, "period": {"from": "2025-01-01", "to": "2025-06-30"}}).json()
            response = client.post('/api/v1/analyses', json={"location_id": location['id'], "mode": "demo", "workflow": plan['workflow'], "assessment_purpose": purpose})
            assert response.status_code == 201
            result = response.json()
            report = result['assessment']
            assert report['status'] == 'demo_only'
            assert 'simulated' in report['conclusion']
            assert all(check['status'] == 'not_assessed' for check in report['missing_checks'])
            assert client.get('/api/v1/analyses/' + result['id']).json()['assessment'] == report
            mismatch = client.post('/api/v1/analyses', json={"location_id": location['id'], "workflow": plan['workflow'], "assessment_purpose": 'development_purchase' if sector == 'agriculture' else 'agriculture_purchase'})
            assert mismatch.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_vegetation_statistics_exclude_invalid_pixels_and_cannot_prove_suitability():
    first = np.array([[0.6, 0.6], [0.6, 0.6]])
    second = np.array([[0.2, 0.6], [0.9, 99.0]])
    valid = np.array([[True, True], [True, False]])
    result = real_vegetation_change({}, {}, first, valid, second, valid, 100, 'EPSG:32643', 10)
    metrics = result['metrics']
    assert metrics['valid_pixel_count'] == 3
    assert metrics['ndvi_t2_median'] == 0.6
    assert metrics['ndvi_t2_p90'] < 1
    assert metrics['decline_share_pct'] == 33.33
    assert metrics['increase_share_pct'] == 33.33
    report = build_assessment(result, 'agriculture_purchase')
    assert report['status'] == 'insufficient_evidence'
    assert any(check['name'] == 'Soil' for check in report['missing_checks'])


def test_agricultural_condition_query_runs_supported_measurements():
    assert plan_query('Analyze vegetation condition in this field').workflow == 'vegetation_change'

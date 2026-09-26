import tempfile
import unittest
from pathlib import Path

import numpy as np

from satchetak.analysis import _clean_regions, real_vegetation_change, vegetation_change
from satchetak.imagery import demo_observations, select_pair
from satchetak.schemas import LocationCreate, PolygonGeometry
from satchetak.storage import Store
from pydantic import ValidationError


AOI = {"type": "Polygon", "coordinates": [[[77.55, 12.92], [77.565, 12.92], [77.565, 12.932], [77.55, 12.932], [77.55, 12.92]]]}
PERIOD = {"from": "2025-01-01", "to": "2025-06-30"}


class ContractTests(unittest.TestCase):
    def test_closed_polygon_is_required(self):
        with self.assertRaises(ValidationError):
            PolygonGeometry.model_validate({"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]]})

    def test_location_contract(self):
        value = LocationCreate.model_validate({"name": "Farm", "sector": "agriculture", "aoi": AOI, "period": PERIOD})
        self.assertEqual(value.sector.value, "agriculture")

    def test_zero_area_polygon_is_rejected(self):
        with self.assertRaises(ValidationError):
            PolygonGeometry.model_validate({"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [2, 2], [0, 0]]]})


class WorkflowTests(unittest.TestCase):
    def test_land_change_regions_remove_isolated_speckle(self):
        classification = np.zeros((6, 6), dtype=np.uint8)
        classification[0, 0] = 2
        classification[3:5, 3:5] = 2
        cleaned, regions, minimum_pixels = _clean_regions(classification, 400)
        self.assertEqual(minimum_pixels, 3)
        self.assertEqual(cleaned[0, 0], 0)
        self.assertEqual(int((cleaned == 2).sum()), 4)
        self.assertEqual(regions[0]["area_ha"], 0.16)

    def test_pair_rejects_cloudy_middle_scene(self):
        scenes = demo_observations(PERIOD)
        t1, t2 = select_pair(scenes)
        self.assertEqual(t1["quality_state"], "selected_t1")
        self.assertEqual(t2["quality_state"], "selected_t2")
        self.assertLess(t1["acquisition_time"], t2["acquisition_time"])

    def test_evidence_is_computed_from_grids(self):
        t1, t2 = select_pair(demo_observations(PERIOD))
        result = vegetation_change(AOI, t1, t2)
        self.assertEqual(result["evidence"]["grid_size"], 24)
        self.assertGreater(result["metrics"]["decline_pixel_count"], 0)
        self.assertGreater(result["metrics"]["vegetation_decline_area_ha_estimate"], 0)
        self.assertEqual(result["explanation_source"], "deterministic_template")

    def test_store_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "test.db")
            store.put("location", "1", {"id": "1"})
            self.assertEqual(store.get("location", "1"), {"id": "1"})

    def test_real_raster_metrics_use_only_mutually_valid_pixels(self):
        t1, t2 = select_pair(demo_observations(PERIOD))
        ndvi1 = np.array([[0.6, 0.5], [0.2, 0.1]], dtype=np.float32)
        ndvi2 = np.array([[0.3, 0.7], [0.2, 0.8]], dtype=np.float32)
        valid1 = np.array([[True, True], [True, False]])
        valid2 = np.array([[True, True], [False, True]])
        result = real_vegetation_change(t1, t2, ndvi1, valid1, ndvi2, valid2, 100, "EPSG:32643", 10)
        self.assertEqual(result["metrics"]["valid_pixel_count"], 2)
        self.assertEqual(result["metrics"]["vegetation_decline_area_ha"], 0.01)
        self.assertEqual(result["metrics"]["vegetation_increase_area_ha"], 0.01)
        self.assertEqual(result["evidence"]["source_mode"], "live_processing_api")


if __name__ == "__main__":
    unittest.main()

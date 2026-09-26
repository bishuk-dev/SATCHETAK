import numpy as np
import pytest

from satchetak.config import Settings
from satchetak import processing
from satchetak.processing import ProcessingConfigurationError, _ProcessResult, _utm_epsg, credentials_configured

AOI = {"type": "Polygon", "coordinates": [[[77.55, 12.92], [77.565, 12.92], [77.565, 12.932], [77.55, 12.932], [77.55, 12.92]]]}


def test_bengaluru_aoi_uses_utm_zone_43_north():
    assert _utm_epsg(AOI) == 32643


def test_missing_credentials_are_explicit(tmp_path):
    settings = Settings(data_dir=tmp_path, cors_origins=(), cdse_client_id=None, cdse_client_secret=None)
    assert credentials_configured(settings) is False
    from satchetak.processing import _access_token
    with pytest.raises(ProcessingConfigurationError, match="CDSE_CLIENT_ID"):
        _access_token(settings)


def test_ndvi_processing_separates_four_display_bands_from_mask(monkeypatch, tmp_path):
    data = np.ones((5, 2, 3), dtype=np.float32)
    data[2] = 0.2
    data[3] = 0.6
    data[4, 0, 0] = 0
    monkeypatch.setattr(processing, "_process_raster", lambda *args, **kwargs: _ProcessResult(data, 100, "EPSG:32643", 10, []))
    result = processing.fetch_ndvi(AOI, "2025-01-01T00:00:00Z", Settings(data_dir=tmp_path))
    assert result.bands.shape == (4, 2, 3)
    assert result.ndvi.shape == (2, 3)
    assert not result.valid[0, 0]
    assert result.valid[1, 1]


def test_multispectral_processing_keeps_all_six_bands_and_last_mask(monkeypatch, tmp_path):
    data = np.ones((7, 2, 3), dtype=np.float32)
    data[6, 1, 2] = 0
    monkeypatch.setattr(processing, "_process_raster", lambda *args, **kwargs: _ProcessResult(data, 100, "EPSG:32643", 10, []))
    result = processing.fetch_multispectral(AOI, "2025-01-01T00:00:00Z", Settings(data_dir=tmp_path))
    assert result.bands.shape == (6, 2, 3)
    assert not result.valid[1, 2]
    assert result.valid[0, 0]

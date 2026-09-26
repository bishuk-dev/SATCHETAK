from satchetak import imagery


AOI = {"type": "Polygon", "coordinates": [[[77.55, 12.92], [77.565, 12.92], [77.565, 12.932], [77.55, 12.932], [77.55, 12.92]]]}
PERIOD = {"from": "2025-01-01", "to": "2025-06-30"}


def test_planetary_computer_stac_is_normalized(monkeypatch):
    monkeypatch.setattr(imagery, "_post_json", lambda *args, **kwargs: {"features": [{
        "id": "S2_TEST", "properties": {"datetime": "2025-02-01T05:00:00Z", "eo:cloud_cover": 4.2, "platform": "sentinel-2b", "proj:epsg": 32643},
        "assets": {"B02": {"href": "blue.tif"}, "B03": {"href": "green.tif"}, "B04": {"href": "red.tif"}, "B08": {"href": "nir.tif"}, "B11": {"href": "swir.tif"}, "B12": {"href": "swir2.tif"}},
    }]})
    result = imagery.search_planetary_computer(AOI, PERIOD)
    assert result[0]["provider"] == "planetary_computer"
    assert result[0]["bands"] == ["B02", "B03", "B04", "B08", "B11", "B12"]
    assert result[0]["crs"] == "EPSG:32643"

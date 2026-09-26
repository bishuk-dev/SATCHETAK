from satchetak.geocoding import _result


def test_nominatim_result_becomes_map_bounds():
    result = _result({
        "display_name": "Bengaluru, Karnataka, India",
        "lat": "12.9767936",
        "lon": "77.590082",
        "boundingbox": ["12.8340125", "13.1436649", "77.4601025", "77.7840515"],
        "type": "city",
    })
    assert result["bounds"] == {"west": 77.4601025, "south": 12.8340125, "east": 77.7840515, "north": 13.1436649}
    assert result["display_name"].startswith("Bengaluru")

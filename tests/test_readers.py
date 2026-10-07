from app.services.readers import parse_kml, parse_shapefile_zip


def test_parse_shapefile_zip(sample_shapefile_zip):
    parsed = parse_shapefile_zip(sample_shapefile_zip)
    assert len(parsed.features) == 1
    assert parsed.crs.to_string() == "EPSG:4326"

def test_parse_kml(sample_kml):
    parsed = parse_kml(sample_kml)
    assert len(parsed.features) == 1
    assert parsed.crs.to_string() == "EPSG:4326"

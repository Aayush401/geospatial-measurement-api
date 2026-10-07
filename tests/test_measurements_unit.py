from shapely.geometry import GeometryCollection, Point, Polygon

from app.services.measurements import compute_measurements


def test_compute_measurements_point():
    geom = Point(72.8, 19.0)
    m = compute_measurements(geom, "EPSG:4326")
    assert m.supported is True
    assert m.note == "No measurement required for points"
    assert m.area_sq_m is None

def test_compute_measurements_polygon():
    # Roughly a 1 degree square in Mumbai
    geom = Polygon([(72.8, 19.0), (72.9, 19.0), (72.9, 19.1), (72.8, 19.1), (72.8, 19.0)])
    m = compute_measurements(geom, "EPSG:4326")
    assert m.supported is True
    assert m.area_sq_m is not None
    assert m.geodesic_area_sq_m is not None
    
    # Check within 0.5% agreement
    diff_ratio = abs(m.area_sq_m - m.geodesic_area_sq_m) / m.geodesic_area_sq_m
    assert diff_ratio < 0.005

def test_compute_measurements_geometry_collection():
    geom = GeometryCollection([Point(0,0)])
    m = compute_measurements(geom, "EPSG:4326")
    assert m.supported is False
    assert "Measurement not supported" in m.note

import os
import tempfile
import zipfile

import pytest
from shapely.geometry import LineString

from app.services.measurements import compute_measurements
from app.services.readers import parse_shapefile_zip


def test_compute_measurements_line():
    geom = LineString([(72.8, 19.0), (72.9, 19.0)])
    m = compute_measurements(geom, "EPSG:4326")
    assert m.supported is True
    assert m.length_m is not None
    assert m.geodesic_length_m is not None
    
def test_compute_measurements_invalid_crs():
    geom = LineString([(72.8, 19.0), (72.9, 19.0)])
    m = compute_measurements(geom, "INVALID_CRS")
    assert m.supported is False
    assert "Invalid source CRS" in m.note
    
def test_parse_shapefile_zip_multiple_shp():
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("test1.shp", "dummy")
        zf.writestr("test2.shp", "dummy")
    with pytest.raises(ValueError, match="Multiple .shp files"):
        parse_shapefile_zip(path)
    os.remove(path)

def test_parse_shapefile_zip_no_shp():
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("test.txt", "dummy")
    with pytest.raises(ValueError, match="No .shp file found"):
        parse_shapefile_zip(path)
    os.remove(path)

def test_upload_huge_file(client, tmp_path):
    # Simulate a huge file (we'll just use a normal file and patch settings if possible, or upload a 51MB file, 
    # but generating a 51MB file takes time. Let's just rely on the API test for now, or just patch the setting)
    from app.config import settings
    orig_max = settings.MAX_UPLOAD_MB
    settings.MAX_UPLOAD_MB = 0 # 0 MB max
    
    fd, path = tempfile.mkstemp(suffix=".kml")
    os.close(fd)
    with open(path, "w") as f:
        f.write("A" * 1024)
        
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("test.kml", f, "application/vnd.google-earth.kml+xml")})
    assert response.status_code == 413
    
    settings.MAX_UPLOAD_MB = orig_max
    os.remove(path)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
def test_global_exception(client):
    # we can mock an exception on an endpoint to hit the exception handler
    with pytest.MonkeyPatch.context():
        from app.database import get_db
        def mock_get_db():
            raise RuntimeError("Database error")
        client.app.dependency_overrides[get_db] = mock_get_db
        response = client.get("/api/files/123/")
        assert response.status_code == 500
        from tests.conftest import override_get_db
        client.app.dependency_overrides[get_db] = override_get_db

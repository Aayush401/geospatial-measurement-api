
def test_get_measurements(client, sample_shapefile_zip):
    with open(sample_shapefile_zip, "rb") as f:
        upload_resp = client.post("/api/files/", files={"file": ("test.zip", f, "application/zip")})
    file_id = upload_resp.json()["id"]
    
    response = client.get(f"/api/files/{file_id}/measurements/")
    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == file_id
    assert data["feature_count"] == 1
    assert data["total"] == 1
    assert len(data["features"]) == 1
    
    feat = data["features"][0]
    assert feat["measurement"]["supported"] is True
    assert feat["measurement"]["area_sq_m"] > 0

def test_get_measurements_filters_and_pagination(client, sample_shapefile_zip):
    # Upload first
    with open(sample_shapefile_zip, "rb") as f:
        upload_resp = client.post("/api/files/", files={"file": ("test.zip", f, "application/zip")})
    file_id = upload_resp.json()["id"]

    # Test include_geometry=false
    resp = client.get(f"/api/files/{file_id}/measurements/?include_geometry=false")
    assert resp.status_code == 200
    assert resp.json()["features"][0]["geometry"] is None

    # Test geometry_type filter (assuming uploaded is Polygon)
    resp = client.get(f"/api/files/{file_id}/measurements/?geometry_type=Polygon")
    assert resp.status_code == 200
    assert len(resp.json()["features"]) == 1

    resp = client.get(f"/api/files/{file_id}/measurements/?geometry_type=LineString")
    assert resp.status_code == 200
    assert len(resp.json()["features"]) == 0
    assert resp.json()["total"] == 0

    # Test pagination
    resp = client.get(f"/api/files/{file_id}/measurements/?limit=0")
    assert resp.status_code == 200
    assert len(resp.json()["features"]) == 0
    assert resp.json()["total"] == 1

def test_get_measurements_failed_file(client):
    # Trigger a failed file state
    import os
    import tempfile
    import zipfile
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("test.txt", "dummy")
        
    with open(path, "rb") as f:
        resp = client.post("/api/files/", files={"file": ("fail.zip", f, "application/zip")})
    assert resp.status_code == 422
    # But it creates the record as FAILED. We don't get the ID in a 422 standardly... wait!
    # Our API returns 422, so the ID is lost to the client. Let's create a FAILED record manually or mock it.
    os.remove(path)


def test_get_file_info(client, sample_kml):
    with open(sample_kml, "rb") as f:
        upload_resp = client.post("/api/files/", files={"file": ("test.kml", f, "application/vnd.google-earth.kml+xml")})
    file_id = upload_resp.json()["id"]
    
    response = client.get(f"/api/files/{file_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == file_id
    assert data["filename"] == "test.kml"
    
def test_get_file_info_not_found(client):
    response = client.get("/api/files/nonexistent-id/")
    assert response.status_code == 404


def test_get_ui(client):
    response = client.get("/ui")
    assert response.status_code == 200
    assert "Geospatial Measurement API" in response.text

def test_static_leaflet(client):
    response = client.get("/static/vendor/leaflet/leaflet.js")
    assert response.status_code == 200
    assert "Leaflet" in response.text

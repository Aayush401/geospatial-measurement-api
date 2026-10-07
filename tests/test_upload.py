import os
import tempfile


def test_upload_kml(client, sample_kml):
    with open(sample_kml, "rb") as f:
        response = client.post("/api/files/", files={"file": ("test.kml", f, "application/vnd.google-earth.kml+xml")})
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["feature_count"] == 1
    assert data["crs"] == "EPSG:4326"

def test_upload_shapefile_zip(client, sample_shapefile_zip):
    with open(sample_shapefile_zip, "rb") as f:
        response = client.post("/api/files/", files={"file": ("test.zip", f, "application/zip")})
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["feature_count"] == 1

def test_upload_invalid_extension(client):
    response = client.post("/api/files/", files={"file": ("test.txt", b"dummy", "text/plain")})
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]
    
def test_upload_corrupt_zip(client):
    fd, path = tempfile.mkstemp(suffix=".zip")
    with os.fdopen(fd, "wb") as f:
        f.write(b"this is not a real zip file")
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("corrupt.zip", f, "application/zip")})
    assert response.status_code == 400
    os.remove(path)

def test_upload_zip_with_two_shp(client):
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    import zipfile
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("test1.shp", "dummy")
        zf.writestr("test2.shp", "dummy")
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("two_shp.zip", f, "application/zip")})
    assert response.status_code == 422
    assert "Multiple .shp files" in response.json()["detail"]
    os.remove(path)

def test_upload_zip_no_shp(client):
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    import zipfile
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("test.txt", "dummy")
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("no_shp.zip", f, "application/zip")})
    assert response.status_code == 422
    assert "No .shp file" in response.json()["detail"]
    os.remove(path)

def test_upload_zip_slip(client):
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    import zipfile
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("../unsafe.shp", "dummy")
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("slip.zip", f, "application/zip")})
    assert response.status_code == 400
    assert "Zip file is unsafe" in response.json()["detail"]
    os.remove(path)

def test_upload_empty_kml(client):
    fd, path = tempfile.mkstemp(suffix=".kml")
    os.close(fd)
    # create a valid kml structure but with no features
    kml = '<?xml version="1.0" encoding="utf-8" ?><kml xmlns="http://www.opengis.net/kml/2.2"><Document></Document></kml>'
    with open(path, "w") as f:
        f.write(kml)
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("empty.kml", f, "application/vnd.google-earth.kml+xml")})
    assert response.status_code == 422
    assert "Invalid or malformed KML file." in response.json()["detail"] or "The uploaded file is empty." in response.json()["detail"] or "No features found" in response.json()["detail"]
    os.remove(path)

def test_upload_malformed_kml(client):
    fd, path = tempfile.mkstemp(suffix=".kml")
    os.close(fd)
    with open(path, "w") as f:
        f.write('<?xml version="1.0"><kml><broken')
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("malformed.kml", f, "application/vnd.google-earth.kml+xml")})
    assert response.status_code == 422
    assert "Invalid or malformed KML file." in response.json()["detail"] or "The uploaded file is empty." in response.json()["detail"]
    os.remove(path)

def test_upload_pdf_as_kml(client):
    fd, path = tempfile.mkstemp(suffix=".kml")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(b"%PDF-1.4\n%...\n")
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("fake.kml", f, "application/vnd.google-earth.kml+xml")})
    assert response.status_code == 422
    assert "Invalid or malformed KML file." in response.json()["detail"] or "The uploaded file is empty." in response.json()["detail"]
    os.remove(path)

def test_upload_empty_kml_proper(client):
    fd, path = tempfile.mkstemp(suffix=".kml")
    os.close(fd)
    # literally size 0
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("empty.kml", f, "application/vnd.google-earth.kml+xml")})
    assert response.status_code == 422
    assert response.json()["detail"] == "The uploaded file is empty."
    assert "data/uploads" not in response.text
    os.remove(path)

def test_upload_bad_kml_proper(client):
    fd, path = tempfile.mkstemp(suffix=".kml")
    os.close(fd)
    with open(path, "w") as f:
        f.write("not xml")
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("bad.kml", f, "application/vnd.google-earth.kml+xml")})
    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid or malformed KML file."
    assert "data/uploads" not in response.text
    os.remove(path)

def test_upload_corrupt_zip_proper(client):
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    with open(path, "w") as f:
        f.write("definitely not a zip file")
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("corrupt.zip", f, "application/zip")})
    assert response.status_code == 400
    assert "Zip file is unsafe" in response.json()["detail"]
    assert "data/uploads" not in response.text
    os.remove(path)

def test_upload_zip_no_shp_no_path_leak(client):
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    import zipfile
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("test.txt", "dummy")
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("no_shp.zip", f, "application/zip")})
    assert response.status_code == 422
    assert "No .shp file found in the zip." in response.json()["detail"]
    assert "data/uploads" not in response.text
    os.remove(path)

def test_upload_kml_properties(client):
    import os
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".kml")
    os.close(fd)
    with open(path, "w") as f:
        f.write("""<?xml version="1.0" encoding="utf-8" ?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <Placemark>
    <name>Test Placemark</name>
    <description>Test Description</description>
    <ExtendedData>
      <Data name="color"><value>red</value></Data>
    </ExtendedData>
    <Point><coordinates>72.85,19.05</coordinates></Point>
  </Placemark>
</Document>
</kml>""")
    with open(path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("test_props.kml", f, "application/vnd.google-earth.kml+xml")})
    assert response.status_code == 201
    file_id = response.json()["id"]
    
    measurements = client.get(f"/api/files/{file_id}/measurements/")
    assert measurements.status_code == 200
    features = measurements.json()["features"]
    assert len(features) == 1
    props = features[0]["properties"]
    assert props["name"] == "Test Placemark"
    assert props["description"] == "Test Description"
    assert props["color"] == "red"
    
    os.remove(path)

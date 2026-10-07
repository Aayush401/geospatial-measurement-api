from app.database import get_db
from app.models import UploadedFile


def test_get_measurements_failed_file_db(client):
    # Inject a FAILED file into DB directly
    db = next(client.app.dependency_overrides[get_db]())
    failed_file = UploadedFile(
        id="failed-123",
        filename="failed.zip",
        file_type="shapefile",
        status="FAILED",
        stored_path="/dummy"
    )
    db.add(failed_file)
    db.commit()

    resp = client.get("/api/files/failed-123/measurements/")
    assert resp.status_code == 409
    assert "File status is FAILED" in resp.json()["detail"]

# Geospatial Measurement API

A production-ready FastAPI backend that accepts geospatial files (Shapefile zip or KML), extracts their features, detects or calculates Coordinate Reference Systems (CRS), and computes measurements (area, perimeter, length). It also performs geodesic cross-checks to ensure high-accuracy metric measurements.

## Features
- **File Upload:** Accepts `.zip` (Shapefile) or `.kml`. Validates sizes, sanitizes inputs, and extracts data.
- **Robust CRS Handling:** Infers EPSG:4326 if unprojected and lacking a `.prj`, selects UTM zones dynamically based on feature centroids, and falls back to polar stereographic for high latitudes.
- **Accurate Measurements:** Computes area in square meters and hectares, plus perimeter and length in meters. Runs `pyproj.Geod` geodesic area/length as a cross-check.
- **SQLite Storage:** Synchronously parses and processes all data in-memory and writes directly to an integrated SQLite database (`app.db`).

## Tech Stack
- **Web Framework:** FastAPI, Uvicorn, python-multipart
- **Geospatial Processing:** GeoPandas, Pyogrio (bundling GDAL/LIBKML), Shapely, PyProj
- **Database:** SQLAlchemy 2.x, SQLite (Zero-setup)
- **Tooling:** Pytest, Ruff

## Setup & Run

### Prerequisites
Python 3.11+ and standard virtual environment tools.

### Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the API
```bash
uvicorn app.main:app --reload
```
The application will listen at `http://localhost:8000`. API Docs are available at `http://localhost:8000/docs`.

### Testing and Linting
```bash
# Run tests with coverage
pytest --cov=app tests/

# Run ruff linter
ruff check app tests
```

## API Documentation

### 1. `POST /api/files/`
Uploads and parses a new file.

**Request:**
```bash
curl -X POST -F "file=@sample_data/sample_shapefile.zip" http://localhost:8000/api/files/
```
**Response (201 Created):**
```json
{
  "id": "55369071-14ca-4074-a4e7-77a9d87cfb13",
  "filename": "sample_shapefile.zip",
  "feature_count": 2,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "error": null,
  "created_at": "2026-10-07T04:09:36.748806",
  "supported_feature_count": 2,
  "unsupported_feature_count": 0
}
```

### 2. `GET /api/files/{id}/`
Returns metadata about an uploaded file.

**Request:**
```bash
curl http://localhost:8000/api/files/55369071-14ca-4074-a4e7-77a9d87cfb13/
```
**Response (200 OK):**
```json
{
  "id": "55369071-14ca-4074-a4e7-77a9d87cfb13",
  "filename": "sample_shapefile.zip",
  "feature_count": 2,
  ...
}
```

### 3. `GET /api/files/{id}/measurements/`
Retrieves per-feature geometry (GeoJSON format), properties, and measurement calculations.

**Request:**
```bash
curl http://localhost:8000/api/files/1280d326-e7b1-40b4-8c96-3031a470718d/measurements/
```
**Response (200 OK):**
```json
{
  "file_id": "1280d326-e7b1-40b4-8c96-3031a470718d",
  "crs": "EPSG:4326",
  "feature_count": 3,
  "total": 3,
  "features": [
    {
      "index": 0,
      "geometry_type": "Polygon",
      "crs": "EPSG:4326",
      "properties": {
        "Name": "Mumbai Plot (Polygon)"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[72.8, 19.0], [72.9, 19.0], [72.9, 19.1], [72.8, 19.1], [72.8, 19.0]]]
      },
      "measurement": {
        "supported": true,
        "area_sq_m": 116569956.25,
        "area_hectares": 11656.99,
        "length_m": null,
        "perimeter_m": 43200.69,
        "geodesic_area_sq_m": 116515684.34,
        "geodesic_length_m": null,
        "projected_crs": "EPSG:32643",
        "note": null
      }
    }
  ]
}
```


## Architecture
### High-Level Structure
The system is built as a modular FastAPI application relying on synchronous REST paradigms. Incoming HTTP boundaries are managed strictly within `app.api`, keeping side-effects and serialization concerns isolated from core business logic.
- **app.api:** Defines routing, query param parsing, dependency injection, and returns validated Pydantic schemas.
- **app.services:** The "pure logic" tier. Contains isolated modules for `crs` (coordinate logic), `measurements` (Shapely and pyproj computations), `readers` (GeoPandas and Pyogrio I/O), and `file_processor` (the central orchestrator that glues them all together).
- **app.models / app.database:** Defines SQLAlchemy declarative base classes mapping directly into a local SQLite data store.

### File-Processing Flow
1. **Request Intake:** `POST /api/files/` receives a multipart form payload. Basic extension validation occurs immediately.
2. **Safety Sandbox:** For `.zip` files, `app.utils.zip_safety.check_zip_safety()` acts as a defense-in-depth layer. It iterates over the Zip archive's headers without extracting them, ensuring no path traversal (`../`) strings exist and summing uncompressed byte sizes to prevent Zip Bombs.
3. **Extraction & Reading:** Using Python's `tempfile` module, archives are briefly extracted to ephemeral OS-managed `/tmp/` mounts. `app.services.readers.parse_shapefile_zip` and `parse_kml` harness the high-performance C++ `pyogrio` library (wrapped nicely by GeoPandas) to load geometries natively into memory.
4. **Validation & Iteration:** Features without spatial geometries are dropped. Valid features undergo extraction of their properties dictionary, and geometries are sanitized using Shapely's `make_valid` where necessary.
5. **Database Storage:** Processed features are converted to GeoJSON compliant dictionaries and committed synchronously to the SQLite `features` table. The uploaded file is moved to `./data/uploads/{id}/` for durable storage.

### Measurement Flow
Upon successfully loading the features:
1. Every geometry is passed to `app.services.measurements.compute_measurements()`.
2. A strict mapping is applied: Points are skipped, Polygons compute Area/Perimeter, LineStrings compute Length.
3. The measurement service projects the geometries (see CRS handling below) and queries native Cartesian properties (e.g. `proj_geom.area`). 
4. A parallel execution calculates `pyproj.Geod` ellipsoidal metrics over the WGS84 ellipsoid as a high-fidelity cross-check. Both sets of values are returned in the JSON payload.

### CRS Handling Flow
Because shapefiles and KMLs rarely arrive with identical Coordinate Reference Systems, `app.services.crs` acts as a normalization engine:
1. It attempts to parse `.prj` files via Pyogrio. If none exist, it verifies if the coordinate bounds fit within the `[-180, 180]` global geographic box and assumes `EPSG:4326`.
2. For calculating metric measurements, degree geometries must be projected.
3. If the input geometry is Geographic (lat/lon), the centroid of the feature is used to mathematically derive its local UTM Zone.
4. A fast PyProj `Transformer` instance translates the geometry from its source CRS to the customized UTM CRS. If a feature sits at extremely high latitudes (>84 degrees), it falls back to polar stereographic (`EPSG:3413` or `3031`).

## Design Decisions
### 1. Synchronous Processing vs. Background Workers
- **Decision:** Files are parsed, measured, and saved entirely within the HTTP request lifecycle blocking the thread until completion.
- **Why:** The prompt defined this as an assignment-scale project. Bringing in Celery, RabbitMQ, or Redis fundamentally alters the operational complexity of a simple deployable container. Synchronous processing handles ~50MB shapefiles cleanly and rapidly due to Pyogrio's C++ bindings.
- **Alternative:** FastAPI `BackgroundTasks` or Celery. This would allow the API to immediately return `202 Accepted` with a `PENDING` state. A worker would later update the DB to `COMPLETED`. We chose Sync due to simplicity, though the database schema was intentionally designed with a `status` field (`PENDING`/`COMPLETED`/`FAILED`) specifically to allow this alternative to be added as a 1-line change in the future.

### 2. Pyogrio (GDAL) vs. Fiona
- **Decision:** We used `pyogrio` configured as the backend engine for GeoPandas (`engine="pyogrio"`).
- **Why:** Pyogrio binds directly to GDAL/OGR using vectorized reads. Notably, the official pre-compiled Pyogrio wheels include the `LIBKML` drivers by default across Linux, Mac, and Windows.
- **Alternative:** `fiona`. Fiona is the classic driver but frequently runs into cross-platform installation issues regarding KML drivers unless the host OS has a custom-compiled GDAL. By choosing Pyogrio, we ensured the API runs consistently without forcing users to install system-level C-libraries.

### 3. Dynamic UTM Reprojection vs. Global Equal-Area Projections
- **Decision:** We actively calculate the exact UTM zone for each feature's centroid using the formula `floor((lon + 180) / 6) + 1` rather than forcing all geometries into a single web-mercator or equal-area plane.
- **Why:** UTM provides extremely high metric accuracy (sub-meter) near the central meridian of the zone. This is ideal for Drone data (the client's domain) which typically operates strictly on hyper-local survey plots. 
- **Alternative:** We could have reprojected everything to a Global Equal Area cylinder like `EPSG:6933` (CEA). While simpler to implement (no centroid lookup), it introduces minor but compounding latitudinal distortions.

### 4. Database Selection: SQLite + SQLAlchemy
- **Decision:** `sqlite:///./data/app.db` initialized synchronously on startup. 
- **Why:** Portability. It satisfies the requirement of "zero-setup". 
- **Alternative:** PostGIS/PostgreSQL. While PostGIS natively handles geospatial indexing and area calculation natively in SQL (`ST_Area`), it requires running Docker containers. However, by using SQLAlchemy ORM, the codebase can point to a Postgres database simply by modifying `DATABASE_URL` in the environment.

## Learnings
### 1. Test Isolation and FastAPI Dependency Overrides
During the initial build phase, Pytest began exhibiting cascading failures across multiple test files. We learned that modifying `client.app.dependency_overrides` using a global state change (`client.app.dependency_overrides[get_db] = override`) within a single test bleeds over to all subsequently executed tests because the FastAPI `app` object exists globally within the test session. The fix involved strictly using `pytest.MonkeyPatch.context()` to modify the overrides dict, ensuring Python gracefully restored the original dependencies during test teardown.

### 2. Handling Exceptions in FastAPI TestClient
FastAPI's TestClient has an option `raise_server_exceptions`. When unhandled exceptions occur in endpoint logic (e.g., a simulated 500 error from database failure), TestClient will physically raise the exception in the test runner, crashing Pytest instead of returning a `Response(status_code=500)` object. We learned to either configure TestClient carefully or explicitly bind generic `@app.exception_handler(Exception)` blocks to cleanly catch everything, ensuring tests can meaningfully assert on the returned 500 JSON bodies.

### 3. Geopandas/Pyogrio Empty Geometry Behaviors
When processing KMLs without features or entirely malformed XML, Geopandas does not always throw a clean ValueError. Because it delegates down to C-bindings, a perfectly empty KML often results in an `IndexError: index 0 is out of bounds for axis 0 with size 0` deep within pandas DataFrame conversions. We learned that relying on simple string assertions for `Exception` messages in data science libraries is brittle. 

### 4. Exception Layering
Initially, our architecture raised `fastapi.HTTPException` deep within `app.services`. This violated separation of concerns, as core business logic became coupled to HTTP status codes. We learned that designing custom exception classes (`InvalidExtensionError`, `UnsafeZipError`) in the application layer, and letting FastAPI gracefully handle them via `@app.exception_handler` at the routing boundary, results in far cleaner unit tests and easily reusable service layers for non-HTTP contexts (such as a CLI script).

## Web UI
This project includes a convenient, single-page web interface served at `/ui` (available when running the application). It provides a polished way to interact with the underlying REST API without needing `curl` or Postman.
- **Functionality:** Upload files via drag-and-drop, view summary statistics, and visualize extracted geometries directly on a Leaflet map. 
- **Interactive Tables:** Filter, sort, and search across thousands of features, and cross-highlight them dynamically between the table and the map.
- **Data Export:** Generate JSON and CSV exports of your processed data directly from the browser.
- **Security:** The frontend strictly uses `document.createElement` and `textContent` to inject user-provided property data (like Names) into the DOM. `innerHTML` is strictly avoided to ensure zero surface area for Cross-Site Scripting (XSS) vulnerabilities.

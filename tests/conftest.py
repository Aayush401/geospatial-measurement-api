import os
import shutil
import tempfile
import zipfile

import geopandas as gpd
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import Polygon
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

@pytest.fixture(scope="module")
def sample_kml():
    fd, path = tempfile.mkstemp(suffix=".kml")
    kml_content = """<?xml version="1.0" encoding="utf-8" ?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <Placemark>
    <name>Mumbai Plot (Polygon)</name>
    <Polygon>
      <outerBoundaryIs><LinearRing><coordinates>72.8,19.0 72.9,19.0 72.9,19.1 72.8,19.1 72.8,19.0</coordinates></LinearRing></outerBoundaryIs>
    </Polygon>
  </Placemark>
</Document>
</kml>
"""
    with os.fdopen(fd, "w") as f:
        f.write(kml_content)
    yield path
    os.remove(path)
    
@pytest.fixture(scope="module")
def sample_shapefile_zip():
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    temp_dir = tempfile.mkdtemp()
    
    p1 = Polygon([(72.8, 19.0), (72.9, 19.0), (72.9, 19.1), (72.8, 19.1), (72.8, 19.0)])
    gdf = gpd.GeoDataFrame({"name": ["Plot A"]}, geometry=[p1], crs="EPSG:4326")
    gdf.to_file(os.path.join(temp_dir, "test.shp"), engine="pyogrio")
    
    with zipfile.ZipFile(path, "w") as zf:
        for filename in os.listdir(temp_dir):
            zf.write(os.path.join(temp_dir, filename), arcname=filename)
            
    shutil.rmtree(temp_dir)
    yield path
    os.remove(path)

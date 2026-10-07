import os
import shutil
import zipfile

import geopandas as gpd
from shapely.geometry import Polygon

os.makedirs("sample_data", exist_ok=True)

# 1. Sample Mixed KML
kml_content = """<?xml version="1.0" encoding="utf-8" ?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <Placemark>
    <name>Mumbai Plot (Polygon)</name>
    <Polygon>
      <outerBoundaryIs><LinearRing><coordinates>72.8,19.0 72.9,19.0 72.9,19.1 72.8,19.1 72.8,19.0</coordinates></LinearRing></outerBoundaryIs>
    </Polygon>
  </Placemark>
  <Placemark>
    <name>Line (LineString)</name>
    <LineString><coordinates>72.8,19.0 72.9,19.0</coordinates></LineString>
  </Placemark>
  <Placemark>
    <name>Point</name>
    <Point><coordinates>72.85,19.05</coordinates></Point>
  </Placemark>
</Document>
</kml>
"""
with open("sample_data/sample_mixed.kml", "w") as f:
    f.write(kml_content)

# 2. Sample Shapefile (Polygons in Mumbai area)
p1 = Polygon([(72.8, 19.0), (72.9, 19.0), (72.9, 19.1), (72.8, 19.1), (72.8, 19.0)])
p2 = Polygon([(73.0, 19.0), (73.1, 19.0), (73.1, 19.1), (73.0, 19.1), (73.0, 19.0)])
gdf = gpd.GeoDataFrame({"name": ["Plot A", "Plot B"]}, geometry=[p1, p2], crs="EPSG:4326")
os.makedirs("sample_data/shp_temp", exist_ok=True)
gdf.to_file("sample_data/shp_temp/sample_shapefile.shp", engine="pyogrio")

with zipfile.ZipFile("sample_data/sample_shapefile.zip", "w") as zf:
    for filename in os.listdir("sample_data/shp_temp"):
        zf.write(os.path.join("sample_data/shp_temp", filename), arcname=filename)
shutil.rmtree("sample_data/shp_temp")

print("Generated sample data.")

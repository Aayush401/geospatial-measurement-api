import sys

# Need to set path
sys.path.insert(0, ".")
import shapely.ops
from pyproj import Transformer
from shapely.geometry import Polygon

from app.services.measurements import compute_measurements

# Create a 1km x 1km square in EPSG:32643 (UTM 43N)
# Let's say origin is at (500000, 2100000)
# 1km = 1000 meters
origin_x, origin_y = 500000, 2100000
p_utm = Polygon([
    (origin_x, origin_y), 
    (origin_x + 1000, origin_y), 
    (origin_x + 1000, origin_y + 1000), 
    (origin_x, origin_y + 1000), 
    (origin_x, origin_y)
])

# Reproject to EPSG:4326 (Degrees)
transformer = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)
p_4326 = shapely.ops.transform(transformer.transform, p_utm)

print("--- PROOF FOR CHECK 7 ---")
print(f"Original 1km x 1km Area in UTM: {p_utm.area} sq m")
print(f"Polygon in degrees (EPSG:4326):\n{p_4326}")

m = compute_measurements(p_4326, "EPSG:4326")
print(f"Computed Area from App: {m.area_sq_m} sq m")
print(f"Projected CRS used: {m.projected_crs}")
print(f"Geodesic cross-check: {m.geodesic_area_sq_m} sq m")

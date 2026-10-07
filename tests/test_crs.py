from pyproj import CRS
from shapely.geometry import Point

from app.services.crs import select_projected_crs


def test_select_projected_crs_mumbai():
    geom = Point(72.8, 19.0) # Mumbai
    src_crs = CRS.from_epsg(4326)
    proj_crs = select_projected_crs(geom, src_crs)
    assert proj_crs.to_string() == "EPSG:32643"

def test_select_projected_crs_south_hemisphere():
    geom = Point(144.96, -37.81) # Melbourne
    src_crs = CRS.from_epsg(4326)
    proj_crs = select_projected_crs(geom, src_crs)
    assert proj_crs.to_string() == "EPSG:32755"

def test_select_projected_crs_already_projected_meters():
    geom = Point(500000, 4000000)
    src_crs = CRS.from_epsg(32643) # Already UTM
    proj_crs = select_projected_crs(geom, src_crs)
    assert proj_crs == src_crs

def test_select_projected_crs_polar():
    geom = Point(0, 85) # North pole area
    src_crs = CRS.from_epsg(4326)
    proj_crs = select_projected_crs(geom, src_crs)
    assert proj_crs.to_string() == "EPSG:3413"

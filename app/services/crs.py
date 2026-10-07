import logging
import math
from functools import lru_cache

from pyproj import CRS, Transformer
from shapely.geometry.base import BaseGeometry

logger = logging.getLogger(__name__)

@lru_cache(maxsize=128)
def get_transformer(src_crs_str: str, dst_crs_str: str) -> Transformer:
    """Returns a cached transformer between two CRSs."""
    return Transformer.from_crs(src_crs_str, dst_crs_str, always_xy=True)

def select_projected_crs(geom: BaseGeometry, src_crs: CRS) -> CRS:
    """
    Selects an appropriate projected CRS for a given geometry and source CRS.
    """
    if src_crs.is_projected:
        axis_info = src_crs.axis_info
        if axis_info and axis_info[0].unit_name in ("metre", "meter"):
            return src_crs

    if geom.is_empty:
        return src_crs

    centroid = geom.centroid
    if src_crs.to_string() != "EPSG:4326":
        t = get_transformer(src_crs.to_string(), "EPSG:4326")
        lon, lat = t.transform(centroid.x, centroid.y)
    else:
        lon, lat = centroid.x, centroid.y

    if abs(lat) > 84:
        if lat > 0:
            return CRS.from_epsg(3413) # North
        else:
            return CRS.from_epsg(3031) # South
    
    zone_num = math.floor((lon + 180) / 6) + 1
    epsg_code = 32600 + zone_num if lat >= 0 else 32700 + zone_num
    return CRS.from_epsg(epsg_code)

import logging

import shapely
import shapely.ops
from pyproj import CRS, Geod
from pyproj.exceptions import CRSError

from app.schemas import Measurement
from app.services.crs import get_transformer, select_projected_crs

logger = logging.getLogger(__name__)

def compute_measurements(geom: shapely.geometry.base.BaseGeometry, src_crs_str: str) -> Measurement:
    if geom is None or geom.is_empty:
        return Measurement(supported=False, note="Geometry is null or empty")
    
    geom_type = geom.geom_type
    
    if geom_type in ("Point", "MultiPoint"):
        return Measurement(supported=True, note="No measurement required for points")
        
    if geom_type not in ("Polygon", "MultiPolygon", "LineString", "MultiLineString"):
        return Measurement(supported=False, note=f"Measurement not supported for {geom_type}")
        
    try:
        src_crs = CRS.from_string(src_crs_str)
    except CRSError:
        return Measurement(supported=False, note=f"Invalid source CRS: {src_crs_str}")

    note = None
    if not geom.is_valid:
        geom = shapely.make_valid(geom)
        note = "geometry was invalid; repaired for measurement"
        if geom.is_empty or geom.geom_type not in ("Polygon", "MultiPolygon", "LineString", "MultiLineString"):
             return Measurement(supported=False, note="Repaired geometry is not measurable")

    try:
        proj_crs = select_projected_crs(geom, src_crs)
        
        if src_crs.to_string() != proj_crs.to_string():
            transformer = get_transformer(src_crs.to_string(), proj_crs.to_string())
            proj_geom = shapely.ops.transform(transformer.transform, geom)
        else:
            proj_geom = geom
            
        area_sq_m = None
        area_hectares = None
        length_m = None
        perimeter_m = None
        
        if proj_geom.geom_type in ("Polygon", "MultiPolygon"):
            area_sq_m = proj_geom.area
            area_hectares = area_sq_m / 10000.0
            perimeter_m = proj_geom.length
        elif proj_geom.geom_type in ("LineString", "MultiLineString"):
            length_m = proj_geom.length
            
        geod = Geod(ellps="WGS84")
        if src_crs.to_string() != "EPSG:4326":
            t_4326 = get_transformer(src_crs.to_string(), "EPSG:4326")
            geom_4326 = shapely.ops.transform(t_4326.transform, geom)
        else:
            geom_4326 = geom
            
        geodesic_area = None
        geodesic_length = None
        
        if geom_4326.geom_type in ("Polygon", "MultiPolygon"):
            area, _perim = geod.geometry_area_perimeter(geom_4326)
            geodesic_area = abs(area)
        elif geom_4326.geom_type in ("LineString", "MultiLineString"):
            geodesic_length = geod.geometry_length(geom_4326)
            
        return Measurement(
            supported=True,
            area_sq_m=area_sq_m,
            area_hectares=area_hectares,
            length_m=length_m,
            perimeter_m=perimeter_m,
            geodesic_area_sq_m=geodesic_area,
            geodesic_length_m=geodesic_length,
            projected_crs=proj_crs.to_string(),
            note=note
        )
    except CRSError:
        logger.exception("Error computing measurement")
        return Measurement(supported=False, note="Measurement could not be computed for this geometry")

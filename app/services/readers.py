import logging
import os
import zipfile
from dataclasses import dataclass

import geopandas as gpd
import shapely.geometry
from pyproj import CRS

from app.utils.serialization import sanitize_properties

logger = logging.getLogger(__name__)

@dataclass
class ParsedFeature:
    index: int
    geometry: shapely.geometry.base.BaseGeometry | None
    properties: dict

@dataclass
class ParsedFile:
    crs: CRS
    features: list

def parse_shapefile_zip(zip_path: str) -> ParsedFile:
    if os.path.getsize(zip_path) == 0:
        raise ValueError("The uploaded file is empty.")
    shp_count = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.filename.lower().endswith(".shp") and not info.filename.startswith("__MACOSX"):
                shp_count += 1
    if shp_count > 1:
        raise ValueError("Multiple .shp files found in the zip. Please upload a zip with exactly one shapefile.")
    if shp_count == 0:
        raise ValueError("No .shp file found in the zip.")

    try:
        gdf = gpd.read_file(zip_path, engine="pyogrio")
    except Exception:
        logger.exception("Failed to parse shapefile zip")
        raise ValueError("Could not read the Shapefile. Make sure the zip contains valid .shp, .shx and .dbf files.") from None
        
    if len(gdf) == 0:
        raise ValueError("No features found")
        
    crs = gdf.crs
    if crs is None:
        bounds = gdf.total_bounds
        if len(bounds) == 4 and bounds[0] >= -180 and bounds[1] >= -90 and bounds[2] <= 180 and bounds[3] <= 90:
            crs = CRS.from_epsg(4326)
            logger.warning("CRS missing; inferred EPSG:4326 from bounds")
        else:
            raise ValueError("CRS missing and cannot be inferred")
            
    features = []
    for idx, row in gdf.iterrows():
        geom = row.geometry
        props = row.drop('geometry').to_dict()
        if 'Name' in props:
            props['name'] = props.pop('Name')
        # Drop internal GDAL KML columns if they are empty/default to keep properties clean
        defaults = {"id": None, 'description': None, 'timestamp': None, 'begin': None, 'end': None, 'altitudeMode': None, 'tessellate': -1, 'extrude': 0, 'visibility': -1, 'drawOrder': None, 'icon': None}
        for k, default_val in defaults.items():
            import pandas as pd
            if k in props and (props[k] == default_val or pd.isna(props[k])):
                props.pop(k)
        features.append(ParsedFeature(
            index=int(idx),
            geometry=geom,
            properties=sanitize_properties(props)
        ))
    return ParsedFile(crs=crs, features=features)

def parse_kml(file_path: str) -> ParsedFile:
    if os.path.getsize(file_path) == 0:
        raise ValueError("The uploaded file is empty.")
    crs = CRS.from_epsg(4326)
    try:
        gdf = gpd.read_file(file_path, engine="pyogrio")
    except Exception:
        logger.exception("Failed to parse KML file")
        raise ValueError("Invalid or malformed KML file.") from None
        
    if len(gdf) == 0:
        raise ValueError("No features found")
        
    features = []
    for idx, row in gdf.iterrows():
        geom = row.geometry
        props = row.drop('geometry').to_dict()
        if 'Name' in props:
            props['name'] = props.pop('Name')
        # Drop internal GDAL KML columns if they are empty/default to keep properties clean
        defaults = {"id": None, 'description': None, 'timestamp': None, 'begin': None, 'end': None, 'altitudeMode': None, 'tessellate': -1, 'extrude': 0, 'visibility': -1, 'drawOrder': None, 'icon': None}
        for k, default_val in defaults.items():
            import pandas as pd
            if k in props and (props[k] == default_val or pd.isna(props[k])):
                props.pop(k)
        features.append(ParsedFeature(
            index=int(idx),
            geometry=geom,
            properties=sanitize_properties(props)
        ))
    return ParsedFile(crs=crs, features=features)

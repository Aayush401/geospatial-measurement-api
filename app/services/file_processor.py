import logging
import os
import uuid

import shapely.geometry
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import (
    FileProcessingError,
    FileSizeLimitError,
    InvalidExtensionError,
    UnsafeZipError,
)
from app.models import Feature, UploadedFile
from app.services.measurements import compute_measurements
from app.services.readers import parse_kml, parse_shapefile_zip
from app.utils.zip_safety import check_zip_safety

logger = logging.getLogger(__name__)

def process_file(db: Session, file: UploadFile) -> UploadedFile:
    file_id = str(uuid.uuid4())
    ext = file.filename.split('.')[-1].lower() if file.filename else ""
    
    if ext not in ("zip", "kml"):
        raise InvalidExtensionError("Invalid file extension. Only .zip and .kml are supported.")
        
    file_type = "shapefile" if ext == "zip" else "kml"
    
    file_dir = os.path.join(settings.DATA_DIR, "uploads", file_id)
    os.makedirs(file_dir, exist_ok=True)
    file_path = os.path.join(file_dir, file.filename)
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise FileSizeLimitError(f"File exceeds maximum upload size of {settings.MAX_UPLOAD_MB} MB")
        
    with open(file_path, "wb") as f:
        f.write(file.file.read())
        
    if ext == "zip" and not check_zip_safety(file_path):
            raise UnsafeZipError("Zip file is unsafe (zip slip or exceeds uncompressed limits) or corrupt")
            
    db_file = UploadedFile(
        id=file_id,
        filename=file.filename,
        file_type=file_type,
        status="PROCESSING",
        stored_path=file_path
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    try:
        parsed = parse_shapefile_zip(file_path) if file_type == "shapefile" else parse_kml(file_path)
            
        db_file.crs = parsed.crs.to_string()
        db_file.feature_count = len(parsed.features)
        
        for p_feat in parsed.features:
            geom = p_feat.geometry
            geom_type = geom.geom_type if geom else None
            
            measurement = compute_measurements(geom, db_file.crs)
            
            db_feat = Feature(
                file_id=file_id,
                feature_index=p_feat.index,
                geometry_type=geom_type,
                crs=db_file.crs,
                properties=p_feat.properties,
                geometry=shapely.geometry.mapping(geom) if geom else None,
                supported=measurement.supported,
                measurement=measurement.model_dump()
            )
            db.add(db_feat)
            
        db_file.status = "COMPLETED"
        db.commit()
        db.refresh(db_file)
        
    except ValueError as e:
        db.rollback()
        db_file.status = "FAILED"
        db_file.error = str(e)
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        raise FileProcessingError(str(e)) from e
    except Exception:
        db.rollback()
        logger.exception("Processing error")
        db_file.status = "FAILED"
        db_file.error = "Internal processing error"
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        raise FileProcessingError("Internal processing error") from None
        
    return db_file

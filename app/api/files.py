
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Feature, UploadedFile
from app.schemas import FeatureResponse, FileInfo, MeasurementsResponse
from app.services.file_processor import process_file

router = APIRouter(prefix="/api/files", tags=["files"])

def get_file_info_dict(db: Session, db_file: UploadedFile) -> dict:
    supp = db.query(func.count(Feature.id)).filter(Feature.file_id == db_file.id, Feature.supported.is_(True)).scalar()
    unsupp = db.query(func.count(Feature.id)).filter(Feature.file_id == db_file.id, Feature.supported.is_(False)).scalar()
    
    return {
        "id": db_file.id,
        "filename": db_file.filename,
        "feature_count": db_file.feature_count,
        "crs": db_file.crs,
        "status": db_file.status,
        "error": db_file.error,
        "created_at": db_file.created_at,
        "supported_feature_count": supp if db_file.status == "COMPLETED" else None,
        "unsupported_feature_count": unsupp if db_file.status == "COMPLETED" else None,
    }

@router.post("/", response_model=FileInfo, status_code=201)
def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    db_file = process_file(db, file)
    return get_file_info_dict(db, db_file)

@router.get("/{id}/", response_model=FileInfo)
def get_file(id: str, db: Session = Depends(get_db)):
    db_file = db.query(UploadedFile).filter(UploadedFile.id == id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    return get_file_info_dict(db, db_file)

@router.get("/{id}/measurements/", response_model=MeasurementsResponse)
def get_measurements(
    id: str, 
    geometry_type: str | None = Query(None),
    include_geometry: bool = Query(True),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    db_file = db.query(UploadedFile).filter(UploadedFile.id == id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
        
    if db_file.status != "COMPLETED":
        raise HTTPException(status_code=409, detail=f"File status is {db_file.status}")

    query = db.query(Feature).filter(Feature.file_id == id)
    if geometry_type:
        query = query.filter(Feature.geometry_type == geometry_type)
        
    total = query.count()
    features = query.order_by(Feature.feature_index).offset(offset).limit(limit).all()
    
    feature_responses = []
    for f in features:
        feature_responses.append(FeatureResponse(
            index=f.feature_index,
            geometry_type=f.geometry_type,
            crs=f.crs,
            properties=f.properties,
            geometry=f.geometry if include_geometry else None,
            measurement=f.measurement
        ))
        
    return MeasurementsResponse(
        file_id=id,
        crs=db_file.crs,
        feature_count=db_file.feature_count or 0,
        total=total,
        features=feature_responses
    )

import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False) # "shapefile" or "kml"
    status = Column(String, nullable=False)    # PENDING, PROCESSING, COMPLETED, FAILED
    crs = Column(String, nullable=True)
    feature_count = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    stored_path = Column(String, nullable=False)
    
    features = relationship("Feature", back_populates="file", cascade="all, delete-orphan")

class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("uploaded_files.id"), index=True, nullable=False)
    feature_index = Column(Integer, nullable=False)
    geometry_type = Column(String, nullable=True)
    crs = Column(String, nullable=True)
    properties = Column(JSON, nullable=True)
    geometry = Column(JSON, nullable=True)
    supported = Column(Boolean, nullable=False)
    measurement = Column(JSON, nullable=True)

    file = relationship("UploadedFile", back_populates="features")

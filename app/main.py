import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import files
from app.config import settings
from app.database import Base, engine
from app.exceptions import (
    FileProcessingError,
    FileSizeLimitError,
    InvalidExtensionError,
    UnsafeZipError,
)

logging.basicConfig(level=logging.INFO)

os.makedirs(os.path.join(settings.DATA_DIR, "uploads"), exist_ok=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Geospatial Measurement API", version="1.0.0")


app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/ui", response_class=HTMLResponse)
async def get_ui():
    return FileResponse("app/static/index.html")

app.include_router(files.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.exception_handler(InvalidExtensionError)
async def invalid_extension_handler(request: Request, exc: InvalidExtensionError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(FileSizeLimitError)
async def file_size_limit_handler(request: Request, exc: FileSizeLimitError):
    return JSONResponse(status_code=413, content={"detail": str(exc)})

@app.exception_handler(UnsafeZipError)
async def unsafe_zip_handler(request: Request, exc: UnsafeZipError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(FileProcessingError)
async def file_processing_handler(request: Request, exc: FileProcessingError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("Unhandled exception:")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

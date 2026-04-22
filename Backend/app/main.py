"""
PDF Summarization Project - FastAPI Entry Point
Main application file that sets up the FastAPI server and includes all routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
import os

# Import routers
from app.routers import upload, extract, clean, summarize, translate_summary

load_dotenv()


def _parse_origins(value: str) -> list[str]:
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    return origins or ["http://localhost:3000", "http://localhost:5173"]


def _resolve_directory(env_name: str, default_path: Path) -> Path:
    configured_value = os.getenv(env_name)
    if configured_value:
        return Path(configured_value).expanduser().resolve()
    return default_path


# Create FastAPI app
app = FastAPI(
    title="PDF Summarization API",
    description="API for uploading, extracting, cleaning, and summarizing PDF documents",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_origins(os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = _resolve_directory("UPLOADS_DIR", BASE_DIR / "uploads")
OUTPUTS_DIR = _resolve_directory("OUTPUTS_DIR", BASE_DIR / "outputs")

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files for serving uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# Include routers
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(extract.router, prefix="/api/extract", tags=["extract"])
app.include_router(clean.router, prefix="/api/clean", tags=["clean"])
app.include_router(summarize.router, prefix="/api/summarize", tags=["summarize"])
app.include_router(translate_summary.router, prefix="/api/translate", tags=["translate"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "PDF Summarization API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "upload": "/api/upload",
            "extract": "/api/extract", 
            "clean": "/api/clean",
            "summarize": "/api/summarize",
            "translate": "/api/translate"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

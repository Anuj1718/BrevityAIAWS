"""
PDF Summarization Project - FastAPI Entry Point
Main application file that sets up the FastAPI server and includes all routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
import os
import asyncio

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


async def _preload_models():
    """Preload ML models in the background after server starts."""
    await asyncio.sleep(2)  # Let the server finish starting first
    try:
        # Check if torch is available
        import torch
        gpu_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu_available else "None"
        print(f"[Startup] GPU: {gpu_name} | CUDA: {gpu_available}")

        # Preload BART summarization model using direct model loading
        # (pipeline task names changed in transformers 5.x)
        print("[Startup] Preloading BART summarization model...")
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        model_name = "facebook/bart-large-cnn"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            dtype=torch.float16 if gpu_available else torch.float32,
            device_map="auto" if gpu_available else None
        )
        # Store on the summarizer instance for reuse
        summarize.summarizer._abstractive_model = model
        summarize.summarizer._abstractive_tokenizer = tokenizer
        print(f"[Startup] ✅ BART model loaded and ready! (GPU: {gpu_available})")

    except ImportError:
        print("[Startup] PyTorch not available — running in extractive-only mode")
    except Exception as e:
        print(f"[Startup] Model preload warning: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: preload models on startup."""
    # Start model preloading in background
    preload_task = asyncio.create_task(_preload_models())
    yield
    preload_task.cancel()


# Create FastAPI app
app = FastAPI(
    title="PDF Summarization API",
    description="API for uploading, extracting, cleaning, and summarizing PDF documents",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_origins(
        os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:5173,https://brevityaiapp.vercel.app"
        )
    ),
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
    """Health check endpoint with GPU status."""
    status = {"status": "healthy"}
    try:
        import torch
        status["gpu_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            status["gpu_name"] = torch.cuda.get_device_name(0)
            status["gpu_memory_allocated"] = f"{torch.cuda.memory_allocated(0) / 1024**2:.0f} MB"
        status["bart_loaded"] = summarize.summarizer._abstractive_model is not None
    except ImportError:
        status["gpu_available"] = False
        status["bart_loaded"] = False
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

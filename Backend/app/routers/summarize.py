"""
Enhanced Summarize Router - Handles optimized text summarization endpoints 
(extractive + abstractive + hybrid + formatted_hybrid)
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from app.services.summarizer import OptimizedTextSummarizer
from app.services.cleaner import TextCleaner
import os

router = APIRouter()
summarizer = OptimizedTextSummarizer()
cleaner = TextCleaner()

# -------------------------------
# Optimized Extractive Summary
# -------------------------------
@router.post("/extractive/{filename}")
async def extractive_summary(
    filename: str,
    summary_ratio: float = Query(0.5, description="Ratio of sentences to keep (0.1-0.9)"),
    algorithm: str = Query("textrank", description="Algorithm: textrank, tfidf, or lsa"),
    use_cache: bool = Query(True, description="Use caching for better performance")
):
    try:
        try:
            result = await summarizer.extractive_summary(filename, summary_ratio, algorithm, use_cache)
        except FileNotFoundError:
            # If cleaned text not found, run cleaning first
            await cleaner.clean_text(filename)
            result = await summarizer.extractive_summary(filename, summary_ratio, algorithm, use_cache)

        return JSONResponse(status_code=200, content={
            "message": "Extractive summary generated successfully",
            "filename": filename,
            **result,
            "algorithm": algorithm,
            "optimized": True
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extractive summarization failed: {str(e)}")


# -------------------------------
# Optimized Abstractive Summary
# -------------------------------
@router.post("/abstractive/{filename}")
async def abstractive_summary(
    filename: str,
    max_length: int = Query(150, description="Maximum length of summary"),
    min_length: int = Query(30, description="Minimum length of summary"),
    model: str = Query("sshleifer/distilbart-cnn-12-6", description="Model to use for abstractive summarization"),
    use_pipeline: bool = Query(True, description="Use pipeline for better performance")
):
    try:
        try:
            result = await summarizer.abstractive_summary(filename, max_length, min_length, model, use_pipeline)
        except FileNotFoundError:
            await cleaner.clean_text(filename)
            result = await summarizer.abstractive_summary(filename, max_length, min_length, model, use_pipeline)

        return JSONResponse(status_code=200, content={
            "message": "Abstractive summary generated successfully",
            "filename": filename,
            **result,
            "model": model,
            "optimized": True
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Abstractive summarization failed: {str(e)}")


# -------------------------------
# Optimized Hybrid Summary
# -------------------------------
@router.post("/hybrid/{filename}")
async def hybrid_summary(
    filename: str,
    extractive_ratio: float = Query(0.5, description="Ratio for extractive preprocessing"),
    max_length: int = Query(200, description="Maximum length of final summary"),
    min_length: int = Query(50, description="Minimum length of final summary"),
    use_pipeline: bool = Query(True, description="Use pipeline for better performance")
):
    try:
        try:
            result = await summarizer.hybrid_summary(filename, extractive_ratio, max_length, min_length, use_pipeline)
        except FileNotFoundError:
            await cleaner.clean_text(filename)
            result = await summarizer.hybrid_summary(filename, extractive_ratio, max_length, min_length, use_pipeline)

        return JSONResponse(status_code=200, content={
            "message": "Hybrid summary generated successfully",
            "filename": filename,
            **result,
            "extractive_ratio": extractive_ratio,
            "optimized": True
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid summarization failed: {str(e)}")


# -------------------------------
# Optimized Formatted Hybrid Summary
# -------------------------------
@router.post("/formatted-hybrid/{filename}")
async def formatted_hybrid_summary(
    filename: str,
    extractive_ratio: float = Query(0.5, description="Ratio for extractive preprocessing"),
    max_length: int = Query(200, description="Maximum length of final summary"),
    min_length: int = Query(50, description="Minimum length of final summary"),
    use_pipeline: bool = Query(True, description="Use pipeline for better performance")
):
    try:
        try:
            result = await summarizer.formatted_hybrid_summary(filename, extractive_ratio, max_length, min_length, use_pipeline)
        except FileNotFoundError:
            await cleaner.clean_text(filename)
            result = await summarizer.formatted_hybrid_summary(filename, extractive_ratio, max_length, min_length, use_pipeline)

        return JSONResponse(status_code=200, content={
            "message": "Formatted hybrid summary generated successfully",
            "filename": filename,
            **result,
            "extractive_ratio": extractive_ratio,
            "optimized": True
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Formatted hybrid summarization failed: {str(e)}")


# -------------------------------
# Get Summary (Retrieve Saved)
# -------------------------------
@router.get("/summary/{filename}")
async def get_summary(
    filename: str,
    summary_type: str = Query("extractive", description="Type: extractive, abstractive, hybrid, formatted_hybrid")
):
    try:
        result = summarizer.get_summary(filename, summary_type)
        return JSONResponse(status_code=200, content={
            "message": f"{summary_type.title()} summary retrieved successfully",
            "filename": filename,
            "summary_type": summary_type,
            **result
        })
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{summary_type.title()} summary not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")

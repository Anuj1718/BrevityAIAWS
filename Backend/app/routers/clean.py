"""
Clean Router - Handles text cleaning and normalization endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from app.services.cleaner import TextCleaner
from typing import Optional

router = APIRouter()
cleaner = TextCleaner()

@router.post("/text/{filename}")
async def clean_text(
    filename: str,
    remove_stopwords: bool = Query(True, description="Remove stopwords"),
    normalize_whitespace: bool = Query(True, description="Normalize whitespace"),
    remove_special_chars: bool = Query(False, description="Remove special characters"),
    min_sentence_length: int = Query(10, description="Minimum sentence length"),
    ocr_mode: bool = Query(False, description="Preserve OCR line boundaries during cleaning")
):
    """
    Clean and normalize extracted text from a PDF.
    
    Args:
        filename: Name of the PDF file
        remove_stopwords: Whether to remove stopwords
        normalize_whitespace: Whether to normalize whitespace
        remove_special_chars: Whether to remove special characters
        min_sentence_length: Minimum length for sentences to keep
        
    Returns:
        JSON response with cleaned text
    """
    try:
        # Clean the text
        result = await cleaner.clean_text(
            filename=filename,
            remove_stopwords=remove_stopwords,
            normalize_whitespace=normalize_whitespace,
            remove_special_chars=remove_special_chars,
            min_sentence_length=min_sentence_length,
            ocr_mode=ocr_mode
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Text cleaned successfully",
                "filename": filename,
                "original_length": result["original_length"],
                "cleaned_length": result["cleaned_length"],
                "cleaned_text": result["cleaned_text"],
                "sentences": result["sentences"],
                "word_count": result["word_count"],
                "file_path": result["file_path"]
            }
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="PDF file or extracted text not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text cleaning failed: {str(e)}")

@router.get("/text/{filename}")
async def get_cleaned_text(filename: str):
    """
    Get previously cleaned text from a PDF file.
    
    Args:
        filename: Name of the PDF file
        
    Returns:
        JSON response with cleaned text
    """
    try:
        result = cleaner.get_cleaned_text(filename)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Cleaned text retrieved successfully",
                "filename": filename,
                "cleaned_text": result["cleaned_text"],
                "sentences": result["sentences"],
                "word_count": result["word_count"]
            }
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Cleaned text not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cleaned text: {str(e)}")

@router.post("/preview/{filename}")
async def preview_cleaning(
    filename: str,
    sample_size: int = Query(500, description="Number of characters to preview")
):
    """
    Preview text cleaning without saving the result.
    
    Args:
        filename: Name of the PDF file
        sample_size: Number of characters to preview
        
    Returns:
        JSON response with cleaning preview
    """
    try:
        result = await cleaner.preview_cleaning(filename, sample_size)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Cleaning preview generated successfully",
                "filename": filename,
                "original_sample": result["original_sample"],
                "cleaned_sample": result["cleaned_sample"],
                "preview_length": result["preview_length"]
            }
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="PDF file or extracted text not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")

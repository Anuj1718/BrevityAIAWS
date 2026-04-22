"""
Text Cleaner Service - Handles text cleaning and normalization
"""

import os
import json
import re
import string
from typing import Dict, Any, List
from app.utils.text_utils import TextUtils

class TextCleaner:
    """Handles text cleaning and normalization operations."""
    
    def __init__(self):
        self.output_dir = "outputs"
        self.text_utils = TextUtils()
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure output directory exists."""
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def clean_text(
        self,
        filename: str,
        remove_stopwords: bool = True,
        normalize_whitespace: bool = True,
        remove_special_chars: bool = False,
        min_sentence_length: int = 10,
        ocr_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Clean and normalize extracted text.
        
        Args:
            filename: Name of the PDF file
            remove_stopwords: Whether to remove stopwords
            normalize_whitespace: Whether to normalize whitespace
            remove_special_chars: Whether to remove special characters
            min_sentence_length: Minimum length for sentences to keep
            
        Returns:
            Dictionary with cleaned text and metadata
        """
        # Get extracted text
        extraction_metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_extraction_metadata.json")
        
        if not os.path.exists(extraction_metadata_path):
            raise FileNotFoundError(f"Extracted text not found for: {filename}")
        
        with open(extraction_metadata_path, 'r', encoding='utf-8') as f:
            extraction_data = json.load(f)
        
        original_text = extraction_data["text"]
        original_length = len(original_text)
        
        # Clean the text
        cleaned_text = original_text
        
        # Always remove page markers first
        cleaned_text = self.text_utils.remove_page_markers(cleaned_text)
        
        if normalize_whitespace:
            cleaned_text = self._normalize_ocr_whitespace(cleaned_text) if ocr_mode else self._normalize_whitespace(cleaned_text)
        
        if remove_special_chars and not ocr_mode:
            cleaned_text = self._remove_special_characters(cleaned_text)
        
        # Split into sentences
        sentences = self.text_utils.split_into_sentences(cleaned_text)
        original_sentence_count = len(sentences)

        if ocr_mode and remove_special_chars:
            sentences = [self._remove_special_characters(sentence) for sentence in sentences]
        
        # Filter sentences by length
        sentences = [s for s in sentences if len(s.strip()) >= min_sentence_length]

        # OCR text can be fragmented; if filtering removes everything, keep the original candidates.
        if not sentences and original_sentence_count > 0:
            sentences = self.text_utils.split_into_sentences(cleaned_text)
        
        # Remove stopwords if requested
        if remove_stopwords:
            sentences = [self.text_utils.remove_stopwords(s) for s in sentences]
        
        # Join sentences back
        cleaned_text = " ".join(sentences)
        
        # Calculate statistics
        word_count = len(cleaned_text.split())
        cleaned_length = len(cleaned_text)
        
        # Save cleaned text
        output_filename = f"{os.path.splitext(filename)[0]}_cleaned.txt"
        output_path = os.path.join(self.output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        # Save metadata
        metadata = {
            "cleaned_text": cleaned_text,
            "sentences": sentences,
            "original_length": original_length,
            "cleaned_length": cleaned_length,
            "word_count": word_count,
            "sentence_count": len(sentences),
            "file_path": output_path,
            "cleaning_options": {
                "remove_stopwords": remove_stopwords,
                "normalize_whitespace": normalize_whitespace,
                "remove_special_chars": remove_special_chars,
                "min_sentence_length": min_sentence_length,
                "ocr_mode": ocr_mode
            }
        }
        
        metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_cleaning_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return metadata
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    def _normalize_ocr_whitespace(self, text: str) -> str:
        """Normalize OCR text while preserving line boundaries for sentence recovery."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        lines = [line for line in lines if line]
        return "\n".join(lines)
    
    def _remove_special_characters(self, text: str) -> str:
        """Remove special characters from text."""
        # Keep only letters, numbers, spaces, and basic punctuation
        text = re.sub(r'[^\w\s.,!?;:]', '', text)
        return text
    
    def get_cleaned_text(self, filename: str) -> Dict[str, Any]:
        """
        Get previously cleaned text.
        
        Args:
            filename: Name of the PDF file
            
        Returns:
            Dictionary with cleaned text and metadata
        """
        metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_cleaning_metadata.json")
        
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Cleaned text not found for: {filename}")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return metadata
    
    async def preview_cleaning(self, filename: str, sample_size: int = 500) -> Dict[str, Any]:
        """
        Preview text cleaning without saving the result.
        
        Args:
            filename: Name of the PDF file
            sample_size: Number of characters to preview
            
        Returns:
            Dictionary with cleaning preview
        """
        # Get extracted text
        extraction_metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_extraction_metadata.json")
        
        if not os.path.exists(extraction_metadata_path):
            raise FileNotFoundError(f"Extracted text not found for: {filename}")
        
        with open(extraction_metadata_path, 'r', encoding='utf-8') as f:
            extraction_data = json.load(f)
        
        original_text = extraction_data["text"]
        
        # Take a sample
        original_sample = original_text[:sample_size]
        
        # Apply basic cleaning
        cleaned_sample = self._normalize_whitespace(original_sample)
        cleaned_sample = self._remove_special_characters(cleaned_sample)
        
        return {
            "original_sample": original_sample,
            "cleaned_sample": cleaned_sample,
            "preview_length": len(cleaned_sample)
        }

"""
Enhanced PDF Extractor Service - Optimized PDF text extraction and OCR
with improved performance and multi-language support (English, Hindi, Marathi)
"""

import os
import json
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, Any, Optional, List, Tuple
import io
import asyncio
import concurrent.futures
from functools import lru_cache
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    # OpenCV not available - will use PIL-only preprocessing

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: Transformers not available. Advanced OCR will be disabled.")


class EnhancedPDFExtractor:
    """Enhanced PDF extractor with optimized OCR and multi-language support."""

    def __init__(self):
        self.upload_dir = os.getenv("UPLOADS_DIR", "uploads")
        self.output_dir = os.getenv("OUTPUTS_DIR", "outputs")
        self.ensure_directories()
        
        # Configure tesseract path
        self._configure_tesseract()
        
        # Thread pool for parallel processing
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        # OCR pipeline for advanced text recognition
        self._ocr_pipeline = None
        
        # Language-specific OCR configurations
        self.ocr_configs = {
            "eng": "--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?;:()[]{}'\"- ",
            "hin": "--psm 6",
            "mar": "--psm 6",
            "eng+hin": "--psm 6",
            "eng+mar": "--psm 6",
            "eng+hin+mar": "--psm 6"
        }

    def ensure_directories(self):
        """Ensure necessary directories exist."""
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def _configure_tesseract(self):
        """Configure Tesseract OCR with fallback paths."""
        tesseract_cmd = os.getenv("TESSERACT_CMD")
        if tesseract_cmd and os.path.exists(tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        else:
            # Try common Windows paths
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv("USERNAME", "")),
                "/usr/bin/tesseract",  # Linux
                "/usr/local/bin/tesseract",  # macOS
                "tesseract"  # In PATH
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        
        # Configure tessdata prefix for language packs
        tessdata_prefix = os.getenv("TESSDATA_PREFIX")
        if tessdata_prefix:
            os.environ["TESSDATA_PREFIX"] = tessdata_prefix

    async def extract_text_from_pdf(
        self,
        filename: str,
        use_ocr: bool = False,
        page_range: Optional[str] = None,
        lang: str = "eng+hin+mar",
        chunk_size: int = 50,
        ocr_quality: str = "high",
        preprocess_images: bool = True
    ) -> Dict[str, Any]:
        """
        Enhanced PDF text extraction with optimized OCR and image preprocessing.

        Args:
            filename: Name of the PDF file
            use_ocr: Whether to use OCR for scanned PDFs
            page_range: Specific pages to extract (e.g., "1-5" or "1,3,5")
            lang: Languages for OCR (default = "eng+hin+mar")
            chunk_size: Number of pages to process at once (default = 50)
            ocr_quality: OCR quality setting ("low", "medium", "high")
            preprocess_images: Whether to preprocess images before OCR

        Returns:
            Dictionary with extracted text and metadata
        """
        file_path = os.path.join(self.upload_dir, filename)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {filename}")

        # Check file size and warn if very large
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size_mb > 100:  # Warn for files > 100MB
            print(f"Warning: Large PDF detected ({file_size_mb:.1f}MB). Processing may take time.")

        # Open PDF
        doc = fitz.open(file_path)
        total_pages = len(doc)

        # Parse page range
        pages_to_extract = self._parse_page_range(page_range, total_pages)
        
        # Limit pages for very large PDFs if no specific range given
        if not page_range and total_pages > 1000:
            pages_to_extract = pages_to_extract[:1000]  # Limit to first 1000 pages
            print(f"Warning: PDF has {total_pages} pages. Processing first 1000 pages only.")

        extracted_text = ""
        extraction_method = "direct" if not use_ocr else f"ocr({lang})"
        ocr_stats = {"pages_processed": 0, "text_length": 0, "processing_time": 0}

        # Process pages in chunks to manage memory
        start_time = asyncio.get_event_loop().time()
        
        for i in range(0, len(pages_to_extract), chunk_size):
            chunk_pages = pages_to_extract[i:i + chunk_size]
            
            # Process chunk pages in parallel
            chunk_tasks = []
            for page_num in chunk_pages:
                task = self._process_page_async(
                    doc, page_num, use_ocr, lang, ocr_quality, preprocess_images
                )
                chunk_tasks.append(task)
            
            # Wait for all pages in chunk to complete
            chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)
            
            for page_num, result in zip(chunk_pages, chunk_results):
                if isinstance(result, Exception):
                    print(f"Error processing page {page_num}: {str(result)}")
                    continue
                
                page_text = result
                extracted_text += f"\n--- Page {page_num} ---\n{page_text}\n"
                ocr_stats["pages_processed"] += 1
                ocr_stats["text_length"] += len(page_text)
                
                # Progress indicator for large PDFs
                if len(pages_to_extract) > 100 and page_num % 50 == 0:
                    print(f"Processed {page_num} of {len(pages_to_extract)} pages...")

        doc.close()
        ocr_stats["processing_time"] = asyncio.get_event_loop().time() - start_time

        # Save extracted text in chunks if very large
        output_filename = f"{os.path.splitext(filename)[0]}_extracted.txt"
        output_path = os.path.join(self.output_dir, output_filename)

        if len(extracted_text) > 10 * 1024 * 1024:  # If text > 10MB
            # Save in chunks to avoid memory issues
            self._save_large_text(extracted_text, output_path)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)

        # Save metadata
        metadata = {
            "text": extracted_text,
            "page_count": len(pages_to_extract),
            "total_pages": total_pages,
            "method": extraction_method,
            "file_path": output_path,
            "pages_extracted": pages_to_extract,
            "file_size_mb": file_size_mb,
            "text_size_mb": len(extracted_text) / (1024 * 1024),
            "ocr_stats": ocr_stats,
            "ocr_quality": ocr_quality,
            "preprocessing_enabled": preprocess_images
        }

        metadata_path = os.path.join(
            self.output_dir,
            f"{os.path.splitext(filename)[0]}_extraction_metadata.json",
        )
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return metadata

    async def _process_page_async(
        self, 
        doc: fitz.Document, 
        page_num: int, 
        use_ocr: bool, 
        lang: str, 
        ocr_quality: str,
        preprocess_images: bool
    ) -> str:
        """Process a single page asynchronously."""
        loop = asyncio.get_event_loop()
        
        def process_page():
            try:
                page = doc[page_num - 1]  # PyMuPDF uses 0-based indexing
                
                if use_ocr:
                    return self._extract_text_with_enhanced_ocr(
                        page, lang=lang, quality=ocr_quality, preprocess=preprocess_images
                    )
                else:
                    return page.get_text()
            except Exception as e:
                print(f"Error processing page {page_num}: {str(e)}")
                return ""
        
        return await loop.run_in_executor(self._thread_pool, process_page)

    def _extract_text_with_enhanced_ocr(
        self, 
        page, 
        lang: str = "eng+hin+mar", 
        quality: str = "high",
        preprocess: bool = True
    ) -> str:
        """
        Enhanced OCR text extraction with image preprocessing and quality optimization.

        Args:
            page: PyMuPDF page object
            lang: OCR languages (e.g., "eng", "hin", "mar", or "eng+hin+mar")
            quality: OCR quality setting ("low", "medium", "high")
            preprocess: Whether to preprocess images before OCR

        Returns:
            str: Extracted text
        """
        # Convert page to image with quality-based resolution
        resolution_multiplier = self._get_resolution_multiplier(quality)
        mat = fitz.Matrix(resolution_multiplier, resolution_multiplier)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")

        # Convert to PIL Image
        image = Image.open(io.BytesIO(img_data))

        # Preprocess image if enabled
        if preprocess:
            image = self._preprocess_image(image, quality)

        # Get OCR configuration
        config = self.ocr_configs.get(lang, "--psm 6")

        # Extract text using OCR with given languages and configuration
        try:
            text = pytesseract.image_to_string(image, lang=lang, config=config)
            
            # Post-process text for better quality
            text = self._post_process_text(text)
            
            return text
            
        except Exception as e:
            print(f"OCR error: {str(e)}")
            # Fallback to basic OCR without preprocessing
            try:
                return pytesseract.image_to_string(image, lang=lang)
            except Exception as e2:
                print(f"Fallback OCR also failed: {str(e2)}")
                return ""

    def _get_resolution_multiplier(self, quality: str) -> float:
        """Get resolution multiplier based on quality setting."""
        multipliers = {
            "low": 1.0,
            "medium": 1.5,
            "high": 2.0
        }
        return multipliers.get(quality, 2.0)

    def _preprocess_image(self, image: Image.Image, quality: str) -> Image.Image:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: PIL Image object
            quality: Quality setting for preprocessing intensity
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL to numpy array for OpenCV processing
            if CV2_AVAILABLE:
                img_array = np.array(image)
                
                # Convert RGB to BGR for OpenCV
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                # Apply preprocessing based on quality
                if quality == "high":
                    # High quality preprocessing
                    img_bgr = self._apply_high_quality_preprocessing(img_bgr)
                elif quality == "medium":
                    # Medium quality preprocessing
                    img_bgr = self._apply_medium_quality_preprocessing(img_bgr)
                else:
                    # Low quality preprocessing
                    img_bgr = self._apply_low_quality_preprocessing(img_bgr)
                
                # Convert back to RGB
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(img_rgb)
            else:
                # Fallback to PIL-only preprocessing
                image = self._apply_pil_preprocessing(image, quality)
            
            return image
            
        except Exception as e:
            print(f"Image preprocessing error: {str(e)}")
            return image

    def _apply_high_quality_preprocessing(self, img_bgr) -> np.ndarray:
        """Apply high-quality image preprocessing."""
        # Convert to grayscale
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Convert back to 3-channel for consistency
        return cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)

    def _apply_medium_quality_preprocessing(self, img_bgr) -> np.ndarray:
        """Apply medium-quality image preprocessing."""
        # Convert to grayscale
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply thresholding
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to 3-channel
        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    def _apply_low_quality_preprocessing(self, img_bgr) -> np.ndarray:
        """Apply low-quality image preprocessing."""
        # Convert to grayscale
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Simple thresholding
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Convert back to 3-channel
        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    def _apply_pil_preprocessing(self, image: Image.Image, quality: str) -> Image.Image:
        """Apply PIL-only image preprocessing."""
        try:
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            if quality in ["medium", "high"]:
                # Apply additional enhancements for medium/high quality
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(1.05)
                
                # Apply slight blur to reduce noise
                image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
            
        except Exception as e:
            print(f"PIL preprocessing error: {str(e)}")
            return image

    def _post_process_text(self, text: str) -> str:
        """Post-process OCR text to improve quality."""
        if not text:
            return text
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Fix common OCR errors
        text = text.replace('|', 'I')  # Common OCR error
        text = text.replace('0', 'O')  # In certain contexts
        
        # Remove single characters that are likely noise
        words = text.split()
        cleaned_words = []
        
        for word in words:
            # Keep words that are longer than 1 character or are common single letters
            if len(word) > 1 or word.lower() in ['a', 'i', 'o']:
                cleaned_words.append(word)
        
        return ' '.join(cleaned_words)

    def _parse_page_range(self, page_range: Optional[str], total_pages: int) -> List[int]:
        """
        Parse page range string into list of page numbers.

        Args:
            page_range: Page range string (e.g., "1-5" or "1,3,5")
            total_pages: Total number of pages in PDF

        Returns:
            List of page numbers to extract
        """
        if not page_range:
            return list(range(1, total_pages + 1))

        pages = []
        parts = page_range.split(",")

        for part in parts:
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-"))
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))

        # Filter valid pages
        return [p for p in pages if 1 <= p <= total_pages]

    def get_extracted_text(self, filename: str) -> Dict[str, Any]:
        """
        Get previously extracted text.

        Args:
            filename: Name of the PDF file

        Returns:
            Dictionary with extracted text and metadata
        """
        metadata_path = os.path.join(
            self.output_dir,
            f"{os.path.splitext(filename)[0]}_extraction_metadata.json",
        )

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Extracted text not found for: {filename}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        return metadata

    async def get_pdf_info(self, filename: str) -> Dict[str, Any]:
        """
        Get PDF file information without extracting text.

        Args:
            filename: Name of the PDF file

        Returns:
            Dictionary with PDF information
        """
        file_path = os.path.join(self.upload_dir, filename)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {filename}")

        doc = fitz.open(file_path)

        info = {
            "filename": filename,
            "page_count": len(doc),
            "file_size": os.path.getsize(file_path),
            "metadata": doc.metadata,
            "is_encrypted": doc.is_encrypted,
            "needs_password": doc.needs_pass,
        }

        doc.close()
        return info

    def _save_large_text(self, text: str, output_path: str, chunk_size: int = 1024 * 1024):
        """
        Save large text in chunks to avoid memory issues.
        
        Args:
            text: Text to save
            output_path: Path to save the text
            chunk_size: Size of each chunk in bytes
        """
        with open(output_path, "w", encoding="utf-8") as f:
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                f.write(chunk)
                f.flush()  # Ensure data is written to disk

    async def detect_text_type(self, filename: str, sample_pages: int = 3) -> Dict[str, Any]:
        """
        Detect if PDF contains searchable text or requires OCR.
        
        Args:
            filename: Name of the PDF file
            sample_pages: Number of pages to sample for detection
            
        Returns:
            Dictionary with text type detection results
        """
        file_path = os.path.join(self.upload_dir, filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {filename}")
        
        doc = fitz.open(file_path)
        total_pages = len(doc)
        
        # Sample pages for analysis
        sample_size = min(sample_pages, total_pages)
        sample_pages_list = [i for i in range(0, sample_size)]
        
        text_lengths = []
        has_images = []
        
        for page_num in sample_pages_list:
            page = doc[page_num]
            
            # Get text length
            text = page.get_text()
            text_lengths.append(len(text.strip()))
            
            # Check for images
            image_list = page.get_images()
            has_images.append(len(image_list) > 0)
        
        doc.close()
        
        # Analyze results
        avg_text_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
        has_image_pages = sum(has_images)
        
        # Determine text type
        if avg_text_length < 50:  # Very little text
            text_type = "scanned"
            recommendation = "Use OCR for better results"
        elif avg_text_length < 200 and has_image_pages > 0:  # Mixed content
            text_type = "mixed"
            recommendation = "Try direct extraction first, use OCR if needed"
        else:  # Good amount of text
            text_type = "searchable"
            recommendation = "Direct extraction should work well"
        
        return {
            "text_type": text_type,
            "recommendation": recommendation,
            "avg_text_length": avg_text_length,
            "pages_with_images": has_image_pages,
            "total_pages_analyzed": sample_size,
            "confidence": "high" if avg_text_length > 200 or avg_text_length < 50 else "medium"
        }

    def __del__(self):
        """Cleanup thread pool on destruction."""
        if hasattr(self, '_thread_pool'):
            self._thread_pool.shutdown(wait=False)


# Backward compatibility alias
PDFExtractor = EnhancedPDFExtractor

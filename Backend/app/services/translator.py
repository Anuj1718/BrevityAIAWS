"""
Enhanced Translation Service - Supports multiple translation methods
including online translators and local models for English to Hindi/Marathi
"""

import os
import json
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import concurrent.futures
from functools import lru_cache

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch and transformers not available. Local translation will be disabled.")


class TranslationProvider(ABC):
    """Abstract base class for translation providers."""
    
    @abstractmethod
    async def translate(self, text: str, target_lang: str, source_lang: str = "en") -> str:
        """Translate text from source to target language."""
        pass


class GoogleTranslateProvider(TranslationProvider):
    """Google Translate API provider using unofficial API."""
    
    def __init__(self):
        self.base_url = "https://translate.googleapis.com/translate_a/single"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def translate(self, text: str, target_lang: str, source_lang: str = "en") -> str:
        """Translate text using Google Translate API."""
        try:
            params = {
                "client": "gtx",
                "sl": source_lang,
                "tl": target_lang,
                "dt": "t",
                "q": text
            }
            
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            
            result = response.json()
            if result and len(result) > 0 and result[0]:
                translated_text = ""
                for item in result[0]:
                    if item and len(item) > 0:
                        translated_text += item[0]
                return translated_text.strip()
            
            return text
            
        except Exception as e:
            print(f"Google Translate error: {str(e)}")
            return text
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


class LibreTranslateProvider(TranslationProvider):
    """LibreTranslate API provider."""
    
    def __init__(self, api_url: str = "https://libretranslate.de/translate"):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def translate(self, text: str, target_lang: str, source_lang: str = "en") -> str:
        """Translate text using LibreTranslate API."""
        try:
            data = {
                "q": text,
                "source": source_lang,
                "target": target_lang,
                "format": "text"
            }
            
            response = await self.client.post(self.api_url, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result.get("translatedText", text)
            
        except Exception as e:
            print(f"LibreTranslate error: {str(e)}")
            return text
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


class LocalTranslationProvider(TranslationProvider):
    """Local translation using T5 or Marian models."""
    
    def __init__(self):
        self._t5_model = None
        self._t5_tokenizer = None
        self._marian_model = None
        self._marian_tokenizer = None
        self._translation_pipeline = None
    
    async def translate(self, text: str, target_lang: str, source_lang: str = "en") -> str:
        """Translate text using local models."""
        if not TORCH_AVAILABLE:
            return text
        
        # Load appropriate model based on target language
        if target_lang.lower() in ["hi", "hindi"]:
            return await self._translate_to_hindi(text)
        elif target_lang.lower() in ["mr", "marathi"]:
            return await self._translate_to_marathi(text)
        else:
            return await self._translate_with_t5(text, target_lang)
    
    async def _translate_to_hindi(self, text: str) -> str:
        """Translate to Hindi using Marian model."""
        try:
            if self._marian_model is None:
                self._load_marian_model("Helsinki-NLP/opus-mt-en-hi")
            
            # Use pipeline for better performance
            if self._translation_pipeline is None:
                self._translation_pipeline = pipeline(
                    "translation_en_to_hi",
                    model="Helsinki-NLP/opus-mt-en-hi",
                    device=0 if torch.cuda.is_available() else -1
                )
            
            # Split text into chunks for better processing
            chunks = self._split_text(text, max_length=500)
            translated_chunks = []
            
            for chunk in chunks:
                if len(chunk.strip()) > 10:  # Only translate substantial chunks
                    result = self._translation_pipeline(chunk)
                    translated_chunks.append(result[0]["translation_text"])
            
            return " ".join(translated_chunks)
            
        except Exception as e:
            print(f"Hindi translation error: {str(e)}")
            return text
    
    async def _translate_to_marathi(self, text: str) -> str:
        """Translate to Marathi using T5 model."""
        try:
            if self._t5_model is None:
                self._load_t5_model()
            
            # Use T5 for Marathi translation
            chunks = self._split_text(text, max_length=500)
            translated_chunks = []
            
            for chunk in chunks:
                if len(chunk.strip()) > 10:
                    input_text = f"translate English to Marathi: {chunk}"
                    inputs = self._t5_tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
                    
                    with torch.no_grad():
                        outputs = self._t5_model.generate(
                            **inputs,
                            max_length=512,
                            num_beams=4,
                            early_stopping=True
                        )
                    
                    translated_chunk = self._t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
                    translated_chunks.append(translated_chunk)
            
            return " ".join(translated_chunks)
            
        except Exception as e:
            print(f"Marathi translation error: {str(e)}")
            return text
    
    async def _translate_with_t5(self, text: str, target_lang: str) -> str:
        """Generic T5 translation."""
        try:
            if self._t5_model is None:
                self._load_t5_model()
            
            chunks = self._split_text(text, max_length=500)
            translated_chunks = []
            
            for chunk in chunks:
                if len(chunk.strip()) > 10:
                    input_text = f"translate English to {target_lang}: {chunk}"
                    inputs = self._t5_tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
                    
                    with torch.no_grad():
                        outputs = self._t5_model.generate(
                            **inputs,
                            max_length=512,
                            num_beams=4,
                            early_stopping=True
                        )
                    
                    translated_chunk = self._t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
                    translated_chunks.append(translated_chunk)
            
            return " ".join(translated_chunks)
            
        except Exception as e:
            print(f"T5 translation error: {str(e)}")
            return text
    
    def _load_t5_model(self):
        """Load T5 model for translation."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch and transformers are required for local translation.")
        
        self._t5_tokenizer = AutoTokenizer.from_pretrained("t5-small")
        self._t5_model = AutoModelForSeq2SeqLM.from_pretrained(
            "t5-small",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
    
    def _load_marian_model(self, model_name: str):
        """Load Marian model for translation."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch and transformers are required for local translation.")
        
        self._marian_tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._marian_model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
    
    def _split_text(self, text: str, max_length: int = 500) -> List[str]:
        """Split text into manageable chunks."""
        sentences = text.split(". ")
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk.split()) + len(sentence.split()) <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


class EnhancedTranslator:
    """Enhanced translator with multiple providers and fallback mechanisms."""
    
    def __init__(self):
        self.output_dir = os.getenv("OUTPUTS_DIR", "outputs")
        self.ensure_directories()
        
        # Initialize providers
        self.google_provider = GoogleTranslateProvider()
        self.libre_provider = LibreTranslateProvider()
        self.local_provider = LocalTranslationProvider()
        
        # Thread pool for parallel processing
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        
        # Language mapping
        self.language_codes = {
            "hindi": "hi",
            "marathi": "mr",
            "english": "en",
            "hi": "hi",
            "mr": "mr",
            "en": "en"
        }
    
    def ensure_directories(self):
        """Ensure necessary directories exist."""
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def translate_text(
        self, 
        text: str, 
        target_language: str, 
        source_language: str = "en",
        provider: str = "auto",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Translate text using specified provider with fallback mechanisms.
        
        Args:
            text: Text to translate
            target_language: Target language (hindi, marathi, etc.)
            source_language: Source language (default: en)
            provider: Translation provider (google, libre, local, auto)
            use_cache: Whether to use caching
            
        Returns:
            Dictionary with translation results and metadata
        """
        if not text or not text.strip():
            return {
                "original_text": text,
                "translated_text": text,
                "source_language": source_language,
                "target_language": target_language,
                "provider": "none",
                "success": True,
                "cached": False
            }
        
        # Normalize language codes
        target_lang = self.language_codes.get(target_language.lower(), target_language.lower())
        source_lang = self.language_codes.get(source_language.lower(), source_language.lower())
        
        # Check cache if enabled
        if use_cache:
            cached_result = self._get_cached_translation(text, target_lang, source_lang)
            if cached_result:
                return cached_result
        
        # Choose provider
        if provider == "auto":
            provider = self._choose_best_provider(target_lang)
        
        # Translate using chosen provider
        translated_text = await self._translate_with_provider(
            text, target_lang, source_lang, provider
        )
        
        # Cache result if enabled
        if use_cache:
            self._cache_translation(text, translated_text, target_lang, source_lang, provider)
        
        return {
            "original_text": text,
            "translated_text": translated_text,
            "source_language": source_lang,
            "target_language": target_lang,
            "provider": provider,
            "success": True,
            "cached": False,
            "character_count": len(text),
            "translation_ratio": len(translated_text) / len(text) if len(text) > 0 else 1.0
        }
    
    async def translate_summary(
        self, 
        filename: str, 
        summary_type: str = "hybrid",
        target_language: str = "hindi",
        provider: str = "auto"
    ) -> Dict[str, Any]:
        """
        Translate a summary file to target language.
        
        Args:
            filename: Name of the PDF file
            summary_type: Type of summary (extractive, abstractive, hybrid, formatted_hybrid)
            target_language: Target language for translation
            provider: Translation provider to use
            
        Returns:
            Dictionary with translated summary and metadata
        """
        # Get summary metadata - handle formatted-hybrid naming difference
        base_name = os.path.splitext(filename)[0]
        if summary_type in ("formatted-hybrid", "formatted_hybrid"):
            # Formatted hybrid saves as _formatted_summary.json (different pattern)
            summary_metadata_path = os.path.join(
                self.output_dir, f"{base_name}_formatted_summary.json"
            )
        else:
            summary_metadata_path = os.path.join(
                self.output_dir, f"{base_name}_{summary_type}_summary_metadata.json"
            )
        
        if not os.path.exists(summary_metadata_path):
            raise FileNotFoundError(f"{summary_type.title()} summary not found for: {filename}")
        
        with open(summary_metadata_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Formatted hybrid uses 'final_abstract' key; others use 'summary_text'
        summary_text = (
            summary_data.get("summary_text")
            or summary_data.get("final_abstract")
            or ""
        )
        
        # Translate the summary
        translation_result = await self.translate_text(
            summary_text, 
            target_language, 
            provider=provider
        )
        
        # Save translated summary
        translated_filename = f"{os.path.splitext(filename)[0]}_{summary_type}_summary_{target_language}.txt"
        translated_path = os.path.join(self.output_dir, translated_filename)
        
        with open(translated_path, 'w', encoding='utf-8') as f:
            f.write(translation_result["translated_text"])
        
        # Create metadata for translated summary
        translated_metadata = {
            "original_summary": summary_text,
            "translated_summary": translation_result["translated_text"],
            "source_language": "en",
            "target_language": target_language,
            "summary_type": summary_type,
            "provider": translation_result["provider"],
            "file_path": translated_path,
            "translation_metadata": translation_result
        }
        
        metadata_path = os.path.join(
            self.output_dir, 
            f"{os.path.splitext(filename)[0]}_{summary_type}_summary_{target_language}_metadata.json"
        )
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(translated_metadata, f, indent=2, ensure_ascii=False)
        
        return translated_metadata
    
    async def _translate_with_provider(
        self, 
        text: str, 
        target_lang: str, 
        source_lang: str, 
        provider: str
    ) -> str:
        """Translate text using specified provider with fallback."""
        try:
            if provider == "google":
                # Create a new instance to avoid client closure issues
                google_provider = GoogleTranslateProvider()
                try:
                    return await google_provider.translate(text, target_lang, source_lang)
                finally:
                    await google_provider.client.aclose()
            elif provider == "libre":
                # Create a new instance to avoid client closure issues
                libre_provider = LibreTranslateProvider()
                try:
                    return await libre_provider.translate(text, target_lang, source_lang)
                finally:
                    await libre_provider.client.aclose()
            elif provider == "local":
                return await self.local_provider.translate(text, target_lang, source_lang)
            else:
                # Try providers in order of preference
                providers_to_try = ["google", "libre", "local"]
                for p in providers_to_try:
                    try:
                        return await self._translate_with_provider(text, target_lang, source_lang, p)
                    except Exception as e:
                        print(f"Provider {p} failed: {str(e)}")
                        continue
                
                # If all providers fail, return original text
                return text
                
        except Exception as e:
            print(f"Translation error with provider {provider}: {str(e)}")
            return text
    
    def _choose_best_provider(self, target_lang: str) -> str:
        """Choose the best provider based on target language."""
        if target_lang in ["hi", "mr"]:  # Hindi or Marathi
            return "google"  # Google has better support for Indian languages
        elif target_lang in ["en", "fr", "de", "es", "it", "pt"]:  # European languages
            return "libre"  # LibreTranslate is more reliable for European languages
        else:
            return "google"  # Default to Google for other languages
    
    def _get_cached_translation(self, text: str, target_lang: str, source_lang: str) -> Optional[Dict[str, Any]]:
        """Get cached translation if available."""
        cache_key = f"{hash(text)}_{source_lang}_{target_lang}"
        cache_file = os.path.join(self.output_dir, f"translation_cache_{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                cached_data["cached"] = True
                return cached_data
            except Exception:
                pass
        
        return None
    
    def _cache_translation(self, text: str, translated_text: str, target_lang: str, source_lang: str, provider: str):
        """Cache translation result."""
        cache_key = f"{hash(text)}_{source_lang}_{target_lang}"
        cache_file = os.path.join(self.output_dir, f"translation_cache_{cache_key}.json")
        
        cache_data = {
            "original_text": text,
            "translated_text": translated_text,
            "source_language": source_lang,
            "target_language": target_lang,
            "provider": provider,
            "cached": False
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to cache translation: {str(e)}")
    
    def get_supported_languages(self) -> Dict[str, List[str]]:
        """Get list of supported languages by provider."""
        return {
            "google": ["hi", "mr", "en", "fr", "de", "es", "it", "pt", "ru", "ja", "ko", "zh"],
            "libre": ["hi", "mr", "en", "fr", "de", "es", "it", "pt", "ru", "ja", "ko", "zh"],
            "local": ["hi", "mr", "en"]  # Limited by available models
        }
    
    def __del__(self):
        """Cleanup thread pool on destruction."""
        if hasattr(self, '_thread_pool'):
            self._thread_pool.shutdown(wait=False)

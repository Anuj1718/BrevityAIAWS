"""
Optimized Text Summarizer Service - Handles text summarization with performance improvements
(extractive + abstractive + hybrid + universal formatted summary)
"""

import os
import re
import json
import numpy as np
import asyncio
from typing import Dict, Any, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from app.utils.text_utils import TextUtils
import concurrent.futures
from functools import lru_cache

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch and transformers not available. Abstractive summarization will be disabled.")


class OptimizedTextSummarizer:
    """Optimized text summarizer with performance improvements and caching."""

    def __init__(self):
        self.output_dir = "outputs"
        self.text_utils = TextUtils()
        self.ensure_directories()
        
        # Model caching for better performance
        self._abstractive_model = None
        self._abstractive_tokenizer = None
        self._summarization_pipeline = None
        
        # Thread pool for CPU-intensive tasks
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        # Cache for similarity matrices
        self._similarity_cache = {}

    def ensure_directories(self):
        os.makedirs(self.output_dir, exist_ok=True)

    # -------------------- Optimized Extractive Summary --------------------
    async def extractive_summary(
        self, 
        filename: str, 
        summary_ratio: float = 0.3, 
        algorithm: str = "textrank",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Optimized extractive summary with caching and parallel processing."""
        
        cleaning_metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_cleaning_metadata.json")
        if not os.path.exists(cleaning_metadata_path):
            raise FileNotFoundError(f"Cleaned text not found for: {filename}")

        with open(cleaning_metadata_path, 'r', encoding='utf-8') as f:
            cleaning_data = json.load(f)
        
        sentences = cleaning_data.get("sentences") or []
        if not sentences:
            cleaned_text = cleaning_data.get("cleaned_text", "")
            sentences = self.text_utils.split_into_sentences(cleaned_text)
        if not sentences:
            cleaned_text = cleaning_data.get("cleaned_text", "")
            sentences = self.text_utils.chunk_text_by_words(cleaned_text, chunk_size=25)
        original_sentences = len(sentences)
        if original_sentences == 0:
            raise ValueError("No sentences found in cleaned text")

        num_sentences = max(1, int(original_sentences * summary_ratio))

        # Use optimized algorithms with caching
        if algorithm == "textrank":
            summary_sentences = await self._optimized_textrank_summarize(sentences, num_sentences, use_cache)
        elif algorithm == "tfidf":
            summary_sentences = await self._optimized_tfidf_summarize(sentences, num_sentences)
        elif algorithm == "lsa":
            summary_sentences = await self._optimized_lsa_summarize(sentences, num_sentences)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        summary_text = " ".join(summary_sentences)
        # Compression ratio = how much was removed (0.7 = 70% compression)
        compression_ratio = 1 - (len(summary_sentences) / original_sentences)
        
        # Calculate word counts for display
        summary_word_count = len(summary_text.split())
        # Estimate original word count from sentences
        full_text = " ".join(sentences)
        original_word_count = len(full_text.split())

        output_filename = f"{os.path.splitext(filename)[0]}_extractive_summary.txt"
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)

        metadata = {
            "summary_text": summary_text,
            "summary_sentences": summary_sentences,
            "original_sentences": original_sentences,
            "original_length": original_word_count,
            "summary_length": summary_word_count,
            "compression_ratio": compression_ratio,
            "algorithm": algorithm,
            "summary_ratio": summary_ratio,
            "file_path": output_path,
            "processing_time": "optimized"
        }
        metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_extractive_summary_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        return metadata

    # -------------------- Optimized Abstractive Summary --------------------
    async def abstractive_summary(
        self, 
        filename: str, 
        max_length: int = 150, 
        min_length: int = 30, 
        model: str = "facebook/bart-large-cnn",
        use_pipeline: bool = True
    ) -> Dict[str, Any]:
        """Optimized abstractive summary with pipeline and chunking improvements."""

        cleaning_metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_cleaning_metadata.json")
        if not os.path.exists(cleaning_metadata_path):
            raise FileNotFoundError(f"Cleaned text not found for: {filename}")

        with open(cleaning_metadata_path, 'r', encoding='utf-8') as f:
            cleaning_data = json.load(f)
        text = cleaning_data["cleaned_text"]
        original_length = len(text)

        if not TORCH_AVAILABLE:
            return await self._heuristic_abstractive_summary(
                filename=filename,
                text=text,
                max_length=max_length,
                min_length=min_length,
            )

        # Use pipeline for better performance if available
        if use_pipeline and self._summarization_pipeline is None:
            self._load_summarization_pipeline(model)

        if use_pipeline and self._summarization_pipeline is not None:
            summary_text = await self._pipeline_summarize(text, max_length, min_length)
        else:
            # Fallback to chunked processing
            if self._abstractive_model is None or self._abstractive_tokenizer is None:
                self._load_abstractive_model(model)
            summary_text = await self._chunked_summarize(text, max_length, min_length)

        # Calculate using word counts
        original_word_count = len(text.split())
        summary_word_count = len(summary_text.split())
        compression_ratio = 1 - (summary_word_count / original_word_count) if original_word_count > 0 else 0

        output_filename = f"{os.path.splitext(filename)[0]}_abstractive_summary.txt"
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)

        metadata = {
            "summary_text": summary_text,
            "original_length": original_word_count,
            "summary_length": summary_word_count,
            "compression_ratio": compression_ratio,
            "model": model,
            "max_length": max_length,
            "min_length": min_length,
            "file_path": output_path,
            "processing_method": "pipeline" if use_pipeline else "chunked"
        }
        metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_abstractive_summary_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        return metadata

    async def _heuristic_abstractive_summary(
        self,
        filename: str,
        text: str,
        max_length: int,
        min_length: int,
    ) -> Dict[str, Any]:
        """Provide a lightweight abstractive-style fallback when ML models are unavailable."""
        sentences = self.text_utils.split_into_sentences(text)
        if not sentences:
            sentences = self.text_utils.chunk_text_by_words(text, chunk_size=20)

        if not sentences:
            raise ValueError("No sentences available for abstractive summarization")

        target_count = max(2, min(5, len(sentences)))
        summary_sentences = await self._optimized_tfidf_summarize(sentences, target_count)
        summary_sentences = [self._lightly_rephrase_sentence(sentence) for sentence in summary_sentences]
        summary_text = self._compose_narrative_summary(summary_sentences, max_length, min_length)

        original_word_count = len(text.split())
        summary_word_count = len(summary_text.split())
        compression_ratio = 1 - (summary_word_count / original_word_count) if original_word_count > 0 else 0

        output_filename = f"{os.path.splitext(filename)[0]}_abstractive_summary.txt"
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)

        metadata = {
            "summary_text": summary_text,
            "original_length": original_word_count,
            "summary_length": summary_word_count,
            "compression_ratio": compression_ratio,
            "model": "heuristic-fallback",
            "max_length": max_length,
            "min_length": min_length,
            "file_path": output_path,
            "processing_method": "heuristic",
            "fallback_used": True,
        }

        metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_abstractive_summary_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return metadata

    def _lightly_rephrase_sentence(self, sentence: str) -> str:
        """Make summary sentences read more like prose."""
        sentence = re.sub(r"^[\-•*\d\.)\s]+", "", sentence).strip()
        sentence = re.sub(r"\s+", " ", sentence)
        if not sentence:
            return sentence
        return sentence[0].upper() + sentence[1:]

    def _compose_narrative_summary(self, sentences: List[str], max_length: int, min_length: int) -> str:
        """Combine selected sentences into a compact narrative paragraph."""
        if not sentences:
            return ""

        parts: List[str] = []
        for index, sentence in enumerate(sentences):
            sentence = sentence.strip().rstrip(".")
            if not sentence:
                continue

            if index == 0:
                parts.append(f"This document highlights that {sentence[0].lower() + sentence[1:] if len(sentence) > 1 else sentence}.")
            elif index == len(sentences) - 1:
                parts.append(f"Overall, {sentence[0].lower() + sentence[1:] if len(sentence) > 1 else sentence}.")
            else:
                parts.append(f"Additionally, {sentence[0].lower() + sentence[1:] if len(sentence) > 1 else sentence}.")

        summary_text = " ".join(parts).strip()
        if len(summary_text.split()) < min_length:
            summary_text = " ".join(sentences).strip()

        words = summary_text.split()
        if len(words) > max_length:
            summary_text = " ".join(words[:max_length]).rstrip() + "..."

        return summary_text

    def _load_abstractive_model(self, model_name: str):
        """Load abstractive model with optimizations."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch and transformers are required for abstractive summarization.")
        
        self._abstractive_tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._abstractive_model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )

    def _load_summarization_pipeline(self, model_name: str):
        """Load summarization pipeline for better performance."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch and transformers are required for pipeline summarization.")
        
        self._summarization_pipeline = pipeline(
            "summarization",
            model=model_name,
            device=0 if torch.cuda.is_available() else -1,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )

    async def _pipeline_summarize(self, text: str, max_length: int, min_length: int) -> str:
        """Use pipeline for faster summarization."""
        # Split text into manageable chunks
        chunk_size = 1000
        sentences = text.split(". ")
        chunks, temp_chunk = [], ""
        
        for sentence in sentences:
            if len(temp_chunk.split()) + len(sentence.split()) <= chunk_size:
                temp_chunk += sentence + ". "
            else:
                chunks.append(temp_chunk.strip())
                temp_chunk = sentence + ". "
        if temp_chunk:
            chunks.append(temp_chunk.strip())

        # Process chunks in parallel
        loop = asyncio.get_event_loop()
        summaries = []
        
        for chunk in chunks:
            if len(chunk.strip()) > 50:  # Only process substantial chunks
                summary = await loop.run_in_executor(
                    self._thread_pool,
                    lambda: self._summarization_pipeline(
                        chunk,
                        max_length=max_length,
                        min_length=min_length,
                        do_sample=False
                    )[0]["summary_text"]
                )
                summaries.append(summary)

        return " ".join(summaries)

    async def _chunked_summarize(self, text: str, max_length: int, min_length: int) -> str:
        """Fallback chunked summarization method."""
        chunk_size = 1024
        sentences = text.split(". ")
        chunks, temp_chunk = [], ""
        
        for sentence in sentences:
            if len(temp_chunk.split()) + len(sentence.split()) <= chunk_size:
                temp_chunk += sentence + ". "
            else:
                chunks.append(temp_chunk.strip())
                temp_chunk = sentence + ". "
        if temp_chunk:
            chunks.append(temp_chunk.strip())

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._abstractive_model = self._abstractive_model.to(device)

        summaries = []
        for chunk in chunks:
            inputs = self._abstractive_tokenizer(
                chunk, max_length=1024, truncation=True, return_tensors="pt"
            ).to(device)
            with torch.no_grad():
                summary_ids = self._abstractive_model.generate(
                    inputs["input_ids"], 
                    max_length=max_length, 
                    min_length=min_length, 
                    num_beams=2, 
                    early_stopping=True
                )
            summaries.append(self._abstractive_tokenizer.decode(summary_ids[0], skip_special_tokens=True))

        return " ".join(summaries)

    # -------------------- Optimized Helper Methods --------------------
    async def _optimized_textrank_summarize(self, sentences: List[str], num_sentences: int, use_cache: bool = True) -> List[str]:
        """Optimized TextRank with caching."""
        cache_key = f"textrank_{hash(' '.join(sentences))}"
        
        if use_cache and cache_key in self._similarity_cache:
            similarity_matrix = self._similarity_cache[cache_key]
        else:
            similarity_matrix = await self._create_similarity_matrix_async(sentences)
            if use_cache:
                self._similarity_cache[cache_key] = similarity_matrix
        
        scores = self._pagerank(similarity_matrix)
        sentence_scores = [(scores[i], sentences[i]) for i in range(len(sentences))]
        sentence_scores.sort(key=lambda x: x[0], reverse=True)
        return [sentence for score, sentence in sentence_scores[:num_sentences]]

    async def _optimized_tfidf_summarize(self, sentences: List[str], num_sentences: int) -> List[str]:
        """Optimized TF-IDF summarization."""
        loop = asyncio.get_event_loop()
        
        def compute_tfidf():
            vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
            tfidf_matrix = vectorizer.fit_transform(sentences)
            scores = np.array(tfidf_matrix.sum(axis=1)).flatten()
            sentence_scores = [(scores[i], sentences[i]) for i in range(len(sentences))]
            sentence_scores.sort(key=lambda x: x[0], reverse=True)
            return [sentence for score, sentence in sentence_scores[:num_sentences]]
        
        return await loop.run_in_executor(self._thread_pool, compute_tfidf)

    async def _optimized_lsa_summarize(self, sentences: List[str], num_sentences: int) -> List[str]:
        """Optimized LSA summarization."""
        loop = asyncio.get_event_loop()
        
        def compute_lsa():
            vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
            tfidf_matrix = vectorizer.fit_transform(sentences)
            svd = TruncatedSVD(n_components=min(num_sentences, len(sentences)))
            lsa_matrix = svd.fit_transform(tfidf_matrix)
            scores = np.linalg.norm(lsa_matrix, axis=1)
            sentence_scores = [(scores[i], sentences[i]) for i in range(len(sentences))]
            sentence_scores.sort(key=lambda x: x[0], reverse=True)
            return [sentence for score, sentence in sentence_scores[:num_sentences]]
        
        return await loop.run_in_executor(self._thread_pool, compute_lsa)

    async def _create_similarity_matrix_async(self, sentences: List[str]) -> np.ndarray:
        """Create similarity matrix asynchronously."""
        loop = asyncio.get_event_loop()
        
        def compute_similarity():
            vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
            tfidf_matrix = vectorizer.fit_transform(sentences)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            similarity_matrix = similarity_matrix / (similarity_matrix.sum(axis=1, keepdims=True) + 1e-8)
            return similarity_matrix
        
        return await loop.run_in_executor(self._thread_pool, compute_similarity)

    # -------------------- Optimized Hybrid Summary --------------------
    async def hybrid_summary(
        self, 
        filename: str, 
        extractive_ratio: float = 0.5, 
        max_length: int = 200, 
        min_length: int = 50,
        use_pipeline: bool = True
    ) -> Dict[str, Any]:
        """Optimized hybrid summary combining extractive and abstractive methods."""
        
        # Run extractive summary first
        extractive_result = await self.extractive_summary(
            filename, 
            summary_ratio=extractive_ratio, 
            algorithm="textrank"
        )

        cleaning_metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_cleaning_metadata.json")
        with open(cleaning_metadata_path, 'r', encoding='utf-8') as f:
            cleaning_data = json.load(f)

        original_cleaned_text = cleaning_data["cleaned_text"]
        cleaning_data["cleaned_text"] = extractive_result["summary_text"]
        with open(cleaning_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(cleaning_data, f, ensure_ascii=False, indent=2)

        # Run abstractive summary on extractive result
        hybrid_result = await self.abstractive_summary(
            filename, 
            max_length=max_length, 
            min_length=min_length, 
            model="facebook/bart-large-cnn",
            use_pipeline=use_pipeline
        )

        # Restore original text
        cleaning_data["cleaned_text"] = original_cleaned_text
        with open(cleaning_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(cleaning_data, f, ensure_ascii=False, indent=2)

        output_filename = f"{os.path.splitext(filename)[0]}_hybrid_summary.txt"
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(hybrid_result["summary_text"])

        metadata = {
            "summary_text": hybrid_result["summary_text"],
            "original_length": len(original_cleaned_text),
            "summary_length": hybrid_result["summary_length"],
            "compression_ratio": hybrid_result["compression_ratio"],
            "extractive_ratio": extractive_ratio,
            "file_path": output_path,
            "processing_method": "optimized_hybrid"
        }
        metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_hybrid_summary_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        return metadata

        # -------------------- Universal Formatted Summary --------------------
    async def formatted_hybrid_summary(
        self, 
        filename: str, 
        extractive_ratio: float = 0.5,
        max_length: int = 200, 
        min_length: int = 50,
        use_pipeline: bool = True
    ) -> Dict[str, Any]:
        """Optimized formatted hybrid summary with better structure detection."""
        
        # Step 0: Clean text (remove page markers & emails/phones)
        cleaning_metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_cleaning_metadata.json")
        cleaned_text = ""
        if os.path.exists(cleaning_metadata_path):
            with open(cleaning_metadata_path, 'r', encoding='utf-8') as f:
                cleaning_data = json.load(f)
            cleaned_text = cleaning_data.get("cleaned_text", "")
            # Remove page markers
            cleaned_text = re.sub(r'[-]{2,}\s*Page\s*\d+\s*[-]{2,}', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'Page\s*\d+', '', cleaned_text, flags=re.IGNORECASE)
            # Remove emails & phone numbers
            cleaned_text = re.sub(r'\S+@\S+', '', cleaned_text)
            cleaned_text = re.sub(r'\+?\d[\d\s\-]{7,}\d', '', cleaned_text)
            cleaning_data["cleaned_text"] = cleaned_text
            with open(cleaning_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(cleaning_data, f, indent=2, ensure_ascii=False)

        # Step 1: Abstractive summary
        abstractive_result = await self.abstractive_summary(
            filename, 
            max_length=max_length, 
            min_length=min_length,
            use_pipeline=use_pipeline
        )
        final_abstract = abstractive_result["summary_text"]

        # Step 2: Extractive key points
        extractive_result = await self.extractive_summary(
            filename, 
            summary_ratio=extractive_ratio,
            algorithm="textrank"
        )
        key_points = [s.strip() for s in extractive_result["summary_sentences"]]

        # Step 3: Title & Objective
        sentences = [s.strip() for s in final_abstract.split(".") if s.strip()]
        title = "Untitled"
        objective = "Objective not detected"

        if cleaned_text:
            lines = [line.strip() for line in cleaned_text.split("\n") if line.strip()]
            for line in lines:
                # Short & strong line as title
                if 3 <= len(line.split()) <= 12:
                    title = line
                    break
            else:
                title = sentences[0] if sentences else "Untitled"

        if len(sentences) > 1:
            objective = " ".join(sentences[1:3])

        # Step 4: Section-wise summary
        section_summary_raw = self.text_utils.get_section_wise_summary(cleaning_metadata_path)
        section_summary = {}

        # For resumes: try detecting common sections
        resume_sections = ["Education", "Projects", "Skills", "Work Experience"]
        for sec in resume_sections:
            # Simple regex search in cleaned text
            pattern = re.compile(sec, re.IGNORECASE)
            match = pattern.search(cleaned_text)
            if match:
                start_idx = match.start()
                rest_text = cleaned_text[start_idx:]
                sents = self.text_utils.split_into_sentences(rest_text)[:2]  # take first 1-2 sentences
                section_summary[sec] = " ".join(sents)

        # fallback for other sections
        for sec, sents in section_summary_raw.items():
            if sec not in section_summary:
                if isinstance(sents, list):
                    section_summary[sec] = " ".join(sents[:2])
                else:
                    section_summary[sec] = str(sents)

        # Step 5: Compile formatted summary
        formatted_summary = {
            "title": title,
            "objective": objective,
            "key_points": key_points,
            "section_summary": section_summary,
            "final_abstract": final_abstract,
            "processing_method": "optimized_formatted"
        }

        # Step 6: Save formatted summary
        output_filename = f"{os.path.splitext(filename)[0]}_formatted_summary.json"
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_summary, f, indent=2, ensure_ascii=False)

        formatted_summary["file_path"] = output_path
        return formatted_summary

    # -------------------- Get Existing Summary --------------------
    def get_summary(self, filename: str, summary_type: str) -> Dict[str, Any]:
        """Get existing summary with error handling."""
        metadata_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}_{summary_type}_summary_metadata.json")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"{summary_type.title()} summary not found for: {filename}")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata

    # -------------------- Legacy Helper Methods (for compatibility) --------------------
    def _textrank_summarize(self, sentences: List[str], num_sentences: int) -> List[str]:
        """Legacy TextRank method for compatibility."""
        similarity_matrix = self._create_similarity_matrix(sentences)
        scores = self._pagerank(similarity_matrix)
        sentence_scores = [(scores[i], sentences[i]) for i in range(len(sentences))]
        sentence_scores.sort(key=lambda x: x[0], reverse=True)
        return [sentence for score, sentence in sentence_scores[:num_sentences]]

    def _tfidf_summarize(self, sentences: List[str], num_sentences: int) -> List[str]:
        """Legacy TF-IDF method for compatibility."""
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(sentences)
        scores = np.array(tfidf_matrix.sum(axis=1)).flatten()
        sentence_scores = [(scores[i], sentences[i]) for i in range(len(sentences))]
        sentence_scores.sort(key=lambda x: x[0], reverse=True)
        return [sentence for score, sentence in sentence_scores[:num_sentences]]

    def _lsa_summarize(self, sentences: List[str], num_sentences: int) -> List[str]:
        """Legacy LSA method for compatibility."""
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(sentences)
        svd = TruncatedSVD(n_components=min(num_sentences, len(sentences)))
        lsa_matrix = svd.fit_transform(tfidf_matrix)
        scores = np.linalg.norm(lsa_matrix, axis=1)
        sentence_scores = [(scores[i], sentences[i]) for i in range(len(sentences))]
        sentence_scores.sort(key=lambda x: x[0], reverse=True)
        return [sentence for score, sentence in sentence_scores[:num_sentences]]

    def _create_similarity_matrix(self, sentences: List[str]) -> np.ndarray:
        """Legacy similarity matrix creation for compatibility."""
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(sentences)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        similarity_matrix = similarity_matrix / (similarity_matrix.sum(axis=1, keepdims=True) + 1e-8)
        return similarity_matrix

    def _pagerank(self, similarity_matrix: np.ndarray, damping: float = 0.85, max_iter: int = 100) -> np.ndarray:
        """Optimized PageRank algorithm."""
        n = similarity_matrix.shape[0]
        scores = np.ones(n) / n
        for _ in range(max_iter):
            new_scores = (1 - damping) / n + damping * similarity_matrix.T.dot(scores)
            if np.allclose(scores, new_scores, atol=1e-6):
                break
            scores = new_scores
        return scores

    def __del__(self):
        """Cleanup thread pool on destruction."""
        if hasattr(self, '_thread_pool'):
            self._thread_pool.shutdown(wait=False)


# Backward compatibility alias
TextSummarizer = OptimizedTextSummarizer

"""
Text Utils - Text processing helper functions
"""
import os
import re
import json
import string
import nltk
from typing import List, Dict
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class TextUtils:
    """Utility class for text processing operations."""

    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))

    # ------------------ Basic Cleaning ------------------
    
    def remove_page_markers(self, text: str) -> str:
        # Remove patterns like -- - Page 1 -- - or Page 1, Page 2 etc.
        text = re.sub(r'[-]{2,}\s*Page\s*\d+\s*[-]{2,}', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Page\s*\d+', '', text, flags=re.IGNORECASE)
        return text

    def split_into_sentences(self, text: str) -> List[str]:
        if not text:
            return []

        normalized_text = text.replace("\r\n", "\n").replace("\r", "\n").strip()

        try:
            sentences = sent_tokenize(normalized_text)
        except LookupError:
            sentences = []

        sentences = [sentence.strip() for sentence in sentences if sentence and sentence.strip()]
        if sentences:
            return sentences

        # OCR output often arrives as newline-separated fragments without punctuation.
        line_candidates = [
            re.sub(r"^[\-•*\d\.)\s]+", "", line).strip()
            for line in normalized_text.split("\n")
            if line.strip()
        ]
        line_candidates = [line for line in line_candidates if line]

        if len(line_candidates) > 1:
            line_sentences: List[str] = []
            for line in line_candidates:
                pieces = re.split(r"(?<=[.!?।])\s+|\s{2,}", line)
                pieces = [piece.strip() for piece in pieces if piece and piece.strip()]
                line_sentences.extend(pieces or [line])

            if line_sentences:
                return line_sentences

        # Final fallback: chunk very long OCR blocks into pseudo-sentences.
        return self.chunk_text_by_words(normalized_text, chunk_size=25)

    def chunk_text_by_words(self, text: str, chunk_size: int = 25) -> List[str]:
        """Split long text into pseudo-sentences when punctuation is unavailable."""
        if not text:
            return []

        words = [word for word in text.split() if word.strip()]
        if not words:
            return []

        chunk_size = max(5, chunk_size)
        chunks = [
            " ".join(words[index:index + chunk_size]).strip()
            for index in range(0, len(words), chunk_size)
        ]
        return [chunk for chunk in chunks if chunk]

    def split_into_words(self, text: str) -> List[str]:
        words = word_tokenize(text)
        return [w.strip() for w in words if w.strip()]

    def remove_stopwords(self, text: str) -> str:
        words = self.split_into_words(text)
        filtered_words = [word for word in words if word.lower() not in self.stop_words]
        return ' '.join(filtered_words)

    def stem_words(self, text: str) -> str:
        words = self.split_into_words(text)
        return ' '.join([self.stemmer.stem(word) for word in words])

    def remove_punctuation(self, text: str) -> str:
        return text.translate(str.maketrans('', '', string.punctuation))

    def remove_numbers(self, text: str) -> str:
        return re.sub(r'\d+', '', text)

    def remove_extra_whitespace(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()
    
    

    def clean_text(self, text: str, remove_punctuation: bool = False,
                   remove_numbers: bool = False, remove_stopwords: bool = False,
                   stem_words: bool = False,remove_page_marks: bool = True) -> str:
        cleaned_text = text
        if remove_page_marks:
            cleaned_text = self.remove_page_markers(cleaned_text)
        if remove_punctuation:
            cleaned_text = self.remove_punctuation(cleaned_text)
        if remove_numbers:
            cleaned_text = self.remove_numbers(cleaned_text)
        cleaned_text = self.remove_extra_whitespace(cleaned_text)
        if remove_stopwords:
            cleaned_text = self.remove_stopwords(cleaned_text)
        if stem_words:
            cleaned_text = self.stem_words(cleaned_text)
        return cleaned_text

    # ------------------ Text Analysis ------------------

    def get_word_frequency(self, text: str) -> dict:
        words = self.split_into_words(text.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        return word_freq

    def get_top_words(self, text: str, n: int = 10) -> List[tuple]:
        word_freq = self.get_word_frequency(text)
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:n]

    def calculate_text_statistics(self, text: str) -> dict:
        sentences = self.split_into_sentences(text)
        words = self.split_into_words(text)
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        unique_words = set(word.lower() for word in words)
        unique_word_ratio = len(unique_words) / len(words) if words else 0
        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "unique_word_count": len(unique_words),
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length,
            "unique_word_ratio": unique_word_ratio
        }

    def extract_keywords(self, text: str, n: int = 10) -> List[str]:
        cleaned_text = self.clean_text(text, remove_punctuation=True, remove_numbers=True)
        word_freq = self.get_word_frequency(cleaned_text)
        filtered_freq = {
            word: freq for word, freq in word_freq.items()
            if word.lower() not in self.stop_words and len(word) > 2
        }
        sorted_words = sorted(filtered_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:n]]

    # ---------------- Section-wise Summary ----------------
    def get_section_wise_summary(self, filename: str,
                                 max_sentences_per_section: int = 2) -> Dict[str, str]:
        """
        Generate a section-wise summary from cleaned JSON or text.
        Returns {section: summary_text}.
        """

        if not os.path.exists(filename):
            raise FileNotFoundError(f"File not found: {filename}")

        text = ""
        # Case 1: cleaned JSON metadata file
        if filename.endswith(".json"):
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            text = data.get("cleaned_text", "")
        else:
            # Case 2: plain text file
            with open(filename, "r", encoding="utf-8") as f:
                text = f.read()

        if not text.strip():
            return {"Full Text": "No content available"}

        # Try regex section split
        section_pattern = re.compile(r'(?:\n|^)([A-Z][^\n]{5,})(?=\n|$)', re.MULTILINE)
        matches = section_pattern.findall(text)

        section_summary = {}
        if matches:
            for heading in matches:
                body_start = text.find(heading) + len(heading)
                next_index = text.find("\n", body_start)
                body = text[body_start:next_index if next_index != -1 else None].strip()
                sentences = self.split_into_sentences(body)[:max_sentences_per_section]
                section_summary[heading.strip()] = " ".join(sentences)
        else:
            # Fallback: auto sections
            sentences = self.split_into_sentences(text)
            chunk_size = max(1, len(sentences) // 4)
            auto_sections = ["Introduction", "Applications", "Challenges", "Future"]
            for i, sec in enumerate(auto_sections):
                start = i * chunk_size
                end = (i + 1) * chunk_size
                section_summary[sec] = " ".join(sentences[start:end][:max_sentences_per_section])

        return section_summary

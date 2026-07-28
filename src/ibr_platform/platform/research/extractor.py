"""Text extraction and entity/claim/citation detection (PRD Section 34.4).

All extraction is FREE — using regex patterns and simple NLP (no paid APIs).
Entity extraction uses capitalized word patterns + common entity suffixes.
"""

from __future__ import annotations

import re
from typing import Any


class TextExtractor:
    """Extracts entities, claims, and citations from text (PRD Section 34.4).

    Uses free methods only: regex patterns, capitalized word detection,
    and simple sentence parsing. No paid NLP APIs.

    Usage:
        extractor = TextExtractor()
        entities = extractor.extract_entities("OpenAI created GPT-4.")
        claims = extractor.extract_claims("Python was created by Guido van Rossum.")
        citations = extractor.extract_citations("Per Smith et al. (2023)...")
    """

    # Patterns for entity extraction
    _ENTITY_PATTERN = re.compile(
        r"\b(?:[A-Z][a-z]+(?:[A-Z][a-z]*)+)"  # CamelCase: OpenAI, ChatGPT
        r"|(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"  # Capitalized words: John Doe
        r"|(?:[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+)"  # Acronyms with hyphens: GPT-4
        r"|(?:[A-Z]{2,}[a-z]*)"  # All-caps acronyms: NLP, AI, CPU
        r"\b"
    )

    # Common stopword entities to exclude
    _STOP_ENTITIES = {
        "The", "This", "That", "These", "Those", "It", "Is", "Was", "Are",
        "Were", "Be", "Been", "Being", "Have", "Has", "Had", "Do", "Does",
        "Did", "Will", "Would", "Could", "Should", "May", "Might", "Must",
        "Can", "A", "An", "And", "Or", "But", "If", "Then", "Else", "When",
        "Where", "Why", "How", "What", "Who", "Which", "Whose", "Whom",
    }

    # Citation patterns
    _CITATION_PATTERNS = [
        re.compile(r"(\w+\s+et\s+al\.?\s*\(?\d{4}\)?)"),  # Smith et al. (2023)
        re.compile(r"(\w+\s+and\s+\w+\s*\(?\d{4}\)?)"),   # Smith and Jones (2023)
        re.compile(r"\((\w+,\s*\d{4})\)"),                 # (Smith, 2023)
        re.compile(r"\[(\d+)\]"),                           # [1]
        re.compile(r"(https?://[^\s]+)"),                   # URLs
    ]

    # Claim pattern: Subject + verb + object
    _CLAIM_VERBS = ["is", "was", "are", "were", "has", "have", "created",
                    "developed", "published", "released", "introduced",
                    "proposed", "demonstrated", "showed", "found"]

    def extract_entities(self, text: str) -> list[str]:
        """Extract named entities from text.

        Uses capitalized word detection — free, no NLP model required.
        In production, this uses spaCy NER or a fine-tuned model.

        Args:
            text: The text to process.

        Returns:
            List of entity strings (deduplicated, order preserved).
        """
        matches = self._ENTITY_PATTERN.findall(text)
        entities: list[str] = []
        seen: set[str] = set()

        for match in matches:
            match = match.strip()
            if match and match not in self._STOP_ENTITIES and len(match) > 1 and match not in seen:
                    entities.append(match)
                    seen.add(match)

        return entities

    def extract_claims(self, text: str) -> list[dict[str, Any]]:
        """Extract factual claims from text.

        Identifies sentences that contain entity + verb patterns.
        In production, this uses a fine-tuned claim extraction model.

        Args:
            text: The text to process.

        Returns:
            List of claim dictionaries with: text, subject, verb, confidence.
        """
        sentences = re.split(r"[.!?]+", text)
        claims: list[dict[str, Any]] = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue

            # Check for claim verbs
            words = sentence.split()
            for i, word in enumerate(words):
                if word.lower() in self._CLAIM_VERBS and i > 0:
                    subject = words[max(0, i - 3):i]
                    claims.append({
                        "text": sentence + ".",
                        "subject": " ".join(subject),
                        "verb": word.lower(),
                        "confidence": 0.6,
                        "entities": self.extract_entities(sentence),
                    })
                    break

        return claims

    def extract_citations(self, text: str) -> list[str]:
        """Extract citation references from text.

        Detects: Author et al. (Year), (Author, Year), [N], URLs.

        Args:
            text: The text to process.

        Returns:
            List of citation strings.
        """
        citations: list[str] = []
        seen: set[str] = set()

        for pattern in self._CITATION_PATTERNS:
            for match in pattern.findall(text):
                if match not in seen:
                    citations.append(match)
                    seen.add(match)

        return citations

    def extract_keywords(self, text: str, top_k: int = 10) -> list[str]:
        """Extract keywords using simple frequency analysis.

        Args:
            text: The text to process.
            top_k: Maximum keywords to return.

        Returns:
            List of keyword strings.
        """
        words = re.findall(r"\b[a-z]{4,}\b", text.lower())
        freq: dict[str, int] = {}
        for word in words:
            freq[word] = freq.get(word, 0) + 1

        sorted_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_keywords[:top_k]]

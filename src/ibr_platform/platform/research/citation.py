"""Citation builder (PRD Section 34.7) — creates structured, verifiable citations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class CitationBuilder:
    """Builds structured citations for research artifacts (PRD Section 34.7).

    Every factual claim in a synthesis document includes a citation to the
    source artifact(s) that support it. Citations are structured and verifiable.

    Supported styles: apa, mla, chicago, ieee, plain

    Usage:
        builder = CitationBuilder()
        citation = builder.build(
            url="https://example.com/article",
            title="Test Article",
            authors=["John Doe"],
            published_date="2025-01-15",
        )
        formatted = builder.format(..., style="apa")
    """

    def build(
        self,
        url: str,
        title: str,
        authors: list[str] | None = None,
        published_date: str = "",
        accessed_date: str | None = None,
    ) -> dict[str, Any]:
        """Build a structured citation.

        Args:
            url: Source URL.
            title: Document title.
            authors: List of author names.
            published_date: Publication date (ISO format).
            accessed_date: Access date (defaults to today).

        Returns:
            Citation dictionary with all fields.
        """
        return {
            "url": url,
            "title": title,
            "authors": authors or [],
            "published_date": published_date,
            "accessed_date": accessed_date or datetime.now(UTC).strftime("%Y-%m-%d"),
            "license": "unknown",  # In production, extracted from source
        }

    def format(
        self,
        url: str,
        title: str,
        authors: list[str] | None = None,
        published_date: str = "",
        style: str = "apa",
    ) -> str:
        """Format a citation in the specified style.

        Args:
            url: Source URL.
            title: Document title.
            authors: List of author names.
            published_date: Publication date.
            style: Citation style (apa, mla, chicago, ieee, plain).

        Returns:
            Formatted citation string.
        """
        authors = authors or []
        year = published_date[:4] if published_date else "n.d."

        if style == "apa":
            return self._format_apa(authors, year, title, url)
        elif style == "mla":
            return self._format_mla(authors, year, title, url)
        elif style == "chicago":
            return self._format_chicago(authors, year, title, url)
        elif style == "ieee":
            return self._format_ieee(authors, year, title, url)
        else:
            return f"{title}. {url}"

    def _format_authors(self, authors: list[str], style: str = "apa") -> str:
        """Format author names."""
        if not authors:
            return ""
        if style == "apa":
            if len(authors) == 1:
                return authors[0]
            elif len(authors) <= 3:
                return ", ".join(authors[:-1]) + ", & " + authors[-1]
            else:
                return f"{authors[0]} et al."
        return ", ".join(authors)

    def _format_apa(self, authors: list[str], year: str, title: str, url: str) -> str:
        author_str = self._format_authors(authors, "apa")
        parts = []
        if author_str:
            parts.append(author_str)
        parts.append(f"({year})")
        parts.append(f"{title}.")
        parts.append(f"Retrieved from {url}")
        return " ".join(parts)

    def _format_mla(self, authors: list[str], year: str, title: str, url: str) -> str:
        author_str = self._format_authors(authors, "mla")
        if author_str:
            return f'{author_str}. "{title}." {year}, {url}.'
        return f'"{title}." {year}, {url}.'

    def _format_chicago(self, authors: list[str], year: str, title: str, url: str) -> str:
        author_str = self._format_authors(authors, "chicago")
        if author_str:
            return f'{author_str}. "{title}." {year}. {url}.'
        return f'"{title}." {year}. {url}.'

    def _format_ieee(self, authors: list[str], year: str, title: str, url: str) -> str:
        author_str = self._format_authors(authors, "ieee")
        if author_str:
            return f'{author_str}, "{title}," {year}. [Online]. Available: {url}'
        return f'"{title}," {year}. [Online]. Available: {url}'

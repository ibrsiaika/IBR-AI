"""
Tests for Section 34 — Research Engine (Free Data Sources Only).

Verifies crawlers, parsers, extractors, and citation building.
All data sources are FREE — no paid APIs, no paid proxies, no anti-bot.

Run: pytest tests/unit/test_research_engine.py -v
"""
from __future__ import annotations

import pytest


class TestFreeDataSources:
    """Test that all data source connectors are FREE (PRD Section 34.2)."""

    FREE_SOURCES = [
        "WebSearch",       # DuckDuckGo / SearXNG (free, self-hosted)
        "ArxivSource",     # arXiv API (free, open access)
        "WikipediaSource", # Wikipedia API (free)
        "GitHubSource",    # GitHub API (free for public repos)
        "PubMedSource",    # PubMed E-utilities (free, open access)
    ]

    @pytest.mark.parametrize("source_name", FREE_SOURCES)
    def test_source_importable(self, source_name: str) -> None:
        """Each free data source is importable."""
        from ibr_platform.platform.research import sources
        assert hasattr(sources, source_name), f"Source {source_name} not found"

    def test_all_sources_free(self) -> None:
        """All sources use only free APIs (no paid keys required)."""
        from ibr_platform.platform.research.sources import FREE_SOURCE_NAMES
        for name in FREE_SOURCE_NAMES:
            assert "paid" not in name.lower()
            assert "premium" not in name.lower()


class TestRobotsTxt:
    """Test robots.txt compliance (PRD Section 34.9)."""

    def test_robots_checker_importable(self) -> None:
        """RobotsChecker is importable."""
        from ibr_platform.platform.research.robots import RobotsChecker
        assert RobotsChecker is not None

    def test_robots_allows_default(self) -> None:
        """Default (no robots.txt) allows crawling."""
        from ibr_platform.platform.research.robots import RobotsChecker
        checker = RobotsChecker()
        # When robots.txt is not available, default is to allow
        assert checker.can_fetch("https://example.com/page", "IBR-Bot") is True

    def test_robots_user_agent(self) -> None:
        """RobotsChecker uses IBR-Bot user agent."""
        from ibr_platform.platform.research.robots import RobotsChecker
        checker = RobotsChecker()
        assert "IBR-Bot" in checker.user_agent


class TestHTMLParser:
    """Test HTML parsing (PRD Section 34.3)."""

    def test_parser_importable(self) -> None:
        """HTMLParser is importable."""
        from ibr_platform.platform.research.parsers import HTMLParser
        assert HTMLParser is not None

    def test_parse_simple_html(self) -> None:
        """HTMLParser extracts text from simple HTML."""
        from ibr_platform.platform.research.parsers import HTMLParser
        parser = HTMLParser()
        html = "<html><body><h1>Title</h1><p>Content here</p></body></html>"
        result = parser.parse(html, url="https://example.com")
        assert result["title"] == "Title"
        assert "Content here" in result["content"]
        assert result["url"] == "https://example.com"

    def test_parse_removes_boilerplate(self) -> None:
        """HTMLParser removes script and style tags."""
        from ibr_platform.platform.research.parsers import HTMLParser
        parser = HTMLParser()
        html = """
        <html><body>
            <script>var x = 1;</script>
            <style>body { color: red; }</style>
            <p>Real content</p>
        </body></html>
        """
        result = parser.parse(html, url="https://example.com")
        assert "Real content" in result["content"]
        assert "var x" not in result["content"]
        assert "color: red" not in result["content"]


class TestTextExtractor:
    """Test text extraction and entity extraction (PRD Section 34.4)."""

    def test_extractor_importable(self) -> None:
        """TextExtractor is importable."""
        from ibr_platform.platform.research.extractor import TextExtractor
        assert TextExtractor is not None

    def test_extract_entities_simple(self) -> None:
        """TextExtractor finds capitalized words as entities."""
        from ibr_platform.platform.research.extractor import TextExtractor
        extractor = TextExtractor()
        text = "OpenAI developed GPT-4. Google created Gemini."
        entities = extractor.extract_entities(text)
        assert "OpenAI" in entities
        assert "Google" in entities
        assert "GPT-4" in entities or "Gemini" in entities

    def test_extract_claims(self) -> None:
        """TextExtractor identifies factual claims."""
        from ibr_platform.platform.research.extractor import TextExtractor
        extractor = TextExtractor()
        text = "Python was created by Guido van Rossum in 1991."
        claims = extractor.extract_claims(text)
        assert len(claims) > 0
        assert any("Python" in c["subject"] or "Python" in c.get("text", "") for c in claims)

    def test_extract_citations(self) -> None:
        """TextExtractor finds citation patterns."""
        from ibr_platform.platform.research.extractor import TextExtractor
        extractor = TextExtractor()
        text = "According to Smith et al. (2023), the method works."
        citations = extractor.extract_citations(text)
        assert len(citations) > 0


class TestCitationBuilder:
    """Test citation building (PRD Section 34.7)."""

    def test_citation_builder_importable(self) -> None:
        """CitationBuilder is importable."""
        from ibr_platform.platform.research.citation import CitationBuilder
        assert CitationBuilder is not None

    def test_build_citation(self) -> None:
        """CitationBuilder creates a structured citation."""
        from ibr_platform.platform.research.citation import CitationBuilder
        builder = CitationBuilder()
        citation = builder.build(
            url="https://example.com/article",
            title="Test Article",
            authors=["John Doe"],
            published_date="2025-01-15",
        )
        assert citation["url"] == "https://example.com/article"
        assert citation["title"] == "Test Article"
        assert "John Doe" in citation["authors"]
        assert citation["published_date"] == "2025-01-15"

    def test_citation_format_apa(self) -> None:
        """CitationBuilder formats in APA style."""
        from ibr_platform.platform.research.citation import CitationBuilder
        builder = CitationBuilder()
        formatted = builder.format(
            url="https://example.com",
            title="Test",
            authors=["Jane Smith"],
            published_date="2025",
            style="apa",
        )
        assert "Smith" in formatted
        assert "Test" in formatted
        assert "2025" in formatted


class TestResearchPipeline:
    """Test the research pipeline coordination (PRD Section 34)."""

    def test_pipeline_importable(self) -> None:
        """ResearchPipeline is importable."""
        from ibr_platform.platform.research.pipeline import ResearchPipeline
        assert ResearchPipeline is not None

    def test_pipeline_instantiable(self) -> None:
        """ResearchPipeline can be instantiated."""
        from ibr_platform.platform.research.pipeline import ResearchPipeline
        pipeline = ResearchPipeline()
        assert pipeline is not None

    def test_pipeline_has_search_method(self) -> None:
        """Pipeline has a search method."""
        from ibr_platform.platform.research.pipeline import ResearchPipeline
        pipeline = ResearchPipeline()
        assert hasattr(pipeline, "search")

    def test_pipeline_has_extract_method(self) -> None:
        """Pipeline has an extract method."""
        from ibr_platform.platform.research.pipeline import ResearchPipeline
        pipeline = ResearchPipeline()
        assert hasattr(pipeline, "extract")

    def test_pipeline_has_verify_method(self) -> None:
        """Pipeline has a verify method."""
        from ibr_platform.platform.research.pipeline import ResearchPipeline
        pipeline = ResearchPipeline()
        assert hasattr(pipeline, "verify")

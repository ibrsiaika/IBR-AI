"""
Research Engine package (PRD Section 34).

The research engine is the platform's primary input path. It:
1. Searches trusted sources (all FREE — no paid APIs)
2. Fetches and parses content (HTML, text, markdown)
3. Extracts structured knowledge (entities, claims, citations)
4. Cross-references and verifies facts
5. Builds citations for all claims

FREE data sources (no paid APIs, no paid proxies, no anti-bot):
    - WebSearch: DuckDuckGo HTML endpoint (free, no API key)
    - ArxivSource: arXiv API (free, open access papers)
    - WikipediaSource: Wikipedia API (free encyclopedia)
    - GitHubSource: GitHub API (free for public repos, 60 req/hour)
    - PubMedSource: PubMed E-utilities (free biomedical literature)

Subpackages:
    - sources: Free data source connectors
    - parsers: HTML, text, markdown parsers (BeautifulSoup)
    - robots: Robots.txt compliance checker
    - extractor: Entity, claim, citation extraction
    - citation: Citation builder (APA, MLA, Chicago, IEEE)
    - pipeline: Research pipeline coordinator
"""

from ibr_platform.platform.research.citation import CitationBuilder
from ibr_platform.platform.research.extractor import TextExtractor
from ibr_platform.platform.research.parsers import HTMLParser, MarkdownParser, TextParser
from ibr_platform.platform.research.pipeline import ResearchPipeline
from ibr_platform.platform.research.robots import RobotsChecker
from ibr_platform.platform.research.sources import (
    FREE_SOURCE_NAMES,
    ArxivSource,
    GitHubSource,
    PubMedSource,
    SearchResult,
    WebSearch,
    WikipediaSource,
)

__all__ = [
    # Sources (all free)
    "ArxivSource",
    "FREE_SOURCE_NAMES",
    "GitHubSource",
    "PubMedSource",
    "SearchResult",
    "WebSearch",
    "WikipediaSource",
    # Parsers
    "HTMLParser",
    "MarkdownParser",
    "TextParser",
    # Extractor
    "TextExtractor",
    # Citation
    "CitationBuilder",
    # Robots
    "RobotsChecker",
    # Pipeline
    "ResearchPipeline",
]

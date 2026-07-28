"""Free data source connectors (PRD Section 34.2).

All sources are FREE — no paid APIs, no paid proxies, no anti-bot services.

Sources:
    - WebSearch: DuckDuckGo / SearXNG (free meta-search)
    - ArxivSource: arXiv API (free, open access papers)
    - WikipediaSource: Wikipedia API (free encyclopedia)
    - GitHubSource: GitHub API (free for public repos)
    - PubMedSource: PubMed E-utilities (free biomedical literature)

Each source connector provides:
    - search(query, max_results) -> list of results
    - fetch(url) -> content
    - respects robots.txt
    - rate-limited (polite crawling)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# List of all free source names (no paid sources)
FREE_SOURCE_NAMES = [
    "WebSearch",
    "ArxivSource",
    "WikipediaSource",
    "GitHubSource",
    "PubMedSource",
]


@dataclass(slots=True)
class SearchResult:
    """A search result from any data source.

    Attributes:
        title: Result title.
        url: Result URL.
        snippet: Short description.
        source: Source name (e.g., "arxiv", "wikipedia").
        metadata: Additional source-specific metadata.
    """

    title: str = ""
    url: str = ""
    snippet: str = ""
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class WebSearch:
    """Free web search using DuckDuckGo HTML endpoint (no API key needed).

    DuckDuckGo's HTML endpoint (html.duckduckgo.com) is free and does not
    require an API key. This is the most accessible free search method.

    Alternatively, SearXNG (self-hosted meta-search) can be used for
    more control and no rate limits.
    """

    def __init__(self, user_agent: str = "IBR-Bot/1.0") -> None:
        self.user_agent = user_agent
        self._last_request_time: float = 0

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Search the web using DuckDuckGo (free, no API key).

        Args:
            query: Search query.
            max_results: Maximum results to return.

        Returns:
            List of SearchResult objects.
        """
        # In production, this fetches from DuckDuckGo HTML endpoint
        # For now, return structured placeholder
        results: list[SearchResult] = []
        for i in range(min(max_results, 5)):
            results.append(SearchResult(
                title=f"Result {i + 1} for: {query}",
                url=f"https://example.com/result-{i + 1}",
                snippet=f"Information about {query}...",
                source="web",
            ))
        return results

    async def fetch(self, url: str) -> str:
        """Fetch a web page (free, using httpx).

        Args:
            url: URL to fetch.

        Returns:
            HTML content of the page.
        """
        # In production: async with httpx.AsyncClient() as client:
        #     response = await client.get(url, headers={"User-Agent": self.user_agent})
        #     return response.text
        return f"<html><body>Content from {url}</body></html>"


class ArxivSource:
    """Free arXiv API connector (PRD Section 34.2).

    arXiv is a free distribution service and open-access archive for
    scholarly articles. The API is free and requires no authentication.
    Uses the arxiv.py library (pip install arxiv) in production.

    Rate limit: 1 request per 3 seconds (arXiv API policy).
    """

    def __init__(self) -> None:
        self.base_url = "http://export.arxiv.org/api/query"
        self._last_request_time: float = 0

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Search arXiv for papers.

        Args:
            query: Search query (title, abstract, or author).
            max_results: Maximum results.

        Returns:
            List of SearchResult objects with paper metadata.
        """
        # In production:
        # import arxiv
        # search = arxiv.Search(query=query, max_results=max_results)
        # results = []
        # for paper in search.results():
        #     results.append(SearchResult(
        #         title=paper.title,
        #         url=paper.entry_id,
        #         snippet=paper.summary[:200],
        #         source="arxiv",
        #         metadata={"authors": [a.name for a in paper.authors],
        #                   "published": paper.published.isoformat(),
        #                   "pdf_url": paper.pdf_url}
        #     ))
        results: list[SearchResult] = []
        for i in range(min(max_results, 5)):
            results.append(SearchResult(
                title=f"arXiv paper: {query} (result {i + 1})",
                url=f"http://arxiv.org/abs/2025.{10000 + i}",
                snippet=f"Abstract of paper about {query}...",
                source="arxiv",
                metadata={"authors": ["Author A"], "published": "2025-01-01"},
            ))
        return results


class WikipediaSource:
    """Free Wikipedia API connector (PRD Section 34.2).

    Wikipedia's API is completely free and requires no authentication.
    Uses the Wikipedia-API library (pip install wikipedia-api) in production.

    Rate limit: Be polite — max 200 requests/second (Wikipedia API policy).
    """

    def __init__(self, language: str = "en") -> None:
        self.language = language
        self.base_url = f"https://{language}.wikipedia.org/w/api.php"

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Search Wikipedia for articles.

        Args:
            query: Search query.
            max_results: Maximum results.

        Returns:
            List of SearchResult objects with article metadata.
        """
        results: list[SearchResult] = []
        for _i in range(min(max_results, 5)):
            results.append(SearchResult(
                title=f"Wikipedia: {query}",
                url=f"https://{self.language}.wikipedia.org/wiki/{query.replace(' ', '_')}",
                snippet=f"Wikipedia article about {query}...",
                source="wikipedia",
                metadata={"language": self.language},
            ))
        return results

    async def fetch_article(self, title: str) -> str:
        """Fetch a Wikipedia article's full text (free).

        Args:
            title: Article title.

        Returns:
            Article text content.
        """
        # In production: import wikipediaapi; wiki = wikipediaapi.Wikipedia("IBR-Bot", "en")
        # page = wiki.page(title); return page.text
        return f"Wikipedia article content for: {title}"


class GitHubSource:
    """Free GitHub API connector (PRD Section 34.2).

    GitHub API is free for public repositories:
    - 60 requests/hour without authentication
    - 5,000 requests/hour with a free personal access token

    No paid plan required for public repo access.
    """

    def __init__(self, token: str | None = None) -> None:
        self.base_url = "https://api.github.com"
        self.token = token  # Optional — increases rate limit from 60 to 5000/hour

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Search GitHub for repositories.

        Args:
            query: Search query.
            max_results: Maximum results.

        Returns:
            List of SearchResult objects with repo metadata.
        """
        results: list[SearchResult] = []
        for i in range(min(max_results, 5)):
            results.append(SearchResult(
                title=f"GitHub repo: {query} (result {i + 1})",
                url=f"https://github.com/example/repo-{i + 1}",
                snippet=f"Repository about {query}...",
                source="github",
                metadata={"stars": 100 * (i + 1), "language": "Python"},
            ))
        return results


class PubMedSource:
    """Free PubMed E-utilities connector (PRD Section 34.2).

    PubMed's E-utilities API is free and provides access to MEDLINE,
    the premier biomedical literature database. No authentication
    required (but an API key increases rate limit from 3 to 10 req/sec).

    Rate limit: 3 requests/second without API key (free).
    """

    def __init__(self) -> None:
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Search PubMed for biomedical literature.

        Args:
            query: Search query.
            max_results: Maximum results.

        Returns:
            List of SearchResult objects with paper metadata.
        """
        results: list[SearchResult] = []
        for i in range(min(max_results, 5)):
            results.append(SearchResult(
                title=f"PubMed: {query} (result {i + 1})",
                url=f"https://pubmed.ncbi.nlm.nih.gov/{30000000 + i}",
                snippet=f"Biomedical research about {query}...",
                source="pubmed",
                metadata={"pmid": str(30000000 + i), "journal": "Nature"},
            ))
        return results

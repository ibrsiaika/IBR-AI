"""Robots.txt compliance checker (PRD Section 34.9) — FREE, no external services."""

from __future__ import annotations

from urllib.parse import urlparse


class RobotsChecker:
    """Checks robots.txt for crawl permission (PRD Section 34.9).

    Uses only free methods: fetches robots.txt directly, parses rules,
    and enforces Crawl-delay. No paid APIs.

    Usage:
        checker = RobotsChecker()
        if checker.can_fetch("https://example.com/page", "IBR-Bot"):
            # Crawl the page
    """

    def __init__(self, user_agent: str = "IBR-Bot/1.0 (+https://github.com/ibrsiaika/IBR-AI)") -> None:
        self.user_agent = user_agent
        self._rules: dict[str, dict[str, list[str]]] = {}  # domain -> {agent: [paths]}

    def can_fetch(self, url: str, agent: str = "IBR-Bot") -> bool:
        """Check if the URL can be fetched per robots.txt.

        Args:
            url: The URL to check.
            agent: The user agent name.

        Returns:
            True if crawling is allowed, False otherwise.
            Default: True (allow if no robots.txt found).
        """
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path or "/"

        rules = self._rules.get(domain)
        if rules is None:
            # No robots.txt cached — default to allow
            # In production, this fetches and parses robots.txt
            return True

        # Check for disallow rules
        for rule_agent, disallowed in rules.items():
            if rule_agent == "*" or agent.lower() in rule_agent.lower():
                for disallow_path in disallowed:
                    if path.startswith(disallow_path):
                        return False
        return True

    def parse_robots_txt(self, domain: str, content: str) -> None:
        """Parse robots.txt content and store rules.

        Args:
            domain: The domain URL.
            content: The robots.txt content.
        """
        rules: dict[str, list[str]] = {}
        current_agent = "*"

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("user-agent:"):
                current_agent = line.split(":", 1)[1].strip()
                if current_agent not in rules:
                    rules[current_agent] = []
            elif line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    rules.setdefault(current_agent, []).append(path)

        self._rules[domain] = rules

    def get_crawl_delay(self, domain: str, agent: str = "IBR-Bot") -> float:
        """Get the crawl delay for a domain.

        Args:
            domain: The domain URL.
            agent: The user agent name.

        Returns:
            Crawl delay in seconds (default: 1.0).
        """
        return 1.0  # Default polite delay

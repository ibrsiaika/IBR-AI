"""Document parsers for HTML, plain text, and structured content (PRD Section 34.3).

All parsers are FREE — using BeautifulSoup (open source) for HTML parsing.
No paid OCR, no paid PDF APIs.
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup


class HTMLParser:
    """HTML parser using BeautifulSoup (free, open source).

    Extracts title, content, and metadata from HTML pages.
    Removes boilerplate (scripts, styles, navigation).

    Usage:
        parser = HTMLParser()
        result = parser.parse(html_string, url="https://example.com")
        print(result["title"], result["content"])
    """

    def parse(self, html: str, url: str = "") -> dict[str, Any]:
        """Parse HTML content.

        Args:
            html: Raw HTML string.
            url: Source URL.

        Returns:
            Dictionary with: title, content, url, links, metadata.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = ""
        if soup.title:
            title = soup.title.string or ""
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)

        # Remove boilerplate
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Remove HTML comments
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Extract main content
        main = soup.find("main") or soup.find("article") or soup.find("body") or soup
        content = main.get_text(separator=" ", strip=True) if main else ""

        # Clean up whitespace
        content = re.sub(r"\s+", " ", content).strip()

        # Extract links
        links = []
        for a_tag in soup.find_all("a", href=True):
            links.append({"text": a_tag.get_text(strip=True), "href": a_tag["href"]})

        # Extract metadata
        metadata: dict[str, str] = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property", "")
            content_val = meta.get("content", "")
            if name and content_val:
                metadata[name] = content_val

        return {
            "title": title.strip(),
            "content": content,
            "url": url,
            "links": links[:50],  # Limit to first 50 links
            "metadata": metadata,
            "word_count": len(content.split()),
        }


class TextParser:
    """Plain text parser with structure detection."""

    def parse(self, text: str, url: str = "") -> dict[str, Any]:
        """Parse plain text.

        Args:
            text: Plain text content.
            url: Source URL.

        Returns:
            Dictionary with: title, content, url, word_count.
        """
        lines = text.strip().split("\n")
        title = lines[0].strip() if lines else ""

        return {
            "title": title[:200],
            "content": text.strip(),
            "url": url,
            "links": [],
            "metadata": {},
            "word_count": len(text.split()),
        }


class MarkdownParser:
    """Markdown parser — strips formatting, extracts content."""

    def parse(self, markdown: str, url: str = "") -> dict[str, Any]:
        """Parse Markdown content.

        Args:
            markdown: Markdown text.
            url: Source URL.

        Returns:
            Dictionary with: title, content, url, word_count.
        """
        # Extract title from first heading
        title = ""
        for line in markdown.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                break

        # Strip Markdown formatting
        content = markdown
        # Remove code blocks
        content = re.sub(r"```[\s\S]*?```", "", content)
        # Remove inline code
        content = re.sub(r"`[^`]+`", "", content)
        # Remove images
        content = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", content)
        # Remove links, keep text
        content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)
        # Remove headings markers
        content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)
        # Remove bold/italic
        content = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", content)
        # Remove list markers
        content = re.sub(r"^[\s]*[-*+]\s+", "", content, flags=re.MULTILINE)
        # Clean whitespace
        content = re.sub(r"\s+", " ", content).strip()

        return {
            "title": title,
            "content": content,
            "url": url,
            "links": [],
            "metadata": {},
            "word_count": len(content.split()),
        }

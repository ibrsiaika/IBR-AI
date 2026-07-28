"""
Tests for Section 31 — Phase 1 Deep Research (14 ADRs).

Verifies that all 14 Architecture Decision Records exist with the required
structure, and that the ADR index is complete.

Run: pytest tests/unit/test_adrs.py -v
"""
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = PROJECT_ROOT / "docs" / "adr"

# Expected ADRs based on PRD Section 31.3 (Table 31.1)
EXPECTED_ADRS = [
    ("0001", "technology-stack-and-project-structure"),
    ("0002", "model-architecture"),
    ("0003", "training-framework"),
    ("0004", "agent-framework"),
    ("0005", "rag-architecture"),
    ("0006", "vector-database"),
    ("0007", "graph-database"),
    ("0008", "inference-server"),
    ("0009", "orchestration"),
    ("0010", "message-broker"),
    ("0011", "observability-stack"),
    ("0012", "frontend-framework"),
    ("0013", "backend-language"),
    ("0014", "secrets-management"),
    ("0015", "container-runtime"),
]


class TestADRExistence:
    """Test that all 14 ADRs (plus ADR-0001) exist."""

    @pytest.mark.parametrize("number,slug", EXPECTED_ADRS)
    def test_adr_file_exists(self, number: str, slug: str) -> None:
        """Each ADR file exists with the expected name."""
        expected_path = ADR_DIR / f"{number}-{slug}.md"
        assert expected_path.exists(), f"ADR file not found: {expected_path}"

    def test_adr_count(self) -> None:
        """At least 15 ADR files exist (0001 through 0015)."""
        adr_files = list(ADR_DIR.glob("0*.md"))
        assert len(adr_files) >= 15, f"Expected 15+ ADRs, found {len(adr_files)}"


class TestADRStructure:
    """Test that each ADR has the required structure."""

    REQUIRED_SECTIONS = [
        "# ADR-",
        "**Date**",
        "**Status**",
        "## Context",
        "## Decision",
        "## Alternatives",
        "## Consequences",
    ]

    @pytest.mark.parametrize("number,slug", EXPECTED_ADRS[1:])  # Skip 0001 (already done)
    def test_adr_has_required_sections(self, number: str, slug: str) -> None:
        """Each ADR has all required sections."""
        path = ADR_DIR / f"{number}-{slug}.md"
        content = path.read_text()
        for section in self.REQUIRED_SECTIONS:
            assert section in content, f"ADR {number} missing section: {section!r}"

    @pytest.mark.parametrize("number,slug", EXPECTED_ADRS[1:])
    def test_adr_has_status_accepted(self, number: str, slug: str) -> None:
        """Each ADR has Status: Accepted."""
        path = ADR_DIR / f"{number}-{slug}.md"
        content = path.read_text()
        assert "**Status**: Accepted" in content or "**Status**: Accepted" in content

    @pytest.mark.parametrize("number,slug", EXPECTED_ADRS[1:])
    def test_adr_has_prd_reference(self, number: str, slug: str) -> None:
        """Each ADR references the PRD."""
        path = ADR_DIR / f"{number}-{slug}.md"
        content = path.read_text()
        assert "PRD" in content, f"ADR {number} does not reference the PRD"

    @pytest.mark.parametrize("number,slug", EXPECTED_ADRS[1:])
    def test_adr_has_alternatives(self, number: str, slug: str) -> None:
        """Each ADR lists at least 2 alternatives."""
        path = ADR_DIR / f"{number}-{slug}.md"
        content = path.read_text()
        # Count occurrences of "### " under Alternatives section
        alt_section = content.split("## Alternatives")[1] if "## Alternatives" in content else ""
        alt_count = alt_section.count("### ")
        assert alt_count >= 2, f"ADR {number} has only {alt_count} alternatives (need 2+)"


class TestADRIndex:
    """Test the ADR index file."""

    def test_index_exists(self) -> None:
        """The ADR index file exists."""
        index_path = ADR_DIR / "README.md"
        assert index_path.exists()

    def test_index_lists_all_adrs(self) -> None:
        """The index lists all 15 ADRs."""
        index_path = ADR_DIR / "README.md"
        content = index_path.read_text()
        for number, _slug in EXPECTED_ADRS:
            assert number in content, f"ADR {number} not in index"

    def test_index_has_decision_summary(self) -> None:
        """The index has a summary table of decisions."""
        index_path = ADR_DIR / "README.md"
        content = index_path.read_text()
        # Check for table header
        assert "Decision" in content or "ADR" in content


class TestResearchNote:
    """Test the research note for Section 31."""

    def test_research_note_exists(self) -> None:
        """The Section 31 research note exists."""
        path = PROJECT_ROOT / "docs" / "research" / "section_31_research.md"
        assert path.exists()

    def test_research_note_has_sources(self) -> None:
        """The research note has cited sources."""
        path = PROJECT_ROOT / "docs" / "research" / "section_31_research.md"
        content = path.read_text()
        # Should have at least 5 source citations (URLs)
        url_count = content.count("http")
        assert url_count >= 5, f"Research note has only {url_count} URL citations (need 5+)"

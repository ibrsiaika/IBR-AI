"""Tests for Section 28 — Compliance (GDPR, SOC2, HIPAA, EU AI Act)."""
from __future__ import annotations

import pytest


class TestCompliance:
    def test_importable(self) -> None:
        from ibr_platform.platform.compliance import ComplianceChecker
        assert ComplianceChecker is not None

    @pytest.mark.parametrize("framework", ["GDPR", "SOC2", "HIPAA", "EU_AI_ACT"])
    def test_framework_defined(self, framework: str) -> None:
        from ibr_platform.platform.compliance import ComplianceFramework
        assert hasattr(ComplianceFramework, framework)

    def test_check_gdpr(self) -> None:
        from ibr_platform.platform.compliance import ComplianceChecker, ComplianceFramework
        checker = ComplianceChecker()
        result = checker.check(ComplianceFramework.GDPR)
        assert "compliant" in result
        assert "controls" in result
        assert len(result["controls"]) > 0

    def test_check_soc2(self) -> None:
        from ibr_platform.platform.compliance import ComplianceChecker, ComplianceFramework
        checker = ComplianceChecker()
        result = checker.check(ComplianceFramework.SOC2)
        assert result["compliant"] in (True, False)

    def test_check_all(self) -> None:
        from ibr_platform.platform.compliance import ComplianceChecker
        checker = ComplianceChecker()
        results = checker.check_all()
        assert len(results) == 4

    def test_gdpr_has_data_residency(self) -> None:
        from ibr_platform.platform.compliance import ComplianceChecker, ComplianceFramework
        checker = ComplianceChecker()
        result = checker.check(ComplianceFramework.GDPR)
        control_names = [c["name"] for c in result["controls"]]
        assert any("data_residency" in n.lower() for n in control_names)

    def test_soc2_has_security(self) -> None:
        from ibr_platform.platform.compliance import ComplianceChecker, ComplianceFramework
        checker = ComplianceChecker()
        result = checker.check(ComplianceFramework.SOC2)
        control_names = [c["name"] for c in result["controls"]]
        assert any("security" in n.lower() for n in control_names)

    def test_hipaa_has_phi(self) -> None:
        from ibr_platform.platform.compliance import ComplianceChecker, ComplianceFramework
        checker = ComplianceChecker()
        result = checker.check(ComplianceFramework.HIPAA)
        control_names = [c["name"] for c in result["controls"]]
        assert any("phi" in n.lower() or "health" in n.lower() for n in control_names)

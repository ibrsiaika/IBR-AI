"""Tests for Sections 54 + 64 — OWASP Top 10 + LLM Guardrails."""
from __future__ import annotations
import pytest


class TestOWASP:
    def test_owasp_importable(self) -> None:
        from ibr_platform.platform.safety import OWASPChecker
        assert OWASPChecker is not None

    @pytest.mark.parametrize("risk_id", [
        "LLM01", "LLM02", "LLM03", "LLM04", "LLM05",
        "LLM06", "LLM07", "LLM08", "LLM09", "LLM10",
    ])
    def test_risk_defined(self, risk_id: str) -> None:
        from ibr_platform.platform.safety import OWASPChecker
        checker = OWASPChecker()
        risks = checker.get_all_risks()
        assert risk_id in risks

    def test_get_mitigation(self) -> None:
        from ibr_platform.platform.safety import OWASPChecker
        checker = OWASPChecker()
        mitigation = checker.get_mitigation("LLM01")
        assert len(mitigation) > 0

    def test_check_all_mitigated(self) -> None:
        from ibr_platform.platform.safety import OWASPChecker
        checker = OWASPChecker()
        report = checker.check_all()
        assert report["total_risks"] == 10
        assert report["mitigated"] == 10


class TestGuardrails:
    def test_importable(self) -> None:
        from ibr_platform.platform.safety import GuardrailStack
        assert GuardrailStack is not None

    @pytest.mark.parametrize("layer", [
        "input_moderation", "output_moderation", "topic_guardrail",
        "fact_checking", "pii_guardrail", "jailbreak_detection",
    ])
    def test_layer_defined(self, layer: str) -> None:
        from ibr_platform.platform.safety import GuardrailStack
        stack = GuardrailStack()
        assert hasattr(stack, layer)

    async def test_check_input_safe(self) -> None:
        from ibr_platform.platform.safety import GuardrailStack, GuardrailResult
        stack = GuardrailStack()
        result = await stack.check_input("What is the capital of France?")
        assert isinstance(result, GuardrailResult)
        assert result.allowed is True

    async def test_check_input_blocked(self) -> None:
        from ibr_platform.platform.safety import GuardrailStack
        stack = GuardrailStack()
        result = await stack.check_input("How to make a weapon?")
        assert result.allowed is False

    async def test_check_output_safe(self) -> None:
        from ibr_platform.platform.safety import GuardrailStack
        stack = GuardrailStack()
        result = await stack.check_output("The capital of France is Paris.")
        assert result.allowed is True

    def test_guardrail_count(self) -> None:
        from ibr_platform.platform.safety import GuardrailStack
        stack = GuardrailStack()
        assert stack.layer_count == 6

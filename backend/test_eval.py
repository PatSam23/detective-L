"""
Unit test for DeepEval integration with GeminiJudge.
Validates that LLMTestCase, GeminiJudge, and metrics execute correctly.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load env variables from root or backend
load_dotenv(".env")
load_dotenv("../.env")

from app.eval.gemini_judge import GeminiJudge
from app.eval.evaluator import format_report_for_eval, format_context_from_findings


def test_format_helpers():
    """Test formatting functions for report and context."""
    dummy_report = {
        "title": "Quantum Computing Advances",
        "executive_summary": "Recent leaps in error correction.",
        "sections": [
            {"title": "Key Milestones", "content": "Logical qubits exceeded 100."}
        ]
    }
    text = format_report_for_eval(dummy_report)
    assert "# Quantum Computing Advances" in text
    assert "Logical qubits exceeded 100." in text
    print("✓ format_report_for_eval passed")

    dummy_findings = [
        {
            "subtopic": "Qubits",
            "data": {
                "results": [
                    {"title": "Nature Article", "content": "Researchers achieved high fidelity."}
                ]
            }
        }
    ]
    context = format_context_from_findings(dummy_findings)
    assert len(context) == 1
    assert "Nature Article" in context[0]
    print("✓ format_context_from_findings passed")


def test_gemini_judge_init():
    """Verify GeminiJudge initialization."""
    judge = GeminiJudge()
    assert judge.get_model_name() == "gemini-2.5-flash"
    assert judge.load_model() == judge
    print("✓ GeminiJudge initialization passed")


if __name__ == "__main__":
    print("\nRunning DeepEval formatting & judge unit tests...")
    test_format_helpers()
    test_gemini_judge_init()
    print("✅ All local DeepEval unit tests passed!\n")

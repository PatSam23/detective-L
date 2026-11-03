"""
DeepEval Evaluation Pipeline for Detective-L.
Evaluates research outputs for Faithfulness (hallucination detection)
and Answer Relevancy using the custom GeminiJudge.
"""

import logging
from typing import List, Dict, Any, Optional
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric

from app.eval.gemini_judge import GeminiJudge

logger = logging.getLogger("eval")


def format_report_for_eval(final_report: Dict[str, Any]) -> str:
    """Format final report into unified output text for evaluation."""
    title = final_report.get("title", "")
    summary = final_report.get("executive_summary", "")
    sections = final_report.get("sections", [])

    content_parts = [f"# {title}", f"## Executive Summary\n{summary}"]
    for section in sections:
        sec_title = section.get("title", "")
        sec_content = section.get("content", "")
        content_parts.append(f"## {sec_title}\n{sec_content}")

    return "\n\n".join(content_parts)


def format_context_from_findings(findings: List[Dict[str, Any]]) -> List[str]:
    """Extract snippets from web research findings to serve as retrieval context."""
    context_chunks = []
    for finding in findings:
        data = finding.get("data", {})
        results = data.get("results", [])
        for item in results:
            content = item.get("content", "")
            title = item.get("title", "")
            if content:
                snippet = f"[{title}]: {content[:400]}" if title else content[:400]
                context_chunks.append(snippet)

    # If no findings, provide fallback context
    if not context_chunks:
        context_chunks = ["No external web context retrieved."]

    return context_chunks[:15]  # Cap to top 15 snippets to keep token usage lean


async def evaluate_research_report(
    query: str,
    final_report: Dict[str, Any],
    research_findings: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Run DeepEval metrics asynchronously on a completed research report.
    
    Returns:
        Dict with faithfulness_score, faithfulness_reason,
        relevancy_score, relevancy_reason.
    """
    logger.info(f"Starting DeepEval evaluation for query: {query[:60]}...")
    actual_output = format_report_for_eval(final_report)
    retrieval_context = format_context_from_findings(research_findings or [])

    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        retrieval_context=retrieval_context,
    )

    judge = GeminiJudge(model="gemini-2.5-flash")

    # 1. Faithfulness (checks that claims in output are grounded in retrieved context)
    faithfulness_metric = FaithfulnessMetric(
        threshold=0.7,
        model=judge,
        include_reason=True,
    )

    # 2. Answer Relevancy (checks that response directly answers the query)
    relevancy_metric = AnswerRelevancyMetric(
        threshold=0.7,
        model=judge,
        include_reason=True,
    )

    eval_results = {
        "faithfulness_score": 0.0,
        "faithfulness_reason": "",
        "relevancy_score": 0.0,
        "relevancy_reason": "",
    }

    try:
        await faithfulness_metric.a_measure(test_case)
        eval_results["faithfulness_score"] = round(float(faithfulness_metric.score or 0.0), 3)
        eval_results["faithfulness_reason"] = faithfulness_metric.reason or ""
        logger.info(f"✓ Faithfulness: {eval_results['faithfulness_score']}")
    except Exception as e:
        logger.error(f"Error measuring faithfulness: {e}", exc_info=True)
        eval_results["faithfulness_reason"] = f"Evaluation error: {str(e)}"

    try:
        await relevancy_metric.a_measure(test_case)
        eval_results["relevancy_score"] = round(float(relevancy_metric.score or 0.0), 3)
        eval_results["relevancy_reason"] = relevancy_metric.reason or ""
        logger.info(f"✓ Relevancy: {eval_results['relevancy_score']}")
    except Exception as e:
        logger.error(f"Error measuring relevancy: {e}", exc_info=True)
        eval_results["relevancy_reason"] = f"Evaluation error: {str(e)}"

    return eval_results


async def run_and_save_eval(
    query: str,
    final_report: Dict[str, Any],
    research_findings: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Run DeepEval metrics and persist the results to PostgreSQL eval_logs table.
    Designed to run as a non-blocking background task.
    """
    try:
        from app.db.database import AsyncSessionLocal
        from app.db.models import EvalLog

        scores = await evaluate_research_report(query, final_report, research_findings)

        async with AsyncSessionLocal() as session:
            eval_entry = EvalLog(
                query=query,
                faithfulness_score=scores["faithfulness_score"],
                faithfulness_reason=scores["faithfulness_reason"],
                relevancy_score=scores["relevancy_score"],
                relevancy_reason=scores["relevancy_reason"],
            )
            session.add(eval_entry)
            await session.commit()
            logger.info(f"✓ DeepEval scores saved to PostgreSQL: F={scores['faithfulness_score']}, R={scores['relevancy_score']}")
        return scores
    except Exception as e:
        logger.error(f"Failed to record DeepEval evaluation: {e}", exc_info=True)
        return None


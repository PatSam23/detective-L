"""
Formatter Agent: Converts draft report into final structured intelligence report.

This final node takes the approved draft report and formats it into
the structured FinalReport output with metadata and sources.
"""

import logging
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.core.llm_client import llm
from app.core.models import FinalReport
from app.core.state import AgentState
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _extract_sources(findings: list) -> List[str]:
    """Extract unique URLs from research findings."""
    sources = set()
    for finding in findings:
        data = finding.get("data", {})
        results = data.get("results", [])
        for result in results:
            url = result.get("url", "")
            if url:
                sources.add(url)
    return list(sources)


def _calculate_confidence(fact_check_results: list) -> float:
    """Calculate overall confidence score."""
    if not fact_check_results:
        return 0.5
    
    scores = [c.get("confidence", 0.5) for c in fact_check_results]
    avg = sum(scores) / len(scores)
    
    # Clamp between 0.4 and 0.95 (avoid extremes)
    return max(0.4, min(0.95, avg))


# Create the formatter chain
formatter_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert report formatter. Your job is to:

1. Take the draft report text
2. Extract a clear, concise TITLE (max 80 chars)
3. Write an EXECUTIVE_SUMMARY (2-3 sentences)
4. Break the report into 3-4 SECTIONS, each with:
   - A section title (e.g., "Key Findings", "Implications", "Challenges")
   - Detailed content for that section
5. Format as JSON with "title", "executive_summary", and "sections" fields.
   - sections should be an array of objects: [{"title": "...", "content": "..."}, ...]"""),
    ("human", "{report}")
])

formatter_parser = JsonOutputParser(pydantic_object=FinalReport)

formatter_chain = formatter_prompt | llm | formatter_parser


def formatter_node(state: AgentState) -> dict:
    """
    Formatter node: creates final structured report.
    
    Reads:
        - state["draft_report"]: Approved draft report
        - state["research_findings"]: Source material
        - state["fact_check_results"]: Confidence scores
        - state["revision_count"]: Revisions performed
    
    Writes:
        - state["final_report"]: Structured final output
        - state["sources"]: Extracted source URLs
    
    Args:
        state: Current AgentState
    
    Returns:
        Dictionary with "final_report" and "sources"
    """
    logger.info("Structuring final report")
    
    # Extract sources and confidence
    sources = _extract_sources(state["research_findings"])
    confidence_score = _calculate_confidence(state["fact_check_results"])
    revision_count = state.get("revision_count", 0)
    
    logger.info(f"Extracted {len(sources)} sources, confidence: {confidence_score:.2f}")
    
    # Format the draft report
    try:
        result = formatter_chain.invoke({"report": state["draft_report"]})
        
        # Build final report dict with new schema
        final_report = {
            "title": result.get("title", "Research Report"),
            "executive_summary": result.get("executive_summary", ""),
            "sections": result.get("sections", []),
            "confidence_score": confidence_score,
            "sources": sources,
            "revision_count": revision_count,
        }
        
        logger.info(f"Final report generated: {final_report['title']}")
        logger.info(f"Sections: {len(final_report['sections'])}, Sources: {len(sources)}")
        logger.debug(f"Report structure: title={len(final_report['title'])}, summary={len(final_report['executive_summary'])}")
        
        return {
            "final_report": final_report,
            "sources": sources,
        }
    
    except Exception as e:
        logger.error(f"Error formatting report: {str(e)}", exc_info=True)
        logger.info("Using fallback report structure")
        
        # Fallback to simple structure with new schema
        sections = [
            {
                "title": "Overview",
                "content": state["draft_report"][:300]
            },
            {
                "title": "Key Points",
                "content": state["draft_report"][300:600] if len(state["draft_report"]) > 300 else ""
            }
        ]
        final_report = {
            "title": state["query"][:80],
            "executive_summary": state["draft_report"][:200],
            "sections": sections,
            "confidence_score": confidence_score,
            "sources": sources,
            "revision_count": revision_count,
        }
        
        return {
            "final_report": final_report,
            "sources": sources,
        }

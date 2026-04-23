"""
Critic Agent: Fact-checks claims and scores confidence levels.

This agent implements the "Reflexion" pattern from research papers.
It extracts claims from the draft report, scores each one for confidence,
and determines if revision is needed (up to 2 times max).
"""

import logging
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json

from app.core.llm_client import llm_strict
from app.core.models import Claim, CriticOutput
from app.core.state import AgentState
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Create the critic chain
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert fact-checker and research validator. Your job is to:

1. Extract the 5-7 most important CLAIMS from the provided draft report
2. Score each claim's confidence 0-1 based on:
   - How well-supported it is by the provided sources
   - How specific and verifiable the claim is
   - How recent and reliable the sources are
3. Flag claims below 0.6 confidence
4. Determine if overall revision is needed (if >30% of claims are below 0.6)
5. If revision needed, provide specific instructions for improvement

Output valid JSON with "claims", "needs_revision", and "revision_instructions" fields."""),
    ("human", """Draft Report:
{draft_report}

Source Material:
{sources}

Please analyze and score the claims in this report.""")
])

parser = JsonOutputParser(pydantic_object=CriticOutput)

critic_chain = critic_prompt | llm_strict | parser


def _format_sources(findings: list) -> str:
    """Format research findings for source material."""
    if not findings:
        return "No sources available."
    
    formatted = []
    for finding in findings:
        subtopic = finding.get("subtopic", "Unknown")
        data = finding.get("data", {})
        results = data.get("results", [])
        
        for result in results[:2]:
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")
            formatted.append(f"[{title}] ({url}): {content[:200]}")
    
    return "\n".join(formatted)


def critic_node(state: AgentState) -> dict:
    """
    Critic node: fact-checks draft report and scores confidence.
    
    Reads:
        - state["draft_report"]: The synthesis draft report
        - state["research_findings"]: Source material for fact-checking
        - state["revision_count"]: How many times we've revised (max 2)
    
    Writes:
        - state["fact_check_results"]: List of claim scores
        - state["needs_revision"]: Whether to loop back for revision
        - state["revision_count"]: Increment count
    
    Args:
        state: Current AgentState
    
    Returns:
        Dictionary with fact-check results
    """
    revision_num = state['revision_count']
    logger.info(f"Fact-checking draft report (revision attempt {revision_num})")
    
    try:
        formatted_sources = _format_sources(state["research_findings"])
        
        result = critic_chain.invoke({
            "draft_report": state["draft_report"],
            "sources": formatted_sources
        })
        
        num_claims = len(result.claims)
        low_confidence = sum(1 for c in result.claims if c.confidence < 0.6)
        avg_confidence = sum(c.confidence for c in result.claims) / num_claims if num_claims > 0 else 0
        
        logger.info(f"Analyzed {num_claims} claims")
        logger.info(f"Average confidence: {avg_confidence:.2f}, Low confidence: {low_confidence}/{num_claims}")
        
        # Log individual claims at debug level
        claims_summary = [f"{c.text[:50]}... ({c.confidence:.2f})" for c in result.claims]
        logger.debug(f"Individual claims: {claims_summary}") 
        
        # Can only revise up to 2 times
        needs_revision = result.needs_revision and state["revision_count"] < 2
        logger.info(f"Needs revision: {needs_revision} (result.needs_revision={result.needs_revision})")
        
        return {
            "fact_check_results": [c.dict() for c in result.claims],
            "needs_revision": needs_revision,
            "revision_count": state["revision_count"] + 1,
        }
    except Exception as e:
        logger.error(f"Error in critic node: {str(e)}", exc_info=True)
        raise


def route_after_critic(state: AgentState) -> str:
    """
    Conditional edge routing after critic.
    
    Routes to "revisor" if needs_revision is True, else "format_report".
    """
    if state["needs_revision"]:
        logger.info("Routing to REVISOR for improvement")
        return "revisor"
    else:
        logger.info("Report approved, routing to final formatting")
        return "format_report"

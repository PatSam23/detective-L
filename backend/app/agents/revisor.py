"""
Revisor Agent: Improves the draft report based on Critic feedback.

If the Critic identifies low-confidence claims or issues, the Revisor
rewrites the report with more specificity, better citations, and improved
structure based on the Critic's instructions.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.llm_client import llm
from app.core.state import AgentState
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _format_feedback(fact_check_results: list) -> str:
    """Format fact-check results for the revisor."""
    if not fact_check_results:
        return "No feedback available."
    
    low_confidence = [c for c in fact_check_results if c.get("confidence", 1) < 0.6]
    
    feedback = []
    feedback.append(f"Total claims analyzed: {len(fact_check_results)}")
    feedback.append(f"Low confidence claims: {len(low_confidence)}")
    
    if low_confidence:
        feedback.append("\nClaims that need attention:")
        for claim in low_confidence[:5]:  # Show top 5
            text = claim.get("text", "")
            conf = claim.get("confidence", 0)
            feedback.append(f"  - [{conf:.2f}] {text[:100]}")
    
    return "\n".join(feedback)


# Create the revisor chain
revisor_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert research document revisor. Your job is to:

1. Take a draft report that needs improvement
2. Use the criticism feedback to make it better
3. Focus on:
   - Adding more specific citations and evidence
   - Strengthening low-confidence claims with better sources
   - Clarifying ambiguous statements
   - Improving overall structure and flow
4. Maintain the same general content but improve quality
5. Be more conservative and evidence-based

Output an improved version of the report."""),
    ("human", """Original Query: {query}

Current Report:
{draft_report}

Feedback from Critic:
{feedback}

Please revise and improve this report.""")
])

revisor_parser = StrOutputParser()

revisor_chain = revisor_prompt | llm | revisor_parser


def revisor_node(state: AgentState) -> dict:
    """
    Revisor node: improves draft report based on critic feedback.
    
    Reads:
        - state["query"]: Original user query
        - state["draft_report"]: Current draft report
        - state["fact_check_results"]: Critic's feedback
        - state["revision_count"]: Current revision attempt
    
    Writes:
        - state["draft_report"]: Improved report (replaces old one)
    
    Args:
        state: Current AgentState
    
    Returns:
        Dictionary with updated "draft_report"
    """
    revision_num = state['revision_count']
    logger.info(f"Improving draft report (revision {revision_num})")
    
    try:
        formatted_feedback = _format_feedback(state["fact_check_results"])
        logger.debug(f"Feedback summary: {formatted_feedback[:200]}...")
        
        result = revisor_chain.invoke({
            "query": state["query"],
            "draft_report": state["draft_report"],
            "feedback": formatted_feedback
        })
        
        logger.info(f"Improved report generated ({len(result)} characters)")
        logger.debug(f"Report preview: {result[:200]}...")
        
        return {
            "draft_report": result,
        }
    except Exception as e:
        logger.error(f"Error in revisor node: {str(e)}", exc_info=True)
        raise

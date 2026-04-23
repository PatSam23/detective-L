"""
Synthesis Agent: Merges parallel research findings into a structured draft report.

After all web researchers complete, the synthesis agent takes all findings,
removes duplicates, structures them logically, and creates a draft report.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json

from app.core.llm_client import llm
from app.core.state import AgentState
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _format_findings(findings: list) -> str:
    """Format research findings for the LLM."""
    if not findings:
        return "No research findings available."
    
    formatted = []
    for i, finding in enumerate(findings, 1):
        subtopic = finding.get("subtopic", "Unknown")
        data = finding.get("data", {})
        
        # Extract results from Tavily response
        results = data.get("results", [])
        
        formatted.append(f"\n## Subtopic {i}: {subtopic}")
        
        for j, result in enumerate(results[:3], 1):  # Limit to top 3 per subtopic
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")
            
            formatted.append(f"\n### Result {j}: {title}")
            formatted.append(f"URL: {url}")
            formatted.append(f"Content: {content[:300]}...")
    
    return "\n".join(formatted)


# Create the synthesis chain
synthesis_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert research synthesis specialist. Your job is to:

1. Take research findings from multiple sources on different subtopics
2. Identify and remove duplicates
3. Structure findings into a logical, cohesive draft report
4. Use clear section headers and organize by topic
5. Maintain a neutral, analytical tone
6. Include citations/URLs where appropriate

Output a well-structured markdown report with sections for each major finding."""),
    ("human", """Original Query: {query}

Research Findings:
{findings}

Please synthesize these findings into a comprehensive draft report.""")
])

synthesis_parser = StrOutputParser()

synthesis_chain = synthesis_prompt | llm | synthesis_parser


def synthesis_node(state: AgentState) -> dict:
    """
    Synthesis node: merges research findings into a draft report.
    
    Reads:
        - state["query"]: Original user query
        - state["research_findings"]: List of findings from web researchers
    
    Writes:
        - state["draft_report"]: Structured draft report
    
    Args:
        state: Current AgentState
    
    Returns:
        Dictionary with "draft_report" key
    """
    num_findings = len(state['research_findings'])
    logger.info(f"Merging {num_findings} research findings")
    
    try:
        formatted_findings = _format_findings(state["research_findings"])
        
        result = synthesis_chain.invoke({
            "query": state["query"],
            "findings": formatted_findings
        })
        
        logger.info(f"Draft report generated ({len(result)} characters)")
        logger.debug(f"Report preview: {result[:200]}...")
        
        return {
            "draft_report": result,
        }
    except Exception as e:
        logger.error(f"Error in synthesis node: {str(e)}", exc_info=True)
        raise

"""
Core state management for the LangGraph research agent system.

The AgentState (GraphState) is the single source of truth that flows through
all nodes in the graph. Every node reads from and writes to this state.
"""

from typing import TypedDict, Annotated, List
import operator


class AgentState(TypedDict):
    """
    Shared state dictionary that flows through the entire LangGraph.
    
    This is the spine of the multi-agent system. Every agent node reads from
    and writes to this state. The Annotated fields with operator.add enable
    LangGraph to correctly handle parallel agent writes (appending rather than
    overwriting when multiple agents write simultaneously).
    """
    
    # Input: user query
    query: str
    
    # Planner output: list of subtopics to research
    subtopics: List[str]
    
    # Web/RAG agents output: parallel agents append research findings here
    # Using Annotated[List, operator.add] tells LangGraph to append (not overwrite)
    # when multiple agents write simultaneously
    research_findings: Annotated[List[dict], operator.add]
    
    # Synthesis agent output: merged, structured research report
    draft_report: str
    
    # Critic agent output: fact-checking results
    fact_check_results: List[dict]
    
    # Critic decision: does the report need revision?
    needs_revision: bool
    
    # Revision counter: track how many times we've looped back (max 2)
    revision_count: int
    
    # Final output: structured intelligence report
    final_report: dict
    
    # Sources collected during research
    sources: List[str]

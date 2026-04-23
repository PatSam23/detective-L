"""
Main LangGraph research orchestration pipeline.

This is where all the agents (Planner, Web Researchers, Synthesis, Critic,
Revisor, Formatter) are connected into a single coordinated graph.

The graph structure:
1. Start -> Planner (decompose query)
2. Planner -> Web Researchers (fan-out with Send())
3. Web Researchers -> Synthesis (merge findings)
4. Synthesis -> Critic (fact-check)
5. Critic -> (conditional) Revisor or Formatter
6. Revisor -> Critic (loop, max 2 times)
7. Formatter -> End
"""

import logging
from langgraph.graph import StateGraph, START, END
from langgraph.types import StateSnapshot

from app.core.state import AgentState
from app.core.logging_config import get_logger
from app.agents.planner import planner_node
from app.agents.web_researcher import web_research_agent, fan_out_to_web_researchers
from app.agents.synthesis import synthesis_node
from app.agents.critic import critic_node, route_after_critic
from app.agents.revisor import revisor_node
from app.agents.formatter import formatter_node

logger = get_logger(__name__)


def build_research_graph():
    """
    Build the LangGraph research orchestration pipeline.
    
    Returns:
        Compiled research graph ready for execution
    """
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("web_research_agent", web_research_agent)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("critic", critic_node)
    graph.add_node("revisor", revisor_node)
    graph.add_node("format_report", formatter_node)
    
    # Add edges
    graph.add_edge(START, "planner")
    
    # Planner -> Fan-out to web researchers
    graph.add_conditional_edges(
        "planner",
        fan_out_to_web_researchers
    )
    
    # All web researchers -> Synthesis
    graph.add_edge("web_research_agent", "synthesis")
    
    # Synthesis -> Critic
    graph.add_edge("synthesis", "critic")
    
    # Critic -> (conditional) Revisor or Formatter
    graph.add_conditional_edges(
        "critic",
        route_after_critic
    )
    
    # Revisor loops back to Critic
    graph.add_edge("revisor", "critic")
    
    # Formatter -> End
    graph.add_edge("format_report", END)
    
    # Compile the graph
    return graph.compile()


# Create the global research app
research_app = build_research_graph()


def run_research(query: str, verbose: bool = True) -> dict:
    """
    Run the research pipeline on a query.
    
    Args:
        query: User's research query
        verbose: Print debug output
    
    Returns:
        Final report dictionary
    """
    logger.info(f"Starting research: {query}")
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"🚀 STARTING RESEARCH: {query}")
        print(f"{'='*60}\n")
    
    # Initialize state
    initial_state = {
        "query": query,
        "subtopics": [],
        "research_findings": [],
        "draft_report": "",
        "fact_check_results": [],
        "needs_revision": False,
        "revision_count": 0,
        "final_report": {},
        "sources": [],
    }
    
    try:
        # Run the graph
        result = research_app.invoke(initial_state)
        
        logger.info("Research completed successfully")
        logger.info(f"Final report: {result.get('final_report', {}).get('title', 'N/A')}")
        logger.info(f"Sources: {len(result.get('sources', []))}, Revisions: {result.get('revision_count', 0)}")
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"✅ RESEARCH COMPLETE")
            print(f"{'='*60}\n")
        
        return result
    
    except Exception as e:
        logger.error(f"Research failed: {str(e)}", exc_info=True)
        raise


async def arun_research(query: str, verbose: bool = True) -> dict:
    """
    Async version of run_research for use in FastAPI endpoints.
    
    Args:
        query: User's research query
        verbose: Print debug output
    
    Returns:
        Final report dictionary
    """
    logger.info(f"Starting async research: {query}")
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"🚀 STARTING ASYNC RESEARCH: {query}")
        print(f"{'='*60}\n")
    
    # Initialize state
    initial_state = {
        "query": query,
        "subtopics": [],
        "research_findings": [],
        "draft_report": "",
        "fact_check_results": [],
        "needs_revision": False,
        "revision_count": 0,
        "final_report": {},
        "sources": [],
    }
    
    try:
        # Run the graph asynchronously
        result = await research_app.ainvoke(initial_state)
        
        logger.info("Async research completed successfully")
        logger.info(f"Final report: {result.get('final_report', {}).get('title', 'N/A')}")
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"✅ ASYNC RESEARCH COMPLETE")
            print(f"{'='*60}\n")
        
        return result
    
    except Exception as e:
        logger.error(f"Async research failed: {str(e)}", exc_info=True)
        raise


def stream_research(query: str):
    """
    Stream research progress events for real-time UI updates.
    
    Args:
        query: User's research query
    
    Yields:
        Event dictionaries with progress information
    """
    logger.info(f"Starting stream research: {query}")
    
    initial_state = {
        "query": query,
        "subtopics": [],
        "research_findings": [],
        "draft_report": "",
        "fact_check_results": [],
        "needs_revision": False,
        "revision_count": 0,
        "final_report": {},
        "sources": [],
    }
    
    try:
        event_count = 0
        for event in research_app.stream(initial_state):
            event_count += 1
            logger.debug(f"Stream event {event_count}: {str(event)[:100]}")
            yield event
        
        logger.info(f"Stream research completed with {event_count} events")
    
    except Exception as e:
        logger.error(f"Stream research failed: {str(e)}", exc_info=True)
        raise

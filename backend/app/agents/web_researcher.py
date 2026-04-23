"""
Web Research Agents: Dynamically spawned to research each subtopic in parallel.

Uses the Tavily API for real-time web search. The Send() pattern in LangGraph
allows us to spawn one agent per subtopic, all running in parallel.
"""

import logging
import os
from typing import List
from tavily import TavilyClient
from dotenv import load_dotenv

from app.core.state import AgentState
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Load environment
load_dotenv()

# Initialize Tavily client for web search
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY not found in environment. "
        "Please add it to backend/.env file or set as environment variable."
    )

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


def web_research_agent(state: dict) -> dict:
    """
    Web research agent: searches the web for a specific subtopic.
    
    This node is dynamically spawned via Send() for each subtopic.
    It runs in parallel with other web_research_agent instances.
    
    Reads:
        - state["subtopic"]: The subtopic to research
        - state["original_query"]: The original user query for context
    
    Writes:
        - state["research_findings"]: Appends finding to the list
          (Using Annotated[List, operator.add] ensures append, not overwrite)
    
    Args:
        state: Subgraph state with subtopic and original_query
    
    Returns:
        Dictionary with "research_findings" to append to state
    """
    subtopic = state.get("subtopic", "")
    original_query = state.get("original_query", "")
    search_query = f"{original_query} — {subtopic}"
    
    logger.info(f"Searching subtopic: {subtopic}")
    logger.debug(f"Full search query: {search_query}")
    
    try:
        results = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            max_results=5,
            include_raw_content=False,
        )
        
        num_results = len(results.get('results', []))
        logger.info(f"Found {num_results} results for {subtopic}")
        
        finding = {
            "subtopic": subtopic,
            "data": results,
            "agent_type": "web_search",
        }
        
        return {"research_findings": [finding]}
    
    except Exception as e:
        logger.error(f"Error searching for {subtopic}: {str(e)}", exc_info=True)
        finding = {
            "subtopic": subtopic,
            "data": {"results": [], "error": str(e)},
            "agent_type": "web_search_error",
        }
        return {"research_findings": [finding]}


def fan_out_to_web_researchers(state: AgentState):
    """
    Fan-out function: spawns parallel web researchers using Send().
    
    This is called after the planner generates subtopics. It dynamically
    creates one web_research_agent task per subtopic.
    
    Args:
        state: Current AgentState with subtopics
    
    Returns:
        List of Send() objects, one per subtopic
    """
    from langgraph.constants import Send
    
    num_subtopics = len(state['subtopics'])
    logger.info(f"Spawning {num_subtopics} parallel web researchers")
    
    return [
        Send(
            "web_research_agent",
            {
                "subtopic": topic,
                "original_query": state["query"],
            }
        )
        for topic in state["subtopics"]
    ]

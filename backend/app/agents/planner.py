"""
Planner Agent: Breaks down a user query into research subtopics.

This is the first node in the LangGraph that receives the user's query
and decomposes it into N subtopics. Each subtopic will be researched
by parallel web/RAG agents.
"""

import logging
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from app.core.llm_client import llm_creative
from app.core.state import AgentState
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PlannerOutput(BaseModel):
    """Structured output from the Planner agent."""
    
    subtopics: List[str] = Field(
        description="List of 3-5 research subtopics derived from the query"
    )
    research_depth: str = Field(
        default="advanced",
        description="How deep to research: basic, standard, or advanced"
    )
    reasoning: str = Field(
        description="Brief explanation of why these subtopics were chosen"
    )


# Create the planner chain
planner_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert research strategist. Your job is to take a user's query 
and break it down into 3-5 focused research subtopics that will be researched in parallel.

Each subtopic should:
- Be specific enough to guide a web search
- Cover different angles or aspects of the main query
- Together provide comprehensive coverage of the topic

Output valid JSON with the structure: {{"subtopics": [...], "research_depth": "...", "reasoning": "..."}}
"""),
    ("human", "Query: {query}")
])

parser = JsonOutputParser(pydantic_object=PlannerOutput)

planner_chain = planner_prompt | llm_creative | parser


def planner_node(state: AgentState) -> dict:
    """
    Planner node: breaks query into subtopics.
    
    Reads:
        - state["query"]: User's research question
    
    Writes:
        - state["subtopics"]: List of research subtopics
    
    Args:
        state: Current AgentState
    
    Returns:
        Dictionary with "subtopics" key to update state
    """
    query = state["query"]
    logger.info(f"Processing query: {query[:100]}")
    
    try:
        result = planner_chain.invoke({"query": query})
        logger.info(f"Generated {len(result['subtopics'])} subtopics")
        for i, topic in enumerate(result["subtopics"], 1):
            logger.debug(f"  Subtopic {i}: {topic}")
        return {
            "subtopics": result["subtopics"],
        }
    except Exception as e:
        logger.error(f"Error in planner node: {str(e)}", exc_info=True)
        raise

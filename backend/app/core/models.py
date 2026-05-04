"""
Pydantic models for structured outputs with type validation and serialization.

These models ensure type safety, runtime validation, and clean serialization
across the multi-agent pipeline.
"""

from pydantic import BaseModel, Field
from typing import List


class Claim(BaseModel):
    """A single claim extracted from the draft report during fact-checking."""
    
    text: str = Field(description="The claim text")
    confidence: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Confidence score 0-1 (0=unsure, 1=certain)"
    )
    flagged: bool = Field(
        description="True if confidence is below 0.6 or needs review"
    )


class CriticOutput(BaseModel):
    """Structured output from the Critic agent after fact-checking."""
    
    claims: List[Claim] = Field(
        description="List of claims extracted and scored from the draft report"
    )
    needs_revision: bool = Field(
        description="True if too many low-confidence claims require revision"
    )
    revision_instructions: str = Field(
        description="Specific instructions for the Revisor on what to improve"
    )


class ResearchFinding(BaseModel):
    """A single research finding from a web or RAG agent."""
    
    subtopic: str = Field(description="The subtopic this finding addresses")
    data: dict = Field(description="Raw research data from Tavily or RAG")
    agent_type: str = Field(
        default="web_search",
        description="Type of agent that gathered this (web_search, rag, etc.)"
    )


class FinalReport(BaseModel):
    """The final structured intelligence report output."""
    
    title: str = Field(description="Report title")
    summary: str = Field(description="Executive summary/overview")
    key_findings: List[str] = Field(description="List of key findings")
    analysis: str = Field(description="Detailed analysis")
    confidence_score: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Overall confidence of the report"
    )
    sources: List[str] = Field(description="All sources cited")
    claims: List[Claim] = Field(default_factory=list, description="Claims with confidence scores")
    revision_count: int = Field(default=0, description="Number of times the report was revised")

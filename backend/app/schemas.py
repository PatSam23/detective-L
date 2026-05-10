"""Pydantic schemas for API request/response contracts."""

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    """Schema for POST /research and POST /research/stream endpoints."""
    query: str = Field(
        ..., 
        min_length=5, 
        description="The research topic to investigate"
    )


class ResearchResponse(BaseModel):
    """Schema for POST /research synchronous endpoint response."""
    status: str = Field(description="Status of the research (e.g., 'success')")
    final_report: dict = Field(description="Structured final research report with title, sections, etc.")
    sources: list[str] = Field(description="List of source URLs cited in the report")
    revision_count: int = Field(description="Number of times the report was revised by the Revisor agent")

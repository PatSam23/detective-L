from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import logging
import asyncio

from app.core.graph import arun_research, astream_research, research_app

# Setup minimal file logger specifically for API entry if needed
logger = logging.getLogger("api")

app = FastAPI(
    title="Detective-L Research API",
    description="Multi-agent parallel research intelligence system",
    version="1.0.0"
)

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=5, description="The research topic to investigate")


class ResearchResponse(BaseModel):
    status: str
    final_report: dict
    sources: list[str]
    revision_count: int


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "detective-l"}


@app.post("/research", response_model=ResearchResponse)
async def run_research_sync(request: ResearchRequest):
    """
    Execute the research pipeline synchronously. 
    This blocks until all agents complete and the final report is generated.
    """
    try:
        logger.info(f"Received sync research request: {request.query}")
        # Run graph
        result = await arun_research(request.query, verbose=False)
        
        return ResearchResponse(
            status="success",
            final_report=result.get("final_report", {}),
            sources=result.get("sources", []),
            revision_count=result.get("revision_count", 0)
        )
    except Exception as e:
        logger.error(f"Error in research processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/stream")
async def stream_research_events(request: ResearchRequest):
    """
    Execute research pipeline and stream SSE events for each agent's progress.
    """
    logger.info(f"Received streaming research request: {request.query}")
    
    async def generate_events():
        try:
            async for event in astream_research(request.query):
                # Format as SSE
                for node_name, state_update in event.items():
                    # Filter out large/non-serializable data from state_update
                    filtered_update = {}
                    for key, value in state_update.items():
                        # Skip large lists like research_findings to avoid payload bloat
                        if key in ["research_findings", "draft_report"] and isinstance(value, (list, str)):
                            filtered_update[key] = f"<{key}>{len(value)} items" if isinstance(value, list) else f"<{key}>{len(value)} chars"
                        else:
                            try:
                                json.dumps(value)  # Test serializability
                                filtered_update[key] = value
                            except (TypeError, ValueError):
                                filtered_update[key] = str(value)
                    
                    payload = {
                        "type": "agent_update",
                        "name": node_name,
                        "data": filtered_update
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                    
            # Send final explicit completion event
            yield f"data: {json.dumps({'type': 'research_complete'})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate_events(), media_type="text/event-stream")

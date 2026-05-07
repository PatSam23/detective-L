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
    Sends agent_start, agent_update, and agent_complete events for proper frontend tracking.
    """
    logger.info(f"Received streaming research request: {request.query}")
    
    async def generate_events():
        try:
            agent_started = set()  # Track which agents have sent start event
            
            async for event in astream_research(request.query):
                # Process each node in the event
                for node_name, state_update in event.items():
                    # Send agent_start event on first appearance
                    if node_name not in agent_started:
                        agent_started.add(node_name)
                        start_payload = {
                            "type": "agent_start",
                            "name": node_name,
                        }
                        yield f"data: {json.dumps(start_payload)}\n\n"
                        logger.debug(f"Sent agent_start for {node_name}")
                    
                    # Filter out large/non-serializable data to reduce payload size
                    filtered_update = {}
                    for key, value in state_update.items():
                        # Skip large lists/strings to minimize payload
                        if key in ["research_findings", "draft_report"]:
                            if isinstance(value, list):
                                filtered_update[key] = f"<{len(value)} items>"
                            elif isinstance(value, str):
                                filtered_update[key] = f"<{len(value)} chars>"
                        else:
                            try:
                                json.dumps(value)  # Test serializability
                                filtered_update[key] = value
                            except (TypeError, ValueError):
                                filtered_update[key] = str(value)
                    
                    # Send agent_update with filtered data
                    update_payload = {
                        "type": "agent_update",
                        "name": node_name,
                        "data": filtered_update
                    }
                    yield f"data: {json.dumps(update_payload)}\n\n"
                    
                    # Send agent_complete after processing
                    # (in LangGraph streaming, each event means the node has completed)
                    complete_payload = {
                        "type": "agent_complete",
                        "name": node_name,
                    }
                    yield f"data: {json.dumps(complete_payload)}\n\n"
                    logger.debug(f"Sent agent_complete for {node_name}")
                    
            # Send final explicit completion event
            research_complete_payload = {
                "type": "research_complete"
            }
            yield f"data: {json.dumps(research_complete_payload)}\n\n"
            logger.info("Research stream completed successfully")
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            error_payload = {
                "type": "error",
                "message": str(e)
            }
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

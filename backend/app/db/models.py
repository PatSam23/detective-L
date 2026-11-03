from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class LLMUsageLog(Base):
    __tablename__ = "llm_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True, nullable=False)
    model = Column(String, index=True, nullable=False)
    messages = Column(JSON, nullable=False)
    temperature = Column(Float, nullable=False)
    max_tokens = Column(Integer, nullable=False)
    
    response_content = Column(String, nullable=True)
    
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    latency_ms = Column(Float, nullable=False)
    cache_hit = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class EvalLog(Base):
    __tablename__ = "eval_logs"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    faithfulness_score = Column(Float, nullable=False, default=0.0)
    faithfulness_reason = Column(String, nullable=True)
    relevancy_score = Column(Float, nullable=False, default=0.0)
    relevancy_reason = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


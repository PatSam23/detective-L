"""
LLM client configuration for Google Gemini API.

Initializes and configures the LangChain ChatGoogleGenerativeAI client
with proper settings for the detective-L system.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found in environment. "
        "Please add it to backend/.env file."
    )


def get_llm(temperature: float = 0.7, model: str = "gemini-2.5-flash") -> ChatGoogleGenerativeAI:
    """
    Get configured LLM client for Gemini API.
    
    Args:
        temperature: Sampling temperature (0.0-1.0). Higher = more creative.
        model: Model name (default: gemini-2.5-flash - latest and stable)
    
    Returns:
        Configured ChatGoogleGenerativeAI client
    """
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        api_key=GEMINI_API_KEY,
        max_tokens=4096,
        timeout=60,
    )


# Create default LLM instance for single imports
llm = get_llm(temperature=0.5)

# LLM for creative tasks (brainstorming, planning)
llm_creative = get_llm(temperature=0.8)

# LLM for fact-checking (lower temp = more conservative)
llm_strict = get_llm(temperature=0.2)

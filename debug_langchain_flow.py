"""
Debug script to show the complete LangChain flow and message structure.

This script enables full LangChain debugging to show:
1. Exactly what messages are sent to the LLM
2. How output parsers process the LLM response
3. The complete prompt structure
"""

import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Enable LangChain debugging BEFORE importing LangChain modules
os.environ["LANGCHAIN_DEBUG"] = "true"

# Import after setting debug env
from langchain_core.globals import set_debug
from app.core.logging_config import setup_logging, get_logger

# Enable debug for LangChain core
set_debug(True)

# Set up logging at DEBUG level to see everything
setup_logging(level=logging.DEBUG, console=True)
logger = get_logger(__name__)

# Import agents after logging is configured
from app.agents.planner import planner_chain, parser
from app.core.llm_client import llm_creative


def test_planner_chain():
    """Test the planner chain to see complete message flow."""
    print("\n" + "=" * 80)
    print("TESTING PLANNER CHAIN - FULL LANGCHAIN FLOW")
    print("=" * 80 + "\n")
    
    query = "What are the latest developments in artificial intelligence and machine learning?"
    
    logger.info(f"Starting planner chain test with query: {query}")
    print(f"\n[INPUT] QUERY:\n{query}\n")
    
    try:
        # Invoke the chain - this will show all intermediate steps
        result = planner_chain.invoke({"query": query})
        
        print("\n" + "=" * 80)
        print("OUTPUT PARSER RESULT (Pydantic Model)")
        print("=" * 80)
        print(f"\nParsed Output Type: {type(result)}")
        print(f"\nSubtopics ({len(result['subtopics'])} total):")
        for i, topic in enumerate(result["subtopics"], 1):
            print(f"  {i}. {topic}")
        print(f"\nResearch Depth: {result.get('research_depth', 'N/A')}")
        print(f"\nReasoning: {result.get('reasoning', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Error in planner chain: {str(e)}", exc_info=True)
        raise


def show_chain_structure():
    """Show the chain structure and how components connect."""
    print("\n" + "=" * 80)
    print("CHAIN STRUCTURE EXPLANATION")
    print("=" * 80)
    
    explanation = """
CHAIN PIPELINE: prompt | llm | parser
                  ↓      ↓      ↓

1. PROMPT (ChatPromptTemplate)
   - System message: Instructs the model on its role
   - Human message: Contains the user input ({query})
   - Creates a formatted message ready for the LLM
   
   OUTPUT: List[BaseMessage] objects
   
2. LLM (ChatGoogleGenerativeAI)
   - Takes the message list
   - Sends to Google Gemini API
   - Returns: AIMessage with text content
   
   OUTPUT: AIMessage object with 'content' field
   
3. PARSER (JsonOutputParser)
   - Takes the LLM response text
   - Extracts JSON from the text
   - Validates against PlannerOutput Pydantic model
   - Converts JSON to Python dictionary
   
   OUTPUT: dict matching the Pydantic model schema

WHAT ACTUALLY GETS SENT TO THE LLM:
1. Formatted messages (not raw strings)
2. The messages contain:
   - role: "system" or "user"
   - content: The actual prompt text
3. LLM client adds configuration:
   - model: "gemini-2.5-flash"
   - temperature: 0.8 (for planner = creative)
   - max_tokens: 4096

WHAT COMES BACK FROM THE LLM:
1. AIMessage object with:
   - content: Raw text response (usually contains JSON)
   - response_metadata: Info about the API call
   - usage_metadata: Token counts
   
2. Output parser extracts the JSON and validates it
3. Result is a clean Python dict/Pydantic model instance
    """
    print(explanation)


if __name__ == "__main__":
    print("\n[DEBUG] LANGCHAIN COMPLETE FLOW ANALYSIS\n")
    
    show_chain_structure()
    test_planner_chain()
    
    print("\n[SUCCESS] Test completed. Check the logs above for complete message flow.\n")

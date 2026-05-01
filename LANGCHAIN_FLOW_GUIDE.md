# Complete LangChain Flow: From Output Parser to LLM

## Overview

This document breaks down **exactly** how your output parser gets sent to the LLM, using real logs from your detective-L system.

---

## The Complete Flow Pipeline

```
User Input
    ↓
ChatPromptTemplate (Formats the message)
    ↓
ChatGoogleGenerativeAI (Sends to Gemini API)
    ↓
LLM Response (Raw text with JSON)
    ↓
JsonOutputParser (Extracts & validates JSON)
    ↓
Python Dictionary/Pydantic Model
```

---

## Step 1: Creating the Chain

### Your Code (in planner.py)
```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Define expected output structure
class PlannerOutput(BaseModel):
    subtopics: List[str] = Field(description="List of 3-5 research subtopics")
    research_depth: str = Field(default="advanced", description="How deep to research")
    reasoning: str = Field(description="Brief explanation of why these subtopics were chosen")

# Create the prompt template
planner_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert research strategist..."""),
    ("human", "Query: {query}")
])

# Create the parser
parser = JsonOutputParser(pydantic_object=PlannerOutput)

# Chain them together: prompt | llm | parser
planner_chain = planner_prompt | llm_creative | parser
```

**Why this matters:**
- `parser` tells LangChain to expect JSON output matching `PlannerOutput`
- The `|` operator chains components in a pipeline
- Order matters: `prompt | llm | parser`

---

## Step 2: What Gets Sent to the LLM (Real Logs)

When you call `planner_chain.invoke({"query": query})`, here's what LangChain sends:

### The Prompt Transformation
```
[chain/start] [chain:RunnableSequence > prompt:ChatPromptTemplate]
Input: {"query": "What are the latest developments in artificial intelligence...?"}
```

### What Actually Goes to the API
```
[llm/start] [chain:RunnableSequence > llm:ChatGoogleGenerativeAI]
Entering LLM run with input:
{
  "prompts": [
    "System: You are an expert research strategist. Your job is to take a user's query 
    and break it down into 3-5 focused research subtopics that will be researched in parallel.
    
    Each subtopic should:
    - Be specific enough to guide a web search
    - Cover different angles or aspects of the main query
    - Together provide comprehensive coverage of the topic
    
    Output valid JSON with the structure: {\"subtopics\": [...], \"research_depth\": \"...\", \"reasoning\": \"...\"}
    
    Human: Query: What are the latest developments in artificial intelligence and machine learning?"
  ]
}
```

**Key Point:** The system prompt + user message are merged into a single prompt string sent to the API.

### HTTP Request to Gemini API
```
HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
Status: 200 OK
Time: 8.02s
```

**Configuration sent with the request:**
- `model`: "gemini-2.5-flash"
- `temperature`: 0.8 (for creative planner)
- `max_tokens`: 4096
- `api_key`: GEMINI_API_KEY (from environment)

---

## Step 3: LLM Response (Raw Text)

### What Comes Back
```json
{
  "text": "```json\n{\n  \"subtopics\": [\n    \"Latest breakthroughs and architectural innovations in Generative AI...\",\n    \"Recent advancements and applications of AI/ML in scientific discovery...\",\n    ...\n  ],\n  \"research_depth\": \"high\",\n  \"reasoning\": \"The user's query asks for 'latest developments'...\"\n}\n```",
  "generation_info": {
    "finish_reason": "STOP",
    "model_name": "gemini-2.5-flash",
    "safety_ratings": []
  },
  "usage_metadata": {
    "input_tokens": 119,      # Your prompt = 119 tokens
    "output_tokens": 1180,    # Model response = 1180 tokens
    "total_tokens": 1299
  }
}
```

**Important:** The response is wrapped in markdown code blocks: `` ```json ... ``` ``

---

## Step 4: Output Parser Extracts the JSON

### Parser Log
```
[chain/start] [chain:RunnableSequence > parser:JsonOutputParser]
Entering Parser run with input: [inputs]
```

### What the Parser Does

1. **Extracts JSON** from the markdown code blocks
   ```python
   # LangChain internally does something like:
   import json
   import re
   
   # Remove markdown wrappers
   json_str = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL).group(1)
   
   # Parse JSON
   parsed = json.loads(json_str)
   ```

2. **Validates** against the Pydantic model
   ```python
   # LangChain validates that all required fields exist:
   # - subtopics: List[str] ✓
   # - research_depth: str ✓
   # - reasoning: str ✓
   ```

3. **Returns** clean Python dict (or Pydantic model instance)
   ```python
   {
     "subtopics": [
       "Latest breakthroughs and architectural innovations in Generative AI...",
       "Recent advancements and applications of AI/ML in scientific discovery...",
       ...
     ],
     "research_depth": "high",
     "reasoning": "The user's query asks for 'latest developments'..."
   }
   ```

### Parser Log Output
```
[chain/end] [chain:RunnableSequence > parser:JsonOutputParser] [26ms]
Exiting Parser run with output:
{
  "subtopics": [...],
  "research_depth": "high",
  "reasoning": "..."
}
```

---

## Step 5: Final Result

```python
result = planner_chain.invoke({"query": query})

# result is now a clean Python dict:
{
  "subtopics": [
    "Latest breakthroughs and architectural innovations in Generative AI...",
    "Recent advancements and applications of AI/ML in scientific discovery...",
    "Developments in Edge AI, efficient AI algorithms...",
    "Emerging trends in ethical AI, AI safety research...",
    "Progress in Reinforcement Learning (RL), robotics..."
  ],
  "research_depth": "high",
  "reasoning": "The user's query asks for 'latest developments'..."
}
```

---

## How This Works in Your Graph (Planner Node)

```python
def planner_node(state: AgentState) -> dict:
    query = state["query"]
    
    # This internally runs: prompt | llm | parser
    result = planner_chain.invoke({"query": query})
    
    # result is already parsed and validated
    # No need to manually parse JSON!
    return {
        "subtopics": result['subtopics'],  # Already a list
    }
```

---

## Key Insights

### 1. **The Parser is Defined BEFORE Sending**
- When you create `JsonOutputParser(pydantic_object=PlannerOutput)`, it tells LangChain what to expect
- LangChain can include hints in the prompt: "Output valid JSON with structure: {...}"

### 2. **The LLM is Instructed in the Prompt**
```
Output valid JSON with the structure: {"subtopics": [...], "research_depth": "...", "reasoning": "..."}
```
This instruction is in your `("system", "...")` message!

### 3. **The Parser Handles Messy Responses**
- LLM wraps JSON in markdown: `` ```json { ... } ``` ``
- Parser extracts and cleans it up
- Validates against your Pydantic schema
- Returns clean Python dict

### 4. **Token Usage is Tracked**
```
input_tokens: 119       # Your prompt cost
output_tokens: 1180     # LLM response cost
total_tokens: 1299      # Billable to Gemini API
```

### 5. **Temperature Controls Creativity**
```python
llm_creative = get_llm(temperature=0.8)  # Used in planner (creative)
llm_strict = get_llm(temperature=0.2)    # Used in critic (conservative)
```

---

## Complete Message Flow Diagram

```
YOU:
    query = "What are the latest developments in AI?"
    
PROMPT TEMPLATE:
    System: "You are an expert research strategist..."
    + Human: "Query: What are the latest developments in AI?"
    = Single formatted string
    
LLM (Gemini API):
    Input:  119 tokens (your prompt)
    Process: 8.02 seconds
    Output: 1180 tokens (JSON response)
    
OUTPUT PARSER:
    Raw: "```json\n{...}\n```"
    Cleaned: Extract JSON from markdown
    Validated: Check against PlannerOutput schema
    Result: {"subtopics": [...], "research_depth": "high", ...}
    
YOUR CODE:
    result['subtopics']  # Ready to use!
```

---

## How Other Agents Use Parsers

### Synthesis Agent (StrOutputParser)
```python
synthesis_chain = synthesis_prompt | llm | StrOutputParser()
# Returns: Raw string (markdown report)
```

### Critic Agent (JsonOutputParser)
```python
critic_chain = critic_prompt | llm_strict | JsonOutputParser(pydantic_object=CriticOutput)
# Returns: dict with "claims", "needs_revision", "revision_instructions"
```

---

## Troubleshooting

### Problem: "JSON not found in output"
```
JsonDecodeError: No JSON found in model output
```
**Solution:** The LLM didn't output JSON. Check:
1. Your system prompt instructions
2. Whether the model followed directions
3. Add stricter validation in output schema

### Problem: Validation fails
```
ValidationError: 'subtopics' field required
```
**Solution:** The LLM output doesn't match your Pydantic schema
- Ensure all required fields are in the model
- Add descriptive field instructions
- Make optional fields with defaults if needed

### Problem: Slow parsing
- JsonOutputParser is very fast (~26ms in your logs)
- Usually the LLM is the bottleneck (8.02s)

---

## Summary

1. **You define** the structure with Pydantic models
2. **You create** a parser with `JsonOutputParser(pydantic_object=YourModel)`
3. **You chain** it: `prompt | llm | parser`
4. **LangChain formats** the prompt and sends to the API
5. **API responds** with JSON (usually in markdown)
6. **Parser extracts** and validates the JSON
7. **You get** clean Python dict/model instances

The entire flow is type-safe, validated, and handles the messy business of LLM responses automatically!

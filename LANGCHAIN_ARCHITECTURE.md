# LangChain Architecture in Detective-L

Visual guide showing how LangChain components work together in your system.

---

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│                                                                   │
│  [Research Form] ──→ POST /research ──→ [Research Results]      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓ FastAPI
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│  main.py: run_research_sync(request)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                 LangGraph Research App                           │
│                   (graph.py)                                     │
│                                                                   │
│  research_app = build_research_graph()                          │
│  result = research_app.invoke(initial_state)                    │
└──┬────────┬──────────┬─────────┬─────────────┬──────────────────┘
   │        │          │         │             │
   ↓        ↓          ↓         ↓             ↓
  [1]      [2]        [3]       [4]           [5]
 PLANNER  WEB QUERY  SYNTHESIS  CRITIC      REVISOR/
                                            FORMATTER
```

---

## Detailed: LangChain Pipeline for Each Agent

### Agent Pattern (All agents follow this):

```
INPUT STATE
    │
    ↓
┌─────────────────────────────────────────┐
│  ChatPromptTemplate                     │
│  - System message (role/instructions)   │
│  - Human message (variables from input) │
│  - Formats into BaseMessage list        │
└─────────┬───────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────┐
│  ChatGoogleGenerativeAI (LLM)           │
│  - model: "gemini-2.5-flash"            │
│  - temperature: varies by agent         │
│  - max_tokens: 4096                     │
│  - Sends to API, waits, returns text    │
└─────────┬───────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────┐
│  OutputParser                           │
│  - JsonOutputParser (most agents)       │
│  - StrOutputParser (synthesis)          │
│  - Validates output against schema      │
└─────────┬───────────────────────────────┘
          │
          ↓
     PYTHON DICT
   (ready to use)
       │
       ↓
  State Updated
```

---

## Agent Configurations

### 1️⃣ PLANNER AGENT

```
Code: app/agents/planner.py

Input:
  state["query"] = "What are latest AI developments?"

Prompt Template:
  System: "You are an expert research strategist..."
  Human: "Query: {query}"

LLM Config:
  llm_creative (temperature=0.8)

Output Parser:
  JsonOutputParser(pydantic_object=PlannerOutput)
  
Expected Output Schema:
  {
    "subtopics": List[str],
    "research_depth": str,
    "reasoning": str
  }

Output State Update:
  state["subtopics"] = [5 research topics]
```

**Chain:**
```python
planner_chain = planner_prompt | llm_creative | parser
```

---

### 2️⃣ WEB RESEARCHER AGENT

```
Code: app/agents/web_researcher.py

Input:
  state["subtopics"] = [topic1, topic2, topic3, topic4, topic5]

For Each Subtopic:
  → Search via Tavily API
  → Collect results
  → Store in state["research_findings"]

Output Parser:
  No parser needed (raw API results)

Output State Update:
  state["research_findings"] = [
    {
      "subtopic": "...",
      "data": {
        "results": [
          {"title": "...", "url": "...", "content": "..."},
          ...
        ]
      }
    },
    ...
  ]
```

---

### 3️⃣ SYNTHESIS AGENT

```
Code: app/agents/synthesis.py

Input:
  state["query"] = original query
  state["research_findings"] = [5 research topic results]

Prompt Template:
  System: "You are an expert research synthesis specialist..."
  Human: "Original Query: {query}\nResearch Findings:\n{findings}"

LLM Config:
  llm (temperature=0.5)

Output Parser:
  StrOutputParser()  ← Note: Returns raw string, not JSON!

Output State Update:
  state["draft_report"] = """
  # Research Report
  
  ## Topic 1
  ...
  """
```

**Chain:**
```python
synthesis_chain = synthesis_prompt | llm | StrOutputParser()
```

---

### 4️⃣ CRITIC AGENT

```
Code: app/agents/critic.py

Input:
  state["draft_report"] = markdown report
  state["research_findings"] = source material
  state["revision_count"] = 0 (or 1, max 2)

Prompt Template:
  System: "You are an expert fact-checker..."
  Human: "Draft Report:\n{draft_report}\n\nSource Material:\n{sources}"

LLM Config:
  llm_strict (temperature=0.2)  ← Conservative for fact-checking

Output Parser:
  JsonOutputParser(pydantic_object=CriticOutput)

Expected Output Schema:
  {
    "claims": List[Claim],  # Each with text, confidence_score
    "needs_revision": bool,
    "revision_instructions": str
  }

Output State Update:
  state["fact_check_results"] = claims
  state["needs_revision"] = True/False
  state["revision_count"] += 1
```

**Chain:**
```python
critic_chain = critic_prompt | llm_strict | parser
```

---

### 5️⃣ REVISOR & FORMATTER AGENTS

```
Code: app/agents/revisor.py & formatter.py

REVISOR:
  If state["needs_revision"] == True AND revision_count < 2:
    → Revise draft_report based on fact_check_results
    → Loop back to Critic for another pass

FORMATTER:
  After critic approval (or 2 revisions):
    → Convert draft_report to structured JSON
    → Extract key findings
    → Format for final output

Output:
  state["final_report"] = {
    "title": "...",
    "sections": [...],
    "key_findings": [...]
  }
```

---

## Temperature Settings by Agent

```python
# llm_creative (temperature=0.8)
Used by: PLANNER
Purpose: Brainstorm diverse research angles
Behavior: More creative, varied outputs

# llm (temperature=0.5)
Used by: SYNTHESIS
Purpose: Organize findings coherently
Behavior: Balanced between creative & deterministic

# llm_strict (temperature=0.2)
Used by: CRITIC
Purpose: Fact-check conservatively
Behavior: Focused, deterministic, risk-averse
```

**Why Different Temps?**
- Planner should think creatively about angles
- Critic should be conservative about claims
- Synthesis should balance both

---

## Message Flow Through Chain

### Step-by-Step: Planner Chain

```
1. USER CALLS:
   result = planner_chain.invoke({"query": "What is AI?"})

2. PROMPT TEMPLATE CREATES:
   [
     SystemMessage(content="You are an expert research strategist..."),
     HumanMessage(content="Query: What is AI?")
   ]

3. LLM RECEIVES (as single string):
   "System: You are an expert research strategist...
    
    Human: Query: What is AI?"

4. LLM GENERATES:
   "```json
    {
      \"subtopics\": [...],
      \"research_depth\": \"advanced\",
      \"reasoning\": \"...\"
    }
    ```"

5. PARSER EXTRACTS:
   • Detects markdown code blocks
   • Extracts JSON between ```...```
   • Parses JSON string to Python dict
   • Validates against PlannerOutput schema

6. RETURNS:
   {
     "subtopics": [...],
     "research_depth": "advanced",
     "reasoning": "..."
   }

7. YOUR CODE GETS:
   result["subtopics"]  # Clean list of strings
```

---

## State Flow Through Graph

```
Initial State:
{
  "query": "What is AI?",
  "subtopics": [],
  "research_findings": [],
  "draft_report": "",
  "fact_check_results": [],
  "needs_revision": False,
  "revision_count": 0,
  "final_report": {},
  "sources": []
}
        │
        ↓
    PLANNER NODE
        │
        ├─→ state["subtopics"] = ["LLMs", "RL", ...]
        │
        ↓
   WEB RESEARCHERS (parallel)
        │
        ├─→ state["research_findings"] = [results...]
        │
        ↓
   SYNTHESIS NODE
        │
        ├─→ state["draft_report"] = "# AI Report\n..."
        │
        ↓
   CRITIC NODE
        │
        ├─→ state["fact_check_results"] = [claims...]
        ├─→ state["needs_revision"] = True/False
        ├─→ state["revision_count"] = 1
        │
        ↓ (if needs_revision)
   REVISOR NODE
        │
        ├─→ state["draft_report"] = "# Revised AI Report\n..."
        ├─→ state["revision_count"] = 2
        │
        ↓ (loop back to CRITIC if revision_count < 2)
   
   [CRITIC checks again]
        │
        ↓ (if OK or revision_count >= 2)
   FORMATTER NODE
        │
        ├─→ state["final_report"] = {structured JSON}
        ├─→ state["sources"] = [all sources]
        │
        ↓
   Final State returned to API
```

---

## Code Example: End-to-End

```python
# 1. SETUP: Define output schema
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

class PlannerOutput(BaseModel):
    subtopics: List[str] = Field(description="...")
    research_depth: str = Field(...)
    reasoning: str = Field(...)

# 2. SETUP: Create prompt template
from langchain_core.prompts import ChatPromptTemplate

planner_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research strategist..."),
    ("human", "Query: {query}")
])

# 3. SETUP: Create parser
parser = JsonOutputParser(pydantic_object=PlannerOutput)

# 4. SETUP: Get LLM
from app.core.llm_client import llm_creative

# 5. SETUP: Create chain
planner_chain = planner_prompt | llm_creative | parser

# 6. RUN: Invoke chain
result = planner_chain.invoke({"query": "What is AI?"})
#        ↑ This internally:
#        - Formats prompt
#        - Sends to API
#        - Parses JSON response
#        - Validates schema
#        - Returns dict

# 7. USE: Access parsed result
print(result["subtopics"])     # Already a list!
print(result["research_depth"]) # Already a string!
print(result["reasoning"])      # Already a string!

# No need to manually parse JSON - parser did it all!
```

---

## Common Patterns

### Pattern 1: JSON Output
```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser(pydantic_object=YourModel)
chain = prompt | llm | parser

result = chain.invoke(input_data)
# result is dict matching YourModel schema
```

### Pattern 2: String Output
```python
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
chain = prompt | llm | parser

result = chain.invoke(input_data)
# result is raw string (no parsing)
```

### Pattern 3: Structured Output
```python
from langchain_core.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=YourModel)
chain = prompt | llm | parser

result = chain.invoke(input_data)
# result is Pydantic model instance (has .dict() method)
```

---

## Troubleshooting Guide

### "JSON Parsing Failed"
```
Cause: LLM didn't output valid JSON
Fix:
  1. Check system prompt - is it clear about JSON format?
  2. Add example in prompt: "Output like: {\"field\": \"value\"}"
  3. Lower temperature (0.3-0.5)
```

### "ValidationError: field required"
```
Cause: LLM output missing required field
Fix:
  1. Make sure all required fields in Pydantic model
  2. Add descriptions to fields
  3. Include required fields in system prompt
```

### "Timeout after 60 seconds"
```
Cause: LLM API too slow
Fix:
  1. Check API status
  2. Reduce max_tokens
  3. Simplify prompt
  4. Increase timeout in llm_client.py
```

### "Validation error: subtopics must be List[str]"
```
Cause: LLM returned wrong type
Fix:
  1. Be explicit: "subtopics should be a list of strings"
  2. Add example: "subtopics: [\"topic1\", \"topic2\"]"
  3. Use Union types if flexible: List[str] | str
```

---

## Performance Notes

```
Typical Latencies:
├─ Prompt formatting:     < 1ms
├─ Network latency:       ~500ms
├─ LLM generation:        ~5000ms (LLM thinking)
├─ Response download:     ~1500ms
├─ JSON parsing:          ~26ms
├─ Validation:            ~5ms
└─ Total:                 ~7s per agent call

Graph with 5 parallel researchers (sequential):
├─ Planner:              ~8s
├─ 5 Web Researchers:    ~12s × 5 = ~15s (parallel, ~15s)
├─ Synthesis:           ~6s
├─ Critic:              ~8s
├─ Revisor (if needed): ~8s
└─ Formatter:           ~4s
   Total (end-to-end):  ~45-55 seconds
```

---

## Summary

1. **Each agent has a chain:** `prompt | llm | parser`
2. **Prompt is formatted** before sending to LLM
3. **LLM receives merged system + human message**
4. **Parser extracts and validates** JSON response
5. **Your code gets clean Python objects**
6. **State flows through graph** from agent to agent
7. **Temperature controls creativity** for each agent
8. **Everything is logged** in debug mode

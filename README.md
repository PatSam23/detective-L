# detective-L: Multi-Agent Enterprise Research Intelligence Platform 

"An autonomous multi-agent system that researches any business topic by orchestrating specialized AI agents in parallel, synthesizes findings into structured intelligence reports, fact-checks its own output, and delivers everything through a real-time streaming dashboard — built on LangGraph, LangChain, and fully observable via LangSmith."
  
## The Architecture
- **Planner Agent:** Breaks query into N subtopics and assigns agent types.
- **Web Agents / RAG Agents:** Dynamically spawn to gather knowledge in parallel.
- **Synthesis Agent:** Merges findings, removes duplicates, structures report.
- **Critic Agent:** Fact-checks claims, scores confidence, flags uncertainty.
- **Revisor Agent:** Automatically revises based on the Critic's instructions (loops max 2 times).

## Tech Stack 
### Backend
- **LangGraph** — multi-agent orchestration, state, cycles
- **LangChain** — LLM calls, RAG, tools, prompts
- **LangSmith** — full observability, eval dashboards
- **FastAPI** — streaming API server
- **Tavily API** — real-time web search
- **ChromaDB** — vector store for internal knowledge

### Frontend
- **Next.js** — framework
- **Tailwind CSS** — styling
- **Framer Motion** — animations for agent status lights
- **SSE / WebSockets** — real-time streaming from FastAPI to UI

## Installation

\\\ash
git clone https://github.com/PatSam23/detective-L.git
cd detective-L
\\\

## License
This project is licensed under the MIT License - see the LICENSE file for details.

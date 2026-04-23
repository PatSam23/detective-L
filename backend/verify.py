#!/usr/bin/env python3
"""
Quick verification script to check all imports and graph structure.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_imports():
    """Verify all modules can be imported."""
    print("Verifying imports...\n")
    
    try:
        print("  ✓ Importing AgentState...")
        from app.core.state import AgentState
        
        print("  ✓ Importing Pydantic models...")
        from app.core.models import Claim, CriticOutput, ResearchFinding, FinalReport
        
        print("  ✓ Importing LLM client...")
        from app.core.llm_client import get_llm, llm, llm_creative, llm_strict
        
        print("  ✓ Importing agents...")
        from app.agents.planner import planner_node
        from app.agents.web_researcher import web_research_agent, fan_out_to_web_researchers
        from app.agents.synthesis import synthesis_node
        from app.agents.critic import critic_node, route_after_critic
        from app.agents.revisor import revisor_node
        from app.agents.formatter import formatter_node
        
        print("  ✓ Importing graph...")
        from app.core.graph import build_research_graph, run_research, arun_research, stream_research
        
        print("\nAll imports successful!\n")
        return True
    
    except ImportError as e:
        print(f"\nImport error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def verify_graph_structure():
    """Verify the graph structure."""
    print("Verifying graph structure...\n")
    
    try:
        from app.core.graph import research_app
        
        print(f"  + Graph type: {type(research_app)}")
        print(f"  + Graph nodes: {list(research_app.nodes.keys())}")
        
        # Try to get the schema
        try:
            schema = research_app.get_schema()
            print(f"  + Graph schema available")
        except:
            print(f"  * Graph schema not available (may need compilation)")
        
        print("\nGraph structure verified!\n")
        return True
    
    except Exception as e:
        print(f"\nGraph verification error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verifications."""
    print("\n" + "="*60)
    print("DETECTIVE-L VERIFICATION SUITE")
    print("="*60 + "\n")
    
    imports_ok = verify_imports()
    graph_ok = verify_graph_structure()
    
    if imports_ok and graph_ok:
        print("="*60)
        print("ALL VERIFICATIONS PASSED!")
        print("="*60)
        print("\nNext steps:")
        print("  1. Logging configured and initialized")
        print("  2. Run: python test_graph.py")
        print("  3. Check logs in backend/logs/")
        print()
        return 0
    else:
        print("="*60)
        print("VERIFICATION FAILED")
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

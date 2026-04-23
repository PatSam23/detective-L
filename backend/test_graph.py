"""
Test script to run the research graph locally.

This script demonstrates how to use the research_app and run_research function.
"""

import sys
sys.path.insert(0, "/")

from app.core.graph import run_research


def test_research():
    """Test the research pipeline with a sample query."""
    
    query = "What are the latest trends in AI-powered drug discovery in 2026?"
    
    print("\n" + "="*70)
    print("RESEARCH GRAPH TEST")
    print("="*70)
    print(f"\nQuery: {query}\n")
    
    try:
        result = run_research(query, verbose=True)
        
        print("\n" + "="*70)
        print("FINAL REPORT SUMMARY")
        print("="*70)
        
        final_report = result.get("final_report", {})
        
        if final_report:
            print(f"\n📋 Title: {final_report.get('title', 'N/A')}")
            print(f"📊 Confidence Score: {final_report.get('confidence_score', 0):.2f}")
            print(f"📚 Number of Sections: {len(final_report.get('sections', []))}")
            print(f"🔗 Number of Sources: {len(final_report.get('sources', []))}")
            print(f"🔄 Revisions Made: {final_report.get('revision_count', 0)}")
            
            print(f"\n📝 Executive Summary:")
            print(f"{final_report.get('executive_summary', 'N/A')}")
            
            if final_report.get('sections'):
                print(f"\n📌 Sections:")
                for i, section in enumerate(final_report['sections'][:3], 1):
                    print(f"   {i}. {section.get('title', 'Untitled')}")
        
        print("\n" + "="*70 + "\n")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Error running research: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_research()
    sys.exit(0 if success else 1)

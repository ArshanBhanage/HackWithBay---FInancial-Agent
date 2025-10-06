#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""
import os, sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from dotenv import load_dotenv
        print("✅ dotenv imported successfully")
        
        from app.graph.build import build_doc_graph, build_data_graph
        print("✅ app.graph.build imported successfully")
        
        from app.agents.planner import Planner
        from app.agents.extractor import ADEExtractor
        from app.agents.compiler import PolicyCompiler
        from app.agents.validator import RuleValidator
        from app.agents.explainer import Explainer
        print("✅ All agent classes imported successfully")
        
        from app.models import ClauseFrame, PolicyRule, Violation, Evidence
        print("✅ All model classes imported successfully")
        
        from app.policy.dsl import rule_from_clause
        from app.policy.store import write_policy_bundle, load_rules
        print("✅ Policy DSL and store imported successfully")
        
        from app.tools.anthropic_client import ask_json
        from app.tools.ade_client import ade_extract
        print("✅ Tool clients imported successfully")
        
        print("\n🎉 All imports successful! The system is ready to use.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imports()

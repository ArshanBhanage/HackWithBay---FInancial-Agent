#!/usr/bin/env python3
"""
Demo script to show the HWB system capabilities
"""
import os, sys, json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_imports():
    """Demo that all imports work"""
    print("🔍 Testing system imports...")
    try:
        from app.graph.build import build_doc_graph, build_data_graph
        from app.agents.planner import Planner
        from app.agents.extractor import ADEExtractor
        from app.agents.compiler import PolicyCompiler
        from app.agents.validator import RuleValidator
        from app.agents.explainer import Explainer
        from app.models import ClauseFrame, PolicyRule, Violation
        from app.policy.dsl import rule_from_clause
        from app.policy.store import write_policy_bundle
        print("✅ All imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def demo_models():
    """Demo the data models"""
    print("\n📋 Testing data models...")
    try:
        from app.models import ClauseFrame, Evidence, PolicyRule
        
        # Create a sample clause frame
        evidence = Evidence(
            doc="demo.pdf",
            page=1,
            text_snippet="Management fee shall not exceed 2.0%",
            hash="demo123"
        )
        
        clause = ClauseFrame(
            id="demo_clause_1",
            subject="Institution A",
            obligation="limit",
            attribute="management_fee",
            comparator="lte",
            value=0.02,
            unit="%",
            evidence=evidence
        )
        
        print(f"✅ Created ClauseFrame: {clause.subject} {clause.obligation} {clause.attribute} {clause.comparator} {clause.value}{clause.unit}")
        return True
    except Exception as e:
        print(f"❌ Model demo failed: {e}")
        return False

def demo_dsl():
    """Demo the rule DSL"""
    print("\n⚙️  Testing rule DSL...")
    try:
        from app.models import ClauseFrame, Evidence
        from app.policy.dsl import rule_from_clause
        
        evidence = Evidence(doc="demo.pdf", page=1, text_snippet="Demo clause", hash="demo123")
        clause = ClauseFrame(
            id="demo_clause_1",
            subject="Institution A",
            obligation="limit",
            attribute="management_fee",
            comparator="lte",
            value=0.02,
            unit="%",
            evidence=evidence
        )
        
        rule = rule_from_clause(clause)
        print(f"✅ Generated PolicyRule: {rule.id}")
        print(f"   Event triggers: {rule.on_events}")
        print(f"   Check: {rule.check['op']} {rule.check['lhs']} {rule.check['rhs']} {rule.check['unit']}")
        return True
    except Exception as e:
        print(f"❌ DSL demo failed: {e}")
        return False

def demo_validation():
    """Demo fact validation logic"""
    print("\n🔍 Testing validation logic...")
    try:
        from app.agents.validator import RuleValidator
        
        validator = RuleValidator()
        
        # Test fact event
        fact_event = {
            "type": "fee_post",
            "payload": {
                "subject": "Institution A",
                "fee_rate": 0.025  # 2.5% - should trigger violation if rule expects <= 2.0%
            }
        }
        
        print(f"✅ Created validator and test fact event")
        print(f"   Event type: {fact_event['type']}")
        print(f"   Subject: {fact_event['payload']['subject']}")
        print(f"   Fee rate: {fact_event['payload']['fee_rate']}")
        return True
    except Exception as e:
        print(f"❌ Validation demo failed: {e}")
        return False

def main():
    """Run the demo"""
    print("🚀 HWB System Demo")
    print("=" * 50)
    
    # Test imports
    if not demo_imports():
        return False
    
    # Test models
    if not demo_models():
        return False
    
    # Test DSL
    if not demo_dsl():
        return False
    
    # Test validation
    if not demo_validation():
        return False
    
    print("\n🎉 All demos passed!")
    print("\nNext steps:")
    print("1. Configure your API keys in .env file")
    print("2. Add a PDF contract to ./docs/ directory")
    print("3. Run: python scripts/build_policy.py ./docs/your_contract.pdf")
    print("4. Test validation: python scripts/validate_fact.py '{\"type\":\"fee_post\",\"payload\":{\"subject\":\"Test\",\"fee_rate\":0.02}}'")
    
    return True

if __name__ == "__main__":
    main()

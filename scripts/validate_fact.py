import os, sys, json
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph.build import build_data_graph

if __name__ == "__main__":
    load_dotenv()
    
    if len(sys.argv) < 2:
        print("❌ Error: Please provide a JSON payload as an argument.")
        print("Example: python scripts/validate_fact.py '{\"type\":\"fee_post\",\"payload\":{\"subject\":\"Institution A\",\"fee_rate\":0.0200}}'")
        sys.exit(1)
    
    try:
        payload = json.loads(sys.argv[1])
        print(f"🔄 Validating fact: {payload.get('type', 'unknown')} for {payload.get('payload', {}).get('subject', 'unknown')}")
        
        graph = build_data_graph()
        out = graph.invoke({"data_event": payload})
        
        violations = out.get("violations", [])
        if violations:
            print(f"⚠️  Found {len(violations)} violation(s):")
            print(json.dumps(violations, indent=2))
        else:
            print("✅ No violations found")
        
        messages = out.get("messages", [])
        if messages:
            print("\n📝 Explanations:")
            for msg in messages:
                print(f"  • {msg}")
                
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON payload: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error validating fact: {e}")
        sys.exit(1)

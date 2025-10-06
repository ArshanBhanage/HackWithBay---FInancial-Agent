import os, sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph.build import build_doc_graph

if __name__ == "__main__":
    load_dotenv()
    doc = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getenv("DOCS_DIR","./docs"), "SideLetter_InstitutionA.pdf")
    
    if not os.path.exists(doc):
        print(f"❌ Error: Document not found: {doc}")
        print("Please provide a valid PDF file path as an argument.")
        print("Example: python scripts/build_policy.py ./docs/contract.pdf")
        sys.exit(1)
    
    print(f"🔄 Processing document: {doc}")
    try:
        print("🔄 Building graph...")
        graph = build_doc_graph()
        print("🔄 Invoking graph...")
        result = graph.invoke({"doc_path": doc})
        print("✅ Policy compiled successfully from:", doc)
        print("📁 Output files created in ./out/ directory")
        print("📊 Result keys:", list(result.keys()))
    except Exception as e:
        print(f"❌ Error processing document: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

import os, sys, json
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.planner import Planner
from app.agents.extractor import ADEExtractor

if __name__ == "__main__":
    load_dotenv()
    pdf = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getenv("DOCS_DIR","./docs"), "SideLetter_InstitutionA.pdf")

    planner = Planner()
    decision = planner.run(pdf)
    print("Planner decision:", decision.model_dump())

    extractor = ADEExtractor()
    result = extractor.run(pdf, decision)
    print("Frames extracted:", json.dumps([f.model_dump() for f in result.frames], indent=2))

import os, requests, json
from typing import Any, Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ADE_PARSE_URL = os.getenv("ADE_PARSE_URL", "https://api.va.landing.ai/v1/ade/parse")
ADE_EXTRACT_URL = os.getenv("ADE_EXTRACT_URL", "https://api.va.landing.ai/v1/ade/extract")
ADE_API_KEY = os.getenv("ADE_API_KEY", "")

def ade_extract(pdf_path: str, targets: List[str]) -> Dict[str, Any]:
    """
    Two-step process:
    1. Parse PDF to Markdown using /v1/ade/parse
    2. Extract fields from Markdown using /v1/ade/extract
    """
    if not ADE_API_KEY:
        raise RuntimeError("ADE_API_KEY is missing")

    # Step 1: Parse PDF to Markdown
    print(f"Step 1: Parsing PDF {pdf_path} to Markdown...")
    with open(pdf_path, "rb") as f:
        files = {"document": (os.path.basename(pdf_path), f, "application/pdf")}
        headers = {"Authorization": f"Bearer {ADE_API_KEY}"}
        
        parse_response = requests.post(ADE_PARSE_URL, files=files, headers=headers, timeout=90)
        parse_response.raise_for_status()
        parse_result = parse_response.json()
        
        markdown_content = parse_result.get("markdown", "")
        if not markdown_content:
            raise RuntimeError("Parse step returned empty markdown")
        
        print(f"✓ Parsed PDF to Markdown ({len(markdown_content)} characters)")

    # Step 2: Extract fields from Markdown
    print("Step 2: Extracting fields from Markdown...")
    
    # Create schema based on targets
    schema = {
        "type": "object",
        "properties": {
            target: {"type": "string", "description": f"Information about {target}"}
            for target in targets
        },
        "required": []
    }
    
    # Create schema.json file content
    schema_content = json.dumps(schema)
    
    # Use the parsed markdown as input
    # Schema should be in data, not files (based on 422 error)
    files = {
        "markdown": ("markdown.md", markdown_content, "text/markdown")
    }
    data = {"schema": schema_content}
    headers = {"Authorization": f"Bearer {ADE_API_KEY}"}
    
    extract_response = requests.post(ADE_EXTRACT_URL, files=files, data=data, headers=headers, timeout=90)
    extract_response.raise_for_status()
    extract_result = extract_response.json()
    
    print(f"✓ Extracted fields from Markdown")
    return extract_result

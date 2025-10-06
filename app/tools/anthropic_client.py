import os
from typing import Any, Dict
from anthropic import Anthropic

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def ask_json(system: str, user: str) -> Dict[str, Any]:
    """
    Call Claude with JSON-only output. Expects a single JSON object in response.
    """
    # Add JSON instruction to the user message since response_format isn't available in all versions
    user_with_json = user + "\n\nPlease respond with ONLY valid JSON, no other text."
    
    resp = _client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": user_with_json}],
        temperature=0
    )
    # Claude returns a list of content blocks; we expect a single text block with JSON
    response_text = resp.content[0].text
    
    # Try to parse as JSON
    import json
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from the response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            raise ValueError(f"Could not parse JSON from response: {response_text}")

import hashlib, os
from typing import List, Dict, Any
from pydantic import ValidationError
from app.agents.roles import ExtractorAgent, PlannerDecision
from app.models import ExtractResult, ClauseFrame, Evidence
# Use real ADE client
from app.tools.ade_client import ade_extract
from app.tools.anthropic_client import ask_json

NORMALIZE_SYSTEM = """You are a contract clause normalizer.
Input: a list of raw clause items (arbitrary keys).
Output: a JSON object with key 'frames' whose value is an array of ClauseFrame-compatible items:
{
  "id": "string-unique",
  "subject": "who/what it applies to",
  "obligation": "verb-like summary (pay/report/prohibit/maintain/notify/limit/etc.)",
  "attribute": "specific attribute if applicable (management_fee, sector, ltv_ratio, interest_rate, covenant, etc.)",
  "comparator": "eq|lte|gte|lt|gt|in|not_in|contains|absent|neq|between",
  "value": "...",        // number|string|list|dict as appropriate
  "unit": "optional unit like %, days, USD, SIC, NAICS, bps",
  "conditions": ["optional strings"],
  "effective_start": "ISO date or null",
  "effective_end": "ISO date or null",
  "confidence": 0..1,
  "evidence": {
     "doc": "filename.pdf",
     "page": 1,
     "bbox": [x1,y1,x2,y2] or null,
     "text_snippet": "short quote",
     "hash": "content-or-span-hash"
  },
  "raw": { "original_item": "include the ADE item minimally" }
}
Rules:
- Fill missing comparator/unit sensibly; prefer eq/lte/gte for numeric, in/not_in for sets.
- subject must be explicit (e.g., 'Institution A', 'Borrower', 'All Investors').
- If page/bbox not present, set them null but keep text_snippet when available.
- IDs must be stable per clause text (e.g., short hash).
Return ONLY JSON.
"""

def _sha(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:10]

def _map_ade_to_minimal_items(ade_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert ADE response to minimal items for normalization.
    ADE returns: {"extraction": {...}, "extraction_metadata": {...}}
    """
    items = []
    extraction = ade_json.get("extraction", {})
    metadata = ade_json.get("extraction_metadata", {})
    
    # Convert extraction fields to items
    for key, value in extraction.items():
        if value and value != "":  # Skip empty values
            item = {
                "key": key,
                "value": value,
                "type": key,
                "confidence": 0.8,  # Default confidence
                "raw": {"original_item": {key: value}}
            }
            
            # Add metadata if available
            if key in metadata and isinstance(metadata[key], dict):
                meta = metadata[key]
                if "value" in meta:
                    item["value"] = meta["value"]
                if "references" in meta:
                    item["references"] = meta["references"]
            
            items.append(item)
    
    # Debug: Log if no items extracted
    if not items:
        print("DEBUG: ADE API returned no extraction data.")
        print(f"ADE response extraction keys: {list(extraction.keys())}")
        print(f"ADE response extraction values: {list(extraction.values())}")
    
    return items

class ADEExtractor(ExtractorAgent):
    def run(self, doc_path: str, decision: PlannerDecision) -> ExtractResult:
        # 1) Call ADE with the planner's targets
        ade_json = ade_extract(doc_path, decision.targets)

        # 2) Convert to a normalizable, minimal list of items
        items = _map_ade_to_minimal_items(ade_json)

        # 3) Ask Claude to normalize to ClauseFrame[]
        doc_name = os.path.basename(doc_path)
        norm_input = {
            "doc": doc_name,
            "items": items
        }
        normalized = ask_json(
            NORMALIZE_SYSTEM,
            f"Document: {doc_name}\nItems:\n{norm_input}"
        )

        # 4) Validate with Pydantic; attach hashes if missing
        frames: List[ClauseFrame] = []
        for raw in normalized.get("frames", []):
            # ensure id and evidence.hash exist
            if not raw.get("id"):
                raw["id"] = _sha(str(raw))
            ev = raw.get("evidence") or {}
            if not ev.get("doc"): ev["doc"] = doc_name
            if not ev.get("hash"):
                ev["hash"] = _sha((ev.get("text_snippet") or "") + f"@{ev.get('page')}")
            raw["evidence"] = ev
            try:
                frames.append(ClauseFrame(**raw))
            except ValidationError as e:
                # you may log and skip bad frames
                continue

        # 5) Return ExtractResult
        doc_hash = _sha(doc_name)
        return ExtractResult(doc=doc_name, doc_hash=doc_hash, frames=frames)

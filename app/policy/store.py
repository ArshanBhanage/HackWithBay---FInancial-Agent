from __future__ import annotations
import os, json, time, yaml
from typing import Dict, List, Tuple
from app.models import PolicyRule

OUT_DIR = os.getenv("OUT_DIR", "./out")
POLICY_YAML = os.path.join(OUT_DIR, "policy.yaml")
RULES_INDEX = os.path.join(OUT_DIR, "rules_index.json")

def _ensure_out():
    os.makedirs(OUT_DIR, exist_ok=True)

def write_policy_bundle(rules: List[PolicyRule]) -> None:
    _ensure_out()
    bundle = {
        "policy_id": f"policy_{int(time.time())}",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rules": [r.model_dump() for r in rules],
    }
    with open(POLICY_YAML, "w") as f:
        yaml.safe_dump(bundle, f, sort_keys=False)

    index = build_index(rules)
    with open(RULES_INDEX, "w") as f:
        json.dump(index, f)

def load_rules() -> List[PolicyRule]:
    if not os.path.exists(POLICY_YAML):
        return []
    with open(POLICY_YAML) as f:
        data = yaml.safe_load(f) or {}
    return [PolicyRule(**r) for r in data.get("rules", [])]

def build_index(rules: List[PolicyRule]) -> Dict[str, Dict[str, List[dict]]]:
    # index[event_type][subject] = [rule, ...]
    idx: Dict[str, Dict[str, List[dict]]] = {}
    for r in rules:
        subs = r.selector.get("subject.eq")
        for ev in r.on_events:
            idx.setdefault(ev, {}).setdefault(subs, []).append(r.model_dump())
    return idx

def get_rules_for(event_type: str, subject: str) -> List[PolicyRule]:
    rules = load_rules()
    out: List[PolicyRule] = []
    for r in rules:
        if event_type in r.on_events and r.selector.get("subject.eq") == subject:
            out.append(r)
    return out

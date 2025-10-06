from __future__ import annotations
import uuid, time
from typing import Any, Dict, List
from app.agents.roles import ValidatorAgent
from app.models import PolicyRule, Violation, Evidence, FactEvent
from app.policy.store import get_rules_for

def _json_get(payload: Dict[str, Any], jsonpath: str) -> Any:
    # very small: only supports "$.<key>"
    if not jsonpath.startswith("$."):
        return None
    key = jsonpath[2:]
    return payload.get(key)

def _as_number(v: Any, unit: str|None) -> float|None:
    try:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            s = v.strip()
            if unit == "%" or s.endswith("%"):
                s = s.replace("%", "")
                return float(s)/100.0
            return float(s)
    except Exception:
        return None
    return None

def _compare(op: str, lhs: Any, rhs: Any) -> bool:
    op = (op or "eq").lower()
    
    # Handle None values
    if lhs is None or rhs is None:
        if op in ("eq", "=="):
            return lhs == rhs
        elif op in ("neq", "!="):
            return lhs != rhs
        else:
            return False  # Most operations with None values are False
    
    if op == "eq":
        return lhs == rhs
    if op == "neq":
        return lhs != rhs
    if op in ("lte","le"):
        return lhs <= rhs
    if op in ("gte","ge"):
        return lhs >= rhs
    if op == "lt":
        return lhs < rhs
    if op == "gt":
        return lhs > rhs
    if op == "in":
        return lhs in (rhs or [])
    if op == "not_in":
        return lhs not in (rhs or [])
    if op == "contains":
        if isinstance(lhs, (list, tuple)):
            return rhs in lhs
        if isinstance(lhs, str) and isinstance(rhs, str):
            return rhs.lower() in lhs.lower()
        return False
    if op == "prohibits":
        # violation when lhs is in rhs
        return not (lhs in (rhs or []))
    if op == "requires":
        # rhs truthy required
        return bool(lhs)
    # default to eq
    return lhs == rhs

class RuleValidator(ValidatorAgent):
    def run(self, rule_index: Any, fact_event: Dict[str, Any]) -> List[Dict[str, Any]]:
        ev = FactEvent(**fact_event)
        subject = ev.payload.get("subject") or ev.payload.get("investor") or "UNKNOWN"
        rules: List[PolicyRule] = get_rules_for(ev.type, subject)

        violations: List[Dict[str, Any]] = []
        for r in rules:
            lhs_val = _json_get(ev.payload, r.check.get("lhs","$.value"))
            rhs_val = r.check.get("rhs")
            unit = r.check.get("unit")

            # numeric normalization (e.g., 1.75% vs 0.0175)
            lnum = _as_number(lhs_val, unit)
            rnum = _as_number(rhs_val, unit)
            if lnum is not None and rnum is not None:
                ok = _compare(r.check["op"], lnum, rnum)
            else:
                ok = _compare(r.check["op"], lhs_val, rhs_val)

            if not ok:
                v = Violation(
                    id=f"V-{uuid.uuid4().hex[:8]}",
                    rule_id=r.id,
                    event_type=ev.type,
                    subject=subject,
                    expected={"op": r.check["op"], "lhs": r.check["lhs"], "rhs": rhs_val, "unit": unit},
                    actual=ev.payload,
                    severity=r.severity,
                    evidence=Evidence(**r.evidence.model_dump()),
                    detected_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
                violations.append(v.model_dump())
        return violations

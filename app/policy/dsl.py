from __future__ import annotations
from typing import Any, Dict, List
from app.models import ClauseFrame, PolicyRule, Evidence

# --- Rule DSL ---
# check := {
#   "op": "eq" | "lte" | "gte" | "in" | "not_in" | "prohibits" | "requires" | "expr",
#   "lhs": "payload.jsonpath or symbolic key" (e.g., "$.fee_rate", "$.report_delay_days", "$.sector"),
#   "rhs": Any,           # 0.0175, 5, ["SIC:7372"], etc.
#   "unit": str|None,     # "%","days","SIC",...
# }
#
# selector := {"subject.eq": "Institution A"}  # minimal, can be extended

_PRIO_ATTRS = ("fee", "rate", "report", "deadline", "sector", "prohibit", "ltv", "collateral", "notice")

def _guess_event(cf: ClauseFrame) -> List[str]:
    # best-effort mapping, still schema-agnostic
    ob = (cf.obligation or "").lower()
    attr = (cf.attribute or "").lower()
    if "fee" in attr or "fee" in ob:
        return ["fee_post"]
    if "report" in ob or "deadline" in attr:
        return ["report_delivered"]
    if "prohibit" in ob or "sector" in attr or "allocation" in attr:
        return ["trade_allocated"]
    if "notify" in ob or "notice" in attr:
        return ["sideletter_ingested", "amendment_ingested"]
    # fallback generic
    return ["data_event"]

def rule_from_clause(cf: ClauseFrame) -> PolicyRule:
    # LHS jsonpath is inferred from attribute; generic fallback is a direct key on payload
    attr = (cf.attribute or cf.obligation or "value").lower()
    # normalize common keys
    if "fee" in attr:
        lhs = "$.fee_rate"        # your ETL should map decimal(0.0175) here
    elif "report" in attr or "deadline" in attr:
        lhs = "$.report_delay_days"
    elif "sector" in attr or "allocation" in attr:
        lhs = "$.sector"
    elif "ltv" in attr:
        lhs = "$.ltv_ratio"
    elif "notice" in attr:
        lhs = "$.notice_sent"
    else:
        lhs = f"$.{attr.replace(' ', '_')}"

    op = (cf.comparator or "expr").lower()
    check = {
        "op": op,
        "lhs": lhs,
        "rhs": cf.value,
        "unit": cf.unit,
    }

    selector = {"subject.eq": cf.subject}
    on_events = _guess_event(cf)

    return PolicyRule(
        id=f"R-{cf.id}",
        selector=selector,
        check=check,
        on_events=on_events,
        severity=("HIGH" if any(k in (cf.attribute or "").lower() for k in _PRIO_ATTRS) else "MEDIUM"),
        evidence=cf.evidence,
        comments=f"Derived from clause: {cf.obligation} {cf.attribute or ''} {cf.comparator or ''} {cf.value} {cf.unit or ''}".strip(),
    )

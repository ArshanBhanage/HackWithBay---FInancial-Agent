from __future__ import annotations
from typing import List
from app.agents.roles import CompilerAgent
from app.models import ClauseFrame, PolicyRule
from app.policy.dsl import rule_from_clause
from app.policy.store import write_policy_bundle

class PolicyCompiler(CompilerAgent):
    def run(self, frames: List[ClauseFrame]) -> List[PolicyRule]:
        rules = [rule_from_clause(cf) for cf in frames]
        write_policy_bundle(rules)  # persists YAML + index
        return rules

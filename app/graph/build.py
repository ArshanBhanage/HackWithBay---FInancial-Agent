from __future__ import annotations
import os, json
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

from app.models import ExtractResult, ClauseFrame
from app.agents.planner import Planner
from app.agents.extractor import ADEExtractor
from app.agents.compiler import PolicyCompiler
from app.agents.validator import RuleValidator
from app.agents.explainer import Explainer

OUT_DIR = os.getenv("OUT_DIR","./out")
VIOS_PATH = os.path.join(OUT_DIR, "violations.jsonl")

class GState(TypedDict, total=False):
    doc_path: Optional[str]
    data_event: Optional[Dict[str, Any]]
    decision: Optional[Dict[str, Any]]
    extracted: Optional[Dict[str, Any]]
    rules_written: Optional[bool]
    violations: Optional[List[Dict[str, Any]]]
    messages: Optional[List[str]]

planner = Planner()
extractor = ADEExtractor()
compiler = PolicyCompiler()
validator = RuleValidator()
explainer = Explainer()

def node_plan(state: GState) -> GState:
    dec = planner.run(state["doc_path"])
    return {"decision": dec.model_dump()}

def node_extract(state: GState) -> GState:
    dec = state["decision"]
    res: ExtractResult = extractor.run(state["doc_path"], type("obj",(object,),dec))
    return {"extracted": {"doc": res.doc, "frames": [f.model_dump() for f in res.frames]}}

def node_compile(state: GState) -> GState:
    frames = [ClauseFrame(**f) for f in state["extracted"]["frames"]]
    rules = compiler.run(frames)
    return {"rules_written": True}

def node_validate(state: GState) -> GState:
    vios = validator.run(None, state["data_event"])  # store reads rules from disk
    return {"violations": vios}

def node_explain_emit(state: GState) -> GState:
    msgs = []
    if state.get("violations"):
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(VIOS_PATH, "a") as f:
            for v in state["violations"]:
                msg = explainer.run(v)
                v["summary"] = msg
                f.write(json.dumps(v) + "\n")
                msgs.append(msg)
    return {"messages": msgs}

def build_doc_graph():
    g = StateGraph(GState)
    g.add_node("plan", node_plan)
    g.add_node("extract", node_extract)
    g.add_node("compile", node_compile)
    g.set_entry_point("plan")
    g.add_edge("plan", "extract")
    g.add_edge("extract", "compile")
    g.add_edge("compile", END)
    return g.compile()

def build_data_graph():
    g = StateGraph(GState)
    g.add_node("validate", node_validate)
    g.add_node("explain_emit", node_explain_emit)
    g.set_entry_point("validate")
    g.add_edge("validate", "explain_emit")
    g.add_edge("explain_emit", END)
    return g.compile()

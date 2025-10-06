import os
import json
import asyncio
import yaml
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from app.graph.build import build_doc_graph, build_data_graph

DOCS_DIR = os.getenv("DOCS_DIR", "./docs")
OUT_DIR = os.getenv("OUT_DIR", "./out")
VIOS_PATH = os.path.join(OUT_DIR, "violations.jsonl")
POLICY_YAML = os.path.join(OUT_DIR, "policy.yaml")
STATE_PATH = os.path.join(OUT_DIR, "violations_state.json")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

class IngestRequest(BaseModel):
    path: Optional[str] = None

app = FastAPI(title="O2A Agent — API")

# CORS for local dev (React on another port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static mounts will be added at the end after all API endpoints

# ---- STATUS STORAGE HELPERS ----

def _load_state():
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def _save_state(state: dict):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f)

@app.get("/health")
def health():
    return {"ok": True}

# ---- POLICY ENDPOINTS ----

@app.get("/policy")
def get_policy(format: str = "json"):
    if not os.path.exists(POLICY_YAML):
        return {} if format == "json" else PlainTextResponse("", media_type="text/plain")
    if format == "yaml":
        with open(POLICY_YAML, "r") as f:
            return PlainTextResponse(f.read(), media_type="text/plain")
    with open(POLICY_YAML, "r") as f:
        return yaml.safe_load(f) or {}

# ---- DOC INGEST (compile rules) ----

@app.post("/api/ingest")
def ingest_doc(request: Optional[IngestRequest] = None, file: Optional[UploadFile] = None):
    """
    Option A: JSON body with {"path": "./docs/YourDoc.pdf"}
    Option B: multipart upload 'file' (saves to DOCS_DIR)
    """
    if file is not None:
        os.makedirs(DOCS_DIR, exist_ok=True)
        dest = os.path.join(DOCS_DIR, file.filename)
        with open(dest, "wb") as f:
            f.write(file.file.read())
        pdf_path = dest
    elif request and request.path:
        pdf_path = request.path
    else:
        raise HTTPException(status_code=400, detail="Provide 'path' or upload 'file'.")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"File not found: {pdf_path}")

    graph = build_doc_graph()
    graph.invoke({"doc_path": pdf_path})
    return {"status": "compiled", "doc": os.path.basename(pdf_path)}

# ---- FACT VALIDATION (sync) ----

@app.post("/facts")
def post_fact(event: Dict[str, Any]):
    """
    Body: { "type": "fee_post", "payload": { "subject": "Institution A", "fee_rate": 0.0200 } }
    Returns: { violations: [...], messages: [...] }
    (Also appends to violations.jsonl and streams via /violations/stream)
    """
    required = ("type", "payload")
    if not all(k in event for k in required):
        raise HTTPException(status_code=400, detail=f"Event must include {required}")

    graph = build_data_graph()
    out = graph.invoke({"data_event": event})
    return {
        "violations": out.get("violations", []),
        "messages": out.get("messages", []),
    }

# ---- SNAPSHOT (pull) ----

@app.get("/violations")
def list_violations(limit: int = 200):
    rows = []
    if os.path.exists(VIOS_PATH):
        with open(VIOS_PATH, "r") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    state = _load_state()
    for v in rows:
        v["status"] = state.get(v.get("id"), "OPEN")
    return rows[-limit:]

# ---- VIOLATION STATUS MANAGEMENT ----

@app.post("/violations/{vid}/status")
def set_violation_status(vid: str, body: dict = Body(...)):
    status = (body or {}).get("status")
    if status not in ("OPEN", "ACK", "RESOLVED"):
        raise HTTPException(status_code=400, detail="status must be OPEN|ACK|RESOLVED")
    state = _load_state()
    state[vid] = status
    _save_state(state)
    return {"ok": True, "id": vid, "status": status}

# ---- SSE STREAM (push) ----

@app.get("/violations/stream")
async def stream_violations(tail: bool = True):
    """
    Server-Sent Events: emits each new JSONL line as an SSE 'violation' event.
    Query: tail=true -> start at EOF; tail=false -> replay from beginning.
    """
    async def event_gen():
        last_pos = 0
        while True:
            if os.path.exists(VIOS_PATH):
                size = os.path.getsize(VIOS_PATH)
                if last_pos == 0:
                    last_pos = size if tail else 0
                if size > last_pos:
                    with open(VIOS_PATH, "r") as f:
                        f.seek(last_pos)
                        for line in f:
                            yield {"event": "violation", "data": line.strip()}
                    last_pos = size
            await asyncio.sleep(1.0)
    return EventSourceResponse(event_gen())

# ---- STATIC FILE SERVING (must be after all API endpoints) ----

# serve PDFs so the viewer can open /docs/<file>#page=<n>
app.mount("/docs", StaticFiles(directory=DOCS_DIR), name="docs")
# serve the one-file UI at /app
app.mount("/app", StaticFiles(directory="ui", html=True), name="app")

#!/usr/bin/env python3
"""
Demo script showing the HWB FastAPI server capabilities
"""
import os, sys
import json
import requests
import subprocess
import time
import threading

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_step(step_num, title):
    """Print a formatted step"""
    print(f"\n📋 Step {step_num}: {title}")
    print("-" * 40)

def demo_server_components():
    """Demo the server components without running the server"""
    print_header("HWB FastAPI Server Components Demo")
    
    print_step(1, "Server Architecture")
    print("""
    🏗️  FastAPI Server Structure:
    
    📡 Endpoints:
      • GET  /health                    - Health check
      • POST /docs/ingest               - Document ingestion (JSON path or file upload)
      • POST /facts                     - Fact validation
      • GET  /violations                - Violations snapshot
      • GET  /violations/stream         - SSE stream for real-time violations
    
    🔧 Features:
      • CORS enabled for local development
      • File upload support for PDF documents
      • Real-time SSE streaming of violations
      • JSONL persistence of violation log
      • Integration with existing HWB pipeline
    """)
    
    print_step(2, "API Endpoint Examples")
    print("""
    📄 Document Ingestion:
      curl -X POST http://localhost:7000/docs/ingest \\
        -H "Content-Type: application/json" \\
        -d '{"path":"./docs/SideLetter_InstitutionA.pdf"}'
    
    🧪 Fact Validation:
      curl -X POST http://localhost:7000/facts \\
        -H "Content-Type: application/json" \\
        -d '{"type":"fee_post","payload":{"subject":"Institution A","fee_rate":0.0200}}'
    
    📊 Violations Snapshot:
      curl http://localhost:7000/violations?limit=5
    
    📡 SSE Stream (real-time):
      curl -N http://localhost:7000/violations/stream
    """)
    
    print_step(3, "Server Integration Points")
    print("""
    🔗 Integration with HWB Pipeline:
    
    1. Document Ingestion → build_doc_graph()
       • PDF → Planner → Extractor → Compiler → Policy Rules
       • Rules saved to policy.yaml and rules_index.json
    
    2. Fact Validation → build_data_graph()
       • Fact Event → Validator → Violations → Explainer
       • Violations appended to violations.jsonl
       • SSE stream emits new violations in real-time
    
    3. Real-time Monitoring:
       • React dashboard can connect to SSE stream
       • WebSocket-like experience for violation updates
       • Persistent violation log for historical analysis
    """)
    
    print_step(4, "Production Deployment")
    print("""
    🚀 Production Ready Features:
    
    ✅ FastAPI with automatic OpenAPI docs
    ✅ CORS middleware for web frontend
    ✅ File upload handling for document ingestion
    ✅ Server-Sent Events for real-time streaming
    ✅ JSONL persistence for violation logging
    ✅ Error handling and HTTP status codes
    ✅ Environment variable configuration
    
    🔧 Next Steps for Production:
      • Add authentication/authorization
      • Implement rate limiting
      • Add request logging and metrics
      • Set up health checks and monitoring
      • Deploy with Docker/Kubernetes
      • Add database persistence (PostgreSQL/MongoDB)
      • Implement caching layer (Redis)
    """)

def demo_api_usage():
    """Show how to use the API programmatically"""
    print_step(5, "Programmatic API Usage")
    
    print("""
    🐍 Python Client Example:
    
    import requests
    import json
    
    BASE_URL = "http://localhost:7000"
    
    # 1. Ingest a document
    response = requests.post(f"{BASE_URL}/docs/ingest", 
                           json={"path": "./docs/contract.pdf"})
    print(response.json())  # {"status": "compiled", "doc": "contract.pdf"}
    
    # 2. Validate a fact
    fact = {"type": "fee_post", "payload": {"subject": "Institution A", "fee_rate": 0.02}}
    response = requests.post(f"{BASE_URL}/facts", json=fact)
    result = response.json()
    print(f"Violations: {result['violations']}")
    print(f"Messages: {result['messages']}")
    
    # 3. Get violation history
    response = requests.get(f"{BASE_URL}/violations?limit=10")
    violations = response.json()
    for v in violations:
        print(f"Rule: {v['rule_id']}, Subject: {v['subject']}")
    
    # 4. Stream violations (SSE)
    import sseclient
    
    response = requests.get(f"{BASE_URL}/violations/stream", stream=True)
    client = sseclient.SSEClient(response)
    
    for event in client.events():
        if event.event == 'violation':
            violation = json.loads(event.data)
            print(f"New violation: {violation['rule_id']}")
    """)

def demo_react_integration():
    """Show how to integrate with React frontend"""
    print_step(6, "React Frontend Integration")
    
    print("""
    ⚛️  React Component Example:
    
    import { useState, useEffect } from 'react';
    import { useEventSource } from 'react-use';
    
    function ViolationMonitor() {
      const [violations, setViolations] = useState([]);
      
      // Connect to SSE stream
      const { lastEvent, readyState } = useEventSource(
        'http://localhost:7000/violations/stream'
      );
      
      // Handle new violations
      useEffect(() => {
        if (lastEvent && lastEvent.event === 'violation') {
          const violation = JSON.parse(lastEvent.data);
          setViolations(prev => [violation, ...prev.slice(0, 99)]);
        }
      }, [lastEvent]);
      
      // Submit fact for validation
      const validateFact = async (fact) => {
        const response = await fetch('/facts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(fact)
        });
        return response.json();
      };
      
      // Upload document
      const uploadDocument = async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/docs/ingest', {
          method: 'POST',
          body: formData
        });
        return response.json();
      };
      
      return (
        <div>
          <h2>Contract Violations</h2>
          {violations.map(v => (
            <div key={v.id} className="violation">
              <h3>{v.rule_id}</h3>
              <p>{v.summary}</p>
              <small>Subject: {v.subject}</small>
            </div>
          ))}
        </div>
      );
    }
    """)

def main():
    """Run the complete API demo"""
    demo_server_components()
    demo_api_usage()
    demo_react_integration()
    
    print_header("API Demo Complete! 🎉")
    print("""
    🚀 The HWB FastAPI server is ready for production use!
    
    To start the server:
      python run_server.py
    
    To test the API:
      python test_api.py
    
    To view API documentation:
      http://localhost:7000/docs
    
    The server provides:
    ✅ Document ingestion and policy compilation
    ✅ Real-time fact validation
    ✅ SSE streaming of violations
    ✅ RESTful API for all operations
    ✅ Production-ready FastAPI framework
    """)

if __name__ == "__main__":
    main()

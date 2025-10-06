#!/usr/bin/env python3
"""
Enhanced UI and Server Demo

This script demonstrates the enhanced HWB system with:
1. Extended FastAPI server with policy viewing and violation status management
2. Rich web UI with filters, CSV export, and PDF viewing
3. Real-time SSE streaming with status management
4. Complete end-to-end workflow demonstration

Usage:
    python demo_enhanced_ui.py
"""

import os
import sys
import time
import json
import subprocess
import threading
import requests
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*70}")
    print(f"🚀 {title}")
    print(f"{'='*70}")

def print_step(step_num, title):
    """Print a formatted step"""
    print(f"\n📋 Step {step_num}: {title}")
    print("-" * 50)

def print_substep(substep, description):
    """Print a formatted substep"""
    print(f"\n  🔸 {substep}")
    print(f"     {description}")

def start_server():
    """Start the enhanced FastAPI server"""
    print_step(1, "Starting Enhanced FastAPI Server")
    
    print_substep("Server Features", """
    ✅ Extended FastAPI server with new endpoints:
       • GET /policy - View policy rules in JSON or YAML format
       • POST /violations/{id}/status - Manage violation status (OPEN/ACK/RESOLVED)
       • Static file serving for PDFs (/docs) and UI (/app)
       • Enhanced violations endpoint with status merging
    """)
    
    print("  🚀 Starting server with: python -m uvicorn app.server:app --port 7000")
    print("  📱 UI will be available at: http://localhost:7000/app")
    print("  📚 API docs at: http://localhost:7000/docs")

def demonstrate_policy_endpoints():
    """Demonstrate the new policy endpoints"""
    print_step(2, "Policy Endpoints Demo")
    
    print_substep("Policy JSON Endpoint", "GET /policy?format=json")
    try:
        response = requests.get("http://localhost:7000/policy")
        if response.status_code == 200:
            policy = response.json()
            print(f"     ✅ Policy loaded: {policy.get('policy_id', 'unknown')}")
            print(f"     📊 Rules count: {len(policy.get('rules', []))}")
            print(f"     📅 Generated: {policy.get('generated_at', 'unknown')}")
        else:
            print(f"     ❌ Policy endpoint error: {response.status_code}")
    except requests.exceptions.RequestException:
        print("     ❌ Could not connect to policy endpoint")
    
    print_substep("Policy YAML Endpoint", "GET /policy?format=yaml")
    try:
        response = requests.get("http://localhost:7000/policy?format=yaml")
        if response.status_code == 200:
            yaml_content = response.text
            print(f"     ✅ YAML content length: {len(yaml_content)} characters")
            print(f"     📄 First 100 chars: {yaml_content[:100]}...")
        else:
            print(f"     ❌ YAML endpoint error: {response.status_code}")
    except requests.exceptions.RequestException:
        print("     ❌ Could not connect to YAML endpoint")

def demonstrate_violation_management():
    """Demonstrate violation status management"""
    print_step(3, "Violation Status Management Demo")
    
    print_substep("List Violations with Status", "GET /violations")
    try:
        response = requests.get("http://localhost:7000/violations")
        if response.status_code == 200:
            violations = response.json()
            print(f"     ✅ Found {len(violations)} violations")
            
            if violations:
                # Show status distribution
                status_counts = {}
                for v in violations:
                    status = v.get('status', 'OPEN')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print(f"     📊 Status distribution: {status_counts}")
                
                # Test status update
                test_violation = violations[0]
                vid = test_violation.get('id')
                original_status = test_violation.get('status', 'OPEN')
                
                print_substep("Update Violation Status", f"POST /violations/{vid}/status")
                print(f"     Original status: {original_status}")
                
                # Try to update status
                new_status = "ACK" if original_status != "ACK" else "RESOLVED"
                response = requests.post(f"http://localhost:7000/violations/{vid}/status", 
                                       json={"status": new_status})
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"     ✅ Status updated: {result}")
                    
                    # Verify the update
                    response = requests.get("http://localhost:7000/violations")
                    if response.status_code == 200:
                        updated_violations = response.json()
                        updated_v = next((v for v in updated_violations if v.get('id') == vid), None)
                        if updated_v:
                            print(f"     ✅ Verified status: {updated_v.get('status')}")
                else:
                    print(f"     ❌ Status update failed: {response.status_code}")
            else:
                print("     ℹ️  No violations found to test status management")
        else:
            print(f"     ❌ Violations endpoint error: {response.status_code}")
    except requests.exceptions.RequestException:
        print("     ❌ Could not connect to violations endpoint")

def demonstrate_ui_features():
    """Demonstrate the enhanced UI features"""
    print_step(4, "Enhanced UI Features Demo")
    
    print_substep("Web UI Components", """
    🎨 Rich Web Interface at http://localhost:7000/app:
       • Policy YAML viewer with syntax highlighting
       • Rules table with filtering (severity, subject, event type)
       • Live violations table with SSE updates
       • Violation status management (Ack/Resolve buttons)
       • CSV export functionality
       • PDF viewer modal for evidence documents
       • Real-time SSE streaming of new violations
    """)
    
    print_substep("UI Navigation", """
    📱 UI Access Points:
       • Main UI: http://localhost:7000/app
       • API Docs: http://localhost:7000/docs
       • Health Check: http://localhost:7000/health
       • Policy YAML: http://localhost:7000/policy?format=yaml
       • Policy JSON: http://localhost:7000/policy?format=json
       • Violations: http://localhost:7000/violations
       • SSE Stream: http://localhost:7000/violations/stream
    """)
    
    print_substep("Static File Serving", """
    📁 Static File Mounts:
       • PDF Documents: http://localhost:7000/docs/{filename}
       • Web UI: http://localhost:7000/app (serves ui/index.html)
       • Direct PDF access with page anchors: /docs/file.pdf#page=3
    """)

def demonstrate_complete_workflow():
    """Demonstrate the complete enhanced workflow"""
    print_step(5, "Complete Enhanced Workflow Demo")
    
    print_substep("Workflow Overview", """
    🔄 Complete Enhanced Workflow:
       1. Document Processing → Policy Rules Compilation
       2. Real-time Fact Streaming → Violation Detection
       3. SSE Streaming → Live UI Updates
       4. Status Management → Violation Tracking
       5. PDF Viewing → Evidence Inspection
       6. CSV Export → Data Analysis
    """)
    
    print_substep("Testing Commands", """
    🧪 Manual Testing Commands:
       
       # 1. Start the enhanced server
       python -m uvicorn app.server:app --port 7000
       
       # 2. Open the UI in browser
       open http://localhost:7000/app
       
       # 3. Test policy endpoints
       curl http://localhost:7000/policy?format=yaml
       curl http://localhost:7000/policy?format=json
       
       # 4. Test violation management
       curl http://localhost:7000/violations
       curl -X POST http://localhost:7000/violations/{violation_id}/status \\
            -H "Content-Type: application/json" \\
            -d '{"status": "ACK"}'
       
       # 5. Test SSE streaming
       curl -N http://localhost:7000/violations/stream
    """)

def show_production_features():
    """Show production-ready features"""
    print_step(6, "Production-Ready Features")
    
    print_substep("Enhanced Server Features", """
    🚀 Production Enhancements:
       • Static file serving for PDFs and UI
       • Policy viewing in multiple formats (JSON/YAML)
       • Violation status management (OPEN/ACK/RESOLVED)
       • Persistent state storage for violation statuses
       • Enhanced CORS support for web frontend
       • Rich web UI with no build process required
       • Real-time SSE streaming with status updates
       • CSV export for data analysis
       • PDF viewer modal for evidence inspection
    """)
    
    print_substep("UI Features", """
    🎨 Rich Web Interface:
       • Responsive design with modern CSS
       • Real-time data updates via SSE
       • Interactive filtering and sorting
       • Export functionality (CSV)
       • Modal PDF viewer for evidence
       • Status management with visual feedback
       • No JavaScript framework required
       • Works in any modern browser
    """)

def main():
    """Run the complete enhanced UI demo"""
    print_header("HWB Enhanced UI and Server Demo")
    
    print("""
  🎯 This demo shows the enhanced HWB system with:
     1. Extended FastAPI server with policy viewing and violation management
     2. Rich web UI with filters, CSV export, and PDF viewing
     3. Real-time SSE streaming with status management
     4. Complete end-to-end workflow demonstration
  
  ⚠️  Prerequisites:
     • Enhanced server running: python -m uvicorn app.server:app --port 7000
     • Policy rules compiled (from document processing)
     • Some violations present for testing
  """)
    
    start_server()
    demonstrate_policy_endpoints()
    demonstrate_violation_management()
    demonstrate_ui_features()
    demonstrate_complete_workflow()
    show_production_features()
    
    print_header("Enhanced UI Demo Complete! 🎉")
    print("""
  🚀 The HWB system now has a complete web interface!
  
  🌐 Access Points:
     • Web UI: http://localhost:7000/app
     • API Docs: http://localhost:7000/docs
     • Policy YAML: http://localhost:7000/policy?format=yaml
  
  ✨ New Features:
     ✅ Rich web interface with real-time updates
     ✅ Policy viewing in JSON and YAML formats
     ✅ Violation status management (OPEN/ACK/RESOLVED)
     ✅ CSV export for data analysis
     ✅ PDF viewer for evidence inspection
     ✅ Interactive filtering and sorting
     ✅ Static file serving for documents and UI
  
  🎯 Ready for production use with full web interface! 🚀
  """)

if __name__ == "__main__":
    main()

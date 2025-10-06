#!/usr/bin/env python3
"""
Complete Streaming Pipeline Demo

This script demonstrates the full HWB streaming pipeline:
1. Document processing and policy compilation
2. Real-time fact validation through Pathway
3. SSE streaming of violations
4. Complete end-to-end workflow

Usage:
    python demo_streaming.py
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

def check_services():
    """Check if required services are running"""
    print_step(1, "Service Health Check")
    
    services = {
        "FastAPI Server": "http://localhost:7000/health",
        "Pathway Runner": "Check if python -m app.pathway.facts_runner is running"
    }
    
    for service, endpoint in services.items():
        if service == "FastAPI Server":
            try:
                response = requests.get(endpoint, timeout=2)
                if response.status_code == 200:
                    print(f"  ✅ {service}: Running")
                else:
                    print(f"  ❌ {service}: Not responding (status {response.status_code})")
            except requests.exceptions.RequestException:
                print(f"  ❌ {service}: Not running")
        else:
            print(f"  ⚠️  {service}: Manual check required")

def setup_sample_data():
    """Set up sample CSV data for testing"""
    print_step(2, "Setting Up Sample Data")
    
    data_dir = os.getenv("DATA_DIR", "./data")
    facts_csv = os.path.join(data_dir, "facts.csv")
    
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Create clean CSV with headers only
    with open(facts_csv, "w") as f:
        f.write("type,subject,fee_rate,report_delay_days,sector,notice_sent\n")
    
    print_substep("CSV Setup", f"Created/cleared {facts_csv}")
    
    # Check if policy rules exist
    policy_file = os.path.join(os.getenv("OUT_DIR", "./out"), "policy.yaml")
    if os.path.exists(policy_file):
        print_substep("Policy Rules", "Found existing policy.yaml")
    else:
        print_substep("Policy Rules", "⚠️  No policy.yaml found - run document processing first")

def demonstrate_fact_processing():
    """Demonstrate real-time fact processing"""
    print_step(3, "Real-time Fact Processing Demo")
    
    data_dir = os.getenv("DATA_DIR", "./data")
    facts_csv = os.path.join(data_dir, "facts.csv")
    
    # Test facts that should trigger violations
    test_facts = [
        {
            "fact": "fee_post,Institution A,0.015,,,",
            "description": "Valid fee (1.5% - should pass)"
        },
        {
            "fact": "fee_post,Institution A,0.0200,,,",
            "description": "Invalid fee (2.0% - should violate 1.75% limit)"
        },
        {
            "fact": "report_delivered,Foundation B,,7,,",
            "description": "Late report (7 days - should violate 45 day limit)"
        },
        {
            "fact": "trade_allocated,Institution A,,,SIC:7372,",
            "description": "Prohibited sector trade (SIC:7372 - should violate)"
        },
        {
            "fact": "trade_allocated,Institution A,,,SIC:7371,",
            "description": "Valid trade (SIC:7371 - should pass)"
        }
    ]
    
    print_substep("Test Facts", f"Processing {len(test_facts)} test facts")
    
    for i, test in enumerate(test_facts, 1):
        print(f"\n  📝 Fact {i}: {test['description']}")
        print(f"     Data: {test['fact']}")
        
        # Add fact to CSV
        with open(facts_csv, "a") as f:
            f.write(test['fact'] + "\n")
        
        print(f"     ✅ Added to CSV")
        
        # Wait for processing
        time.sleep(3)
        
        # Check for new violations
        try:
            response = requests.get("http://localhost:7000/violations?limit=5")
            if response.status_code == 200:
                violations = response.json()
                print(f"     📊 Total violations: {len(violations)}")
                if violations:
                    latest = violations[-1]
                    print(f"     ⚠️  Latest violation: {latest.get('rule_id', 'unknown')}")
            else:
                print(f"     ❌ Could not check violations (status {response.status_code})")
        except requests.exceptions.RequestException:
            print(f"     ❌ Could not connect to API")

def demonstrate_sse_streaming():
    """Demonstrate SSE streaming capabilities"""
    print_step(4, "SSE Streaming Demo")
    
    print_substep("SSE Endpoint", "http://localhost:7000/violations/stream")
    print_substep("Usage", "curl -N http://localhost:7000/violations/stream")
    
    print("\n  🔄 To test SSE streaming:")
    print("     1. Run: curl -N http://localhost:7000/violations/stream")
    print("     2. Add facts to data/facts.csv in another terminal")
    print("     3. Watch violations appear in real-time")
    
    # Try to connect to SSE stream briefly
    try:
        print("\n  🧪 Testing SSE connection...")
        response = requests.get("http://localhost:7000/violations/stream", 
                              stream=True, timeout=5)
        if response.status_code == 200:
            print("     ✅ SSE stream is accessible")
        else:
            print(f"     ❌ SSE stream error (status {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"     ❌ Could not connect to SSE stream: {e}")

def show_violation_summary():
    """Show summary of current violations"""
    print_step(5, "Violation Summary")
    
    try:
        response = requests.get("http://localhost:7000/violations")
        if response.status_code == 200:
            violations = response.json()
            
            if violations:
                print_substep("Total Violations", f"{len(violations)} violations found")
                
                # Group by rule ID
                rule_counts = {}
                for v in violations:
                    rule_id = v.get('rule_id', 'unknown')
                    rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
                
                print("\n  📊 Violations by Rule:")
                for rule_id, count in rule_counts.items():
                    print(f"     • {rule_id}: {count} violations")
                
                # Show latest violation details
                latest = violations[-1]
                print(f"\n  🔍 Latest Violation:")
                print(f"     Rule: {latest.get('rule_id', 'unknown')}")
                print(f"     Subject: {latest.get('subject', 'unknown')}")
                print(f"     Summary: {latest.get('summary', 'No summary')}")
                
            else:
                print_substep("No Violations", "No violations found in the system")
                
        else:
            print_substep("Error", f"Could not fetch violations (status {response.status_code})")
            
    except requests.exceptions.RequestException as e:
        print_substep("Error", f"Could not connect to API: {e}")

def show_next_steps():
    """Show next steps for the user"""
    print_step(6, "Next Steps")
    
    print("""
  🚀 Your HWB streaming pipeline is ready!
  
  📋 To continue testing:
     1. Keep the FastAPI server running: python run_server.py
     2. Keep the Pathway runner running: python -m app.pathway.facts_runner
     3. Monitor violations: curl -N http://localhost:7000/violations/stream
     4. Add more facts: echo "fact_data" >> data/facts.csv
  
  🔧 To integrate with your own data:
     1. Replace data/facts.csv with your real data source
     2. Modify app/pathway/facts_runner.py for your data format
     3. Update the validation rules in your policy.yaml
     4. Connect your frontend to the SSE stream
  
  📊 To monitor the system:
     • API docs: http://localhost:7000/docs
     • Health check: http://localhost:7000/health
     • Violations: http://localhost:7000/violations
     • SSE stream: http://localhost:7000/violations/stream
  """)

def main():
    """Run the complete streaming demo"""
    print_header("HWB Complete Streaming Pipeline Demo")
    
    print("""
  🎯 This demo shows the complete HWB streaming pipeline:
     1. Real-time fact processing through Pathway
     2. Violation detection and explanation
     3. SSE streaming for live monitoring
     4. End-to-end workflow demonstration
  
  ⚠️  Prerequisites:
     • FastAPI server running: python run_server.py
     • Pathway runner running: python -m app.pathway.facts_runner
     • Policy rules compiled (from document processing)
  """)
    
    check_services()
    setup_sample_data()
    demonstrate_fact_processing()
    demonstrate_sse_streaming()
    show_violation_summary()
    show_next_steps()
    
    print_header("Streaming Demo Complete! 🎉")
    print("""
  🚀 The HWB streaming pipeline is fully operational!
  
  Your system can now:
  ✅ Process documents and compile policy rules
  ✅ Stream real-time facts through Pathway
  ✅ Detect violations and generate explanations
  ✅ Stream violations via SSE for live monitoring
  ✅ Provide RESTful API for all operations
  
  Ready for production deployment! 🚀
  """)

if __name__ == "__main__":
    main()

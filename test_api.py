#!/usr/bin/env python3
"""
Test script for the HWB FastAPI server
"""
import requests
import json
import time

BASE_URL = "http://localhost:7000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"✅ Health check: {response.json()}")

def test_doc_ingest():
    """Test document ingestion"""
    print("\n📄 Testing document ingestion...")
    
    # Test with existing document
    payload = {"path": "./docs/SideLetter_InstitutionA.pdf"}
    response = requests.post(
        f"{BASE_URL}/docs/ingest",
        headers={"Content-Type": "application/json"},
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Document ingested: {result}")
    else:
        print(f"❌ Error ingesting document: {response.status_code} - {response.text}")

def test_fact_validation():
    """Test fact validation"""
    print("\n🧪 Testing fact validation...")
    
    test_facts = [
        {
            "name": "Valid fee post",
            "fact": {"type": "fee_post", "payload": {"subject": "Institution A", "fee_rate": 0.015}},
            "expected": "No violations"
        },
        {
            "name": "Invalid fee post (too high)",
            "fact": {"type": "fee_post", "payload": {"subject": "Institution A", "fee_rate": 0.02}},
            "expected": "Violation detected"
        }
    ]
    
    for test in test_facts:
        print(f"\n  🧪 Testing: {test['name']}")
        print(f"     Fact: {test['fact']}")
        print(f"     Expected: {test['expected']}")
        
        response = requests.post(
            f"{BASE_URL}/facts",
            headers={"Content-Type": "application/json"},
            json=test['fact']
        )
        
        if response.status_code == 200:
            result = response.json()
            violations = result.get("violations", [])
            messages = result.get("messages", [])
            
            if violations:
                print(f"     ⚠️  Result: Found {len(violations)} violation(s)")
                for v in violations:
                    print(f"        - Rule: {v['rule_id']}")
                    if 'summary' in v:
                        print(f"        - Summary: {v['summary']}")
            else:
                print(f"     ✅ Result: No violations found")
        else:
            print(f"     ❌ Error: {response.status_code} - {response.text}")

def test_violations_snapshot():
    """Test violations snapshot endpoint"""
    print("\n📊 Testing violations snapshot...")
    
    response = requests.get(f"{BASE_URL}/violations?limit=5")
    
    if response.status_code == 200:
        violations = response.json()
        print(f"✅ Retrieved {len(violations)} violations")
        for i, v in enumerate(violations[-3:], 1):  # Show last 3
            print(f"  {i}. Rule: {v.get('rule_id', 'Unknown')}")
            print(f"     Subject: {v.get('subject', 'Unknown')}")
            print(f"     Summary: {v.get('summary', 'No summary')[:100]}...")
    else:
        print(f"❌ Error retrieving violations: {response.status_code} - {response.text}")

def test_sse_stream():
    """Test SSE stream (just check if it's accessible)"""
    print("\n📡 Testing SSE stream accessibility...")
    
    try:
        response = requests.get(f"{BASE_URL}/violations/stream", stream=True, timeout=2)
        if response.status_code == 200:
            print("✅ SSE stream is accessible")
        else:
            print(f"❌ SSE stream error: {response.status_code}")
    except requests.exceptions.Timeout:
        print("✅ SSE stream is accessible (timeout expected)")
    except Exception as e:
        print(f"❌ SSE stream error: {e}")

def main():
    """Run all API tests"""
    print("🚀 HWB FastAPI Server Test Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Server is not running: {e}")
        print("Please start the server with: python run_server.py")
        return
    
    # Run tests
    test_health()
    test_doc_ingest()
    test_fact_validation()
    test_violations_snapshot()
    test_sse_stream()
    
    print("\n🎉 API test suite completed!")
    print("\nNext steps:")
    print("📡 Open SSE stream: curl -N http://localhost:7000/violations/stream")
    print("🌐 View API docs: http://localhost:7000/docs")
    print("📊 View violations: curl http://localhost:7000/violations")

if __name__ == "__main__":
    main()

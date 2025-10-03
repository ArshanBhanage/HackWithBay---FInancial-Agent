#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Financial Contract Drift Monitor
Tests all endpoints and validates responses
"""

import requests
import json
import time
import os
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_endpoint(method: str, endpoint: str, data: Dict[Any, Any] = None, files: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test a single endpoint and return results"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method.upper() == "POST":
            if files:
                response = requests.post(url, data=data, files=files, timeout=10)
            else:
                response = requests.post(url, json=data, timeout=10)
        elif method.upper() == "PATCH":
            response = requests.patch(url, json=data, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        return {
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "success": 200 <= response.status_code < 300
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "success": False}

def run_api_tests():
    """Run comprehensive API tests"""
    print("🧪 Starting API Tests for Financial Contract Drift Monitor")
    print("=" * 60)
    
    tests = [
        # Health and Status
        ("GET", "/health", "Health Check"),
        
        # Core Endpoints
        ("GET", "/contracts", "List Contracts"),
        ("GET", "/alerts", "List Alerts"),
        ("GET", "/notifications/test", "Test Notifications"),
        
        # Upload Test
        ("POST", "/upload", "Upload Document", 
         {"document_type": "credit_agreement"}, 
         {"file": ("test_contract.txt", "This is a test contract", "text/plain")}),
        
        # Drift Detection
        ("POST", "/contracts/test_id/detect-drift", "Detect Drift", 
         None, None, {"from_version_id": "v1", "to_version_id": "v2"}),
        
        # Policy Compilation
        ("POST", "/policies/compile", "Compile Policy", {
            "policy_id": "test_policy",
            "name": "Test Policy",
            "rules": [{
                "id": "test_rule",
                "type": "fee_rate",
                "field": "management_fee",
                "operator": "equals",
                "value": "1.5",
                "severity": "HIGH"
            }]
        }),
        
        # Webhook Tests (will fail due to signature validation)
        ("POST", "/webhooks/crm", "CRM Webhook", {"event": "test", "data": {"message": "test"}}),
        ("POST", "/webhooks/portfolio", "Portfolio Webhook", {"event": "test", "data": {"message": "test"}}),
        ("POST", "/webhooks/fund-admin", "Fund Admin Webhook", {"event": "test", "data": {"message": "test"}}),
    ]
    
    results = []
    
    for test in tests:
        method, endpoint, name = test[:3]
        data = test[3] if len(test) > 3 else None
        files = test[4] if len(test) > 4 else None
        params = test[5] if len(test) > 5 else None
        
        print(f"\n🔍 Testing {name}...")
        result = test_endpoint(method, endpoint, data, files, params)
        
        if result.get("success"):
            print(f"✅ {name}: PASSED (Status: {result['status_code']})")
        else:
            print(f"❌ {name}: FAILED")
            if "error" in result:
                print(f"   Error: {result['error']}")
            else:
                print(f"   Status: {result['status_code']}")
                print(f"   Response: {result.get('response', 'No response')}")
        
        results.append({
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "success": result.get("success", False),
            "status_code": result.get("status_code"),
            "error": result.get("error")
        })
    
    # Test Frontend
    print(f"\n🌐 Testing Frontend...")
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print("✅ Frontend: PASSED")
            frontend_success = True
        else:
            print(f"❌ Frontend: FAILED (Status: {response.status_code})")
            frontend_success = False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend: FAILED (Error: {e})")
        frontend_success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"Backend API Tests: {passed}/{total} passed")
    print(f"Frontend: {'PASSED' if frontend_success else 'FAILED'}")
    
    print(f"\n📋 Detailed Results:")
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"  {status} {result['method']} {result['endpoint']} - {result['name']}")
        if not result["success"] and result.get("error"):
            print(f"    Error: {result['error']}")
    
    return {
        "backend_passed": passed,
        "backend_total": total,
        "frontend_success": frontend_success,
        "results": results
    }

if __name__ == "__main__":
    # Create test file
    with open("test_contract.txt", "w") as f:
        f.write("This is a test contract document for API testing.")
    
    try:
        results = run_api_tests()
        
        # Clean up
        if os.path.exists("test_contract.txt"):
            os.remove("test_contract.txt")
        
        print(f"\n🎯 Overall Status: {'ALL TESTS PASSED' if results['backend_passed'] == results['backend_total'] and results['frontend_success'] else 'SOME TESTS FAILED'}")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
    finally:
        # Clean up
        if os.path.exists("test_contract.txt"):
            os.remove("test_contract.txt")

#!/usr/bin/env python3
"""
HWB System Status Checker

Quick status check for all HWB system components:
- FastAPI server health
- Pathway runner status
- Policy rules compilation
- Violation tracking
- File system status

Usage:
    python status.py
"""

import os
import sys
import json
import requests
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_status(title, status, details=""):
    """Print a status line with emoji"""
    emoji = "✅" if status else "❌"
    print(f"{emoji} {title}")
    if details:
        print(f"   {details}")

def check_fastapi_server():
    """Check FastAPI server status"""
    try:
        response = requests.get("http://localhost:7000/health", timeout=2)
        if response.status_code == 200:
            return True, "Server responding"
        else:
            return False, f"Server error (status {response.status_code})"
    except requests.exceptions.RequestException:
        return False, "Server not running"

def check_pathway_runner():
    """Check if Pathway runner is likely running"""
    # This is a heuristic check - we can't easily detect if the runner is running
    # without additional infrastructure
    return None, "Manual check required (python -m app.pathway.facts_runner)"

def check_policy_rules():
    """Check if policy rules are compiled"""
    policy_file = os.path.join(os.getenv("OUT_DIR", "./out"), "policy.yaml")
    rules_index = os.path.join(os.getenv("OUT_DIR", "./out"), "rules_index.json")
    
    if os.path.exists(policy_file) and os.path.exists(rules_index):
        try:
            with open(rules_index, 'r') as f:
                rules_data = json.load(f)
            rule_count = len(rules_data.get('rules', []))
            return True, f"{rule_count} rules compiled"
        except:
            return True, "Rules compiled (index error)"
    else:
        return False, "No compiled rules found"

def check_violations():
    """Check violation tracking"""
    violations_file = os.path.join(os.getenv("OUT_DIR", "./out"), "violations.jsonl")
    
    if os.path.exists(violations_file):
        try:
            with open(violations_file, 'r') as f:
                lines = f.readlines()
            violation_count = len([line for line in lines if line.strip()])
            return True, f"{violation_count} violations logged"
        except:
            return True, "Violations logged (read error)"
    else:
        return False, "No violation log found"

def check_data_files():
    """Check data files status"""
    data_dir = os.getenv("DATA_DIR", "./data")
    facts_csv = os.path.join(data_dir, "facts.csv")
    
    if os.path.exists(facts_csv):
        try:
            with open(facts_csv, 'r') as f:
                lines = f.readlines()
            fact_count = len([line for line in lines if line.strip() and not line.startswith('#')])
            return True, f"{fact_count} facts in CSV"
        except:
            return True, "CSV exists (read error)"
    else:
        return False, "No facts CSV found"

def check_file_system():
    """Check file system structure"""
    required_dirs = ["app", "scripts", "data", "out"]
    required_files = [
        "requirements.txt",
        "app/server.py",
        "app/pathway/facts_runner.py",
        "app/graph/build.py"
    ]
    
    missing_dirs = [d for d in required_dirs if not os.path.exists(d)]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if not missing_dirs and not missing_files:
        return True, "All required files present"
    else:
        missing = missing_dirs + missing_files
        return False, f"Missing: {', '.join(missing)}"

def get_system_info():
    """Get basic system information"""
    info = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version.split()[0],
        "working_directory": os.getcwd(),
        "environment": {
            "DATA_DIR": os.getenv("DATA_DIR", "./data"),
            "OUT_DIR": os.getenv("OUT_DIR", "./out"),
            "DOCS_DIR": os.getenv("DOCS_DIR", "./docs"),
        }
    }
    return info

def main():
    """Run system status check"""
    print("🚀 HWB System Status Check")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check all components
    checks = [
        ("FastAPI Server", check_fastapi_server),
        ("Pathway Runner", check_pathway_runner),
        ("Policy Rules", check_policy_rules),
        ("Violation Tracking", check_violations),
        ("Data Files", check_data_files),
        ("File System", check_file_system),
    ]
    
    all_good = True
    for title, check_func in checks:
        status, details = check_func()
        print_status(title, status, details)
        if status is False:
            all_good = False
    
    print()
    print("📊 System Information:")
    info = get_system_info()
    for key, value in info.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for k, v in value.items():
                print(f"     {k}: {v}")
        else:
            print(f"   {key}: {value}")
    
    print()
    if all_good:
        print("🎉 System Status: ALL SYSTEMS OPERATIONAL")
        print()
        print("🚀 Ready for:")
        print("   • Document processing: python scripts/build_policy.py")
        print("   • Real-time streaming: python -m app.pathway.facts_runner")
        print("   • API access: http://localhost:7000/docs")
        print("   • SSE monitoring: curl -N http://localhost:7000/violations/stream")
    else:
        print("⚠️  System Status: ISSUES DETECTED")
        print()
        print("🔧 Recommended actions:")
        print("   • Start FastAPI server: python run_server.py")
        print("   • Start Pathway runner: python -m app.pathway.facts_runner")
        print("   • Process documents: python scripts/build_policy.py")
        print("   • Set up data: python scripts/test_streaming.py")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script for Pathway streaming functionality

This script helps test the real-time streaming pipeline by:
1. Creating sample CSV data
2. Providing commands to append new facts
3. Demonstrating the streaming workflow

Usage:
    python scripts/test_streaming.py
"""

import os
import sys
import time
import subprocess

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_step(step_num, title):
    """Print a formatted step"""
    print(f"\n📋 Step {step_num}: {title}")
    print("-" * 40)

def create_sample_csv():
    """Create sample CSV data for testing"""
    print_step(1, "Creating Sample CSV Data")
    
    data_dir = os.getenv("DATA_DIR", "./data")
    facts_csv = os.path.join(data_dir, "facts.csv")
    
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Create CSV with headers and sample data
    sample_data = [
        "type,subject,fee_rate,report_delay_days,sector,notice_sent",
        "# Valid fee post (should not trigger violation)",
        "fee_post,Institution A,0.015,,,",
        "# Invalid fee post (should trigger violation - exceeds 1.75%)",
        "fee_post,Institution A,0.0200,,,",
        "# Late report (should trigger violation - exceeds 45 days)",
        "report_delivered,Foundation B,,7,,",
        "# Prohibited sector trade (should trigger violation)",
        "trade_allocated,Institution A,,,SIC:7372,",
        "# Valid trade (should not trigger violation)",
        "trade_allocated,Institution A,,,SIC:7371,",
    ]
    
    with open(facts_csv, "w") as f:
        for line in sample_data:
            f.write(line + "\n")
    
    print(f"✅ Created sample CSV: {facts_csv}")
    print(f"📊 Sample data includes:")
    print(f"   • Valid fee post (1.5% - should pass)")
    print(f"   • Invalid fee post (2.0% - should violate 1.75% limit)")
    print(f"   • Late report (7 days - should violate 45 day limit)")
    print(f"   • Prohibited sector trade (SIC:7372 - should violate)")
    print(f"   • Valid trade (SIC:7371 - should pass)")

def show_streaming_commands():
    """Show commands for testing streaming"""
    print_step(2, "Streaming Test Commands")
    
    data_dir = os.getenv("DATA_DIR", "./data")
    facts_csv = os.path.join(data_dir, "facts.csv")
    
    print("""
    🚀 To test the streaming pipeline:
    
    1. Start the FastAPI server (in one terminal):
       python run_server.py
    
    2. Start the Pathway facts runner (in another terminal):
       python -m app.pathway.facts_runner
    
    3. Monitor violations in real-time (in a third terminal):
       curl -N http://localhost:7000/violations/stream
    
    4. Add new facts to trigger violations:
    """)
    
    print(f"   # Add a high fee (should trigger violation):")
    print(f'   echo "fee_post,Institution A,0.025,,," >> {facts_csv}')
    print()
    print(f"   # Add a late report (should trigger violation):")
    print(f'   echo "report_delivered,Foundation B,,60,," >> {facts_csv}')
    print()
    print(f"   # Add a prohibited trade (should trigger violation):")
    print(f'   echo "trade_allocated,Institution A,,,SIC:7372," >> {facts_csv}')
    print()
    print(f"   # Add a valid fact (should not trigger violation):")
    print(f'   echo "fee_post,Institution A,0.01,,," >> {facts_csv}')

def show_manual_testing():
    """Show manual testing approach"""
    print_step(3, "Manual Testing Approach")
    
    print("""
    🧪 Manual Testing Steps:
    
    1. **Start all services:**
       Terminal 1: python run_server.py
       Terminal 2: python -m app.pathway.facts_runner
       Terminal 3: curl -N http://localhost:7000/violations/stream
    
    2. **Add facts one by one and watch for violations:**
       - Each line added to data/facts.csv should be processed immediately
       - Violations should appear in the SSE stream
       - Check the terminal running the facts runner for processing logs
    
    3. **Verify violation details:**
       - Check out/violations.jsonl for persistent violation log
       - Verify violation summaries and rule IDs
       - Confirm that valid facts don't trigger violations
    
    4. **Test edge cases:**
       - Empty values (should be handled gracefully)
       - Invalid data types (should be skipped with warnings)
       - Multiple rapid additions (should process in order)
    """)

def show_automated_testing():
    """Show automated testing approach"""
    print_step(4, "Automated Testing")
    
    print("""
    🤖 Automated Testing Script:
    
    You can create a script to automatically add facts and verify violations:
    
    ```python
    import time
    import requests
    
    # Test facts that should trigger violations
    test_facts = [
        "fee_post,Institution A,0.025,,,",  # High fee
        "report_delivered,Foundation B,,60,,",  # Late report
        "trade_allocated,Institution A,,,SIC:7372,",  # Prohibited sector
    ]
    
    # Add facts with delays
    for fact in test_facts:
        with open("data/facts.csv", "a") as f:
            f.write(fact + "\\n")
        time.sleep(2)  # Wait for processing
        print(f"Added: {fact}")
    
    # Check violations
    response = requests.get("http://localhost:7000/violations")
    violations = response.json()
    print(f"Total violations: {len(violations)}")
    ```
    """)

def main():
    """Run the streaming test setup"""
    print_header("HWB Pathway Streaming Test Setup")
    
    create_sample_csv()
    show_streaming_commands()
    show_manual_testing()
    show_automated_testing()
    
    print_header("Streaming Test Setup Complete! 🎉")
    print("""
    🚀 Ready to test real-time streaming!
    
    Next steps:
    1. Start the FastAPI server: python run_server.py
    2. Start the Pathway runner: python -m app.pathway.facts_runner
    3. Monitor violations: curl -N http://localhost:7000/violations/stream
    4. Add facts to data/facts.csv to trigger real-time validation
    
    The system will now process facts in real-time and stream violations
    to the SSE endpoint for live monitoring! 📡
    """)

if __name__ == "__main__":
    main()

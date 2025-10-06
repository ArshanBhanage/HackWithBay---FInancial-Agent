"""
Pathway Facts Runner - Stream CSV data and trigger real-time violations

This module watches a CSV file for new fact events and processes them through
the HWB LangGraph pipeline to generate violations that stream to the SSE endpoint.

Usage:
    python -m app.pathway.facts_runner

The runner expects a CSV file at data/facts.csv with the following columns:
- type: Event type (e.g., "fee_post", "report_delivered", "trade_allocated")
- subject: Entity subject (e.g., "Institution A", "Foundation B")
- fee_rate: Fee rate as decimal (e.g., "0.0200")
- report_delay_days: Report delay in days (e.g., "7")
- sector: Sector code (e.g., "SIC:7372")
- notice_sent: Notice sent flag (e.g., "true", "false")
"""

import os
import sys
import pathway as pw
from typing import Optional

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.graph.build import build_data_graph

# Configuration
DATA_DIR = os.getenv("DATA_DIR", "./data")
FACTS_CSV = os.path.join(DATA_DIR, "facts.csv")

# Initialize the data validation graph
graph = build_data_graph()

@pw.udf
def validate_fact(event_type: str,
                  subject: Optional[str] = None,
                  fee_rate: Optional[str] = None,
                  report_delay_days: Optional[str] = None,
                  sector: Optional[str] = None,
                  notice_sent: Optional[str] = None) -> str:
    """
    Process a fact event through the HWB validation pipeline.
    
    Args:
        event_type: Type of event (fee_post, report_delivered, trade_allocated, etc.)
        subject: Entity subject name
        fee_rate: Fee rate as string (will be converted to float)
        report_delay_days: Report delay in days as string (will be converted to int)
        sector: Sector code
        notice_sent: Notice sent flag as string (will be converted to bool)
    
    Returns:
        "ok" on successful processing
    """
    try:
        # Build payload from available fields
        payload = {}
        
        if subject and subject.strip():
            payload["subject"] = subject.strip()
            
        if fee_rate and fee_rate.strip() and fee_rate.strip().lower() not in ("", "null", "none"):
            try:
                payload["fee_rate"] = float(fee_rate)
            except ValueError:
                print(f"Warning: Invalid fee_rate '{fee_rate}', skipping")
                
        if report_delay_days and report_delay_days.strip() and report_delay_days.strip().lower() not in ("", "null", "none"):
            try:
                payload["report_delay_days"] = int(report_delay_days)
            except ValueError:
                print(f"Warning: Invalid report_delay_days '{report_delay_days}', skipping")
                
        if sector and sector.strip() and sector.strip().lower() not in ("", "null", "none"):
            payload["sector"] = sector.strip()
            
        if notice_sent and notice_sent.strip() and notice_sent.strip().lower() not in ("", "null", "none"):
            payload["notice_sent"] = notice_sent.strip().lower() in ("1", "true", "yes", "y")
        
        # Create the event object
        event = {
            "type": event_type.strip(),
            "payload": payload
        }
        
        print(f"Processing event: {event}")
        
        # Invoke the data validation graph
        result = graph.invoke({"data_event": event})
        
        # Log the result
        violations = result.get("violations", [])
        messages = result.get("messages", [])
        
        if violations:
            print(f"⚠️  Generated {len(violations)} violations:")
            for violation in violations:
                print(f"   - {violation.get('rule_id', 'unknown')}: {violation.get('summary', 'No summary')}")
        else:
            print("✅ No violations detected")
            
        if messages:
            print(f"📝 Messages: {messages}")
            
        return "ok"
        
    except Exception as e:
        print(f"❌ Error processing event: {e}")
        return f"error: {str(e)}"

def main():
    """
    Main function to start the Pathway facts watcher.
    
    Creates the data directory if it doesn't exist and starts watching
    the CSV file for new fact events.
    """
    print("🚀 Starting HWB Pathway Facts Runner")
    print("=" * 50)
    print(f"📁 Watching CSV file: {FACTS_CSV}")
    print(f"📊 Data directory: {DATA_DIR}")
    print("=" * 50)
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Create empty CSV with headers if it doesn't exist
    if not os.path.exists(FACTS_CSV):
        print(f"📝 Creating CSV file: {FACTS_CSV}")
        with open(FACTS_CSV, "w") as f:
            f.write("type,subject,fee_rate,report_delay_days,sector,notice_sent\n")
    
    try:
        # Read CSV file in streaming mode
        print("👀 Starting CSV stream watcher...")
        facts = pw.io.csv.read(
            FACTS_CSV,
            header=True,
            mode="streaming",
            autocommit_duration_ms=1000  # Process changes every second
        )
        
        # Process each row through the validation pipeline
        output = facts.select(
            result=validate_fact(
                facts.type,
                facts.subject,
                facts.fee_rate,
                facts.report_delay_days,
                facts.sector,
                facts.notice_sent
            )
        )
        
        # Start the Pathway runtime
        print("🔄 Pathway runtime started - watching for new facts...")
        print("💡 Add rows to data/facts.csv to trigger real-time validation")
        print("📡 Violations will appear in the SSE stream at http://localhost:7000/violations/stream")
        print("🛑 Press Ctrl+C to stop")
        
        pw.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping Pathway facts runner...")
    except Exception as e:
        print(f"❌ Error in Pathway runner: {e}")
        raise

if __name__ == "__main__":
    main()

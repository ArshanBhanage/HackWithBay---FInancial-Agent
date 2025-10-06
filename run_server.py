#!/usr/bin/env python3
"""
Run the HWB FastAPI server
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    print("🚀 Starting HWB FastAPI Server...")
    print("📡 Server will be available at: http://localhost:7000")
    print("📊 API docs will be available at: http://localhost:7000/docs")
    print("🔗 SSE stream will be available at: http://localhost:7000/violations/stream")
    print("\n🛑 Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "app.server:app",
        host="0.0.0.0",
        port=7000,
        reload=True,
        log_level="info"
    )

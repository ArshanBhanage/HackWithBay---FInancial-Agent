#!/bin/bash
# HWB FastAPI Server - Curl Test Script
# Make sure the server is running: python run_server.py

BASE_URL="http://localhost:7000"

echo "🚀 HWB FastAPI Server - Curl Test Suite"
echo "========================================"

echo ""
echo "1. 🔍 Testing health endpoint..."
curl -s "$BASE_URL/health" | jq '.' || echo "❌ Health check failed"

echo ""
echo "2. 📄 Testing document ingestion..."
curl -X POST "$BASE_URL/docs/ingest" \
  -H "Content-Type: application/json" \
  -d '{"path":"./docs/SideLetter_InstitutionA.pdf"}' \
  | jq '.' || echo "❌ Document ingestion failed"

echo ""
echo "3. 🧪 Testing fact validation (should be valid)..."
curl -X POST "$BASE_URL/facts" \
  -H "Content-Type: application/json" \
  -d '{"type":"fee_post","payload":{"subject":"Institution A","fee_rate":0.015}}' \
  | jq '.' || echo "❌ Fact validation failed"

echo ""
echo "4. ⚠️  Testing fact validation (should trigger violation)..."
curl -X POST "$BASE_URL/facts" \
  -H "Content-Type: application/json" \
  -d '{"type":"fee_post","payload":{"subject":"Institution A","fee_rate":0.02}}' \
  | jq '.' || echo "❌ Fact validation failed"

echo ""
echo "5. 📊 Testing violations snapshot..."
curl -s "$BASE_URL/violations?limit=3" | jq '.' || echo "❌ Violations snapshot failed"

echo ""
echo "6. 📡 Testing SSE stream (will timeout after 3 seconds)..."
timeout 3 curl -N "$BASE_URL/violations/stream" || echo "✅ SSE stream is accessible"

echo ""
echo "🎉 Curl test suite completed!"
echo ""
echo "Next steps:"
echo "• View API docs: http://localhost:7000/docs"
echo "• Monitor SSE stream: curl -N http://localhost:7000/violations/stream"
echo "• Upload document: curl -X POST http://localhost:7000/docs/ingest -F 'file=@./docs/contract.pdf'"

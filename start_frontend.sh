#!/bin/bash
set -e
cd "$(dirname "$0")"
export PORT="${PORT:-9000}"
export VERIFYIT_DS_API="http://localhost:8000/api"
exec python3 -m streamlit run frontend/app.py \
  --server.port "$PORT" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --server.baseUrlPath "/ds" \
  --browser.gatherUsageStats false

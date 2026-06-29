#!/usr/bin/env bash
set -e

echo "==> Starting Elasticsearch + Kibana…"
docker compose up -d

echo ""
echo "==> Installing Python dependencies…"
pip install -q -r requirements.txt

echo ""
echo "==> Generating and loading 1 000 000 documents…"
python3 generate_and_load.py

echo ""
echo "==> Done!"
echo "    Elasticsearch : http://localhost:9200"
echo "    Kibana        : http://localhost:5601"

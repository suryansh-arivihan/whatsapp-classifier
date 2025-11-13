#!/bin/bash

echo "Testing: physics me important questions chahiye h"
echo ""

curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"message": "physics me important questions chahiye h"}' \
  2>/dev/null | python3 -m json.tool

echo ""

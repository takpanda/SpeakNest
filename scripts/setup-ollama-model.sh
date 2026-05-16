#!/usr/bin/env bash
# Pull gemma4:e4b into the remote Ollama server (192.168.1.103).
# Usage: ./scripts/setup-ollama-model.sh

set -euo pipefail

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://192.168.1.103:11434}"
MODEL="${MODEL:-gemma4:e4b}"

echo "Pulling ${MODEL} into Ollama at ${OLLAMA_BASE_URL} ..."

STATUS=$(curl -sf --max-time 30 "${OLLAMA_BASE_URL}/api/tags" | python3 -c "import sys,json; tags=json.load(sys.stdin); print(' '.join(d.get('name','') for d in tags.get('models',[])))")

if echo "$STATUS" | grep -qF "${MODEL}"; then
    echo "Model ${MODEL} already present."
else
    curl -fs --max-time 600 "${OLLAMA_BASE_URL}/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"${MODEL}\"}" || {
        echo "ERROR: Failed to pull ${MODEL}"
        exit 1
    }
    echo "Model ${MODEL} pulled successfully."
fi

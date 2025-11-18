#!/bin/sh
set -eu

MODEL_LIST="${OLLAMA_PULL_MODELS:-}"
LISTEN_HOST="${OLLAMA_LISTEN_HOST:-0.0.0.0}"

echo "Starting Ollama server on ${LISTEN_HOST}"
OLLAMA_HOST="${LISTEN_HOST}" ollama serve &
SERVER_PID=$!

cleanup() {
  echo "Shutting down Ollama server"
  kill -TERM "${SERVER_PID}" 2>/dev/null || true
  wait "${SERVER_PID}" 2>/dev/null || true
}
trap cleanup INT TERM

if [ -n "${MODEL_LIST}" ]; then
  # CLI connections should use loopback even if the server listens on 0.0.0.0
  export OLLAMA_HOST="127.0.0.1:11434"
  echo "Waiting for Ollama API to become ready..."
  until ollama list >/dev/null 2>&1; do
    sleep 1
  done

  for model in ${MODEL_LIST}; do
    echo "Pulling Ollama model: ${model}"
    ollama pull "${model}"
  done
fi

wait "${SERVER_PID}"

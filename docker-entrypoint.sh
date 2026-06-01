#!/bin/bash

ollama serve &
OLLAMA_PID=$!

echo "Aguardando Ollama iniciar..."
sleep 20

echo "Baixando modelo llama3.2:3b..."
ollama pull llama3.2:3b

wait $OLLAMA_PID
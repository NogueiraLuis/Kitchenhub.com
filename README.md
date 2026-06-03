---
title: Ollama API
emoji: 🦙
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Ollama API

Serviço de IA usando Ollama com modelo TinyLlama.

## Como usar

```bash
curl -X POST [https://vxzs-ollama-api.hf.space/api/generate](https://vxzs-ollama-api.hf.space/api/generate) \
  -d '{
    "model": "tinyllama",
    "prompt": "Crie uma receita com frango",
    "stream": false
  }'
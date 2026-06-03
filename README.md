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

Serviço de IA usando Ollama com modelo Qwen 2.5 (1.5B).

## Como usar

```bash
curl -X POST [https://vxzs-ollama-api.hf.space/api/generate](https://vxzs-ollama-api.hf.space/api/generate) \
  -d '{
    "model": "qwen2.5:1.5b",
    "prompt": "Crie uma receita com frango",
    "stream": false
  }'
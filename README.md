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

Serviço de IA usando Ollama com modelo llama3.2:3b.

## Como usar

```bash
curl -X POST https://vxzs-ollama-api.hf.space/api/generate \
  -d '{
    "model": "llama3.2:3b",
    "prompt": "Crie uma receita com frango",
    "stream": false
  }'
```

## Documentação

https://ollama.ai
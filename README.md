---
title: Ollama Api
emoji: 👁
colorFrom: yellow
colorTo: yellow
sdk: docker
pinned: false
license: mit
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

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
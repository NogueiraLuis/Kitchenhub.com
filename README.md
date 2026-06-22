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
  }
```

# Sistema de Livro de Receitas Inteligente

## Descrição do Projeto

O sistema é uma aplicação web que permite aos usuários pesquisar receitas, criar sua própria coleção de receitas favoritas e utilizar recursos de Inteligência Artificial para auxiliar na geração de novas receitas.

A aplicação foi desenvolvida seguindo uma arquitetura cliente-servidor, com frontend responsável pela interface do usuário e backend responsável pelo processamento das regras de negócio, persistência de dados e integração com serviços externos.

---

## Funcionalidades

* Cadastro de usuários
* Login de usuários
* Favoritar receitas
* Criação de um livro de receitas personalizado
* Armazenamento persistente de receitas favoritas
* Tradução automática de conteúdos
* Integração com Inteligência Artificial para geração de receitas
* Histórico de conversas com a IA
* Consumo de APIs externas
* Servidor de arquivos estáticos (HTML, CSS, JavaScript e imagens)

---

## Arquitetura

A aplicação utiliza uma arquitetura Full Stack composta por:

### Frontend

Responsável pela interface do usuário e interação com o sistema.

### Backend

Responsável por:

* Gerenciamento de usuários
* Autenticação
* Manipulação de receitas
* Comunicação com APIs externas
* Integração com IA
* Persistência de dados

### Banco de Dados

Utilizado para armazenar:

* Usuários cadastrados
* Receitas favoritas
* Dados necessários para funcionamento do sistema

---

## Tecnologias Utilizadas

### Linguagens

* Python
* JavaScript
* HTML5
* CSS3
* SQL

### Backend

* FastAPI
* Uvicorn
* SQLModel
* SQLAlchemy
* Pydantic

### Banco de Dados

* SQLite

### Integrações e APIs

* Ollama API
* HTTPX
* Requests

### Inteligência Artificial

* Ollama
* Modelo Qwen 2.5 (1.5B)

### Tradução

* Deep Translator
* Google Translator

### Frontend

* HTML5
* CSS3
* JavaScript

### Infraestrutura e Deploy

* Docker
* Procfile (deploy em plataforma cloud)
* Git
* GitHub
* Railway

---

## Bibliotecas Principais

* FastAPI
* SQLModel
* SQLAlchemy
* Pydantic
* HTTPX
* Requests
* Deep Translator
* Uvicorn

---

## Conceitos Aplicados

Durante o desenvolvimento foram aplicados conhecimentos de:

* Programação Full Stack
* Desenvolvimento de APIs REST
* Modelagem de Banco de Dados
* CRUD (Create, Read, Update e Delete)
* Integração com APIs externas
* Persistência de dados
* Estruturação de rotas
* Programação assíncrona
* Arquitetura Cliente-Servidor
* Manipulação de JSON
* Inteligência Artificial aplicada a sistemas web
* Controle de versão com Git

---

## Objetivo Acadêmico

O projeto tem como objetivo demonstrar a aplicação prática dos conhecimentos adquiridos em desenvolvimento web, banco de dados, integração de APIs e Inteligência Artificial, oferecendo aos usuários uma plataforma para gerenciamento de receitas culinárias personalizadas.

## link do site publicado!

https://kthub.up.railway.app

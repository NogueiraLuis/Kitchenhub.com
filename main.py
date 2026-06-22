import os
import json
import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional
import httpx
from deep_translator import GoogleTranslator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

# Cache global na memória do servidor para evitar chamadas duplicadas à API de tradução
CACHE_TRADUCOES = {}

# ---- CONFIGURAÇÃO ----
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///receitas.db")
PORT = int(os.getenv("PORT", 8000))
OLLAMA_URL = os.getenv("OLLAMA_URL", "https://vxzs-ollama-api.hf.space")
MODELO_IA = "qwen2.5:1.5b"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ---- MODELOS ----
class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    senha: str  # Alerta de amigo: Em produção, lembre-se de usar hashes (ex: bcrypt)!

class ReceitaFavorita(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: int
    titulo: str
    imagem: str
    serve: int = 0
    tempo: int = 0
    usuario_id: int

class DadosLogin(BaseModel):
    email: str
    senha: str

# ADIÇÃO CRÍTICA 1: Tabela para salvar o histórico no banco de dados SQLite
class MensagemChat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: str  # Guardamos como string para casar com o localStorage
    autor: str       # 'user' ou 'assistant'
    conteudo: str

# ---- APP ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_credentials=False,
    allow_headers=["Content-Type"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# ---- ROTAS HTML ----
TEMPLATES_DIR = "templates"

@app.get("/")
def index():
    return FileResponse(f"{TEMPLATES_DIR}/index.html")

@app.get("/{page}.html")
def serve_page(page: str):
    path = f"{TEMPLATES_DIR}/{page}.html"
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Página não encontrada")
    return FileResponse(path)

# ---- AUTENTICAÇÃO ----
@app.post("/api/usuario/cadastro")
def cadastrar_usuario(usuario: Usuario):
    with Session(engine) as session:
        if session.exec(select(Usuario).where(Usuario.email == usuario.email)).first():
            raise HTTPException(status_code=400, detail="Este usuário já está cadastrado.")
        session.add(usuario)
        session.commit()
        session.refresh(usuario)
        return {"mensagem": "Usuário criado com sucesso!", "usuario_id": usuario.id, "usuario": usuario.email}

@app.post("/api/usuario/login")
def logar_usuario(dados_login: DadosLogin):
    with Session(engine) as session:
        usuario = session.exec(
            select(Usuario).where(Usuario.email == dados_login.email, Usuario.senha == dados_login.senha)
        ).first()
        if not usuario:
            raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")
        return {"mensagem": "Login efetuado!", "usuario_id": usuario.id, "usuario": usuario.email}

# ---- API EXTERNA (TheMealDB) ----
CATEGORIA_MAP = {"massa": "Pasta", "sobremesa": "Dessert", "japonesa": "Seafood"}

@app.get("/api/externa/receitas")
async def buscar_externas(categoria: str):
    url = (
        "https://www.themealdb.com/api/json/v1/1/search.php?s=pizza"
        if categoria == "pizza"
        else f"https://www.themealdb.com/api/json/v1/1/filter.php?c={CATEGORIA_MAP.get(categoria, 'Pasta')}"
    )
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resposta = await client.get(url)
        if resposta.status_code != 200:
            return []
        dados = resposta.json().get("meals")
        return dados if dados else []
    except Exception as e:
        print(f"Erro ao buscar categoria '{categoria}': {e}")
        return []

def _executar_traducao_segura(partes_texto: list) -> str:
    texto_junto = " ||| ".join(partes_texto)
    return GoogleTranslator(source="en", target="pt").translate(texto_junto)

@app.get("/api/externa/receita-detalhes/{id_receita}")
async def obter_detalhes(id_receita: str):
    if id_receita in CACHE_TRADUCOES:
        return CACHE_TRADUCOES[id_receita]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resposta = await client.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={id_receita}")
            
        if resposta.status_code != 200:
            raise HTTPException(status_code=502, detail="Erro ao consultar API externa")

        dados = resposta.json()
        if not dados or "meals" not in dados or not dados["meals"]:
            raise HTTPException(status_code=404, detail="Receita não encontrada")

        receita = dados["meals"][0]
        titulo = receita.get("strMeal", "Receita sem título")
        instrucoes = receita.get("strInstructions", "Sem instruções disponíveis.")
        imagem = receita.get("strMealThumb", "")
        id_meal = receita.get("idMeal", id_receita)

        ingredientes_en = []
        for i in range(1, 21):
            ing = receita.get(f"strIngredient{i}")
            med = receita.get(f"strMeasure{i}")
            if ing and ing.strip():
                ingredientes_en.append(f"{med} - {ing}" if med and med.strip() else ing)

        titulo_pt, instrucoes_pt, ingredientes_pt = titulo, instrucoes, ingredientes_en
        
        try:
            partes = [titulo, instrucoes] + ingredientes_en
            traduzido = await asyncio.to_thread(_executar_traducao_segura, partes)
            
            if traduzido:
                split = traduzido.split(" ||| ")
                if len(split) >= 2:
                    titulo_pt, instrucoes_pt = split[0], split[1]
                    ingredientes_pt = split[2:]
        except Exception as e:
            print(f"Falha na tradução: {e}. Usando fallback em inglês.")

        CACHE_TRADUCOES[id_receita] = {
            "id": id_meal,
            "name": titulo_pt,
            "image": imagem,
            "instructions": instrucoes_pt,
            "ingredients": [i.strip() for i in ingredientes_pt],
        }

        return CACHE_TRADUCOES[id_receita]
    except Exception as e:
        print(f"Erro crítico na rota de detalhes: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar a receita")

# ---- MEU LIVRO ----
@app.get("/api/meu-livro/{id_usuario}", response_model=List[ReceitaFavorita])
def ver_livro(id_usuario: int):
    with Session(engine) as session:
        return session.exec(select(ReceitaFavorita).where(ReceitaFavorita.usuario_id == id_usuario)).all()

@app.post("/api/meu-livro")
def favoritar(receita: ReceitaFavorita):
    with Session(engine) as session:
        session.add(receita)
        session.commit()
        session.refresh(receita)
        return receita

@app.delete("/api/meu-livro/{id_banco}")
def remover_favorito(id_banco: int):
    with Session(engine) as session:
        receita = session.get(ReceitaFavorita, id_banco)
        if not receita:
            raise HTTPException(status_code=404, detail="Receita não encontrada")
        session.delete(receita)
        session.commit()
        return {"mensagem": "Receita removida com sucesso"}

# ---- ROTAS OLLAMA (IA) ----

# ADIÇÃO CRÍTICA 2: Rota GET para carregar o histórico quando o usuário abrir o chat
@app.get("/api/chat/historico/{usuario_id}")
def obter_historico_completo(usuario_id: str):
    with Session(engine) as session:
        mensagens = session.exec(
            select(MensagemChat)
            .where(MensagemChat.usuario_id == usuario_id)
            .order_by(MensagemChat.id.asc())
        ).all()
    return {"sucesso": True, "mensagens": mensagens}

# ADIÇÃO CRÍTICA 3: Rota adaptada para persistência e otimizada para o Qwen 1.5B
@app.post("/api/chat")
async def chat(data: dict):
    try:
        texto = data.get("texto", "").strip()
        usuario_chave = str(data.get("usuario_id", "anonimo"))
        
        if not texto:
            return {"sucesso": False, "erro": "Texto vazio"}
        
        # Busca as últimas 6 mensagens desse usuário específico no banco de dados
        with Session(engine) as session:
            mensagens_banco = session.exec(
                select(MensagemChat)
                .where(MensagemChat.usuario_id == usuario_chave)
                .order_by(MensagemChat.id.desc())
                .limit(6)
            ).all()
            
        # Inverte para manter a ordem cronológica correta antes de criar o prompt
        mensagens_banco.reverse()
            
        # Construção limpa e estruturada do histórico em ChatML
        contexto_passado = ""
        for msg in mensagens_banco:
            contexto_passado += f"<|im_start|>{msg.autor}\n{msg.conteudo}<|im_end|>\n"
            
        # Prompt do Sistema simplificado focado em Culinária e Substituições (evita confusões no Qwen 1.5B)
        prompt_final = (
            "<|im_start|>system\n"
            "Você é o Chef IA do KitchenHub. Seu trabalho é ajudar o usuário com receitas, dicas de culinária, substituição de ingredientes e passo a passo de pratos.\n"
            "Aproveite o histórico abaixo para lembrar o que o usuário já te disse.\n"
            "Seja direto, amigável e responda sempre em português do Brasil de forma curta.\n"
            "<|im_end|>\n"
            f"{contexto_passado}"
            f"<|im_start|>user\n{texto}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODELO_IA,
                    "prompt": prompt_final,
                    "stream": False,
                    "options": { 
                        "temperature": 0.3,
                        "top_p": 0.85
                    }
                }
            )
        
        if response.status_code == 200:
            resposta_ia = response.json().get("response", "").strip()
            resposta_ia = resposta_ia.replace("<|im_start|>", "").replace("<|im_end|>", "").strip()
            
            if not resposta_ia:
                resposta_ia = "Olá! Como posso ajudar na sua cozinha hoje?"
            
            # Grava a conversa atual no banco de dados para a próxima requisição
            with Session(engine) as session:
                msg_usuario = MensagemChat(usuario_id=usuario_chave, autor="user", conteudo=texto)
                msg_ia = MensagemChat(usuario_id=usuario_chave, autor="assistant", conteudo=resposta_ia)
                session.add(msg_usuario)
                session.add(msg_ia)
                session.commit()
            
            return {"sucesso": True, "resposta": resposta_ia}
        return {"sucesso": False, "erro": f"Erro do servidor de IA: {response.status_code}"}
            
    except Exception as e:
        print(f"Erro no chat: {e}")
        return {"sucesso": False, "erro": f"Erro interno: {str(e)}"}

# ADIÇÃO CRÍTICA 4: Rota de limpar histórico atualizada para expurgar as mensagens do banco
@app.post("/api/chat/limpar")
def limpar_historico(data: dict):
    usuario_chave = str(data.get("usuario_id", "anonimo"))
    with Session(engine) as session:
        mensagens = session.exec(select(MensagemChat).where(MensagemChat.usuario_id == usuario_chave)).all()
        for msg in mensagens:
            session.delete(msg)
        session.commit()
    return {"sucesso": True, "mensagem": "Histórico limpo com sucesso"}

@app.get("/api/health-ollama")
async def health_ollama():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            return {"status": "ok", "ollama": "disponível", "modelos": models}
        return {"status": "erro", "mensagem": f"Erro HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}

@app.get("/api/gerar-receita-ia/{ingredientes}")
async def gerar_receita_ia(ingredientes: str):
    try:
        mensagens = [
            {
                "role": "system",
                "content": "Você é um Chef IA estrutural. Sua única função é receber ingredientes e retornar um JSON válido e estrito. NENHUM texto adicional é permitido."
            },
            {
                "role": "user",
                "content": "Ingredientes: ovo, farinha de trigo, leite"
            },
            {
                "role": "assistant",
                "content": '{"nome": "Panqueca Simples", "ingredientes": ["1 ovo", "1 xícara de farinha", "1 xícara de leite"], "preparo": ["Misture tudo", "Frite"], "tempo_minutos": 10}'
            },
            {
                "role": "user",
                "content": f"Ingredientes: {ingredientes}"
            }
        ]

        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODELO_IA,
                    "messages": mensagens,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.1
                    }
                }
            )
        
        if response.status_code == 200:
            resposta_bruta = response.json().get("message", {}).get("content", "").strip()
            
            try:
                receita_json = json.loads(resposta_bruta)
                return {"sucesso": True, "receita": receita_json, "modelo": MODELO_IA}
            except json.JSONDecodeError:
                return {"sucesso": False, "erro": "A IA gerou um formato inválido.", "raw": resposta_bruta}
                
        return {"sucesso": False, "erro": f"Erro do servidor de IA: {response.status_code}"}
    except Exception as e:
        return {"sucesso": False, "erro": f"Erro interno: {str(e)}"}
import os
from contextlib import asynccontextmanager
from typing import List, Optional

import httpx
from deep_translator import GoogleTranslator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Field, Session, SQLModel, create_engine, select

# ---- CONFIGURAÇÃO ----

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///receitas.db")
PORT = int(os.getenv("PORT", 8000))

# URL do Ollama hospedado no HuggingFace Spaces
OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "https://vxzs-ollama-api.hf.space"
)

engine = create_engine(DATABASE_URL)


# ---- MODELOS ----

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    senha: str


class ReceitaFavorita(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: int
    titulo: str
    imagem: str
    serve: int = 0
    tempo: int = 0
    usuario_id: int


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

# Arquivos estáticos e assets
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


# ---- ROTAS HTML (SPA-style) ----

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
def logar_usuario(dados_login: dict):
    email = dados_login.get("email")
    senha = dados_login.get("senha")
    if not email or not senha:
        raise HTTPException(status_code=400, detail="E-mail e senha são obrigatórios.")
    with Session(engine) as session:
        usuario = session.exec(
            select(Usuario).where(Usuario.email == email, Usuario.senha == senha)
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
    except httpx.ReadTimeout:
        return []
    except Exception as e:
        print(f"Erro ao buscar categoria '{categoria}': {e}")
        return []


@app.get("/api/externa/receita-detalhes/{id_receita}")
async def obter_detalhes(id_receita: str):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resposta = await client.get(
                f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={id_receita}"
            )
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
            traduzido = GoogleTranslator(source="en", target="pt").translate(" ||| ".join(partes))
            if traduzido:
                split = traduzido.split(" ||| ")
                if len(split) >= 2:
                    titulo_pt, instrucoes_pt = split[0], split[1]
                    ingredientes_pt = split[2:]
        except Exception as e:
            print(f"Falha na tradução: {e}. Usando inglês.")

        return {
            "id": id_meal,
            "name": titulo_pt,
            "image": imagem,
            "instructions": instrucoes_pt,
            "ingredients": [i.strip() for i in ingredientes_pt],
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro crítico na rota de detalhes: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar a receita")


# ---- MEU LIVRO ----

@app.get("/api/meu-livro/{id_usuario}", response_model=List[ReceitaFavorita])
def ver_livro(id_usuario: int):
    with Session(engine) as session:
        return session.exec(
            select(ReceitaFavorita).where(ReceitaFavorita.usuario_id == id_usuario)
        ).all()


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


# ---- ROTAS OLLAMA (IA via HuggingFace Spaces) ----

@app.post("/api/chat")
async def chat(data: dict):
    """
    Chat com Ollama otimizado para o TinyLlama não alucinar
    """
    try:
        texto = data.get("texto", "")
        
        if not texto:
            return {"sucesso": False, "erro": "Texto vazio"}
        
        # PROMPT ULTRA RÍGIDO: Mostra pro TinyLlama exatamente o formato que ele deve responder
        # PROMPT DIRETO: Sem exemplos para o TinyLlama não copiar o texto errado
        prompt_sistema = """Você é o KitchenHub, um chef de cozinha assistente virtual.
        Você NUNCA fala sobre outros assuntos. Você APENAS responde sobre receitas e culinária.
        Responda sempre em português do Brasil, de forma curta, educada e direta.
        Não adicione marcações como [INST] ou Pergunta na sua resposta. Além disso, NUNCA repita o que o usuário disse. Responda apenas a resposta, sem introdução ou conclusão.
        Se o usuário fizer uma pergunta que não seja sobre culinária, responda: "Desculpe, só posso ajudar com receitas e culinária. Como posso te ajudar com suas receitas hoje?".
        Se o usuário pedir uma receita, responda apenas a receita, sem introdução ou conclusão. Seja direto e objetivo.
        Se o usuário fizer uma pergunta sobre culinária, responda de forma clara e direta, sem rodeios. Seja objetivo e educado.
        Se o usuário fizer uma pergunta vaga, responda pedindo mais detalhes, mas sem usar palavras como "Pergunta" ou "Usuário". Seja direto e educado.
        """
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "tinyllama",
                    "prompt": f"{prompt_sistema}\n\nUsuário: {texto}\nAssistente:",
                    "stream": False,
                    "temperature": 0.3,  # Baixamos a temperatura para ele ser menos "criativo" e errar menos
                    "stop": ["Usuário:", "[INST]"] # Trava para ele não simular a conversa sozinho
                }
            )
        
        if response.status_code == 200:
            result = response.json()
            resposta_ia = result.get("response", "").strip()
            
            # Limpeza rápida caso ele repita o prompt
            if "Pergunta:" in resposta_ia:
                resposta_ia = resposta_ia.split("Pergunta:")[0].strip()
                
            return {
                "sucesso": True,
                "resposta": resposta_ia if resposta_ia else "Olá! Como posso te ajudar com suas receitas hoje?"
            }
        else:
            return {"sucesso": False, "erro": f"Erro do servidor: {response.status_code}"}
            
    except Exception as e:
        print(f"Erro no chat: {e}")
        return {"sucesso": False, "erro": f"Erro: {str(e)}"}


@app.get("/api/health-ollama")
async def health_ollama():
    """
    Verifica se Ollama está online no HuggingFace Spaces
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
        
        if response.status_code == 200:
            data = response.json()
            models = [m["name"] for m in data.get("models", [])] if data else []
            return {
                "status": "ok",
                "ollama": "disponível online",
                "url": OLLAMA_URL,
                "modelos": models
            }
        else:
            return {
                "status": "erro",
                "mensagem": f"Ollama respondeu com erro {response.status_code}"
            }
    
    except httpx.ConnectError:
        return {
            "status": "erro",
            "mensagem": "Não conseguiu conectar ao Ollama"
        }
    except Exception as e:
        return {
            "status": "erro",
            "mensagem": f"Ollama offline: {str(e)}"
        }


@app.get("/api/gerar-receita-ia/{ingredientes}")
async def gerar_receita_ia(ingredientes: str):
    """
    Gera uma receita usando TinyLlama (rápido)
    Otimizado com tags de controle para não quebrar o português
    """
    try:
        # Prompt ultra engessado com as tags [INST] que o TinyLlama obedece
        prompt = f"""[INST] Você é um chef de cozinha brasileiro. Você deve criar uma receita simples usando obrigatoriamente estes ingredientes: {ingredientes}.
        Você deve responder APENAS no formato do exemplo abaixo, em português do Brasil. Não adicione saudações ou textos extras. Além disso, NUNCA repita os ingredientes ou o que o usuário disse. Responda apenas a receita, sem introdução ou conclusão. Seja direto e objetivo. Se o usuário pedir uma receita que não seja possível com os ingredientes fornecidos, responda apenas "Não foi possível criar uma receita com esses ingredientes. Tente outros ingredientes.". Também, se o usuário pedir uma receita que seja muito complexa para os ingredientes fornecidos, responda apenas "Com esses ingredientes, só consigo criar receitas bem simples. Tente adicionar mais ingredientes para algo mais elaborado.". Se o usuário pedir uma receita que seja possível, responda seguindo estritamente o formato abaixo, sem variações. Use os ingredientes fornecidos, mas sinta-se livre para ajustar as quantidades e adicionar temperos básicos como sal, pimenta e óleo. O tempo de preparo deve ser estimado com base na complexidade da receita, mas tente manter as receitas simples e rápidas. Seja criativo dentro dessas limitações! Se o usuário não tiver o ingrediente, dê outra opção de receita usando os ingredientes disponíveis. Lembre-se: responda APENAS no formato do exemplo, sem variações, sem introdução e sem conclusão. Seja direto e objetivo.

        Exemplo de formato exigido:
        Nome: Omelete Rápido
        Ingredientes:
        - 2 Ovos
        - Sal a gosto
        Modo de preparo:
        1. Bata os ovos.
        2. Cozinhe na frigideira.
        Tempo: 5 minutos
        [/INST]"""

        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "tinyllama",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.2,  # Baixamos para 0.2 para ele focar estritamente no formato
                    "stop": ["[/INST]", "Usuário:"]
                }
            )
        
        if response.status_code == 200:
            result = response.json()
            receita_gerada = result.get("response", "").strip()
            
            return {
                "sucesso": True,
                "receita": receita_gerada if receita_gerada else "Não foi possível estruturar a receita. Tente outros ingredientes.",
                "modelo": "tinyllama"
            }
        else:
            return {
                "sucesso": False,
                "erro": f"Erro do servidor de IA: {response.status_code}"
            }
    
    except httpx.TimeoutException:
        return {
            "sucesso": False,
            "erro": "O servidor de IA demorou para responder. Tente novamente!"
        }
    except Exception as e:
        print(f"Erro ao gerar receita: {e}")
        return {
            "sucesso": False,
            "erro": "Erro ao processar os ingredientes."
        }
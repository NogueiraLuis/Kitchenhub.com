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
# Railway injeta a variável PORT; padrão local = 8000
PORT = int(os.getenv("PORT", 8000))

engine = create_engine(DATABASE_URL)


# ---- MODELOS ----

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    senha: str  # TODO: usar bcrypt em produção


class ReceitaFavorita(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: int
    titulo: str
    imagem: str
    serve: int = 0
    tempo: int = 0  # 1=massa 2=sobremesa 3=japonesa 4=pizza
    usuario_id: int


# ---- APP ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

# CORS: em produção, substitua "*" pelo domínio do Railway gerado para você
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

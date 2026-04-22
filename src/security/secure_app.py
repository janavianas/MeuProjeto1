"""ShopAgent com autenticacao, protecao SQL e auditoria."""
import os
import asyncio
import re
from dotenv import load_dotenv

_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base, "../../gen/.env"))

api_key = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('"')
os.environ["ANTHROPIC_API_KEY"] = api_key

import chainlit as cl
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from src.security.auth import autenticar, DESCRICOES_PAPEIS
from src.security.audit_log import AuditLogger, criar_tabela_auditoria
from src.security.sql_guard import criar_guard
from src.security.rbac import RBACGuard, POLITICAS

import psycopg2, json
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

DB_URL = "postgresql://shopagent:shopagent@localhost:5432/shopagent"
QDRANT_URL = "http://localhost:6333"
COLLECTION = "shopagent_reviews"

SYSTEM_PROMPT = """Voce e o ShopAgent, assistente de dados de e-commerce.

Ferramentas disponiveis:
- query_ledger: dados exatos (numeros, faturamento, pedidos)
- search_memory: sentimentos e reviews de clientes

Responda sempre em portugues. Seja claro e use tabelas quando apropriado.
IMPORTANTE: Nunca exiba CPF, email, telefone ou dados pessoais nas respostas."""


def criar_system_prompt(papel: str) -> str:
    """Gera system prompt adaptado ao papel do usuario."""
    politica = POLITICAS.get(papel, POLITICAS["viewer"])
    bloqueadas = politica["colunas_bloqueadas"]
    permitidas = politica["tabelas_permitidas"]

    restricoes = ""
    if "total_amount" in bloqueadas or "unit_price" in bloqueadas:
        restricoes += "\n- NAO acesse nem mencione valores financeiros (total_amount, unit_price, price)."
    if "cpf" in bloqueadas:
        restricoes += "\n- NAO acesse nem exiba CPF, email, telefone ou dados pessoais."

    return f"""Voce e o ShopAgent, assistente de dados de e-commerce.

O usuario tem perfil: {papel.upper()}
Tabelas disponiveis: {', '.join(permitidas)}
{f'Restricoes para este perfil:{restricoes}' if restricoes else ''}

Ferramentas disponiveis:
- query_ledger: dados exatos (numeros, pedidos, produtos)
- search_memory: sentimentos e reviews de clientes

Se o usuario pedir algo fora das suas permissoes, explique educadamente
qual e a limitacao do perfil dele e o que ele pode acessar.
Responda sempre em portugues com clareza e tabelas quando apropriado."""


def criar_tools_seguras(user_id: str, user_email: str, papel: str = "viewer"):
    """Cria tools com protecao SQL e auditoria injetadas."""

    guard = criar_guard(user_id)
    rbac  = RBACGuard(papel=papel)
    logger = AuditLogger(user_id=user_id, user_email=user_email)

    @tool
    def query_ledger(sql: str) -> str:
        """Use para dados exatos: faturamento, contagens, pedidos, produtos, clientes.
        Recebe SQL SELECT e retorna dados do Postgres."""
        try:
            # CAMADA 3: Validar SQL (segurança)
            sql_validado = guard.validar(sql)
            # CAMADA 2: Validar permissoes do papel
            sql_validado = rbac.validar_query(sql_validado)
            query_hash = guard.gerar_hash(sql_validado)

            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            cur.execute(sql_validado)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            cur.close()
            conn.close()

            resultado = [dict(zip(cols, row)) for row in rows]

            # Detectar tabelas acessadas
            tabelas = re.findall(r"\bFROM\s+(\w+)", sql_validado.upper())
            tabelas += re.findall(r"\bJOIN\s+(\w+)", sql_validado.upper())

            # CAMADA 5: Registrar acesso bem-sucedido
            logger.registrar_query(
                ferramenta="query_ledger",
                query_hash=query_hash,
                tabelas=[t.lower() for t in tabelas],
                linhas=len(resultado),
                sucesso=True,
            )

            return json.dumps(resultado, default=str, ensure_ascii=False)

        except PermissionError as e:
            # CAMADA 5: Registrar tentativa negada
            logger.registrar_acesso_negado(
                motivo=str(e),
                ferramenta="query_ledger"
            )
            return f"Acesso negado: {str(e)}"

        except Exception as e:
            logger.registrar_query(
                ferramenta="query_ledger",
                query_hash="",
                tabelas=[],
                linhas=0,
                sucesso=False,
                erro=str(e),
            )
            return f"Erro ao consultar banco: {str(e)}"

    @tool
    def search_memory(query: str) -> str:
        """Use para sentimentos, reclamacoes e reviews de clientes.
        Recebe texto e retorna reviews semanticamente similares."""
        try:
            model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")
            embedding = list(model.embed([query]))[0].tolist()

            client = QdrantClient(url=QDRANT_URL)
            results = client.query_points(
                collection_name=COLLECTION,
                query=embedding,
                limit=5,
            )

            reviews = []
            for point in results.points:
                reviews.append({
                    "score": round(point.score, 3),
                    "review": point.payload.get("review_text", ""),
                    "rating": point.payload.get("rating", ""),
                    # Nao retornar customer_id ou dados pessoais
                })

            # CAMADA 5: Registrar busca semantica
            logger.registrar_query(
                ferramenta="search_memory",
                query_hash=guard.gerar_hash(query),
                tabelas=["qdrant:shopagent_reviews"],
                linhas=len(reviews),
                sucesso=True,
            )

            return json.dumps(reviews, default=str, ensure_ascii=False)

        except Exception as e:
            logger.registrar_query(
                ferramenta="search_memory",
                query_hash="",
                tabelas=[],
                linhas=0,
                sucesso=False,
                erro=str(e),
            )
            return f"Erro ao buscar reviews: {str(e)}"

    return [query_ledger, search_memory]


# ─── TELA DE LOGIN ─────────────────────────────────────────────────────
@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    """CAMADA 1: Chainlit chama essa funcao ao fazer login."""
    usuario = autenticar(email=username, senha=password)

    if not usuario:
        return None  # Login recusado

    # Registrar login no audit log
    logger = AuditLogger(user_id=usuario["id"], user_email=usuario["email"])
    logger.registrar_login(sucesso=True)

    return cl.User(
        identifier=usuario["email"],
        metadata={
            "id":    usuario["id"],
            "nome":  usuario["nome"],
            "papel": usuario["papel"],
        }
    )


@cl.on_chat_start
async def on_start():
    """Iniciado apos login bem-sucedido."""
    user = cl.user_session.get("user")
    papel = user.metadata.get("papel", "viewer")
    nome  = user.metadata.get("nome", "Usuario")

    # Criar tools e system prompt adaptados ao papel
    tools = criar_tools_seguras(
        user_id=user.metadata.get("id", user.identifier),
        user_email=user.identifier,
        papel=papel,
    )
    system_prompt = criar_system_prompt(papel)

    llm = ChatAnthropic(
        model="claude-haiku-4-5",
        api_key=api_key,
        temperature=0,
        max_tokens=2048,
    )
    agent = create_react_agent(model=llm, tools=tools, prompt=system_prompt)
    cl.user_session.set("agent", agent)

    desc_papel = DESCRICOES_PAPEIS.get(papel, papel)

    await cl.Message(content=f"""# ShopAgent — Acesso Seguro

Bem-vindo(a), **{nome}**!

Seu perfil: `{desc_papel}`

Todos os acessos sao registrados no log de auditoria.

**Exemplos de perguntas:**
- Qual o faturamento total por estado?
- Quais clientes reclamam de entrega atrasada?
- Top 5 produtos por receita?
""").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Processa mensagem com agent seguro."""
    agent = cl.user_session.get("agent")
    if not agent:
        await cl.Message(content="Sessao expirada. Faca login novamente.").send()
        return

    thinking = cl.Message(content="Processando...")
    await thinking.send()

    try:
        result = await asyncio.to_thread(
            lambda: agent.invoke({"messages": [{"role": "user", "content": message.content}]})
        )
        final = result["messages"][-1].content
        await cl.Message(content=final).send()

    except Exception as e:
        await cl.Message(content=f"Erro ao processar: {str(e)}").send()

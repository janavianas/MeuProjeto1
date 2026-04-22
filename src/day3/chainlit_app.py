"""Passo 10 — Interface de chat com Chainlit para o ShopAgent."""
import os
import asyncio
import traceback
from dotenv import load_dotenv

# Carregar variaveis de ambiente
_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base, "../../gen/.env"))

import chainlit as cl
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from src.day3.tools import query_ledger, search_memory

TOOLS = [query_ledger, search_memory]

SYSTEM_PROMPT = """Voce e o ShopAgent, um assistente especializado em dados de e-commerce.

Voce tem acesso a dois stores de dados:

THE LEDGER (query_ledger): Dados exatos - receita, contagens, medias, pedidos, produtos, clientes.
Use para perguntas sobre numeros: faturamento, quantidade, percentual, ticket medio, ranking.

THE MEMORY (search_memory): Significado - reclamacoes, sentimentos, temas, opiniao de clientes.
Use para perguntas sobre texto: o que clientes dizem, reclamacoes, elogios, problemas relatados.

Para perguntas hibridas, use AMBAS as ferramentas em sequencia.
Responda sempre em portugues, de forma clara e formatada com markdown."""

EXEMPLOS = """**Perguntas sobre The Ledger (numeros exatos):**
- Qual o faturamento total por estado?
- Quantos pedidos foram cancelados?
- Top 10 produtos por receita?
- Distribuicao de pagamentos (pix/cartao/boleto)?

**Perguntas sobre The Memory (sentimentos):**
- Quais clientes reclamam de entrega atrasada?
- Quais sao os principais elogios dos clientes?
- O que os clientes falam sobre qualidade?

**Perguntas hibridas (usa os dois):**
- Top 3 estados com mais reclamacoes e seu faturamento?
- Clientes premium insatisfeitos: qual o ticket medio?"""


@cl.on_chat_start
async def on_start():
    """Executado quando o usuario abre o chat."""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        print(f"[DEBUG] ANTHROPIC_API_KEY carregada: {'SIM' if api_key else 'NAO'}")

        llm = ChatAnthropic(
            model="claude-haiku-4-5",
            api_key=api_key,
            temperature=0,
            max_tokens=2048,
        )
        agent = create_react_agent(model=llm, tools=TOOLS, prompt=SYSTEM_PROMPT)

        # Salvar o agente na sessao do usuario
        cl.user_session.set("agent", agent)
        print("[DEBUG] Agente criado com sucesso")

        # Mensagem de boas-vindas
        await cl.Message(
            content=f"""# ShopAgent

Ola! Sou o ShopAgent, seu assistente de dados de e-commerce.

Tenho acesso a:
- **The Ledger** (Postgres): dados exatos de pedidos, clientes e produtos
- **The Memory** (Qdrant): reviews e sentimentos dos clientes

{EXEMPLOS}

Como posso ajudar?"""
        ).send()

    except Exception as e:
        print(f"[ERRO no_start] {traceback.format_exc()}")
        await cl.Message(content=f"Erro ao iniciar o agente: {str(e)}").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Executado a cada mensagem do usuario."""
    try:
        agent = cl.user_session.get("agent")
        if agent is None:
            await cl.Message(content="Erro: agente nao inicializado. Recarregue a pagina.").send()
            return

        print(f"[DEBUG] Pergunta recebida: {message.content}")

        # Rodar o agente em thread separada
        def run_agent():
            return agent.invoke({"messages": [{"role": "user", "content": message.content}]})

        result = await asyncio.to_thread(run_agent)
        print("[DEBUG] Agente respondeu com sucesso")

        # Identificar quais tools foram usadas
        tool_calls = [
            m for m in result["messages"]
            if hasattr(m, "name") and m.name in ["query_ledger", "search_memory"]
        ]
        tools_used = list(set([m.name for m in tool_calls]))

        # Resposta final
        final = result["messages"][-1].content

        # Mostrar quais stores foram consultados
        stores_info = ""
        if tools_used:
            stores = []
            if "query_ledger" in tools_used:
                stores.append("The Ledger (Postgres)")
            if "search_memory" in tools_used:
                stores.append("The Memory (Qdrant)")
            stores_info = f"\n\n---\n*Stores consultados: {', '.join(stores)}*"

        await cl.Message(content=final + stores_info).send()

    except Exception as e:
        print(f"[ERRO on_message] {traceback.format_exc()}")
        await cl.Message(content=f"Erro ao processar pergunta: {str(e)}").send()

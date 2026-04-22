"""Passo 9 — ShopAgent com LangGraph ReAct + Claude."""
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from src.day3.tools import query_ledger, search_memory

# Carregar variaveis de ambiente
_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base, "../../gen/.env"))

# Ferramentas do agente
TOOLS = [query_ledger, search_memory]

# System prompt — instrucoes que guiam o roteamento
SYSTEM_PROMPT = """Voce e o ShopAgent, um assistente especializado em dados de e-commerce.

Voce tem acesso a dois stores de dados:

THE LEDGER (query_ledger): Dados exatos — receita, contagens, medias, pedidos, produtos, clientes.
Use para perguntas sobre numeros: faturamento, quantidade, percentual, ticket medio, ranking.

THE MEMORY (search_memory): Significado — reclamacoes, sentimentos, temas, opiniao de clientes.
Use para perguntas sobre texto: o que clientes dizem, reclamacoes, elogios, problemas relatados.

Para perguntas hibridas, use AMBAS as ferramentas em sequencia.
Responda sempre em portugues, de forma clara e formatada."""


def create_shop_agent():
    llm = ChatAnthropic(
        model="claude-haiku-4-5",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0,
        max_tokens=2048,
    )
    return create_react_agent(
        model=llm,
        tools=TOOLS,
        prompt=SYSTEM_PROMPT,
    )


def run_tests():
    print("=" * 60)
    print("PASSO 9 - SHOPAGENT (LangGraph ReAct + Claude)")
    print("=" * 60)

    agent = create_shop_agent()

    perguntas = [
        "Qual o faturamento total por estado? Mostre os top 5.",
        "Quais clientes reclamam de entrega atrasada?",
        "Quais os top 3 estados com mais reclamacoes e qual o faturamento de cada um?",
    ]

    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n{'='*60}")
        print(f"PERGUNTA {i}: {pergunta}")
        print("=" * 60)

        messages = [{"role": "user", "content": pergunta}]
        result = agent.invoke({"messages": messages})

        # Pegar a ultima mensagem (resposta final)
        final = result["messages"][-1].content
        print(f"\nRESPOSTA FINAL:\n{final}".encode("ascii", "replace").decode("ascii"))

        # Mostrar quais tools foram usadas
        tool_calls = [
            m for m in result["messages"]
            if hasattr(m, "name") and m.name in ["query_ledger", "search_memory"]
        ]
        if tool_calls:
            print(f"\nTools usadas: {[m.name for m in tool_calls]}")


if __name__ == "__main__":
    run_tests()

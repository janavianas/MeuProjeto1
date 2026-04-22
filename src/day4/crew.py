"""Passo 15 - ShopCrew: orquestracao do time de agentes."""
import os
import sys
from dotenv import load_dotenv
from crewai import Crew, Process

# Carregar variaveis de ambiente
_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base, "../../gen/.env"))

# Garantir que a API key esta disponivel para o CrewAI
api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key:
    os.environ["ANTHROPIC_API_KEY"] = api_key

from src.day4.tasks import create_tasks


def run_shop_crew(pergunta: str) -> str:
    """Executa o ShopCrew para responder uma pergunta de negocio."""

    print("\n" + "=" * 65)
    print("SHOPCREW INICIANDO")
    print("=" * 65)
    print(f"Pergunta: {pergunta}")
    print("=" * 65 + "\n")

    # Criar as tasks (que ja criam os agentes internamente)
    tasks = create_tasks(pergunta)

    # Extrair os agentes das tasks
    agentes = list({task.agent for task in tasks})

    # Montar o Crew
    crew = Crew(
        agents=agentes,
        tasks=tasks,
        process=Process.sequential,  # Tasks executam em sequencia
        verbose=True,
    )

    # Executar!
    resultado = crew.kickoff()

    print("\n" + "=" * 65)
    print("SHOPCREW FINALIZADO")
    print("=" * 65)

    return str(resultado)


if __name__ == "__main__":
    # Perguntas de teste
    perguntas = [
        "Quais os 3 estados com maior faturamento e o que os clientes de la falam?",
    ]

    pergunta = perguntas[0]
    if len(sys.argv) > 1:
        pergunta = " ".join(sys.argv[1:])

    resultado = run_shop_crew(pergunta)

    print("\n")
    print("=" * 65)
    print("RELATORIO FINAL")
    print("=" * 65)
    print(resultado)

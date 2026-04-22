"""Passo 16 - Avaliacao de qualidade com DeepEval."""
import os
from dotenv import load_dotenv

# Carregar variaveis de ambiente
_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base, "../../gen/.env"))

api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key:
    os.environ["ANTHROPIC_API_KEY"] = api_key

from deepeval import evaluate
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric,
)
from deepeval.test_case import LLMTestCase
from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_anthropic import ChatAnthropic


class AnthropicWrapper(DeepEvalBaseLLM):
    """Wrapper para usar Claude como modelo de avaliacao no DeepEval."""

    def __init__(self):
        self.model = ChatAnthropic(
            model="claude-haiku-4-5",
            api_key=api_key,
            temperature=0,
        )

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        response = self.model.invoke(prompt)
        return response.content

    async def a_generate(self, prompt: str) -> str:
        response = await self.model.ainvoke(prompt)
        return response.content

    def get_model_name(self) -> str:
        return "claude-haiku-4-5"


def avaliar_resposta(pergunta: str, resposta: str, contextos: list[str]) -> None:
    """Avalia a qualidade de uma resposta do ShopCrew."""

    print("\n" + "=" * 65)
    print("DEEPEVAL - AVALIACAO DE QUALIDADE")
    print("=" * 65)
    print(f"Pergunta: {pergunta}")
    print(f"Resposta (primeiros 200 chars): {resposta[:200]}...")
    print("=" * 65 + "\n")

    modelo = AnthropicWrapper()

    # Caso de teste
    test_case = LLMTestCase(
        input=pergunta,
        actual_output=resposta,
        retrieval_context=contextos,
    )

    # Metricas de avaliacao
    metricas = [
        AnswerRelevancyMetric(
            threshold=0.7,
            model=modelo,
            verbose_mode=True,
        ),
        FaithfulnessMetric(
            threshold=0.7,
            model=modelo,
            verbose_mode=True,
        ),
        ContextualRelevancyMetric(
            threshold=0.7,
            model=modelo,
            verbose_mode=True,
        ),
    ]

    # Executar avaliacao
    print("Avaliando com 3 metricas:")
    print("  1. AnswerRelevancy   - a resposta e relevante para a pergunta?")
    print("  2. Faithfulness      - a resposta e fiel aos dados?")
    print("  3. ContextualRelevancy - o contexto e relevante?")
    print()

    evaluate(test_cases=[test_case], metrics=metricas)


if __name__ == "__main__":
    # Exemplo de avaliacao com dados simulados
    pergunta = "Quais os 3 estados com maior faturamento?"

    resposta = """
    ## Relatorio de Faturamento por Estado

    Os 3 estados com maior faturamento sao:

    | Estado | Faturamento |
    |--------|-------------|
    | SP     | R$ 450.000  |
    | RJ     | R$ 280.000  |
    | MG     | R$ 190.000  |

    Sao Paulo lidera com folga, representando 45% do faturamento total.
    """

    contextos = [
        "SP teve faturamento de R$ 450.000 no periodo analisado.",
        "RJ registrou R$ 280.000 em vendas totais.",
        "MG acumulou R$ 190.000 em receita.",
        "Os dados foram extraidos da tabela orders do banco Postgres.",
    ]

    avaliar_resposta(pergunta, resposta, contextos)

"""Passo 17 - Monitoramento com LangFuse v2."""
import os
import time
from dotenv import load_dotenv

# Carregar variaveis de ambiente
_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base, "../../gen/.env"))

def _limpar(valor):
    return valor.strip().strip('"').strip("'") if valor else ""

# LangFuse v2 usa variaveis de ambiente para configuracao
os.environ["ANTHROPIC_API_KEY"]   = _limpar(os.getenv("ANTHROPIC_API_KEY", ""))
os.environ["LANGFUSE_SECRET_KEY"] = _limpar(os.getenv("LANGFUSE_SECRET_KEY", ""))
os.environ["LANGFUSE_PUBLIC_KEY"] = _limpar(os.getenv("LANGFUSE_PUBLIC_KEY", ""))
os.environ["LANGFUSE_HOST"]       = _limpar(os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"))

from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context
from src.day4.crew import run_shop_crew

# Cliente para forcar envio dos traces
_langfuse_client = Langfuse(
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    host=os.environ["LANGFUSE_HOST"],
)


@observe()
def run_com_monitoramento(pergunta: str) -> str:
    """Executa o ShopCrew com rastreamento no LangFuse."""

    # Adicionar metadados ao trace
    langfuse_context.update_current_trace(
        name="shopcrew-run",
        tags=["shopcrew", "day4"],
        metadata={
            "projeto": "ShopAgent",
            "versao": "1.0",
        },
    )

    print(f"\nMonitoramento ativo! Acompanhe em: https://cloud.langfuse.com")
    print(f"Pergunta: {pergunta}\n")

    inicio = time.time()

    resultado = run_shop_crew(pergunta)

    duracao = round(time.time() - inicio, 2)
    print(f"\nTempo total: {duracao}s")
    print("Trace enviado ao LangFuse!")

    return resultado


if __name__ == "__main__":
    pergunta = "Quais produtos tem mais reclamacoes e qual o faturamento deles?"

    resultado = run_com_monitoramento(pergunta)

    # Forcar envio dos traces antes de sair
    print("\nEnviando traces ao LangFuse...")
    _langfuse_client.flush()
    print("Traces enviados! Verifique em: https://cloud.langfuse.com")

    print("\n" + "=" * 65)
    print("RELATORIO FINAL")
    print("=" * 65)
    print(resultado)

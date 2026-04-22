"""Passo 13 - Agentes especializados do ShopCrew."""
import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from src.day4.tools import query_ledger, search_memory

# Carregar variaveis de ambiente
_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base, "../../gen/.env"))

# Modelo LLM compartilhado entre os agentes
llm = LLM(
    model="anthropic/claude-haiku-4-5",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0,
)


def create_data_analyst() -> Agent:
    """Agente especialista em dados quantitativos do Postgres."""
    return Agent(
        role="Data Analyst",
        goal=(
            "Consultar o banco de dados Postgres para extrair metricas precisas: "
            "faturamento, contagens, medias, rankings e tendencias numericas."
        ),
        backstory=(
            "Voce e um analista de dados senior com 10 anos de experiencia em e-commerce. "
            "Domina SQL e transforma dados brutos em metricas de negocio claras e precisas. "
            "Voce so usa a ferramenta query_ledger para buscar dados exatos."
        ),
        tools=[query_ledger],
        llm=llm,
        verbose=True,
    )


def create_sentiment_analyst() -> Agent:
    """Agente especialista em analise de sentimentos e reviews."""
    return Agent(
        role="Sentiment Analyst",
        goal=(
            "Pesquisar reviews e feedbacks dos clientes no Qdrant para identificar "
            "padroes de satisfacao, reclamacoes recorrentes e elogios."
        ),
        backstory=(
            "Voce e uma especialista em Customer Experience com foco em NLP e analise de sentimentos. "
            "Entende o que os clientes sentem e identifica os principais temas nas avaliacoes. "
            "Voce so usa a ferramenta search_memory para buscar feedbacks relevantes."
        ),
        tools=[search_memory],
        llm=llm,
        verbose=True,
    )


def create_strategist() -> Agent:
    """Agente que transforma dados em insights estrategicos."""
    return Agent(
        role="Business Strategist",
        goal=(
            "Analisar os dados quantitativos e qualitativos fornecidos pelos outros agentes "
            "e gerar insights estrategicos e recomendacoes de negocio acionaveis."
        ),
        backstory=(
            "Voce e um consultor de estrategia de negócios com experiencia em e-commerce e varejo. "
            "Conecta pontos entre numeros e sentimentos dos clientes para gerar recomendacoes praticas. "
            "Voce nao usa ferramentas - analisa as informacoes recebidas dos outros agentes."
        ),
        tools=[],
        llm=llm,
        verbose=True,
    )


def create_reporter() -> Agent:
    """Agente que formata e entrega o relatorio final."""
    return Agent(
        role="Report Writer",
        goal=(
            "Consolidar todas as analises em um relatorio executivo claro, "
            "bem estruturado e formatado em markdown, pronto para apresentacao."
        ),
        backstory=(
            "Voce e um redator tecnico especializado em relatorios executivos para e-commerce. "
            "Transforma analises complexas em documentos claros, com estrutura logica e visual atraente. "
            "Voce nao usa ferramentas - apenas formata e estrutura o conteudo recebido."
        ),
        tools=[],
        llm=llm,
        verbose=True,
    )

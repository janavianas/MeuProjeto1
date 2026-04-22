"""Passo 14 - Tasks do ShopCrew: o que cada agente deve fazer."""
from crewai import Task
from src.day4.agents import (
    create_data_analyst,
    create_sentiment_analyst,
    create_strategist,
    create_reporter,
)


def create_tasks(pergunta: str):
    """Cria os agentes e as tasks para responder a pergunta do usuario."""

    # Instanciar os agentes
    data_analyst = create_data_analyst()
    sentiment_analyst = create_sentiment_analyst()
    strategist = create_strategist()
    reporter = create_reporter()

    # Task 1: Analise quantitativa (Postgres)
    task_dados = Task(
        description=(
            f"O usuario perguntou: '{pergunta}'\n\n"
            "Consulte o banco de dados Postgres usando a ferramenta query_ledger "
            "para extrair os dados numericos relevantes para responder essa pergunta. "
            "Inclua metricas como faturamento, contagens, percentuais e rankings conforme necessario. "
            "Retorne os dados de forma organizada com numeros exatos."
        ),
        expected_output=(
            "Relatorio de dados quantitativos com metricas numericas precisas, "
            "tabelas e rankings relevantes para a pergunta do usuario."
        ),
        agent=data_analyst,
    )

    # Task 2: Analise qualitativa (Qdrant)
    task_sentimentos = Task(
        description=(
            f"O usuario perguntou: '{pergunta}'\n\n"
            "Pesquise os reviews e feedbacks dos clientes usando a ferramenta search_memory "
            "para identificar sentimentos, reclamacoes e elogios relacionados a pergunta. "
            "Faca buscas com diferentes termos relevantes para cobrir bem o tema. "
            "Retorne os principais temas encontrados com exemplos reais dos clientes."
        ),
        expected_output=(
            "Analise de sentimentos com os principais temas positivos e negativos, "
            "reclamacoes recorrentes e exemplos de feedback dos clientes."
        ),
        agent=sentiment_analyst,
    )

    # Task 3: Insights estrategicos (sem ferramentas)
    task_estrategia = Task(
        description=(
            f"O usuario perguntou: '{pergunta}'\n\n"
            "Com base nos dados quantitativos e na analise de sentimentos fornecidos, "
            "gere 3 a 5 insights estrategicos e recomendacoes acionaveis de negocio. "
            "Conecte os numeros com os sentimentos dos clientes para insights mais ricos. "
            "Seja especifico e pratico - evite recomendacoes genericas."
        ),
        expected_output=(
            "Lista de 3 a 5 insights estrategicos claros e acionaveis, "
            "cada um conectando dados quantitativos com feedback qualitativo."
        ),
        agent=strategist,
        context=[task_dados, task_sentimentos],
    )

    # Task 4: Relatorio final (sem ferramentas)
    task_relatorio = Task(
        description=(
            f"O usuario perguntou: '{pergunta}'\n\n"
            "Consolide todas as analises anteriores em um relatorio executivo completo em markdown. "
            "Use a seguinte estrutura:\n"
            "1. Resumo Executivo (2-3 linhas)\n"
            "2. Dados Quantitativos (tabelas e numeros)\n"
            "3. Voz do Cliente (sentimentos e exemplos)\n"
            "4. Insights Estrategicos (recomendacoes)\n"
            "5. Proximos Passos (acoes concretas)\n\n"
            "Use markdown com headers, tabelas e listas para facilitar a leitura."
        ),
        expected_output=(
            "Relatorio executivo completo em markdown com todas as secoes preenchidas, "
            "pronto para ser apresentado a stakeholders."
        ),
        agent=reporter,
        context=[task_dados, task_sentimentos, task_estrategia],
    )

    return [task_dados, task_sentimentos, task_estrategia, task_relatorio]

"""Passo 13b - Tools no formato CrewAI (diferente do LangChain do Dia 3)."""
import os
import json
import psycopg2
from dotenv import load_dotenv
from crewai.tools import BaseTool
from pydantic import Field

# Carregar variaveis de ambiente
_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base, "../../gen/.env"))

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://shopagent:shopagent@localhost:5432/shopagent"
)
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "shopagent_reviews")


class QueryLedgerTool(BaseTool):
    name: str = "query_ledger"
    description: str = (
        "Use para dados exatos: faturamento, contagens, medias, pedidos, produtos, clientes. "
        "Recebe uma query SQL e retorna os resultados do Postgres. "
        "Exemplo: SELECT state, SUM(total_amount) FROM orders GROUP BY state ORDER BY 2 DESC LIMIT 5"
    )

    def _run(self, sql: str) -> str:
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            cur.close()
            conn.close()
            result = [dict(zip(cols, row)) for row in rows]
            return json.dumps(result, default=str, ensure_ascii=False)
        except Exception as e:
            return f"Erro ao consultar Postgres: {str(e)}"


class SearchMemoryTool(BaseTool):
    name: str = "search_memory"
    description: str = (
        "Use para significado: reclamacoes, sentimentos, temas, opiniao de clientes. "
        "Recebe uma query em texto e retorna reviews semanticamente similares do Qdrant. "
        "Exemplo: 'entrega atrasada produto danificado' ou 'excelente qualidade recomendo'"
    )

    def _run(self, query: str) -> str:
        try:
            from qdrant_client import QdrantClient
            from fastembed import TextEmbedding

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
                    "customer_id": str(point.payload.get("customer_id", "")),
                })
            return json.dumps(reviews, default=str, ensure_ascii=False)
        except Exception as e:
            return f"Erro ao buscar no Qdrant: {str(e)}"


# Instancias prontas para usar
query_ledger = QueryLedgerTool()
search_memory = SearchMemoryTool()

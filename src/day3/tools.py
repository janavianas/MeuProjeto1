"""Passo 8 — LangChain Tools: query_ledger + search_memory."""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from langchain_core.tools import tool
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

# Configuracoes
PG = dict(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", 5432)),
    dbname=os.getenv("POSTGRES_DB", "shopagent"),
    user=os.getenv("POSTGRES_USER", "shopagent"),
    password=os.getenv("POSTGRES_PASSWORD", "shopagent"),
)
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "shopagent_reviews")

# Inicializar modelo de embedding (carregado uma vez)
_embed_model = None


def get_embed_model() -> TextEmbedding:
    global _embed_model
    if _embed_model is None:
        _embed_model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")
    return _embed_model


@tool
def query_ledger(sql: str) -> str:
    """Use for exact data: revenue, counts, averages, orders, products, customers.
    Examples: total revenue by state, order counts, payment distribution,
    top products by sales, customer segment analysis, cancellation rates.
    Input: a valid PostgreSQL SELECT query.
    Tables: customers(customer_id, name, email, city, state, segment),
            products(product_id, name, category, price, brand),
            orders(order_id, customer_id, product_id, qty, total, status, payment, created_at).
    """
    try:
        conn = psycopg2.connect(**PG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if not rows:
            return "Nenhum resultado encontrado."
        # Converter para lista de dicts
        result = [dict(r) for r in rows]
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return f"Erro ao executar SQL: {str(e)}"


@tool
def search_memory(query: str) -> str:
    """Use for meaning: complaints, sentiment, review themes, customer opinions.
    Examples: customers complaining about late delivery, positive reviews about quality,
    problems with shipping, what customers say about a product, negative experiences.
    Input: a natural language query describing what you are looking for.
    Returns top 5 most semantically similar customer reviews.
    """
    try:
        model = get_embed_model()
        client = QdrantClient(url=QDRANT_URL)
        vector = list(model.embed([query]))[0].tolist()
        results = client.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=5,
            with_payload=True,
        ).points
        reviews = []
        for r in results:
            p = r.payload
            reviews.append({
                "score": round(r.score, 3),
                "rating": p.get("rating"),
                "sentiment": p.get("sentiment"),
                "comment": p.get("comment"),
                "order_id": p.get("order_id"),
            })
        return json.dumps(reviews, ensure_ascii=False)
    except Exception as e:
        return f"Erro na busca semantica: {str(e)}"

"""Passo 7 — Verificar colecao Qdrant criada corretamente."""
import json
import os
import requests
from qdrant_client import QdrantClient

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "shopagent_reviews")
REVIEWS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "../../gen/data/reviews/reviews.jsonl")


def check_collection_info():
    """1. Info da colecao via HTTP."""
    resp = requests.get(f"{QDRANT_URL}/collections/{COLLECTION}")
    data = resp.json()["result"]
    cfg  = data["config"]["params"]["vectors"]
    print("  Status    :", data["status"])
    print("  Pontos    :", data["points_count"])
    print("  Segmentos :", data["segments_count"])
    print("  Tam. vetor:", cfg["size"])
    print("  Distancia :", cfg["distance"])
    return data["points_count"]


def sample_point(client: QdrantClient):
    """2. Inspecionar um ponto de exemplo."""
    results = client.query_points(
        collection_name=COLLECTION,
        query=[0.0] * 768,
        limit=1,
        with_payload=True,
        with_vectors=False,
    ).points
    if results:
        p = results[0].payload
        print("  ID        :", results[0].id)
        print("  review_id :", p.get("review_id"))
        print("  order_id  :", p.get("order_id"))
        print("  rating    :", p.get("rating"))
        print("  sentiment :", p.get("sentiment"))
        print("  comment   :", p.get("comment", "")[:60] + "...")


def compare_counts(points_count: int):
    """3. Comparar reviews JSONL vs pontos no Qdrant."""
    jsonl_count = sum(1 for _ in open(REVIEWS_PATH, encoding="utf-8"))
    print(f"  Reviews no JSONL : {jsonl_count}")
    print(f"  Pontos no Qdrant : {points_count}")
    if jsonl_count == points_count:
        print("  Resultado        : OK - todos os reviews foram indexados!")
    else:
        diff = jsonl_count - points_count
        print(f"  Resultado        : ATENCAO - {diff} reviews faltando!")


def main():
    print("=" * 55)
    print("PASSO 7 - VERIFICACAO DA COLECAO QDRANT")
    print("=" * 55)

    client = QdrantClient(url=QDRANT_URL)

    print("\n1. INFO DA COLECAO")
    print("-" * 40)
    points_count = check_collection_info()

    print("\n2. AMOSTRA DE UM PONTO")
    print("-" * 40)
    sample_point(client)

    print("\n3. JSONL vs QDRANT")
    print("-" * 40)
    compare_counts(points_count)

    print("\n" + "=" * 55)
    print("Verificacao concluida!")
    print("=" * 55)


if __name__ == "__main__":
    main()

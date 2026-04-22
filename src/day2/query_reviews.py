"""Passo 6 — Busca semantica no Qdrant (The Memory)."""
import os
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "shopagent_reviews")
TOP_K = 5


def search(client: QdrantClient, model: TextEmbedding, query: str) -> list:
    vector = list(model.embed([query]))[0].tolist()
    results = client.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=TOP_K,
        with_payload=True,
    ).points
    return results


def print_results(query: str, results: list) -> None:
    print(f"\n  Busca: \"{query}\"")
    print(f"  {'-' * 52}")
    for i, r in enumerate(results, 1):
        p = r.payload
        score = r.score
        sentiment_icon = {"positive": "[+]", "neutral": "[~]", "negative": "[-]"}.get(p["sentiment"], "[?]")
        print(f"  {i}. [{score:.3f}] Rating:{p['rating']} {sentiment_icon} {p['sentiment']}")
        print(f"     \"{p['comment']}\"")


def main():
    print("=" * 55)
    print("PASSO 6 - BUSCA SEMANTICA (The Memory)")
    print("=" * 55)

    print("\nCarregando modelo e conectando ao Qdrant...")
    model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")
    client = QdrantClient(url=QDRANT_URL)
    print("Pronto!\n")

    queries = [
        "Clientes reclamando de entrega atrasada",
        "Reviews positivos sobre qualidade do produto",
        "Problemas com pagamento ou frete caro",
    ]

    print("=" * 55)
    print("RESULTADOS DA BUSCA SEMANTICA")
    print("=" * 55)

    for query in queries:
        results = search(client, model, query)
        print_results(query, results)

    print()
    print("=" * 55)
    print("DEMONSTRACAO: O que o SQL nao consegue fazer")
    print("=" * 55)
    query = "produto que nao chegou no endereco"
    results = search(client, model, query)
    print_results(query, results)
    print()
    print("  Note: a busca encontrou reviews com significado")
    print("  similar mesmo usando palavras diferentes!")


if __name__ == "__main__":
    main()

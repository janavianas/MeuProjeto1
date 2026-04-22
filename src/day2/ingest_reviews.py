"""Passo 5 — Pipeline RAG: carrega reviews no Qdrant (The Memory).
Usa qdrant-client + fastembed diretamente (compativel com Python 3.14).
"""
import json
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

QDRANT_URL  = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION  = os.getenv("QDRANT_COLLECTION", "shopagent_reviews")
REVIEWS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "../../gen/data/reviews/reviews.jsonl")
VECTOR_SIZE = 768   # BAAI/bge-base-en-v1.5
BATCH_SIZE  = 50


def load_reviews(path: str) -> list[dict]:
    reviews = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            reviews.append(json.loads(line))
    return reviews


def create_collection(client: QdrantClient) -> None:
    """Cria a colecao no Qdrant (apaga se ja existir)."""
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION in existing:
        print(f"  Colecao '{COLLECTION}' ja existe — recriando...")
        client.delete_collection(COLLECTION)

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    print(f"  Colecao '{COLLECTION}' criada (vetores de {VECTOR_SIZE} dimensoes, distancia COSINE)")


def ingest(client: QdrantClient, reviews: list[dict], model: TextEmbedding) -> None:
    """Gera embeddings e insere no Qdrant em batches."""
    total = len(reviews)
    inserted = 0

    for i in range(0, total, BATCH_SIZE):
        batch = reviews[i:i + BATCH_SIZE]
        texts = [r["comment"] for r in batch]

        # Gerar embeddings (lista de vetores)
        vectors = list(model.embed(texts))

        # Montar pontos para o Qdrant
        points = [
            PointStruct(
                id=idx + i,
                vector=vectors[idx].tolist(),
                payload={
                    "review_id": r["review_id"],
                    "order_id":  r["order_id"],
                    "rating":    r["rating"],
                    "comment":   r["comment"],
                    "sentiment": r["sentiment"],
                }
            )
            for idx, r in enumerate(batch)
        ]

        client.upsert(collection_name=COLLECTION, points=points)
        inserted += len(batch)
        print(f"  Indexados: {inserted}/{total}", end="\r")

    print(f"  Indexados: {inserted}/{total} — concluido!")


def verify_collection(client: QdrantClient) -> None:
    info = client.get_collection(COLLECTION)
    print(f"\n  Colecao      : {COLLECTION}")
    print(f"  Pontos       : {info.points_count}")
    print(f"  Tamanho vetor: {info.config.params.vectors.size}")
    print(f"  Distancia    : {info.config.params.vectors.distance}")


def main():
    print("=" * 55)
    print("PASSO 5 - RAG INGEST PIPELINE (The Memory)")
    print("=" * 55)

    # 1. Carregar reviews
    print(f"\n1. Carregando reviews...")
    reviews = load_reviews(REVIEWS_PATH)
    print(f"   {len(reviews)} reviews carregados")

    # 2. Carregar modelo de embedding
    print("\n2. Carregando modelo de embedding (BAAI/bge-base-en-v1.5)...")
    print("   (Modelo ja baixado anteriormente)")
    model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")
    print("   Modelo pronto!")

    # 3. Conectar ao Qdrant e criar colecao
    print(f"\n3. Conectando ao Qdrant ({QDRANT_URL})...")
    client = QdrantClient(url=QDRANT_URL)
    create_collection(client)

    # 4. Indexar reviews
    print("\n4. Gerando embeddings e indexando no Qdrant...")
    ingest(client, reviews, model)

    # 5. Verificar colecao
    print("\n5. Verificando colecao criada:")
    verify_collection(client)

    print("\n" + "=" * 55)
    print("The Memory esta pronta! Reviews indexados no Qdrant.")
    print("=" * 55)


if __name__ == "__main__":
    main()

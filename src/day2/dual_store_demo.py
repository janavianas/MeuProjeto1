"""Passo 10 — Demo dual store: Qdrant + Postgres juntos."""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

QDRANT_URL  = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION  = os.getenv("QDRANT_COLLECTION", "shopagent_reviews")
PG = dict(host="localhost", port=5432, dbname="shopagent",
          user="shopagent", password="shopagent")


def semantic_search(client, model, query, top_k=10):
    vector = list(model.embed([query]))[0].tolist()
    return client.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=top_k,
        with_payload=True,
    ).points


def main():
    print("=" * 60)
    print("PASSO 10 - DEMO DUAL STORE (Ledger + Memory)")
    print("=" * 60)

    model  = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")
    qclient = QdrantClient(url=QDRANT_URL)
    pgconn  = psycopg2.connect(**PG)
    pgcur   = pgconn.cursor(cursor_factory=RealDictCursor)

    # ----------------------------------------------------------
    # PERGUNTA 1: Clientes do Sudeste que reclamam de entrega
    # Passo 1: Qdrant -> encontrar reviews negativos de entrega
    # Passo 2: Postgres -> filtrar por estado do Sudeste
    # ----------------------------------------------------------
    print("\n[1] Clientes do Sudeste que reclamam de entrega")
    print("-" * 60)

    results = semantic_search(qclient, model, "entrega atrasada nao recebi produto", top_k=20)
    order_ids = [r.payload["order_id"] for r in results if r.payload["sentiment"] == "negative"]

    if order_ids:
        pgcur.execute("""
            SELECT DISTINCT c.name, c.state, c.segment, o.total
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_id = ANY(%s::uuid[])
              AND c.state IN ('SP', 'RJ', 'MG')
            ORDER BY o.total DESC
            LIMIT 5
        """, (order_ids,))
        rows = pgcur.fetchall()
        if rows:
            print(f"  {'Nome':<30} {'Estado':<8} {'Segmento':<10} {'Ticket':>10}")
            print(f"  {'-'*30} {'-'*8} {'-'*10} {'-'*10}")
            for r in rows:
                print(f"  {r['name']:<30} {r['state']:<8} {r['segment']:<10} R$ {float(r['total']):>7,.2f}")
        else:
            print("  Nenhum cliente do Sudeste encontrado nessa amostra.")
    else:
        print("  Nenhum review negativo encontrado.")

    # ----------------------------------------------------------
    # PERGUNTA 2: Ticket medio dos clientes com reclamacoes
    # ----------------------------------------------------------
    print("\n[2] Ticket medio dos clientes com reclamacoes de entrega")
    print("-" * 60)

    results = semantic_search(qclient, model, "entrega problema atraso nao chegou", top_k=50)
    all_order_ids = [r.payload["order_id"] for r in results]

    if all_order_ids:
        pgcur.execute("""
            SELECT
                c.segment,
                COUNT(DISTINCT c.customer_id) AS clientes,
                ROUND(AVG(o.total)::numeric, 2) AS ticket_medio
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_id = ANY(%s::uuid[])
            GROUP BY c.segment
            ORDER BY ticket_medio DESC
        """, (all_order_ids,))
        rows = pgcur.fetchall()
        print(f"  {'Segmento':<12} {'Clientes':>10} {'Ticket Medio':>14}")
        print(f"  {'-'*12} {'-'*10} {'-'*14}")
        for r in rows:
            print(f"  {r['segment']:<12} {r['clientes']:>10} R$ {float(r['ticket_medio']):>10,.2f}")

    # ----------------------------------------------------------
    # PERGUNTA 3: Top 3 estados com mais reclamacoes + faturamento
    # ----------------------------------------------------------
    print("\n[3] Top 3 estados com reclamacoes e seu faturamento")
    print("-" * 60)

    results = semantic_search(qclient, model, "reclamacao problema insatisfeito ruim", top_k=100)
    neg_order_ids = [r.payload["order_id"] for r in results if r.payload["sentiment"] == "negative"]

    if neg_order_ids:
        pgcur.execute("""
            SELECT
                c.state,
                COUNT(o.order_id)               AS reclamacoes,
                ROUND(SUM(o.total)::numeric, 2) AS faturamento
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_id = ANY(%s::uuid[])
            GROUP BY c.state
            ORDER BY reclamacoes DESC
            LIMIT 3
        """, (neg_order_ids,))
        rows = pgcur.fetchall()
        print(f"  {'Estado':<8} {'Reclamacoes':>12} {'Faturamento':>15}")
        print(f"  {'-'*8} {'-'*12} {'-'*15}")
        for r in rows:
            print(f"  {r['state']:<8} {r['reclamacoes']:>12} R$ {float(r['faturamento']):>11,.2f}")

    # ----------------------------------------------------------
    # PERGUNTA 4: Resumo executivo
    # ----------------------------------------------------------
    print("\n[4] Resumo executivo")
    print("-" * 60)

    pgcur.execute("SELECT COUNT(*) as total, ROUND(SUM(total)::numeric,2) as receita FROM orders WHERE status='cancelled'")
    cancelados = pgcur.fetchone()

    pgcur.execute("SELECT ROUND(AVG(total)::numeric,2) as ticket FROM orders")
    ticket = pgcur.fetchone()

    neg_count = sum(1 for r in results if r.payload["sentiment"] == "negative")

    print(f"""
  Pedidos cancelados   : {cancelados['total']} (R$ {float(cancelados['receita']):,.2f} em receita perdida)
  Ticket medio geral   : R$ {float(ticket['ticket']):,.2f}
  Reviews negativos    : {neg_count} encontrados na busca semantica
  Principais problemas : entrega atrasada, produto nao recebido

  Recomendacao: revisar processo logistico nos estados RS e PR,
  que lideram em volume de pedidos e concentram reclamacoes.
    """)

    pgcur.close()
    pgconn.close()
    print("=" * 60)
    print("Demo concluida! Voce usou os DOIS stores em conjunto.")
    print("=" * 60)


if __name__ == "__main__":
    main()

"""Passo 4 — The Ledger: queries de negocio no Postgres."""
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    return psycopg2.connect(
        host="localhost", port=5432,
        dbname="shopagent", user="shopagent", password="shopagent"
    )


def revenue_by_state(cur, top=5):
    cur.execute("""
        SELECT c.state,
               COUNT(o.order_id)          AS pedidos,
               COUNT(DISTINCT c.customer_id) AS clientes,
               ROUND(SUM(o.total)::numeric, 2) AS receita_total
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.state
        ORDER BY receita_total DESC
        LIMIT %s
    """, (top,))
    return cur.fetchall()


def order_status_distribution(cur):
    cur.execute("""
        SELECT status,
               COUNT(*) AS total,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
        FROM orders
        GROUP BY status
        ORDER BY total DESC
    """)
    return cur.fetchall()


def top_products_by_revenue(cur, top=10):
    cur.execute("""
        SELECT p.name,
               p.category,
               COUNT(o.order_id)              AS vendas,
               ROUND(SUM(o.total)::numeric, 2) AS receita_total
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        GROUP BY p.product_id, p.name, p.category
        ORDER BY receita_total DESC
        LIMIT %s
    """, (top,))
    return cur.fetchall()


def payment_distribution(cur):
    cur.execute("""
        SELECT payment,
               COUNT(*) AS total,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct,
               ROUND(SUM(total)::numeric, 2) AS volume_financeiro
        FROM orders
        GROUP BY payment
        ORDER BY total DESC
    """)
    return cur.fetchall()


def segment_analysis(cur):
    cur.execute("""
        SELECT c.segment,
               COUNT(DISTINCT c.customer_id)   AS clientes,
               COUNT(o.order_id)               AS pedidos,
               ROUND(AVG(o.total)::numeric, 2) AS ticket_medio,
               ROUND(SUM(o.total)::numeric, 2) AS receita_total
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.segment
        ORDER BY receita_total DESC
    """)
    return cur.fetchall()


def main():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 60)
    print("THE LEDGER - ANALISE DE NEGOCIOS (Dia 2)")
    print("=" * 60)

    # 1. Receita por estado
    print("\n1. RECEITA POR ESTADO (Top 5)")
    print(f"  {'Estado':<8} {'Pedidos':>8} {'Clientes':>10} {'Receita Total':>15}")
    print(f"  {'-'*8} {'-'*8} {'-'*10} {'-'*15}")
    for r in revenue_by_state(cur):
        print(f"  {r['state']:<8} {r['pedidos']:>8} {r['clientes']:>10} R$ {float(r['receita_total']):>11,.2f}")

    # 2. Status dos pedidos
    print("\n2. STATUS DOS PEDIDOS")
    print(f"  {'Status':<14} {'Total':>7} {'Pct':>7}")
    print(f"  {'-'*14} {'-'*7} {'-'*7}")
    for r in order_status_distribution(cur):
        print(f"  {r['status']:<14} {r['total']:>7} {float(r['pct']):>6.1f}%")

    # 3. Top produtos por receita
    print("\n3. TOP 10 PRODUTOS POR RECEITA")
    print(f"  {'Produto':<35} {'Categoria':<15} {'Vendas':>7} {'Receita':>12}")
    print(f"  {'-'*35} {'-'*15} {'-'*7} {'-'*12}")
    for r in top_products_by_revenue(cur):
        nome = r['name'][:34]
        cat = r['category'][:14]
        print(f"  {nome:<35} {cat:<15} {r['vendas']:>7} R$ {float(r['receita_total']):>8,.2f}")

    # 4. Distribuicao de pagamento
    print("\n4. METODOS DE PAGAMENTO")
    print(f"  {'Metodo':<14} {'Total':>7} {'Pct':>7} {'Volume Financeiro':>18}")
    print(f"  {'-'*14} {'-'*7} {'-'*7} {'-'*18}")
    for r in payment_distribution(cur):
        print(f"  {r['payment']:<14} {r['total']:>7} {float(r['pct']):>6.1f}% R$ {float(r['volume_financeiro']):>13,.2f}")

    # 5. Analise por segmento
    print("\n5. ANALISE POR SEGMENTO")
    print(f"  {'Segmento':<10} {'Clientes':>10} {'Pedidos':>8} {'Ticket Medio':>14} {'Receita Total':>15}")
    print(f"  {'-'*10} {'-'*10} {'-'*8} {'-'*14} {'-'*15}")
    for r in segment_analysis(cur):
        print(f"  {r['segment']:<10} {r['clientes']:>10} {r['pedidos']:>8} R$ {float(r['ticket_medio']):>10,.2f} R$ {float(r['receita_total']):>11,.2f}")

    cur.close()
    conn.close()
    print("\nThe Ledger consultado com sucesso!")


if __name__ == "__main__":
    main()

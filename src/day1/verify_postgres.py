import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="shopagent", user="shopagent", password="shopagent"
)
cur = conn.cursor(cursor_factory=RealDictCursor)

# 1. Contagem de registros
print("=" * 50)
print("1. CONTAGEM DE REGISTROS")
print("=" * 50)
for tabela in ["customers", "products", "orders"]:
    cur.execute(f"SELECT COUNT(*) as total FROM {tabela}")
    row = cur.fetchone()
    print(f"  {tabela:12}: {row['total']:>6} registros")

# 2. Amostra de clientes
print("\n" + "=" * 50)
print("2. AMOSTRA DE CLIENTES (5 primeiros)")
print("=" * 50)
cur.execute("SELECT name, state, segment FROM customers LIMIT 5")
rows = cur.fetchall()
print(f"  {'Nome':<30} {'Estado':<8} {'Segmento'}")
print(f"  {'-'*30} {'-'*8} {'-'*10}")
for r in rows:
    print(f"  {r['name']:<30} {r['state']:<8} {r['segment']}")

# 3. Amostra de pedidos
print("\n" + "=" * 50)
print("3. AMOSTRA DE PEDIDOS (5 primeiros)")
print("=" * 50)
cur.execute("SELECT total, status, payment FROM orders LIMIT 5")
rows = cur.fetchall()
print(f"  {'Total':>10}  {'Status':<12} {'Pagamento'}")
print(f"  {'-'*10}  {'-'*12} {'-'*12}")
for r in rows:
    print(f"  R$ {float(r['total']):>7.2f}  {r['status']:<12} {r['payment']}")

# 4. Distribuição de pedidos por status
print("\n" + "=" * 50)
print("4. PEDIDOS POR STATUS")
print("=" * 50)
cur.execute("""
    SELECT status,
           COUNT(*) as total,
           ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
    FROM orders
    GROUP BY status
    ORDER BY total DESC
""")
rows = cur.fetchall()
print(f"  {'Status':<14} {'Qtd':>6}  {'%':>6}")
print(f"  {'-'*14} {'-'*6}  {'-'*6}")
for r in rows:
    print(f"  {r['status']:<14} {r['total']:>6}  {float(r['pct']):>5.1f}%")

# 5. Distribuição de clientes por estado
print("\n" + "=" * 50)
print("5. CLIENTES POR ESTADO")
print("=" * 50)
cur.execute("""
    SELECT state, COUNT(*) as total
    FROM customers
    GROUP BY state
    ORDER BY total DESC
""")
rows = cur.fetchall()
print(f"  {'Estado':<8} {'Qtd':>6}")
print(f"  {'-'*8} {'-'*6}")
for r in rows:
    print(f"  {r['state']:<8} {r['total']:>6}")

cur.close()
conn.close()
print("\n✓ Verificação concluída com sucesso!")

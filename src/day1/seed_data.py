"""Gera dados sinteticos de e-commerce no Postgres (substitui ShadowTraffic)."""
import random
import json
import os
import psycopg2
from faker import Faker

fake = Faker("pt_BR")
random.seed(42)

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="shopagent", user="shopagent", password="shopagent"
)
cur = conn.cursor()

# Limpar tabelas na ordem correta (FK)
cur.execute("DELETE FROM orders")
cur.execute("DELETE FROM customers")
cur.execute("DELETE FROM products")
conn.commit()

# --- CUSTOMERS (500) ---
print("Gerando customers...")
states = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "PE"]
segments = ["premium", "standard", "basic"]
customer_ids = []

for _ in range(500):
    cid = fake.uuid4()
    customer_ids.append(cid)
    cur.execute(
        "INSERT INTO customers VALUES (%s, %s, %s, %s, %s, %s)",
        (cid, fake.name(), fake.email(), fake.city(),
         random.choice(states), random.choice(segments))
    )
conn.commit()
print(f"  {len(customer_ids)} customers inseridos")

# --- PRODUCTS (200) ---
print("Gerando products...")
categories = ["Eletronicos", "Moda", "Casa", "Esportes", "Livros", "Beleza", "Brinquedos"]
brands = [fake.company() for _ in range(30)]
product_ids = []

for _ in range(200):
    pid = fake.uuid4()
    product_ids.append(pid)
    cur.execute(
        "INSERT INTO products VALUES (%s, %s, %s, %s, %s)",
        (pid, fake.bs().title()[:50], random.choice(categories),
         round(random.uniform(19.90, 999.90), 2), random.choice(brands))
    )
conn.commit()
print(f"  {len(product_ids)} products inseridos")

# --- ORDERS (5000) ---
print("Gerando orders (5000)...")
statuses = ["delivered", "shipped", "processing", "cancelled"]
status_weights = [0.50, 0.20, 0.20, 0.10]
payments = ["pix", "credit_card", "boleto"]
payment_weights = [0.45, 0.40, 0.15]
order_ids = []

for i in range(5000):
    oid = fake.uuid4()
    order_ids.append(oid)
    cur.execute(
        "INSERT INTO orders VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (oid,
         random.choice(customer_ids),
         random.choice(product_ids),
         random.randint(1, 10),
         round(random.uniform(29.90, 999.90), 2),
         random.choices(statuses, weights=status_weights)[0],
         random.choices(payments, weights=payment_weights)[0],
         fake.date_time_between(start_date="-6m", end_date="now"))
    )
    if i % 1000 == 0:
        conn.commit()
        print(f"  {i+1}/5000...")
conn.commit()
print(f"  {len(order_ids)} orders inseridos")

# --- REVIEWS (500) em JSONL ---
print("Gerando reviews (JSONL)...")
comments = [
    "Produto chegou antes do prazo, estou muito satisfeito com a compra.",
    "Entrega atrasou mais de 10 dias, nao recebi nenhuma notificacao.",
    "O produto e exatamente como descrito na foto, otima qualidade.",
    "Frete absurdamente caro, quase o dobro do valor do produto.",
    "Ate hoje nao recebi meu pedido, faz 20 dias que comprei.",
    "Superou todas as minhas expectativas, recomendo muito.",
    "Produto chegou danificado, a embalagem estava completamente amassada.",
    "Atendimento ao cliente pessimo, ninguem resolve o problema.",
    "Entrega rapida e produto de otima qualidade, voltarei a comprar.",
    "O produto veio diferente da foto, cor totalmente errada.",
    "Demorou 15 dias para chegar, mas o produto e bom.",
    "Excelente custo-beneficio, produto de qualidade por um preco justo.",
    "Nao recebi o produto e o suporte nao responde meus chamados.",
    "Produto danificado na entrega, pedi reembolso mas nao obtive resposta.",
    "Chegou no prazo, embalagem bem protegida, produto perfeito.",
    "O frete demorou mais do que o esperado, porem o produto e bom.",
    "Comprei ha 3 semanas e ainda esta como pedido em processamento.",
    "Qualidade excelente, bem melhor do que esperava pelo preco.",
    "Produto veio com defeito de fabricacao, muito decepcionante.",
    "Entrega super rapida, recebi em 2 dias uteis. Recomendo o vendedor.",
    "O material e fraco, nao vale o preco que foi cobrado.",
    "Otimo produto, ja e minha segunda compra e continua me surpreendendo.",
    "A entrega estava prevista para sexta e chegou apenas na quarta da semana seguinte.",
    "Produto identico ao anunciado, funcionando perfeitamente.",
    "Tive que abrir disputa pois o produto nunca chegou no endereco.",
    "Muito bom, superou as expectativas em termos de qualidade e acabamento.",
    "Embalagem chegou aberta e produto com sinais de uso, inaceitavel.",
    "Rapido, seguro e produto de alta qualidade. Nota maxima.",
    "O vendedor nao fornece rastreamento atualizado, ficou dias sem movimentacao.",
    "Produto fantastico, vale cada centavo investido na compra.",
]
sentiments = ["positive", "neutral", "negative"]
sentiment_weights = [0.35, 0.30, 0.35]
ratings = [1, 2, 3, 4, 5]
rating_weights = [0.05, 0.10, 0.20, 0.30, 0.35]

reviews_dir = os.path.join(os.path.dirname(__file__), "../../gen/data/reviews")
os.makedirs(reviews_dir, exist_ok=True)
reviews_path = os.path.join(reviews_dir, "reviews.jsonl")

with open(reviews_path, "w", encoding="utf-8") as f:
    for _ in range(500):
        review = {
            "review_id": fake.uuid4(),
            "order_id": random.choice(order_ids),
            "rating": random.choices(ratings, weights=rating_weights)[0],
            "comment": random.choice(comments),
            "sentiment": random.choices(sentiments, weights=sentiment_weights)[0],
        }
        f.write(json.dumps(review, ensure_ascii=False) + "\n")

print(f"  500 reviews gravados em {reviews_path}")

cur.close()
conn.close()
print("\nTudo pronto!")

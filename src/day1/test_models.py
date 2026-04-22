"""Testa validacoes dos modelos Pydantic do ShopAgent."""
import uuid
from datetime import datetime
from pydantic import ValidationError
from src.day1.models import Customer, Product, Order, Review

cid = uuid.uuid4()
pid = uuid.uuid4()
oid = uuid.uuid4()
rid = uuid.uuid4()

print("=" * 55)
print("TESTES DE VALIDACAO — MODELOS PYDANTIC")
print("=" * 55)

# 1. Order valida
print("\n1. Order VALIDA")
try:
    order = Order(
        order_id=oid,
        customer_id=cid,
        product_id=pid,
        qty=3,
        total=299.90,
        status="delivered",
        payment="pix",
        created_at=datetime.now(),
    )
    print(f"   OK: {order.model_dump()}")
except ValidationError as e:
    print(f"   ERRO inesperado: {e}")

# 2. Order com qty=0 (invalido: minimo e 1)
print("\n2. Order com qty=0 (deve falhar)")
try:
    Order(order_id=oid, customer_id=cid, product_id=pid,
          qty=0, total=100.0, status="delivered", payment="pix")
    print("   ERRO: deveria ter falhado!")
except ValidationError as e:
    for err in e.errors():
        print(f"   Capturado: campo '{err['loc'][0]}' — {err['msg']}")

# 3. Order com payment='dinheiro' (invalido)
print("\n3. Order com payment='dinheiro' (deve falhar)")
try:
    Order(order_id=oid, customer_id=cid, product_id=pid,
          qty=2, total=150.0, status="shipped", payment="dinheiro")
    print("   ERRO: deveria ter falhado!")
except ValidationError as e:
    for err in e.errors():
        print(f"   Capturado: campo '{err['loc'][0]}' — {err['msg']}")

# 4. Review valida com rating=5
print("\n4. Review VALIDA com rating=5")
try:
    review = Review(
        review_id=rid,
        order_id=oid,
        rating=5,
        comment="Produto fantastico, vale cada centavo!",
        sentiment="positive",
    )
    print(f"   OK: {review.model_dump()}")
except ValidationError as e:
    print(f"   ERRO inesperado: {e}")

# 5. Review com rating=6 (invalido: maximo e 5)
print("\n5. Review com rating=6 (deve falhar)")
try:
    Review(review_id=rid, order_id=oid, rating=6, comment="Otimo!")
    print("   ERRO: deveria ter falhado!")
except ValidationError as e:
    for err in e.errors():
        print(f"   Capturado: campo '{err['loc'][0]}' — {err['msg']}")

# 6. Customer com segment invalido
print("\n6. Customer com segment='vip' (deve falhar)")
try:
    Customer(customer_id=cid, name="Janaina", email="j@email.com", segment="vip")
    print("   ERRO: deveria ter falhado!")
except ValidationError as e:
    for err in e.errors():
        print(f"   Capturado: campo '{err['loc'][0]}' — {err['msg']}")

print("\n" + "=" * 55)
print("Todos os testes executados!")
print("=" * 55)

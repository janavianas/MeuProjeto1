"""Passo 11 — Provocacao RAG: o que o SQL nao consegue responder."""
import json
from collections import Counter

# Carregar reviews
reviews = []
with open("gen/data/reviews/reviews.jsonl", encoding="utf-8") as f:
    for line in f:
        reviews.append(json.loads(line))

negativos = [r for r in reviews if r["sentiment"] == "negative"]

print("=" * 55)
print("PASSO 11 - PROVOCACAO RAG")
print("=" * 55)

# 1. Temas das reclamacoes negativas
print("\n1. PRINCIPAIS TEMAS NAS RECLAMACOES NEGATIVAS")
print("   (reviews com sentiment = negative)")
print()

palavras_chave = {
    "entrega/prazo":       ["atraso", "atrasou", "demorou", "prazo", "dias", "semanas"],
    "produto danificado":  ["danificado", "defeito", "amassada", "aberta", "sinais de uso"],
    "suporte/atendimento": ["suporte", "atendimento", "pessimo", "nao responde"],
    "produto errado":      ["diferente", "errada", "foto"],
    "nao recebeu":         ["nao recebi", "nunca chegou", "disputa", "processamento"],
    "preco/frete":         ["caro", "fraco", "nao vale"],
}

temas = Counter()
for r in negativos:
    comentario = r["comment"].lower()
    for tema, palavras in palavras_chave.items():
        if any(p in comentario for p in palavras):
            temas[tema] += 1

for tema, qtd in temas.most_common():
    barra = "#" * qtd
    print(f"   {tema:<25} {qtd:>3} ocorrencias  {barra}")

# 2. Ratings nos reviews negativos
print("\n2. RATINGS NOS REVIEWS NEGATIVOS")
ratings_neg = Counter(r["rating"] for r in negativos)
for nota in sorted(ratings_neg.keys()):
    print(f"   Nota {nota}: {ratings_neg[nota]} reviews")

# 3. O limite do SQL
print()
print("=" * 55)
print("O LIMITE DO SQL")
print("=" * 55)
print()
print("Perguntas que o SQL responde facilmente:")
print("  - Quantos pedidos foram cancelados?  -> COUNT + WHERE")
print("  - Qual o ticket medio?               -> AVG(total)")
print("  - Top estados por receita?           -> GROUP BY + SUM")
print()
print("Perguntas que o SQL NAO consegue responder:")
print("  - Quais clientes reclamam de atraso na entrega?")
print("  - Quais produtos tem mais queixas de qualidade?")
print("  - O que clientes premium acham do frete?")
print("  - Ha correlacao entre regiao e tipo de reclamacao?")
print()
print("Por que o SQL nao resolve?")
print("  Os comentarios sao TEXTO LIVRE. O SQL so faz busca")
print("  exata (LIKE), nao entende SIGNIFICADO.")
print()
print('  Exemplo: "Esperava receber antes do fim de semana"')
print("  -> SQL com LIKE '%atraso%'  = NAO encontra")
print("  -> Busca semantica (Qdrant) = ENCONTRA")
print()
print("=" * 55)
print("O QUE FAREMOS NO DIA 2")
print("=" * 55)
print()
print("  Carregar os 500 reviews no Qdrant como vetores.")
print("  Cada comentario vira um numero que representa")
print("  seu SIGNIFICADO. Ai podemos perguntar:")
print()
print('  "Quais reviews falam sobre problemas de entrega?"')
print()
print("  E o Qdrant encontra todos os textos com esse")
print("  significado — mesmo que nao usem a palavra 'entrega'.")
print()

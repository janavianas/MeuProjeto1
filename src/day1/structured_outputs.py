"""Analisa reviews com Claude e retorna resultado estruturado via Pydantic."""
import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import anthropic

_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(_base, "../../gen/.env"))


class ReviewAnalysis(BaseModel):
    total_reviews: int
    average_rating: float
    sentiment_distribution: dict[str, int]
    top_complaints: list[str]
    top_praises: list[str]


def load_reviews(path: str, n: int = 10) -> list[dict]:
    reviews = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            reviews.append(json.loads(line))
            if len(reviews) >= n:
                break
    return reviews


def analyze_reviews(reviews: list[dict]) -> ReviewAnalysis:
    client = anthropic.Anthropic()

    reviews_text = json.dumps(reviews, ensure_ascii=False, indent=2)

    prompt = f"""Analise estas avaliacoes de e-commerce e retorne uma analise estruturada.

Reviews:
{reviews_text}

Retorne um JSON com exatamente esta estrutura:
{{
  "total_reviews": <numero inteiro>,
  "average_rating": <media das notas, numero decimal>,
  "sentiment_distribution": {{
    "positive": <contagem>,
    "neutral": <contagem>,
    "negative": <contagem>
  }},
  "top_complaints": ["reclamacao 1", "reclamacao 2", "reclamacao 3"],
  "top_praises": ["elogio 1", "elogio 2", "elogio 3"]
}}

Responda APENAS com o JSON, sem texto adicional."""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    data = json.loads(raw)
    return ReviewAnalysis(**data)


def main():
    reviews_path = os.path.join(
        os.path.dirname(__file__), "../../gen/data/reviews/reviews.jsonl"
    )

    print("Carregando 10 reviews...")
    reviews = load_reviews(reviews_path, n=10)
    print(f"  {len(reviews)} reviews carregados")

    print("\nEnviando para o Claude...")
    analysis = analyze_reviews(reviews)

    print("\n" + "=" * 50)
    print("ANALISE ESTRUTURADA (via Claude SDK)")
    print("=" * 50)
    print(f"\nTotal de reviews analisados : {analysis.total_reviews}")
    print(f"Media das notas             : {analysis.average_rating:.1f} / 5.0")

    print("\nDistribuicao de sentimentos:")
    for sentimento, qtd in analysis.sentiment_distribution.items():
        print(f"  {sentimento:<10}: {qtd}")

    print("\nPrincipais reclamacoes:")
    for i, c in enumerate(analysis.top_complaints, 1):
        print(f"  {i}. {c}")

    print("\nPrincipais elogios:")
    for i, p in enumerate(analysis.top_praises, 1):
        print(f"  {i}. {p}")

    print("\n" + "=" * 50)
    print("Tipo do resultado:", type(analysis).__name__)
    print("=" * 50)


if __name__ == "__main__":
    main()

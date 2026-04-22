"""Passo 11 — Provocacao: e se o agente decidisse sozinho qual store usar?"""

perguntas = [
    # (pergunta, store_correto, motivo)
    ("Qual o faturamento total do mes passado?",
     "LEDGER (Postgres)",
     "Pergunta numerica exata -> SQL: SUM(total) WHERE created_at..."),

    ("Quais clientes estao reclamando de atraso na entrega?",
     "MEMORY (Qdrant)",
     "Busca por significado -> 'atraso', 'nao recebi', 'demorou' = mesmo tema"),

    ("Quantos pedidos foram cancelados em SP?",
     "LEDGER (Postgres)",
     "Contagem exata com filtro -> COUNT WHERE status='cancelled' AND state='SP'"),

    ("O que os clientes premium acham da qualidade dos produtos?",
     "MEMORY (Qdrant) + LEDGER (Postgres)",
     "Qdrant: busca reviews sobre qualidade | Postgres: filtrar por segmento=premium"),

    ("Qual o ticket medio por estado?",
     "LEDGER (Postgres)",
     "Media numerica por grupo -> AVG(total) GROUP BY state"),

    ("Quais sao os principais elogios dos clientes satisfeitos?",
     "MEMORY (Qdrant)",
     "Temas e sentimentos -> busca semantica em texto livre"),

    ("Produto mais vendido no RS com reclamacoes de qualidade?",
     "MEMORY (Qdrant) + LEDGER (Postgres)",
     "Qdrant: reviews negativos de qualidade | Postgres: JOIN com produtos e filtro RS"),

    ("Qual metodo de pagamento gera mais cancelamentos?",
     "LEDGER (Postgres)",
     "Correlacao entre colunas -> COUNT GROUP BY payment WHERE status='cancelled'"),
]

print("=" * 65)
print("PASSO 11 - PROVOCACAO: O AGENTE DECIDE SOZINHO")
print("=" * 65)
print()
print("Hoje VOCE decidiu qual store usar em cada pergunta.")
print("Amanha o AGENTE decide sozinho. Mas como ele saberia?")
print()

print("-" * 65)
print(f"  {'Pergunta':<42} {'Store'}")
print("-" * 65)
for pergunta, store, motivo in perguntas:
    p = pergunta[:41] + "?" if len(pergunta) > 41 else pergunta
    print(f"  {p:<42} {store}")
print("-" * 65)

print()
print("COMO O AGENTE VAI APRENDER ISSO?")
print()
print("  Regra 1: palavras como 'faturamento', 'total', 'media',")
print("           'quantos', 'percentual' -> LEDGER (SQL exato)")
print()
print("  Regra 2: palavras como 'reclamacao', 'opiniao', 'sentimento',")
print("           'elogio', 'problema', 'queixa' -> MEMORY (semantico)")
print()
print("  Regra 3: perguntas que misturam numeros COM sentimentos")
print("           -> USA OS DOIS stores em sequencia")
print()
print("=" * 65)
print("PREVIEW DO DIA 3")
print("=" * 65)
print()
print("  O agente tera 2 ferramentas (tools):")
print()
print("  tool: query_ledger(sql)")
print("    -> executa SQL no Postgres")
print("    -> usa quando a pergunta e sobre numeros exatos")
print()
print("  tool: search_memory(query)")
print("    -> busca semantica no Qdrant")
print("    -> usa quando a pergunta e sobre texto/sentimento")
print()
print("  O LLM (Claude) vai ler a pergunta do usuario,")
print("  decidir qual tool chamar, executar, e retornar")
print("  a resposta — tudo automaticamente.")
print()
print("  Isso e um AGENTE com roteamento de ferramentas.")
print()

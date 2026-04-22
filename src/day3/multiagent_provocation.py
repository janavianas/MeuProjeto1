"""Passo 11 - Provocacao: e se houvesse um time de agentes especializados?"""

print("=" * 65)
print("PASSO 11 - PROVOCACAO: DO AGENTE UNICO AO TIME DE AGENTES")
print("=" * 65)
print()
print("Hoje voce construiu UM agente que faz tudo:")
print()
print("  ShopAgent")
print("  |-- query_ledger  (Postgres)")
print("  |-- search_memory (Qdrant)")
print()
print("Ele e inteligente, mas faz tudo sozinho.")
print("E se o problema fosse mais complexo?")
print()

print("-" * 65)
print("LIMITACOES DO AGENTE UNICO")
print("-" * 65)
print()

limitacoes = [
    ("Pergunta complexa",  "Preciso de um relatorio completo: faturamento,\n"
                           "    top produtos, reclamacoes e recomendacoes estrategicas."),
    ("Problema",           "Um unico agente tenta fazer tudo em sequencia.\n"
                           "    Pode perder contexto, demorar, ou misturar raciocinio."),
    ("Solucao com times",  "Dividir em agentes especializados que colaboram."),
]

for titulo, descricao in limitacoes:
    print(f"  {titulo}:")
    print(f"    {descricao}")
    print()

print("=" * 65)
print("PREVIEW DO DIA 4 - MULTI-AGENTES COM CREWAI")
print("=" * 65)
print()
print("No Dia 4 voce vai construir um TIME de agentes:")
print()

agentes = [
    ("DataAnalystAgent",    "Consulta The Ledger (Postgres)\n"
                            "     Especialista em SQL, numeros, metricas"),
    ("SentimentAgent",      "Consulta The Memory (Qdrant)\n"
                            "     Especialista em reviews, reclamacoes, elogios"),
    ("StrategyAgent",       "Recebe os resultados dos dois acima\n"
                            "     Gera insights e recomendacoes estrategicas"),
    ("ReportAgent",         "Monta o relatorio final\n"
                            "     Formata tudo em markdown estruturado"),
]

for nome, descricao in agentes:
    print(f"  [{nome}]")
    print(f"     {descricao}")
    print()

print("-" * 65)
print("COMO ELES VAN COLABORAR (CrewAI)")
print("-" * 65)
print()
print("  Usuario: 'Relatorio completo de performance de novembro'")
print()
print("  1. DataAnalystAgent  -> query_ledger(sql)")
print("     Resultado: faturamento, top produtos, cancelamentos")
print()
print("  2. SentimentAgent    -> search_memory(query)")
print("     Resultado: principais reclamacoes e elogios")
print()
print("  3. StrategyAgent     <- recebe resultados 1 e 2")
print("     Resultado: 3 insights estrategicos")
print()
print("  4. ReportAgent       <- recebe tudo acima")
print("     Resultado: relatorio formatado, pronto para entregar")
print()

print("=" * 65)
print("A DIFERENCA ENTRE AGENTE UNICO E MULTI-AGENTE")
print("=" * 65)
print()

comparacao = [
    ("Aspecto",          "Agente Unico",        "Multi-Agente (CrewAI)"),
    ("-" * 20,           "-" * 20,              "-" * 20),
    ("Especializacao",   "Generalista",         "Cada agente eh expert"),
    ("Paralelismo",      "Sequencial",          "Agentes em paralelo"),
    ("Complexidade",     "Tarefas simples",     "Tarefas complexas"),
    ("Manutencao",       "Um arquivo",          "Modular e escalavel"),
    ("Raciocinio",       "Contexto unico",      "Multiplas perspectivas"),
]

for linha in comparacao:
    print(f"  {linha[0]:<22} {linha[1]:<22} {linha[2]}")

print()
print("=" * 65)
print("O QUE VOCE VAI APRENDER NO DIA 4")
print("=" * 65)
print()
print("  - CrewAI: framework para times de agentes")
print("  - Definir Agents com roles, goals e backstories")
print("  - Criar Tasks e encadear resultados")
print("  - Crew: orquestrar o time completo")
print("  - DeepEval: avaliar a qualidade das respostas")
print("  - LangFuse: observabilidade e rastreamento")
print("  - Deploy: Supabase (Postgres) + Qdrant Cloud")
print()
print("  O ShopAgent vira o ShopCrew!")
print()
print("=" * 65)

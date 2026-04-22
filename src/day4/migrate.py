"""Passo 18 - Migracao para a nuvem: Supabase + Qdrant Cloud."""
import os
import json
import psycopg2
from dotenv import load_dotenv

_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base, "../../gen/.env"))

def _limpar(valor):
    return valor.strip().strip('"').strip("'") if valor else ""

# Conexoes locais (Docker)
LOCAL_DB = "postgresql://shopagent:shopagent@localhost:5432/shopagent"
LOCAL_QDRANT = _limpar(os.getenv("QDRANT_URL", "http://localhost:6333"))
COLLECTION = _limpar(os.getenv("QDRANT_COLLECTION", "shopagent_reviews"))

# Conexoes na nuvem
CLOUD_DB = _limpar(os.getenv("SUPABASE_URL", ""))
CLOUD_QDRANT_URL = _limpar(os.getenv("QDRANT_CLOUD_URL", ""))
CLOUD_QDRANT_KEY = _limpar(os.getenv("QDRANT_CLOUD_API_KEY", ""))


def migrar_postgres():
    """Migra todas as tabelas do Postgres local para o Supabase."""
    print("\n" + "=" * 65)
    print("MIGRANDO POSTGRES -> SUPABASE")
    print("=" * 65)

    if not CLOUD_DB:
        print("ERRO: SUPABASE_URL nao configurada no .env")
        return False

    # Conectar aos dois bancos
    print("Conectando ao Postgres local...")
    conn_local = psycopg2.connect(LOCAL_DB)

    print("Conectando ao Supabase...")
    conn_cloud = psycopg2.connect(CLOUD_DB)
    conn_cloud.autocommit = False

    cur_local = conn_local.cursor()
    cur_cloud = conn_cloud.cursor()

    tabelas = ["customers", "products", "orders", "reviews"]

    for tabela in tabelas:
        print(f"\nMigrando tabela: {tabela}...")

        # Buscar estrutura da tabela
        cur_local.execute(f"""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{tabela}'
            ORDER BY ordinal_position
        """)
        colunas_info = cur_local.fetchall()

        # Buscar dados locais
        cur_local.execute(f"SELECT * FROM {tabela}")
        rows = cur_local.fetchall()
        cols = [desc[0] for desc in cur_local.description]

        if not rows:
            print(f"  Tabela {tabela} vazia, pulando...")
            continue

        # Criar tabela no Supabase (drop se existir)
        cur_cloud.execute(f"DROP TABLE IF EXISTS {tabela} CASCADE")

        # Gerar DDL baseado na estrutura original
        cur_local.execute(f"""
            SELECT column_name, data_type, character_maximum_length,
                   is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{tabela}'
            ORDER BY ordinal_position
        """)
        col_defs = []
        for col in cur_local.fetchall():
            nome, tipo, max_len, nullable, default = col
            if tipo == 'uuid':
                col_def = f"{nome} UUID"
            elif tipo == 'character varying':
                tamanho = max_len or 255
                col_def = f"{nome} VARCHAR({tamanho})"
            elif tipo == 'integer':
                col_def = f"{nome} INTEGER"
            elif tipo == 'numeric':
                col_def = f"{nome} NUMERIC"
            elif tipo == 'text':
                col_def = f"{nome} TEXT"
            elif tipo == 'jsonb':
                col_def = f"{nome} JSONB"
            elif tipo == 'timestamp without time zone':
                col_def = f"{nome} TIMESTAMP"
            elif tipo == 'boolean':
                col_def = f"{nome} BOOLEAN"
            else:
                col_def = f"{nome} TEXT"

            if nullable == 'NO':
                col_def += " NOT NULL"
            col_defs.append(col_def)

        ddl = f"CREATE TABLE {tabela} ({', '.join(col_defs)})"
        cur_cloud.execute(ddl)

        # Inserir dados em lotes
        placeholders = ", ".join(["%s"] * len(cols))
        insert_sql = f"INSERT INTO {tabela} ({', '.join(cols)}) VALUES ({placeholders})"

        lote = 100
        total = len(rows)
        for i in range(0, total, lote):
            batch = rows[i:i+lote]
            cur_cloud.executemany(insert_sql, batch)
            print(f"  {min(i+lote, total)}/{total} registros inseridos...")

        conn_cloud.commit()
        print(f"  Tabela {tabela}: {total} registros migrados!")

    cur_local.close()
    cur_cloud.close()
    conn_local.close()
    conn_cloud.close()

    print("\nPostgres -> Supabase: CONCLUIDO!")
    return True


def migrar_qdrant():
    """Migra vetores do Qdrant local para o Qdrant Cloud."""
    print("\n" + "=" * 65)
    print("MIGRANDO QDRANT -> QDRANT CLOUD")
    print("=" * 65)

    if not CLOUD_QDRANT_URL or not CLOUD_QDRANT_KEY:
        print("ERRO: QDRANT_CLOUD_URL ou QDRANT_CLOUD_API_KEY nao configurados")
        return False

    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct

    print("Conectando ao Qdrant local...")
    client_local = QdrantClient(url=LOCAL_QDRANT)

    print("Conectando ao Qdrant Cloud...")
    client_cloud = QdrantClient(
        url=CLOUD_QDRANT_URL,
        api_key=CLOUD_QDRANT_KEY,
    )

    # Verificar colecao local
    info = client_local.get_collection(COLLECTION)
    vector_size = info.config.params.vectors.size
    print(f"Colecao local: {COLLECTION} ({info.points_count} pontos, {vector_size} dims)")

    # Recriar colecao no cloud
    try:
        client_cloud.delete_collection(COLLECTION)
        print(f"Colecao existente removida no cloud")
    except:
        pass

    client_cloud.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    print(f"Colecao criada no Qdrant Cloud")

    # Migrar pontos em lotes
    lote = 100
    offset = None
    total_migrado = 0

    while True:
        results = client_local.scroll(
            collection_name=COLLECTION,
            limit=lote,
            offset=offset,
            with_vectors=True,
            with_payload=True,
        )
        pontos, next_offset = results

        if not pontos:
            break

        points_to_upsert = [
            PointStruct(
                id=str(p.id),
                vector=p.vector,
                payload=p.payload,
            )
            for p in pontos
        ]

        client_cloud.upsert(
            collection_name=COLLECTION,
            points=points_to_upsert,
        )

        total_migrado += len(pontos)
        print(f"  {total_migrado} vetores migrados...")

        if next_offset is None:
            break
        offset = next_offset

    print(f"\nQdrant -> Cloud: {total_migrado} vetores migrados! CONCLUIDO!")
    return True


if __name__ == "__main__":
    print("SHOPCREW - MIGRACAO PARA A NUVEM")
    print("Local (Docker) -> Nuvem (Supabase + Qdrant Cloud)")

    ok_pg = migrar_postgres()
    ok_qd = migrar_qdrant()

    print("\n" + "=" * 65)
    print("RESULTADO DA MIGRACAO")
    print("=" * 65)
    print(f"Postgres -> Supabase : {'OK' if ok_pg else 'FALHOU'}")
    print(f"Qdrant   -> Cloud    : {'OK' if ok_qd else 'FALHOU'}")

    if ok_pg and ok_qd:
        print("\nMigracao concluida! O ShopCrew agora pode rodar 100% na nuvem.")

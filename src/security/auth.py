"""Camada 1 - Autenticacao de usuarios para o Chainlit."""
import os
import hashlib
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base, "../../gen/.env"))

DB_URL = "postgresql://shopagent:shopagent@localhost:5432/shopagent"


def criar_tabela_usuarios():
    """Cria tabela de usuarios se nao existir."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_users (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email       VARCHAR(255) UNIQUE NOT NULL,
            senha_hash  VARCHAR(64) NOT NULL,
            nome        VARCHAR(255),
            papel       VARCHAR(50) NOT NULL DEFAULT 'viewer',
            ativo       BOOLEAN DEFAULT TRUE,
            criado_em   TIMESTAMPTZ DEFAULT NOW(),
            ultimo_login TIMESTAMPTZ
        )
    """)
    conn.commit()

    # Criar usuarios de demonstracao
    usuarios_demo = [
        ("admin@shopagent.com",    "admin123",    "Administrador",   "admin"),
        ("gestor@shopagent.com",   "gestor123",   "Gestor Vendas",   "gestor"),
        ("analista@shopagent.com", "analista123", "Analista Dados",  "analista"),
        ("viewer@shopagent.com",   "viewer123",   "Visualizador",    "viewer"),
    ]

    for email, senha, nome, papel in usuarios_demo:
        senha_hash = _hash_senha(senha)
        cur.execute("""
            INSERT INTO app_users (email, senha_hash, nome, papel)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, (email, senha_hash, nome, papel))

    conn.commit()
    cur.close()
    conn.close()
    print("Tabela de usuarios criada com usuarios demo!")


def _hash_senha(senha: str) -> str:
    """Hash SHA-256 da senha. Em producao real use bcrypt."""
    return hashlib.sha256(senha.encode()).hexdigest()


def autenticar(email: str, senha: str) -> dict | None:
    """
    Valida email e senha. Retorna dados do usuario ou None.
    Em producao real use bcrypt para comparar hashes.
    """
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, email, nome, papel, ativo
            FROM app_users
            WHERE email = %s AND senha_hash = %s
        """, (email, _hash_senha(senha)))

        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return None

        user_id, email_db, nome, papel, ativo = row

        if not ativo:
            cur.close()
            conn.close()
            return None

        # Atualizar ultimo login
        cur.execute("""
            UPDATE app_users SET ultimo_login = NOW() WHERE id = %s
        """, (user_id,))
        conn.commit()
        cur.close()
        conn.close()

        return {
            "id": str(user_id),
            "email": email_db,
            "nome": nome,
            "papel": papel,
        }

    except Exception as e:
        print(f"Erro na autenticacao: {e}")
        return None


# Descricoes dos papeis para mostrar ao usuario
DESCRICOES_PAPEIS = {
    "viewer":   "Visualizador — contagens e status de pedidos",
    "analista": "Analista — faturamento agregado e tendencias",
    "gestor":   "Gestor — acesso completo exceto dados pessoais",
    "admin":    "Administrador — acesso total e logs de auditoria",
}

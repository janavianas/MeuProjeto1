"""Camada 5 - Log de auditoria: registra todos os acessos."""
import os
import json
import psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv

_base = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_base, "../../gen/.env"))

DB_URL = "postgresql://shopagent:shopagent@localhost:5432/shopagent"


def criar_tabela_auditoria():
    """Cria a tabela de auditoria se nao existir."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id          SERIAL PRIMARY KEY,
            timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            user_id     VARCHAR(255) NOT NULL,
            user_email  VARCHAR(255),
            acao        VARCHAR(50)  NOT NULL,
            ferramenta  VARCHAR(50),
            query_hash  VARCHAR(32),
            tabelas     TEXT[],
            linhas      INTEGER,
            sucesso     BOOLEAN      NOT NULL,
            erro        TEXT,
            ip          VARCHAR(50),
            detalhes    JSONB
        )
    """)
    # Indices para busca rapida
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_user
        ON audit_log(user_id, timestamp DESC)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp
        ON audit_log(timestamp DESC)
    """)
    conn.commit()
    cur.close()
    conn.close()


class AuditLogger:
    """Registra cada acesso no log imutavel de auditoria."""

    def __init__(self, user_id: str, user_email: str = "", ip: str = ""):
        self.user_id    = user_id
        self.user_email = user_email
        self.ip         = ip

    def registrar_query(
        self,
        ferramenta: str,
        query_hash: str,
        tabelas: list[str],
        linhas: int,
        sucesso: bool,
        erro: str = None,
    ):
        """Registra uma consulta ao banco de dados."""
        self._inserir(
            acao="QUERY",
            ferramenta=ferramenta,
            query_hash=query_hash,
            tabelas=tabelas,
            linhas=linhas,
            sucesso=sucesso,
            erro=erro,
        )

    def registrar_login(self, sucesso: bool, erro: str = None):
        """Registra tentativa de login."""
        self._inserir(
            acao="LOGIN",
            sucesso=sucesso,
            erro=erro,
        )

    def registrar_logout(self):
        """Registra logout do usuario."""
        self._inserir(acao="LOGOUT", sucesso=True)

    def registrar_acesso_negado(self, motivo: str, ferramenta: str = None):
        """Registra tentativa de acesso nao autorizado."""
        self._inserir(
            acao="ACESSO_NEGADO",
            ferramenta=ferramenta,
            sucesso=False,
            erro=motivo,
        )

    def _inserir(self, acao: str, ferramenta: str = None, query_hash: str = None,
                 tabelas: list = None, linhas: int = None, sucesso: bool = True,
                 erro: str = None):
        """Insere o registro no banco. Falha silenciosa para nao quebrar o agente."""
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO audit_log
                    (user_id, user_email, acao, ferramenta, query_hash,
                     tabelas, linhas, sucesso, erro, ip)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.user_id, self.user_email, acao, ferramenta,
                query_hash, tabelas, linhas, sucesso, erro, self.ip
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            # Log local como fallback se o banco estiver fora
            print(f"[AUDIT FALLBACK] {datetime.now()} | {self.user_id} | {acao} | {erro or 'ok'}")


def buscar_logs(user_id: str = None, limite: int = 50) -> list:
    """Consulta o historico de auditoria. Uso exclusivo de admins."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    if user_id:
        cur.execute("""
            SELECT timestamp, user_id, user_email, acao, ferramenta,
                   tabelas, linhas, sucesso, erro
            FROM audit_log
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (user_id, limite))
    else:
        cur.execute("""
            SELECT timestamp, user_id, user_email, acao, ferramenta,
                   tabelas, linhas, sucesso, erro
            FROM audit_log
            ORDER BY timestamp DESC
            LIMIT %s
        """, (limite,))

    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


if __name__ == "__main__":
    print("Criando tabela de auditoria...")
    criar_tabela_auditoria()
    print("Tabela criada!")

    # Teste de log
    logger = AuditLogger(user_id="teste-123", user_email="teste@exemplo.com")
    logger.registrar_login(sucesso=True)
    logger.registrar_query(
        ferramenta="query_ledger",
        query_hash="abc123",
        tabelas=["orders"],
        linhas=10,
        sucesso=True,
    )
    print("Logs registrados!")

    logs = buscar_logs(limite=5)
    for log in logs:
        print(log)

"""Camada 3 - Protecao contra SQL injection e operacoes destrutivas."""
import re
import hashlib
from datetime import datetime


# Operacoes proibidas absolutamente
COMANDOS_PROIBIDOS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE",
    "ALTER", "CREATE", "GRANT", "REVOKE", "EXEC",
    "EXECUTE", "XP_", "SP_", "--", "/*", "*/",
]

# Colunas que nunca devem aparecer em queries (dados pessoais)
COLUNAS_SENSIVEIS = [
    "cpf", "password", "senha", "token", "secret",
    "credit_card", "cartao", "pin",
]


class SQLGuard:
    """Valida e sanitiza queries SQL antes de executar."""

    def __init__(self, user_id: str = "anonimo"):
        self.user_id = user_id

    def validar(self, sql: str) -> str:
        """
        Valida a query. Retorna a query limpa ou lanca excecao.
        """
        sql_limpo = sql.strip()
        sql_upper = sql_limpo.upper()

        # 1. Deve comecar com SELECT
        if not sql_upper.lstrip().startswith("SELECT"):
            raise PermissionError(
                "Apenas consultas SELECT sao permitidas. "
                "O agente nao pode modificar dados."
            )

        # 2. Nao pode conter comandos destrutivos
        for cmd in COMANDOS_PROIBIDOS:
            if cmd in sql_upper:
                raise PermissionError(
                    f"Comando '{cmd}' nao e permitido. "
                    "Tentativa de operacao nao autorizada registrada."
                )

        # 3. Nao pode acessar colunas sensiveis diretamente
        for col in COLUNAS_SENSIVEIS:
            # Verifica se a coluna aparece no SELECT (nao no WHERE com hash)
            padrao = rf"\bSELECT\b.*\b{col}\b"
            if re.search(padrao, sql_upper, re.DOTALL):
                raise PermissionError(
                    f"Acesso direto a coluna sensivel '{col}' nao e permitido."
                )

        # 4. Sem multiplas queries (ponto-e-virgula no meio)
        partes = [p.strip() for p in sql_limpo.split(";") if p.strip()]
        if len(partes) > 1:
            raise PermissionError(
                "Multiplas queries em uma unica chamada nao sao permitidas."
            )

        return sql_limpo

    def gerar_hash(self, sql: str) -> str:
        """Gera hash da query para o log (nao salva a query completa)."""
        return hashlib.sha256(sql.encode()).hexdigest()[:16]


def criar_guard(user_id: str = "anonimo") -> SQLGuard:
    return SQLGuard(user_id=user_id)

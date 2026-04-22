"""Camada 2 - RBAC: controle de acesso por papel do usuario."""

# Politicas de acesso por papel
POLITICAS = {
    "viewer": {
        "descricao": "Apenas contagens e status de pedidos",
        "colunas_bloqueadas": [
            "total_amount", "unit_price", "price", "revenue",
            "cpf", "email", "phone", "password", "senha",
        ],
        "tabelas_permitidas": ["orders", "products"],
        "mensagem_bloqueio": (
            "Seu perfil (Visualizador) nao tem acesso a dados financeiros. "
            "Solicite ao administrador o perfil Analista para ver faturamentos."
        ),
    },
    "analista": {
        "descricao": "Faturamento agregado, sem dados pessoais",
        "colunas_bloqueadas": [
            "cpf", "email", "phone", "password", "senha",
        ],
        "tabelas_permitidas": ["orders", "products", "customers", "reviews"],
        "mensagem_bloqueio": (
            "Seu perfil (Analista) nao tem acesso a dados pessoais de clientes."
        ),
    },
    "gestor": {
        "descricao": "Acesso completo exceto dados pessoais",
        "colunas_bloqueadas": [
            "cpf", "email", "phone", "password", "senha",
        ],
        "tabelas_permitidas": ["orders", "products", "customers", "reviews"],
        "mensagem_bloqueio": (
            "Seu perfil (Gestor) nao tem acesso a dados pessoais de clientes."
        ),
    },
    "admin": {
        "descricao": "Acesso total",
        "colunas_bloqueadas": [],
        "tabelas_permitidas": [
            "orders", "products", "customers", "reviews",
            "audit_log", "app_users",
        ],
        "mensagem_bloqueio": "",
    },
}


class RBACGuard:
    """Aplica politica de acesso baseada no papel do usuario."""

    def __init__(self, papel: str):
        self.papel    = papel
        self.politica = POLITICAS.get(papel, POLITICAS["viewer"])

    def validar_query(self, sql: str) -> str:
        """Verifica se a query respeita as permissoes do papel."""
        sql_upper = sql.upper()

        # 1. Verificar colunas bloqueadas no SELECT
        for coluna in self.politica["colunas_bloqueadas"]:
            # Detecta coluna no SELECT ou como alias
            import re
            padrao = rf"(?:SELECT|,)\s+(?:\w+\.)?{coluna.upper()}\b"
            if re.search(padrao, sql_upper):
                raise PermissionError(self.politica["mensagem_bloqueio"])

        # 2. Verificar tabelas permitidas
        import re
        tabelas_na_query = re.findall(r"\bFROM\s+(\w+)", sql_upper)
        tabelas_na_query += re.findall(r"\bJOIN\s+(\w+)", sql_upper)

        for tabela in tabelas_na_query:
            if tabela.lower() not in self.politica["tabelas_permitidas"]:
                raise PermissionError(
                    f"Seu perfil ({self.papel}) nao tem acesso a tabela '{tabela.lower()}'. "
                    f"Tabelas disponiveis: {', '.join(self.politica['tabelas_permitidas'])}"
                )

        return sql

    def pode_ver_financeiro(self) -> bool:
        return "total_amount" not in self.politica["colunas_bloqueadas"]

    def pode_ver_dados_pessoais(self) -> bool:
        return "cpf" not in self.politica["colunas_bloqueadas"]

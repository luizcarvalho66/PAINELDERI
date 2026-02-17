"""
Obter Token Databricks via U2M (User-to-Machine) OAuth.

PRÉ-REQUISITOS:
  1. pip install databricks-sdk
  2. Databricks CLI configurado com profile:
     databricks auth login --host https://adb-7941093640821140.0.azuredatabricks.net

COMO FUNCIONA:
  - U2M usa o browser para autenticação OAuth interativa.
  - O SDK obtém automaticamente o token via o profile configurado no ~/.databrickscfg
  - Quando o token expira, ele é renovado automaticamente.
"""

from databricks.sdk import WorkspaceClient

# ============================================================
# MÉTODO 1: Usando profile do CLI (RECOMENDADO para uso local)
# ============================================================
# O profile já deve existir em ~/.databrickscfg após rodar:
#   databricks auth login --host https://adb-7941093640821140.0.azuredatabricks.net

HOST = "https://adb-7941093640821140.0.azuredatabricks.net"
PROFILE = "adb-7941093640821140"

def get_token_via_profile():
    """Obtém token usando o profile do Databricks CLI (U2M OAuth)."""
    w = WorkspaceClient(
        host=HOST,
        profile=PROFILE,       # Usa o profile do ~/.databrickscfg
        auth_type="databricks-cli"  # Força usar CLI/OAuth U2M
    )
    
    # Obtém os headers de autenticação (contém o Bearer token)
    config = w.config
    headers = config.authenticate()
    
    # authenticate() retorna uma callable (HeaderFactory) ou dict
    if callable(headers):
        headers = headers()
    
    auth_header = headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
        return token
    else:
        raise Exception(f"Header de autenticação inesperado: {auth_header[:50]}...")


def get_token_via_host_only():
    """
    Obtém token usando apenas o host.
    O SDK tenta automaticamente todos os métodos de auth disponíveis:
      1. Variáveis de ambiente (DATABRICKS_TOKEN, etc.)
      2. Profile padrão do ~/.databrickscfg
      3. Azure CLI (az login)
    """
    w = WorkspaceClient(host=HOST)
    
    config = w.config
    print(f"Auth type detectado: {config.auth_type}")
    
    headers = config.authenticate()
    if callable(headers):
        headers = headers()
    
    auth_header = headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
        return token
    else:
        raise Exception(f"Header inesperado: {auth_header[:50]}...")


# ============================================================
# MÉTODO 2: Usando databricks-sql-connector com CLI auth
# ============================================================
def connect_sql_warehouse():
    """
    Conecta diretamente ao SQL Warehouse usando auth_type='databricks-cli'.
    Isso usa o token do profile automaticamente — NÃO precisa extrair manualmente.
    """
    from databricks import sql
    
    conn = sql.connect(
        server_hostname="adb-7941093640821140.0.azuredatabricks.net",
        http_path="/sql/1.0/warehouses/ce56ec5f5d0a3e07",
        auth_type="databricks-cli",
        profile=PROFILE
    )
    return conn


# ============================================================
# EXECUÇÃO
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  DATABRICKS U2M TOKEN RETRIEVAL")
    print("=" * 60)
    
    # --- Método 1: Via Profile ---
    print("\n[1] Obtendo token via profile CLI...")
    try:
        token = get_token_via_profile()
        print(f"    ✅ Token obtido com sucesso!")
        print(f"    Tamanho: {len(token)} caracteres")
        print(f"    Preview: {token[:20]}...{token[-10:]}")
    except Exception as e:
        print(f"    ❌ Erro: {e}")
        print(f"    Certifique-se de rodar primeiro:")
        print(f"    databricks auth login --host {HOST}")
    
    # --- Método 2: Conexão direta ao SQL Warehouse ---
    print("\n[2] Testando conexão direta ao SQL Warehouse...")
    try:
        conn = connect_sql_warehouse()
        cursor = conn.cursor()
        cursor.execute("SELECT current_user() as user, current_timestamp() as ts")
        row = cursor.fetchone()
        print(f"    ✅ Conectado como: {row[0]}")
        print(f"    Timestamp: {row[1]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"    ❌ Erro: {e}")
    
    print("\n" + "=" * 60)

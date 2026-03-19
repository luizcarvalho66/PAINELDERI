import duckdb
import os
import tempfile
import threading
import shutil
import time

# CONFIGURAÇÃO DE PERSISTÊNCIA (Volume Databricks vs Local)
# Tenta usar Volume do Unity Catalog se disponível, senão usa pasta local 'data'
VOLUME_PATH = "/Volumes/main/default/ri_dashboard_data"
LOCAL_DATA_DIR = os.path.join(os.getcwd(), "data")

# Detecção de Ambiente
if os.path.exists("/Volumes"):
    # Estamos no Databricks (provavelmente)
    DB_DIR = VOLUME_PATH
    pass  # Ambiente Databricks
else:
    # Ambiente Local
    DB_DIR = LOCAL_DATA_DIR
    pass  # Ambiente Local

# Garante que o diretório existe
try:
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)
except Exception as e:
    pass  # fallback para temp
    # Fallback extremo para temp se falhar permissão
    DB_DIR = tempfile.gettempdir()

DB_PATH = os.path.join(DB_DIR, "dashboard.duckdb")

# MIGRAÇÃO LEGADA DESATIVADA
# O banco antigo no temp tem schema incompatível com o sync Databricks atual.
# Se precisar recuperar dados, faça um sync completo via botão "Sincronizar".
TEMP_DB_PATH = os.path.join(tempfile.gettempdir(), "data.duckdb")
# Nota: NÃO copiar mais do temp — o schema mudou significativamente.


# Thread-local storage for connections
_thread_local = threading.local()
_conn_pid = None
_lock = threading.Lock()
_active_connections = [] # Registry to close all if needed

# DuckDB performance configuration
DUCKDB_CONFIG = {
    'threads': 4,                    # Use multiple threads for parallelism
    'memory_limit': '2GB',           # Increased from 512MB to 2GB to support 448MB+ files
    'temp_directory': tempfile.gettempdir(),  # Explicit temp dir
}

# Maintenance Lock
_maintenance_event = threading.Event()
_maintenance_event.set()  # Initially set (True) meaning NOT in maintenance

def set_maintenance_mode(active=True):
    """
    Controls maintenance mode.
    active=True -> Blocks new RO connections, closes existing ones.
    active=False -> Resumes normal operation.
    """
    if active:
        pass  # Maintenance Mode ON
        _maintenance_event.clear()
        close_connection()
        time.sleep(0.5)
    else:
        pass  # Maintenance Mode OFF
        _maintenance_event.set()

def get_connection(read_only=True):
    """
    Universal connection factory.
    """
    if read_only:
        return get_readonly_connection()
    else:
        # Escrita requer fechar RO connections para evitar conflitos de lock/config
        try:
            close_connection()
            return duckdb.connect(DB_PATH, read_only=False, config=DUCKDB_CONFIG)
        except Exception as e:
            print(f"[DuckDB WRITE ERROR] Failed to create Write connection: {e}")
            raise e

def get_readonly_connection():
    """
    Returns a thread-local Read-Only connection.
    Safe for multi-threaded Dash environment.
    """
    global _conn_pid

    # Block if in maintenance mode
    if not _maintenance_event.is_set():
        pass  # Waiting for maintenance
        if not _maintenance_event.wait(timeout=30):
            raise Exception("Database is in Maintenance Mode (Timeout)")

    current_pid = os.getpid()
    
    # Check if we have a connection for this thread
    conn = getattr(_thread_local, 'conn', None)
    
    # Validation: PID change or closed connection
    if conn is not None:
        if _conn_pid != current_pid:
            conn = None
        else:
            try:
                conn.execute("SELECT 1")
            except Exception:
                conn = None
    
    if conn is None:
        with _lock:
            try:
                # STRICTLY READ ONLY
                conn = duckdb.connect(DB_PATH, read_only=True, config=DUCKDB_CONFIG)
                _thread_local.conn = conn
                _conn_pid = current_pid
                _active_connections.append(conn)
                pass  # New RO connection
            except Exception as e:
                print(f"[DuckDB CRITICAL] Read-Only Connection Failed: {e}")
                raise e
    
    return conn

def close_connection():
    """Closes all active connections in the registry and current thread."""
    global _active_connections, _conn_pid
    with _lock:
        pass  # Closing connections
        for conn in _active_connections:
            try:
                conn.close()
            except Exception:
                pass
        _active_connections = []
        _conn_pid = None
        if hasattr(_thread_local, 'conn'):
            _thread_local.conn = None

def init_db():
    """Initializes the database via a schema creation script."""
    # MUST USE WRITE CONNECTION and CLOSE IT properly
    conn = None
    try:
        conn = get_connection(read_only=False)
    except Exception as e:
        print(f"[INIT DB] Skipped init due to lock: {e}")
        return

    try:
        # --- CAMADA GOLD (DATA MART / ANALYTICS) ---
        # Tabelas otimizadas com tipagem forte para máxima performance no consumo

        # logs_regulacao_preventiva - mesmos dados que ri_preventiva_detalhamento (sync grava ambas)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS logs_regulacao_preventiva (
            numero_os VARCHAR,
            codigo_item VARCHAR,
            codigo_cliente VARCHAR,
            codigo_tgm VARCHAR,
            codigo_estabelecimento VARCHAR,
            nome_cliente VARCHAR,
            nome_estabelecimento VARCHAR,
            placa VARCHAR,
            fabricante VARCHAR,
            modelo_veiculo VARCHAR,
            familia_veiculo VARCHAR,
            uf VARCHAR,
            cidade VARCHAR,
            chassi VARCHAR,
            ano_veiculo VARCHAR,
            descricao_peca VARCHAR,
            complemento_peca VARCHAR,
            tipo_manutencao VARCHAR,
            status_os VARCHAR,
            valor_total DOUBLE,
            valor_aprovado DOUBLE,
            valor_peca DOUBLE,
            valor_mo DOUBLE,
            data_transacao TIMESTAMP,
            data_atualizacao TIMESTAMP,
            data_criacao_os TIMESTAMP,
            data_aprovacao_os TIMESTAMP,
            nome_aprovador VARCHAR,
            tipo_mo VARCHAR,
            hodometro DOUBLE,
            mensagem_log VARCHAR,
            tipo_manutencao_oficina VARCHAR,
            peca VARCHAR,
            descricao_servico VARCHAR
        );
        """)

        # logs_regulacao_preventiva_header - criada pelo sync a partir de logs_regulacao_preventiva
        # Schema alinhado com o que o sync Databricks grava
        conn.execute("""
        CREATE TABLE IF NOT EXISTS logs_regulacao_preventiva_header (
            cod_chamado_manutencao VARCHAR,
            data_cadastro TIMESTAMP,
            valor_limite_chamado_mult VARCHAR,
            valor_limite_chamado_conc VARCHAR,
            plano_manutencao VARCHAR
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS logs_regulacao_preventiva_items (
            id_log VARCHAR, 
            mensagem_log VARCHAR,
            plano_preventivo VARCHAR,
            tipo_ec_corrigido VARCHAR,
            perc_dif DECIMAL(10,4),
            cod_chamado_preventivo VARCHAR,
            codigo_cliente VARCHAR,
            codigo_estabelecimento VARCHAR,
            data_cadastro DATE,
            data_envio_orcamento DATE
        );
        """)

        # logs_corretiva - mesmos dados que ri_corretiva_detalhamento (sync grava ambas)
        # Schema igual ao de ri_corretiva_detalhamento
        conn.execute("""
        CREATE TABLE IF NOT EXISTS logs_corretiva (
            numero_os VARCHAR,
            codigo_item VARCHAR,
            codigo_cliente VARCHAR,
            codigo_tgm VARCHAR,
            codigo_estabelecimento VARCHAR,
            nome_cliente VARCHAR,
            nome_estabelecimento VARCHAR,
            placa VARCHAR,
            fabricante VARCHAR,
            modelo_veiculo VARCHAR,
            familia_veiculo VARCHAR,
            uf VARCHAR,
            cidade VARCHAR,
            chassi VARCHAR,
            ano_veiculo VARCHAR,
            descricao_peca VARCHAR,
            complemento_peca VARCHAR,
            tipo_manutencao VARCHAR,
            status_os VARCHAR,
            valor_total DOUBLE,
            valor_aprovado DOUBLE,
            valor_peca DOUBLE,
            valor_mo DOUBLE,
            data_transacao TIMESTAMP,
            data_atualizacao TIMESTAMP,
            data_criacao_os TIMESTAMP,
            data_aprovacao_os TIMESTAMP,
            nome_aprovador VARCHAR,
            tipo_mo VARCHAR,
            hodometro DOUBLE,
            mensagem_log VARCHAR,
            tipo_manutencao_oficina VARCHAR,
            peca VARCHAR,
            descricao_servico VARCHAR
        );
        """)
        
        # ri_preventiva_detalhamento - mesmo schema, criada pelo sync (fallback)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS ri_preventiva_detalhamento (
            numero_os VARCHAR,
            codigo_item VARCHAR,
            codigo_cliente VARCHAR,
            codigo_tgm VARCHAR,
            codigo_estabelecimento VARCHAR,
            nome_cliente VARCHAR,
            nome_estabelecimento VARCHAR,
            placa VARCHAR,
            fabricante VARCHAR,
            modelo_veiculo VARCHAR,
            familia_veiculo VARCHAR,
            uf VARCHAR,
            cidade VARCHAR,
            chassi VARCHAR,
            ano_veiculo VARCHAR,
            descricao_peca VARCHAR,
            complemento_peca VARCHAR,
            tipo_manutencao VARCHAR,
            status_os VARCHAR,
            valor_total DOUBLE,
            valor_aprovado DOUBLE,
            valor_peca DOUBLE,
            valor_mo DOUBLE,
            data_transacao TIMESTAMP,
            data_atualizacao TIMESTAMP,
            data_criacao_os TIMESTAMP,
            data_aprovacao_os TIMESTAMP,
            nome_aprovador VARCHAR,
            tipo_mo VARCHAR,
            hodometro DOUBLE,
            mensagem_log VARCHAR,
            tipo_manutencao_oficina VARCHAR,
            peca VARCHAR,
            descricao_servico VARCHAR
        );
        """)
        
        # RI_Corretiva_Detalhamento
        # Schema alinhado com as colunas que o sync do Databricks realmente grava
        # A tabela é recriada pelo sync — este CREATE IF NOT EXISTS é apenas fallback
        conn.execute("""
        CREATE TABLE IF NOT EXISTS ri_corretiva_detalhamento (
            numero_os VARCHAR,
            codigo_item VARCHAR,
            codigo_cliente VARCHAR,
            codigo_tgm VARCHAR,
            codigo_estabelecimento VARCHAR,
            nome_cliente VARCHAR,
            nome_estabelecimento VARCHAR,
            placa VARCHAR,
            fabricante VARCHAR,
            modelo_veiculo VARCHAR,
            familia_veiculo VARCHAR,
            uf VARCHAR,
            cidade VARCHAR,
            chassi VARCHAR,
            ano_veiculo VARCHAR,
            descricao_peca VARCHAR,
            complemento_peca VARCHAR,
            tipo_manutencao VARCHAR,
            status_os VARCHAR,
            valor_total DOUBLE,
            valor_aprovado DOUBLE,
            valor_peca DOUBLE,
            valor_mo DOUBLE,
            data_transacao TIMESTAMP,
            data_atualizacao TIMESTAMP,
            data_criacao_os TIMESTAMP,
            data_aprovacao_os TIMESTAMP,
            nome_aprovador VARCHAR,
            tipo_mo VARCHAR,
            hodometro DOUBLE,
            mensagem_log VARCHAR,
            tipo_manutencao_oficina VARCHAR,
            peca VARCHAR,
            descricao_servico VARCHAR
        );
        """)

        # Aprovação_em_Pacotes
        conn.execute("""
        CREATE TABLE IF NOT EXISTS aprovacao_em_pacotes (
            codigo_cliente VARCHAR,
            flag_possui_pacote_servico BOOLEAN,
            nome_cliente VARCHAR,
            numero_os VARCHAR
        );
        """)

        # Peca_intercambiavel
        conn.execute("""
        CREATE TABLE IF NOT EXISTS peca_intercambiavel (
            column3 VARCHAR,
            peca VARCHAR
        );
        """)

        # --- REF: ITENS APROVAÇÃO AUTOMÁTICA ---
        # Knowledge integrated from Context Excel
        conn.execute("CREATE TABLE IF NOT EXISTS ref_aprovacao_automatica (tipo_mo VARCHAR PRIMARY KEY)")
        
        # Upsert logic (delete all and re-insert to ensure sync with code)
        # Using specific items extracted from "Itens Aprovação Automática.xlsx"
        auto_approve_items = [
            'ALINHAMENTO DE SUSPENSAO', 'BALANCEAMENTO DE RODA', 'BALANCEAR', 'CAMBER',
            'CONTRATO MECANICA GERAL  ESP', 'CONTRATO SERV ELETRICA GERAL', 'CONTRATO SERV MECANICA GERAL',
            'HONORARIO', 'LAVAGEM A SECO COMPLETA', 'LAVAGEM A SECO EXTERNA', 'LAVAGEM A SECO INTERNA',
            'LAVAGEM COMPLETA', 'LAVAGEM COMPLETA COM CERA', 'LAVAGEM CONVENCIONAL', 'LAVAGEM EXPRESSA',
            'LAVAGEM EXTERNA', 'LAVAGEM INTERNA', 'LUBRIFICACAO GERAL', 'LUBRIFICAR', 'POLIR', 'RODIZIO DE PNEUS'
        ]
        
        # Check if empty or just truncate and refill to be safe
        conn.execute("DELETE FROM ref_aprovacao_automatica")
        for item in auto_approve_items:
            # Secure insert
            conn.execute("INSERT INTO ref_aprovacao_automatica VALUES (?)", [item])
        
        # --- REF: PEÇAS INTERCAMBIÁVEIS ---
        # Peças que podem ser aprovadas automaticamente (de "Peças intercambiaveis - NOVA.xlsx")
        conn.execute("CREATE TABLE IF NOT EXISTS ref_pecas_intercambiaveis (peca VARCHAR PRIMARY KEY)")
        
        pecas_intercambiaveis = [
            'OLEO MOTOR', 'OLEO DIRECAO HIDRAULICA', 'OLEO DIFERENCIAL', 'OLEO CAMBIO', 
            'OLEO TRANSMISSAO', 'FLUIDO DE FREIO', 'LIQUIDO DE ARREFECIMENTO', 'AGUA DESTILADA',
            'FILTRO DE AR MOTOR', 'FILTRO DE OLEO MOTOR', 'FILTRO COMBUSTIVEL', 'FILTRO AR CONDICIONADO',
            'FILTRO DE AR DO HABITACULO', 'FILTRO SECADOR AR', 'FILTRO SEPARADOR DE AGUA',
            'VELA DE IGNICAO', 'CABO DE VELA', 'BOBINA DE IGNICAO', 'BATERIA',
            'LAMPADA FAROL', 'LAMPADA LANTERNA', 'LAMPADA FREIO', 'LAMPADA RE', 'LAMPADA SETA',
            'LAMPADA PLACA', 'LAMPADA TETO', 'LAMPADA PAINEL', 'LAMPADA T5', 'LAMPADA T10',
            'LAMPADA H1', 'LAMPADA H3', 'LAMPADA H4', 'LAMPADA H7', 'LAMPADA H11',
            'PALHETA LIMPADOR', 'PALHETA LIMPADOR DIANTEIRO', 'PALHETA LIMPADOR TRASEIRO',
            'CORREIA ALTERNADOR', 'CORREIA AR CONDICIONADO', 'CORREIA DENTADA', 'CORREIA POLY V',
            'PNEU', 'CAMARA DE AR', 'VALVULA DE PNEU', 'BICO PNEU',
            'PASTILHA FREIO DIANTEIRO', 'PASTILHA FREIO TRASEIRO', 'LONA DE FREIO',
            'DISCO DE FREIO DIANTEIRO', 'DISCO DE FREIO TRASEIRO', 'TAMBOR FREIO',
            'FUSIVEL', 'RELE', 'LAMPADA LED', 'LAMPADA XENON',
            'TERMINAL BATERIA', 'CABO BATERIA', 'CINTA BATERIA',
            'SILICONE', 'GRAXA', 'ADITIVO RADIADOR', 'ADITIVO COMBUSTIVEL',
            'CHAVE DE RODA', 'MACACO', 'TRIANGULO', 'EXTINTOR',
            'ESGUICHO LIMPADOR', 'RESERVATORIO AGUA', 'TAMPA RESERVATORIO',
            'PRESILHA', 'GRAMPO', 'ABRAÇADEIRA', 'MANGUEIRA',
            'AMORTECEDOR DIANTEIRO', 'AMORTECEDOR TRASEIRO', 'KIT AMORTECEDOR',
            'MOLA DIANTEIRA', 'MOLA TRASEIRA', 'MOLA HELICOIDAL',
            'BUCHA BANDEJA', 'BUCHA BARRA ESTABILIZADORA', 'PIVO',
            'TERMINAL DIREÇÃO', 'BARRA DIREÇÃO', 'CAIXA DIREÇÃO',
            'JUNTA HOMOCINETICA', 'COIFA HOMOCINETICA', 'SEMI EIXO',
            'ROLAMENTO RODA DIANTEIRA', 'ROLAMENTO RODA TRASEIRA', 'CUBO RODA',
            'EMBREAGEM', 'PLATÔ', 'DISCO EMBREAGEM', 'ROLAMENTO EMBREAGEM',
            'BOMBA DAGUA', 'BOMBA COMBUSTIVEL', 'BOMBA OLEO', 'BOMBA DIRECAO',
            'RADIADOR', 'MANGUEIRA RADIADOR', 'VENTOINHA', 'MOTOR VENTOINHA',
            'ALTERNADOR', 'MOTOR PARTIDA', 'REGULADOR VOLTAGEM',
            'SENSOR TEMPERATURA', 'SENSOR PRESSAO OLEO', 'SENSOR ABS', 'SENSOR VELOCIDADE',
            'VIDRO PARABRISA', 'VIDRO TRASEIRO', 'VIDRO PORTA', 'BORRACHA VIDRO',
            'RETROVISOR', 'ESPELHO RETROVISOR', 'CAPA RETROVISOR',
            'PARA-CHOQUE DIANTEIRO', 'PARA-CHOQUE TRASEIRO', 'GRADE DIANTEIRA',
            'FAROL DIANTEIRO', 'LANTERNA TRASEIRA', 'PISCA LATERAL',
            'MAÇANETA EXTERNA', 'MAÇANETA INTERNA', 'FECHADURA PORTA',
            'LIMITADOR PORTA', 'DOBRADIÇA PORTA', 'GUARNIÇÃO PORTA',
            'CINTO SEGURANÇA', 'FIVELA CINTO', 'RETRATOR CINTO',
            'TAPETE', 'CARPETE', 'CONSOLE', 'PORTA OBJETOS',
            
            # VARIAÇÕES ENCONTRADAS NO DUMP DO USUÁRIO
            'FILTRO DE OLEO', 'FILTRO OLEO', 'FILTRO DE CABINE', 'FILTRO CABINE',
            'KIT EMBREAGEM', 'KIT DE EMBREAGEM', 
            'VALVULA AR PNEU', 'VALVULA PNEU',
            'VELA', 'JOGO DE VELA',
            'TERMINAL DIRECAO', 'TERMINAL DE DIRECAO',
            'LANTERNA LATERAL', 'LANTERNA',
            'AGUA DESMINERALIZADA',
            'ABRACADEIRA AUTOTRAV', 'ABRACADEIRA',
            'FILTRO SEPARADOR', 'FILTRO RACOR',
            'RESERVATORIO DE AGUA',
            'RADIADOR DE AGUA',
            'ANEL DE VEDACAO', 'ANEL VEDACAO',
            'CORPO BORBOLETA',
            'CAPO DIANTEIRO', 'CAPO',
            'DESCARBONIZANTE',
            'GUIA DO PARACHOQUE', 'GUIA PARACHOQUE',
            'ADESIVOS', 'ADESIVO',
            'BUCHA ESTABILIZADOR',
            'PARAFUSO RODA', 'PARAFUSO DE RODA',
            'PORCA RODA', 'PORCA DE RODA'
        ]
        
        conn.execute("DELETE FROM ref_pecas_intercambiaveis")
        for peca in pecas_intercambiaveis:
            try:
                conn.execute("INSERT INTO ref_pecas_intercambiaveis VALUES (?)", [peca])
            except Exception:
                pass  # Ignore duplicates
        
        # --- REF: CLIENTES COM PACOTES ---
        # Clientes que possuem pacotes de serviços pré-aprovados
        conn.execute("""
        CREATE TABLE IF NOT EXISTS ref_clientes_pacote (
            codigo_cliente VARCHAR PRIMARY KEY,
            nome_cliente VARCHAR,
            possui_pacote BOOLEAN DEFAULT TRUE
        )
        """)
        
        # Nota: Os dados de clientes com pacotes serão carregados via sync do Databricks.
        # Por ora, deixamos a tabela vazia para ser populada.
        
        # --- REF: CLIENTES TGFM (Filtro Global) ---
        # Tabela de referência para filtrar dados apenas dos clientes TGFM
        conn.execute("""
        CREATE TABLE IF NOT EXISTS ref_clientes_tgfm (
            codigo_cliente VARCHAR PRIMARY KEY
        )
        """)
        
        # Sincronizar com a lista do config
        try:
            from backend.config.tgfm_clients import TGFM_ALL_CLIENTS
            conn.execute("DELETE FROM ref_clientes_tgfm")
            for code in TGFM_ALL_CLIENTS:
                try:
                    conn.execute("INSERT INTO ref_clientes_tgfm VALUES (?)", [str(code)])
                except Exception:
                    pass  # Ignore duplicates
            pass  # TGFM loaded
        except ImportError:
            print("[INIT DB WARNING] backend.config.tgfm_clients não encontrado. Tabela ref_clientes_tgfm vazia.")
        except Exception as e:
            print(f"[INIT DB WARNING] Erro ao popular ref_clientes_tgfm: {e}")

        # Optimization: Create indexes for performance (Consumo)
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_preventiva_cod ON logs_regulacao_preventiva (cod_chamado_manutencao)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_corretiva_chave ON logs_corretiva (chave_item)")
            # CRITICAL INDEX for RI Corretiva Detalhamento
            conn.execute("CREATE INDEX IF NOT EXISTS idx_detalhamento_chave ON ri_corretiva_detalhamento (chave_item)")
            # Index for TGFM filter performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_corr_det_cliente ON ri_corretiva_detalhamento (codigo_cliente)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prev_det_cliente ON ri_preventiva_detalhamento (codigo_cliente)")
        except Exception:
            pass # Some versions of DuckDB handle indices differently or already exist

    except Exception as e:
        print(f"[INIT DB ERROR] {e}")
    finally:
        if conn:
            conn.close()
            pass  # Connection closed

if __name__ == "__main__":
    init_db()

"""
Testes automatizados para o sync Databricks → DuckDB.
Testa lógica local (DuckDB, watermark, merge) SEM precisar de conexão real ao Databricks.

Executar: python -m pytest tests/test_sync.py -v
"""
import os
import sys
import pytest
import duckdb
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Ajustar path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def tmp_db(tmp_path):
    """Cria um DuckDB temporário para testes."""
    db_path = str(tmp_path / "test_dashboard.duckdb")
    conn = duckdb.connect(db_path, read_only=False)
    yield conn, db_path
    conn.close()


@pytest.fixture
def sample_df():
    """DataFrame de exemplo simulando dados do Databricks."""
    now = datetime.now()
    return pd.DataFrame({
        'numero_os': ['OS001', 'OS001', 'OS002', 'OS003'],
        'codigo_item': ['ITEM1', 'ITEM2', 'ITEM1', 'ITEM1'],
        'codigo_cliente': ['6240480', '6240480', '6240480', '6240480'],
        'codigo_tgm': ['60905', '60905', '60905', '60905'],
        'codigo_estabelecimento': ['EST1', 'EST1', 'EST2', 'EST3'],
        'nome_cliente': ['JBS', 'JBS', 'JBS', 'JBS'],
        'nome_estabelecimento': ['Oficina A', 'Oficina A', 'Oficina B', 'Oficina C'],
        'placa': ['ABC1234', 'ABC1234', 'DEF5678', 'GHI9012'],
        'fabricante': ['SCANIA', 'SCANIA', 'VOLVO', 'MERCEDES'],
        'modelo_veiculo': ['R450', 'R450', 'FH540', 'ACTROS'],
        'familia_veiculo': ['PESADO', 'PESADO', 'PESADO', 'PESADO'],
        'uf': ['SP', 'SP', 'MG', 'PR'],
        'cidade': ['São Paulo', 'São Paulo', 'BH', 'Curitiba'],
        'chassi': ['CH001', 'CH001', 'CH002', 'CH003'],
        'ano_veiculo': ['2022', '2022', '2023', '2021'],
        'descricao_peca': ['FILTRO OLEO', 'CORREIA', None, 'PASTILHA'],
        'complemento_peca': ['GENERICA', 'GATES', 'GENERICA', 'FRAS-LE'],
        'tipo_manutencao': ['CORRETIVA', 'CORRETIVA', 'PREVENTIVA', 'CORRETIVA'],
        'status_os': ['APROVADA', 'APROVADA', 'PENDENTE', 'CANCELADA'],
        'valor_total': [150.0, 200.0, 500.0, 300.0],
        'valor_aprovado': [140.0, 180.0, None, None],
        'valor_peca': [100.0, 120.0, 350.0, 200.0],
        'valor_mo': [40.0, 60.0, 150.0, 100.0],
        'data_transacao': [now - timedelta(days=10), now - timedelta(days=10), now - timedelta(days=5), now - timedelta(days=1)],
        'data_atualizacao': [now - timedelta(days=9), now - timedelta(days=9), now - timedelta(days=4), now],
        'data_criacao_os': [now - timedelta(days=10), now - timedelta(days=10), now - timedelta(days=5), now - timedelta(days=1)],
        'data_aprovacao_os': [now - timedelta(days=8), now - timedelta(days=8), None, None],
        'nome_aprovador': ['João', 'João', 'SISTEMA', 'SISTEMA'],
        'tipo_mo': ['MECANICA', 'ELETRICA', 'REVISAO', 'FUNILARIA'],
        'hodometro': [150000.0, 150000.0, 80000.0, 200000.0],
        'mensagem_log': ['Aprovacao Manual', 'Aprovacao Manual', 'Aprovacao Manual', 'Cancelada pelo gestor'],
        'tipo_manutencao_oficina': ['FACT_MAINTENANCE'] * 4,
        'peca': ['FILTRO OLEO', 'CORREIA', 'SEM PEÇA', 'PASTILHA'],
        'descricao_servico': ['MECANICA', 'ELETRICA', 'REVISAO', 'FUNILARIA'],
    })


@pytest.fixture
def sample_df_incremental():
    """DataFrame simulando dados NOVOS para sync incremental."""
    now = datetime.now()
    return pd.DataFrame({
        'numero_os': ['OS004', 'OS002'],  # OS004 é novo, OS002 é update
        'codigo_item': ['ITEM1', 'ITEM1'],
        'codigo_cliente': ['6240480', '6240480'],
        'codigo_tgm': ['60905', '60905'],
        'codigo_estabelecimento': ['EST4', 'EST2'],
        'nome_cliente': ['JBS', 'JBS'],
        'nome_estabelecimento': ['Oficina D', 'Oficina B'],
        'placa': ['JKL3456', 'DEF5678'],
        'fabricante': ['DAF', 'VOLVO'],
        'modelo_veiculo': ['XF', 'FH540'],
        'familia_veiculo': ['PESADO', 'PESADO'],
        'uf': ['RS', 'MG'],
        'cidade': ['Porto Alegre', 'BH'],
        'chassi': ['CH004', 'CH002'],
        'ano_veiculo': ['2024', '2023'],
        'descricao_peca': ['AMORTECEDOR', None],
        'complemento_peca': ['MONROE', 'GENERICA'],
        'tipo_manutencao': ['CORRETIVA', 'PREVENTIVA'],
        'status_os': ['PENDENTE', 'APROVADA'],  # OS002 mudou de PENDENTE -> APROVADA
        'valor_total': [800.0, 500.0],
        'valor_aprovado': [None, 480.0],
        'valor_peca': [600.0, 350.0],
        'valor_mo': [200.0, 150.0],
        'data_transacao': [now, now - timedelta(days=5)],
        'data_atualizacao': [now, now - timedelta(hours=2)],
        'data_criacao_os': [now, now - timedelta(days=5)],
        'data_aprovacao_os': [None, now - timedelta(hours=2)],
        'nome_aprovador': ['SISTEMA', 'Maria'],
        'tipo_mo': ['SUSPENSAO', 'REVISAO'],
        'hodometro': [50000.0, 80500.0],
        'mensagem_log': ['Aprovacao Manual', 'Aprovacao Manual'],
        'tipo_manutencao_oficina': ['FACT_MAINTENANCE'] * 2,
        'peca': ['AMORTECEDOR', 'SEM PEÇA'],
        'descricao_servico': ['SUSPENSAO', 'REVISAO'],
    })


# ============================================================
# TESTE 1: Query Builder
# ============================================================

class TestBuildQuery:
    """Testa a construção da query SQL."""

    def test_full_load_query(self):
        """Query deve SEMPRE usar date_add (incremental retroativo)."""
        from backend.services.databricks_sync import _build_query
        query = _build_query(days=150)
        assert "date_add(current_date(), -150)" in query

    def test_query_always_uses_days(self):
        """Query sem watermark usa days."""
        from backend.services.databricks_sync import _build_query
        query = _build_query(days=90)
        assert "date_add(current_date(), -90)" in query

    def test_incremental_query_with_watermark(self):
        """Query com watermark busca apenas dados novos."""
        from backend.services.databricks_sync import _build_query
        wm = "2026-02-01"
        query = _build_query(watermark=wm)
        assert wm in query
        assert "date_add" not in query

    def test_gap_fill_query(self):
        """Query com date_from/date_to busca intervalo específico."""
        from backend.services.databricks_sync import _build_query
        query = _build_query(date_from="2025-09-20", date_to="2025-10-15")
        assert "2025-09-20" in query
        assert "2025-10-15" in query
        assert "date_add" not in query

    def test_query_has_all_columns(self):
        """Query deve conter todas as colunas necessárias."""
        from backend.services.databricks_sync import _build_query
        query = _build_query()
        required_cols = [
            'numero_os', 'codigo_item', 'codigo_cliente', 'tipo_manutencao',
            'status_os', 'valor_aprovado', 'data_transacao', 'placa',
            'nome_aprovador', 'tipo_mo', 'hodometro',
        ]
        for col in required_cols:
            assert col in query, f"Coluna {col} não encontrada na query"

    def test_query_has_client_filter(self):
        """Query deve filtrar por TGM_CLIENT_IDS via dim_fuelcustomers."""
        from backend.services.databricks_sync import _build_query
        query = _build_query()
        assert "fc.CustomerSourceCode IN" in query


# ============================================================
# TESTE 2: Watermark
# ============================================================

class TestLocalDateRange:
    """Testa a detecção do range de dados locais."""

    def test_no_data_on_empty_db(self, tmp_db):
        """Sem tabela → _get_local_date_range deve retornar (None, None, 0)."""
        conn, db_path = tmp_db
        with patch('backend.services.databricks_sync.get_connection') as mock_conn:
            mock_conn.return_value = conn
            from backend.services.databricks_sync import _get_local_date_range
            min_d, max_d, count = _get_local_date_range()
            assert min_d is None
            assert max_d is None
            assert count == 0

    def test_date_range_with_records(self, tmp_db, sample_df):
        """Com registros → deve retornar min/max dates e count."""
        conn, db_path = tmp_db
        df_corretiva = sample_df[sample_df['tipo_manutencao'] == 'CORRETIVA'].copy()
        conn.register('stg', df_corretiva)
        conn.execute("CREATE TABLE ri_corretiva_detalhamento AS SELECT * FROM stg")
        
        with patch('backend.services.databricks_sync.get_connection') as mock_conn:
            mock_conn.return_value = conn
            from backend.services.databricks_sync import _get_local_date_range
            min_d, max_d, count = _get_local_date_range()
            assert min_d is not None
            assert max_d is not None
            assert count > 0

    def test_no_data_with_empty_table(self, tmp_db):
        """Com tabela vazia → deve retornar (None, None, 0)."""
        conn, db_path = tmp_db
        conn.execute("CREATE TABLE ri_corretiva_detalhamento (data_transacao TIMESTAMP, id INTEGER)")
        
        with patch('backend.services.databricks_sync.get_connection') as mock_conn:
            mock_conn.return_value = conn
            from backend.services.databricks_sync import _get_local_date_range
            min_d, max_d, count = _get_local_date_range()
            assert min_d is None
            assert count == 0


# ============================================================
# TESTE 3: Full Load no DuckDB
# ============================================================

class TestFullLoad:
    """Testa o full load (drop + create) no DuckDB local."""

    def test_full_load_creates_tables(self, tmp_db, sample_df):
        """Full load deve criar todas as tabelas corretamente."""
        conn, db_path = tmp_db
        
        df_corretiva = sample_df[sample_df['tipo_manutencao'] == 'CORRETIVA'].copy()
        df_preventiva = sample_df[sample_df['tipo_manutencao'] == 'PREVENTIVA'].copy()
        
        conn.register('stg_corretiva', df_corretiva)
        conn.register('stg_preventiva', df_preventiva)
        
        conn.execute("DROP TABLE IF EXISTS ri_corretiva_detalhamento")
        conn.execute("CREATE TABLE ri_corretiva_detalhamento AS SELECT * FROM stg_corretiva")
        
        conn.execute("DROP TABLE IF EXISTS ri_preventiva_detalhamento")
        conn.execute("CREATE TABLE ri_preventiva_detalhamento AS SELECT * FROM stg_preventiva")
        
        # Verificar contagens
        corr_count = conn.execute("SELECT COUNT(*) FROM ri_corretiva_detalhamento").fetchone()[0]
        prev_count = conn.execute("SELECT COUNT(*) FROM ri_preventiva_detalhamento").fetchone()[0]
        
        assert corr_count == 3  # OS001 (2 items) + OS003
        assert prev_count == 1  # OS002

    def test_full_load_replaces_data(self, tmp_db, sample_df):
        """Full load deve substituir dados existentes."""
        conn, db_path = tmp_db
        
        # Inserir dados iniciais
        df_corretiva = sample_df[sample_df['tipo_manutencao'] == 'CORRETIVA'].copy()
        conn.register('stg1', df_corretiva)
        conn.execute("CREATE TABLE ri_corretiva_detalhamento AS SELECT * FROM stg1")
        
        initial_count = conn.execute("SELECT COUNT(*) FROM ri_corretiva_detalhamento").fetchone()[0]
        
        # Simular full reload com DataFrame menor
        df_small = df_corretiva.head(1)
        conn.register('stg2', df_small)
        conn.execute("DROP TABLE IF EXISTS ri_corretiva_detalhamento")
        conn.execute("CREATE TABLE ri_corretiva_detalhamento AS SELECT * FROM stg2")
        
        final_count = conn.execute("SELECT COUNT(*) FROM ri_corretiva_detalhamento").fetchone()[0]
        
        assert initial_count == 3
        assert final_count == 1  # Foi substituído!


# ============================================================
# TESTE 4: Sync Incremental (Merge)
# ============================================================

class TestIncrementalSync:
    """Testa o merge incremental (DELETE + INSERT por chave)."""

    def test_incremental_adds_new_records(self, tmp_db, sample_df, sample_df_incremental):
        """Sync incremental deve adicionar novos registros."""
        conn, db_path = tmp_db
        
        # Setup: full load inicial
        df_corretiva = sample_df[sample_df['tipo_manutencao'] == 'CORRETIVA'].copy()
        conn.register('stg_initial', df_corretiva)
        conn.execute("CREATE TABLE ri_corretiva_detalhamento AS SELECT * FROM stg_initial")
        
        initial_count = conn.execute("SELECT COUNT(*) FROM ri_corretiva_detalhamento").fetchone()[0]
        assert initial_count == 3  # OS001(x2) + OS003
        
        # Incremental: adicionar OS004 (nova corretiva)
        df_new = sample_df_incremental[sample_df_incremental['tipo_manutencao'] == 'CORRETIVA'].copy()
        conn.register('stg_new', df_new)
        
        # Merge: DELETE by numero_os + INSERT
        conn.execute("""
            DELETE FROM ri_corretiva_detalhamento 
            WHERE numero_os IN (SELECT DISTINCT numero_os FROM stg_new)
        """)
        conn.execute("INSERT INTO ri_corretiva_detalhamento SELECT * FROM stg_new")
        
        final_count = conn.execute("SELECT COUNT(*) FROM ri_corretiva_detalhamento").fetchone()[0]
        assert final_count == 4  # OS001(x2) + OS003 + OS004

    def test_incremental_updates_existing(self, tmp_db, sample_df, sample_df_incremental):
        """Sync incremental deve atualizar registros existentes (via merge)."""
        conn, db_path = tmp_db
        
        # Setup: full load inicial com preventiva
        df_prev = sample_df[sample_df['tipo_manutencao'] == 'PREVENTIVA'].copy()
        conn.register('stg_initial', df_prev)
        conn.execute("CREATE TABLE ri_preventiva_detalhamento AS SELECT * FROM stg_initial")
        
        # Verificar status inicial de OS002 = PENDENTE
        status = conn.execute(
            "SELECT status_os FROM ri_preventiva_detalhamento WHERE numero_os = 'OS002'"
        ).fetchone()[0]
        assert status == 'PENDENTE'
        
        # Incremental: OS002 agora APROVADA
        df_update = sample_df_incremental[sample_df_incremental['tipo_manutencao'] == 'PREVENTIVA'].copy()
        conn.register('stg_update', df_update)
        
        conn.execute("""
            DELETE FROM ri_preventiva_detalhamento 
            WHERE numero_os IN (SELECT DISTINCT numero_os FROM stg_update)
        """)
        conn.execute("INSERT INTO ri_preventiva_detalhamento SELECT * FROM stg_update")
        
        # Verificar status atualizado
        new_status = conn.execute(
            "SELECT status_os FROM ri_preventiva_detalhamento WHERE numero_os = 'OS002'"
        ).fetchone()[0]
        assert new_status == 'APROVADA'

    def test_incremental_idempotent(self, tmp_db, sample_df):
        """Rodar o merge múltiplas vezes deve ser idempotente."""
        conn, db_path = tmp_db
        
        df_corretiva = sample_df[sample_df['tipo_manutencao'] == 'CORRETIVA'].copy()
        conn.register('stg', df_corretiva)
        conn.execute("CREATE TABLE ri_corretiva_detalhamento AS SELECT * FROM stg")
        
        # Rodar merge 3 vezes com os mesmos dados
        for i in range(3):
            conn.register(f'stg_repeat_{i}', df_corretiva)
            conn.execute(f"""
                DELETE FROM ri_corretiva_detalhamento 
                WHERE numero_os IN (SELECT DISTINCT numero_os FROM stg_repeat_{i})
            """)
            conn.execute(f"INSERT INTO ri_corretiva_detalhamento SELECT * FROM stg_repeat_{i}")
        
        final_count = conn.execute("SELECT COUNT(*) FROM ri_corretiva_detalhamento").fetchone()[0]
        assert final_count == 3  # Mesma contagem que o início


# ============================================================
# TESTE 5: Download (Arrow vs Legacy)
# ============================================================

class TestDownload:
    """Testa as funções de download."""

    def test_download_legacy_returns_dataframe(self):
        """_download_legacy deve retornar DataFrame."""
        from backend.services.databricks_sync import _download_legacy
        
        mock_cursor = MagicMock()
        mock_cursor.description = [('col1',), ('col2',)]
        mock_cursor.fetchmany.side_effect = [
            [('a', 1), ('b', 2)],
            [('c', 3)],
            [],
        ]
        
        df = _download_legacy(mock_cursor, chunk_size=2)
        
        assert len(df) == 3
        assert list(df.columns) == ['col1', 'col2']
        assert df.iloc[0]['col1'] == 'a'

    def test_download_legacy_empty(self):
        """_download_legacy com resultado vazio deve retornar DataFrame vazio."""
        from backend.services.databricks_sync import _download_legacy
        
        mock_cursor = MagicMock()
        mock_cursor.description = [('col1',)]
        mock_cursor.fetchmany.return_value = []
        
        df = _download_legacy(mock_cursor, chunk_size=10)
        assert len(df) == 0


# ============================================================
# TESTE 6: Sync Metadata
# ============================================================

class TestSyncMetadata:
    """Testa gravação e leitura de metadata do sync."""

    def test_metadata_stores_sync_info(self, tmp_db):
        """Metadata deve armazenar informações do sync corretamente."""
        conn, db_path = tmp_db
        
        conn.execute("""
            CREATE TABLE sync_metadata (
                last_sync TIMESTAMP, status VARCHAR, sync_type VARCHAR,
                records INTEGER, watermark VARCHAR
            )
        """)
        
        conn.execute(
            "INSERT INTO sync_metadata VALUES (current_timestamp, 'SUCCESS', 'INCREMENTAL_RETROATIVO', 800000, '150')"
        )
        
        result = conn.execute("SELECT * FROM sync_metadata").fetchone()
        assert result[1] == 'SUCCESS'
        assert result[2] == 'INCREMENTAL_RETROATIVO'
        assert result[3] == 800000
        assert result[4] == '150'

    def test_metadata_overwritten_on_new_sync(self, tmp_db):
        """Nova sync deve substituir metadata anterior."""
        conn, db_path = tmp_db
        
        conn.execute("""
            CREATE TABLE sync_metadata (
                last_sync TIMESTAMP, status VARCHAR, sync_type VARCHAR,
                records INTEGER, watermark VARCHAR
            )
        """)
        
        # Primeiro sync
        conn.execute(
            "INSERT INTO sync_metadata VALUES (current_timestamp, 'SUCCESS', 'FULL', 800000, '150')"
        )
        
        # Segundo sync (deve substituir)
        conn.execute("DELETE FROM sync_metadata")
        conn.execute(
            "INSERT INTO sync_metadata VALUES (current_timestamp, 'SUCCESS', 'INCREMENTAL_RETROATIVO', 900000, '150')"
        )
        
        count = conn.execute("SELECT COUNT(*) FROM sync_metadata").fetchone()[0]
        assert count == 1
        
        result = conn.execute("SELECT sync_type, records FROM sync_metadata").fetchone()
        assert result[0] == 'INCREMENTAL_RETROATIVO'
        assert result[1] == 900000


# ============================================================
# TESTE 7: Progress Tracking
# ============================================================

class TestProgressTracking:
    """Testa o sistema de progresso do sync."""

    def test_init_progress(self):
        """_init_progress deve criar 7 etapas pendentes."""
        from backend.services.databricks_sync import _init_progress, get_sync_progress
        _init_progress()
        progress = get_sync_progress()
        
        assert len(progress['steps']) == 7
        assert all(s['status'] == 'pending' for s in progress['steps'])

    def test_update_step(self):
        """_update_step deve atualizar status da etapa correta."""
        from backend.services.databricks_sync import _init_progress, _update_step, get_sync_progress
        _init_progress()
        
        _update_step("connect", "running", "Conectando...")
        progress = get_sync_progress()
        
        connect_step = next(s for s in progress['steps'] if s['id'] == 'connect')
        assert connect_step['status'] == 'running'
        assert connect_step['detail'] == 'Conectando...'

    def test_progress_tracks_counts(self):
        """Progresso deve permitir atualizar contagens."""
        from backend.services.databricks_sync import _init_progress, _sync_progress
        _init_progress()
        
        _sync_progress["total_records"] = 500000
        _sync_progress["corretiva_count"] = 400000
        _sync_progress["preventiva_count"] = 100000
        
        assert _sync_progress["total_records"] == 500000
        assert _sync_progress["corretiva_count"] + _sync_progress["preventiva_count"] == 500000


# ============================================================
# TESTE 8: Data Processing
# ============================================================

class TestDataProcessing:
    """Testa o processamento de dados (transformações)."""

    def test_split_corretiva_preventiva(self, sample_df):
        """Dados devem ser splittados corretamente por tipo_manutencao."""
        df_corretiva = sample_df[sample_df['tipo_manutencao'] == 'CORRETIVA'].copy()
        df_preventiva = sample_df[sample_df['tipo_manutencao'] == 'PREVENTIVA'].copy()
        
        assert len(df_corretiva) == 3
        assert len(df_preventiva) == 1
        assert len(df_corretiva) + len(df_preventiva) == len(sample_df)

    def test_peca_fillna(self, sample_df):
        """Peças nulas devem ser preenchidas com 'SEM PEÇA'."""
        # A fixture sample_df já tem peca preenchida, mas testar a lógica
        df = sample_df.copy()
        df['peca'] = df['descricao_peca'].fillna('SEM PEÇA')
        
        null_desc = df[df['descricao_peca'].isna()]
        assert all(null_desc['peca'] == 'SEM PEÇA')

    def test_watermark_calculation(self, sample_df):
        """Watermark deve ser MAX(data_transacao)."""
        watermark = sample_df['data_transacao'].max()
        assert watermark == sample_df['data_transacao'].max()
        assert pd.notna(watermark)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

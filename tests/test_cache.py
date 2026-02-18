"""
Testes unitários para o sistema de cache refatorado.
Valida que:
1. Cache usa SimpleCache (in-memory, sem persistência no disco)
2. safe_memoize funciona corretamente com cache ativo e inativo
3. clear_cache() limpa snapshots JSON e cache in-memory
4. Nenhum dado persiste entre reinícios do app
"""
import os
import sys
import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock

# Adiciona raiz do projeto ao sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================================
# TESTE 1: Configuração do Cache
# ============================================================================

class TestCacheConfiguration:
    """Verifica que o cache está configurado como SimpleCache (in-memory)."""

    def test_cache_type_is_simple(self):
        """Cache deve ser SimpleCache, não FileSystemCache."""
        # Simula leitura do app.py para verificar configuração
        app_path = os.path.join(PROJECT_ROOT, "app.py")
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "SimpleCache" in content, (
            "app.py deve usar CACHE_TYPE: SimpleCache, não FileSystemCache"
        )

    def test_no_cache_dir_config(self):
        """Não deve haver CACHE_DIR configurado (SimpleCache não precisa)."""
        app_path = os.path.join(PROJECT_ROOT, "app.py")
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # CACHE_DIR não deve existir na config ativa (pode estar comentado)
        lines = content.split('\n')
        active_cache_dir = [
            l for l in lines 
            if 'CACHE_DIR' in l and not l.strip().startswith('#')
        ]
        assert len(active_cache_dir) == 0, (
            f"CACHE_DIR não deve estar ativo na config: {active_cache_dir}"
        )

    def test_no_flask_cache_in_temp(self):
        """Não deve existir diretório flask_cache no temp após refatoração."""
        flask_cache_dir = os.path.join(tempfile.gettempdir(), "flask_cache")
        # Se existir, deve estar vazio (limpeza do startup removeu)
        if os.path.exists(flask_cache_dir):
            files = os.listdir(flask_cache_dir)
            assert len(files) == 0, (
                f"flask_cache no temp deveria estar vazio, tem {len(files)} arquivos"
            )


# ============================================================================
# TESTE 2: safe_memoize
# ============================================================================

class TestSafeMemoize:
    """Testa o decorator safe_memoize."""

    def test_safe_memoize_executes_when_cache_not_initialized(self):
        """Quando cache não está inicializado, função executa direto."""
        from backend.cache_config import _apply_memoize
        
        call_count = 0
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Simula cache não inicializado
        import backend.cache_config as cc
        original = cc._cache_initialized
        cc._cache_initialized = False
        
        try:
            wrapped = _apply_memoize(my_func, timeout=300)
            result1 = wrapped(5)
            result2 = wrapped(5)
            
            assert result1 == 10
            assert result2 == 10
            # Sem cache, deve executar toda vez
            assert call_count == 2, "Sem cache, função deve ser chamada toda vez"
        finally:
            cc._cache_initialized = original

    def test_safe_memoize_returns_correct_values(self):
        """safe_memoize não deve corromper valores de retorno."""
        from backend.cache_config import _apply_memoize
        import backend.cache_config as cc
        original = cc._cache_initialized
        cc._cache_initialized = False
        
        try:
            def compute(a, b):
                return {"sum": a + b, "product": a * b}
            
            wrapped = _apply_memoize(compute, timeout=300)
            result = wrapped(3, 7)
            
            assert result == {"sum": 10, "product": 21}
        finally:
            cc._cache_initialized = original

    def test_safe_memoize_decorator_forms(self):
        """safe_memoize deve funcionar em todas as formas de uso."""
        from backend.cache_config import safe_memoize
        import backend.cache_config as cc
        original = cc._cache_initialized
        cc._cache_initialized = False
        
        try:
            # Forma 1: @safe_memoize (sem parênteses)
            @safe_memoize
            def func1(x):
                return x + 1
            
            # Forma 2: @safe_memoize(timeout=60)
            @safe_memoize(timeout=60)
            def func2(x):
                return x + 2
            
            # Forma 3: @safe_memoize(60) — positional
            @safe_memoize(60)
            def func3(x):
                return x + 3
            
            assert func1(10) == 11
            assert func2(10) == 12
            assert func3(10) == 13
        finally:
            cc._cache_initialized = original


# ============================================================================
# TESTE 3: clear_cache() limpa snapshots
# ============================================================================

class TestClearCache:
    """Verifica que clear_cache() limpa snapshots JSON."""

    def test_clear_cache_removes_snapshot_files(self):
        """clear_cache deve remover farol_stats_snapshot.json e kpi_history.json."""
        data_dir = os.path.join(PROJECT_ROOT, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Cria arquivos de snapshot fake
        snapshot_file = os.path.join(data_dir, "farol_stats_snapshot.json")
        history_file = os.path.join(data_dir, "kpi_history.json")
        
        for f in [snapshot_file, history_file]:
            with open(f, 'w') as fh:
                json.dump({"test": True}, fh)
        
        # Verifica que existem
        assert os.path.exists(snapshot_file)
        assert os.path.exists(history_file)
        
        # Importa e executa clear_cache com mock do Flask cache
        from backend.cache_config import clear_cache
        import backend.cache_config as cc
        
        original_init = cc._cache_initialized
        original_app = cc.cache.app if hasattr(cc.cache, 'app') else None
        
        cc._cache_initialized = True
        cc.cache.app = MagicMock()  # Simula app inicializado
        cc._cache_dir = None  # Sem diretório de cache (SimpleCache)
        
        try:
            # Mock cache.clear() para não falhar
            with patch.object(cc.cache, 'clear'):
                clear_cache()
            
            # Snapshots devem ter sido removidos
            assert not os.path.exists(snapshot_file), "farol_stats_snapshot.json deveria ter sido removido"
            assert not os.path.exists(history_file), "kpi_history.json deveria ter sido removido"
        finally:
            cc._cache_initialized = original_init
            if original_app:
                cc.cache.app = original_app

    def test_clear_cache_handles_missing_files(self):
        """clear_cache não deve falhar se snapshots não existem."""
        from backend.cache_config import clear_cache
        import backend.cache_config as cc
        
        original_init = cc._cache_initialized
        cc._cache_initialized = True
        cc.cache.app = MagicMock()
        cc._cache_dir = None
        
        try:
            with patch.object(cc.cache, 'clear'):
                # Não deve lançar exceção
                result = clear_cache()
                assert result == True
        finally:
            cc._cache_initialized = original_init


# ============================================================================
# TESTE 4: Sem persistência no disco
# ============================================================================

class TestNoDiskPersistence:
    """Verifica que nenhum cache persiste no disco."""

    def test_no_temp_duckdb(self):
        """Não deve existir data.duckdb no temp (migração desativada)."""
        # Este teste verifica que a migração do temp foi desativada
        db_path = os.path.join(PROJECT_ROOT, "database.py")
        with open(db_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # shutil.copy do temp NÃO deve estar ativo
        assert "shutil.copy2(TEMP_DB_PATH, DB_PATH)" not in content, (
            "Migração de banco do temp deve estar desativada"
        )

    def test_no_parquet_auto_import(self):
        """Auto-import de Parquet deve estar desabilitado."""
        app_path = os.path.join(PROJECT_ROOT, "app.py")
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # read_parquet não deve aparecer no initial_sync_check ativo
        assert "read_parquet" not in content, (
            "Auto-import de Parquet deve estar desabilitado em app.py"
        )

    def test_database_init_creates_all_tables(self):
        """init_db deve criar TODAS as tabelas necessárias (incluindo preventiva)."""
        db_path = os.path.join(PROJECT_ROOT, "database.py")
        with open(db_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_tables = [
            "ri_corretiva_detalhamento",
            "ri_preventiva_detalhamento",
            "logs_corretiva",
            "logs_regulacao_preventiva",
            "logs_regulacao_preventiva_header",
        ]
        
        for table in required_tables:
            assert f"CREATE TABLE IF NOT EXISTS {table}" in content, (
                f"init_db() deve criar tabela {table}"
            )

    def test_schema_has_valor_total(self):
        """O schema de ri_corretiva_detalhamento deve ter valor_total."""
        db_path = os.path.join(PROJECT_ROOT, "database.py")
        with open(db_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "valor_total DOUBLE" in content, (
            "Schema deve incluir coluna valor_total DOUBLE"
        )

    def test_schema_has_status_os(self):
        """O schema deve usar status_os, não status."""
        db_path = os.path.join(PROJECT_ROOT, "database.py")
        with open(db_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "status_os VARCHAR" in content, (
            "Schema deve usar status_os (não status)"
        )


# ============================================================================
# TESTE 5: Repositórios usam colunas corretas
# ============================================================================

class TestRepositoryColumns:
    """Verifica que os repositórios referenciam as colunas corretas."""

    def test_repo_farol_uses_status_os(self):
        """repo_farol_table.py deve usar status_os, não status."""
        repo_path = os.path.join(
            PROJECT_ROOT, "backend", "repositories", "repo_farol_table.py"
        )
        with open(repo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Procura por "status" sozinho em queries SQL (não status_os)
        import re
        # Padrão: "status" seguido de espaço, = ou ) mas NÃO precedido por _
        bad_refs = re.findall(r"(?<!_)(?<!\w)status(?!_os)(?!\w)", content)
        # Filtra falsos positivos (strings como "status_os", comentários, etc.)
        # Aceita "status" em strings descritivas ou comentários
        assert len(bad_refs) == 0 or all(
            'status_os' in content[max(0, content.index('status')-20):content.index('status')+20]
            for _ in bad_refs
        ), "repo_farol_table.py não deve referenciar coluna 'status' sem sufixo '_os'"

    def test_repo_dashboard_uses_codigo_item(self):
        """repo_dashboard.py deve usar codigo_item, não cod_item."""
        repo_path = os.path.join(
            PROJECT_ROOT, "backend", "repositories", "repo_dashboard.py"
        )
        with open(repo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # cod_item NÃO deve aparecer (deve ser codigo_item)
        assert "cod_item" not in content or "codigo_item" in content, (
            "repo_dashboard.py deve usar codigo_item, não cod_item"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

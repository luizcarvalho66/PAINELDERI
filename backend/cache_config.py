from flask_caching import Cache
from functools import wraps

# Inicializa o objeto Cache (será configurado no app.py)
# Exportado aqui para evitar ciclos de importação
cache = Cache()

# Flag para verificar se o cache foi inicializado
_cache_initialized = False

# Armazena o diretório de cache para limpeza manual
_cache_dir = None


import hashlib
import json

def _make_cache_key(func, args, kwargs):
    """Gera uma chave única e segura para o cache baseada nos argumentos."""
    def _default(obj):
        # Fallback para objetos não serializáveis
        return str(obj)

    try:
        # Serializa args e kwargs para JSON de forma consistente (ordenada)
        key_data = {
            "module": func.__module__,
            "name": func.__name__,
            "args": args,
            "kwargs": kwargs
        }
        # sort_keys=True garante que dicts com mesma data e ordem diferente gerem mesmo hash
        key_str = json.dumps(key_data, sort_keys=True, default=_default)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"[CACHE KEY ERROR] Falha ao gerar chave para {func.__name__}: {e}")
        return None

def _apply_memoize(func, timeout):
    """Lógica interna do wrapper de cache (Implementação Manual Get/Set)."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        global _cache_initialized
        
        # Se cache NÃO inicializado, executa direto
        if not _cache_initialized or not cache.app:
            return func(*args, **kwargs)
            
        try:
            # 1. Gerar chave de cache
            cache_key = _make_cache_key(func, args, kwargs)
            if not cache_key:
                return func(*args, **kwargs)
            
            # 2. Tentar recuperar do cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                # print(f"[CACHE HIT] {func.__name__}")
                return cached_value
            
            # 3. Executar função e salvar no cache
            # print(f"[CACHE MISS] Executing {func.__name__}")
            result = func(*args, **kwargs)
            
            # Só cacheia se o resultado não for None (opcional, mas boa prática)
            if result is not None:
                try:
                    cache.set(cache_key, result, timeout=timeout)
                except Exception as cache_err:
                    # DataFrame grande ou não serializável - segue sem cache
                    print(f"[CACHE SET WARNING] Falha ao salvar no cache ({func.__name__}): {cache_err}")
                
            return result
            
        except Exception as e:
            print(f"[CACHE WARNING] Falha no mecanismo de cache manual: {e}")
            return func(*args, **kwargs)
            
    return wrapper

def safe_memoize(func=None, timeout=300):
    """
    Decorator wrapper seguro para memoize.
    Suporta uso como:
      @safe_memoize
      @safe_memoize(timeout=60)
      @safe_memoize(60)
    """
    # Caso: @safe_memoize(60) -> func captura o inteiro posicional
    if func is not None and not callable(func):
        timeout = func
        func = None

    # Caso: @safe_memoize (sem parenteses) -> func é a função
    if func is not None and callable(func):
        return _apply_memoize(func, timeout)

    # Caso: @safe_memoize(timeout=xyz) -> retorna decorator
    def decorator(f):
        return _apply_memoize(f, timeout)
    return decorator



def mark_cache_initialized(cache_dir=None):
    """Marca o cache como inicializado. Chamado após cache.init_app()"""
    global _cache_initialized, _cache_dir
    _cache_initialized = True
    _cache_dir = cache_dir
    print(f"[CACHE] Cache marcado como inicializado (dir: {cache_dir})")

def clear_cache():
    """
    Limpa todo o cache do aplicativo.
    Chamado após sync do Databricks para garantir que os dados antigos não persistam.
    Com SimpleCache, limpa o dict in-memory + snapshots JSON no disco.
    """
    global _cache_initialized, _cache_dir
    import os
    
    if _cache_initialized and cache.app:
        try:
            print("[CACHE] Iniciando limpeza total...")
            
            # 1. Limpa cache in-memory (SimpleCache)
            cache.clear()
            
            # 2. Limpar JSONs de snapshot/histórico que persistem dados antigos
            data_dir = os.path.join(os.getcwd(), "data")
            snapshot_files = [
                os.path.join(data_dir, "farol_stats_snapshot.json"),
                os.path.join(data_dir, "kpi_history.json"),
            ]
            for sf in snapshot_files:
                if os.path.exists(sf):
                    try:
                        os.unlink(sf)
                        print(f"[CACHE] Snapshot removido: {os.path.basename(sf)}")
                    except Exception as e:
                        print(f"[CACHE] Falha ao remover snapshot {sf}: {e}")
            
            print("[CACHE] Limpeza concluída com sucesso.")
            return True
        except Exception as e:
            print(f"[CACHE ERROR] Erro durante o flush do cache: {e}")
    return False


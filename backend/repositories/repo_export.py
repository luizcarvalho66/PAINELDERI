import pandas as pd
from backend.repositories.repo_base import get_readonly_connection

def get_export_data(filters: dict = None, limit: int = None):
    conn = get_readonly_connection()
    if not conn: return pd.DataFrame()
    
    where_conditions = ["status_os != 'CANCELADA'"]
    if filters and filters.get("clientes"):
        valid_clients = [str(c) for c in filters["clientes"] if c and str(c).strip() != ""]
        if valid_clients:
            clients_escaped = "', '".join([c.replace("'", "''") for c in valid_clients])
            where_conditions.append(f"nome_cliente IN ('{clients_escaped}')")
            
    if filters and filters.get("periodos"):
        period_clauses = []
        for p in filters["periodos"]:
            try:
                year, month = p.split("-")
                period_clauses.append(f"(year(data_transacao) = {year} AND month(data_transacao) = {month})")
            except Exception:
                pass
        if period_clauses:
            where_conditions.append(f"({' OR '.join(period_clauses)})")
            
    where_clause = " AND ".join(where_conditions)
    
    columns = """
        numero_os, data_transacao, nome_cliente, nome_estabelecimento, 
        placa, fabricante, modelo_veiculo, familia_veiculo, uf, cidade, chassi, ano_veiculo, 
        tipo_manutencao, peca, descricao_servico, valor_total, valor_aprovado, valor_peca, valor_mo,
        data_criacao_os, data_aprovacao_os, nome_aprovador, tipo_mo, hodometro, 
        mensagem_log, detalhe_regulacao, silent_order_pbi, status_os
    """
    
    query = f"""
    SELECT {columns}, 'CORRETIVA' as origem FROM ri_corretiva_detalhamento WHERE {where_clause}
    UNION ALL
    SELECT {columns}, 'PREVENTIVA' as origem FROM ri_preventiva_detalhamento WHERE {where_clause}
    ORDER BY data_transacao DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
        
    try:
        df = conn.execute(query).fetchdf()
        
        rename_map = {
            'numero_os': 'Número OS',
            'data_transacao': 'Data da Transação',
            'nome_cliente': 'Cliente',
            'nome_estabelecimento': 'Estabelecimento (EC)',
            'placa': 'Placa',
            'fabricante': 'Fabricante',
            'modelo_veiculo': 'Modelo do Veículo',
            'familia_veiculo': 'Família',
            'uf': 'UF',
            'cidade': 'Cidade',
            'chassi': 'Chassi',
            'ano_veiculo': 'Ano Veículo',
            'tipo_manutencao': 'Tipo de Manutenção',
            'peca': 'Serviço/Peça (Linha)',
            'descricao_servico': 'Desc. Serviço',
            'valor_total': 'Valor Solicitado Bruto',
            'valor_aprovado': 'Valor Aprovado Negociado',
            'valor_peca': 'Valor Peça',
            'valor_mo': 'Valor MO',
            'data_criacao_os': 'Data Criação OS',
            'data_aprovacao_os': 'Data Aprovação',
            'nome_aprovador': 'Aprovador TGM',
            'tipo_mo': 'Tipo MDO',
            'hodometro': 'Hodômetro',
            'mensagem_log': 'Mensagem Log (Regramentos)',
            'detalhe_regulacao': 'Detalhe Regulação',
            'silent_order_pbi': 'Aprovação Automática (SO)',
            'status_os': 'Status O.S',
            'origem': 'Classificação de Análise'
        }
        
        # Adjust types and format
        df['data_transacao'] = pd.to_datetime(df['data_transacao']).dt.strftime('%d/%m/%Y %H:%M')
        
        return df.rename(columns=rename_map)
    except Exception as e:
        print(f"[EXPORT REPOSITORY ERROR] {e}")
        return pd.DataFrame()

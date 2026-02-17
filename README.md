# Painel de Regulação Inteligente (RI) - Edenred

> **Corporate Analytics Solution** | _Databricks Apps Integration_

Este repositório contém o código-fonte da aplicação **Painel RI**, uma solução estratégica de _Business Intelligence_ desenvolvida para a **Edenred Repom**. O sistema atua como um motor de auditoria e visualização de dados, focado na otimização de custos de manutenção de frotas através da comparação entre modelos preventivos e corretivos.

---

## Contexto e Objetivo de Negócio

A Regulação Inteligente (RI) é o diferencial competitivo da operação de frotas. Este painel tem como objetivos centrais:

1.  **Auditoria Operacional:** Monitorar o cumprimento das regras de aprovação automática versus manual.
2.  **Eficiência Financeira:** Identificar _savings_ (economias) gerados pela negociação ativa de peças e mão-de-obra.
3.  **Visibilidade Estratégica ("Farol"):** Prover indicadores claros (Verde/Amarelo/Vermelho) sobre a saúde da operação de manutenção.
4.  **Apoio à Decisão:** Permitir que gestores filtrem dados por cliente, tipo de peça e período para tomadas de decisão baseadas em dados.

---

## Arquitetura Técnica

O projeto utiliza uma arquitetura **Modularizada** e **Serverless**, desenhada para alta performance e baixo custo de manutenção.

### Stack Tecnológico

- **Core:** Python 3.10+
- **Frontend Interativo:** [Dash Enterprise](https://dash.plotly.com/) (React.js wrapper para Python).
- **UI Framework:** Dash Bootstrap Components (Layout Responsivo e Executivo).
- **Data Engine:** [DuckDB](https://duckdb.org/) (Processamento analítico OLAP em memória) + Pandas.
- **Hospedagem:** Databricks Apps (Compute Serverless).
- **Gerenciamento de Dependências:** `pip` / `requirements.txt`.

### Padrão de Projeto (Design Pattern)

O código segue rigorosamente o princípio de **Responsabilidade Única (SRP)**:

1.  **frontend/**: Camada de Apresentação.
    - _Regra:_ Um componente visual = Um arquivo (Ex: `sidebar.py`, `farol_section.py`). Não contém lógica de negócios.
2.  **backend/**: Camada de Controle e Dados.
    - `callbacks/`: Gerencia a interatividade (Inputs/Outputs do Dash).
    - `repositories/`: Abstração de acesso aos dados. Contém as queries SQL otimizadas.
3.  **engine/**: Camada de Regra de Negócio (Core).
    - Responsável pelo ETL (Extract, Transform, Load) dos arquivos CSV/Excel.
    - Aplica as regras de "Farol" (limites de valores, SLAs).

---

## Lógica do Motor ("Engine")

O "coração" do sistema reside no diretório `engine/`. O fluxo de processamento segue as etapas:

1.  **Ingestão:** O sistema recebe planilhas de logs brutos (Preventiva e Corretiva).
2.  **Normalização:** Padronização de nomes de colunas, datas e tipos numéricos.
3.  **Cross-Reference (Cruzamento):**
    - O motor cruza dados de _Peças_ e _Mão de Obra_.
    - Calcula o delta entre valor orçado vs. valor aprovado.
4.  **Categorização (Lógica do Farol):**
    - Cada transação é classificada baseada em Regras de Negócio (ex: Desvio > 10% = Crítico).
    - Geração de estatísticas agregadas para os cartões de KPI.

---

## Guia de Desenvolvimento e Deploy

### 1. Ambiente Local (Recomendado)

Para garantir estabilidade e _Zero Downtime_, todo desenvolvimento é feito localmente no VS Code.

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação (Modo Debug)
python app.py
```

_Acesse em: `http://127.0.0.1:8050/`_

### 2. Processo de Validação

Antes de qualquer subida para produção, o código passa por:

- [x] Validação de sintaxe (Linting).
- [x] Teste de carga de dados (Verificação de Schema).
- [x] Validação visual dos gráficos no navegador local.

### 3. Deploy para Databricks (CI/CD)

Utilizamos scripts de automação (`PowerShell`) para sincronizar o código com o Workspace seguro da Edenred.

**Comando de Deploy:**

```powershell
.\scripts\deploy.ps1
```

_Este script realiza o handshake de autenticação (OAuth), sincroniza os arquivos modificados e reinicia o cluster da aplicação._

---

## Segurança e Governança

- **Autenticação:** Integrada ao padrão OAuth 2.0 do Databricks/Azure AD.
- **Dados:** Nenhum dado sensível é persistido no código. O processamento é volátil ou conectado a Data Lakes seguros.
- **Logs:** O sistema gera logs de execução para auditoria de erros e performance.

---

© 2025 Edenred - Todos os direitos reservados.
_Desenvolvido pela equipe de entrega de resultados.


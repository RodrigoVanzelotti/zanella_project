# Google Sheets Asset Allocation Module

Módulo completo para buscar e parsear dados de alocação de ativos do Google Sheets com validação e tipagem via Pydantic.

## 📁 Estrutura

```
google_sheets/
├── __init__.py                    # Exports do módulo
├── google_sheets_service.py       # Serviço para buscar dados do Google Sheets
├── asset_allocation_parser.py     # Parser para processar os dados
├── models.py                      # Modelos Pydantic para validação
├── example_usage.py               # Exemplo de uso completo
└── README.md                      # Esta documentação
```

## 🚀 Quick Start

```python
from app.services.google_sheets import (
    GoogleSheetsService,
    AssetAllocationParser,
    AssetAllocationData
)

# 1. Buscar dados do Google Sheets
service = GoogleSheetsService()
data = service.fetch_spreadsheet_rows("Nome da Planilha", skip_initial_rows=7)

# 2. Parsear os dados
parser = AssetAllocationParser()
al_detail, al_summary = parser.parse_general_allocation(data['Asset Allocation'][:22])
subtables = parser.parse_multiple_tables(data['Asset Allocation'])

# 3. Converter para modelos Pydantic (type-safe!)
asset_allocation: AssetAllocationData = parser.to_asset_allocation_data(
    general_allocation=(al_detail, al_summary),
    subtables=subtables
)

# 4. Acessar dados tipados
if asset_allocation.commodities:
    for investment in asset_allocation.commodities.rows:
        print(f"{investment.get_nome()}: ${investment.valor_atual_num:,.2f}")
```

## 📊 Modelos Disponíveis

### `AssetAllocationData`
Modelo raiz que contém toda a estrutura de alocação:
- `general_allocation`: Alocação geral (summary e detailed)
- `renda_fixa_brasil`: Renda Fixa Brasil (com blocos Curto/Médio/Longo)
- `commodities`: Commodities
- `stocks_us`: Ações US
- `world_stocks`: Ações mundiais
- `acoes_br`: Ações brasileiras
- `reits`: REITs
- `fundos_imobiliarios`: Fundos Imobiliários
- `criptos`: Criptomoedas

### `StandardInvestmentTable`
Modelo para tabelas padrão de investimentos:
```python
class StandardInvestmentTable:
    rows: List[StandardInvestmentRow]  # Linhas de investimentos
    total: InvestmentTotal              # Total da tabela
    
    @property
    def total_valor_investido_num(self) -> float  # Soma calculada
    
    @property
    def total_valor_atual_num(self) -> float      # Soma calculada
```

### `StandardInvestmentRow`
Linha individual de investimento com todos os campos:
```python
class StandardInvestmentRow:
    # Nomes (dependendo do tipo)
    nome_do_fundo: Optional[str]
    nome_da_empresa: Optional[str]
    nome_do_reit: Optional[str]
    nome_do_fii: Optional[str]
    
    # Dados básicos
    ticker: Optional[str]
    subsetor: Optional[str]
    onde: Optional[str]
    
    # Valores (string e numérico)
    qtd: Optional[str]
    qtd_num: Optional[float]
    
    preco_medio: Optional[str]
    preco_medio_num: Optional[float]
    
    valor_investido: Optional[str]
    valor_investido_num: Optional[float]
    
    valor_atual: Optional[str]
    valor_atual_num: Optional[float]
    
    # Percentuais
    pct_carteira: Optional[str]
    pct_carteira_pct: Optional[float]  # Como decimal (ex: 0.25 = 25%)
    
    # Helper method
    def get_nome(self) -> Optional[str]  # Retorna o nome independente do tipo
```

### `RendaFixaBrasil`
Estrutura especial para Renda Fixa Brasil:
```python
class RendaFixaBrasil:
    curto_prazo: Optional[RendaFixaBrasilBlock]
    medio_prazo: Optional[RendaFixaBrasilBlock]
    longo_prazo: Optional[RendaFixaBrasilBlock]
    total_renda_fixa_br: Optional[float]
```

## 🔄 Conversões Automáticas

O parser cria automaticamente colunas numéricas:

| Campo Original | Campo Numérico | Tipo |
|---------------|----------------|------|
| `qtd` | `qtd_num` | `float` |
| `preco_medio` | `preco_medio_num` | `float` |
| `valor_investido` | `valor_investido_num` | `float` |
| `valor_atual` | `valor_atual_num` | `float` |
| `pct_carteira` | `pct_carteira_pct` | `float` (decimal) |

## 📤 Exportação

### Para JSON
```python
# Exportar para JSON (excluindo campos None)
json_str = asset_allocation.model_dump_json(indent=2, exclude_none=True)

# Salvar em arquivo
with open("asset_allocation.json", "w") as f:
    f.write(json_str)
```

### Para Dict
```python
# Converter para dicionário Python
data_dict = asset_allocation.model_dump(exclude_none=True)
```

## 💡 Exemplos de Uso

### Calcular Rentabilidade Total
```python
if asset_allocation.commodities:
    total_investido = asset_allocation.commodities.total_valor_investido_num
    total_atual = asset_allocation.commodities.total_valor_atual_num
    
    if total_investido and total_atual:
        rentabilidade = ((total_atual - total_investido) / total_investido) * 100
        print(f"Rentabilidade: {rentabilidade:.2f}%")
```

### Listar Todos os Investimentos
```python
for investment in asset_allocation.commodities.rows:
    print(f"""
    Nome: {investment.get_nome()}
    Ticker: {investment.ticker}
    Quantidade: {investment.qtd_num}
    Valor Investido: ${investment.valor_investido_num:,.2f}
    Valor Atual: ${investment.valor_atual_num:,.2f}
    Resultado: ${investment.resultado_num:,.2f}
    """)
```

### Filtrar por Corretora
```python
commodities_avenue = [
    inv for inv in asset_allocation.commodities.rows 
    if inv.onde and "avenue" in inv.onde.lower()
]
```

### Acessar Renda Fixa Brasil
```python
if asset_allocation.renda_fixa_brasil:
    # Curto prazo
    if asset_allocation.renda_fixa_brasil.curto_prazo:
        print(f"Curto Prazo: {len(asset_allocation.renda_fixa_brasil.curto_prazo.rows)} títulos")
        print(f"Total: R$ {asset_allocation.renda_fixa_brasil.curto_prazo.total:,.2f}")
    
    # Total geral
    print(f"Total BR: R$ {asset_allocation.renda_fixa_brasil.total_renda_fixa_br:,.2f}")
```

## ✅ Benefícios

1. **Type Safety**: Autocomplete e validação de tipos no IDE
2. **Validação Automática**: Pydantic valida os dados na criação
3. **Conversão Fácil**: JSON, dict, etc.
4. **Documentação**: Campos documentados via `Field(description=...)`
5. **Flexibilidade**: Campos opcionais para lidar com dados incompletos

## 🧪 Testes

Veja `example_usage.py` para um exemplo completo de uso.

## 📝 Notas

- Todos os valores monetários são mantidos como string E convertidos para float
- Percentuais são armazenados como decimais (0.25 = 25%)
- Campos `None` são automaticamente excluídos na exportação JSON
- O método `get_nome()` funciona para todos os tipos de investimentos

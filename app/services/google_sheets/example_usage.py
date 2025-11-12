"""
Exemplo de uso dos modelos Pydantic com o parser de Asset Allocation

Este exemplo demonstra como:
1. Fazer parse dos dados brutos do Google Sheets
2. Converter para modelos Pydantic tipados
3. Acessar os dados de forma estruturada e type-safe
"""

from app.services.google_sheets.google_sheets_service import GoogleSheetsService
from app.services.google_sheets.asset_allocation_parser import AssetAllocationParser

# Constantes
ASSET_ALLOCATION_INITIAL_ROW = 7
ASSET_ALLOCATION_SUMMARY_ROW = 22

# Inicializar serviços
google_client = GoogleSheetsService()
parser = AssetAllocationParser()

# Buscar dados do Google Sheets
data = google_client.fetch_spreadsheet_rows(
    "Rodrigo Vanzelotti", 
    skip_initial_rows=ASSET_ALLOCATION_INITIAL_ROW
)

# Parse dos dados brutos
asset_allocation_sheet = data['Asset Allocation']

# 1. Parse da alocação geral
al_detail, al_summary = parser.parse_general_allocation(
    asset_allocation_sheet[:ASSET_ALLOCATION_SUMMARY_ROW]
)

# 2. Parse de todas as sub-tabelas
subtables = parser.parse_multiple_tables(asset_allocation_sheet)

# 3. Converter tudo para modelo Pydantic
asset_allocation_model = parser.to_asset_allocation_data(
    general_allocation=(al_detail, al_summary),
    subtables=subtables
)

# ==================== Exemplos de Uso ====================

print("=== Alocação Geral - Summary ===")
if asset_allocation_model.general_allocation:
    for row in asset_allocation_model.general_allocation.summary:
        print(f"{row.asset_classes}: {row.valor_atual} ({row.pct_atual})")

print("\n=== Commodities ===")
if asset_allocation_model.commodities:
    for investment in asset_allocation_model.commodities.rows:
        nome = investment.get_nome()
        print(f"{nome} ({investment.ticker})")
        print(f"  Quantidade: {investment.qtd_num}")
        print(f"  Valor Investido: ${investment.valor_investido_num:,.2f}")
        print(f"  Valor Atual: ${investment.valor_atual_num:,.2f}")
        print(f"  Resultado: ${investment.resultado_num:,.2f}")
    
    print(f"\nTotal Commodities: {asset_allocation_model.commodities.total.label}")
    print(f"Valor Total: {asset_allocation_model.commodities.total.valor_investido}")

print("\n=== Stocks US ===")
if asset_allocation_model.stocks_us:
    for stock in asset_allocation_model.stocks_us.rows:
        print(f"{stock.get_nome()} ({stock.ticker})")
        print(f"  Qtd: {stock.qtd_num} | Atual: ${stock.valor_atual_num:,.2f}")

print("\n=== Ações BR ===")
if asset_allocation_model.acoes_br:
    for acao in asset_allocation_model.acoes_br.rows:
        print(f"{acao.get_nome()} ({acao.ticker})")
        if acao.pct_carteira_pct:
            print(f"  % Carteira: {acao.pct_carteira_pct*100:.2f}%")

print("\n=== Renda Fixa Brasil ===")
if asset_allocation_model.renda_fixa_brasil:
    if asset_allocation_model.renda_fixa_brasil.curto_prazo:
        print(f"Curto Prazo: R$ {asset_allocation_model.renda_fixa_brasil.curto_prazo.total:,.2f}")
        print(f"  {len(asset_allocation_model.renda_fixa_brasil.curto_prazo.rows)} títulos")
    
    if asset_allocation_model.renda_fixa_brasil.medio_prazo:
        print(f"Médio Prazo: R$ {asset_allocation_model.renda_fixa_brasil.medio_prazo.total:,.2f}")
    
    if asset_allocation_model.renda_fixa_brasil.longo_prazo:
        print(f"Longo Prazo: R$ {asset_allocation_model.renda_fixa_brasil.longo_prazo.total:,.2f}")
    
    if asset_allocation_model.renda_fixa_brasil.total_renda_fixa_br:
        print(f"\nTotal Renda Fixa BR: R$ {asset_allocation_model.renda_fixa_brasil.total_renda_fixa_br:,.2f}")

# ==================== Exportar para JSON ====================
print("\n=== Exportar para JSON ===")
json_data = asset_allocation_model.model_dump_json(indent=2, exclude_none=True)
print(f"Tamanho do JSON: {len(json_data)} bytes")

# Salvar em arquivo (opcional)
# with open("asset_allocation.json", "w", encoding="utf-8") as f:
#     f.write(json_data)

# ==================== Validação e Type Safety ====================
print("\n=== Type Safety ===")
# Com Pydantic, você tem validação automática e autocomplete no IDE
if asset_allocation_model.commodities:
    # Seu IDE vai sugerir os campos disponíveis
    total_investido = asset_allocation_model.commodities.total_valor_investido_num
    total_atual = asset_allocation_model.commodities.total_valor_atual_num
    
    if total_investido and total_atual:
        rentabilidade = ((total_atual - total_investido) / total_investido) * 100
        print(f"Rentabilidade Commodities: {rentabilidade:.2f}%")

print("\n✅ Exemplo concluído com sucesso!")

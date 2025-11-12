"""
Testes básicos para os modelos Pydantic
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.google_sheets.models import (
    StandardInvestmentRow,
    StandardInvestmentTable,
    InvestmentTotal,
    GeneralAllocationSummaryRow,
    AssetAllocationData
)


def test_standard_investment_row():
    """Testa criação e validação de uma linha de investimento"""
    row = StandardInvestmentRow(
        nome_do_fundo="VanEck Gold Miners ETF",
        ticker="GDX",
        subsetor="Ouro/Mineradora",
        qtd="87,55632",
        qtd_num=87.55632,
        preco_medio="$51,97",
        preco_medio_num=51.97,
        valor_investido="$4.550,30",
        valor_investido_num=4550.30,
        valor_atual="$6.716,45",
        valor_atual_num=6716.45,
        resultado="$2.166,14",
        resultado_num=2166.14,
        onde="AVENUE"
    )
    
    assert row.get_nome() == "VanEck Gold Miners ETF"
    assert row.ticker == "GDX"
    assert row.valor_atual_num == 6716.45
    print("✅ test_standard_investment_row passed")


def test_standard_investment_table():
    """Testa tabela completa com cálculos automáticos"""
    rows = [
        StandardInvestmentRow(
            nome_do_fundo="ETF 1",
            ticker="ETF1",
            valor_investido_num=1000.0,
            valor_atual_num=1100.0
        ),
        StandardInvestmentRow(
            nome_do_fundo="ETF 2",
            ticker="ETF2",
            valor_investido_num=2000.0,
            valor_atual_num=2200.0
        )
    ]
    
    total = InvestmentTotal(
        label="Total Test",
        valor_investido="$3000",
        valor_atual="$3300"
    )
    
    table = StandardInvestmentTable(rows=rows, total=total)
    
    assert len(table.rows) == 2
    assert table.total_valor_investido_num == 3000.0
    assert table.total_valor_atual_num == 3300.0
    print("✅ test_standard_investment_table passed")


def test_general_allocation_summary():
    """Testa modelo de summary da alocação geral"""
    summary = GeneralAllocationSummaryRow(
        **{
            "Asset Classes": "RENDA FIXA",
            "Valor Atual": "R$243.301",
            "% Atual": "54,79%",
            "% Meta": "60,00%",
            "Valores $": "R$266.451",
            "Diferença": "-R$23.150"
        }
    )
    
    assert summary.asset_classes == "RENDA FIXA"
    assert summary.valor_atual == "R$243.301"
    assert summary.pct_atual == "54,79%"
    print("✅ test_general_allocation_summary passed")


def test_asset_allocation_data_export():
    """Testa exportação para JSON"""
    # Criar dados mínimos
    row = StandardInvestmentRow(
        nome_do_fundo="Test Fund",
        ticker="TEST",
        valor_atual_num=1000.0
    )
    
    total = InvestmentTotal(label="Total Test")
    
    table = StandardInvestmentTable(rows=[row], total=total)
    
    data = AssetAllocationData(commodities=table)
    
    # Exportar para JSON
    json_str = data.model_dump_json(exclude_none=True)
    
    assert "Test Fund" in json_str
    assert "TEST" in json_str
    assert "commodities" in json_str
    print("✅ test_asset_allocation_data_export passed")


def test_get_nome_helper():
    """Testa helper method get_nome() com diferentes tipos"""
    # Fundo
    row1 = StandardInvestmentRow(nome_do_fundo="My Fund")
    assert row1.get_nome() == "My Fund"
    
    # Empresa
    row2 = StandardInvestmentRow(nome_da_empresa="My Company")
    assert row2.get_nome() == "My Company"
    
    # REIT
    row3 = StandardInvestmentRow(nome_do_reit="My REIT")
    assert row3.get_nome() == "My REIT"
    
    # FII
    row4 = StandardInvestmentRow(nome_do_fii="My FII")
    assert row4.get_nome() == "My FII"
    
    # Nenhum nome
    row5 = StandardInvestmentRow()
    assert row5.get_nome() is None
    
    print("✅ test_get_nome_helper passed")


if __name__ == "__main__":
    test_standard_investment_row()
    test_standard_investment_table()
    test_general_allocation_summary()
    test_asset_allocation_data_export()
    test_get_nome_helper()
    
    print("\n🎉 Todos os testes passaram!")

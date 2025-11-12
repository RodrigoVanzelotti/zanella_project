from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from decimal import Decimal


class InvestmentTotal(BaseModel):
    """Informações de total de uma tabela de investimentos"""
    label: str = Field(..., description="Label do total (ex: 'Total Commodities')")
    valor_investido: Optional[str] = Field(None, description="Valor total investido como string")
    valor_atual: Optional[str] = Field(None, description="Valor atual total como string")


class StandardInvestmentRow(BaseModel):
    """Linha individual de uma tabela padrão de investimentos"""
    nome_do_fundo: Optional[str] = Field(None, alias="nome_do_fundo")
    nome_da_empresa: Optional[str] = Field(None, alias="nome_da_empresa")
    nome_do_reit: Optional[str] = Field(None, alias="nome_do_reit")
    nome_do_fii: Optional[str] = Field(None, alias="nome_do_fii")
    ticker: Optional[str] = Field(None, description="Ticker do ativo")
    subsetor: Optional[str] = Field(None, description="Subsetor do investimento")
    qtd: Optional[str] = Field(None, description="Quantidade como string")
    qtd_num: Optional[float] = Field(None, description="Quantidade como número")
    preco_medio: Optional[str] = Field(None, description="Preço médio como string")
    preco_medio_num: Optional[float] = Field(None, description="Preço médio como número")
    preco_atual: Optional[str] = Field(None, description="Preço atual como string")
    preco_atual_num: Optional[float] = Field(None, description="Preço atual como número")
    valor_investido: Optional[str] = Field(None, description="Valor investido como string")
    valor_investido_num: Optional[float] = Field(None, description="Valor investido como número")
    valor_atual: Optional[str] = Field(None, description="Valor atual como string")
    valor_atual_num: Optional[float] = Field(None, description="Valor atual como número")
    resultado: Optional[str] = Field(None, description="Resultado como string")
    resultado_num: Optional[float] = Field(None, description="Resultado como número")
    pct_carteira: Optional[str] = Field(None, description="Percentual da carteira como string")
    pct_carteira_pct: Optional[float] = Field(None, description="Percentual da carteira como decimal")
    onde: Optional[str] = Field(None, description="Onde está investido (corretora)")
    
    class Config:
        populate_by_name = True
        
    def get_nome(self) -> Optional[str]:
        """Retorna o nome do ativo independente do tipo"""
        return (
            self.nome_do_fundo or 
            self.nome_da_empresa or 
            self.nome_do_reit or 
            self.nome_do_fii
        )


class StandardInvestmentTable(BaseModel):
    """Tabela padrão de investimentos (Commodities, Stocks, etc.)"""
    rows: List[StandardInvestmentRow] = Field(default_factory=list, description="Linhas de dados")
    total: InvestmentTotal = Field(..., description="Informações do total")
    
    @property
    def total_valor_investido_num(self) -> Optional[float]:
        """Calcula o total investido somando as linhas"""
        valores = [row.valor_investido_num for row in self.rows if row.valor_investido_num is not None]
        return sum(valores) if valores else None
    
    @property
    def total_valor_atual_num(self) -> Optional[float]:
        """Calcula o valor atual total somando as linhas"""
        valores = [row.valor_atual_num for row in self.rows if row.valor_atual_num is not None]
        return sum(valores) if valores else None


class RendaFixaBrasilRow(BaseModel):
    """Linha individual de Renda Fixa Brasil"""
    nome_do_titulo: Optional[str] = Field(None, description="Nome do título")
    codigo_taxa: Optional[str] = Field(None, description="Código ou taxa")
    tipo: Optional[str] = Field(None, description="Tipo de investimento")
    quantidade: Optional[str] = Field(None, description="Quantidade")
    preco_medio: Optional[str] = Field(None, description="Preço médio")
    preco_atual: Optional[str] = Field(None, description="Preço atual")
    valor_atual: Optional[str] = Field(None, description="Valor atual como string")
    valor_atual_num: Optional[float] = Field(None, description="Valor atual como número")
    retorno: Optional[str] = Field(None, description="Retorno como string")
    retorno_num: Optional[float] = Field(None, description="Retorno como número")
    pct_carteira: Optional[str] = Field(None, description="Percentual da carteira")
    pct_carteira_pct: Optional[float] = Field(None, description="Percentual da carteira como decimal")
    onde: Optional[str] = Field(None, description="Onde está investido")


class RendaFixaBrasilBlock(BaseModel):
    """Bloco de Renda Fixa Brasil (Curto/Médio/Longo Prazo)"""
    rows: List[RendaFixaBrasilRow] = Field(default_factory=list, description="Linhas do bloco")
    total: float = Field(..., description="Total do bloco")


class RendaFixaBrasil(BaseModel):
    """Estrutura completa de Renda Fixa Brasil"""
    curto_prazo: Optional[RendaFixaBrasilBlock] = Field(None, alias="Curto Prazo")
    medio_prazo: Optional[RendaFixaBrasilBlock] = Field(None, alias="Médio Prazo")
    longo_prazo: Optional[RendaFixaBrasilBlock] = Field(None, alias="Longo Prazo")
    total_renda_fixa_br: Optional[float] = Field(None, alias="Total Renda Fixa BR")
    
    class Config:
        populate_by_name = True


class GeneralAllocationDetailRow(BaseModel):
    """Linha detalhada da alocação geral"""
    asset_classes: str = Field(..., alias="Asset Classes", description="Classe de ativo")
    subclasse: str = Field(..., alias="Subclasse", description="Subclasse do ativo")
    valor_atual: str = Field(..., alias="Valor Atual", description="Valor atual como string")
    pct_atual: str = Field(..., alias="% Atual", description="Percentual atual")
    pct_meta: str = Field(..., alias="% Meta", description="Percentual meta")
    valores_dollar: str = Field(..., alias="Valores $", description="Valores em dólar")
    diferenca: str = Field(..., alias="Diferença", description="Diferença entre atual e meta")
    
    class Config:
        populate_by_name = True


class GeneralAllocationSummaryRow(BaseModel):
    """Linha resumida da alocação geral"""
    asset_classes: str = Field(..., alias="Asset Classes", description="Classe de ativo")
    valor_atual: str = Field(..., alias="Valor Atual", description="Valor atual como string")
    pct_atual: str = Field(..., alias="% Atual", description="Percentual atual")
    pct_meta: str = Field(..., alias="% Meta", description="Percentual meta")
    valores_dollar: str = Field(..., alias="Valores $", description="Valores em dólar")
    diferenca: str = Field(..., alias="Diferença", description="Diferença entre atual e meta")
    
    class Config:
        populate_by_name = True


class GeneralAllocation(BaseModel):
    """Estrutura completa da alocação geral"""
    detailed: List[GeneralAllocationDetailRow] = Field(default_factory=list, description="Linhas detalhadas")
    summary: List[GeneralAllocationSummaryRow] = Field(default_factory=list, description="Linhas resumidas")


class AssetAllocationData(BaseModel):
    """Estrutura completa de dados de alocação de ativos"""
    general_allocation: Optional[GeneralAllocation] = Field(None, description="Alocação geral")
    renda_fixa_brasil: Optional[RendaFixaBrasil] = Field(None, description="Renda Fixa Brasil")
    renda_fixa_eua: Optional[StandardInvestmentTable] = Field(None, description="Renda Fixa EUA")
    multimercado: Optional[StandardInvestmentTable] = Field(None, description="Multimercado")
    commodities: Optional[StandardInvestmentTable] = Field(None, description="Commodities")
    stocks_us: Optional[StandardInvestmentTable] = Field(None, description="Stocks US")
    world_stocks: Optional[StandardInvestmentTable] = Field(None, description="World Stocks")
    acoes_br: Optional[StandardInvestmentTable] = Field(None, description="Ações BR")
    reits: Optional[StandardInvestmentTable] = Field(None, description="REITs")
    fundos_imobiliarios: Optional[StandardInvestmentTable] = Field(None, description="Fundos Imobiliários")
    criptos: Optional[StandardInvestmentTable] = Field(None, description="Criptomoedas")

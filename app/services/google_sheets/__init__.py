"""
Google Sheets Service Module

Este módulo fornece funcionalidades para:
- Buscar dados de Google Sheets (GoogleSheetsService)
- Parsear dados de alocação de ativos (AssetAllocationParser)
- Modelos Pydantic para validação e tipagem (models)
"""

from .google_sheets_service import GoogleSheetsService, MockGoogleSheetsService
from .asset_allocation_parser import AssetAllocationParser
from .models import (
    AssetAllocationData,
    GeneralAllocation,
    GeneralAllocationDetailRow,
    GeneralAllocationSummaryRow,
    StandardInvestmentTable,
    StandardInvestmentRow,
    InvestmentTotal,
    RendaFixaBrasil,
    RendaFixaBrasilBlock,
    RendaFixaBrasilRow
)

__all__ = [
    # Services
    "GoogleSheetsService",
    "MockGoogleSheetsService",
    "AssetAllocationParser",
    
    # Models
    "AssetAllocationData",
    "GeneralAllocation",
    "GeneralAllocationDetailRow",
    "GeneralAllocationSummaryRow",
    "StandardInvestmentTable",
    "StandardInvestmentRow",
    "InvestmentTotal",
    "RendaFixaBrasil",
    "RendaFixaBrasilBlock",
    "RendaFixaBrasilRow",
]

import pandas as pd
from typing import List, Dict, Tuple, Any, Optional
import unicodedata
import re
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

class AssetAllocationParser:
    def __init__(self):
        self.sheets = [
            "general_allocation",
            "renda_fixa_brasil",
            "renda_fixa_eua",
            "multimercado",
            "commodities",
            "stocks_us",
            "world_stocks",
            "acoes_br",
            "reits",
            "fundos_imobiliarios",
            "criptos"
        ]

        self.subtable_names = [
            "Renda Fixa Brasil",
            "Renda Fixa EUA",
            "Multimercado",
            "Commodities",
            "Stocks US",
            "World Stocks",
            "Acões BR",
            "REITs",
            "FUNDOS IMOBILIÁRIOS",
            "Criptos"
        ]

    def _normalize_text(self, s: str) -> str:
        """Remove acentos, lower, remove múltiplos espaços."""
        if s is None:
            return ""
        s = str(s)
        s = s.strip()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = re.sub(r"\s+", " ", s)
        return s.lower()

    def _safe_get(self, row: List[Any], idx: int, default=""):
        return row[idx] if idx < len(row) else default

    def _is_blank_row(self, row: List[Any]) -> bool:
        return all((self._normalize_text(cell) == "" for cell in row))

    def _guess_header_index(self, block: List[List[Any]]) -> int:
        """
        Heurística para achar a linha de cabeçalho dentro do bloco:
        - procura a primeira linha com >= 3 valores não vazios e que
            contenha alguma palavra-chave típica de cabeçalho (nome, ticker, valor, preço, quantidade).
        - se não achar, pega a primeira linha com >= 3 valores não vazios.
        - se não achar nada, retorna 0.
        """
        header_keywords = [
            "nome", "ticker", "preço", "preco", "quantidade", "valor", "investido",
            "valor atual", "valorinvertido", "retorno", "codigo", "taxa", "tipo", "% carteira", "onde?"
        ]
        for i, row in enumerate(block):
            nn = sum(1 for c in row if self._normalize_text(c) != "")
            joined = " ".join(self._normalize_text(c) for c in row)
            if nn >= 3 and any(k in joined for k in header_keywords):
                return i
        # fallback: first row with >=3 non-empty
        for i, row in enumerate(block):
            nn = sum(1 for c in row if self._normalize_text(c) != "")
            if nn >= 3:
                return i
        return 0

    def _clean_col_name(self, raw: str) -> str:
        s = self._normalize_text(raw)
        s = s.replace(" ", "_")
        s = s.replace("%", "pct")
        s = re.sub(r"[^a-z0-9_]", "", s)
        s = s.strip("_")
        return s or "col"

    def _pad_row(self, row: List[Any], length: int) -> List[Any]:
        if len(row) >= length:
            return row[:length]
        return row + [""] * (length - len(row))

    def _convert_money(self, x: str) -> float:
        if x is None:
            return float("nan")
        s = str(x).strip()
        if s == "" or s.upper() in ("-", "—"):
            return float("nan")
        # aceita formatos: R$1.234,56  | $1.234,56 | 1.234,56 | $1,995.65 (USD com ponto)
        s = s.replace("R$", "").replace("$", "").replace(" ", "")
        # detectar se usa vírgula como decimal (ex: 1.234,56) -> trocar ponto thousand e vírg decimal
        # se houver vírgula e ponto: se último separador for vírgula -> vírgula decimal
        if "," in s and "." in s:
            # ex: 1.995,65 -> thousand . and decimal ,
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        else:
            # se só vírgula: vírgula decimal
            if "," in s and "." not in s:
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        try:
            return float(s)
        except:
            # tenta extrair números com regex
            m = re.search(r"-?[\d\.]+(?:\.\d+)?", s.replace(",", ""))
            if m:
                try:
                    return float(m.group(0))
                except:
                    return float("nan")
            return float("nan")

    def _convert_percent(self, x: str) -> float:
        if x is None:
            return float("nan")
        s = str(x).strip().replace("%", "").replace(" ", "")
        s = s.replace(",", ".")
        try:
            return float(s) / 100.0
        except:
            return float("nan")
        
    def split_renda_fixa_brasil(self, df: pd.DataFrame) -> dict:
        """
        Divide o DataFrame de 'Renda Fixa Brasil' em blocos com base nos subtotais.
        Retorna um dicionário estruturado com os blocos e seus totais.
        """
        df = df.copy().reset_index(drop=True)

        # 1. Detectar linhas com "Total"
        total_rows = []
        for i, row in df.iterrows():
            joined = " ".join(str(x) for x in row if str(x).strip() != "")
            if re.search(r"\btotal\b", joined, flags=re.IGNORECASE):
                total_rows.append((i, joined))

        # 2. Identificar as labels (Curto, Médio, Longo, Total BR)
        blocks = []
        for idx, text in total_rows:
            label = (
                "Curto Prazo" if "curto" in text.lower()
                else "Médio Prazo" if "medio" in text.lower() or "médio" in text.lower()
                else "Longo Prazo" if "longo" in text.lower()
                else "Total Renda Fixa BR" if "renda fixa" in text.lower()
                else text
            )
            blocks.append((idx, label))

        # 3. Montar blocos de dados entre subtotais
        result = {}
        for i, (idx, label) in enumerate(blocks):
            # Total da seção atual
            valor_total = None
            if "valor_atual" in df.columns:
                val = df.loc[idx, "valor_atual"]
            else:
                # tenta achar em qualquer coluna
                val = next((v for v in df.loc[idx].values if "R$" in str(v)), "")
            valor_total = self._convert_money(val)

            # Pular o total geral (pois ele não tem seção de dados)
            if "renda fixa" in label.lower():
                result[label] = valor_total
                continue

            # Limites: entre o subtotal anterior e o atual
            start = blocks[i - 1][0] + 1 if i > 0 else 0
            end = idx
            section_df = df.iloc[start:end].copy()
            section_df = section_df[
                ~section_df.apply(lambda r: any("Total" in str(v) for v in r.values), axis=1)
            ]
            result[label] = {
                "df": section_df.reset_index(drop=True),
                "total": valor_total
            }

        return result

    def parse_multiple_tables(self, raw_rows: List[List[Any]],
                            table_names: List[str] = None,
                            convert_numbers: bool = False
                            ) -> Dict[str, pd.DataFrame]:
        """
        Parse a single long list-of-lists `raw_rows` that contains many tables (with headers like 'Renda Fixa Brasil', 'Commodities', etc.)
        `table_names` is a list of logical table keys we want to extract (ex: ["renda_fixa_brasil", "renda_fixa_eua", ...]).
        Returns a dict mapping each table name -> parsed pandas.DataFrame (empty DF if tabela não encontrada).
        If convert_numbers=True, tentativas de conversão em colunas com 'valor' ou 'preço' ou '%' serão feitas.
        """
        if table_names is None:
            table_names = self.subtable_names

        # normalizar as chaves que procuramos
        wanted_norm = { self._normalize_text(k): k for k in table_names }

        # localizar índices onde cada tabela começa
        starts: Dict[int, str] = {}
        for i, row in enumerate(raw_rows):
            joined = " ".join(self._normalize_text(c) for c in row if self._normalize_text(c) != "")
            if not joined:
                continue
            # procurar correspondência parcial com qualquer wanted_norm
            for nk, original_key in wanted_norm.items():
                if nk in joined or joined.startswith(nk) or nk.split("_")[0] in joined:
                    # grava o primeiro match (não sobrescreve se já achamos)
                    if i not in starts:
                        starts[i] = original_key

        # se não detectou por nomes exatos, tentar matches alternativos comuns (por exemplo: 'renda fixa brasil' vs 'Renda Fixa Brasil')
        # (já coberto pelo normalize + substring above)

        # ordena índices de start
        start_indices = sorted(starts.keys())

        # criar slices (blocos) entre starts
        blocks: List[Tuple[int, int, str]] = []
        for idx_pos, start_idx in enumerate(start_indices):
            tbl_name = starts[start_idx]
            end_idx = start_indices[idx_pos + 1] if idx_pos + 1 < len(start_indices) else len(raw_rows)
            blocks.append((start_idx, end_idx, tbl_name))

        # Para cada tabela pedida, tentar encontrar o bloco correspondente (pode haver 0 ou >1)
        result: Dict[str, pd.DataFrame] = {}
        for wanted in table_names:
            # procurar bloco cujo nome normalizado contenha wanted normalizado
            normalized_wanted = self._normalize_text(wanted)
            matched_blocks = [b for b in blocks if normalized_wanted in self._normalize_text(b[2]) or self._normalize_text(b[2]) in normalized_wanted]
            # se exato não achou, procurar por qualquer bloco cujo conteúdo comece com a string esperada
            if not matched_blocks:
                for b in blocks:
                    joined_head = " ".join(self._normalize_text(c) for c in raw_rows[b[0]:b[0]+3] if self._normalize_text(c) != "")
                    if normalized_wanted in joined_head:
                        matched_blocks.append(b)
            # se ainda vazio, devolve empty DF
            if not matched_blocks:
                result[wanted] = pd.DataFrame()
                continue

            # Se houver múltiplos blocos para a mesma tabela, concatenar suas tabelas (raro)
            dfs = []
            for (sidx, eidx, tbl_label) in matched_blocks:
                block = raw_rows[sidx:eidx]
                # remover linhas completamente em branco do início e fim
                while block and self._is_blank_row(block[0]):
                    block = block[1:]
                while block and self._is_blank_row(block[-1]):
                    block = block[:-1]
                if not block:
                    continue

                header_i = self._guess_header_index(block)
                header_row = block[header_i]
                # construir nomes de colunas
                cols = [self._clean_col_name(self._safe_get(header_row, j, "")) for j in range(len(header_row))]
                # cortar cols após última não vazia
                last_nonempty = 0
                for j, c in enumerate(header_row):
                    if self._normalize_text(c) != "":
                        last_nonempty = j
                cols = cols[:last_nonempty+1] if cols else cols

                # montar linhas de dados
                data_rows = block[header_i+1:]
                normalized_rows = []
                for r in data_rows:
                    if self._is_blank_row(r):
                        continue
                    rpad = self._pad_row(r, len(cols))
                    # reduzir para o tamanho das colunas
                    rpad = rpad[:len(cols)]
                    # transformar cada célula em string limpa
                    normalized_rows.append([ (c if (c is not None and c != "") else "") for c in rpad ])

                if not normalized_rows:
                    # se não há linhas, criar DF vazio com colnames
                    df_block = pd.DataFrame(columns=cols)
                else:
                    df_block = pd.DataFrame(normalized_rows, columns=cols)

                # remover colunas vazias (todas vazias)
                df_block = df_block.loc[:, ~(df_block == "").all(axis=0)]
                dfs.append(df_block.reset_index(drop=True))

            # concatenar blocos (se houver vários)
            if dfs:
                df_full = pd.concat(dfs, ignore_index=True, sort=False)
            else:
                df_full = pd.DataFrame()

            # tentativa de conversão numérica para colunas óbvias
            if convert_numbers and not df_full.empty:
                for col in list(df_full.columns):
                    col_low = col.lower()
                    samples = df_full[col].astype(str).head(10).tolist()
                    # se nome da coluna indica valor/preço/valor_atual/valor_investido ou se conteúdos parecem monetários
                    if any(k in col_low for k in ("valor", "preco", "preço", "investido", "valor_atual", "valor_investido")) \
                    or any(re.search(r"[R\$|\$|\d][\d\.,]{2,}", s) for s in samples):
                        # converter money
                        df_full[col + "__num"] = df_full[col].apply(self._convert_money)
                    if "pct" in col_low or "percent" in col_low or "%" in col_low or "pct" in col_low or any(re.search(r"\d+,\d+%", s) or re.search(r"\d+(\.\d+)?%", s) for s in samples):
                        df_full[col + "__pct"] = df_full[col].apply(self._convert_percent)

            result[wanted] = df_full.reset_index(drop=True)

        # Processar Renda Fixa Brasil com lógica especial
        if "Renda Fixa Brasil" in result and isinstance(result["Renda Fixa Brasil"], pd.DataFrame) and not result["Renda Fixa Brasil"].empty:
            result["Renda Fixa Brasil"] = self.split_renda_fixa_brasil(result["Renda Fixa Brasil"])
        
        # Processar tabelas padrão de investimentos
        standard_tables = ["Commodities", "Stocks US", "World Stocks", "Acões BR", "REITs", "FUNDOS IMOBILIÁRIOS"]
        for table_name in standard_tables:
            # Encontrar o bloco correspondente nos raw_rows diretamente (não usar result anterior)
            norm_name = self._normalize_text(table_name)
            for i, row in enumerate(raw_rows):
                joined = " ".join(self._normalize_text(c) for c in row if self._normalize_text(c) != "")
                
                # Verificar se a linha contém o nome da tabela
                if norm_name in joined:
                    # IMPORTANTE: Verificar se a próxima linha (ou próximas 2-3 linhas) contém "ticker" e "qtd"
                    # para garantir que é uma tabela de investimentos detalhada e não a categoria principal
                    has_ticker_header = False
                    for check_idx in range(i + 1, min(i + 4, len(raw_rows))):
                        check_row_text = " ".join(str(c).lower() for c in raw_rows[check_idx])
                        if "ticker" in check_row_text and "qtd" in check_row_text:
                            has_ticker_header = True
                            break
                    
                    # Se não tem cabeçalho com ticker/qtd, não é uma tabela de investimento detalhada
                    if not has_ticker_header:
                        continue
                    
                    # Encontrar o fim do bloco (próxima tabela ou fim)
                    end_idx = len(raw_rows)
                    for j in range(i + 1, len(raw_rows)):
                        next_joined = " ".join(self._normalize_text(c) for c in raw_rows[j] if self._normalize_text(c) != "")
                        # Verificar se é início de outra tabela
                        is_next_table = any(self._normalize_text(other) in next_joined 
                                          for other in self.subtable_names if other != table_name)
                        if is_next_table:
                            end_idx = j
                            break
                    
                    # Extrair bloco e parsear
                    block = raw_rows[i:end_idx]
                    df_parsed, total_info = self.parse_standard_investment_table(block, table_name)
                    result[table_name] = {
                        "df": df_parsed,
                        "total": total_info
                    }
                    break

        return result

    def parse_standard_investment_table(self, raw_rows: List[List[Any]], table_name: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Parse tabelas padrão de investimentos que seguem a estrutura:
        - Commodities, Stocks US, World Stocks, Ações BR, REITs, FUNDOS IMOBILIÁRIOS
        
        Estrutura esperada:
        - Linha de título (ex: "Commodities")
        - Linha de cabeçalho com colunas
        - Linhas de dados (nome do ativo deslocado uma célula à esquerda)
        - Linha de total (começa com "Total...")
        
        Args:
            raw_rows: Lista de listas com os dados brutos da tabela
            table_name: Nome da tabela para identificação
            
        Returns:
            Tuple[pd.DataFrame, Dict]: 
                - DataFrame com os dados dos ativos individuais
                - Dicionário com informações do total
        """
        if not raw_rows:
            return pd.DataFrame(), {}
        
        # 1. Encontrar a linha de cabeçalho (procurar por "Ticker", "Qtd", etc.)
        header_idx = None
        for i, row in enumerate(raw_rows):
            row_text = " ".join(str(c).lower() for c in row)
            if "ticker" in row_text and "qtd" in row_text:
                header_idx = i
                break
        
        if header_idx is None:
            return pd.DataFrame(), {}
        
        # 2. Extrair cabeçalho e normalizar nomes das colunas
        header_row = raw_rows[header_idx]
        
        # Encontrar onde começam as colunas não vazias no cabeçalho
        first_nonempty = None
        for j, cell in enumerate(header_row):
            if str(cell).strip():
                first_nonempty = j
                break
        
        if first_nonempty is None:
            return pd.DataFrame(), {}
        
        # Mapear todas as colunas do cabeçalho
        columns = []
        col_mapping = {}
        for j in range(len(header_row)):
            cell_value = str(header_row[j]).strip()
            if cell_value:
                col_name = self._clean_col_name(cell_value)
                if col_name and col_name != "col":
                    columns.append(col_name)
                    col_mapping[j] = len(columns) - 1
        
        # 3. Processar linhas de dados
        data_rows = []
        total_info = {}
        
        for i in range(header_idx + 1, len(raw_rows)):
            row = raw_rows[i]
            
            # Verificar se é linha de total
            row_text = " ".join(str(c).lower() for c in row)
            if "total" in row_text:
                # Extrair informações do total
                total_info["label"] = next((str(c).strip() for c in row if str(c).strip().lower().startswith("total")), "")
                
                # Procurar valores monetários na linha de total
                for j, cell in enumerate(row):
                    cell_str = str(cell).strip()
                    if cell_str and ("$" in cell_str or "R$" in cell_str):
                        if "valor_investido" not in total_info:
                            total_info["valor_investido"] = cell_str
                        else:
                            total_info["valor_atual"] = cell_str
                break
            
            # Verificar se linha está vazia
            if self._is_blank_row(row):
                continue
            
            # 4. Extrair dados da linha
            # Verificar se a linha tem dados (procurar primeira célula não vazia após índice 1)
            has_data = False
            for j in range(2, len(row)):
                if str(row[j]).strip():
                    has_data = True
                    break
            
            if not has_data:
                continue
            
            # Montar dicionário com os dados - mapear cada coluna do header para o valor da linha
            row_data = {}
            for j, col_idx in col_mapping.items():
                col_name = columns[col_idx]
                # O nome do ativo está deslocado uma coluna à esquerda (índice 2 quando o header começa em índice 1)
                # Se esta é a primeira coluna do header (nome_do_fundo, nome_da_empresa, etc.),
                # pegar o valor da coluna 2 em vez da coluna do header
                if col_idx == 0 and j == first_nonempty:
                    # Pegar o nome do ativo da coluna 2
                    value = str(self._safe_get(row, 2, "")).strip()
                else:
                    value = str(self._safe_get(row, j, "")).strip()
                row_data[col_name] = value
            
            data_rows.append(row_data)
        
        # 5. Criar DataFrame
        if not data_rows:
            df = pd.DataFrame(columns=columns)
        else:
            df = pd.DataFrame(data_rows, columns=columns)
        
        # 6. Conversões numéricas opcionais
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ["qtd", "quantidade"]:
                # Converter quantidade (pode ter vírgula como decimal)
                df[col + "_num"] = df[col].apply(lambda x: self._convert_money(str(x)) if pd.notna(x) else float("nan"))
            elif any(k in col_lower for k in ["valor", "preco", "preço", "cota", "resultado"]):
                # Converter valores monetários
                df[col + "_num"] = df[col].apply(lambda x: self._convert_money(str(x)) if pd.notna(x) else float("nan"))
            elif "pct" in col_lower or "carteira" in col_lower or "%" in col:
                # Converter percentuais
                df[col + "_pct"] = df[col].apply(lambda x: self._convert_percent(str(x)) if pd.notna(x) else float("nan"))
        
        return df, total_info

    def parse_all_sheets(self) -> List[pd.DataFrame]:

        pass

    def parse_specific_subsheets(self, sheet: dict) -> pd.DataFrame:
        
        pass

    def _parse_specific_subsheet(self, sheet: List[List[str]], subsheet_name: str) -> pd.DataFrame:
        pass

    def parse_general_allocation(self, sheet: List[List[str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Recebe uma lista de listas (cada linha = lista) e retorna:
        - df_detailed: linhas por subclasse (Asset Classes, Subclasse, Valor Atual, % Atual, % Meta, Valores $, Diferença)
        - df_summary: primeira linha de cada Asset Class (Asset Classes, Valor Atual, % Atual, % Meta, Valores $, Diferença)
        """

        detailed_rows = []
        summary_rows = []
        current_asset_class = None

        # helper para pegar um index seguro
        def safe_get(row, idx, default=""):
            return row[idx] if idx < len(row) else default

        # pular header se existir (linha onde aparece "Asset Classes" no índice 2)
        start_idx = 0
        for i, row in enumerate(sheet):
            if safe_get(row, 2, "").strip() == "Asset Classes":
                start_idx = i + 1
                break

        for row in sheet[start_idx:]:
            col2 = safe_get(row, 2, "").strip()
            col3 = safe_get(row, 3, "").strip()
            col4 = safe_get(row, 4, "").strip()  # Valor Atual
            col5 = safe_get(row, 5, "").strip()  # % Atual
            col6 = safe_get(row, 6, "").strip()  # % Meta
            col8 = safe_get(row, 8, "").strip()  # Valores $
            col9 = safe_get(row, 9, "").strip()  # Diferença

            # Se linha define um novo Asset Class (col2 não vazio)
            if col2:
                current_asset_class = col2

                # Se essa própria linha é o resumo (col3 vazio) -> guarda no summary
                if col3 == "" and col4 != "":
                    summary_rows.append({
                        "Asset Classes": current_asset_class,
                        "Valor Atual": col4,
                        "% Atual": col5,
                        "% Meta": col6,
                        "Valores $": col8,
                        "Diferença": col9
                    })
                # caso contrário (col3 não vazio) — é uma subclasse na mesma linha; trata como detalhe abaixo

            # Se for uma linha de subclasse / detalhe (col3 não vazio)
            if col3 != "" and col4 != "":
                detailed_rows.append({
                    "Asset Classes": current_asset_class,
                    "Subclasse": col3,
                    "Valor Atual": col4,
                    "% Atual": col5,
                    "% Meta": col6,
                    "Valores $": col8,
                    "Diferença": col9
                })

        df_detailed = pd.DataFrame(detailed_rows)
        df_summary = pd.DataFrame(summary_rows)

        # ordenar por Asset Classes mantendo a ordem de aparição
        if not df_summary.empty:
            ordered = []
            seen = set()
            for row in sheet[start_idx:]:
                name = safe_get(row, 2, "").strip()
                if name and name not in seen:
                    seen.add(name)
                    ordered.append(name)
            df_summary['__order__'] = df_summary['Asset Classes'].apply(lambda x: ordered.index(x) if x in ordered else 999)
            df_summary = df_summary.sort_values('__order__').drop(columns='__order__').reset_index(drop=True)

        return df_detailed.reset_index(drop=True), df_summary.reset_index(drop=True)
    
    # ==================== Métodos de Conversão para Modelos Pydantic ====================
    
    def to_general_allocation_model(self, df_detailed: pd.DataFrame, df_summary: pd.DataFrame) -> GeneralAllocation:
        """Converte DataFrames de alocação geral para modelo Pydantic"""
        detailed_rows = [
            GeneralAllocationDetailRow(**row.to_dict()) 
            for _, row in df_detailed.iterrows()
        ]
        summary_rows = [
            GeneralAllocationSummaryRow(**row.to_dict()) 
            for _, row in df_summary.iterrows()
        ]
        return GeneralAllocation(detailed=detailed_rows, summary=summary_rows)
    
    def to_standard_investment_model(self, df: pd.DataFrame, total_info: Dict[str, Any]) -> StandardInvestmentTable:
        """Converte DataFrame de investimentos padrão para modelo Pydantic"""
        rows = [
            StandardInvestmentRow(**row.to_dict()) 
            for _, row in df.iterrows()
        ]
        total = InvestmentTotal(**total_info)
        return StandardInvestmentTable(rows=rows, total=total)
    
    def to_renda_fixa_brasil_model(self, renda_fixa_dict: Dict) -> RendaFixaBrasil:
        """Converte dicionário de Renda Fixa Brasil para modelo Pydantic"""
        blocks = {}
        
        for key, value in renda_fixa_dict.items():
            if isinstance(value, dict) and "df" in value:
                # É um bloco (Curto/Médio/Longo Prazo)
                rows = [
                    RendaFixaBrasilRow(**row.to_dict()) 
                    for _, row in value["df"].iterrows()
                ]
                blocks[key] = RendaFixaBrasilBlock(rows=rows, total=value["total"])
            elif isinstance(value, (int, float)):
                # É o total geral
                blocks["total_renda_fixa_br"] = value
        
        return RendaFixaBrasil(**blocks)
    
    def to_asset_allocation_data(
        self,
        general_allocation: Optional[Tuple[pd.DataFrame, pd.DataFrame]] = None,
        subtables: Optional[Dict[str, Any]] = None
    ) -> AssetAllocationData:
        """
        Converte todos os dados parseados para o modelo completo AssetAllocationData
        
        Args:
            general_allocation: Tupla (df_detailed, df_summary) da alocação geral
            subtables: Dicionário com todas as sub-tabelas parseadas
            
        Returns:
            AssetAllocationData com todos os dados mapeados
        """
        data = {}
        
        # Converter alocação geral
        if general_allocation:
            df_detailed, df_summary = general_allocation
            data["general_allocation"] = self.to_general_allocation_model(df_detailed, df_summary)
        
        # Converter sub-tabelas
        if subtables:
            # Renda Fixa Brasil (estrutura especial)
            if "Renda Fixa Brasil" in subtables:
                data["renda_fixa_brasil"] = self.to_renda_fixa_brasil_model(subtables["Renda Fixa Brasil"])
            
            # Tabelas padrão de investimentos
            standard_tables_mapping = {
                "Renda Fixa EUA": "renda_fixa_eua",
                "Multimercado": "multimercado",
                "Commodities": "commodities",
                "Stocks US": "stocks_us",
                "World Stocks": "world_stocks",
                "Acões BR": "acoes_br",
                "REITs": "reits",
                "FUNDOS IMOBILIÁRIOS": "fundos_imobiliarios",
                "Criptos": "criptos"
            }
            
            for table_name, model_key in standard_tables_mapping.items():
                if table_name in subtables and isinstance(subtables[table_name], dict):
                    df = subtables[table_name].get("df")
                    total_info = subtables[table_name].get("total")
                    if df is not None and not df.empty:
                        data[model_key] = self.to_standard_investment_model(df, total_info)
        
        return AssetAllocationData(**data)
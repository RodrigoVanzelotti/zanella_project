import pandas as pd
from typing import List, Dict, Tuple, Any
import unicodedata
import re

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

        return result

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
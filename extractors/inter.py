"""
extractors/inter.py
Extrator específico para extratos do Banco Inter (PDF).

O Inter exporta extratos com colunas fixas:
    Data | Descrição | Tipo | Valor

O tipo pode ser 'C' (crédito) ou 'D' (débito).
"""

import re
import pdfplumber
from datetime import datetime
from pathlib import Path


_PATTERN_DATA = re.compile(r"(\d{2}/\d{2}/\d{4})")
_PATTERN_VALOR = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2})")
_PATTERN_TIPO = re.compile(r"\b([CD])\b")


def _parse_data(texto: str) -> datetime | None:
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y")
    except ValueError:
        return None


def _parse_valor(texto: str) -> float | None:
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def extrair(pdf_path: Path) -> list[dict]:
    """
    Extrai transações de um extrato Banco Inter em PDF.

    Retorna lista de dicts com chaves:
        data (datetime), descricao (str), valor (float), tipo (str: debito/credito)
    """
    transacoes = []

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            # Tenta extração por tabela primeiro (mais preciso)
            tabelas = pagina.extract_tables()
            if tabelas:
                for tabela in tabelas:
                    for linha in tabela:
                        if not linha or len(linha) < 3:
                            continue

                        # Ignora cabeçalho
                        primeira_celula = str(linha[0] or "").strip()
                        if not _PATTERN_DATA.match(primeira_celula):
                            continue

                        data = _parse_data(primeira_celula)
                        if not data:
                            continue

                        descricao = str(linha[1] or "").strip()
                        tipo_raw = str(linha[-2] or "").strip().upper() if len(linha) >= 4 else ""
                        valor_raw = str(linha[-1] or "").strip()

                        valor = _parse_valor(valor_raw)
                        if valor is None:
                            continue

                        tipo = "credito" if tipo_raw == "C" else "debito"

                        transacoes.append({
                            "data": data,
                            "descricao": descricao,
                            "valor": abs(valor),
                            "tipo": tipo,
                            "banco": "Inter",
                        })
            else:
                # Fallback: parse linha a linha
                texto = pagina.extract_text() or ""
                for linha in texto.splitlines():
                    match_data = _PATTERN_DATA.match(linha.strip())
                    match_valor = _PATTERN_VALOR.search(linha)
                    if not match_data or not match_valor:
                        continue

                    data = _parse_data(match_data.group(1))
                    valor = _parse_valor(match_valor.group(1))
                    if not data or valor is None:
                        continue

                    match_tipo = _PATTERN_TIPO.search(linha[match_data.end():])
                    tipo = "credito" if match_tipo and match_tipo.group(1) == "C" else "debito"

                    inicio_valor = linha.rfind(match_valor.group(1))
                    descricao = linha[match_data.end():inicio_valor].strip()

                    transacoes.append({
                        "data": data,
                        "descricao": descricao,
                        "valor": abs(valor),
                        "tipo": tipo,
                        "banco": "Inter",
                    })

    return transacoes

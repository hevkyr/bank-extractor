"""
extractors/nubank.py
Extrator específico para extratos do Nubank (PDF).

O Nubank exporta dois tipos de PDF:
  - Fatura do cartão de crédito
  - Extrato da conta corrente / NuConta

Este módulo lida com ambos detectando padrões no texto.
"""

import re
import pdfplumber
from datetime import datetime
from pathlib import Path


# Padrões de data aceitos pelo Nubank
_PATTERN_DATA = re.compile(r"(\d{2}\s+\w{3}(?:\s+\d{4})?)")
_MESES_PT = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}
# Padrão de valor monetário: 1.234,56 ou 1234,56 ou -1.234,56
_PATTERN_VALOR = re.compile(r"-?\d{1,3}(?:\.\d{3})*,\d{2}")


def _parse_data(texto: str, ano_ref: int) -> datetime | None:
    """Converte string de data do Nubank ('15 jan' ou '15 jan 2025') em datetime."""
    partes = texto.strip().lower().split()
    if len(partes) < 2:
        return None
    try:
        dia = int(partes[0])
        mes = _MESES_PT.get(partes[1][:3])
        ano = int(partes[2]) if len(partes) >= 3 else ano_ref
        if mes is None:
            return None
        return datetime(ano, mes, dia)
    except (ValueError, IndexError):
        return None


def _parse_valor(texto: str) -> float | None:
    """Converte string de valor brasileiro em float."""
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def extrair(pdf_path: Path) -> list[dict]:
    """
    Extrai transações de um extrato Nubank em PDF.

    Retorna lista de dicts com chaves:
        data (datetime), descricao (str), valor (float), tipo (str: debito/credito)
    """
    transacoes = []
    ano_ref = datetime.now().year

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text() or ""
            linhas = texto.splitlines()

            for linha in linhas:
                linha = linha.strip()
                if not linha:
                    continue

                # Tentativa de extrair data + descrição + valor na mesma linha
                match_data = _PATTERN_DATA.match(linha)
                match_valor = _PATTERN_VALOR.search(linha)

                if not match_data or not match_valor:
                    continue

                data_str = match_data.group(1)
                data = _parse_data(data_str, ano_ref)
                if not data:
                    continue

                valor_str = match_valor.group(0)
                valor = _parse_valor(valor_str)
                if valor is None:
                    continue

                # Descrição é o texto entre a data e o valor
                inicio_valor = linha.rfind(valor_str)
                fim_data = match_data.end()
                descricao = linha[fim_data:inicio_valor].strip(" -·•")

                if not descricao:
                    continue

                tipo = "credito" if valor > 0 else "debito"

                transacoes.append({
                    "data": data,
                    "descricao": descricao,
                    "valor": abs(valor),
                    "tipo": tipo,
                    "banco": "Nubank",
                })

    return transacoes

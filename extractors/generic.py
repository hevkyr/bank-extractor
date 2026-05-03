"""
extractors/generic.py
Extrator genérico — funciona como fallback para bancos não mapeados
(Itaú, Bradesco, BB, Caixa, Santander, etc.) e para PDFs desconhecidos.

Estratégia:
  1. Tenta extração via tabela (pdfplumber) — cobre a maioria dos PDFs bem estruturados.
  2. Fallback: parse linha a linha buscando padrões de data + valor.

Limitações conhecidas:
  - PDFs escaneados (imagem) não funcionam sem OCR — instale pytesseract para isso.
  - Layouts muito quebrados podem gerar falsos positivos.
"""

import re
import pdfplumber
from datetime import datetime
from pathlib import Path


# Aceita DD/MM/AAAA ou DD-MM-AAAA ou DD.MM.AAAA
_PATTERN_DATA = re.compile(r"(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})")
_PATTERN_VALOR = re.compile(r"-?\d{1,3}(?:[.\s]\d{3})*,\d{2}")

# Palavras que indicam linhas de cabeçalho a ignorar
_IGNORAR = {"data", "descrição", "descricao", "historico", "histórico",
             "valor", "saldo", "lançamento", "lancamento", "tipo", "doc"}


def _parse_data(texto: str) -> datetime | None:
    texto = texto.strip().replace("-", "/").replace(".", "/")
    try:
        return datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return None


def _parse_valor(texto: str) -> float | None:
    texto = texto.strip().replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _e_cabecalho(linha: str) -> bool:
    palavras = set(w.lower() for w in linha.split())
    return bool(palavras & _IGNORAR)


def extrair(pdf_path: Path, banco: str = "Desconhecido") -> list[dict]:
    """
    Extrai transações de um PDF bancário genérico.

    Args:
        pdf_path: Caminho para o arquivo PDF.
        banco:    Nome do banco (usado apenas como metadado).

    Retorna lista de dicts com chaves:
        data, descricao, valor, tipo, banco
    """
    transacoes = []

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            # Tentativa 1: extração por tabela
            tabelas = pagina.extract_tables()
            if tabelas:
                for tabela in tabelas:
                    for linha in tabela:
                        if not linha:
                            continue
                        celulas = [str(c or "").strip() for c in linha]
                        texto_linha = " ".join(celulas)

                        if _e_cabecalho(texto_linha):
                            continue

                        match_data = _PATTERN_DATA.search(texto_linha)
                        match_valor = _PATTERN_VALOR.search(texto_linha)
                        if not match_data or not match_valor:
                            continue

                        data = _parse_data(match_data.group(1))
                        valor = _parse_valor(match_valor.group(0))
                        if not data or valor is None:
                            continue

                        # Descrição: junta células que não são data nem valor
                        descricao_partes = [
                            c for c in celulas
                            if c
                            and not _PATTERN_DATA.match(c)
                            and not _PATTERN_VALOR.match(c)
                        ]
                        descricao = " ".join(descricao_partes).strip()

                        tipo = "credito" if valor > 0 else "debito"
                        transacoes.append({
                            "data": data,
                            "descricao": descricao or "Sem descrição",
                            "valor": abs(valor),
                            "tipo": tipo,
                            "banco": banco,
                        })
                continue  # se tinha tabela, pula o fallback

            # Tentativa 2: parse linha a linha
            texto = pagina.extract_text() or ""
            for linha in texto.splitlines():
                linha = linha.strip()
                if not linha or _e_cabecalho(linha):
                    continue

                match_data = _PATTERN_DATA.search(linha)
                match_valor = _PATTERN_VALOR.search(linha)
                if not match_data or not match_valor:
                    continue

                data = _parse_data(match_data.group(1))
                valor = _parse_valor(match_valor.group(0))
                if not data or valor is None:
                    continue

                # Remove data e valor da linha para obter descrição
                descricao = linha
                descricao = descricao.replace(match_data.group(0), "", 1)
                descricao = descricao.replace(match_valor.group(0), "", 1)
                descricao = re.sub(r"\s{2,}", " ", descricao).strip(" -·|")

                tipo = "credito" if valor > 0 else "debito"
                transacoes.append({
                    "data": data,
                    "descricao": descricao or "Sem descrição",
                    "valor": abs(valor),
                    "tipo": tipo,
                    "banco": banco,
                })

    return transacoes

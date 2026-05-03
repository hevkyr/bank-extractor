"""
normalizer.py
Detecta automaticamente o banco pelo conteúdo do PDF,
delega a extração ao extractor correto e filtra por mês se solicitado.
"""

import pdfplumber
from pathlib import Path
from datetime import datetime

from extractors import nubank, inter, generic


# Palavras-chave para auto-detecção de banco
_ASSINATURAS = {
    "nubank":    ["nubank", "roxinho", "nu pagamentos"],
    "inter":     ["banco inter", "bco inter", "inter s.a"],
    "itau":      ["itaú", "itau unibanco", "itaú s.a"],
    "bradesco":  ["bradesco"],
    "bb":        ["banco do brasil", "bb s.a"],
    "santander": ["santander"],
    "caixa":     ["caixa econômica", "cef"],
}


def _detectar_banco(pdf_path: Path) -> str:
    """Lê as primeiras páginas do PDF e retorna o nome do banco detectado."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Analisa até 3 páginas para detecção
            texto = ""
            for pagina in pdf.pages[:3]:
                texto += (pagina.extract_text() or "").lower()

        for banco, palavras in _ASSINATURAS.items():
            if any(p in texto for p in palavras):
                return banco
    except Exception:
        pass
    return "generico"


def normalizar(
    pdf_path: Path,
    banco_hint: str | None = None,
    filtro_mes: str | None = None,
) -> list[dict]:
    """
    Detecta o banco, extrai e normaliza as transações do PDF.

    Args:
        pdf_path:   Caminho para o PDF.
        banco_hint: Nome do banco fornecido pelo usuário (sobrescreve auto-detect).
        filtro_mes: String 'AAAA-MM' para filtrar um mês específico.

    Retorna lista de dicts normalizados com chaves:
        data (datetime), descricao (str), valor (float), tipo (str), banco (str)
    """
    banco = (banco_hint or "").lower().strip() or _detectar_banco(pdf_path)

    # Delega ao extractor correto
    if banco == "nubank":
        transacoes = nubank.extrair(pdf_path)
    elif banco == "inter":
        transacoes = inter.extrair(pdf_path)
    else:
        # itau, bradesco, bb, santander, caixa, generico
        nome_legivel = banco.capitalize()
        transacoes = generic.extrair(pdf_path, banco=nome_legivel)

    # Filtro de mês
    if filtro_mes:
        try:
            ano, mes = map(int, filtro_mes.split("-"))
            transacoes = [
                t for t in transacoes
                if t["data"].year == ano and t["data"].month == mes
            ]
        except (ValueError, AttributeError):
            pass  # Filtro inválido — ignora e retorna tudo

    # Garante ordenação cronológica
    transacoes.sort(key=lambda t: t["data"])

    return transacoes

"""
bank-extractor · main.py
Ponto de entrada da CLI.

Uso:
    python main.py extrato.pdf
    python main.py extrato.pdf --banco nubank
    python main.py extrato.pdf --banco inter --mes 2025-04
    python main.py extrato.pdf --saida relatorio.xlsx --sem-ia
"""

import typer
from pathlib import Path
from typing import Optional
from normalizer import normalizar
from categorizer import categorizar
from excel_writer import gerar_excel

app = typer.Typer(help="Extrai extratos bancários em PDF e gera relatório Excel.")


@app.command()
def processar(
    pdf: Path = typer.Argument(..., help="Caminho para o extrato em PDF"),
    banco: Optional[str] = typer.Option(
        None,
        "--banco", "-b",
        help="Banco: nubank | inter | itau | bradesco | bb | auto (padrão: auto-detect)",
    ),
    mes: Optional[str] = typer.Option(
        None,
        "--mes", "-m",
        help="Filtrar mês específico (ex: 2025-04). Padrão: todos os meses encontrados.",
    ),
    saida: Path = typer.Option(
        Path("relatorio.xlsx"),
        "--saida", "-s",
        help="Arquivo Excel de saída (padrão: relatorio.xlsx)",
    ),
    sem_ia: bool = typer.Option(
        False,
        "--sem-ia",
        help="Desativa categorização por IA (usa regras simples).",
    ),
):
    """
    Processa um extrato bancário em PDF e gera um relatório Excel
    com transações organizadas por categoria e resumo mensal.
    """
    if not pdf.exists():
        typer.echo(f"❌  Arquivo não encontrado: {pdf}", err=True)
        raise typer.Exit(1)

    typer.echo(f"📄  Lendo: {pdf.name}")

    # 1. Extrair e normalizar transações
    transacoes = normalizar(pdf, banco_hint=banco, filtro_mes=mes)

    if not transacoes:
        typer.echo("⚠️  Nenhuma transação encontrada. Verifique o PDF ou especifique --banco.")
        raise typer.Exit(1)

    typer.echo(f"✅  {len(transacoes)} transações extraídas.")

    # 2. Categorizar
    if sem_ia:
        typer.echo("🏷️  Categorizando com regras simples...")
    else:
        typer.echo("🤖  Categorizando com IA (Claude)...")

    transacoes = categorizar(transacoes, usar_ia=not sem_ia)

    # 3. Gerar Excel
    typer.echo(f"📊  Gerando relatório: {saida}")
    gerar_excel(transacoes, saida)

    typer.echo(f"✅  Concluído! Arquivo salvo em: {saida}")


if __name__ == "__main__":
    app()

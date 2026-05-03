"""
categorizer.py
Categoriza transações bancárias usando a API do Claude (Anthropic).

Estratégias:
  1. Cache local (JSON) — evita recategorizar o mesmo estabelecimento.
  2. Categorização por IA em lote — envia até 50 descrições por chamada.
  3. Fallback por regras simples — usado quando --sem-ia é passado ou a API falha.

Categorias disponíveis:
    Alimentação | Transporte | Moradia | Saúde | Educação |
    Lazer | Vestuário | Investimento | Transferência | Receita |
    Assinatura | Serviços | Impostos | Outros
"""

import json
import os
import re
from pathlib import Path

try:
    import anthropic
    _ANTHROPIC_OK = True
except ImportError:
    _ANTHROPIC_OK = False

# Caminho do cache local de categorias
_CACHE_PATH = Path(__file__).parent / ".categoria_cache.json"

CATEGORIAS = [
    "Alimentação", "Transporte", "Moradia", "Saúde", "Educação",
    "Lazer", "Vestuário", "Investimento", "Transferência", "Receita",
    "Assinatura", "Serviços", "Impostos", "Outros",
]

# Regras simples para fallback (sem IA)
_REGRAS = {
    "Alimentação":   ["ifood", "rappi", "uber eats", "restaurante", "lanch", "padaria",
                      "mercado", "supermercado", "açougue", "hortifruti", "feira",
                      "pão de açúcar", "carrefour", "extra", "atacadão"],
    "Transporte":    ["uber", "99", "cabify", "posto", "combustível", "gasolina",
                      "estacionamento", "metrô", "ônibus", "passagem", "toll",
                      "rodovia", "pedágio", "shell", "ipiranga", "br distribuidora"],
    "Moradia":       ["aluguel", "condomínio", "água", "luz", "energia", "gás",
                      "sabesp", "cemig", "copel", "enel", "elektro"],
    "Saúde":         ["farmácia", "drogaria", "drogasil", "ultrafarma", "raia",
                      "médico", "clínica", "hospital", "plano de saúde", "unimed",
                      "hapvida", "sulamerica saude", "amil", "exame", "laboratório"],
    "Educação":      ["escola", "faculdade", "universidade", "curso", "udemy",
                      "alura", "coursera", "dio", "livro", "livraria"],
    "Lazer":         ["cinema", "netflix", "spotify", "disney", "hbo", "amazon prime",
                      "prime video", "youtube", "steam", "playstation", "xbox",
                      "ingresso", "show", "teatro", "museu", "parque"],
    "Assinatura":    ["apple", "google one", "dropbox", "adobe", "microsoft 365",
                      "office", "icloud", "one drive", "notion", "chatgpt",
                      "anthropic", "openai", "linear", "figma"],
    "Investimento":  ["rico", "xp", "btg", "clear", "nuinvest", "inter invest",
                      "avenue", "nomad", "warren", "ações", "fii", "tesouro",
                      "renda fixa", "cdb", "lci", "lca"],
    "Impostos":      ["receita federal", "prefeitura", "iptu", "ipva", "darf",
                      "inss", "irrf", "ir ", "multa"],
    "Vestuário":     ["zara", "renner", "riachuelo", "c&a", "hering", "shein",
                      "amazon fashion", "nike", "adidas", "foot locker"],
    "Receita":       ["salário", "salario", "pagamento", "honorários", "freelance",
                      "pix recebido", "ted recebido", "rendimento"],
    "Transferência": ["pix", "ted", "doc", "transferência", "transferencia"],
}


def _carregar_cache() -> dict:
    if _CACHE_PATH.exists():
        try:
            return json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def _salvar_cache(cache: dict) -> None:
    _CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _categorizar_por_regras(descricao: str) -> str:
    """Categoriza uma descrição usando correspondência de palavras-chave."""
    desc_lower = descricao.lower()
    for categoria, palavras in _REGRAS.items():
        if any(p in desc_lower for p in palavras):
            return categoria
    return "Outros"


def _categorizar_lote_ia(descricoes: list[str]) -> dict[str, str]:
    """
    Envia um lote de descrições para o Claude e retorna um dict
    {descricao: categoria}.
    """
    if not _ANTHROPIC_OK:
        raise RuntimeError("Biblioteca 'anthropic' não instalada.")

    client = anthropic.Anthropic()  # usa ANTHROPIC_API_KEY do ambiente

    lista_formatada = "\n".join(f"{i+1}. {d}" for i, d in enumerate(descricoes))
    categorias_str = " | ".join(CATEGORIAS)

    prompt = f"""Você é um assistente financeiro. Categorize cada transação bancária abaixo.

Categorias disponíveis: {categorias_str}

Transações:
{lista_formatada}

Responda SOMENTE em JSON válido, no formato:
{{"1": "Categoria", "2": "Categoria", ...}}

Não inclua explicações. Use exatamente os nomes das categorias fornecidos."""

    mensagem = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    texto = mensagem.content[0].text.strip()

    # Remove possíveis marcadores de bloco de código
    texto = re.sub(r"```(?:json)?", "", texto).strip()

    resultado = json.loads(texto)
    return {descricoes[int(k) - 1]: v for k, v in resultado.items()}


def categorizar(transacoes: list[dict], usar_ia: bool = True) -> list[dict]:
    """
    Adiciona o campo 'categoria' a cada transação.

    Args:
        transacoes: Lista de dicts normalizados.
        usar_ia:    Se True, usa Claude API (com fallback por regras em caso de erro).

    Retorna as mesmas transações com o campo 'categoria' preenchido.
    """
    cache = _carregar_cache()
    cache_atualizado = False

    # Separa as que já estão no cache
    sem_categoria = [t for t in transacoes if t["descricao"] not in cache]

    if sem_categoria and usar_ia:
        # Processa em lotes de 50
        lote_size = 50
        descricoes_unicas = list({t["descricao"] for t in sem_categoria})

        for i in range(0, len(descricoes_unicas), lote_size):
            lote = descricoes_unicas[i : i + lote_size]
            try:
                resultado = _categorizar_lote_ia(lote)
                cache.update(resultado)
                cache_atualizado = True
            except Exception as e:
                # Fallback por regras para este lote
                print(f"⚠️  IA indisponível ({e}). Usando regras para este lote.")
                for desc in lote:
                    if desc not in cache:
                        cache[desc] = _categorizar_por_regras(desc)
                cache_atualizado = True

    elif sem_categoria and not usar_ia:
        for t in sem_categoria:
            if t["descricao"] not in cache:
                cache[t["descricao"]] = _categorizar_por_regras(t["descricao"])
        cache_atualizado = True

    if cache_atualizado:
        _salvar_cache(cache)

    # Aplica categorias
    for t in transacoes:
        t["categoria"] = cache.get(t["descricao"], "Outros")

    return transacoes

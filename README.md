# 🏦 bank-extractor

> Extrai extratos bancários em PDF e gera relatórios Excel organizados por categoria, com categorização automática via IA (Claude).

---

## ✨ Funcionalidades

- 📄 Lê extratos em **PDF** (Nubank, Inter, Itaú, Bradesco, BB e genérico)
- 🤖 **Auto-detecção** do banco pelo conteúdo do arquivo
- 🏷️ **Categorização automática** com Claude API (com fallback por regras)
- 💾 **Cache local** de categorias — sem rechamadas desnecessárias à API
- 📊 Relatório Excel com **3 abas**: Transações, Resumo Mensal e Gráfico de Pizza
- 🔍 Filtro por mês via CLI

---

## 🗂️ Estrutura do Projeto

```
bank-extractor/
├── extractors/
│   ├── __init__.py
│   ├── nubank.py       # Parser do Nubank
│   ├── inter.py        # Parser do Banco Inter
│   └── generic.py      # Parser genérico (Itaú, Bradesco, BB, etc.)
├── normalizer.py        # Auto-detecção de banco + normalização
├── categorizer.py       # Categorização por IA ou regras
├── excel_writer.py      # Geração do relatório Excel
├── main.py              # CLI (Typer)
├── requirements.txt
└── README.md
```

---

## ⚙️ Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/hevkyr/bank-extractor
cd bank-extractor

# 2. (Recomendado) Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. Instale as dependências
pip install -r requirements.txt
```

---

## 🔑 Configuração da API (opcional)

A categorização por IA usa a **Claude API** (Anthropic). Se não configurar, o bot usa regras simples automaticamente.

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Ou crie um arquivo `.env` e carregue com `python-dotenv`.

---

## 🚀 Uso

### Básico — auto-detect do banco

```bash
python main.py extrato.pdf
```

### Especificando o banco

```bash
python main.py extrato.pdf --banco nubank
python main.py extrato.pdf --banco inter
python main.py extrato.pdf --banco itau
python main.py extrato.pdf --banco bradesco
python main.py extrato.pdf --banco bb
```

### Filtrar por mês

```bash
python main.py extrato.pdf --mes 2025-04
```

### Arquivo de saída customizado

```bash
python main.py extrato.pdf --saida abril_2025.xlsx
```

### Sem IA (regras simples, offline)

```bash
python main.py extrato.pdf --sem-ia
```

### Combinando opções

```bash
python main.py extrato_nubank.pdf --banco nubank --mes 2025-03 --saida marco.xlsx
```

---

## 📊 Relatório Excel

O arquivo gerado contém 3 abas:

| Aba | Conteúdo |
|-----|----------|
| **Transações** | Tabela completa com filtros. Débitos em vermelho claro, créditos em verde claro. |
| **Resumo Mensal** | Totais por categoria e mês. Útil para análise de padrões. |
| **Gráficos** | Gráfico de pizza com distribuição de gastos por categoria. |

---

## 🏷️ Categorias

| Categoria | Exemplos |
|-----------|---------|
| Alimentação | iFood, Mercado, Restaurante |
| Transporte | Uber, Combustível, Pedágio |
| Moradia | Aluguel, Condomínio, Energia |
| Saúde | Farmácia, Plano de Saúde |
| Educação | Cursos, Livros, Faculdade |
| Lazer | Netflix, Spotify, Cinema |
| Assinatura | iCloud, Adobe, ChatGPT |
| Investimento | XP, Rico, Tesouro Direto |
| Receita | Salário, Freelance |
| Transferência | PIX, TED, DOC |
| Impostos | IPTU, IPVA, DARF |
| Vestuário | Zara, Shein, Renner |
| Serviços | Geral |
| Outros | Não categorizado |

---

## 🛠️ Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Claude](https://img.shields.io/badge/Claude_API-D97757?style=flat-square&logo=anthropic&logoColor=white)
![Excel](https://img.shields.io/badge/openpyxl-217346?style=flat-square&logo=microsoft-excel&logoColor=white)

- **pdfplumber** — extração de texto e tabelas de PDFs
- **openpyxl** — geração e formatação do Excel
- **anthropic** — categorização inteligente via Claude
- **typer** — interface de linha de comando

---

## 🔧 Adicionando suporte a novos bancos

1. Crie `extractors/meu_banco.py` com uma função `extrair(pdf_path) -> list[dict]`
2. Adicione a palavra-chave do banco em `normalizer.py` no dict `_ASSINATURAS`
3. Adicione o `elif banco == "meu_banco":` no `normalizer.py`

---

## 📝 Licença

MIT

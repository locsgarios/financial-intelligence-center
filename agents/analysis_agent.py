import anthropic
from rich.console import Console
from rich.markdown import Markdown

console = Console()

SYSTEM_PROMPT = """Você é um analista financeiro especialista no mercado brasileiro (B3).
Sua função é analisar dados fundamentalistas de ações e gerar análises claras, objetivas e úteis para investidores.

Diretrizes:
- Use linguagem clara e acessível, mas precisa
- Indique explicitamente quando dados estão indisponíveis
- Sempre contextualize com o cenário macroeconômico (Selic, IPCA) quando disponível
- Classifique cada ação como: COMPRA, NEUTRO ou VENDA (com justificativa curta)
- Destaque os principais riscos e oportunidades
- Formate a resposta em Markdown estruturado
"""


class AnalysisAgent:
    """Usa Claude para analisar os dados de mercado e gerar insights."""

    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.model = "claude-sonnet-4-6"

    def analyze(self, market_data: dict) -> str:
        console.print("\n[magenta]🤖 AnalysisAgent:[/] Analisando com Claude...")

        prompt = self._build_prompt(market_data)

        with console.status("[magenta]Gerando análise...[/]"):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

        analysis = response.content[0].text
        console.print("\n[bold]═══ ANÁLISE FUNDAMENTALISTA ═══[/bold]\n")
        console.print(Markdown(analysis))
        return analysis

    def _build_prompt(self, market_data: dict) -> str:
        acoes = market_data.get("acoes", [])
        selic = market_data.get("selic")
        ipca = market_data.get("ipca")

        linhas = []

        if selic:
            linhas.append(f"**Taxa Selic atual:** {selic}% a.a.")
        if ipca:
            linhas.append(f"**IPCA (último):** {ipca}%")

        linhas.append(f"\n**Ações analisadas:** {len(acoes)}\n")

        for s in acoes:
            linhas.append(f"### {s['ticker']} — {s['nome']}")
            linhas.append(f"- Preço: R$ {s['preco']}" if s["preco"] else "- Preço: N/D")
            linhas.append(f"- Variação do dia: {s['variacao_dia']:+.2f}%" if s["variacao_dia"] else "- Variação: N/D")
            linhas.append(f"- Máx 52s: R$ {s['variacao_52s_max']} | Mín 52s: R$ {s['variacao_52s_min']}")
            linhas.append(f"- P/L: {s['p_l']}" if s["p_l"] else "- P/L: N/D")
            linhas.append(f"- P/VP: {s['p_vp']}" if s["p_vp"] else "- P/VP: N/D")
            linhas.append(f"- Dividend Yield: {s['dividend_yield']}%" if s["dividend_yield"] else "- DY: N/D")
            linhas.append(f"- ROE: {s['roe']}" if s["roe"] else "- ROE: N/D")
            linhas.append(f"- Setor: {s['setor']}" if s["setor"] else "")
            linhas.append("")

        linhas.append("""---
Por favor:
1. Faça um resumo do cenário macro atual com base na Selic e IPCA
2. Para cada ação, forneça: análise dos indicadores, pontos positivos, riscos e recomendação (COMPRA/NEUTRO/VENDA)
3. Finalize com um ranking das 3 melhores oportunidades do lote analisado
""")

        return "\n".join(linhas)

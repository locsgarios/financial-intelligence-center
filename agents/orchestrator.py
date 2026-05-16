import os
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from tools.brapi import BrapiClient
from agents.market_agent import MarketAgent
from agents.analysis_agent import AnalysisAgent

console = Console()


class Orchestrator:
    """Coordena o pipeline completo: coleta → análise → relatório."""

    def __init__(self):
        brapi_key = os.getenv("BRAPI_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

        self.brapi = BrapiClient(token=brapi_key)
        self.market_agent = MarketAgent(self.brapi)
        self.analysis_agent = AnalysisAgent(api_key=anthropic_key or None)

        watchlist_env = os.getenv("WATCHLIST", "PETR4,VALE3,ITUB4,BBDC4,WEGE3")
        self.tickers = [t.strip().upper() for t in watchlist_env.split(",") if t.strip()]
        self.max_stocks = int(os.getenv("MAX_STOCKS", "8"))
        self.interval = int(os.getenv("WATCH_INTERVAL", "300"))

    def run_once(self):
        tickers = self.tickers[: self.max_stocks]

        console.print(Panel(
            f"[bold green]Financial Agents — B3[/bold green]\n"
            f"Tickers: [cyan]{', '.join(tickers)}[/cyan]\n"
            f"Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            title="🚀 Iniciando análise",
            border_style="green",
        ))

        market_data = self.market_agent.collect(tickers)
        analysis = self.analysis_agent.analyze(market_data)

        self._save_report(analysis, tickers)

    def run_watch(self):
        console.print(Panel(
            f"[bold yellow]Modo watch ativado[/bold yellow]\n"
            f"Intervalo: {self.interval}s | Tickers: {', '.join(self.tickers[:self.max_stocks])}",
            title="👁️  Watch Mode",
            border_style="yellow",
        ))

        iteration = 1
        while True:
            console.print(Rule(f"[bold]Iteração {iteration} — {datetime.now().strftime('%H:%M:%S')}[/bold]"))
            try:
                self.run_once()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                console.print(f"[red]Erro na iteração {iteration}: {e}[/red]")

            console.print(f"\n[dim]Próxima análise em {self.interval}s. Ctrl+C para sair.[/dim]")
            time.sleep(self.interval)
            iteration += 1

    def _save_report(self, analysis: str, tickers: list[str]):
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = reports_dir / f"relatorio_{timestamp}.md"

        header = (
            f"# Relatório de Análise B3\n\n"
            f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  \n"
            f"**Tickers:** {', '.join(tickers)}\n\n---\n\n"
        )

        filename.write_text(header + analysis, encoding="utf-8")
        console.print(f"\n[green]✅ Relatório salvo em:[/green] [link]{filename}[/link]")

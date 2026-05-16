import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", encoding="utf-8", override=True)

from rich.console import Console
console = Console()


def run_live():
    from tools.brapi import BrapiClient
    from agents.scanner import StockScanner
    from agents.dashboard import run_live_dashboard
    from agents.macro_agent import start_macro_updater

    token = os.getenv("BRAPI_KEY", "")
    console.print("[bold green]Iniciando Financial Intelligence Center...[/bold green]")
    console.print("[dim]Carregando dados macro...[/dim]")
    start_macro_updater(brapi_token=token)

    console.print("[dim]Iniciando scanner de mercado...[/dim]")
    client  = BrapiClient(token=token)
    scanner = StockScanner(client)
    scanner.start()

    run_live_dashboard(scanner)


def run_once(tickers=None):
    from agents.orchestrator import Orchestrator
    orch = Orchestrator()
    if tickers:
        orch.tickers = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    orch.run_once()


def run_watch(tickers=None):
    from agents.orchestrator import Orchestrator
    orch = Orchestrator()
    if tickers:
        orch.tickers = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    orch.run_watch()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Financial Intelligence Center — B3 Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modos:
  live   Dashboard ao vivo — top 10 oportunidades, atualiza a cada segundo (padrão)
  once   Análise única com Claude para tickers específicos
  watch  Análise repetida por intervalo configurado no .env

Exemplos:
  python main.py                                  # live (padrão)
  python main.py --mode live
  python main.py --mode once --tickers PETR4,VALE3
  python main.py --mode watch
        """,
    )
    parser.add_argument("--mode", choices=["live","once","watch"], default="live")
    parser.add_argument("--tickers", type=str, default=None)
    args = parser.parse_args()

    try:
        if   args.mode == "live":  run_live()
        elif args.mode == "once":  run_once(args.tickers)
        elif args.mode == "watch": run_watch(args.tickers)
    except KeyboardInterrupt:
        console.print("\n[yellow]Encerrado.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Erro:[/bold red] {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

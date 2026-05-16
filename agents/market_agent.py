from tools.brapi import BrapiClient
from rich.console import Console
from rich.table import Table

console = Console()


class MarketAgent:
    """Responsável por coletar e estruturar dados de mercado da B3."""

    def __init__(self, client: BrapiClient):
        self.client = client

    def collect(self, tickers: list[str]) -> dict:
        console.print(f"[cyan]📡 MarketAgent:[/] Buscando cotações: {', '.join(tickers)}")

        quotes = self.client.get_quote(tickers)
        selic = self.client.get_prime_rate()
        inflation = self.client.get_inflation()

        stocks = []
        for q in quotes:
            stocks.append({
                "ticker": q.get("symbol", ""),
                "nome": q.get("longName", q.get("shortName", "")),
                "preco": q.get("regularMarketPrice"),
                "variacao_dia": q.get("regularMarketChangePercent"),
                "variacao_52s_max": q.get("fiftyTwoWeekHigh"),
                "variacao_52s_min": q.get("fiftyTwoWeekLow"),
                "volume": q.get("regularMarketVolume"),
                "market_cap": q.get("marketCap"),
                "p_l": q.get("priceEarnings"),
                "p_vp": q.get("priceToBook"),
                "dividend_yield": q.get("dividendYield"),
                "roe": q.get("returnOnEquityTTM"),
                "ebitda": q.get("ebitda"),
                "divida_liquida": q.get("netDebt"),
                "setor": q.get("sector", ""),
                "industria": q.get("industry", ""),
            })

        self._print_table(stocks)

        return {
            "acoes": stocks,
            "selic": selic[0].get("value") if selic else None,
            "ipca": inflation[0].get("value") if inflation else None,
        }

    def _print_table(self, stocks: list[dict]):
        table = Table(title="Cotações B3", show_lines=True)
        table.add_column("Ticker", style="bold cyan")
        table.add_column("Preço", justify="right")
        table.add_column("Var. Dia", justify="right")
        table.add_column("P/L", justify="right")
        table.add_column("DY%", justify="right")
        table.add_column("Setor")

        for s in stocks:
            var = s["variacao_dia"]
            var_str = f"{var:+.2f}%" if var is not None else "-"
            cor = "green" if (var or 0) >= 0 else "red"

            preco = f"R$ {s['preco']:.2f}" if s["preco"] else "-"
            pl = f"{s['p_l']:.1f}" if s["p_l"] else "-"
            dy = f"{s['dividend_yield']:.2f}%" if s["dividend_yield"] else "-"

            table.add_row(
                s["ticker"],
                preco,
                f"[{cor}]{var_str}[/{cor}]",
                pl,
                dy,
                s["setor"] or "-",
            )

        console.print(table)

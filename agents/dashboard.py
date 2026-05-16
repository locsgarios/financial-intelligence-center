import time
from datetime import datetime
from rich.live import Live
from rich.layout import Layout
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.align import Align
from rich.rule import Rule

from models.opportunity import Opportunity, SignalType, OpType, AssetClass
from agents.macro_agent import get_macro
from agents.scanner import StockScanner

console = Console()

SCORE_STYLES = [(85,"bold green"),(70,"green"),(55,"yellow"),(40,"orange3"),(0,"red")]

def _score_style(s: float) -> str:
    for t, c in SCORE_STYLES:
        if s >= t: return c
    return "red"

def _score_bar(s: float) -> str:
    filled = int(s / 10)
    return "█" * filled + "░" * (10 - filled)

def _fmt_signal(opp: Opportunity) -> Text:
    t = Text(f"{opp.signal.emoji} {opp.signal.value}")
    t.stylize(opp.signal.color)
    return t

def _fmt_var(v: float) -> Text:
    s = f"{v:+.2f}%"
    return Text(s, style="bold green" if v >= 0 else "bold red")

def _fmt_op(op: OpType) -> str:
    return {"DT":"[bold magenta]DT[/bold magenta]",
            "SW":"[bold cyan]SW[/bold cyan]",
            "POS":"[bold blue]POS[/bold blue]"}.get(op.value, op.value)

def _fmt_cls(cls: AssetClass) -> str:
    return {"Ação":"[white]AÇÃ[/white]","FII":"[yellow]FII[/yellow]",
            "ETF":"[cyan]ETF[/cyan]","BDR":"[magenta]BDR[/magenta]",
            "Cripto":"[orange3]CRP[/orange3]"}.get(cls.value, cls.value[:3])

def _fmt_rsi(rsi) -> str:
    if rsi is None: return "[dim]-[/dim]"
    if rsi < 30:    return f"[bold green]{rsi:.0f}[/bold green]"
    if rsi > 70:    return f"[bold red]{rsi:.0f}[/bold red]"
    return f"[white]{rsi:.0f}[/white]"

def _fmt_rr(rr: float) -> str:
    if rr <= 0: return "[dim]-[/dim]"
    c = "green" if rr >= 2 else ("yellow" if rr >= 1.5 else "red")
    return f"[{c}]{rr:.1f}x[/{c}]"

def _fmt_price(p) -> str:
    return f"R${p:,.2f}" if p else "-"

def _fmt_conf(c: str) -> str:
    return {"Alto":"[green]●●●[/green]","Médio":"[yellow]●●○[/yellow]",
            "Baixo":"[red]●○○[/red]"}.get(c, c)

MEDALS = ["🥇","🥈","🥉","④","⑤","⑥","⑦","⑧","⑨","⑩"]

def _build_ranking_table(top: list[Opportunity]) -> Table:
    t = Table(show_header=True, header_style="bold white on navy_blue",
              show_lines=True, expand=True, padding=(0,1))
    t.add_column("#",        width=3,  justify="center")
    t.add_column("Cls",      width=4,  justify="center")
    t.add_column("Tipo",     width=4,  justify="center")
    t.add_column("Ticker",   width=7,  style="bold cyan")
    t.add_column("Nome",     min_width=18, max_width=22)
    t.add_column("Sinal",    min_width=16)
    t.add_column("Preço",    width=10, justify="right")
    t.add_column("Var%",     width=8,  justify="right")
    t.add_column("RSI",      width=5,  justify="center")
    t.add_column("Entrada",  width=10, justify="right")
    t.add_column("Stop",     width=10, justify="right")
    t.add_column("Alvo",     width=10, justify="right")
    t.add_column("R:R",      width=6,  justify="center")
    t.add_column("Score",    width=16, justify="left")
    t.add_column("Conf.",    width=5,  justify="center")

    for i, opp in enumerate(top):
        score = opp.score.total
        sty   = _score_style(score)
        bar   = _score_bar(score)
        medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}"

        t.add_row(
            medal,
            _fmt_cls(opp.asset_class),
            _fmt_op(opp.op_type),
            opp.ticker,
            opp.name,
            _fmt_signal(opp),
            _fmt_price(opp.price),
            _fmt_var(opp.var_day),
            _fmt_rsi(opp.ta.rsi),
            _fmt_price(opp.entry),
            _fmt_price(opp.stop),
            _fmt_price(opp.target),
            _fmt_rr(opp.rr),
            f"[{sty}]{bar} {score:.0f}[/{sty}]",
            _fmt_conf(opp.score.confidence),
        )
    return t

def _build_header(stats: dict) -> Panel:
    macro = get_macro()
    now   = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    scanned = stats["scanned"]
    total   = stats["total"]
    current = stats.get("current","")
    last    = stats["last_update"]
    last_s  = last.strftime("%H:%M:%S") if last else "--:--:--"
    pct     = scanned / total * 100 if total else 0

    bar_len = 28
    filled  = int(pct / 100 * bar_len)
    pb = "[green]" + "█"*filled + "[/green][dim]" + "░"*(bar_len-filled) + "[/dim]"

    macro_str = macro.summary() if macro.selic else "[dim]Carregando dados macro...[/dim]"

    lines = [
        f"[bold white] ⚡ FINANCIAL INTELLIGENCE CENTER — B3 LIVE SCANNER [/bold white]  [dim]{now}[/dim]",
        f" {macro_str}",
        f" Varredura: {pb} [cyan]{scanned}/{total}[/cyan] ({pct:.0f}%)   Atual: [yellow]{current}[/yellow]   Última update: [green]{last_s}[/green]",
    ]
    return Panel("\n".join(lines), style="on grey11", padding=(0,1))

def _build_score_legend() -> str:
    return (
        " [bold]Score:[/bold] "
        "[bold green]85+ Muito Forte[/bold green]  "
        "[green]70-84 Relevante[/green]  "
        "[yellow]55-69 Moderada[/yellow]  "
        "[orange3]40-54 Observação[/orange3]  "
        "[red]<40 Descartar[/red]"
        "  [dim]│[/dim]  "
        "[bold]Tipo:[/bold] [magenta]DT[/magenta]=Day Trade  [cyan]SW[/cyan]=Swing  [blue]POS[/blue]=Posição"
        "  [dim]│[/dim]  "
        "[dim]Ctrl+C sair  •  Score: Técn(20)+Fund(15)+Macro(15)+Sent(10)+Liq(10)+R:R(15)+BT(10)+Timing(5)[/dim]"
    )

def _build_reasons_panel(top: list[Opportunity]) -> Panel:
    lines = []
    for opp in top[:5]:
        if opp.reasons or opp.risks:
            reasons_str = "  ".join(f"[green]+[/green] {r}" for r in opp.reasons[:2])
            risks_str   = "  ".join(f"[red]−[/red] {r}" for r in opp.risks[:1])
            trend = opp.ta.trend or ""
            pattern = opp.ta.pattern or ""
            extra = f"[dim]{trend}{'  '+pattern if pattern else ''}[/dim]"
            lines.append(f"[bold cyan]{opp.ticker}[/bold cyan]  {reasons_str}  {risks_str}  {extra}")
    content = "\n".join(lines) if lines else "[dim]Aguardando análises...[/dim]"
    return Panel(content, title="[bold]Motivos (Top 5)[/bold]", padding=(0,1), border_style="dim")

def run_live_dashboard(scanner: StockScanner):
    with Live(console=console, refresh_per_second=1, screen=True) as live:
        while True:
            top   = scanner.get_top(10)
            stats = scanner.get_stats()

            layout = Layout()
            layout.split_column(
                Layout(_build_header(stats), name="header", size=5),
                Layout(name="main"),
                Layout(name="reasons", size=8),
                Layout(Panel(_build_score_legend(), padding=(0,1), style="on grey7"),
                       name="footer", size=3),
            )

            if top:
                layout["main"].update(Panel(
                    _build_ranking_table(top),
                    title="[bold yellow]🏆 TOP 10 OPORTUNIDADES — RANKING AO VIVO (Tempo Real)[/bold yellow]",
                    border_style="yellow", padding=(0,0),
                ))
                layout["reasons"].update(_build_reasons_panel(top))
            else:
                layout["main"].update(Align.center(
                    Panel(
                        "[yellow]Coletando dados...[/yellow]\n"
                        "[dim]O scanner está buscando cotações e calculando indicadores.\n"
                        "Os primeiros resultados aparecem em ~30 segundos.[/dim]",
                        border_style="yellow",
                    ), vertical="middle",
                ))
                layout["reasons"].update(Panel("[dim]Aguardando...[/dim]", padding=(0,1)))

            live.update(layout)
            time.sleep(1)

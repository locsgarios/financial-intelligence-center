import os
import threading
import time
from datetime import datetime

from tools.brapi import BrapiClient
from config.markets import ALL_TICKERS
from models.opportunity import Opportunity
from agents import signal_agent

# Score minimo para disparar alerta Telegram
ALERT_SCORE_THRESHOLD = int(os.getenv('ALERT_SCORE_THRESHOLD', '65'))

class StockScanner:
    """Varre continuamente todos os ativos e mantém o ranking de oportunidades."""

    def __init__(self, client: BrapiClient):
        self.client = client
        self.opportunities: dict[str, Opportunity] = {}
        self.lock = threading.Lock()
        self._running = False
        self.scanned_count = 0
        self.total_tickers = len(ALL_TICKERS)
        self.current_ticker = ''
        self.last_update: datetime | None = None
        self.errors = 0

    def start(self):
        self._running = True
        t = threading.Thread(target=self._scan_loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False

    def _scan_loop(self):
        idx = 0
        while self._running:
            ticker = ALL_TICKERS[idx % len(ALL_TICKERS)]

            with self.lock:
                self.current_ticker = ticker

            quote = self.client.get_single_quote(ticker)

            if quote and quote.get('regularMarketPrice'):
                try:
                    opp = signal_agent.build_opportunity(ticker, quote)
                    if opp:
                        with self.lock:
                            self.opportunities[ticker] = opp
                            self.scanned_count = len(self.opportunities)
                            self.last_update = datetime.now()
                        # Alerta Telegram para oportunidades fortes (nao bloqueia o loop)
                        if opp.score.total >= ALERT_SCORE_THRESHOLD:
                            try:
                                from tools import telegram
                                threading.Thread(
                                    target=telegram.send_alert,
                                    args=(opp,),
                                    daemon=True,
                                ).start()
                            except Exception:
                                pass
                except Exception:
                    self.errors += 1

            idx += 1
            time.sleep(0.4)  # ~2.5 req/s — respeitoso com a BRAPI free

    def get_top(self, n: int = 10, signal_filter=None) -> list[Opportunity]:
        with self.lock:
            ops = list(self.opportunities.values())

        if signal_filter:
            ops = [o for o in ops if o.signal in signal_filter]

        # Exclui sinais de aguardar/stop do ranking padrão
        from models.opportunity import SignalType
        ops = [o for o in ops if o.signal not in (SignalType.WAIT,)]

        ops.sort(key=lambda x: x.score.total, reverse=True)
        return ops[:n]

    def get_stats(self) -> dict:
        with self.lock:
            return {
                'scanned': self.scanned_count,
                'total': self.total_tickers,
                'last_update': self.last_update,
                'current': self.current_ticker,
                'errors': self.errors,
                    }

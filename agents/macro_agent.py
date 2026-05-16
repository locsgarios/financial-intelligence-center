import time
import threading
import requests

_cache: dict = {}
_lock = threading.Lock()
CACHE_TTL = 600  # 10 minutos


def _bcb(series_id: int) -> float | None:
    """Busca último valor de uma série no BCB."""
    key = f"bcb_{series_id}"
    with _lock:
        if key in _cache and time.time() - _cache[key][0] < CACHE_TTL:
            return _cache[key][1]
    try:
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados/ultimos/1?formato=json"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        val = float(r.json()[0]["valor"].replace(",", "."))
        with _lock:
            _cache[key] = (time.time(), val)
        return val
    except Exception:
        return None


def _brapi_quote(symbol: str, token: str = "") -> dict:
    key = f"brapi_{symbol}"
    with _lock:
        if key in _cache and time.time() - _cache[key][0] < 60:
            return _cache[key][1]
    try:
        params = {"token": token} if token else {}
        r = requests.get(f"https://brapi.dev/api/quote/{symbol}", params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        data = results[0] if results else {}
        with _lock:
            _cache[key] = (time.time(), data)
        return data
    except Exception:
        return {}


def _brapi_currency(token: str = "") -> dict:
    key = "brapi_usd"
    with _lock:
        if key in _cache and time.time() - _cache[key][0] < 60:
            return _cache[key][1]
    try:
        params = {"currency": "USD-BRL"}
        if token:
            params["token"] = token
        r = requests.get("https://brapi.dev/api/v2/currency", params=params, timeout=10)
        r.raise_for_status()
        currencies = r.json().get("currency", [])
        data = currencies[0] if currencies else {}
        with _lock:
            _cache[key] = (time.time(), data)
        return data
    except Exception:
        return {}


class MacroContext:
    selic:      float | None = None
    ipca:       float | None = None
    igpm:       float | None = None
    ibov:       float | None = None
    ibov_var:   float | None = None
    dolar:      float | None = None
    dolar_var:  float | None = None
    ifix:       float | None = None

    def macro_score(self) -> float:
        """Score macro para o mercado de ações (0-15)."""
        score = 7.5  # neutro
        if self.selic:
            if self.selic <= 10:    score += 3
            elif self.selic <= 12:  score += 1
            elif self.selic >= 14:  score -= 2
        if self.ipca:
            if self.ipca <= 4:      score += 2
            elif self.ipca >= 6:    score -= 1
        if self.ibov_var:
            if self.ibov_var > 0:   score += 1
            elif self.ibov_var < -1: score -= 1
        return round(min(max(score, 0), 15), 1)

    def sector_boost(self, ticker: str) -> float:
        """Ajuste de score macro por setor/ativo (+/- 0 a 2 pts)."""
        t = ticker.upper()
        # Exportadoras beneficiadas pelo dólar alto
        exporters = {"VALE3", "PETR4", "PETR3", "SUZB3", "KLBN11", "JBSS3", "BRFS3", "MRFG3"}
        # Sensíveis à Selic
        rate_sensitive = {"MGLU3", "COGN3", "YDUQ3", "RENT3", "RAIL3", "CCRO3"}
        # Bancos: spread melhora com Selic alta
        banks = {"ITUB4", "ITUB3", "BBDC4", "BBDC3", "BBAS3", "SANB11", "BPAC11"}

        dolar = self.dolar or 5.0
        selic = self.selic or 13.75

        boost = 0.0
        if t in exporters and dolar > 5.2:    boost += 1.5
        if t in banks and selic > 12:          boost += 1.0
        if t in rate_sensitive and selic > 13: boost -= 1.5
        return boost

    def summary(self) -> str:
        parts = []
        if self.selic:    parts.append(f"SELIC {self.selic:.2f}%")
        if self.ipca:     parts.append(f"IPCA {self.ipca:.2f}%")
        if self.ibov:     parts.append(f"IBOV {self.ibov:,.0f}({self.ibov_var:+.1f}%)" if self.ibov_var else f"IBOV {self.ibov:,.0f}")
        if self.dolar:    parts.append(f"USD R${self.dolar:.2f}({self.dolar_var:+.2f}%)" if self.dolar_var else f"USD R${self.dolar:.2f}")
        return "  │  ".join(parts)


_context = MacroContext()
_context_lock = threading.Lock()


def get_macro() -> MacroContext:
    return _context


def start_macro_updater(brapi_token: str = ""):
    """Inicia thread que atualiza dados macro em background."""
    def _update():
        while True:
            ctx = MacroContext()
            ctx.selic     = _bcb(11)    # Selic Over
            ctx.ipca      = _bcb(433)   # IPCA acumulado 12m
            ctx.igpm      = _bcb(189)   # IGP-M

            ibov = _brapi_quote("^BVSP", brapi_token)
            if ibov:
                ctx.ibov      = ibov.get("regularMarketPrice")
                ctx.ibov_var  = ibov.get("regularMarketChangePercent")

            ifix = _brapi_quote("^IFIX", brapi_token)
            if ifix:
                ctx.ifix = ifix.get("regularMarketPrice")

            usd = _brapi_currency(brapi_token)
            if usd:
                ctx.dolar     = usd.get("bidPrice") or usd.get("ask")
                ctx.dolar_var = usd.get("pctChange")

            with _context_lock:
                global _context
                _context = ctx

            time.sleep(300)  # atualiza a cada 5 min

    t = threading.Thread(target=_update, daemon=True)
    t.start()

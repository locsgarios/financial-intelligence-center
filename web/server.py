import json
import asyncio
import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

_scanner = None
_macro   = None


def set_scanner(scanner, macro_fn):
    global _scanner, _macro
    _scanner = scanner
    _macro   = macro_fn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicia scanner e macro ao subir o servidor (local ou produção)."""
    from tools.brapi import BrapiClient
    from agents.scanner import StockScanner
    from agents.macro_agent import start_macro_updater, get_macro

    token = os.getenv("BRAPI_KEY", "")
    start_macro_updater(brapi_token=token)

    client  = BrapiClient(token=token)
    scanner = StockScanner(client)
    scanner.start()
    set_scanner(scanner, get_macro)

    yield

    scanner.stop()


app = FastAPI(title="Financial Intelligence Center", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _serialize_opp(opp) -> dict:
    return {
        "ticker":      opp.ticker,
        "name":        opp.name,
        "cls":         opp.asset_class.value,
        "op_type":     opp.op_type.value,
        "signal":      opp.signal.value,
        "signal_color":opp.signal.color.replace("bold ", ""),
        "signal_emoji":opp.signal.emoji,
        "price":       opp.price,
        "entry":       opp.entry,
        "stop":        opp.stop,
        "target":      opp.target,
        "rr":          opp.rr,
        "var_day":     round(opp.var_day, 2),
        "volume":      opp.volume,
        "rsi":         round(opp.ta.rsi, 1) if opp.ta.rsi else None,
        "trend":       opp.ta.trend,
        "pattern":     opp.ta.pattern,
        "score":       round(opp.score.total, 1),
        "score_tech":  opp.score.technical,
        "score_fund":  opp.score.fundamental,
        "score_macro": opp.score.macro,
        "score_sent":  opp.score.sentiment,
        "score_liq":   opp.score.liquidity,
        "score_rr":    opp.score.risk_reward,
        "score_bt":    opp.score.backtest,
        "score_time":  opp.score.timing,
        "confidence":  opp.score.confidence,
        "risk_level":  opp.risk_level.value,
        "reasons":     opp.reasons,
        "risks":       opp.risks,
        "updated":     opp.updated_at.strftime("%H:%M:%S"),
    }


def _get_payload() -> dict:
    top   = _scanner.get_top(200) if _scanner else []
    stats = _scanner.get_stats()  if _scanner else {}
    macro = _macro()              if _macro   else None

    return {
        "ts":       datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "scanned":  stats.get("scanned", 0),
        "total":    stats.get("total", 0),
        "current":  stats.get("current", ""),
        "last_upd": stats.get("last_update").strftime("%H:%M:%S") if stats.get("last_update") else "--:--:--",
        "selic":    macro.selic    if macro else None,
        "ipca":     macro.ipca     if macro else None,
        "ibov":     macro.ibov     if macro else None,
        "ibov_var": macro.ibov_var if macro else None,
        "dolar":    macro.dolar    if macro else None,
        "dolar_var":macro.dolar_var if macro else None,
        "opps":     [_serialize_opp(o) for o in top],
    }


@app.get("/api/data")
async def get_data():
    return _get_payload()


@app.get("/health")
async def health():
    return {"status": "ok", "scanned": _scanner.scanned_count if _scanner else 0}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps(_get_payload()))
            await asyncio.sleep(1)
    except (WebSocketDisconnect, Exception):
        pass


@app.get("/", response_class=HTMLResponse)
async def root():
    from web.template import HTML
    return HTMLResponse(HTML)

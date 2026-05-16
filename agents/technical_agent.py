import os
import time
import threading
import warnings
from typing import Optional
import numpy as np
import pandas as pd
import requests
import ta
from config.markets import yf_symbol, AssetClass, asset_class as get_class
from models.opportunity import TechnicalData, ScoreBreakdown, OpType

warnings.filterwarnings("ignore")

_cache: dict[str, tuple[float, pd.DataFrame]] = {}
_cache_lock = threading.Lock()
CACHE_TTL = 300  # 5 minutos
_BRAPI_TOKEN = os.getenv("BRAPI_KEY", "")
_BRAPI_BASE = "https://brapi.dev/api"


def _fetch_brapi_history(ticker: str) -> pd.DataFrame:
    """Busca 3 meses de OHLCV via BRAPI — sem rate-limit do Yahoo Finance."""
    global _BRAPI_TOKEN
    _BRAPI_TOKEN = os.getenv("BRAPI_KEY", _BRAPI_TOKEN)
    try:
        params = {"range": "3mo", "interval": "1d"}
        if _BRAPI_TOKEN:
            params["token"] = _BRAPI_TOKEN
        r = requests.get(f"{_BRAPI_BASE}/quote/{ticker}", params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            return pd.DataFrame()
        hist = results[0].get("historicalDataPrice", [])
        if not hist:
            return pd.DataFrame()
        df = pd.DataFrame(hist)
        df["date"] = pd.to_datetime(df["date"], unit="s")
        df = df.rename(columns={"date": "Date", "open": "Open", "high": "High",
                                  "low": "Low", "close": "Close", "volume": "Volume"})
        df = df.set_index("Date").sort_index()
        return df[["Open","High","Low","Close","Volume"]].dropna(subset=["Close"])
    except Exception:
        return pd.DataFrame()


def _fetch_history(ticker: str, period: str = "60d", interval: str = "1d") -> pd.DataFrame:
    """BRAPI primeiro; fallback yfinance com backoff."""
    key = f"{ticker}_{interval}"
    with _cache_lock:
        if key in _cache:
            ts, df = _cache[key]
            if time.time() - ts < CACHE_TTL:
                return df

    df = _fetch_brapi_history(ticker)

    if df.empty:
        try:
            import yfinance as yf
            sym = yf_symbol(ticker)
            time.sleep(2.0)
            df = yf.download(sym, period=period, interval=interval, progress=False, auto_adjust=True)
            if not df.empty:
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
                df.dropna(subset=["Close"], inplace=True)
        except Exception:
            df = pd.DataFrame()

    with _cache_lock:
        _cache[key] = (time.time(), df)
    return df


def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) < 20:
        return df
    try:
        df["rsi"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
        macd_ind = ta.trend.MACD(df["Close"])
        df["macd"] = macd_ind.macd()
        df["macd_sig"] = macd_ind.macd_signal()
        df["macd_hist"] = macd_ind.macd_diff()
        bb = ta.volatility.BollingerBands(df["Close"], window=20)
        df["bb_high"] = bb.bollinger_hband()
        df["bb_low"] = bb.bollinger_lband()
        df["bb_mid"] = bb.bollinger_mavg()
        df["bb_pct"] = bb.bollinger_pband()
        df["sma20"] = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator()
        df["sma50"] = ta.trend.SMAIndicator(df["Close"], window=50).sma_indicator()
        df["atr"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()
        df["obv"] = ta.volume.OnBalanceVolumeIndicator(df["Close"], df["Volume"]).on_balance_volume()
    except Exception:
        pass
    return df


def _detect_trend(df: pd.DataFrame) -> str:
    try:
        last = df.iloc[-1]
        sma20 = last.get("sma20"); sma50 = last.get("sma50"); close = last["Close"]
        if pd.isna(sma20) or pd.isna(sma50): return "INDEFINIDO"
        if close > sma20 > sma50: return "ALTA"
        if close < sma20 < sma50: return "BAIXA"
        return "LATERAL"
    except Exception:
        return "INDEFINIDO"


def _detect_pattern(df: pd.DataFrame) -> str:
    try:
        if len(df) < 3: return ""
        last = df.iloc[-1]; prev = df.iloc[-2]
        macd=last.get("macd"); macd_sig=last.get("macd_sig")
        p_macd=prev.get("macd"); p_sig=prev.get("macd_sig")
        rsi=last.get("rsi"); bb_pct=last.get("bb_pct")
        sma20=last.get("sma20"); sma50=last.get("sma50")
        p_sma20=prev.get("sma20"); p_sma50=prev.get("sma50")
        if all(v is not None and not pd.isna(v) for v in [macd,macd_sig,p_macd,p_sig]):
            if p_macd < p_sig and macd > macd_sig: return "Cruzamento MACD Alta"
            if p_macd > p_sig and macd < macd_sig: return "Cruzamento MACD Baixa"
        if rsi is not None and not pd.isna(rsi):
            if rsi < 30: return "RSI Sobrevenda"
            if rsi > 70: return "RSI Sobrecompra"
        if bb_pct is not None and not pd.isna(bb_pct):
            if bb_pct < 0.05: return "Suporte Bollinger"
            if bb_pct > 0.95: return "Resistência Bollinger"
        if all(v is not None and not pd.isna(v) for v in [sma20,sma50,p_sma20,p_sma50]):
            if p_sma20 < p_sma50 and sma20 > sma50: return "Golden Cross"
            if p_sma20 > p_sma50 and sma20 < sma50: return "Death Cross"
        return ""
    except Exception:
        return ""


def analyze(ticker: str, current_price: float, var_day: float, volume: float) -> tuple[TechnicalData, float]:
    df = _fetch_history(ticker)
    td = TechnicalData()
    score = 5.0
    if df.empty or len(df) < 20:
        td.trend = "INDEFINIDO"
        if var_day > 2: score += 3
        elif var_day > 0: score += 1
        return td, round(score, 1)
    df = _add_indicators(df)
    last = df.iloc[-1]
    td.rsi=_safe(last,"rsi"); td.macd=_safe(last,"macd"); td.macd_sig=_safe(last,"macd_sig")
    td.bb_pos=_safe(last,"bb_pct"); td.sma20=_safe(last,"sma20"); td.sma50=_safe(last,"sma50")
    td.atr=_safe(last,"atr"); td.trend=_detect_trend(df); td.pattern=_detect_pattern(df)
    score = 5.0
    if td.rsi is not None:
        if td.rsi < 30: score += 5
        elif td.rsi < 40: score += 4
        elif td.rsi < 50: score += 3
        elif td.rsi < 60: score += 2
        elif td.rsi < 70: score += 1
    if td.macd is not None and td.macd_sig is not None:
        hist = td.macd - td.macd_sig
        if td.macd > td.macd_sig and hist > 0: score += 4
        elif td.macd > td.macd_sig: score += 2
        elif td.macd < td.macd_sig and hist < 0: score += 0
        else: score += 1
    score += {"ALTA": 4, "LATERAL": 2, "BAIXA": 0, "INDEFINIDO": 1}.get(td.trend, 1)
    if td.bb_pos is not None:
        if td.bb_pos < 0.2: score += 3
        elif td.bb_pos < 0.4: score += 2
        elif td.bb_pos < 0.6: score += 1
    try:
        obv_vals = df["obv"].dropna()
        if len(obv_vals) >= 5:
            obv_trend = obv_vals.iloc[-1] > obv_vals.iloc[-5]
            if obv_trend and var_day > 0: score += 3
            elif obv_trend: score += 1
    except Exception:
        pass
    return td, round(min(score, 20), 1)


def calc_stops(ticker: str, price: float, op_type: OpType) -> tuple[float, float]:
    df = _fetch_history(ticker)
    if df.empty:
        return round(price * 0.98, 2), round(price * 1.04, 2)
    df = _add_indicators(df)
    atr = _safe(df.iloc[-1], "atr") or price * 0.02
    if op_type == OpType.DAY_TRADE: mult_stop, mult_target = 1.0, 2.0
    elif op_type == OpType.SWING: mult_stop, mult_target = 2.0, 4.0
    else: mult_stop, mult_target = 3.0, 6.0
    return round(price - atr * mult_stop, 2), round(price + atr * mult_target, 2)


def _safe(row, col: str) -> Optional[float]:
    try:
        v = row[col]
        return float(v) if not pd.isna(v) else None
    except Exception:
        return None

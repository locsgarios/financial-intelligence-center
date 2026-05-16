import time
import threading
import warnings
from typing import Optional
import numpy as np
import pandas as pd
import ta
import yfinance as yf
from config.markets import yf_symbol, AssetClass, asset_class as get_class
from models.opportunity import TechnicalData, ScoreBreakdown, OpType

warnings.filterwarnings("ignore")

_cache: dict[str, tuple[float, pd.DataFrame]] = {}
_cache_lock = threading.Lock()
CACHE_TTL = 300  # 5 minutos


def _fetch_history(ticker: str, period: str = "60d", interval: str = "1d") -> pd.DataFrame:
    sym = yf_symbol(ticker)
    key = f"{sym}_{interval}"
    with _cache_lock:
        if key in _cache:
            ts, df = _cache[key]
            if time.time() - ts < CACHE_TTL:
                return df
    try:
        df = yf.download(sym, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df.dropna(subset=["Close"], inplace=True)
        with _cache_lock:
            _cache[key] = (time.time(), df)
        return df
    except Exception:
        return pd.DataFrame()


def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) < 20:
        return df
    try:
        df["rsi"]       = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
        macd_ind        = ta.trend.MACD(df["Close"])
        df["macd"]      = macd_ind.macd()
        df["macd_sig"]  = macd_ind.macd_signal()
        df["macd_hist"] = macd_ind.macd_diff()
        bb              = ta.volatility.BollingerBands(df["Close"], window=20)
        df["bb_high"]   = bb.bollinger_hband()
        df["bb_low"]    = bb.bollinger_lband()
        df["bb_mid"]    = bb.bollinger_mavg()
        df["bb_pct"]    = bb.bollinger_pband()   # 0=inf, 1=sup
        df["sma20"]     = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator()
        df["sma50"]     = ta.trend.SMAIndicator(df["Close"], window=50).sma_indicator()
        df["atr"]       = ta.volatility.AverageTrueRange(
                              df["High"], df["Low"], df["Close"], window=14).average_true_range()
        df["obv"]       = ta.volume.OnBalanceVolumeIndicator(
                              df["Close"], df["Volume"]).on_balance_volume()
    except Exception:
        pass
    return df


def _detect_trend(df: pd.DataFrame) -> str:
    try:
        last = df.iloc[-1]
        sma20 = last.get("sma20")
        sma50 = last.get("sma50")
        close = last["Close"]
        if pd.isna(sma20) or pd.isna(sma50):
            return "INDEFINIDO"
        if close > sma20 > sma50:
            return "ALTA"
        if close < sma20 < sma50:
            return "BAIXA"
        return "LATERAL"
    except Exception:
        return "INDEFINIDO"


def _detect_pattern(df: pd.DataFrame) -> str:
    try:
        if len(df) < 3:
            return ""
        last  = df.iloc[-1]
        prev  = df.iloc[-2]
        prev2 = df.iloc[-3]

        macd     = last.get("macd")
        macd_sig = last.get("macd_sig")
        p_macd   = prev.get("macd")
        p_sig    = prev.get("macd_sig")

        rsi      = last.get("rsi")
        bb_pct   = last.get("bb_pct")
        sma20    = last.get("sma20")
        close    = last["Close"]

        # MACD crossover bullish
        if (not pd.isna(macd) and not pd.isna(macd_sig) and
                not pd.isna(p_macd) and not pd.isna(p_sig)):
            if p_macd < p_sig and macd > macd_sig:
                return "Cruzamento MACD Alta"
            if p_macd > p_sig and macd < macd_sig:
                return "Cruzamento MACD Baixa"

        # RSI oversold/overbought
        if not pd.isna(rsi):
            if rsi < 30:
                return "RSI Sobrevenda"
            if rsi > 70:
                return "RSI Sobrecompra"

        # Bollinger squeeze breakout
        if not pd.isna(bb_pct):
            if bb_pct < 0.05:
                return "Suporte Bollinger"
            if bb_pct > 0.95:
                return "Resistência Bollinger"

        # Golden cross / death cross
        sma50 = last.get("sma50")
        p_sma20 = prev.get("sma20")
        p_sma50 = prev.get("sma50")
        if all(not pd.isna(x) for x in [sma20, sma50, p_sma20, p_sma50]):
            if p_sma20 < p_sma50 and sma20 > sma50:
                return "Golden Cross"
            if p_sma20 > p_sma50 and sma20 < sma50:
                return "Death Cross"

        return ""
    except Exception:
        return ""


def analyze(ticker: str, current_price: float, var_day: float, volume: float) -> tuple[TechnicalData, float]:
    """
    Retorna (TechnicalData, score_tecnico 0-20).
    """
    df = _fetch_history(ticker)
    td = TechnicalData()
    score = 5.0  # base com dados mínimos (preço e variação)

    if df.empty or len(df) < 20:
        # Análise somente com dados intraday da BRAPI
        td.trend = "INDEFINIDO"
        if var_day > 2:
            score += 3
        elif var_day > 0:
            score += 1
        return td, round(score, 1)

    df = _add_indicators(df)
    last = df.iloc[-1]

    td.rsi      = _safe(last, "rsi")
    td.macd     = _safe(last, "macd")
    td.macd_sig = _safe(last, "macd_sig")
    td.bb_pos   = _safe(last, "bb_pct")
    td.sma20    = _safe(last, "sma20")
    td.sma50    = _safe(last, "sma50")
    td.atr      = _safe(last, "atr")
    td.trend    = _detect_trend(df)
    td.pattern  = _detect_pattern(df)

    score = 5.0

    # RSI (0-5)
    if td.rsi is not None:
        if td.rsi < 30:   score += 5
        elif td.rsi < 40: score += 4
        elif td.rsi < 50: score += 3
        elif td.rsi < 60: score += 2
        elif td.rsi < 70: score += 1
        else:             score += 0

    # MACD (0-5)
    if td.macd is not None and td.macd_sig is not None:
        hist = td.macd - td.macd_sig
        if td.macd > td.macd_sig and hist > 0:  score += 4
        elif td.macd > td.macd_sig:              score += 2
        elif td.macd < td.macd_sig and hist < 0: score += 0
        else:                                    score += 1

    # Trend (0-4)
    score += {"ALTA": 4, "LATERAL": 2, "BAIXA": 0, "INDEFINIDO": 1}.get(td.trend, 1)

    # Bollinger position (0-3)
    if td.bb_pos is not None:
        if td.bb_pos < 0.2:   score += 3
        elif td.bb_pos < 0.4: score += 2
        elif td.bb_pos < 0.6: score += 1
        else:                  score += 0

    # Volume spike (0-3): usar variação de OBV como proxy
    try:
        obv_vals = df["obv"].dropna()
        if len(obv_vals) >= 5:
            obv_trend = obv_vals.iloc[-1] > obv_vals.iloc[-5]
            if obv_trend and var_day > 0: score += 3
            elif obv_trend:               score += 1
    except Exception:
        pass

    return td, round(min(score, 20), 1)


def calc_stops(ticker: str, price: float, op_type: OpType) -> tuple[float, float]:
    """Retorna (stop, target) baseados no ATR."""
    df = _fetch_history(ticker)
    if df.empty:
        # fallback: stop 2%, target 4%
        stop   = round(price * 0.98, 2)
        target = round(price * 1.04, 2)
        return stop, target

    df = _add_indicators(df)
    atr = _safe(df.iloc[-1], "atr") or price * 0.02

    if op_type == OpType.DAY_TRADE:
        mult_stop   = 1.0
        mult_target = 2.0
    elif op_type == OpType.SWING:
        mult_stop   = 2.0
        mult_target = 4.0
    else:  # POSITION
        mult_stop   = 3.0
        mult_target = 6.0

    stop   = round(price - atr * mult_stop, 2)
    target = round(price + atr * mult_target, 2)
    return stop, target


def _safe(row, col: str) -> Optional[float]:
    try:
        v = row[col]
        return float(v) if not pd.isna(v) else None
    except Exception:
        return None

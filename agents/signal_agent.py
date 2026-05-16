from config.markets import AssetClass, asset_class as get_class
from models.opportunity import (
    Opportunity, SignalType, OpType, RiskLevel, ScoreBreakdown, TechnicalData
)
from agents import technical_agent as ta_agent
from agents import risk_agent
from agents.macro_agent import get_macro


def _score_fundamental(q: dict, cls: AssetClass) -> float:
    """Score fundamentalista (0-15)."""
    score = 5.0

    if cls == AssetClass.FII:
        dy = q.get("dividendYield") or 0
        if dy >= 10:    score += 5
        elif dy >= 8:   score += 4
        elif dy >= 6:   score += 3
        elif dy >= 4:   score += 1
        pl = q.get("priceEarnings") or 0
        if 0 < pl <= 15: score += 3
        elif pl <= 25:   score += 1
        return min(score, 15)

    if cls in (AssetClass.ETF, AssetClass.CRYPTO):
        return 7.5  # ETFs e cripto: score neutro

    # Ações e BDRs
    pl = q.get("priceEarnings") or 0
    if 0 < pl <= 8:     score += 5
    elif 0 < pl <= 15:  score += 4
    elif 0 < pl <= 25:  score += 2
    elif pl > 25:       score -= 1

    pvp = q.get("priceToBook") or 0
    if 0 < pvp <= 1:    score += 3
    elif 0 < pvp <= 2:  score += 2
    elif 0 < pvp <= 3:  score += 1

    dy = q.get("dividendYield") or 0
    if dy >= 8:     score += 3
    elif dy >= 5:   score += 2
    elif dy >= 3:   score += 1

    roe = q.get("returnOnEquityTTM") or 0
    if roe >= 20:   score += 4
    elif roe >= 15: score += 3
    elif roe >= 10: score += 2
    elif roe >= 5:  score += 1

    return round(min(max(score, 0), 15), 1)


def _score_macro(ticker: str) -> float:
    ctx = get_macro()
    base = ctx.macro_score()
    boost = ctx.sector_boost(ticker)
    return round(min(max(base + boost, 0), 15), 1)


def _score_timing(var_day: float, td: TechnicalData) -> float:
    """Score de timing (0-5)."""
    score = 2.0
    if var_day > 0 and td.trend == "ALTA":   score += 2
    if var_day < 0 and td.trend == "BAIXA":  score -= 1
    if td.pattern in ("Cruzamento MACD Alta", "RSI Sobrevenda", "Suporte Bollinger", "Golden Cross"):
        score += 1
    return round(min(max(score, 0), 5), 1)


def _determine_op_type(td: TechnicalData, var_day: float, volume: float) -> OpType:
    """Define se é Day Trade, Swing ou Posição."""
    has_strong_momentum = abs(var_day) > 1.5 and volume > 5_000_000
    rsi = td.rsi or 50

    if has_strong_momentum and td.trend in ("ALTA", "BAIXA"):
        return OpType.DAY_TRADE

    if (td.pattern in ("Cruzamento MACD Alta", "RSI Sobrevenda", "Golden Cross") or
            (rsi < 35 and td.trend != "BAIXA")):
        return OpType.SWING

    return OpType.POSITION


def _determine_signal(score: ScoreBreakdown, td: TechnicalData, var_day: float) -> SignalType:
    t = score.total
    rsi = td.rsi or 50
    trend = td.trend

    # Sinais de venda/stop
    if rsi > 75 and trend == "BAIXA":
        return SignalType.SELL
    if td.pattern == "Death Cross":
        return SignalType.STOP
    if var_day < -3 and trend == "BAIXA":
        return SignalType.STOP
    if rsi > 70 and var_day > 2:
        return SignalType.PARTIAL_SELL

    # Sinais de compra
    if t >= 85:  return SignalType.BUY_STRONG
    if t >= 70:  return SignalType.BUY
    if t >= 55:  return SignalType.BUY_SPEC
    if t >= 40:  return SignalType.WATCH
    return SignalType.WAIT


def build_opportunity(ticker: str, quote: dict) -> Opportunity | None:
    """Constrói uma Opportunity completa a partir da cotação da BRAPI."""
    price = quote.get("regularMarketPrice") or 0
    if not price:
        return None

    var_day   = quote.get("regularMarketChangePercent") or 0
    volume    = quote.get("regularMarketVolume") or 0
    mkt_cap   = quote.get("marketCap")
    name      = (quote.get("shortName") or quote.get("longName") or ticker)[:28]
    cls       = get_class(ticker)

    # Análise técnica
    td, tech_score = ta_agent.analyze(ticker, price, var_day, volume)

    # Op type
    op_type = _determine_op_type(td, var_day, volume)

    # Stops via ATR
    stop, target = ta_agent.calc_stops(ticker, price, op_type)
    entry = round(price, 2)
    rr    = risk_agent.calc_rr(entry, stop, target)

    # Scores
    fund_score  = _score_fundamental(quote, cls)
    macro_score = _score_macro(ticker)
    liq_score   = risk_agent.score_liquidity(volume, mkt_cap)
    rr_score    = risk_agent.score_risk_reward(rr, op_type)
    timing_score = _score_timing(var_day, td)

    score = ScoreBreakdown(
        technical   = tech_score,
        fundamental = fund_score,
        macro       = macro_score,
        sentiment   = 5.0,   # placeholder — agente de notícias (MVP 2)
        liquidity   = liq_score,
        risk_reward = rr_score,
        backtest    = 5.0,   # placeholder — agente de backtest (MVP 2)
        timing      = timing_score,
    )

    signal     = _determine_signal(score, td, var_day)
    risk_level = risk_agent.classify_risk(score, op_type)

    # Motivos principais
    reasons: list[str] = []
    risks:   list[str] = []

    if td.rsi and td.rsi < 35:
        reasons.append(f"RSI {td.rsi:.0f} — sobrevenda")
    if td.trend == "ALTA":
        reasons.append("Tendência de alta confirmada (MA20 > MA50)")
    if td.pattern:
        reasons.append(td.pattern)
    if (quote.get("priceEarnings") or 0) > 0 and (quote.get("priceEarnings") or 99) < 12:
        reasons.append(f"P/L {quote['priceEarnings']:.1f}x — valor atrativo")
    if (quote.get("dividendYield") or 0) >= 6:
        reasons.append(f"DY {quote['dividendYield']:.1f}% — renda relevante")
    if rr >= 2:
        reasons.append(f"R:R {rr:.1f}x — boa assimetria")

    if td.rsi and td.rsi > 70:
        risks.append(f"RSI {td.rsi:.0f} — sobrecomprado")
    if td.trend == "BAIXA":
        risks.append("Tendência de baixa")
    if volume < 500_000:
        risks.append("Baixa liquidez")
    macro = get_macro()
    if macro.selic and macro.selic > 13:
        risks.append(f"Selic {macro.selic:.2f}% eleva custo de capital")

    return Opportunity(
        ticker      = ticker,
        name        = name,
        asset_class = cls,
        signal      = signal,
        op_type     = op_type,
        score       = score,
        price       = price,
        entry       = entry,
        stop        = stop,
        target      = target,
        rr          = rr,
        risk_level  = risk_level,
        var_day     = var_day,
        volume      = volume,
        market_cap  = mkt_cap,
        ta          = td,
        reasons     = reasons,
        risks       = risks,
    )

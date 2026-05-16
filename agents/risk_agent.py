from models.opportunity import OpType, RiskLevel, ScoreBreakdown


MAX_RISK_PCT = {
    OpType.DAY_TRADE: 1.0,   # stop máx 1% no DT
    OpType.SWING:     2.5,   # stop máx 2.5% no swing
    OpType.POSITION:  5.0,   # stop máx 5% na posição
}

MAX_POSITION_PCT = {
    RiskLevel.CONSERVATIVE: 5.0,
    RiskLevel.MODERATE:     10.0,
    RiskLevel.AGGRESSIVE:   20.0,
}


def classify_risk(score: ScoreBreakdown, op_type: OpType) -> RiskLevel:
    t = score.total
    if t >= 75 and op_type == OpType.POSITION:
        return RiskLevel.CONSERVATIVE
    if t >= 65:
        return RiskLevel.MODERATE
    return RiskLevel.AGGRESSIVE


def calc_rr(entry: float, stop: float, target: float) -> float:
    """Calcula relação risco-retorno."""
    risk   = abs(entry - stop)
    reward = abs(target - entry)
    if risk == 0:
        return 0.0
    return round(reward / risk, 2)


def score_risk_reward(rr: float, op_type: OpType) -> float:
    """Retorna score de risco-retorno (0-15)."""
    # Mínimos aceitáveis por tipo de operação
    min_rr = {OpType.DAY_TRADE: 1.5, OpType.SWING: 2.0, OpType.POSITION: 2.5}
    floor  = min_rr.get(op_type, 2.0)

    if rr <= 0:           return 0
    if rr < floor:        return 2
    if rr < floor * 1.5:  return 7
    if rr < floor * 2:    return 11
    return 15


def suggest_position_size(capital: float, entry: float, stop: float,
                           risk_level: RiskLevel = RiskLevel.MODERATE) -> dict:
    """
    Sugere tamanho de posição baseado em gestão de risco (1-2% do capital por operação).
    """
    risk_per_share = abs(entry - stop)
    if risk_per_share == 0:
        return {"shares": 0, "capital": 0, "risk_pct": 0}

    risk_pct = 1.0 if risk_level == RiskLevel.CONSERVATIVE else (
               2.0 if risk_level == RiskLevel.MODERATE else 3.0)
    max_loss   = capital * risk_pct / 100
    shares     = int(max_loss / risk_per_share)
    shares     = (shares // 100) * 100  # lote padrão B3
    if shares == 0:
        shares = 100

    position_value = shares * entry
    max_pos = capital * MAX_POSITION_PCT[risk_level] / 100
    if position_value > max_pos:
        shares     = int((max_pos / entry) // 100) * 100

    return {
        "shares":    shares,
        "capital":   round(shares * entry, 2),
        "risk_pct":  risk_pct,
        "max_loss":  round(shares * risk_per_share, 2),
    }


def score_liquidity(volume: float, market_cap: float | None) -> float:
    """Score de liquidez (0-10)."""
    score = 0.0

    # Volume diário
    if volume >= 50_000_000:   score += 5
    elif volume >= 10_000_000: score += 4
    elif volume >= 5_000_000:  score += 3
    elif volume >= 1_000_000:  score += 2
    elif volume >= 100_000:    score += 1

    # Market cap
    if market_cap:
        if market_cap >= 100e9:  score += 5
        elif market_cap >= 20e9: score += 4
        elif market_cap >= 5e9:  score += 3
        elif market_cap >= 1e9:  score += 2
        elif market_cap >= 100e6: score += 1

    return min(score, 10)


def worst_case(entry: float, stop: float, shares: int) -> dict:
    """Calcula pior cenário razoável."""
    loss = (entry - stop) * shares
    gap_pct = 20  # gap de abertura estimado em cenário de stress
    stress_loss = entry * (gap_pct / 100) * shares
    return {
        "normal_stop_loss": round(loss, 2),
        "stress_scenario":  round(stress_loss, 2),
        "warning": "Risco real pode ser maior em gaps ou eventos extraordinários." if stress_loss > loss * 2 else None,
    }

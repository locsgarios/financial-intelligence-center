from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from config.markets import AssetClass


class SignalType(Enum):
    BUY_STRONG    = "COMPRA FORTE"
    BUY           = "COMPRA"
    BUY_SPEC      = "COMPRA ESPEC."
    WATCH         = "OBSERVAÇÃO"
    WAIT          = "AGUARDAR"
    PARTIAL_SELL  = "VENDA PARCIAL"
    SELL          = "VENDA TOTAL"
    STOP          = "STOP"
    HEDGE         = "HEDGE"

    @property
    def color(self) -> str:
        return {
            "COMPRA FORTE":   "bold green",
            "COMPRA":         "green",
            "COMPRA ESPEC.":  "cyan",
            "OBSERVAÇÃO":     "yellow",
            "AGUARDAR":       "dim",
            "VENDA PARCIAL":  "orange3",
            "VENDA TOTAL":    "red",
            "STOP":           "bold red",
            "HEDGE":          "magenta",
        }.get(self.value, "white")

    @property
    def emoji(self) -> str:
        return {
            "COMPRA FORTE":   "🟢",
            "COMPRA":         "🟢",
            "COMPRA ESPEC.":  "🔵",
            "OBSERVAÇÃO":     "🟡",
            "AGUARDAR":       "⚪",
            "VENDA PARCIAL":  "🟠",
            "VENDA TOTAL":    "🔴",
            "STOP":           "🛑",
            "HEDGE":          "🛡️",
        }.get(self.value, "⚪")


class OpType(Enum):
    DAY_TRADE   = "DT"
    SWING       = "SW"
    POSITION    = "POS"


class RiskLevel(Enum):
    CONSERVATIVE = "Conservador"
    MODERATE     = "Moderado"
    AGGRESSIVE   = "Agressivo"


@dataclass
class ScoreBreakdown:
    """Score 0-100 distribuído em 8 dimensões."""
    technical:   float = 0   # 0-20: indicadores técnicos
    fundamental: float = 0   # 0-15: fundamentos da empresa
    macro:       float = 0   # 0-15: cenário macroeconômico
    sentiment:   float = 0   # 0-10: notícias e sentimento
    liquidity:   float = 0   # 0-10: volume e liquidez
    risk_reward: float = 0   # 0-15: relação risco-retorno
    backtest:    float = 0   # 0-10: histórico estatístico
    timing:      float = 0   # 0-5:  timing do mercado

    @property
    def total(self) -> float:
        return round(sum([
            self.technical, self.fundamental, self.macro, self.sentiment,
            self.liquidity, self.risk_reward, self.backtest, self.timing
        ]), 1)

    @property
    def classification(self) -> str:
        t = self.total
        if t >= 85: return "MUITO FORTE"
        if t >= 70: return "RELEVANTE"
        if t >= 55: return "MODERADA"
        if t >= 40: return "OBSERVAÇÃO"
        return "DESCARTAR"

    @property
    def confidence(self) -> str:
        filled = sum(1 for v in [
            self.technical, self.fundamental, self.macro,
            self.liquidity, self.risk_reward
        ] if v > 0)
        if filled >= 5: return "Alto"
        if filled >= 3: return "Médio"
        return "Baixo"


@dataclass
class TechnicalData:
    rsi:        Optional[float] = None
    macd:       Optional[float] = None
    macd_sig:   Optional[float] = None
    bb_pos:     Optional[float] = None   # posição nas bollinger (0=inf, 1=sup)
    sma20:      Optional[float] = None
    sma50:      Optional[float] = None
    atr:        Optional[float] = None
    trend:      str = ""                 # ALTA / BAIXA / LATERAL
    pattern:    str = ""                 # ex: "Cruzamento MA"


@dataclass
class Opportunity:
    ticker:      str
    name:        str
    asset_class: AssetClass
    signal:      SignalType
    op_type:     OpType
    score:       ScoreBreakdown

    price:       float = 0.0
    entry:       Optional[float] = None
    stop:        Optional[float] = None
    target:      Optional[float] = None
    rr:          float = 0.0             # risk/reward ratio

    risk_level:  RiskLevel = RiskLevel.MODERATE
    var_day:     float = 0.0
    volume:      float = 0.0
    market_cap:  Optional[float] = None

    ta:          TechnicalData = field(default_factory=TechnicalData)
    reasons:     list[str] = field(default_factory=list)
    risks:       list[str] = field(default_factory=list)

    updated_at:  datetime = field(default_factory=datetime.now)
    data_delay:  str = "15min"

    @property
    def risk_pct(self) -> Optional[float]:
        if self.entry and self.stop:
            return abs(self.entry - self.stop) / self.entry * 100
        return None

    @property
    def gain_pct(self) -> Optional[float]:
        if self.entry and self.target:
            return abs(self.target - self.entry) / self.entry * 100
        return None

from enum import Enum


class AssetClass(Enum):
    STOCK = "Ação"
    FII = "FII"
    ETF = "ETF"
    BDR = "BDR"
    CRYPTO = "Cripto"
    INDEX = "Índice"


# ─── AÇÕES (Ibovespa + IBRX-100 + líquidas) ────────────────────────────────
STOCKS = [
    "PETR4","PETR3","VALE3","ITUB4","ITUB3","BBDC4","BBDC3","ABEV3","WEGE3",
    "RENT3","LREN3","RADL3","JBSS3","SUZB3","GGBR4","USIM5","CSNA3","BPAC11",
    "BBAS3","SANB11","BRFS3","MRFG3","BEEF3","SMTO3","SLCE3","AGRO3","EMBR3",
    "AZUL4","GOLL4","CSAN3","UGPA3","VBBR3","PRIO3","RECV3","RRRP3","CYRE3",
    "EZTC3","MRVE3","EVEN3","JHSF3","MULT3","KLBN11","DXCO3","RANI3","FLRY3",
    "HAPV3","RDOR3","QUAL3","HYPE3","PNVL3","DASA3","AALR3","ODPV3","LWSA3",
    "TOTS3","SEER3","COGN3","YDUQ3","ANIM3","VITT3","PETZ3","NTCO3","SOMA3",
    "AZZA3","GRND3","ALPA4","VULC3","GUAR3","CPLE6","EGIE3","CPFE3","ELET3",
    "ELET6","CMIG4","TAEE11","TRPL4","AURE3","ENEV3","TIMS3","VIVT3","BRSR6",
    "BPAN4","ITSA4","ITSA3","BBSE3","IRBR3","PSSA3","BRAP4","GOAU4","MILS3",
    "SBSP3","SAPR11","CSMG3","ECOR3","CCRO3","STBP3","LOGN3","RAIL3","MGLU3",
    "VIVA3","CASH3","DESK3","OIBR3","PINE4","CGRA4","MOAR3","TTEN3","SMFT3",
]

# ─── FIIs (Fundos de Investimento Imobiliário) ───────────────────────────────
FIIS = [
    "HGLG11","KNRI11","XPML11","VISC11","IRDM11","BTLG11","MXRF11","HGRE11",
    "RBRF11","CPTS11","RZTR11","RBRR11","KNCR11","BCFF11","XPCI11","RECT11",
    "TRXF11","HGCR11","VGIP11","FIIB11","HSML11","BRCO11","LVBI11","MALL11",
    "MGFF11","BRCR11","FVPQ11","VINO11","VRTA11","RCRB11","TGAR11","HFOF11",
    "PVBI11","RBLC11","TEPP11","JSRE11","BPML11","CSHG11","RBVA11","URPR11",
    "GGRC11","GTWR11","AFHI11","HGBS11","PATL11","TSNC11","VGHF11","DEVA11",
]

# ─── ETFs ────────────────────────────────────────────────────────────────────
ETFS = [
    "BOVA11","SMAL11","IVVB11","HASH11","SPXI11","GOLD11","MATB11","FIND11",
    "UTIL11","DIVO11","ECOO11","GOVE11","ISUS11","NFNC11","BBSD11","XINA11",
    "ACWI11","BNDX11","EURP11","NASD11","BOVV11","CSMO11",
]

# ─── BDRs (recibos de ações estrangeiras) ────────────────────────────────────
BDRS = [
    "AAPL34","MSFT34","AMZN34","GOOGL34","META34","TSLA34","NVDC34","NFLX34",
    "DISB34","BERK34","JPMC34","BABA34","VISA34","JNJ34","WMT34","V3OC34",
    "PYPL34","ADBE34","CRM034","INTC34","AMD34","COIN34","UBER34","LYFT34",
]

# ─── Cripto (via yfinance) ───────────────────────────────────────────────────
CRYPTO = [
    "BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD","ADA-USD","AVAX-USD",
]

# ─── yfinance suffix por classe ──────────────────────────────────────────────
YF_SUFFIX = {
    AssetClass.STOCK:  ".SA",
    AssetClass.FII:    ".SA",
    AssetClass.ETF:    ".SA",
    AssetClass.BDR:    ".SA",
    AssetClass.CRYPTO: "",     # já vem com -USD
    AssetClass.INDEX:  ".SA",
}

# mapa ticker → classe
ASSET_CLASS_MAP: dict[str, AssetClass] = {}
for t in STOCKS:  ASSET_CLASS_MAP[t] = AssetClass.STOCK
for t in FIIS:    ASSET_CLASS_MAP[t] = AssetClass.FII
for t in ETFS:    ASSET_CLASS_MAP[t] = AssetClass.ETF
for t in BDRS:    ASSET_CLASS_MAP[t] = AssetClass.BDR
for t in CRYPTO:  ASSET_CLASS_MAP[t] = AssetClass.CRYPTO

ALL_TICKERS: list[str] = STOCKS + FIIS + ETFS + BDRS + CRYPTO


def yf_symbol(ticker: str) -> str:
    """Converte ticker B3 para símbolo yfinance."""
    cls = ASSET_CLASS_MAP.get(ticker, AssetClass.STOCK)
    suffix = YF_SUFFIX.get(cls, ".SA")
    return f"{ticker}{suffix}"


def asset_class(ticker: str) -> AssetClass:
    return ASSET_CLASS_MAP.get(ticker, AssetClass.STOCK)

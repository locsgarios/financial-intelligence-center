import os
import threading
import time
import requests

_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
_sent: set = set()
_lock = threading.Lock()
_last_reset = time.time()

def _refresh_env():
    global _TOKEN, _CHAT_ID
    _TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', _TOKEN)
    _CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', _CHAT_ID)

def _reset_if_new_day():
    global _last_reset
    now = time.time()
    if now - _last_reset > 86400:
        with _lock:
            _sent.clear()
            _last_reset = now

def send_alert(opp) -> bool:
    """Envia alerta de oportunidade no Telegram. Deduplicado por ticker+sinal."""
    _refresh_env()
    _reset_if_new_day()
    if not _TOKEN or not _CHAT_ID:
        return False

    signal_name = opp.signal.value if hasattr(opp.signal, 'value') else str(opp.signal)
    key = opp.ticker + '_' + signal_name
    with _lock:
        if key in _sent:
            return False
        _sent.add(key)

    sc = opp.score.total
    if 'COMPRA' in signal_name.upper():
        emoji = chr(0x1F7E2)
    elif any(x in signal_name.upper() for x in ('VENDA', 'STOP')):
        emoji = chr(0x1F534)
    else:
        emoji = chr(0x1F7E1)
    bar = chr(0x2588) * int(sc // 10) + chr(0x2591) * (10 - int(sc // 10))

    text = (
        '*⚡ Financial Intelligence Center*\n\n'
        + emoji + ' *' + opp.ticker + '* \u2014 ' + signal_name + '\n'
        + 'Score: *' + str(int(sc)) + '/100*  ' + bar + '\n\n'
        + '\U0001f4b0 Pre\u00e7o:   R$' + '{:.2f}'.format(opp.price) + '\n'
        + '\U0001f3af Entrada: R$' + '{:.2f}'.format(opp.entry) + '\n'
        + '\U0001f6d1 Stop:    R$' + '{:.2f}'.format(opp.stop) + '\n'
        + '\U0001f3c6 Alvo:    R$' + '{:.2f}'.format(opp.target) + '\n'
        + '\u2696\ufe0f  R\\:R:    ' + '{:.1f}x'.format(opp.rr) + '\n'
    )
    if opp.ta and opp.ta.rsi:
        text += '\U0001f4ca RSI:     ' + '{:.0f}'.format(opp.ta.rsi) + '\n'
    if opp.ta and opp.ta.trend:
        text += '\U0001f4c8 Trend:   ' + opp.ta.trend + '\n'
    if opp.reasons:
        text += '\n*Motivos:*\n' + '\n'.join('\u2705 ' + r for r in opp.reasons[:3])
    if opp.risks:
        text += '\n*Riscos:*\n' + '\n'.join('\u26a0\ufe0f ' + r for r in opp.risks[:2])

    try:
        r = requests.post(
            'https://api.telegram.org/bot' + _TOKEN + '/sendMessage',
            json={'chat_id': _CHAT_ID, 'text': text, 'parse_mode': 'Markdown'},
            timeout=8,
        )
        return r.status_code == 200
    except Exception:
        return False

def send_message(text: str) -> bool:
    """Envia mensagem simples no Telegram."""
    _refresh_env()
    if not _TOKEN or not _CHAT_ID:
        return False
    try:
        r = requests.post(
            'https://api.telegram.org/bot' + _TOKEN + '/sendMessage',
            json={'chat_id': _CHAT_ID, 'text': text, 'parse_mode': 'Markdown'},
            timeout=8,
        )
        return r.status_code == 200
    except Exception:
        return False

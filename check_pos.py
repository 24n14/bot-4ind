import config
from log import logger

symbol = config.SYMBOL


def _fetch_last_pnl(exchange, symbol):
    """Запрашивает P&L последней закрытой позиции"""
    try:
        # Bybit: fetch_closed_orders или fetch_my_trades
        trades = exchange.fetch_my_trades(symbol, limit=1)
        if trades:
            pnl = trades[-1].get('info', {}).get('closedPnl') or trades[-1].get('info', {}).get('realizedPnl')
            return float(pnl) if pnl is not None else None
    except Exception as e:
        logger.warning(f"⚠️  Не удалось получить P&L: {e}")
    return None
'''
#запасной вариант
def _fetch_last_pnl(exchange, symbol):
    """Запрашивает P&L последней закрытой позиции через Bybit"""
    try:
        # Bybit: closed P&L через приватный endpoint
        response = exchange.private_get_v5_position_closed_pnl({
            'category': 'linear',
            'symbol': symbol.replace('/', '').replace(':USDT', ''),
            'limit': 1
        })
        items = response.get('result', {}).get('list', [])
        if items:
            pnl = items[0].get('closedPnl')
            return float(pnl) if pnl is not None else None
    except Exception as e:
        logger.warning(f"⚠️  Не удалось получить P&L: {e}")
    return None

'''

def _fetch_balance(exchange):
    """Запрашивает актуальный баланс"""
    try:
        balance = exchange.fetch_balance()
        usdt = balance.get('USDT', {}).get('total') or balance.get('total', {}).get('USDT')
        return float(usdt) if usdt is not None else None
    except Exception as e:
        logger.warning(f"⚠️  Не удалось получить баланс: {e}")
    return None


def has_open_position(exchange, symbol):
    """
    Проверяет открытую позицию (для Bybit).

    - Если позиция открыта  → возвращает (True, pos)
    - Если позиции нет      → логирует P&L + баланс, возвращает (False, None)
    """
    uid = getattr(config, 'UID', 'N/A')

    try:
        logger.info(f"🔍 [{uid}] Проверка позиции для {symbol}...")
        positions = exchange.fetch_positions()

        for pos in positions:
            if pos['symbol'] == symbol:
                if pos.get('contracts') and pos['contracts'] != 0:
                    logger.info(
                        f"✅ [{uid}] Открыта {pos['side'].upper()} | "
                        f"Контракты: {pos['contracts']} | "
                        f"Символ: {symbol}"
                    )
                    return True, pos

        # ── Позиция не найдена ─────────────────────────────

        else:
            logger.info(f"📭 [{uid}] Открытых позиций по {symbol} нет")
            pnl = _fetch_last_pnl(exchange, symbol)
            if pnl is not None:
                icon = "🟢" if pnl >= 0 else "🔴"
                logger.info(f"{icon} [{uid}] P&L последней позиции: {pnl:+.4f} USDT")
            else:
                logger.info(f"📊 [{uid}] P&L последней позиции: нет данных")

            # Актуальный баланс
            balance = _fetch_balance(exchange)
            if balance is not None:
                logger.info(f"💰 [{uid}] Баланс: {balance:.2f} USDT")
            else:
                logger.info(f"💰 [{uid}] Баланс: нет данных")

            return False, None

    except Exception as e:
        logger.error(f"❌ [{uid}] Ошибка при проверке позиции: {e}")
        return False, None

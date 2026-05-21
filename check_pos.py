import config
from log import logger

symbol = config.SYMBOL

def _fetch_account_realized_pnl(exchange, symbol: str | None = None) -> float | None:
    #logger.info("[DEBUG] Вход в _fetch_account_realized_pnl")
    """
    Возвращает суммарный Realized PnL аккаунта (как его считает Bybit).
    Если передан symbol — берём только по этому инструменту.
    """
    try:
        # ccxt: для Bybit деривативов здесь придут позиции с сырыми полями из v5
        positions = exchange.fetch_positions([symbol]) if symbol else exchange.fetch_positions()

        total_pnl = 0.0
        found = False

        for pos in positions:
            info = pos.get('info', {}) or {}
            #logger.debug(f"info позиции: {info}")

            # Bybit v5:
            #  - cumRealisedPnl — кумулятивный реализованный PnL по позиции
            #  - curRealisedPnl — реализованный PnL по текущему холду
            pnl_str = (
                info.get('cumRealisedPnl')
                #or info.get('curRealisedPnl')
                #or info.get('realisedPnl')   # на всякий случай разные варианты написания
                #or info.get('realizedPnl')
            )

            if pnl_str is None:
                continue

            try:
                total_pnl += float(pnl_str)
                found = True
            except (TypeError, ValueError):
                continue

        return total_pnl if found else None

    except Exception as e:
        logger.warning(f"⚠️ Не удалось получить Realized PnL аккаунта: {e}")
        return None

'''
def _fetch_last_pnl(exchange, symbol):
    """Realized PnL по последней закрытой сделке/позиции по symbol."""
    try:
        trades = exchange.fetch_my_trades(symbol, limit=1)
        if not trades:
            return None

        info = trades[-1].get('info', {}) or {}
        #logger.debug(f"info последней сделки: {info}")

        pnl_str = (
                info.get('closedPnl')
                or info.get('realisedPnl')
                or info.get('realizedPnl')
                or info.get('trade_profit')
        )

        return float(pnl_str) if pnl_str is not None else None

    except Exception as e:
        logger.warning(f"⚠️ Не удалось получить Realized PnL последней сделки: {e}")
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
        logger.info(f"🔍 {uid} Проверка позиции для {symbol}...")
        positions = exchange.fetch_positions()

        for pos in positions:
            if pos['symbol'] == symbol:
                if pos.get('contracts') and pos['contracts'] != 0:
                    logger.info(
                        f"✅ {uid} Открыта {pos['side'].upper()} | "
                        f"Контракты: {pos['contracts']} | "
                        f"Символ: {symbol}"
                    )
                    return True, pos

        # ── Позиция не найдена ─────────────────────────────

        else:
            logger.info(f"📭 [{uid}] Открытых позиций по {symbol} нет")
            #pnl = _fetch_last_pnl(exchange, symbol)
            realized_pnl = _fetch_account_realized_pnl(exchange, symbol)
            '''
            if pnl is not None:
                icon = "🟢" if pnl >= 0 else "🔴"
                logger.info(f"{icon} [{uid}] P&L последней позиции: {pnl:+.4f} USDT")
            else:
                logger.info(f"📊 [{uid}] P&L последней позиции: нет данных")
            '''
            if realized_pnl is not None:
                icon = "💰 🟢" if realized_pnl >= 0 else "💰 🔴"
                logger.info(f"{icon} {uid} ОБЩИЙ REALIZED_PNL: {realized_pnl:+.4f} USDT")
            else:
                logger.info(f"📊 {uid} ОБЩИЙ REALIZED_PNL: нет данных")

            # Актуальный баланс
            balance = _fetch_balance(exchange)
            if balance is not None:
                logger.info(f"💰 {uid} Баланс: {balance:.2f} USDT")
            else:
                logger.info(f"💰 {uid} Баланс: нет данных")

            return False, None

    except Exception as e:
        logger.error(f"❌ {uid} Ошибка при проверке позиции: {e}")
        return False, None

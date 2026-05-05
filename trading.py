import config
import pandas as pd
import time
import numpy as np
from wait_candle_close import wait_for_candle_close
from indicators import get_indicator_analysis
from open_pos import execute_trade
from check_pos import has_open_position
from log import logger
from level_determinator import find_support_resistance_levels
from position_filter import is_near_historical_high, is_near_historical_low


symbol = config.SYMBOL
amount = config.AMOUNT

def main_trading_loop(exchange):
    logger.info("🚀 Запуск торгового бота")

    # Параметры фильтрации сигналов
    MIN_CONFIDENCE = 0.5  # минимальная уверенность для входа

    try:
        while True:
            try:
                # 1. Ждём закрытия текущей свечи
                wait_success = wait_for_candle_close(exchange, config.SYMBOL, config.TIMEFRAME)
                if not wait_success:
                    logger.warning("⚠️ Ошибка синхронизации свечи, пропускаем итерацию")
                    time.sleep(5)
                    continue

                # 2. Получаем данные (свеча уже закрыта)
                #logger.debug("📥 Загружаем OHLCV данные...")
                candles = exchange.fetch_ohlcv(
                    config.SYMBOL,
                    config.TIMEFRAME,
                    limit=config.LIMIT
                )

                if not candles or len(candles) < 100:
                    logger.warning(f"⚠️ Недостаточно свечей: {len(candles) if candles else 0}")
                    time.sleep(1)
                    continue

                # 3. Создаём DataFrame
                data = pd.DataFrame(
                    candles,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )

                # 4. Конвертируем в numpy массивы
                high = data['high'].values
                low = data['low'].values
                close = data['close'].values
                volume = data['volume'].values

                # 5. Проверяем на NaN
                if np.any(np.isnan(close)) or np.any(np.isnan(volume)):
                    logger.warning("⚠️ Обнаружены NaN значения в данных")
                    time.sleep(1)
                    continue

                levels_data = find_support_resistance_levels(data, n_clusters=6, lookback=200)
                logger.debug(f"📊 Данные загружены: {len(close)} свечей, последняя цена: {close[-1]:.2f}")

                # 6. Генерируем сигнал
                consensus_signal, details, is_absolute = get_indicator_analysis(high, low, close, volume)
                # 7. Проверяем наличие позиций
                has_pos, pos_data = has_open_position(exchange, config.SYMBOL)
                signal = consensus_signal
                # ── НАДЗИРАЮЩИЙ ФИЛЬТР ────────────────────────────────────────────────
                current_price = float(close[-1])

                long_check = is_near_historical_high(current_price, data, levels_data)
                short_check = is_near_historical_low(current_price, data, levels_data)

                long_allowed = not long_check['blocked']
                short_allowed = not short_check['blocked']

                # Выводим сообщения только если есть сигналы и они заблокированы
                if signal == 'bullish' and long_check['blocked']:
                    logger.warning(f"🚫 LONG заблокирован: {long_check['reason']}")
                if signal == 'bearish' and short_check['blocked']:
                    logger.warning(f"🚫 SHORT заблокирован: {short_check['reason']}")
                # ─────────────────────────────────────────────────────────────────────
                # 8. Логика входа с учётом confidence
                if not has_pos:
                    if signal is not None:
                        logger.info(f"📊 Сигнал: {signal.upper()}")
                        if signal == 'bullish' and long_allowed:
                            logger.info(f"🟢 ВХОД В LONG")
                            execute_trade(exchange, symbol, 'buy')
                        elif signal == 'bearish' and short_allowed:
                            logger.info(f"🔴 ВХОД В SHORT")
                            execute_trade(exchange, symbol, 'sell')
                        elif signal in ('bullish', 'bearish'):
                            logger.info(f"🛑 Сигнал {signal.upper()} отклонён фильтром уровней")
                        else:
                            logger.info(f"⚠️ HOLD")
                    else:
                        logger.debug("📭 Сигнала нет")

                elif has_pos:
                    if is_absolute:
                        if (signal == 'bearish' and pos_data['side'] == 'long') or \
                                (signal == 'bullish' and pos_data['side'] == 'short'):
                            logger.info(f"🔄 Обнаружен сигнал разворота")
                            if signal == 'bullish' and long_allowed:
                                logger.info(f"🟢 РАЗВОРОТ В LONG")
                                execute_trade(exchange, symbol, 'buy')
                                execute_trade(exchange, symbol, 'buy')
                            elif signal == 'bearish' and short_allowed:
                                logger.info(f"🔴 РАЗВОРОТ В SHORT")
                                execute_trade(exchange, symbol, 'sell')
                                execute_trade(exchange, symbol, 'sell')
                            else:
                                logger.warning(f"🛑 Разворот отклонён фильтром уровней")
                    else:
                        logger.debug(f"⌛ Позиция открыта ({pos_data['side'].upper()}), ожидаем...")
                '''
                # 8. Логика входа с учётом confidence
                if not has_pos:
                    if signal is not None:
                        logger.info(f"📊 Сигнал: {signal.upper()}")
                        if signal == 'bullish':
                            logger.info(f"🟢 ВХОД В LONG")
                            execute_trade(exchange, symbol, 'buy')
                        elif signal == 'bearish':
                            logger.info(f"🔴 ВХОД В SHORT")
                            execute_trade(exchange, symbol, 'sell')
                        else:
                            logger.info(f"⚠️HOLD")
                    else:
                        logger.debug("📭 Сигнала нет")

                elif has_pos:
                    if is_absolute:
                        # Разворот позиции
                        if (signal == 'bearish' and pos_data['side'] == 'long') or \
                                (signal == 'bullish' and pos_data['side'] == 'short'):
                            logger.info(f"🔄 Обнаружен сигнал разворота")
                            if signal == 'bullish':
                                logger.info(f"🟢 ВХОД В LONG")
                                execute_trade(exchange, symbol, 'buy')
                                execute_trade(exchange, symbol, 'buy')
                            elif signal == 'bearish':
                                logger.info(f"🔴 ВХОД В SHORT")
                                execute_trade(exchange, symbol, 'sell')
                                execute_trade(exchange, symbol, 'sell')
                            # Здесь логика закрытия и открытия противоположной позиции
                    else:
                        logger.debug(f"⌛ Позиция открыта ({pos_data['side'].upper()}), ожидаем...")
                '''
                # Небольшая пауза перед следующим циклом
                time.sleep(5)

            except KeyboardInterrupt:
                raise  # Пробрасываем наружу для обработки
            except Exception as e:
                logger.error(f"❌ Ошибка в торговом цикле: {e}", exc_info=True)
                time.sleep(10)

    except KeyboardInterrupt:
        logger.info("⏹️ ПОЛУЧЕНА КОМАНДА ВЫКЛЮЧЕНИЯ (Ctrl+C)")
        logger.info("👋 Бот выключается...")
        return

    except Exception as e:
        logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        raise
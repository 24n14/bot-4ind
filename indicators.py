import config
import pandas as pd
from config import INDICATOR_WEIGHTS
from log import logger
from strategy.ma_crossover import _get_ma_crossover_signal
from strategy.macd import _get_macd_signal
from strategy.stochastic import _get_stochastic_signal
from strategy.obv import _get_obv_signal
from strategy.position_filter import is_near_historical_high,  is_near_historical_low
# переменные MACD
fastperiod = config.FAST_macd
slowperiod = config.SLOW_macd
signalperiod = config.SIGNAL_macd
# переменные STOCHASTIK
fastk_period = config.FASTK
slowk_period = config.SLOWK
slowd_period = config.SLOWD


def calculate_indicator_signals(high, low, close, volume, levels_data):
    signals = {}
    try:
        # Индикатор #1: MA1/EMA Crossover
        signals['ma_crossover'] = _get_ma_crossover_signal(close)
    except Exception as e:
        logger.warning(f"Ошибка при расчете MA crossover: {e}")
        signals['ma_crossover'] = None
    try:
        # Индикатор #2: MACD
        signals['macd'] = _get_macd_signal(close)
    except Exception as e:
        logger.warning(f"Ошибка при расчете MACD: {e}")
        signals['macd'] = None
    try:
        # Индикатор #3: Stochastic
        signals['stochastic'] = _get_stochastic_signal(high, low, close)
    except Exception as e:
        logger.warning(f"Ошибка при расчете Stochastic: {e}")
        signals['stochastic'] = None
    try:
        # Индикатор #4: OBV Trend
        signals['obv'] = _get_obv_signal(close, volume)
    except Exception as e:
        logger.warning(f"Ошибка при расчете OBV: {e}")
        signals['obv'] = None
    try:
        # Проверка на исторический максимум
        current_price = close[-1]
        long_filter = is_near_historical_high(current_price, pd.DataFrame({'high': high, 'low': low, 'close': close}),
                                              levels_data)
        short_filter = is_near_historical_low(current_price, pd.DataFrame({'high': high, 'low': low, 'close': close}),
                                              levels_data)

        if long_filter['blocked']:
            signals['position_filter'] = 'bearish'
        elif short_filter['blocked']:
            signals['position_filter'] = 'bullish'
        else:
            signals['position_filter'] = 'hold'  # или None
    except Exception as e:
        logger.warning(f"Ошибка при расчете position_filter: {e}")
        signals['position_filter'] = None

    return signals

def calculate_consensus_signal(signals):
    """
    Рассчитывает консенсус-сигнал на основе взвешенного голосования.
    Args:
        signals (dict): Результат calculate_indicator_signals()
    Returns:
        tuple: (consensus_signal, details)
            consensus_signal: 'bullish', 'bearish', или 'hold'
            details: dict с детальной информацией о голосовании
    """
    MIN_CONSENSUS_WEIGHT = config.MIN_CONSENSUS_WEIGHT  # Минимум 3 индикатора для сигнала
    MIN_PARTICIPATION = config.MIN_PARTICIPATION  # Минимум 4 индикатора должны работать

    # Инициализируем счетчики
    bullish_weight = 0.0
    bearish_weight = 0.0
    active_indicators = 0  # Счетчик работающих индикаторов (не None)
    details = {
        'votes': {},
        'weights_used': INDICATOR_WEIGHTS.copy(),
        'bullish_total': 0.0,
        'bearish_total': 0.0,
        'consensus': None
    }

    # Обходим каждый индикатор
    for indicator_name, signal in signals.items():
        weight = INDICATOR_WEIGHTS.get(indicator_name, 1.0)

        details['votes'][indicator_name] = {
            'signal': signal,
            'weight': weight
        }
        # None = индикатор не работает, пропускаем
        if signal is None:
            logger.warning(f"⚠️ {indicator_name}: None (индикатор не активен)")
            continue
        # Индикатор работает
        active_indicators += 1

        if signal == 'bullish':
            bullish_weight += weight
        elif signal == 'bearish':
            bearish_weight += weight

    details['bullish_total'] = bullish_weight
    details['bearish_total'] = bearish_weight

    # Логируем голосование
    logger.info(f"📊 Консенсус-голосование:")
    for ind_name, vote_info in details['votes'].items():
        logger.info(f"📣 {ind_name}: {vote_info['signal']} (вес:{vote_info['weight']})")
    logger.info(f"BULLISH сумма: {bullish_weight}|BEARISH сумма:{bearish_weight}")
    logger.info(f"📊 Активных индикаторов: {active_indicators}")

    # Проверяем, достаточно ли индикаторов работает
    if active_indicators < MIN_PARTICIPATION:
        consensus_signal = 'hold'
        logger.info(f"⏸️  HOLD консенсус (недостаточно активных индикаторов: {active_indicators} < {MIN_PARTICIPATION})")

    elif bullish_weight > bearish_weight and bullish_weight >= MIN_CONSENSUS_WEIGHT:
        consensus_signal = 'bullish'
        if bullish_weight == 5:
            logger.info(f"🔥 ABSOLUTE BULLISH CONSENSUS !!!")
        else:
            logger.info(f"📊📈 BULLISH консенсус ({bullish_weight} vs {bearish_weight})")

    elif bearish_weight > bullish_weight and bearish_weight >= MIN_CONSENSUS_WEIGHT:
        consensus_signal = 'bearish'
        if bearish_weight == 5:
            logger.info(f"🔥 ABSOLUTE BEARISH CONSENSUS !!!")
        else:
            logger.info(f"📊📉 BEARISH консенсус ({bearish_weight} vs {bullish_weight})")

    else:
        consensus_signal = 'hold'
        logger.info(f"⏸️  HOLD консенсус | B={bullish_weight} S={bearish_weight} | Мин.порог={MIN_CONSENSUS_WEIGHT}")

    is_absolute = (bullish_weight == 5) or (bearish_weight == 5)
    details['consensus'] = consensus_signal  # ← теперь всегда определена
    return consensus_signal, details, is_absolute


def get_indicator_analysis(high, low, close, volume, levels_data):

    # Получаем сигналы от всех индикаторов
    signals = calculate_indicator_signals(high, low, close, volume, levels_data)

    # Рассчитываем консенсус-сигнал
    consensus_signal, details, is_absolute = calculate_consensus_signal(signals)

    return consensus_signal, details, is_absolute

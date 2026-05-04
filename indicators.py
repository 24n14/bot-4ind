import numpy as np
import talib
#import logging

import config
from config import INDICATOR_WEIGHTS
from log import logger
#logger = logging.getLogger(__name__)
# переменные MACD
fastperiod = config.FAST_macd
slowperiod = config.SLOW_macd
signalperiod = config.SIGNAL_macd
# переменные STOCHASTIK
fastk_period=config.FASTK
slowk_period=config.SLOWK
slowd_period=config.SLOWD
def calculate_indicator_signals(high, low, close, volume):

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

    return signals


def _get_ma_crossover_signal(close):
    if len(close) < config.EMA:
        return None

    ma = talib.SMA(close, timeperiod=config.MA)
    ema = talib.EMA(close, timeperiod=config.EMA)

    current_ma = ma[-1]
    current_ema = ema[-1]

    if np.isnan(current_ma) or np.isnan(current_ema):
        return None

    if current_ma > current_ema:
        return 'bullish'
    elif current_ma < current_ema:
        return 'bearish'
    else:
        return 'hold'


def _get_macd_signal(close):
    """
    Индикатор #2: MACD

    Бычий сигнал: MACD пересекает сигнальную линию снизу вверх
    Медвежий сигнал: MACD пересекает сигнальную линию сверху вниз
    """
    if len(close) < 26:
        return None

    macd, signal_line, histogram = talib.MACD(close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)

    # Берем последние 2 значения
    current_macd = macd[-1]
    current_signal = signal_line[-1]
    prev_macd = macd[-2]
    prev_signal = signal_line[-2]

    # Проверяем пересечение
    if np.isnan(current_macd) or np.isnan(current_signal) or \
            np.isnan(prev_macd) or np.isnan(prev_signal):
        return None

    # MACD было ниже сигнальной линии, теперь выше → BULLISH
    if prev_macd <= prev_signal and current_macd > current_signal:
        return 'bullish'

    # MACD было выше сигнальной линии, теперь ниже → BEARISH
    elif prev_macd >= prev_signal and current_macd < current_signal:
        return 'bearish'

    return 'hold'


def _get_stochastic_signal(high, low, close):
    """
    Индикатор #3: Stochastic Oscillator

    Бычий сигнал: %K пересекает %D снизу вверх в зоне перепродажи (<20)
    Медвежий сигнал: %K пересекает %D сверху вниз в зоне перекупленности (>80)
    """
    if len(close) < 14:
        return None

    slowk, slowd = talib.STOCH(high, low, close, fastk_period=fastk_period, slowk_period=slowk_period, slowd_period=slowd_period)

    # Берем последние 2 значения
    current_k = slowk[-1]
    current_d = slowd[-1]
    prev_k = slowk[-2]
    prev_d = slowd[-2]

    if np.isnan(current_k) or np.isnan(current_d) or \
            np.isnan(prev_k) or np.isnan(prev_d):
        return None

    # %K пересекает %D снизу вверх в зоне перепродажи → BULLISH
    if prev_k <= prev_d and current_k > current_d and current_k < 20:
        return 'bullish'

    # %K пересекает %D сверху вниз в зоне перекупленности → BEARISH
    elif prev_k >= prev_d and current_k < current_d and current_k > 80:
        return 'bearish'

    return 'hold'


def _get_obv_signal(close, volume):
    """
    Индикатор #4: OBV Trend

    Бычий сигнал: OBV растет
    Медвежий сигнал: OBV падает
    """
    if len(close) < 10:
        return None

    obv = talib.OBV(close, volume)

    # Сглаживаем OBV для более стабильного сигнала
    obv_sma = talib.SMA(obv, timeperiod=config.SMA_obv)

    # Берем последние 2 значения
    current_obv = obv_sma[-1]
    prev_obv = obv_sma[-2]

    if np.isnan(current_obv) or np.isnan(prev_obv):
        return None

    # OBV растет → BULLISH
    if current_obv > prev_obv:
        return 'bullish'

    # OBV падает → BEARISH
    elif current_obv < prev_obv:
        return 'bearish'

    return 'hold'


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
    MIN_CONSENSUS_WEIGHT = config.MIN_CONSENSUS_WEIGHT  # Минимум 2 индикатора для сигнала
    MIN_PARTICIPATION = config.MIN_PARTICIPATION  # Минимум 3 индикатора должны работать

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
    logger.info(f"Консенсус-голосование:")
    for ind_name, vote_info in details['votes'].items():
        logger.info(f"  {ind_name}: {vote_info['signal']} (вес: {vote_info['weight']})")
    logger.info(f"  BULLISH сумма: {bullish_weight} | BEARISH сумма: {bearish_weight}")
    logger.info(f"  Активных индикаторов: {active_indicators}")

    # Проверяем, достаточно ли индикаторов работает
    if active_indicators < MIN_PARTICIPATION:
        consensus_signal = 'hold'
        logger.info(f"⏸️  HOLD консенсус (недостаточно активных индикаторов: {active_indicators} < {MIN_PARTICIPATION})")

    elif bullish_weight > bearish_weight and bullish_weight >= MIN_CONSENSUS_WEIGHT:
        consensus_signal = 'bullish'
        if bullish_weight == 4:
            logger.info(f"🔥 ABSOLUTE BULLISH CONSENSUS !!!")
        else:
            logger.info(f"✅ BULLISH консенсус ({bullish_weight} vs {bearish_weight})")

    elif bearish_weight > bullish_weight and bearish_weight >= MIN_CONSENSUS_WEIGHT:
        consensus_signal = 'bearish'
        if bearish_weight == 4:
            logger.info(f"🔥 ABSOLUTE BEARISH CONSENSUS !!!")
        else:
            logger.info(f"❌ BEARISH консенсус ({bearish_weight} vs {bullish_weight})")

    else:
        consensus_signal = 'hold'
        logger.info(f"⏸️  HOLD консенсус | B={bullish_weight} S={bearish_weight} | Мин.порог={MIN_CONSENSUS_WEIGHT}")

    is_absolute = (bullish_weight == 4) or (bearish_weight == 4)
    details['consensus'] = consensus_signal  # ← теперь всегда определена
    return consensus_signal, details, is_absolute


def get_indicator_analysis(high, low, close, volume):

    # Получаем сигналы от всех индикаторов
    signals = calculate_indicator_signals(high, low, close, volume)

    # Рассчитываем консенсус-сигнал
    consensus_signal, details, is_absolute = calculate_consensus_signal(signals)

    return consensus_signal, details, is_absolute

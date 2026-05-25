import numpy as np
import talib
import config

def _get_ma_crossover_signal(close, lookback=50):
    """
    MA/EMA Crossover с анализом тренда за последние N свечей
    """
    min_required = max(config.EMA, config.MA, lookback)
    if len(close) < min_required:
        return None

    ma = talib.SMA(close, timeperiod=config.MA)
    ema = talib.EMA(close, timeperiod=config.EMA)

    # Последние значения
    current_ma = ma[-1]
    current_ema = ema[-1]

    if np.isnan(current_ma) or np.isnan(current_ema):
        return None

    # Берём последние lookback значений
    ma_slice = ma[-lookback:]
    ema_slice = ema[-lookback:]

    # Считаем, сколько раз MA была выше EMA
    above_count = np.sum(ma_slice > ema_slice)
    below_count = np.sum(ma_slice < ema_slice)

    # Определяем направление тренда MA и EMA
    ma_trend = np.sign(ma_slice[-1] - ma_slice[0])
    ema_trend = np.sign(ema_slice[-1] - ema_slice[0])

    # Основная логика сигнала
    if current_ma > current_ema:
        if above_count > lookback * 0.7 and ma_trend >= 0:
            return 'bullish'
        elif above_count > lookback * 0.5:
            return 'bullish'
        else:
            return 'hold'
    elif current_ma < current_ema:
        if below_count > lookback * 0.7 and ema_trend <= 0:
            return 'bearish'
        elif below_count > lookback * 0.5:
            return 'bearish'
        else:
            return 'hold'
    else:
        return 'hold'

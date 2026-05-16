import numpy as np
import talib
import config
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
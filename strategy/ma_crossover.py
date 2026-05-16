import numpy as np
import talib
import config
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
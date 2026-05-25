import numpy as np
import talib
import config

fastperiod = config.FAST_macd
slowperiod = config.SLOW_macd
signalperiod = config.SIGNAL_macd

def _get_macd_signal(close, lookback=50):
    """
    MACD с анализом последних N свечей (по умолчанию 50)
    """
    min_required = max(26, lookback)
    if len(close) < min_required:
        return None

    macd, signal_line, histogram = talib.MACD(
        close,
        fastperiod=fastperiod,
        slowperiod=slowperiod,
        signalperiod=signalperiod
    )

    # Берём последние значения
    current_macd = macd[-1]
    current_signal = signal_line[-1]
    current_histogram = histogram[-1]

    if np.isnan(current_macd) or np.isnan(current_signal):
        return None

    # === НОВЫЙ БЛОК: анализ за последние lookback свечей ===
    hist_window = histogram[-lookback:]
    macd_window = macd[-lookback:]
    signal_window = signal_line[-lookback:]

    # Убираем NaN
    valid_mask = ~np.isnan(hist_window) & ~np.isnan(macd_window) & ~np.isnan(signal_window)
    hist_window = hist_window[valid_mask]
    macd_window = macd_window[valid_mask]
    signal_window = signal_window[valid_mask]

    if len(hist_window) < 5:
        return None

    # 1. Сила тренда гистограммы (сколько свечей подряд растёт/падает)
    hist_diff = np.diff(hist_window)
    bullish_hist_bars = np.sum(hist_diff > 0)
    bearish_hist_bars = np.sum(hist_diff < 0)

    # 2. Сколько свечей MACD выше сигнальной
    macd_above_signal = np.sum(macd_window > signal_window)
    macd_below_signal = np.sum(macd_window < signal_window)

    # === Основная логика с учётом истории ===

    # Сильное пересечение (как раньше)
    if macd[-2] <= signal_line[-2] and current_macd > current_signal:
        return 'bullish'
    if macd[-2] >= signal_line[-2] and current_macd < current_signal:
        return 'bearish'

    # Гистограмма устойчиво растёт + MACD выше сигнальной
    if bullish_hist_bars > len(hist_diff) * 0.65 and current_macd > current_signal:
        return 'bullish'

    # Гистограмма устойчиво падает + MACD ниже сигнальной
    if bearish_hist_bars > len(hist_diff) * 0.65 and current_macd < current_signal:
        return 'bearish'

    # MACD уверенно выше сигнальной большую часть окна
    if macd_above_signal > len(macd_window) * 0.7 and current_macd > 0:
        return 'bullish'

    # MACD уверенно ниже сигнальной большую часть окна
    if macd_below_signal > len(macd_window) * 0.7 and current_macd < 0:
        return 'bearish'

    # Слабые сигналы
    if current_macd > current_signal and current_macd > 0:
        return 'hold'
    if current_macd < current_signal and current_macd < 0:
        return 'hold'

    return 'hold'

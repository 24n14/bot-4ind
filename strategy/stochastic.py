import numpy as np
import talib
import config

fastk_period = config.FASTK
slowk_period = config.SLOWK
slowd_period = config.SLOWD

def _get_stochastic_signal(high, low, close, lookback=50):
    """
    Stochastic Oscillator с анализом тренда за последние N свечей
    """
    min_required = max(14, lookback)
    if len(close) < min_required:
        return None

    slowk, slowd = talib.STOCH(
        high, low, close,
        fastk_period=fastk_period,
        slowk_period=slowk_period,
        slowd_period=slowd_period
    )

    current_k = slowk[-1]
    current_d = slowd[-1]

    if np.isnan(current_k) or np.isnan(current_d):
        return None

    # Берём последние lookback значений
    k_slice = slowk[-lookback:]
    d_slice = slowd[-lookback:]

    # Считаем статистику за период
    k_above_d = np.sum(k_slice > d_slice)
    oversold_count = np.sum(k_slice < 20)
    overbought_count = np.sum(k_slice > 80)
    k_trend = np.mean(np.diff(k_slice[-10:])) if len(k_slice) > 10 else 0  # тренд за последние 10 баров

    # 1. СИЛЬНЫЙ СИГНАЛ — пересечение в зоне
    prev_k = slowk[-2]
    prev_d = slowd[-2]
    if prev_k <= prev_d and current_k > current_d and current_k < 20:
        return 'bullish'
    if prev_k >= prev_d and current_k < current_d and current_k > 80:
        return 'bearish'

    # 2. УСТАНОВИВШИЙСЯ ТРЕНД (смотрим на lookback)
    if current_k > current_d and oversold_count > lookback * 0.6:
        return 'bullish'
    if current_k < current_d and overbought_count > lookback * 0.6:
        return 'bearish'

    # 3. ВЫХОД ИЗ ЗОНЫ
    if prev_k < 20 and current_k > 20 and current_k > current_d:
        return 'bullish'
    if prev_k > 80 and current_k < 80 and current_k < current_d:
        return 'bearish'

    # 4. НАПРАВЛЕНИЕ ДВИЖЕНИЯ (учитываем тренд за период)
    if k_trend > 0 and current_k < 50 and k_above_d > lookback * 0.55:
        return 'bullish'
    if k_trend < 0 and current_k > 50 and k_above_d < lookback * 0.45:
        return 'bearish'

    return 'hold'

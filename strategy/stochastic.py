import numpy as np
import talib
import config
fastk_period = config.FASTK
slowk_period = config.SLOWK
slowd_period = config.SLOWD
def _get_stochastic_signal(high, low, close):
    """
    Индикатор #3: Stochastic Oscillator

    Бычий сигнал:
    - %K пересекает %D снизу вверх в зоне перепродажи (<20)
    - %K > %D и обе линии в зоне перепродажи (<20) — установившийся бычий

    Медвежий сигнал:
    - %K пересекает %D сверху вниз в зоне перекупленности (>80)
    - %K < %D и обе линии в зоне перекупленности (>80) — установившийся медвежий
    """
    if len(close) < 14:
        return None

    slowk, slowd = talib.STOCH(
        high, low, close,
        fastk_period=fastk_period,
        slowk_period=slowk_period,
        slowd_period=slowd_period
    )

    # Берём последние значения
    current_k = slowk[-1]
    current_d = slowd[-1]
    prev_k = slowk[-2]
    prev_d = slowd[-2]

    if np.isnan(current_k) or np.isnan(current_d) or \
            np.isnan(prev_k) or np.isnan(prev_d):
        return None

    # 1. МОМЕНТ ПЕРЕСЕЧЕНИЯ (самый сильный сигнал)
    # %K пересекает %D снизу вверх в зоне перепродажи → BULLISH
    if prev_k <= prev_d and current_k > current_d and current_k < 20:
        return 'bullish'

    # %K пересекает %D сверху вниз в зоне перекупленности → BEARISH
    if prev_k >= prev_d and current_k < current_d and current_k > 80:
        return 'bearish'

    # 2. УСТАНОВИВШИЙСЯ ТРЕНД (после пересечения)
    # %K выше %D и обе линии в зоне перепродажи (<20) → BULLISH
    if current_k > current_d and current_k < 20 and current_d < 20:
        return 'bullish'

    # %K ниже %D и обе линии в зоне перекупленности (>80) → BEARISH
    if current_k < current_d and current_k > 80 and current_d > 80:
        return 'bearish'

    # 3. ВЫХОД ИЗ ЗОНЫ (дополнительный сигнал)
    # %K выходит из зоны перепродажи вверх (>20) → BULLISH
    if prev_k < 20 and current_k > 20 and current_k > current_d:
        return 'bullish'

    # %K выходит из зоны перекупленности вниз (<80) → BEARISH
    if prev_k > 80 and current_k < 80 and current_k < current_d:
        return 'bearish'

    # 4. НАПРАВЛЕНИЕ ДВИЖЕНИЯ (слабый сигнал)
    # %K и %D растут и находятся ниже 50 → потенциальный BULLISH
    if current_k > prev_k and current_d > prev_d and current_k < 50:
        return 'bullish'

    # %K и %D падают и находятся выше 50 → потенциальный BEARISH
    if current_k < prev_k and current_d < prev_d and current_k > 50:
        return 'bearish'

    return 'hold'
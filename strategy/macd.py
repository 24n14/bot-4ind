import numpy as np
import talib
import config

# переменные MACD
fastperiod = config.FAST_macd
slowperiod = config.SLOW_macd
signalperiod = config.SIGNAL_macd
def _get_macd_signal(close):
    """
    Индикатор #2: MACD

    Приоритет сигналов:
    1. Пересечения (самый сильный сигнал)
    2. Направление гистограммы + положение MACD
    3. Положение MACD относительно нуля и сигнальной
    """
    if len(close) < 26:
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
    prev_macd = macd[-2]
    prev_signal = signal_line[-2]
    prev_histogram = histogram[-2]

    # Проверяем на NaN
    if np.isnan(current_macd) or np.isnan(current_signal) or \
            np.isnan(prev_macd) or np.isnan(prev_signal):
        return None

    # 1. ПРОВЕРКА ПЕРЕСЕЧЕНИЙ (наивысший приоритет)
    # MACD пересекает сигнальную снизу вверх → BULLISH
    if prev_macd <= prev_signal and current_macd > current_signal:
        return 'bullish'

    # MACD пересекает сигнальную сверху вниз → BEARISH
    if prev_macd >= prev_signal and current_macd < current_signal:
        return 'bearish'

    # 2. ПРОВЕРКА ТРЕНДА ПО ГИСТОГРАММЕ (второй приоритет)
    # Гистограмма растёт → BULLISH (если MACD выше сигнальной)
    if current_histogram > prev_histogram and current_macd > current_signal:
        return 'bullish'

    # Гистограмма падает → BEARISH (если MACD ниже сигнальной)
    if current_histogram < prev_histogram and current_macd < current_signal:
        return 'bearish'

    # 3. ПРОВЕРКА ПОЛОЖЕНИЯ MACD (третий приоритет)
    # MACD выше сигнальной И выше нуля И гистограмма положительная → BULLISH
    if current_macd > current_signal and current_macd > 0 and current_histogram > 0:
        return 'bullish'

    # MACD ниже сигнальной И ниже нуля И гистограмма отрицательная → BEARISH
    if current_macd < current_signal and current_macd < 0 and current_histogram < 0:
        return 'bearish'

    # 4. СЛАБЫЕ СИГНАЛЫ (четвёртый приоритет)
    # MACD выше сигнальной, но гистограмма падает → слабый BULLISH (только если выше нуля)
    if current_macd > current_signal and current_macd > 0 and current_histogram < prev_histogram:
        return 'hold'  # Слишком слабый сигнал для входа

    # MACD ниже сигнальной, но гистограмма растёт → слабый BEARISH (только если ниже нуля)
    if current_macd < current_signal and current_macd < 0 and current_histogram > prev_histogram:
        return 'hold'  # Слишком слабый сигнал для входа

    return 'hold'

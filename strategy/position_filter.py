# position_filter.py
import pandas as pd
import config


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    high = df['high']
    low = df['low']
    close = df['close']
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def _rolling_extremes(df: pd.DataFrame, window: int = 50) -> tuple[float, float]:
    tail = df.tail(window)
    return float(tail['high'].max()), float(tail['low'].min())


def _near_level(price: float, levels: list[float], tolerance: float) -> bool:
    return any(abs(price - lvl) <= tolerance for lvl in levels)


def is_near_historical_high(current_price: float, df: pd.DataFrame, levels_data: dict, atr_multiplier: float = None, extreme_window: int = None) -> dict:
    """
    Проверяет, находится ли цена близко к историческому максимуму.
    Возвращает словарь с результатом проверки.
    """
    if atr_multiplier is None:
        atr_multiplier = config.ATR_MULTIPLIER
    if extreme_window is None:
        extreme_window = config.EXTREME_WINDOW

    atr = _atr(df)
    if not pd.notna(atr) or atr <= 0:
        return {'blocked': False, 'reason': 'Нет данных для ATR'}

    tolerance = atr * atr_multiplier
    hist_high, hist_low = _rolling_extremes(df, window=extreme_window)

    # Проверяем, насколько цена близка к историческим уровням
    dist_to_high = hist_high - current_price
    dist_to_low = current_price - hist_low

    # Проверяем уровни поддержки/сопротивления
    cluster_resistance = [lvl for lvl in levels_data['cluster_levels'] if lvl > current_price]
    cluster_support = [lvl for lvl in levels_data['cluster_levels'] if lvl < current_price]

    near_resistance = _near_level(current_price, cluster_resistance, tolerance)
    near_support = _near_level(current_price, cluster_support, tolerance)

    # Проверяем, находится ли цена в пределах tolerance от уровня
    near_hist_high = 0 <= dist_to_high <= tolerance
    near_hist_low = 0 <= dist_to_low <= tolerance

    if near_hist_high or near_resistance:
        return {'blocked': True, 'reason': f'Цена близка к историческому максимуму {hist_high:.2f}'}
    else:
        return {'blocked': False, 'reason': 'Цена не близка к историческому максимуму'}


def is_near_historical_low(current_price: float, df: pd.DataFrame, levels_data: dict, atr_multiplier: float = None, extreme_window: int = None) -> dict:
    """
    Проверяет, находится ли цена близко к историческому минимуму.
    Возвращает словарь с результатом проверки.
    """
    if atr_multiplier is None:
        atr_multiplier = config.ATR_MULTIPLIER
    if extreme_window is None:
        extreme_window = config.EXTREME_WINDOW

    atr = _atr(df)
    if not pd.notna(atr) or atr <= 0:
        return {'blocked': False, 'reason': 'Нет данных для ATR'}

    tolerance = atr * atr_multiplier
    hist_high, hist_low = _rolling_extremes(df, window=extreme_window)

    # Проверяем, насколько цена близка к историческим уровням
    dist_to_high = hist_high - current_price
    dist_to_low = current_price - hist_low

    # Проверяем уровни поддержки/сопротивления
    cluster_resistance = [lvl for lvl in levels_data['cluster_levels'] if lvl > current_price]
    cluster_support = [lvl for lvl in levels_data['cluster_levels'] if lvl < current_price]

    near_resistance = _near_level(current_price, cluster_resistance, tolerance)
    near_support = _near_level(current_price, cluster_support, tolerance)

    # Проверяем, находится ли цена в пределах tolerance от уровня
    near_hist_high = 0 <= dist_to_high <= tolerance
    near_hist_low = 0 <= dist_to_low <= tolerance

    if near_hist_low or near_support:
        return {'blocked': True, 'reason': f'Цена близка к историческому минимуму {hist_low:.2f}'}
    else:
        return {'blocked': False, 'reason': 'Цена не близка к историческому минимуму'}


def get_position_filter_signal(
        current_price: float,
        df: pd.DataFrame,
        levels_data: dict,
        atr_multiplier: float = None,
        extreme_window: int = None
) -> str:
    """
    Возвращает сигнал фильтра позиций как индикатор.
    Возвращает 'bullish', 'bearish' или 'hold' в зависимости от ситуации.
    """
    if atr_multiplier is None:
        atr_multiplier = config.ATR_MULTIPLIER
    if extreme_window is None:
        extreme_window = config.EXTREME_WINDOW

    atr = _atr(df)
    if not pd.notna(atr) or atr <= 0:
        return 'hold'  # Нет данных для анализа

    tolerance = atr * atr_multiplier
    hist_high, hist_low = _rolling_extremes(df, window=extreme_window)

    # Проверяем, насколько цена близка к историческим уровням
    dist_to_high = hist_high - current_price
    dist_to_low = current_price - hist_low

    # Проверяем уровни поддержки/сопротивления
    cluster_resistance = [lvl for lvl in levels_data['cluster_levels'] if lvl > current_price]
    cluster_support = [lvl for lvl in levels_data['cluster_levels'] if lvl < current_price]

    near_resistance = _near_level(current_price, cluster_resistance, tolerance)
    near_support = _near_level(current_price, cluster_support, tolerance)

    # Логика сигналов:
    # Если цена близка к верху истории или к сопротивлению - "bearish"
    # Если цена близка к низу истории или к поддержке - "bullish"
    # Иначе "hold"

    if near_resistance:
        return 'bearish'
    elif near_support:
        return 'bullish'
    else:
        return 'hold'

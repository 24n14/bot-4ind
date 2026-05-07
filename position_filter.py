#import numpy as np
import pandas as pd
import config


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    high  = df['high']
    low   = df['low']
    close = df['close']
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low  - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def _rolling_extremes(df: pd.DataFrame, window: int = 50) -> tuple[float, float]:
    tail = df.tail(window)
    return float(tail['high'].max()), float(tail['low'].min())


def _near_level(price: float, levels: list[float], tolerance: float) -> bool:
    return any(abs(price - lvl) <= tolerance for lvl in levels)


def is_near_historical_high(
    current_price: float,
    df: pd.DataFrame,
    levels_data: dict,
    atr_multiplier: float = None,
    extreme_window: int = None
) -> dict:

    if atr_multiplier is None:
        atr_multiplier = config.ATR_MULTIPLIER
    if extreme_window is None:
        extreme_window = config.EXTREME_WINDOW

    atr = _atr(df)
    tolerance = atr * atr_multiplier
    hist_high, _ = _rolling_extremes(df, window=extreme_window)

    dist_to_high = hist_high - current_price
    distance_in_atr = dist_to_high / atr if atr > 0 else 999

    # ✅ Берём только кластеры ВЫШЕ текущей цены (они — сопротивления)
    cluster_resistance = [lvl for lvl in levels_data['cluster_levels'] if lvl > current_price]
    #resistance_levels = levels_data['resistance']  # уже отфильтрованы
    near_resistance = _near_level(
        current_price,
        cluster_resistance,
        #levels_data['resistance'] + cluster_resistance,  # ✅ исправлено
        #resistance_levels + cluster_resistance,
        tolerance
    )
    near_hist_high = dist_to_high <= tolerance
    at_poc_top     = current_price >= levels_data['poc'] and near_hist_high

    blocked = near_hist_high or near_resistance or at_poc_top

    reasons = []
    if near_hist_high:
        reasons.append(f"цена в {distance_in_atr:.2f} ATR от исторического хая ({hist_high:.4f})")
    if near_resistance:
        reasons.append("цена у уровня сопротивления")
    if at_poc_top:
        reasons.append("цена выше POC и у хая")

    return {
        'blocked':         blocked,
        'reason':          " | ".join(reasons) if reasons else "OK",
        'distance_atr':    round(distance_in_atr, 3),
        'hist_high':       hist_high,
        'near_resistance': near_resistance
    }


def is_near_historical_low(
    current_price: float,
    df: pd.DataFrame,
    levels_data: dict,
    atr_multiplier: float = None,
    extreme_window: int = None
) -> dict:

    if atr_multiplier is None:
        atr_multiplier = config.ATR_MULTIPLIER
    if extreme_window is None:
        extreme_window = config.EXTREME_WINDOW

    atr = _atr(df)
    tolerance = atr * atr_multiplier
    _, hist_low = _rolling_extremes(df, window=extreme_window)

    dist_to_low = current_price - hist_low
    distance_in_atr = dist_to_low / atr if atr > 0 else 999

    # ✅ Берём только кластеры НИЖЕ текущей цены (они — поддержки)
    cluster_support = [lvl for lvl in levels_data['cluster_levels'] if lvl < current_price]
    #support_levels = levels_data['support']  # уже отфильтрованы
    near_support = _near_level(
        current_price,
        cluster_support,
        #levels_data['support'] + cluster_support,
        #support_levels + cluster_support,
        tolerance
    )
    near_hist_low = dist_to_low <= tolerance
    at_poc_bottom = current_price <= levels_data['poc'] and near_hist_low

    blocked = near_hist_low or near_support or at_poc_bottom

    reasons = []
    if near_hist_low:
        reasons.append(f"цена в {distance_in_atr:.2f} ATR от исторического лоя ({hist_low:.4f})")
    if near_support:
        reasons.append("цена у уровня поддержки")
    if at_poc_bottom:
        reasons.append("цена ниже POC и у лоя")

    return {
        'blocked':      blocked,
        'reason':       " | ".join(reasons) if reasons else "OK",
        'distance_atr': round(distance_in_atr, 3),
        'hist_low':     hist_low,
        'near_support': near_support
    }

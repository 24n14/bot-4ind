import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def find_support_resistance_levels(
    df: pd.DataFrame,
    n_clusters: int = 6,
    lookback: int = 200,
    price_col_high: str = 'high',
    price_col_low: str = 'low',
    price_col_close: str = 'close',
    price_col_volume: str = 'volume'
) -> dict:
    df = df.tail(lookback).copy()
    df.reset_index(drop=True, inplace=True)

    # ── 1. KMeans по экстремумам ──────────────────────────────────────
    extremes = pd.concat([
        df[price_col_high],
        df[price_col_low]
    ]).values.reshape(-1, 1)

    k = min(n_clusters, len(extremes) - 1)
    km = KMeans(n_clusters=k, random_state=42, n_init='auto')
    km.fit(extremes)
    cluster_levels = sorted(
        [float(c[0]) for c in km.cluster_centers_]
    )

    # ── 2. Volume Profile — POC ───────────────────────────────────────
    price_min = df[price_col_low].min()
    price_max = df[price_col_high].max()
    bins = 50
    bin_edges = np.linspace(price_min, price_max, bins + 1)
    bin_volumes = np.zeros(bins)

    for _, row in df.iterrows():
        for i in range(bins):
            lo_bin = bin_edges[i]
            hi_bin = bin_edges[i + 1]
            candle_lo = row[price_col_low]
            candle_hi = row[price_col_high]
            overlap = max(0.0, min(candle_hi, hi_bin) - max(candle_lo, lo_bin))
            candle_range = candle_hi - candle_lo
            if candle_range > 0:
                bin_volumes[i] += row[price_col_volume] * (overlap / candle_range)

    poc_idx = int(np.argmax(bin_volumes))
    poc = float((bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2)

    # ── 3. Pivot Points ───────────────────────────────────────────────
    h = float(df[price_col_high].iloc[-1])
    l = float(df[price_col_low].iloc[-1])
    c = float(df[price_col_close].iloc[-1])

    pp = (h + l + c) / 3
    r1 = 2 * pp - l
    r2 = pp + (h - l)
    r3 = h + 2 * (pp - l)
    s1 = 2 * pp - h
    s2 = pp - (h - l)
    s3 = l - 2 * (h - pp)

    # ── 4. Делим кластеры на resistance / support по POC ─────────────
    #   Кластеры ВЫШЕ poc → resistance (мешают лонгу)
    #   Кластеры НИЖЕ poc → support    (мешают шорту)
    cluster_resistance = [lvl for lvl in cluster_levels if lvl >= poc]
    cluster_support = [lvl for lvl in cluster_levels if lvl < poc]

    # ── 5. Объединяем уровни по направлению ──────────────────────────
    resistance_levels = sorted(set(cluster_resistance + [r1, r2, r3]))
    support_levels = sorted(set(cluster_support + [s1, s2, s3]))

    all_levels = sorted(set(
        cluster_levels + [poc, pp, r1, r2, r3, s1, s2, s3]
    ))

    return {
        'cluster_levels':     cluster_levels,       # все кластеры (для инфо)
        'cluster_resistance': cluster_resistance,   # ← НОВОЕ
        'cluster_support':    cluster_support,      # ← НОВОЕ
        'poc':                poc,
        'pivot':              pp,
        'resistance':         resistance_levels,    # pivot R1 R2 R3 + кластеры выше
        'support':            support_levels,       # pivot S1 S2 S3 + кластеры ниже
        'all_levels':         all_levels
    }

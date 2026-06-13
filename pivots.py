"""
Pivot Detection Module - ZigZag Algorithm
Identifies swing highs/lows which form the basis of Elliott Wave labeling.

The ZigZag filters out minor fluctuations and reveals the dominant swings.
Threshold = minimum % price movement to qualify as a new swing.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Tuple
from config import DEFAULT_ZIGZAG_THRESHOLD


@dataclass
class Pivot:
    """A single swing high or swing low."""
    index: int          # positional index in the price series
    date: pd.Timestamp  # datetime of the pivot
    price: float        # price at the pivot
    pivot_type: str     # 'HIGH' or 'LOW'
    bar_index: int = 0  # raw bar index in original dataframe

    def __repr__(self):
        return f"Pivot({self.pivot_type} @ {self.date.date()} = {self.price:.4f})"


def detect_pivots(
    df: pd.DataFrame,
    threshold: float = DEFAULT_ZIGZAG_THRESHOLD,
    price_col: str = "Close",
    use_hl: bool = True,
) -> List[Pivot]:
    """
    Detect swing highs and lows using the ZigZag algorithm.

    Parameters
    ----------
    df        : OHLCV DataFrame
    threshold : Minimum price move (as fraction) to register a new swing.
                0.05 = 5% move required to flip direction.
    price_col : Column to use when not using High/Low
    use_hl    : If True, uses High for peaks and Low for troughs (recommended)

    Returns
    -------
    List of Pivot objects, alternating HIGH/LOW
    """
    if use_hl and "High" in df.columns and "Low" in df.columns:
        highs = df["High"].values
        lows  = df["Low"].values
    else:
        highs = df[price_col].values
        lows  = df[price_col].values

    dates = df.index
    n = len(df)

    if n < 4:
        raise ValueError("Need at least 4 bars to detect pivots.")

    # ── Phase 1: detect raw direction changes ──────────────────────────────
    pivots_raw: List[Tuple[int, float, str]] = []  # (idx, price, type)

    # Find first meaningful move
    direction = None
    anchor_price = highs[0]
    anchor_idx   = 0

    for i in range(1, n):
        h, l = highs[i], lows[i]
        if direction is None:
            move_up   = (h - anchor_price) / anchor_price
            move_down = (anchor_price - l) / anchor_price
            if move_up >= threshold:
                pivots_raw.append((anchor_idx, lows[anchor_idx], "LOW"))
                direction    = "UP"
                anchor_price = h
                anchor_idx   = i
            elif move_down >= threshold:
                pivots_raw.append((anchor_idx, highs[anchor_idx], "HIGH"))
                direction    = "DOWN"
                anchor_price = l
                anchor_idx   = i
        elif direction == "UP":
            if h > anchor_price:
                anchor_price = h
                anchor_idx   = i
            elif (anchor_price - l) / anchor_price >= threshold:
                pivots_raw.append((anchor_idx, anchor_price, "HIGH"))
                direction    = "DOWN"
                anchor_price = l
                anchor_idx   = i
        else:  # DOWN
            if l < anchor_price:
                anchor_price = l
                anchor_idx   = i
            elif (h - anchor_price) / anchor_price >= threshold:
                pivots_raw.append((anchor_idx, anchor_price, "LOW"))
                direction    = "UP"
                anchor_price = h
                anchor_idx   = i

    # Add final pivot
    if direction == "UP":
        pivots_raw.append((anchor_idx, anchor_price, "HIGH"))
    elif direction == "DOWN":
        pivots_raw.append((anchor_idx, anchor_price, "LOW"))

    # ── Phase 2: build Pivot objects ───────────────────────────────────────
    pivots: List[Pivot] = []
    for seq_i, (bar_i, price, ptype) in enumerate(pivots_raw):
        pivots.append(Pivot(
            index      = seq_i,
            date       = dates[bar_i],
            price      = price,
            pivot_type = ptype,
            bar_index  = bar_i,
        ))

    return pivots


def pivots_to_series(pivots: List[Pivot], df: pd.DataFrame) -> pd.Series:
    """
    Convert pivot list to a price series aligned with the original DataFrame.
    NaN where no pivot.
    """
    s = pd.Series(np.nan, index=df.index)
    for p in pivots:
        s.iloc[p.bar_index] = p.price
    return s


def get_swing_lengths(pivots: List[Pivot]) -> List[float]:
    """Return the absolute price length of each swing between consecutive pivots."""
    return [abs(pivots[i+1].price - pivots[i].price) for i in range(len(pivots)-1)]


def get_swing_retracement(p1: Pivot, p2: Pivot, p3: Pivot) -> float:
    """
    Calculate retracement ratio of wave p2→p3 relative to wave p1→p2.
    Used to check Fibonacci retracement levels.
    """
    wave_len = abs(p2.price - p1.price)
    retrace  = abs(p3.price - p2.price)
    if wave_len == 0:
        return 0.0
    return retrace / wave_len

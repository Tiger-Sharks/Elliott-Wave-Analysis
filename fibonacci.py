"""
Fibonacci Module
Handles ratio calculations, level generation, and ratio matching.
Based on Chapter 3 (Fibonacci mathematics) of Elliott Wave Principle.
"""

import numpy as np
from typing import List, Tuple, Optional
from config import FIBONACCI_RATIOS, RATIO_TOLERANCE, PHI, PHI_INV


def nearest_fib_ratio(ratio: float, tolerance: float = RATIO_TOLERANCE) -> Optional[float]:
    """
    Find the nearest Fibonacci ratio to the given value within tolerance.
    Returns None if no Fibonacci ratio is close enough.
    """
    if ratio <= 0:
        return None
    best = None
    best_diff = float("inf")
    for fib in FIBONACCI_RATIOS:
        diff = abs(ratio - fib)
        if diff < best_diff:
            best_diff = diff
            best = fib
    if best_diff / best <= tolerance:
        return best
    return None


def is_fib_ratio(ratio: float, target: float, tolerance: float = RATIO_TOLERANCE) -> bool:
    """Check if ratio ≈ target within percentage tolerance."""
    if target == 0:
        return False
    return abs(ratio - target) / target <= tolerance


def fib_retracement_levels(high: float, low: float) -> dict:
    """
    Generate standard Fibonacci retracement levels between high and low.
    Returns a dict of {ratio: price_level}.
    """
    diff = high - low
    levels = {}
    for r in [0.236, 0.382, 0.500, 0.618, 0.786]:
        levels[r] = high - diff * r
    return levels


def fib_extension_levels(start: float, end: float, retrace_end: float) -> dict:
    """
    Generate Fibonacci extension levels for a potential next wave.

    Parameters
    ----------
    start       : Origin of wave (e.g., Wave 1 start)
    end         : End of wave   (e.g., Wave 1 end)
    retrace_end : End of retracement (e.g., Wave 2 end)

    Returns dict of {ratio: projected_price}.
    """
    wave_len = abs(end - start)
    direction = 1 if end > start else -1
    levels = {}
    for r in [0.618, 1.0, 1.272, 1.618, 2.0, 2.618]:
        levels[r] = retrace_end + direction * wave_len * r
    return levels


def score_ratio(ratio: float) -> float:
    """
    Score how well a ratio aligns with Fibonacci numbers.
    Returns 0.0 (poor) to 1.0 (perfect Fibonacci alignment).
    """
    if ratio <= 0:
        return 0.0
    best_diff = min(abs(ratio - f) / f for f in FIBONACCI_RATIOS)
    # Convert to 0-1 score (0 diff → 1.0 score, 10%+ diff → 0.0)
    return max(0.0, 1.0 - best_diff / RATIO_TOLERANCE)


def wave_ratio(wave_a_length: float, wave_b_length: float) -> float:
    """Return the ratio of wave_b_length to wave_a_length."""
    if wave_a_length == 0:
        return 0.0
    return wave_b_length / wave_a_length

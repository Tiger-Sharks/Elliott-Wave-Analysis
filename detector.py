"""
Elliott Wave Detector - Main Engine
Scans pivot sequences, builds wave candidates, scores them,
and returns the best-fitting Elliott Wave interpretation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple

from pivots  import Pivot, detect_pivots, get_swing_retracement
from waves   import Wave, WavePattern, AnalysisResult
from rules   import classify_pattern
from fibonacci import fib_extension_levels, fib_retracement_levels, wave_ratio
from config  import (
    DEFAULT_ZIGZAG_THRESHOLD, CONFIDENCE_MEDIUM,
    WAVE_DEGREES,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _pivots_to_waves(pivots: List[Pivot], labels: List[str]) -> List[Wave]:
    """Convert a list of consecutive pivots to Wave objects with given labels."""
    waves: List[Wave] = []
    for i in range(len(labels)):
        if i + 1 >= len(pivots):
            break
        w = Wave(label=labels[i], start=pivots[i], end=pivots[i + 1])
        waves.append(w)
    return waves


def _build_candidates(
    pivots: List[Pivot],
    window: int,
) -> List[Tuple[int, List[Pivot]]]:
    """
    Generate all sliding windows of `window+1` pivots from the pivot list.
    Returns [(start_index, [pivot_0 .. pivot_window]), ...]
    """
    candidates = []
    for start in range(len(pivots) - window):
        window_pivots = pivots[start: start + window + 1]
        # All windows must be alternating HIGH/LOW
        types = [p.pivot_type for p in window_pivots]
        ok = all(types[i] != types[i+1] for i in range(len(types)-1))
        if ok:
            candidates.append((start, window_pivots))
    return candidates


def _wave_direction_ok(pivots: List[Pivot], bullish: bool) -> bool:
    """Check that the first wave moves in the expected direction."""
    if len(pivots) < 2:
        return False
    if bullish:
        return pivots[1].price > pivots[0].price   # first wave is UP
    else:
        return pivots[1].price < pivots[0].price   # first wave is DOWN


# ─────────────────────────────────────────────────────────────────────────────
#  Price targets after pattern completion
# ─────────────────────────────────────────────────────────────────────────────

def compute_targets(pattern: WavePattern) -> Tuple[List[float], float]:
    """
    After a completed impulse (or partial), project likely next move targets
    and the invalidation level.

    Returns (targets, invalidation_price)
    """
    targets: List[float] = []
    invalidation = 0.0

    if not pattern.waves:
        return targets, invalidation

    w = pattern.waves
    bullish = pattern.is_bullish

    if pattern.pattern_type == "IMPULSE":
        # After a 5-wave impulse, expect an A-B-C correction
        # Target: retrace 38.2%–61.8% of the entire impulse
        total_len = abs(pattern.end_price - pattern.start_price)
        if bullish:
            targets.append(pattern.end_price - total_len * 0.382)
            targets.append(pattern.end_price - total_len * 0.500)
            targets.append(pattern.end_price - total_len * 0.618)
            invalidation = pattern.start_price  # Wave 2 can't exceed Wave 1 start
        else:
            targets.append(pattern.end_price + total_len * 0.382)
            targets.append(pattern.end_price + total_len * 0.618)
            invalidation = pattern.start_price

    elif pattern.pattern_type in ("ZIGZAG", "FLAT"):
        # After an A-B-C correction, expect a new impulse
        if len(w) >= 1:
            w_A = w[0]
            if bullish:
                # Correction ends low → new impulse up
                ext = fib_extension_levels(
                    w_A.start.price, w_A.end.price, w[-1].end.price
                )
                targets = [ext[r] for r in sorted(ext)[:3]]
            else:
                ext = fib_extension_levels(
                    w_A.start.price, w_A.end.price, w[-1].end.price
                )
                targets = [ext[r] for r in sorted(ext)[:3]]
        invalidation = pattern.end_price  # break of correction low/high

    return sorted(targets), invalidation


# ─────────────────────────────────────────────────────────────────────────────
#  Current wave position estimation
# ─────────────────────────────────────────────────────────────────────────────

def estimate_current_wave(pivots: List[Pivot], best_pattern: Optional[WavePattern]) -> str:
    """
    Given the latest pivots and the best-fit pattern, estimate what wave we're in now.
    """
    if best_pattern is None or not best_pattern.waves:
        return "?"

    last_pivot_date = pivots[-1].date
    last_wave_end   = best_pattern.waves[-1].end.date

    if last_pivot_date <= last_wave_end:
        # Still inside the pattern
        n = len(best_pattern.waves)
        if best_pattern.pattern_type == "IMPULSE":
            labels = ["1","2","3","4","5"]
            return labels[min(n-1, 4)]
        else:
            labels = ["A","B","C"]
            return labels[min(n-1, 2)]
    else:
        # Pattern complete, next wave underway
        if best_pattern.pattern_type == "IMPULSE":
            return "A (corrective)"
        else:
            return "1 (new impulse)"


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN ANALYSIS FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def analyze(
    df: pd.DataFrame,
    symbol: str = "UNKNOWN",
    timeframe: str = "Daily",
    zigzag_threshold: float = DEFAULT_ZIGZAG_THRESHOLD,
    degree: str = "Minor",
    min_confidence: float = CONFIDENCE_MEDIUM,
    max_patterns: int = 10,
) -> AnalysisResult:
    """
    Full Elliott Wave analysis pipeline.

    Parameters
    ----------
    df               : OHLCV DataFrame
    symbol           : Ticker symbol (for labeling)
    timeframe        : e.g. "Daily", "Weekly", "Hourly"
    zigzag_threshold : ZigZag sensitivity (0.03–0.10 typical)
    degree           : Wave degree label
    min_confidence   : Minimum score to include a pattern in results
    max_patterns     : How many candidate patterns to return

    Returns
    -------
    AnalysisResult with all detected patterns, best pattern, targets
    """
    result = AnalysisResult(symbol=symbol, timeframe=timeframe)

    # ── Step 1: Detect pivot points ─────────────────────────────────────────
    try:
        pivots = detect_pivots(df, threshold=zigzag_threshold)
    except ValueError as e:
        result.summary = f"Error detecting pivots: {e}"
        return result

    if len(pivots) < 4:
        result.summary = "Not enough pivot points found. Try lowering zigzag_threshold."
        return result

    all_patterns: List[WavePattern] = []

    # ── Step 2: Scan for 5-wave impulse patterns ────────────────────────────
    for start_idx, window_pivots in _build_candidates(pivots, window=5):
        for bullish in (True, False):
            if not _wave_direction_ok(window_pivots, bullish):
                continue
            labels = ["1","2","3","4","5"]
            waves  = _pivots_to_waves(window_pivots, labels)
            if len(waves) < 5:
                continue
            ptype, conf, viol, notes = classify_pattern(waves)
            if conf >= min_confidence:
                pat = WavePattern(
                    pattern_type = ptype,
                    waves        = waves,
                    confidence   = conf,
                    degree       = degree,
                    violations   = viol,
                    notes        = notes,
                )
                all_patterns.append(pat)

    # ── Step 3: Scan for 3-wave corrective patterns (A-B-C) ─────────────────
    for start_idx, window_pivots in _build_candidates(pivots, window=3):
        for bullish in (True, False):
            if not _wave_direction_ok(window_pivots, bullish):
                continue
            labels = ["A","B","C"]
            waves  = _pivots_to_waves(window_pivots, labels)
            if len(waves) < 3:
                continue
            ptype, conf, viol, notes = classify_pattern(waves)
            if conf >= min_confidence:
                pat = WavePattern(
                    pattern_type = ptype,
                    waves        = waves,
                    confidence   = conf,
                    degree       = degree,
                    violations   = viol,
                    notes        = notes,
                )
                all_patterns.append(pat)

    # ── Step 4: Scan for triangles (5 corrective waves A-B-C-D-E) ──────────
    for start_idx, window_pivots in _build_candidates(pivots, window=5):
        labels = ["A","B","C","D","E"]
        waves  = _pivots_to_waves(window_pivots, labels)
        if len(waves) < 5:
            continue
        ptype, conf, viol, notes = classify_pattern(waves)
        if ptype == "TRIANGLE" and conf >= min_confidence:
            pat = WavePattern(
                pattern_type = "TRIANGLE",
                waves        = waves,
                confidence   = conf,
                degree       = degree,
                violations   = viol,
                notes        = notes,
            )
            all_patterns.append(pat)

    # ── Step 5: Rank and deduplicate ────────────────────────────────────────
    all_patterns.sort(key=lambda p: p.confidence, reverse=True)

    # Deduplicate: keep only the best pattern for each overlapping pivot window
    seen_ends = set()
    unique_patterns: List[WavePattern] = []
    for pat in all_patterns:
        key = (pat.start_date, pat.end_date, pat.pattern_type)
        if key not in seen_ends:
            seen_ends.add(key)
            unique_patterns.append(pat)
        if len(unique_patterns) >= max_patterns:
            break

    result.patterns = unique_patterns

    # ── Step 6: Identify best pattern ───────────────────────────────────────
    if unique_patterns:
        # Prefer the most recent pattern (latest end date) with highest confidence
        recent_patterns = sorted(
            unique_patterns,
            key=lambda p: (p.end_date or pd.Timestamp.min, p.confidence),
            reverse=True,
        )
        result.best_pattern = recent_patterns[0]

        # ── Step 7: Compute price targets ───────────────────────────────────
        targets, invalidation = compute_targets(result.best_pattern)
        result.next_targets       = targets
        result.invalidation_level = invalidation

        # ── Step 8: Current wave label ──────────────────────────────────────
        result.current_wave_label = estimate_current_wave(pivots, result.best_pattern)

        # ── Step 9: Generate summary ─────────────────────────────────────────
        bp = result.best_pattern
        result.summary = (
            f"Best pattern: {bp.pattern_type} | "
            f"Confidence: {bp.confidence:.0%} | "
            f"{'Bullish' if bp.is_bullish else 'Bearish'} | "
            f"Violations: {len(bp.violations)} | "
            f"Current wave: {result.current_wave_label}"
        )
    else:
        result.summary = (
            f"No patterns found with confidence ≥ {min_confidence:.0%}. "
            f"Try adjusting zigzag_threshold or min_confidence."
        )

    return result

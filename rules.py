"""
Elliott Wave Rules & Guidelines Validator
Based strictly on Frost & Prechter "Elliott Wave Principle"

THREE INVIOLABLE RULES (Chapter 1):
  Rule 1: Wave 2 never retraces more than 100% of Wave 1
  Rule 2: Wave 3 is never the shortest impulse wave (among 1, 3, 5)
  Rule 3: Wave 4 price territory never overlaps Wave 1 price territory
           (except in diagonal triangles)

GUIDELINES (not absolute but expected most of the time):
  - Wave 2 typically retraces 61.8% or 38.2% of Wave 1
  - Wave 3 typically extends to 1.618× Wave 1
  - Wave 4 typically retraces 38.2% of Wave 3
  - Wave 5 ≈ Wave 1, or equals 0.618× Wave 1, or equals 1.618× Wave 1
  - Alternation: Waves 2 and 4 tend to alternate in form
  - Equality: when two motive waves are not extended, they tend to equality
"""

from typing import List, Tuple
from waves import Wave, WavePattern
from fibonacci import score_ratio, wave_ratio, is_fib_ratio
from config import (
    WAVE2_RETRACE_MIN, WAVE2_RETRACE_MAX,
    WAVE4_RETRACE_MIN, WAVE4_RETRACE_MAX,
    RATIO_TOLERANCE, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
)


# ═══════════════════════════════════════════════════════════
#  IMPULSE WAVE RULES  (5-wave motive pattern: 1-2-3-4-5)
# ═══════════════════════════════════════════════════════════

def validate_impulse(waves: List[Wave]) -> Tuple[float, List[str], List[str]]:
    """
    Validate a 5-wave impulse pattern against all EW rules.

    Returns
    -------
    (confidence: float, violations: List[str], notes: List[str])
    """
    if len(waves) != 5:
        return 0.0, ["Need exactly 5 waves for impulse"], []

    w1, w2, w3, w4, w5 = waves
    violations: List[str] = []
    notes:      List[str] = []
    score_components:  List[float] = []

    # ── Rule 1: Wave 2 never retraces 100%+ of Wave 1 ──────────────────────
    w2_retrace = w2.length / w1.length if w1.length > 0 else 99
    if w2_retrace >= 1.0:
        violations.append(
            f"RULE 1 VIOLATED: Wave 2 retraces {w2_retrace:.1%} of Wave 1 "
            f"(must be < 100%)"
        )
        score_components.append(0.0)
    else:
        # Score based on how close to typical 38.2%–78.6% retracement
        if 0.382 <= w2_retrace <= 0.786:
            score_components.append(1.0)
            notes.append(f"Wave 2 retraces {w2_retrace:.1%} of Wave 1 ✓ (typical Fibonacci zone)")
        elif 0.236 <= w2_retrace < 0.382:
            score_components.append(0.7)
            notes.append(f"Wave 2 retraces {w2_retrace:.1%} of Wave 1 (shallow, acceptable)")
        else:
            score_components.append(0.5)
            notes.append(f"Wave 2 retraces {w2_retrace:.1%} of Wave 1 (deep, watch for rule violation)")

    # ── Rule 2: Wave 3 is NEVER the shortest impulse wave ───────────────────
    motive_lengths = [w1.length, w3.length, w5.length]
    if w3.length == min(motive_lengths):
        violations.append(
            f"RULE 2 VIOLATED: Wave 3 ({w3.length:.4f}) is the shortest impulse wave"
        )
        score_components.append(0.0)
    else:
        # Bonus if Wave 3 is clearly the longest (typical)
        if w3.length == max(motive_lengths):
            w3_ratio = w3.length / w1.length
            score_components.append(min(1.0, score_ratio(w3_ratio) + 0.4))
            notes.append(
                f"Wave 3 is longest ({w3.length / w1.length:.3f}× Wave 1) ✓"
            )
        else:
            score_components.append(0.7)
            notes.append(f"Wave 3 is not shortest (Wave 5 is longest - extended 5th)")

    # ── Rule 3: Wave 4 does NOT overlap Wave 1 territory ────────────────────
    bullish = w1.direction == "UP"
    if bullish:
        w1_top    = w1.end.price
        w4_bottom = w4.end.price    # Wave 4 end (corrective low)
        if w4_bottom <= w1_top:
            violations.append(
                f"RULE 3 VIOLATED: Wave 4 low ({w4_bottom:.4f}) overlaps "
                f"Wave 1 high ({w1_top:.4f})"
            )
            score_components.append(0.0)
        else:
            gap = (w4_bottom - w1_top) / w1_top
            score_components.append(min(1.0, 0.6 + gap * 5))
            notes.append(f"Wave 4 above Wave 1 top ✓ (gap: {gap:.1%})")
    else:  # Bearish impulse
        w1_bottom = w1.end.price
        w4_top    = w4.end.price
        if w4_top >= w1_bottom:
            violations.append(
                f"RULE 3 VIOLATED: Wave 4 high ({w4_top:.4f}) overlaps "
                f"Wave 1 low ({w1_bottom:.4f})"
            )
            score_components.append(0.0)
        else:
            score_components.append(0.8)
            notes.append("Wave 4 below Wave 1 bottom ✓")

    # ── Guideline: Wave 3 Fibonacci extension ────────────────────────────────
    w3_ratio = w3.length / w1.length if w1.length > 0 else 0
    fib_score_w3 = score_ratio(w3_ratio)
    score_components.append(fib_score_w3 * 0.5 + 0.5)  # bonus, not penalty
    if is_fib_ratio(w3_ratio, 1.618):
        notes.append(f"Wave 3 = 1.618× Wave 1 ✓ (golden ratio extension)")
    elif is_fib_ratio(w3_ratio, 2.618):
        notes.append(f"Wave 3 = 2.618× Wave 1 ✓ (extended wave)")
    elif is_fib_ratio(w3_ratio, 1.0):
        notes.append(f"Wave 3 ≈ Wave 1 length")

    # ── Guideline: Wave 4 Fibonacci retracement ─────────────────────────────
    w4_retrace = w4.length / w3.length if w3.length > 0 else 0
    if is_fib_ratio(w4_retrace, 0.382):
        score_components.append(1.0)
        notes.append(f"Wave 4 retraces 38.2% of Wave 3 ✓")
    elif is_fib_ratio(w4_retrace, 0.236):
        score_components.append(0.8)
        notes.append(f"Wave 4 retraces 23.6% of Wave 3 (shallow)")
    elif is_fib_ratio(w4_retrace, 0.5):
        score_components.append(0.7)
        notes.append(f"Wave 4 retraces 50% of Wave 3 (deep)")
    else:
        score_components.append(0.5)
        notes.append(f"Wave 4 retraces {w4_retrace:.1%} of Wave 3 (non-Fibonacci)")

    # ── Guideline: Wave 5 vs Wave 1 equality ─────────────────────────────────
    if w1.length > 0:
        w5_ratio = w5.length / w1.length
        if is_fib_ratio(w5_ratio, 1.0):
            score_components.append(1.0)
            notes.append(f"Wave 5 ≈ Wave 1 length ✓ (equality)")
        elif is_fib_ratio(w5_ratio, 0.618):
            score_components.append(0.9)
            notes.append(f"Wave 5 = 0.618× Wave 1 ✓")
        elif is_fib_ratio(w5_ratio, 1.618):
            score_components.append(0.9)
            notes.append(f"Wave 5 = 1.618× Wave 1 ✓ (extended)")
        else:
            score_components.append(0.5)

    # ── Guideline: Alternation (Waves 2 and 4 differ in character) ───────────
    # A simple proxy: if one is shallow and one is deep they alternate
    if abs(w2_retrace - w4_retrace) > 0.10:
        notes.append("Alternation: Wave 2 and Wave 4 differ in depth ✓")
        score_components.append(0.9)
    else:
        notes.append("No clear alternation between Wave 2 and Wave 4")
        score_components.append(0.6)

    # ── Extended wave identification ─────────────────────────────────────────
    max_motive = max(motive_lengths)
    if w1.length == max_motive:
        notes.append("Wave 1 extension detected")
    elif w3.length == max_motive:
        notes.append("Wave 3 extension detected (most common)")
    else:
        notes.append("Wave 5 extension detected")

    # ── Final confidence score ────────────────────────────────────────────────
    if violations:
        confidence = 0.0 if len(violations) >= 2 else 0.15
    else:
        confidence = sum(score_components) / len(score_components) if score_components else 0.5

    return confidence, violations, notes


# ═══════════════════════════════════════════════════════════
#  CORRECTIVE PATTERNS
# ═══════════════════════════════════════════════════════════

def validate_zigzag(waves: List[Wave]) -> Tuple[float, List[str], List[str]]:
    """
    Validate a 3-wave zigzag correction (A-B-C).
    Structure: 5-3-5 (A is impulse, B is corrective, C is impulse)
    Wave C = Wave A, or 0.618/1.618× Wave A
    Wave B retraces 38.2%–78.6% of Wave A
    """
    if len(waves) != 3:
        return 0.0, ["Zigzag needs exactly 3 waves (A-B-C)"], []

    wA, wB, wC = waves
    violations: List[str] = []
    notes:      List[str] = []
    score_parts: List[float] = []

    # Wave B retracement of A
    b_retrace = wB.length / wA.length if wA.length > 0 else 0
    if b_retrace > 1.0:
        violations.append(f"ZZ: Wave B ({b_retrace:.1%}) exceeds Wave A — not a valid zigzag")
        score_parts.append(0.0)
    elif 0.382 <= b_retrace <= 0.786:
        score_parts.append(1.0)
        notes.append(f"Wave B retraces {b_retrace:.1%} of Wave A ✓")
    else:
        score_parts.append(0.5)
        notes.append(f"Wave B retraces {b_retrace:.1%} of Wave A (outside typical zone)")

    # Wave C vs Wave A
    c_ratio = wC.length / wA.length if wA.length > 0 else 0
    if is_fib_ratio(c_ratio, 1.0):
        score_parts.append(1.0)
        notes.append("Wave C = Wave A ✓ (equality)")
    elif is_fib_ratio(c_ratio, 0.618):
        score_parts.append(0.9)
        notes.append("Wave C = 0.618× Wave A ✓")
    elif is_fib_ratio(c_ratio, 1.618):
        score_parts.append(0.9)
        notes.append("Wave C = 1.618× Wave A ✓ (extended)")
    else:
        score_parts.append(0.5)
        notes.append(f"Wave C = {c_ratio:.3f}× Wave A")

    confidence = sum(score_parts) / len(score_parts) if score_parts else 0.5
    return confidence, violations, notes


def validate_flat(waves: List[Wave]) -> Tuple[float, List[str], List[str]]:
    """
    Validate a 3-wave flat correction (A-B-C).
    Structure: 3-3-5
    Wave B retraces 90%–100%+ of Wave A (key distinguishing feature)
    Wave C ≈ Wave A
    """
    if len(waves) != 3:
        return 0.0, ["Flat needs exactly 3 waves (A-B-C)"], []

    wA, wB, wC = waves
    violations: List[str] = []
    notes:      List[str] = []
    score_parts: List[float] = []

    b_retrace = wB.length / wA.length if wA.length > 0 else 0

    # Flat: Wave B must retrace nearly all of Wave A (90%–105%)
    if 0.90 <= b_retrace <= 1.05:
        score_parts.append(1.0)
        notes.append(f"Wave B retraces {b_retrace:.1%} of Wave A ✓ (flat signature)")
    elif b_retrace > 1.05:
        score_parts.append(0.8)
        notes.append(f"Wave B exceeds Wave A ({b_retrace:.1%}) — Expanded Flat")
    else:
        violations.append(f"FLAT: Wave B only retraces {b_retrace:.1%} of A (need ≥90%)")
        score_parts.append(0.0)

    c_ratio = wC.length / wA.length if wA.length > 0 else 0
    if is_fib_ratio(c_ratio, 1.0):
        score_parts.append(1.0)
        notes.append("Wave C = Wave A ✓")
    elif is_fib_ratio(c_ratio, 1.618):
        score_parts.append(0.9)
        notes.append("Wave C = 1.618× Wave A (expanded)")
    else:
        score_parts.append(0.5)

    confidence = sum(score_parts) / len(score_parts)
    return confidence, violations, notes


def validate_triangle(waves: List[Wave]) -> Tuple[float, List[str], List[str]]:
    """
    Validate a 5-wave triangle (A-B-C-D-E).
    Structure: 3-3-3-3-3 (all sub-waves are corrections)
    Each successive wave is shorter (contracting) or longer (expanding).
    """
    if len(waves) != 5:
        return 0.0, ["Triangle needs exactly 5 waves (A-B-C-D-E)"], []

    violations: List[str] = []
    notes:      List[str] = []
    score_parts: List[float] = []

    lengths = [w.length for w in waves]
    # Contracting triangle: each wave shorter than prior
    contracting = all(lengths[i] > lengths[i+1] for i in range(len(lengths)-1))
    # Expanding: each wave longer (rare)
    expanding   = all(lengths[i] < lengths[i+1] for i in range(len(lengths)-1))

    if contracting:
        score_parts.append(1.0)
        notes.append("Contracting triangle ✓ (most common)")
    elif expanding:
        score_parts.append(0.8)
        notes.append("Expanding triangle (rare)")
    else:
        # Partial convergence
        score_parts.append(0.5)
        notes.append("Irregular triangle — partial convergence")

    # Wave E < Wave C < Wave A (typical)
    if lengths[0] > lengths[2] > lengths[4]:
        score_parts.append(1.0)
        notes.append("A > C > E ✓")
    else:
        score_parts.append(0.4)

    confidence = sum(score_parts) / len(score_parts)
    return confidence, violations, notes


def classify_pattern(waves: List[Wave]) -> Tuple[str, float, List[str], List[str]]:
    """
    Attempt to classify a wave sequence into the best-fitting Elliott pattern.

    Returns
    -------
    (pattern_type, confidence, violations, notes)
    """
    n = len(waves)

    if n == 5:
        # Try impulse and triangle
        imp_conf, imp_viol, imp_notes = validate_impulse(waves)
        tri_conf, tri_viol, tri_notes = validate_triangle(waves)
        if imp_conf >= tri_conf:
            return "IMPULSE", imp_conf, imp_viol, imp_notes
        else:
            return "TRIANGLE", tri_conf, tri_viol, tri_notes

    elif n == 3:
        # Try zigzag vs flat
        zz_conf,  zz_viol,  zz_notes  = validate_zigzag(waves)
        flat_conf, flat_viol, flat_notes = validate_flat(waves)
        if zz_conf >= flat_conf:
            return "ZIGZAG", zz_conf, zz_viol, zz_notes
        else:
            return "FLAT", flat_conf, flat_viol, flat_notes

    else:
        return "UNKNOWN", 0.0, [f"No standard EW pattern for {n} waves"], []

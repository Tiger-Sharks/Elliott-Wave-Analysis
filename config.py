"""
Elliott Wave Principle - Configuration & Constants
Based on: "Elliott Wave Principle: Key to Market Behavior" by Frost & Prechter
"""

# ─── Fibonacci Ratios ───────────────────────────────────────────────────────
PHI = 1.6180339887          # Golden Ratio
PHI_INV = 0.6180339887      # 1/PHI  (phi - 1)
PHI_SQ = 2.6180339887       # PHI²

FIBONACCI_RATIOS = [
    0.236,  # PHI^-4 approx
    0.382,  # PHI^-2 approx (1 - 0.618)
    0.500,  # 50% midpoint
    0.618,  # PHI^-1 (most important)
    0.786,  # sqrt(0.618)
    1.000,
    1.272,  # sqrt(1.618)
    1.618,  # PHI
    2.000,
    2.618,  # PHI²
    4.236,  # PHI³
]

# ─── Wave 2 Retracement Rules (must retrace Wave 1) ─────────────────────────
# From book: "Wave 2 corrects wave 1 but never beyond its start"
WAVE2_RETRACE_MIN = 0.236   # Minimum retracement of Wave 1
WAVE2_RETRACE_MAX = 0.999   # Cannot retrace 100% of Wave 1
WAVE2_TYPICAL_MIN = 0.382
WAVE2_TYPICAL_MAX = 0.786

# ─── Wave 3 Rules ───────────────────────────────────────────────────────────
# From book: "Wave 3 is NEVER the shortest impulse wave"
# Typical: Wave 3 = 1.618 × Wave 1
WAVE3_MIN_RATIO = 1.0       # Wave 3 must be at least as long as shortest of W1/W5
WAVE3_TYPICAL_RATIO = 1.618

# ─── Wave 4 Rules ───────────────────────────────────────────────────────────
# From book: "Wave 4 price territory does not overlap Wave 1 price territory"
# Typical retracement: 38.2% of Wave 3
WAVE4_RETRACE_MIN = 0.236
WAVE4_RETRACE_MAX = 0.500   # Rarely exceeds 50% of Wave 3
WAVE4_TYPICAL = 0.382

# ─── Wave 5 Rules ───────────────────────────────────────────────────────────
# Typical: Wave 5 ≈ Wave 1, or 0.618 × Wave 1, or 1.618 × Wave 1
WAVE5_TYPICAL_RATIOS = [0.618, 1.0, 1.618]

# ─── Corrective Wave Rules ───────────────────────────────────────────────────
# Zigzag (5-3-5): Wave C = Wave A, or 1.618 × A
# Flat (3-3-5): Wave B retraces 90-100% of A; C = A
# Triangle (3-3-3-3-3): converging trendlines
ZIGZAG_C_RATIOS = [0.618, 1.0, 1.618]
FLAT_B_RETRACE_MIN = 0.90
FLAT_B_RETRACE_MAX = 1.05

# ─── Pivot Detection ─────────────────────────────────────────────────────────
# ZigZag threshold - minimum % move to count as a swing
DEFAULT_ZIGZAG_THRESHOLD = 0.05   # 5% default, adjustable

# ─── Tolerance for ratio matching ────────────────────────────────────────────
RATIO_TOLERANCE = 0.10   # ±10% tolerance when checking Fibonacci ratios

# ─── Wave Degree Labels (from book, largest to smallest) ─────────────────────
WAVE_DEGREES = [
    "Grand Supercycle",
    "Supercycle",
    "Cycle",
    "Primary",
    "Intermediate",
    "Minor",
    "Minute",
    "Minuette",
    "Subminuette",
]

# ─── Pattern Confidence Thresholds ───────────────────────────────────────────
CONFIDENCE_HIGH   = 0.80
CONFIDENCE_MEDIUM = 0.60
CONFIDENCE_LOW    = 0.40

"""
Wave Data Structures
Defines Wave, WavePattern, and related types used throughout the framework.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pivots import Pivot


@dataclass
class Wave:
    """A single Elliott Wave (one leg between two pivots)."""
    label: str                      # e.g. "1", "2", "3", "4", "5", "A", "B", "C"
    start: Pivot                    # Starting pivot
    end:   Pivot                    # Ending pivot
    direction: str = ""             # "UP" or "DOWN"
    length: float = 0.0             # Absolute price length
    retrace_ratio: float = 0.0      # Retrace vs previous wave (0 if not applicable)
    fib_score: float = 0.0          # Fibonacci alignment score 0.0–1.0
    sub_waves: List["Wave"] = field(default_factory=list)

    def __post_init__(self):
        self.length    = abs(self.end.price - self.start.price)
        self.direction = "UP" if self.end.price > self.start.price else "DOWN"

    def __repr__(self):
        return (f"Wave({self.label}: {self.start.price:.2f}→{self.end.price:.2f} "
                f"[{self.direction}, len={self.length:.2f}])")


@dataclass
class WavePattern:
    """
    A complete identified Elliott Wave pattern.
    Could be an Impulse (5 waves) or Corrective (3 or 5 waves).
    """
    pattern_type: str           # "IMPULSE", "ZIGZAG", "FLAT", "TRIANGLE", "DIAGONAL"
    waves: List[Wave]           # The individual waves in the pattern
    confidence: float = 0.0    # 0.0 – 1.0
    degree: str = "Minor"       # Wave degree (from WAVE_DEGREES)
    violations: List[str] = field(default_factory=list)   # Rule violations
    notes: List[str]    = field(default_factory=list)     # Notable observations

    @property
    def start_price(self) -> float:
        return self.waves[0].start.price if self.waves else 0.0

    @property
    def end_price(self) -> float:
        return self.waves[-1].end.price if self.waves else 0.0

    @property
    def start_date(self):
        return self.waves[0].start.date if self.waves else None

    @property
    def end_date(self):
        return self.waves[-1].end.date if self.waves else None

    @property
    def is_bullish(self) -> bool:
        if not self.waves:
            return True
        return self.waves[0].direction == "UP"

    def __repr__(self):
        return (f"WavePattern({self.pattern_type}, "
                f"confidence={self.confidence:.0%}, "
                f"waves={len(self.waves)}, "
                f"violations={len(self.violations)})")


@dataclass
class AnalysisResult:
    """
    Top-level result of a full Elliott Wave analysis on a price series.
    """
    symbol: str
    timeframe: str
    patterns: List[WavePattern] = field(default_factory=list)
    best_pattern: Optional[WavePattern] = None
    current_wave_label: str = "?"       # Estimated current wave position
    next_targets: List[float] = field(default_factory=list)   # Price targets
    invalidation_level: float = 0.0    # Level that would invalidate the count
    summary: str = ""

    def __repr__(self):
        return (f"AnalysisResult({self.symbol}, "
                f"patterns={len(self.patterns)}, "
                f"best={self.best_pattern})")

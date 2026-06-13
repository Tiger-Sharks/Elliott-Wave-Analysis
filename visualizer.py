"""
Visualization Module - All charts using FREE matplotlib
Plots price data, pivot points, Elliott Wave labels, Fibonacci levels.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   # Non-interactive backend (works everywhere)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from typing import List, Optional

from pivots import Pivot, pivots_to_series
from waves  import WavePattern, AnalysisResult
from fibonacci import fib_retracement_levels


# ─── Color scheme ─────────────────────────────────────────────────────────────
COLORS = {
    "bg":         "#0d1117",
    "price":      "#58a6ff",
    "pivot_high": "#f85149",
    "pivot_low":  "#3fb950",
    "wave_bull":  "#3fb950",
    "wave_bear":  "#f85149",
    "fib":        "#e3b341",
    "wave_line":  "#d2a8ff",
    "label":      "#ffffff",
    "grid":       "#21262d",
    "target":     "#58a6ff",
    "invalidate": "#f85149",
}

WAVE_LABEL_COLORS = {
    "1": "#3fb950", "2": "#f85149", "3": "#3fb950",
    "4": "#f85149", "5": "#3fb950",
    "A": "#e3b341", "B": "#e3b341", "C": "#e3b341",
    "D": "#e3b341", "E": "#e3b341",
}


def _setup_dark_axis(ax, title: str = ""):
    ax.set_facecolor(COLORS["bg"])
    ax.tick_params(colors=COLORS["label"], labelsize=8)
    ax.xaxis.label.set_color(COLORS["label"])
    ax.yaxis.label.set_color(COLORS["label"])
    for spine in ax.spines.values():
        spine.set_edgecolor(COLORS["grid"])
    ax.grid(True, color=COLORS["grid"], linewidth=0.5, alpha=0.7)
    if title:
        ax.set_title(title, color=COLORS["label"], fontsize=11, fontweight="bold", pad=8)


def plot_analysis(
    df: pd.DataFrame,
    result: AnalysisResult,
    pivots: List[Pivot],
    output_path: Optional[str] = None,
    show: bool = False,
) -> str:
    """
    Master chart: price + wave labels + Fibonacci levels + targets.

    Parameters
    ----------
    df          : OHLCV DataFrame
    result      : AnalysisResult from detector.analyze()
    pivots      : Detected pivot points
    output_path : Where to save the PNG. Auto-generated if None.
    show        : Whether to call plt.show() (False for headless)

    Returns path to saved PNG.
    """
    fig = plt.figure(figsize=(16, 9), facecolor=COLORS["bg"])
    fig.patch.set_facecolor(COLORS["bg"])

    # ── Layout: main chart (top 70%) + info panel (bottom 30%) ────────────
    ax_main  = fig.add_axes([0.05, 0.32, 0.90, 0.62])
    ax_info  = fig.add_axes([0.05, 0.02, 0.90, 0.26])

    # ── 1. Price line ──────────────────────────────────────────────────────
    _setup_dark_axis(ax_main, f"Elliott Wave Analysis  |  {result.symbol}  |  {result.timeframe}")
    dates = df.index
    ax_main.plot(dates, df["Close"], color=COLORS["price"],
                 linewidth=1.2, alpha=0.8, label="Close", zorder=2)

    # ── 2. Pivot markers ───────────────────────────────────────────────────
    for p in pivots:
        if p.bar_index < len(df):
            date   = df.index[p.bar_index]
            color  = COLORS["pivot_high"] if p.pivot_type == "HIGH" else COLORS["pivot_low"]
            marker = "v" if p.pivot_type == "HIGH" else "^"
            ax_main.scatter(date, p.price, color=color, marker=marker,
                            s=60, zorder=5, alpha=0.9)

    # ── 3. Wave pattern lines + labels ─────────────────────────────────────
    if result.best_pattern:
        bp = result.best_pattern
        color = COLORS["wave_bull"] if bp.is_bullish else COLORS["wave_bear"]

        prev_date  = None
        prev_price = None
        for wave in bp.waves:
            s_date = wave.start.date
            e_date = wave.end.date
            s_px   = wave.start.price
            e_px   = wave.end.price

            # Draw wave line
            ax_main.plot([s_date, e_date], [s_px, e_px],
                         color=COLORS["wave_line"], linewidth=2.0,
                         linestyle="--", alpha=0.85, zorder=4)

            # Wave label at pivot
            mid_date = s_date + (e_date - s_date) / 2
            mid_px   = (s_px + e_px) / 2
            lbl_color = WAVE_LABEL_COLORS.get(wave.label, COLORS["label"])
            ax_main.annotate(
                wave.label,
                xy=(e_date, e_px),
                xytext=(0, 14 if wave.end.pivot_type == "HIGH" else -20),
                textcoords="offset points",
                fontsize=12, fontweight="bold", color=lbl_color,
                ha="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.2", facecolor=COLORS["bg"],
                          edgecolor=lbl_color, alpha=0.85),
            )

    # ── 4. Fibonacci retracement levels ────────────────────────────────────
    if result.best_pattern and len(result.best_pattern.waves) >= 1:
        w0 = result.best_pattern.waves[0]
        high = max(w0.start.price, w0.end.price)
        low  = min(w0.start.price, w0.end.price)
        fib_levels = fib_retracement_levels(high, low)
        for ratio, level in fib_levels.items():
            ax_main.axhline(level, color=COLORS["fib"], linewidth=0.6,
                            linestyle=":", alpha=0.55, zorder=1)
            ax_main.annotate(
                f"Fib {ratio:.3f}",
                xy=(df.index[-1], level),
                xytext=(4, 2), textcoords="offset points",
                fontsize=7, color=COLORS["fib"], alpha=0.7,
            )

    # ── 5. Price targets ───────────────────────────────────────────────────
    for i, tgt in enumerate(result.next_targets[:3]):
        ax_main.axhline(tgt, color=COLORS["target"], linewidth=0.8,
                        linestyle="-.", alpha=0.6)
        ax_main.annotate(
            f"T{i+1}: {tgt:.2f}",
            xy=(df.index[-1], tgt),
            xytext=(4, 2), textcoords="offset points",
            fontsize=8, color=COLORS["target"],
        )

    # ── 6. Invalidation level ──────────────────────────────────────────────
    if result.invalidation_level:
        ax_main.axhline(result.invalidation_level,
                        color=COLORS["invalidate"], linewidth=0.9,
                        linestyle="--", alpha=0.55)
        ax_main.annotate(
            f"Invalidation: {result.invalidation_level:.2f}",
            xy=(df.index[-1], result.invalidation_level),
            xytext=(4, 2), textcoords="offset points",
            fontsize=8, color=COLORS["invalidate"],
        )

    ax_main.set_ylabel("Price", color=COLORS["label"])

    # ── 7. Info panel ──────────────────────────────────────────────────────
    _setup_dark_axis(ax_info)
    ax_info.axis("off")

    lines = []
    if result.best_pattern:
        bp = result.best_pattern
        lines.append(f"  Pattern : {bp.pattern_type}    |    "
                     f"Confidence : {bp.confidence:.0%}    |    "
                     f"Direction : {'Bullish ▲' if bp.is_bullish else 'Bearish ▼'}")
        lines.append(f"  Current Wave : {result.current_wave_label}    |    "
                     f"Degree : {bp.degree}    |    "
                     f"Violations : {len(bp.violations)}")
        lines.append("")
        if bp.violations:
            lines.append("  ⚠  RULE VIOLATIONS:")
            for v in bp.violations:
                lines.append(f"     • {v}")
            lines.append("")
        if bp.notes:
            lines.append("  NOTES:")
            for n in bp.notes[:5]:
                lines.append(f"     • {n}")
        lines.append("")
        if result.next_targets:
            tgt_str = "  |  ".join(f"T{i+1}: {t:.2f}" for i, t in enumerate(result.next_targets[:3]))
            lines.append(f"  Targets  →  {tgt_str}")
    else:
        lines.append(f"  {result.summary}")

    for i, line in enumerate(lines[:10]):
        ax_info.text(
            0.01, 0.95 - i * 0.09, line,
            transform=ax_info.transAxes,
            color=COLORS["label"] if not line.startswith("  ⚠") else COLORS["pivot_high"],
            fontsize=8.5, verticalalignment="top", fontfamily="monospace",
        )

    # ── 8. Legend ──────────────────────────────────────────────────────────
    legend_elements = [
        Line2D([0], [0], color=COLORS["price"],      lw=1.5, label="Price"),
        Line2D([0], [0], color=COLORS["wave_line"],  lw=2, ls="--", label="Wave"),
        Line2D([0], [0], color=COLORS["fib"],        lw=1, ls=":", label="Fibonacci"),
        Line2D([0], [0], color=COLORS["target"],     lw=1, ls="-.", label="Target"),
        Line2D([0], [0], color=COLORS["invalidate"], lw=1, ls="--", label="Invalidation"),
    ]
    ax_main.legend(handles=legend_elements, loc="upper left",
                   facecolor=COLORS["bg"], edgecolor=COLORS["grid"],
                   labelcolor=COLORS["label"], fontsize=8)

    # ── 9. Save ────────────────────────────────────────────────────────────
    if output_path is None:
        ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/tiger/Documents/Ellie/elliott_wave/outputs/{result.symbol}_{ts}_ew.png"

    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=COLORS["bg"])
    if show:
        plt.show()
    plt.close(fig)
    return output_path


def plot_pivots_only(
    df: pd.DataFrame,
    pivots: List[Pivot],
    symbol: str = "",
    output_path: Optional[str] = None,
) -> str:
    """Quick chart showing just the ZigZag pivots on price."""
    fig, ax = plt.subplots(figsize=(14, 6), facecolor=COLORS["bg"])
    fig.patch.set_facecolor(COLORS["bg"])
    _setup_dark_axis(ax, f"ZigZag Pivots  |  {symbol}")

    ax.plot(df.index, df["Close"], color=COLORS["price"],
            linewidth=1.0, alpha=0.7, label="Close")

    # Connect pivots with zigzag line
    px = [df.index[p.bar_index] for p in pivots if p.bar_index < len(df)]
    py = [p.price for p in pivots if p.bar_index < len(df)]
    ax.plot(px, py, color=COLORS["wave_line"], linewidth=1.5,
            linestyle="--", alpha=0.8, label="ZigZag")

    for p in pivots:
        if p.bar_index >= len(df):
            continue
        d = df.index[p.bar_index]
        c = COLORS["pivot_high"] if p.pivot_type == "HIGH" else COLORS["pivot_low"]
        m = "v" if p.pivot_type == "HIGH" else "^"
        ax.scatter(d, p.price, color=c, marker=m, s=70, zorder=5)

    ax.set_ylabel("Price", color=COLORS["label"])
    ax.legend(facecolor=COLORS["bg"], edgecolor=COLORS["grid"],
              labelcolor=COLORS["label"], fontsize=9)

    if output_path is None:
        ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/mnt/user-data/outputs/{symbol}_{ts}_pivots.png"

    plt.savefig(output_path, dpi=130, bbox_inches="tight",
                facecolor=COLORS["bg"])
    plt.close(fig)
    return output_path


def plot_fibonacci_levels(
    high: float,
    low: float,
    current_price: float,
    symbol: str = "",
    output_path: Optional[str] = None,
) -> str:
    """Standalone Fibonacci retracement chart."""
    fig, ax = plt.subplots(figsize=(8, 7), facecolor=COLORS["bg"])
    fig.patch.set_facecolor(COLORS["bg"])
    _setup_dark_axis(ax, f"Fibonacci Levels  |  {symbol}")

    levels = fib_retracement_levels(high, low)
    y_positions = list(levels.values())
    labels      = [f"{r:.3f}  ({v:.2f})" for r, v in levels.items()]

    for i, (ratio, price) in enumerate(levels.items()):
        alpha = 0.9 if abs(current_price - price) / high < 0.05 else 0.5
        ax.axhline(price, color=COLORS["fib"], linewidth=1.5, alpha=alpha)
        ax.text(0.02, price, f"  {ratio:.3f} — {price:.2f}",
                color=COLORS["fib"], fontsize=9, va="center",
                transform=ax.get_yaxis_transform())

    ax.axhline(high, color=COLORS["pivot_high"], linewidth=2, label=f"High: {high:.2f}")
    ax.axhline(low,  color=COLORS["pivot_low"],  linewidth=2, label=f"Low:  {low:.2f}")
    ax.axhline(current_price, color=COLORS["price"], linewidth=1.5,
               linestyle="--", label=f"Current: {current_price:.2f}")

    ax.set_xlim(0, 1)
    ax.set_ylim(low * 0.97, high * 1.03)
    ax.set_ylabel("Price", color=COLORS["label"])
    ax.legend(facecolor=COLORS["bg"], edgecolor=COLORS["grid"],
              labelcolor=COLORS["label"], fontsize=9)

    if output_path is None:
        ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/mnt/user-data/outputs/{symbol}_{ts}_fib.png"

    plt.savefig(output_path, dpi=130, bbox_inches="tight",
                facecolor=COLORS["bg"])
    plt.close(fig)
    return output_path

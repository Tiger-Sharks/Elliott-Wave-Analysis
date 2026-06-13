"""
Elliott Wave Auto-Detector — CLI Entry Point
============================================
Completely FREE. No API keys. No paid subscriptions.
Data from Yahoo Finance via yfinance.

USAGE EXAMPLES
--------------
# Analyze Apple daily chart
python main.py --symbol AAPL --period 1y --interval 1d

# Bitcoin on weekly bars
python main.py --symbol BTC-USD --period 2y --interval 1wk

# S&P 500 with custom date range
python main.py --symbol ^GSPC --start 2022-01-01 --end 2024-01-01

# Increase sensitivity (detect more small waves)
python main.py --symbol TSLA --threshold 0.03

# Save chart to a specific path
python main.py --symbol EURUSD=X --output /tmp/eur_usd_ew.png
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import argparse
import traceback

from data       import fetch_ohlcv, get_symbol_info, POPULAR_SYMBOLS
from pivots     import detect_pivots
from detector   import analyze
from visualizer import plot_analysis, plot_pivots_only
from config     import DEFAULT_ZIGZAG_THRESHOLD, CONFIDENCE_MEDIUM


# ──────────────────────────────────────────────────────────────────────────────
def print_banner():
    print("\n" + "═" * 65)
    print("  ELLIOTT WAVE AUTO-DETECTOR  |  Based on Frost & Prechter")
    print("  FREE — Powered by yfinance (Yahoo Finance)")
    print("═" * 65 + "\n")


def print_result(result):
    """Pretty-print the analysis result to console."""
    print(f"\n{'─'*65}")
    print(f"  SYMBOL    : {result.symbol}")
    print(f"  TIMEFRAME : {result.timeframe}")
    print(f"{'─'*65}")
    print(f"  SUMMARY   : {result.summary}")

    if result.best_pattern:
        bp = result.best_pattern
        print(f"\n  ┌── BEST PATTERN ──────────────────────────────────────")
        print(f"  │  Type       : {bp.pattern_type}")
        print(f"  │  Confidence : {bp.confidence:.0%}")
        print(f"  │  Direction  : {'Bullish ▲' if bp.is_bullish else 'Bearish ▼'}")
        print(f"  │  Degree     : {bp.degree}")
        print(f"  │  From       : {bp.start_date.date() if bp.start_date else 'N/A'}")
        print(f"  │  To         : {bp.end_date.date()   if bp.end_date   else 'N/A'}")
        print(f"  │  Waves      : {len(bp.waves)}")
        print(f"  └──────────────────────────────────────────────────────")

        if bp.violations:
            print(f"\n  ⚠  RULE VIOLATIONS ({len(bp.violations)}):")
            for v in bp.violations:
                print(f"     ✗  {v}")
        else:
            print("\n  ✓  No rule violations — pattern is valid")

        if bp.notes:
            print(f"\n  NOTES:")
            for n in bp.notes:
                print(f"     •  {n}")

        print(f"\n  INDIVIDUAL WAVES:")
        for w in bp.waves:
            dirstr = "↑" if w.direction == "UP" else "↓"
            print(f"     Wave {w.label} {dirstr}  "
                  f"{w.start.price:.4f} → {w.end.price:.4f}  "
                  f"len={w.length:.4f}  "
                  f"({w.start.date.date()} → {w.end.date.date()})")

        print(f"\n  CURRENT POSITION  : Wave {result.current_wave_label}")

        if result.next_targets:
            print(f"\n  PRICE TARGETS:")
            for i, t in enumerate(result.next_targets[:3]):
                print(f"     T{i+1}  →  {t:.4f}")

        if result.invalidation_level:
            print(f"\n  INVALIDATION LEVEL : {result.invalidation_level:.4f}")

    print(f"\n  OTHER PATTERNS FOUND : {len(result.patterns)}")
    for i, pat in enumerate(result.patterns[:5]):
        print(f"     {i+1}. {pat.pattern_type:12s}  "
              f"conf={pat.confidence:.0%}  "
              f"{'Bullish' if pat.is_bullish else 'Bearish'}  "
              f"viol={len(pat.violations)}  "
              f"({pat.start_date.date() if pat.start_date else '?'} → "
              f"{pat.end_date.date() if pat.end_date else '?'})")
    print()


# ──────────────────────────────────────────────────────────────────────────────
def run_analysis(
    symbol: str,
    period: str       = "1y",
    interval: str     = "1d",
    start: str        = None,
    end: str          = None,
    threshold: float  = DEFAULT_ZIGZAG_THRESHOLD,
    min_conf: float   = CONFIDENCE_MEDIUM,
    output: str       = None,
    no_chart: bool    = False,
    degree: str       = "Minor",
):
    print_banner()

    # Resolve shorthand names
    symbol = POPULAR_SYMBOLS.get(symbol.upper(), symbol)

    print(f"  Fetching data for {symbol}  |  period={period}  |  interval={interval}")
    df   = fetch_ohlcv(symbol, period=period, interval=interval, start=start, end=end)
    info = get_symbol_info(symbol)
    print(f"  {info['name']}  |  {len(df)} bars loaded  |  "
          f"{df.index[0].date()} → {df.index[-1].date()}")

    # Map interval to human-readable timeframe
    TF_MAP = {
        "1d": "Daily", "1wk": "Weekly", "1mo": "Monthly",
        "1h": "Hourly", "4h": "4H", "15m": "15min",
        "5m": "5min", "1m": "1min",
    }
    timeframe = TF_MAP.get(interval, interval)

    print(f"\n  Detecting pivots  (zigzag threshold = {threshold:.1%}) ...")
    pivots = detect_pivots(df, threshold=threshold)
    print(f"  Found {len(pivots)} pivot points")

    print(f"\n  Running Elliott Wave analysis ...")
    result = analyze(
        df,
        symbol           = symbol,
        timeframe        = timeframe,
        zigzag_threshold = threshold,
        min_confidence   = min_conf,
        degree           = degree,
    )

    print_result(result)

    if not no_chart:
        print("  Generating chart ...")
        chart_path = plot_analysis(df, result, pivots, output_path=output)
        print(f"  Chart saved → {chart_path}\n")
        return result, chart_path

    return result, None


# ──────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Auto Elliott Wave Detector (FREE) — Frost & Prechter Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--symbol",    default="^GSPC",  help="Ticker symbol (default: ^GSPC)")
    parser.add_argument("--period",    default="1y",     help="Period: 1d 5d 1mo 3mo 6mo 1y 2y 5y 10y max")
    parser.add_argument("--interval",  default="1D",     help="Bar interval: 1m 5m 15m 1h 1d 1wk 1mo")
    parser.add_argument("--start",     default=None,     help="Start date YYYY-MM-DD (overrides period)")
    parser.add_argument("--end",       default=None,     help="End date   YYYY-MM-DD")
    parser.add_argument("--threshold", default=0.05, type=float,
                        help="ZigZag threshold 0.01–0.20 (default 0.05 = 5%%)")
    parser.add_argument("--min-conf",  default=0.50, type=float,
                        help="Min confidence to show a pattern (default 0.50)")
    parser.add_argument("--output",    default=None,     help="Output PNG path")
    parser.add_argument("--no-chart",  action="store_true", help="Skip chart generation")
    parser.add_argument("--degree",    default="Minor",
                        choices=["Grand Supercycle","Supercycle","Cycle","Primary",
                                 "Intermediate","Minor","Minute","Minuette","Subminuette"],
                        help="Wave degree label")

    args = parser.parse_args()

    try:
        run_analysis(
            symbol    = args.symbol,
            period    = args.period,
            interval  = args.interval,
            start     = args.start,
            end       = args.end,
            threshold = args.threshold,
            min_conf  = args.min_conf,
            output    = args.output,
            no_chart  = args.no_chart,
            degree    = args.degree,
        )
    except Exception as e:
        print(f"\n  ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

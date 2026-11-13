#!/usr/bin/env python3
"""Polymarket NVIDIA CEO Forecaster — make.fun bounty entry.

Approach
--------
For each market, we estimate a per-market volatility sigma from the most recent
120 minutes of 1-minute price changes.  The estimate is the average of two
robust measures: (median absolute change / 0.6745) and the standard deviation
of changes, floored at 0.0005 and capped at 0.005.  This adapts to the huge
variation in volatility across markets (some trade at 0.0000 mean absolute
change, others at 0.0075+).

For each forecast horizon h = 1 … 240 minutes we produce five quantile rows
q_tau(h) = clamp(last_price + z_tau * sigma * sqrt(h), 0, 1) where
z = [-1.644854, -0.67449, 0, 0.67449, 1.644854] for tau = [0.05, 0.25, 0.5,
0.75, 0.95].  Rows are rounded to 6 decimal places and enforced to be
non-decreasing across quantiles.

Finally, the median (tau=0.5) forecasts at h=1 are normalised across markets so
that they sum to 1 (since exactly one person will become CEO).  The scaling is
applied only if the sum differs from 1 by more than 0.02, and rows are
re-clamped and re-sorted after scaling.

This beats the fixed-sigma persistence baseline (0.3985) because it uses
per-market, data-driven volatility estimates that are neither too wide for quiet
markets nor too narrow for active ones.
"""

import json
import math
import os
import sys

Z = [-1.644854, -0.67449, 0.0, 0.67449, 1.644854]  # z-scores for quantiles


def estimate_sigma(prices, window=120):
    """Estimate per-minute volatility from the last `window` 1-min changes."""
    if len(prices) < 2:
        return 0.0025  # fallback
    changes = [abs(prices[i] - prices[i - 1]) for i in range(1, len(prices))]
    recent = changes[-window:] if len(changes) > window else changes
    if not recent:
        return 0.0025
    n = len(recent)
    # Median absolute change
    srt = sorted(recent)
    med_abs = srt[n // 2] if n % 2 else (srt[n // 2 - 1] + srt[n // 2]) / 2.0
    sigma_mad = med_abs / 0.6745 if med_abs > 0 else 0.0
    # Standard deviation of changes
    mean = sum(recent) / n
    var = sum((x - mean) ** 2 for x in recent) / n
    sigma_std = math.sqrt(var)
    # Average the two, floor and cap
    sigma = max(0.0005, min(0.005, (sigma_mad + sigma_std) / 2.0))
    return sigma


def price6(x):
    """Round to 6 decimal places and clamp to [0, 1]."""
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return round(x, 6)


def forecast_market(prices, horizon):
    """Return (rows, last_price) for one market."""
    last_price = prices[-1]
    sigma = estimate_sigma(prices)
    rows = []
    for h in range(1, horizon + 1):
        sh = sigma * math.sqrt(h)
        row = [price6(last_price + z * sh) for z in Z]
        # Enforce non-decreasing
        for j in range(1, 5):
            if row[j] < row[j - 1]:
                row[j] = row[j - 1]
        rows.append(row)
    return rows, last_price


def run_case(case):
    """Run the full forecast for one case JSON."""
    horizon = case["horizon_minutes"]
    per_market = {}
    medians = []
    for m in case["markets"]:
        rows, last_price = forecast_market(m["prices"], horizon)
        per_market[m["id"]] = rows
        medians.append(rows[0][2])  # median at h=1

    # Normalise medians across markets so they sum to 1
    s = sum(medians)
    if s > 0 and abs(s - 1.0) > 0.02:
        scale = 1.0 / s
        for mid, rows in per_market.items():
            for h in range(horizon):
                med = rows[h][2]
                new_med = price6(med * scale)
                # Preserve spread around median
                spread = [rows[h][j] - med for j in range(5)]
                new_row = [price6(new_med + spread[j]) for j in range(5)]
                # Re-enforce non-decreasing
                for j in range(1, 5):
                    if new_row[j] < new_row[j - 1]:
                        new_row[j] = new_row[j - 1]
                rows[h] = new_row

    return [
        {"id": m["id"], "q": per_market[m["id"]]} for m in case["markets"]
    ]


def main():
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)

    for fname in sorted(os.listdir(input_dir)):
        if not fname.endswith(".in"):
            continue
        inpath = os.path.join(input_dir, fname)
        with open(inpath, "r") as f:
            case = json.load(f)
        forecasts = run_case(case)
        outname = fname.replace(".in", ".out")
        outpath = os.path.join(output_dir, outname)
        with open(outpath, "w") as f:
            json.dump({"forecasts": forecasts}, f)


if __name__ == "__main__":
    main()

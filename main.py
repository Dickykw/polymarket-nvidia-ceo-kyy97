#!/usr/bin/env python3
"""Polymarket NVIDIA CEO forecaster.

Per-market short-horizon volatility forecaster. For each market it estimates
the current 1-minute move volatility from the last 120 minutes (a robust mix
of the median absolute move and the standard deviation), then forecasts each
minute's price as a normal random walk around the last price with a spread
that widens like sqrt(h). Medians are normalised so the markets' probabilities
sum to 1 (only one person becomes CEO). No trend: prediction-market prices are
near-martingales, and a fitted trend hurt on every practice case.

Practice score (mean pinball loss, 5 cases): 0.3094 vs house baseline 0.3985.
"""
import json
import math
import os
import sys

Z = [-1.644854, -0.67449, 0.0, 0.67449, 1.644854]
QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]
VOL_WIN = 120
VOL_FLOOR = 0.0005
VOL_CAP = 0.005


def price6(x):
    v = round(min(1.0, max(0.0, x)) * 1e6) / 1e6
    return v + 0.0


def estimate_sigma(prices):
    n = len(prices)
    w = min(VOL_WIN, n - 1)
    if w < 2:
        return VOL_FLOOR
    ch = [prices[i] - prices[i - 1] for i in range(n - w, n)]
    ach = sorted(abs(c) for c in ch)
    med = ach[len(ach) // 2]
    sigma_med = med / 0.6745 if med > 0 else 0.0
    mean = sum(ch) / len(ch)
    sigma_std = math.sqrt(sum((c - mean) ** 2 for c in ch) / len(ch))
    sigma = (sigma_med + sigma_std) / 2.0
    return min(max(sigma, VOL_FLOOR), VOL_CAP)


def forecast_market(prices, horizon):
    x = prices[-1]
    sigma = estimate_sigma(prices)
    rows = []
    for h in range(1, horizon + 1):
        s = sigma * math.sqrt(h)
        row = [price6(x + z * s) for z in Z]
        for j in range(1, 5):
            if row[j] < row[j - 1]:
                row[j] = row[j - 1]
        rows.append(row)
    return rows


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    for fname in sorted(os.listdir(in_dir)):
        if not fname.endswith(".in"):
            continue
        cid = fname[:-3]
        with open(os.path.join(in_dir, fname), "r", encoding="utf-8") as f:
            case = json.load(f)
        horizon = case["horizon_minutes"]
        per = {}
        for m in case["markets"]:
            per[m["id"]] = forecast_market(m["prices"], horizon)
        # Normalise medians so the markets' probabilities sum to 1.
        meds = [per[m["id"]][0][2] for m in case["markets"]]
        s = sum(meds)
        if s > 0 and abs(s - 1.0) > 0.02:
            scale = 1.0 / s
            for mid, rows in per.items():
                for h in range(horizon):
                    med = rows[h][2]
                    nm = price6(med * scale)
                    sp = [rows[h][j] - med for j in range(5)]
                    nr = [price6(nm + sp[j]) for j in range(5)]
                    for j in range(1, 5):
                        if nr[j] < nr[j - 1]:
                            nr[j] = nr[j - 1]
                    rows[h] = nr
        forecasts = [{"id": m["id"], "q": per[m["id"]]} for m in case["markets"]]
        with open(os.path.join(out_dir, cid + ".out"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"forecasts": forecasts}) + "\n")


if __name__ == "__main__":
    main()

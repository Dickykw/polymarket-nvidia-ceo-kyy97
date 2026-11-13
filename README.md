# Polymarket NVIDIA CEO Forecaster

This entry for the make.fun bounty "Forecast Polymarket's next NVIDIA CEO prices minute by minute, 4 hours ahead" predicts the full quantile distribution (0.05, 0.25, 0.5, 0.75, 0.95) for each of the 19–24 CEO-candidate markets, 240 minutes into the future. The core idea is to estimate per-market volatility from the last 120 minutes of 1-minute price changes using a robust average of the median absolute deviation (scaled by 1/0.6745) and the standard deviation, floored at 0.0005 and capped at 0.005. This adaptive sigma replaces the fixed 0.0025 used by the persistence baseline, giving narrower spreads to quiet markets (where prices barely move) and wider spreads to active ones (where jumps occur). Forecasts are generated as q_tau(h) = clamp(last_price + z_tau · sigma · √h, 0, 1), rounded to 6 decimals, with rows enforced to be non-decreasing. Finally, the median forecasts at h=1 are normalised across markets to sum to 1 (since exactly one person will become CEO), applied only if the sum deviates from 1 by more than 0.02. The mean pinball score across five practice cases is 0.3092, well below the house baseline of 0.3985.

## How to Run

Place the input case JSON files (`.in` extension) in a directory and set `MAKEFUN_INPUT_DIR` (default `/input`) and `MAKEFUN_OUTPUT_DIR` (default `/output`). Then run:

```
python3 bot/main.py
```

The program reads every `*.in` file from the input directory, processes each case, and writes a corresponding `*.out` file to the output directory. It uses only the Python 3.13 standard library, is fully deterministic (identical outputs on repeated runs), and completes within 8 seconds per case on a single CPU. To score against the kit's practice cases, use the provided `score_main.py`:

```
python3 score_main.py
```
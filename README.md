# Polymarket NVIDIA CEO Forecaster

Per-market short-horizon volatility forecaster for make.fun's
polymarket-nvidia-ceo-forecast-01 bounty.

For each market it estimates the current 1-minute move volatility from the
last 120 minutes (a robust mix of the median absolute move and the standard
deviation), then forecasts each minute's price as a normal random walk around
the last price with a spread widening like sqrt(h). Medians are normalised so
the markets' probabilities sum to 1.

Practice score (mean pinball loss, 5 cases): 0.3094 vs house baseline 0.3985.

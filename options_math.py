import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq


def bs_price(S, K, T, r, sigma, option_type):
    """Black-Scholes option price."""
    if T <= 0 or sigma <= 0:
        intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
        return intrinsic
    d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def calc_delta(S, K, T, r, sigma, option_type):
    """Compute Black-Scholes delta."""
    if T <= 0 or sigma <= 0:
        if option_type == "call":
            return 1.0 if S > K else (0.5 if S == K else 0.0)
        else:
            return -1.0 if S < K else (-0.5 if S == K else 0.0)
    d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
    if option_type == "call":
        return float(norm.cdf(d1))
    else:
        return float(norm.cdf(d1) - 1)


def calc_iv(market_price, S, K, T, r, option_type):
    """Compute implied volatility using Brent's method."""
    if T <= 0 or market_price <= 0:
        return None
    intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
    if market_price < intrinsic - 0.01:
        return None
    try:
        def objective(sigma):
            return bs_price(S, K, T, r, sigma, option_type) - market_price
        iv = brentq(objective, 1e-6, 10.0, xtol=1e-6, maxiter=200)
        return float(iv)
    except (ValueError, RuntimeError):
        return None

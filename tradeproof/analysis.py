"""Core diagnostics. All functions take a 1-D numpy array of per-trade P&L (account currency)."""
from __future__ import annotations

from dataclasses import dataclass
from math import erf, sqrt, log, e

import numpy as np

EULER_GAMMA = 0.5772156649015329


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + erf(x / sqrt(2)))


def _norm_ppf(p: float) -> float:
    # Acklam's approximation, accurate to ~1e-9; avoids a scipy dependency.
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02, 1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02, 6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00, -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00]
    lo, hi = 0.02425, 1 - 0.02425
    if p < lo:
        q = sqrt(-2 * np.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > hi:
        q = sqrt(-2 * np.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def max_drawdown(pnl: np.ndarray, start_equity: float) -> float:
    """Max peak-to-trough drawdown as a positive fraction of peak equity."""
    eq = start_equity + np.cumsum(pnl)
    eq = np.concatenate([[start_equity], eq])
    peak = np.maximum.accumulate(eq)
    return float(np.max((peak - eq) / np.where(peak > 0, peak, 1)))


@dataclass
class Summary:
    n: int
    total: float
    win_rate: float
    profit_factor: float
    expectancy: float
    sharpe_per_trade: float
    max_dd: float
    longest_losing_streak: int


def summarize(pnl: np.ndarray, start_equity: float) -> Summary:
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    gl = -losses.sum()
    sd = pnl.std(ddof=1)
    streak = cur = 0
    for x in pnl:
        cur = cur + 1 if x < 0 else 0
        streak = max(streak, cur)
    return Summary(
        n=len(pnl), total=float(pnl.sum()), win_rate=float((pnl > 0).mean()),
        profit_factor=float(wins.sum() / gl) if gl > 0 else float("inf"),
        expectancy=float(pnl.mean()), sharpe_per_trade=float(pnl.mean() / sd) if sd > 0 else 0.0,
        max_dd=max_drawdown(pnl, start_equity), longest_losing_streak=streak,
    )


def deflated_sharpe(pnl: np.ndarray, n_trials: int) -> float:
    """Probability the true Sharpe > 0 after correcting for `n_trials` strategy variants tried
    (Bailey & López de Prado, 2014). Uses per-trade Sharpe. 1.0 = very likely real, <0.95 = suspect."""
    n = len(pnl)
    sd = pnl.std(ddof=1)
    if sd == 0 or n < 3:
        return 0.0
    sr = pnl.mean() / sd
    z = (pnl - pnl.mean()) / sd
    skew, kurt = float((z**3).mean()), float((z**4).mean())
    if n_trials > 1:
        sr0 = sqrt(1 / n) * ((1 - EULER_GAMMA) * _norm_ppf(1 - 1 / n_trials) + EULER_GAMMA * _norm_ppf(1 - 1 / (n_trials * e)))
    else:
        sr0 = 0.0
    denom = 1 - skew * sr + (kurt - 1) / 4 * sr**2
    if denom <= 0:
        return 0.0
    return _norm_cdf((sr - sr0) * sqrt(n - 1) / sqrt(denom))


def monte_carlo(pnl: np.ndarray, start_equity: float, runs: int = 5000, seed: int = 7) -> dict:
    """Reshuffle trade order (drawdown/path risk) and bootstrap (sampling risk)."""
    rng = np.random.default_rng(seed)
    n = len(pnl)
    dd_shuf = np.empty(runs)
    tot_boot = np.empty(runs)
    dd_boot = np.empty(runs)
    for i in range(runs):
        dd_shuf[i] = max_drawdown(rng.permutation(pnl), start_equity)
        b = rng.choice(pnl, n, replace=True)
        tot_boot[i] = b.sum()
        dd_boot[i] = max_drawdown(b, start_equity)
    return {
        "dd_median": float(np.median(dd_shuf)), "dd_p95": float(np.percentile(dd_shuf, 95)),
        "boot_dd_p95": float(np.percentile(dd_boot, 95)),
        "prob_loss": float((tot_boot <= 0).mean()),
        "total_p5": float(np.percentile(tot_boot, 5)), "total_p50": float(np.percentile(tot_boot, 50)),
    }


def cost_stress(pnl: np.ndarray, extra_cost_per_trade: list[float]) -> list[tuple[float, float, float]]:
    """(extra cost, total P&L, profit factor) after charging more slippage/commission per trade."""
    rows = []
    for c in extra_cost_per_trade:
        adj = pnl - c
        gl = -adj[adj < 0].sum()
        rows.append((c, float(adj.sum()), float(adj[adj > 0].sum() / gl) if gl > 0 else float("inf")))
    return rows


def split_stability(pnl: np.ndarray, parts: int = 4) -> list[float]:
    """Expectancy per chronological slice; an edge that lives in one slice is likely curve-fit."""
    return [float(c.mean()) for c in np.array_split(pnl, parts)]


def top_trade_dependence(pnl: np.ndarray, k: int = 3) -> float:
    """Share of total profit coming from the k best trades (>1 means profit is carried by outliers)."""
    total = pnl.sum()
    if total <= 0:
        return float("nan")
    return float(np.sort(pnl)[-k:].sum() / total)


def prop_firm_sim(pnl: np.ndarray, account: float, profit_target: float, daily_loss: float,
                  max_loss: float, trailing: bool = False, runs: int = 5000, seed: int = 11,
                  trades_per_day: int = 3) -> dict:
    """Probability of passing a prop-firm evaluation when this trade stream is replayed in
    random order. Fractions are of `account`. Trades are grouped into days of `trades_per_day`."""
    rng = np.random.default_rng(seed)
    n = len(pnl)
    passed = fail_daily = fail_max = timeout = 0
    for _ in range(runs):
        seq = rng.choice(pnl, n * 3, replace=True)  # allow up to 3x the sample length to hit target
        eq = peak = account
        outcome = "timeout"
        for d in range(0, len(seq), trades_per_day):
            day_start = eq
            for x in seq[d:d + trades_per_day]:
                eq += x
                peak = max(peak, eq)
                if day_start - eq >= daily_loss * account:
                    outcome = "daily"; break
                floor = peak - max_loss * account if trailing else account - max_loss * account
                if eq <= floor:
                    outcome = "max"; break
            if outcome != "timeout":
                break
            if eq >= account * (1 + profit_target):
                outcome = "pass"; break
        passed += outcome == "pass"; fail_daily += outcome == "daily"
        fail_max += outcome == "max"; timeout += outcome == "timeout"
    return {"pass": passed / runs, "daily_breach": fail_daily / runs, "max_breach": fail_max / runs, "timeout": timeout / runs}

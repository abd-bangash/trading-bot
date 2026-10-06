"""Run all checks and render a verdict report (Markdown)."""
from __future__ import annotations

import numpy as np

from . import analysis as A


def build_report(pnl: np.ndarray, account: float = 100_000, n_trials: int = 1, prop: dict | None = None) -> tuple[str, str]:
    """Returns (verdict, markdown). verdict in {"PASS", "CAUTION", "FAIL"}."""
    s = A.summarize(pnl, account)
    dsr = A.deflated_sharpe(pnl, n_trials)
    mc = A.monte_carlo(pnl, account)
    avg_win = pnl[pnl > 0].mean() if (pnl > 0).any() else 0.0
    stress = A.cost_stress(pnl, [0, 0.1 * avg_win, 0.25 * avg_win, 0.5 * avg_win])
    slices = A.split_stability(pnl)
    topk = A.top_trade_dependence(pnl)

    flags: list[str] = []
    fails: list[str] = []
    if s.n < 30:
        fails.append(f"Only {s.n} trades: far too few to infer an edge (aim for 100+).")
    elif s.n < 100:
        flags.append(f"Small sample ({s.n} trades).")
    if s.expectancy <= 0:
        fails.append("Negative expectancy: the strategy loses money per trade.")
    if dsr < 0.95:
        (fails if dsr < 0.5 else flags).append(f"Deflated Sharpe probability {dsr:.0%} (<95%): edge not statistically convincing after {n_trials} trial(s).")
    if stress[2][1] <= 0 < stress[0][1]:
        flags.append("Edge disappears if slippage/fees cost an extra 25% of the average win per trade.")
    if sum(1 for x in slices if x <= 0) >= 2:
        flags.append("Edge missing in 2+ of 4 chronological slices: inconsistent, possibly curve-fit.")
    if topk == topk and topk > 1.0:
        flags.append(f"Top 3 trades produce {topk:.0%} of profit: result relies on outliers.")
    if mc["dd_p95"] > 0.25:
        flags.append(f"95th-percentile drawdown across reshuffles is {mc['dd_p95']:.0%}.")
    if mc["prob_loss"] > 0.2:
        flags.append(f"{mc['prob_loss']:.0%} of bootstrap resamples lose money.")
    verdict = "FAIL" if fails else ("CAUTION" if flags else "PASS")

    L = [f"# TradeProof Report: **{verdict}**", "",
         f"Trades: {s.n} | Net P&L: {s.total:,.2f} | Win rate: {s.win_rate:.1%} | Profit factor: {s.profit_factor:.2f} | "
         f"Expectancy/trade: {s.expectancy:,.2f} | Historical max DD: {s.max_dd:.1%} | Longest losing streak: {s.longest_losing_streak}", "",
         "## Findings"]
    L += [f"- FAIL: {m}" for m in fails] + [f"- WARN: {m}" for m in flags]
    if not fails and not flags:
        L.append("- No red flags found by these checks (this is not proof of future profit).")
    L += ["", "## Monte Carlo (5,000 runs)",
          f"- Drawdown if trades arrive in different order: median {mc['dd_median']:.1%}, 95th pct {mc['dd_p95']:.1%} (history: {s.max_dd:.1%})",
          f"- Bootstrap total P&L: 5th pct {mc['total_p5']:,.0f}, median {mc['total_p50']:,.0f}; P(loss) {mc['prob_loss']:.1%}", "",
          "## Cost stress", "| Extra cost/trade | Net P&L | Profit factor |", "|---|---|---|"]
    L += [f"| {c:,.2f} | {t:,.2f} | {pf:.2f} |" for c, t, pf in stress]
    L += ["", "## Consistency", "Expectancy per chronological quarter: " + ", ".join(f"{x:,.2f}" for x in slices)]
    if prop:
        r = A.prop_firm_sim(pnl, account, **prop)
        L += ["", "## Prop-firm challenge simulation",
              f"Pass {r['pass']:.1%} | daily-loss breach {r['daily_breach']:.1%} | max-loss breach {r['max_breach']:.1%} | no result {r['timeout']:.1%}"]
    L += ["", "_Statistical diagnostics on past data. Not financial advice._"]
    return verdict, "\n".join(L)

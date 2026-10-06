# Market research & product decision

## 1. What the two repos are (and what we can legally reuse)

| | Vibe-Trading (HKUDS) | FinceptTerminal |
|---|---|---|
| What | Python/FastAPI/React AI trading agent: 27+ markets, 74+ MCP tools, multi-engine backtester, 18 brokers, swarm agents | C++20/Qt6 desktop "Bloomberg alternative": 100+ data connectors, 37 agents, QuantLib analytics, 16 brokers |
| Traction | ~35k stars | ~32k stars |
| **License** | **MIT** (commercial use OK) | **AGPL-3.0**; commercial use requires their paid Enterprise license |
| Business model | none visible | Enterprise $10-$40/user/mo, uni plan; Quantcept $3-$8/mo |

**Implications**
- Vibe-Trading is the only one you can build a closed, sold product on top of. Fincept code must NOT be embedded in anything you sell (AGPL forces source release, including for SaaS). Treat Fincept as a feature/pricing benchmark only.
- Both are *platforms for building and running strategies*. Both are huge generalist tools, which is itself the gap: they give traders more power to generate strategies, and nothing that tells them whether a strategy is real. Both are also free, so "another terminal / another agent" is a race to zero against 60k stars of free code.

## 2. Pain points found (sources in section 5)

1. **Backtests lie.** Overfitting, data snooping, ignored slippage/fees. Reports of "47 AI agents tested, 3% survived a real drawdown". Retail tools show summary charts but don't explain *why* or whether it's luck. Freelancers already sell "audit my backtest" gigs on Upwork, which shows willingness to pay.
2. **AI/LLM bots multiply the problem.** Anyone can now generate 100 strategies in an afternoon; nobody corrects for the number tried.
3. **Prop-firm challenges.** ~85-95% fail; much of it is rule breaches (daily loss, trailing drawdown), not bad strategy. Rule sets differ per firm and traders miscompute them.
4. **Data but no insight.** Journals (Tradezella etc.) report win rate and drawdown but don't say what to change.
5. **Trust.** "AI" trading products are widely seen as repackaged scripts; buyers are skeptical, so verification is a selling point.

Market context (vendor estimates, treat as directional): algo-trading ~$28.5B (2025); AI trading platforms ~$16B (2026). Comparable pricing: TradingView $13-$200/mo, Fincept Enterprise $10-$40/user/mo.

## 3. Decision: build "TradeProof", a strategy verification layer

**One-liner:** Upload any backtest or trade log (TradingView, MT5, Vibe-Trading, custom CSV); get a PASS / CAUTION / FAIL verdict on whether the edge is real, how bad drawdown can get, whether it survives costs, and whether it would pass your prop-firm challenge.

Why this wedge:
- Hits pain points 1-3 directly with an objective, falsifiable output.
- Platform-agnostic, so it sits *next to* Vibe-Trading/TradingView/MT5 rather than competing with them. Vibe-Trading (MIT) can be a source of strategies and a distribution channel (MCP tool).
- Cheap to build and run (CPU stats, no market-data licensing, no broker liability, no custody, no advice).
- Clear free-to-paid funnel.

**MVP in this repo (v0.1, working):** CSV loader with column auto-detect; deflated Sharpe (corrects for number of variants tried); Monte Carlo reshuffle and bootstrap; cost/slippage stress; chronological-slice consistency; outlier dependence; prop-firm pass-probability simulator (daily + static/trailing max loss); CLI with Markdown report; tests.

## 4. Go-to-market sketch (assumptions, not validated)

| Tier | Price | Contents |
|---|---|---|
| Free | $0 | 1 report/week, watermark |
| Pro | ~$19/mo | unlimited reports, PDF export, prop-firm presets (FTMO, Apex, TopStep), history |
| Teams / prop-firm / educators | ~$99-$299/mo | white-label, API, bulk screening of student/candidate strategies |
| MCP/API | usage-based | plug into AI agents as a "reality check" gate before deploy |

Channels: prop-firm Discords/YouTube, r/algotrading, Vibe-Trading MCP listing, "audit my backtest" content marketing.

**Before charging anyone:** interview ~20 traders; put up a landing page with a sample report and measure sign-ups; check what *not* to claim. Position as statistical diagnostics, not investment advice or signals, and have counsel review the disclaimer in your target jurisdictions.

## 5. Next build steps
1. Web UI (upload CSV, shareable report link) and PDF export.
2. Parsers for TradingView / MT5 / NinjaTrader exports; equity-curve-only input.
3. Prop-firm rule presets; per-day grouping from real timestamps (currently assumes 3 trades/day).
4. Walk-forward and parameter-sensitivity (needs strategy code or optimization grid input).
5. MCP server so agents (Vibe-Trading etc.) can call it.
6. Auth + billing (Stripe), hosting.

## Sources
- Vibe-Trading: https://github.com/HKUDS/Vibe-Trading (MIT)
- FinceptTerminal: https://github.com/Fincept-Corporation/FinceptTerminal (AGPL-3.0 + Enterprise)
- [Automated Trading Software in 2026: A Skeptical Buyer's Guide](https://curvedtrading.com/articles/en/reviews/best-automated-trading-software-2026)
- [I Tested 47 AI Trading Agents and Lost $11,240](https://medium.com/@barbaraperezdavid474omjq5c6f/i-tested-47-ai-trading-agents-and-lost-11-240-heres-how-to-backtest-correctly-in-2026-aba092ace5fe) (anecdotal, single author)
- [Why Your Backtest Lies](https://my.tradingview.com/chart/NAS100USD/76ep1xPi-Overfitting-Will-Break-Your-Strategy-Here-s-Why)
- [Upwork: audit your trading bot for overfitting](https://www.upwork.com/services/product/development-it-audit-your-trading-bot-or-backtest-for-overfitting-and-hidden-risk-2065198556922871282)
- [Tradezella: AI for prop firm traders](https://www.tradezella.com/blog/ai-prop-firm-trading) (vendor claim: 94% fail first challenge)
- [Precedence Research: AI trading platform market](https://www.precedenceresearch.com/table-of-content/6167)
- [TradingView pricing](https://pricingsaas.com/companies/tradingview)
Caveat: market-size and failure-rate figures come from vendor/blog sources and are unverified.

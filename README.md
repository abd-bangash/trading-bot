# TradeProof

Audit a backtest or trade log before risking money. See `docs/MARKET_RESEARCH.md` for why this product.

```bash
pip install numpy pandas
python -m tradeproof examples/noisy_strategy.csv --trials 40 --prop
python -m tradeproof my_trades.csv --account 50000 --prop --target 0.08 --daily-loss 0.05 --max-loss 0.10 --trailing
python -m unittest discover -s tests -t .
```

`--trials` = how many variants you tried before picking this one (drives the deflated-Sharpe penalty).
Exit code 2 on FAIL. Not financial advice.

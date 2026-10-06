import argparse
import sys

from .loader import load_trades
from .report import build_report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="tradeproof", description="Audit a trade log / backtest export.")
    p.add_argument("csv", help="CSV with a P&L column (TradingView, MT5, custom)")
    p.add_argument("--account", type=float, default=100_000, help="starting equity")
    p.add_argument("--trials", type=int, default=1, help="how many strategy variants/parameter sets you tried to find this one")
    p.add_argument("--prop", action="store_true", help="simulate a prop-firm challenge")
    p.add_argument("--target", type=float, default=0.10, help="prop profit target (fraction)")
    p.add_argument("--daily-loss", type=float, default=0.05)
    p.add_argument("--max-loss", type=float, default=0.10)
    p.add_argument("--trailing", action="store_true", help="trailing max drawdown")
    p.add_argument("--out", help="write report to this .md file")
    a = p.parse_args(argv)
    df = load_trades(a.csv)
    prop = dict(profit_target=a.target, daily_loss=a.daily_loss, max_loss=a.max_loss, trailing=a.trailing) if a.prop else None
    verdict, md = build_report(df["pnl"].to_numpy(float), a.account, a.trials, prop)
    if a.out:
        open(a.out, "w").write(md)
    print(md)
    return 0 if verdict != "FAIL" else 2


if __name__ == "__main__":
    sys.exit(main())

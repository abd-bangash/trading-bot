"""Load trade logs from any platform export (TradingView, MT5, Vibe-Trading, custom CSV)."""
from __future__ import annotations

import pandas as pd

PNL_ALIASES = ["pnl", "profit", "net p&l", "net pnl", "profit/loss", "realized pnl", "net profit"]
TIME_ALIASES = ["exit_time", "close time", "time", "date", "exit date", "date/time", "datetime"]


def _find(cols: list[str], aliases: list[str]) -> str | None:
    lowered = {c.lower().strip(): c for c in cols}
    for a in aliases:
        if a in lowered:
            return lowered[a]
    for a in aliases:  # substring fallback, e.g. "Net P&L USD"
        for low, orig in lowered.items():
            if a in low:
                return orig
    return None


def load_trades(path: str) -> pd.DataFrame:
    """Return DataFrame with columns pnl (float) and optional time (datetime), in trade order."""
    df = pd.read_csv(path)
    pnl_col = _find(list(df.columns), PNL_ALIASES)
    if pnl_col is None:
        raise ValueError(f"No P&L column found. Columns: {list(df.columns)}. Expected one of {PNL_ALIASES}")
    out = pd.DataFrame({"pnl": pd.to_numeric(df[pnl_col].astype(str).str.replace(r"[,$]", "", regex=True), errors="coerce")})
    time_col = _find(list(df.columns), TIME_ALIASES)
    if time_col is not None:
        out["time"] = pd.to_datetime(df[time_col], errors="coerce")
        if out["time"].notna().all():
            out = out.sort_values("time", kind="stable")
    out = out.dropna(subset=["pnl"]).reset_index(drop=True)
    if len(out) < 2:
        raise ValueError("Need at least 2 trades with numeric P&L.")
    return out

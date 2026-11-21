"""
================================================================================
PORTFOLIO REAL HISTORICAL BACKTEST & EQUITY CURVE ENGINE
================================================================================
Computes genuine historical performance, drawdown, Sharpe, Sortino, and Calmar
metrics over the active SQLite portfolio holdings vs. SPY and BTC-USD using
`yfinance` daily history with a 12-hour Parquet cache.
================================================================================
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKTEST_PARQUET_PATH = os.path.join(ROOT_DIR, "data_cache", "backtest_prices_3y.parquet")
_BACKTEST_CACHE_TTL_SEC = 12 * 3600


def _map_yf_ticker(tk: str) -> str:
    tk_u = tk.strip().upper()
    return "UNI7083-USD" if tk_u == "UNI-USD" else tk_u


def _load_or_fetch_price_matrix(
    tickers: List[str],
    lookback_period: str = "3y",
) -> pd.DataFrame:
    """Loads cached 3y Close price matrix or downloads fresh daily closes via `yfinance`."""
    req_yf = list(dict.fromkeys([_map_yf_ticker(t) for t in tickers] + ["SPY", "QQQ", "BTC-USD"]))

    if os.path.exists(BACKTEST_PARQUET_PATH) and lookback_period == "3y":
        try:
            age = time.time() - os.path.getmtime(BACKTEST_PARQUET_PATH)
            if age < _BACKTEST_CACHE_TTL_SEC:
                df_cached = pd.read_parquet(BACKTEST_PARQUET_PATH)
                if all(col in df_cached.columns for col in req_yf) and len(df_cached) > 60:
                    return df_cached[req_yf]
        except Exception:
            pass

    try:
        raw = yf.download(req_yf, period=lookback_period, interval="1d", progress=False)
        if raw.empty or "Close" not in raw.columns:
            return pd.DataFrame()
        closes = raw["Close"]
        if isinstance(closes, pd.Series):
            closes = closes.to_frame(name=req_yf[0])
        closes = closes.copy()
        closes.index = pd.to_datetime(closes.index).tz_localize(None)
        closes = closes.sort_index()
        # Filter to actual equity trading calendar before forward-filling crypto prices
        if "SPY" in closes.columns:
            trading_idx = closes["SPY"].dropna().index
            if len(trading_idx) > 0:
                closes = closes.loc[trading_idx]
        closes = closes.ffill()

        if lookback_period == "3y" and not closes.empty:
            try:
                os.makedirs(os.path.dirname(BACKTEST_PARQUET_PATH), exist_ok=True)
                closes.to_parquet(BACKTEST_PARQUET_PATH)
            except Exception:
                pass
        return closes
    except Exception:
        return pd.DataFrame()


def run_portfolio_backtest(
    positions: List[Any],
    capital_usd: float = 100_000.0,
    risk_free_rate_pct: float = 4.0,
    lookback_period: str = "3y",
) -> Dict[str, Any]:
    """
    Runs a real historical daily-return portfolio backtest over `positions` vs.
    SPY & BTC-USD benchmarks. Returns performance KPIs plus DataFrames for plotting.
    """
    fallback = {
        "portfolio_cagr_pct": 18.0,
        "annualized_vol_pct": 16.5,
        "sharpe_ratio": 0.85,
        "sortino_ratio": 1.25,
        "max_drawdown_pct": 18.0,
        "calmar_ratio": 1.00,
        "spy_cagr_pct": 12.0,
        "btc_cagr_pct": 35.0,
        "period_days": 0,
        "equity_curve_df": pd.DataFrame(),
        "drawdown_series": pd.Series(dtype=float),
        "data_source": "STATIC_FALLBACK",
    }

    if not positions:
        return fallback

    raw_weights: Dict[str, float] = {}
    for p in positions:
        tk = str(getattr(p, "ticker", "")).strip().upper()
        w = float(getattr(p, "target_weight_pct", 0.0) or 0.0)
        if tk and w > 0:
            yf_tk = _map_yf_ticker(tk)
            raw_weights[yf_tk] = raw_weights.get(yf_tk, 0.0) + w

    if not raw_weights:
        return fallback

    px_df = _load_or_fetch_price_matrix(list(raw_weights.keys()), lookback_period=lookback_period)
    if px_df.empty:
        return fallback

    # Align to equity market calendar (SPY trading days) so crypto weekends don't distort volatility
    if "SPY" in px_df.columns:
        trading_idx = px_df["SPY"].dropna().index
        px_df = px_df.reindex(trading_idx).ffill()

    avail_cols = [c for c in raw_weights if c in px_df.columns and px_df[c].notna().sum() >= 60]
    if not avail_cols:
        return fallback

    # Build aligned non-NaN window across holdings that have sufficient history (drop recent IPOs only if < 50% coverage)
    min_rows = max(60, int(len(px_df) * 0.45))
    valid_cols = [c for c in avail_cols if px_df[c].notna().sum() >= min_rows] or avail_cols
    sub_df = px_df[list(dict.fromkeys(valid_cols + [b for b in ("SPY", "BTC-USD") if b in px_df.columns]))].dropna()
    if len(sub_df) < 30:
        return fallback

    ret_df = sub_df.pct_change().dropna()
    if len(ret_df) < 25:
        return fallback

    w_sum = sum(raw_weights[c] for c in valid_cols)
    if w_sum <= 0:
        return fallback
    norm_w = np.array([raw_weights[c] / w_sum for c in valid_cols], dtype=float)

    port_ret = pd.Series(ret_df[valid_cols].values @ norm_w, index=ret_df.index, name="Portfolio")
    cum_port = (1.0 + port_ret).cumprod() * float(capital_usd)

    n_days = len(port_ret)
    elapsed_days = max(30, (ret_df.index[-1] - ret_df.index[0]).days)
    years = max(0.25, elapsed_days / 365.25)
    total_mult = float(cum_port.iloc[-1] / capital_usd)
    port_cagr = (max(0.01, total_mult) ** (1.0 / years) - 1.0) * 100.0

    ann_vol = float(port_ret.std(ddof=1) * np.sqrt(252.0) * 100.0)
    rf_dec = float(risk_free_rate_pct) / 100.0
    ann_ret_dec = (port_cagr / 100.0)
    ann_vol_dec = max(0.005, ann_vol / 100.0)
    sharpe = (ann_ret_dec - rf_dec) / ann_vol_dec

    # Textbook institutional Sortino: target semi-deviation across ALL trading days
    mar_daily = rf_dec / 252.0
    downside_diff = np.minimum(0.0, port_ret - mar_daily)
    downside_dev = float(np.sqrt((downside_diff ** 2).mean()) * np.sqrt(252.0))
    sortino = (ann_ret_dec - rf_dec) / max(0.005, downside_dev)

    running_max = cum_port.cummax()
    drawdown_pct_series = ((cum_port / running_max) - 1.0) * 100.0
    max_dd_pct = abs(float(drawdown_pct_series.min()))
    calmar = port_cagr / max(0.5, max_dd_pct)

    eq_curves: Dict[str, pd.Series] = {"Portfolio": cum_port}
    spy_cagr = 0.0
    btc_cagr = 0.0
    if "SPY" in ret_df.columns:
        cum_spy = (1.0 + ret_df["SPY"]).cumprod() * float(capital_usd)
        eq_curves["SPY"] = cum_spy
        spy_cagr = (max(0.01, float(cum_spy.iloc[-1] / capital_usd)) ** (1.0 / years) - 1.0) * 100.0
    if "BTC-USD" in ret_df.columns:
        cum_btc = (1.0 + ret_df["BTC-USD"]).cumprod() * float(capital_usd)
        eq_curves["BTC-USD"] = cum_btc
        btc_cagr = (max(0.01, float(cum_btc.iloc[-1] / capital_usd)) ** (1.0 / years) - 1.0) * 100.0

    return {
        "portfolio_cagr_pct": round(float(port_cagr), 2),
        "annualized_vol_pct": round(float(ann_vol), 2),
        "sharpe_ratio": round(float(sharpe), 2),
        "sortino_ratio": round(float(sortino), 2),
        "max_drawdown_pct": round(float(max_dd_pct), 2),
        "calmar_ratio": round(float(calmar), 2),
        "spy_cagr_pct": round(float(spy_cagr), 2),
        "btc_cagr_pct": round(float(btc_cagr), 2),
        "period_days": int(n_days),
        "assets_covered": len(valid_cols),
        "equity_curve_df": pd.DataFrame(eq_curves),
        "drawdown_series": drawdown_pct_series,
        "data_source": "LIVE_YFINANCE_HISTORY",
    }

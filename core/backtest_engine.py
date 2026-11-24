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
    """Loads cached 3y Close price matrix or downloads fresh daily closes via `yfinance` + Binance fallback."""
    orig_req = list(dict.fromkeys([t.strip().upper() for t in tickers if t and t.strip()] + ["SPY", "QQQ", "BTC-USD"]))
    col_map = {_map_yf_ticker(t): t for t in orig_req}
    req_yf = list(dict.fromkeys(_map_yf_ticker(t) for t in orig_req))

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
        from core.live_quant_fetcher import download_daily_close_series_with_binance_fallback

        series_map = download_daily_close_series_with_binance_fallback(orig_req, period=lookback_period)
        if not series_map:
            return pd.DataFrame()
        closes = pd.DataFrame({_map_yf_ticker(orig_tk): ser for orig_tk, ser in series_map.items()})
        if closes.empty:
            return pd.DataFrame()
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
        "var_95_daily_pct": 1.85,
        "cvar_95_daily_pct": 2.65,
        "var_99_daily_pct": 3.10,
        "cvar_99_daily_pct": 4.20,
        "corr_matrix_df": pd.DataFrame(),
        "stress_tests": [],
        "shannon_vs_bh": {
            "shannon_final_usd": float(capital_usd),
            "passive_final_usd": float(capital_usd),
            "shannon_alpha_usd": 0.0,
            "shannon_alpha_pct": 0.0,
            "months_simulated": 0,
            "monthly_inflow_usd": 2000.0,
        },
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

    # Historical daily VaR & CVaR (Expected Shortfall at 95% and 99%)
    ret_arr = port_ret.values.astype(float)
    q05 = float(np.percentile(ret_arr, 5))
    var_95_daily = round(max(0.0, -q05 * 100.0), 2)
    tail_95 = ret_arr[ret_arr <= q05]
    cvar_95_daily = round(max(var_95_daily, -float(tail_95.mean()) * 100.0 if len(tail_95) > 0 else var_95_daily), 2)

    q01 = float(np.percentile(ret_arr, 1))
    var_99_daily = round(max(0.0, -q01 * 100.0), 2)
    tail_99 = ret_arr[ret_arr <= q01]
    cvar_99_daily = round(max(var_99_daily, -float(tail_99.mean()) * 100.0 if len(tail_99) > 0 else var_99_daily), 2)

    # Cross-Asset Correlation Matrix (Top 12 holdings by target weight)
    top_cols = sorted(valid_cols, key=lambda c: raw_weights[c], reverse=True)[:12]
    corr_matrix_df = ret_df[top_cols].corr().round(2) if len(top_cols) >= 2 else pd.DataFrame()
    corr_matrix_df.columns = ["UNI-USD" if c == "UNI7083-USD" else c for c in corr_matrix_df.columns]
    corr_matrix_df.index = ["UNI-USD" if c == "UNI7083-USD" else c for c in corr_matrix_df.index]

    # Stress Tests: Parametric historical regimes + observed worst 5d/21d windows
    tot_w_pos = sum(max(0.0, float(getattr(p, "target_weight_pct", 0.0) or 0.0)) for p in positions) or 100.0
    crypto_frac = 0.0
    eff_eq_frac = 0.0
    for p in positions:
        tk_p = str(getattr(p, "ticker", "")).strip().upper()
        cat_p = str(getattr(p, "category", "")).upper()
        w_p = max(0.0, float(getattr(p, "target_weight_pct", 0.0) or 0.0)) / tot_w_pos
        if "CRYPTO" in cat_p or tk_p.endswith("-USD"):
            crypto_frac += w_p
        else:
            eff_eq_frac += w_p * (2.0 if tk_p == "QLD" else 1.0)

    stress_tests: List[Dict[str, Any]] = []
    for s_name, eq_shock, cr_shock, desc in (
        ("COVID-19 Liquidity Crash (Feb–Mar 2020)", -0.34, -0.50, "-34% Equities (2x QLD) / -50% Crypto"),
        ("2022 Rate-Hike Tech & Crypto Bear", -0.25, -0.65, "-25% Equities (2x QLD) / -65% Crypto"),
        ("VIX > 35 Volatility Shock", -0.15, -0.25, "-15% Equities (2x QLD) / -25% Crypto"),
    ):
        imp_pct = max(-95.0, min(0.0, (eff_eq_frac * eq_shock + crypto_frac * cr_shock) * 100.0))
        stress_tests.append({
            "Scenario": s_name,
            "Shock Assumptions": desc,
            "Estimated Portfolio Impact (%)": round(imp_pct, 2),
            "Estimated Capital Impact (USD)": round(float(capital_usd) * (imp_pct / 100.0), 2),
        })

    if len(port_ret) >= 21:
        worst_5d = float(((1.0 + port_ret).rolling(5).apply(np.prod, raw=True) - 1.0).min() * 100.0)
        worst_21d = float(((1.0 + port_ret).rolling(21).apply(np.prod, raw=True) - 1.0).min() * 100.0)
        stress_tests.append({
            "Scenario": "Observed Worst 5-Day Window (Historical 3Y)",
            "Shock Assumptions": "Realized tail week in 3Y portfolio returns",
            "Estimated Portfolio Impact (%)": round(worst_5d, 2),
            "Estimated Capital Impact (USD)": round(float(capital_usd) * (worst_5d / 100.0), 2),
        })
        stress_tests.append({
            "Scenario": "Observed Worst 21-Day Window (Historical 3Y)",
            "Shock Assumptions": "Realized worst trading month in 3Y history",
            "Estimated Portfolio Impact (%)": round(worst_21d, 2),
            "Estimated Capital Impact (USD)": round(float(capital_usd) * (worst_21d / 100.0), 2),
        })

    # Shannon Inflow vs Passive Proportional DCA simulation ($2,000/month over backtest dates)
    monthly_inflow = 2000.0
    px_mat = sub_df[valid_cols].values.astype(float)
    p0 = np.maximum(px_mat[0], 1e-8)
    sh_shares = (float(capital_usd) * norm_w) / p0
    pa_shares = (float(capital_usd) * norm_w) / p0
    months_sim = 0
    for idx in range(21, len(px_mat), 21):
        cur_p = np.maximum(px_mat[idx], 1e-8)
        pa_shares += (monthly_inflow * norm_w) / cur_p

        vals = sh_shares * cur_p
        tot_v = float(vals.sum())
        w_cur = vals / max(tot_v, 1e-8)
        gaps = norm_w - w_cur
        pos_idx = [i for i in np.argsort(-gaps) if gaps[i] > 0][:3]
        if pos_idx:
            sub_gaps = np.array([gaps[i] for i in pos_idx], dtype=float)
            alloc_weights = np.zeros_like(norm_w)
            alloc_weights[pos_idx] = sub_gaps / float(sub_gaps.sum())
        else:
            ratios = w_cur / np.maximum(norm_w, 1e-8)
            min_i = int(np.argmin(ratios))
            alloc_weights = np.zeros_like(norm_w)
            alloc_weights[min_i] = 1.0
        sh_shares += (monthly_inflow * alloc_weights) / cur_p
        months_sim += 1

    p_last = np.maximum(px_mat[-1], 1e-8)
    shannon_final = float((sh_shares * p_last).sum())
    passive_final = float((pa_shares * p_last).sum())
    shannon_alpha_usd = shannon_final - passive_final
    shannon_alpha_pct = ((shannon_final / passive_final) - 1.0) * 100.0 if passive_final > 0 else 0.0

    return {
        "portfolio_cagr_pct": round(float(port_cagr), 2),
        "annualized_vol_pct": round(float(ann_vol), 2),
        "sharpe_ratio": round(float(sharpe), 2),
        "sortino_ratio": round(float(sortino), 2),
        "max_drawdown_pct": round(float(max_dd_pct), 2),
        "calmar_ratio": round(float(calmar), 2),
        "spy_cagr_pct": round(float(spy_cagr), 2),
        "btc_cagr_pct": round(float(btc_cagr), 2),
        "var_95_daily_pct": var_95_daily,
        "cvar_95_daily_pct": cvar_95_daily,
        "var_99_daily_pct": var_99_daily,
        "cvar_99_daily_pct": cvar_99_daily,
        "corr_matrix_df": corr_matrix_df,
        "stress_tests": stress_tests,
        "shannon_vs_bh": {
            "shannon_final_usd": round(shannon_final, 2),
            "passive_final_usd": round(passive_final, 2),
            "shannon_alpha_usd": round(shannon_alpha_usd, 2),
            "shannon_alpha_pct": round(shannon_alpha_pct, 2),
            "months_simulated": months_sim,
            "monthly_inflow_usd": monthly_inflow,
        },
        "period_days": int(n_days),
        "assets_covered": len(valid_cols),
        "equity_curve_df": pd.DataFrame(eq_curves),
        "drawdown_series": drawdown_pct_series,
        "data_source": "LIVE_YFINANCE_HISTORY",
    }

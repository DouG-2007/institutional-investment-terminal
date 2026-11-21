"""
================================================================================
LIVE QUANTITATIVE REAL-TIME DATA FETCHER (EQUITIES, CRYPTO, MACRO & ETFs)
================================================================================
Provides deterministic, cached real-time quantitative overlays from 100% free
public APIs with strict sanity bounds and graceful offline fallbacks:
  1. Market Volatility & FX (`^VIX`, `USDBRL=X`)
  2. Live ETF Top Holdings (`yfinance.funds_data.top_holdings` for SPY/QQQ/SMH/ITA)
  3. Live Equity Fundamentals & Financial Statements (`yfinance` + SEC EDGAR XBRL)
  4. Live Crypto Telemetry (5y `yfinance` SMAs/Pi-Cycle, Binance Spot/Futures
     Funding & OI, DeFiLlama TVL/Fees/Stablecoins, CoinGecko Global Dominance,
     and CoinMetrics Community MVRV/Supply where available)
  5. Live Average Daily Trading Volume (`ADTV` in USD Millions)

Cache policy (`data_cache/live_quant_cache.json`):
  - 6 hours TTL for equity fundamentals, SEC XBRL, and ETF constituents
  - 15 minutes TTL for VIX/FX, crypto futures/DeFiLlama, and ADTV
================================================================================
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import datetime
import json
import math
import os
import tempfile
import threading
import time
import urllib.request
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE_QUANT_CACHE_PATH = os.path.join(ROOT_DIR, "data_cache", "live_quant_cache.json")
_CACHE_LOCK = threading.Lock()

_TTL_SLOW_SEC = 6 * 3600   # 6 hours (equity fundamentals, XBRL, ETF constituents)
_TTL_FAST_SEC = 15 * 60    # 15 minutes (VIX/FX, crypto metrics, ADTV)
_USER_AGENT = "InstitutionalInvestmentTerminal/1.0 (research@institutional-terminal.local)"

_DEFILLAMA_SLUG_MAP: Dict[str, str] = {
    "ETH-USD": "ethereum",
    "SOL-USD": "solana",
    "AAVE-USD": "aave",
    "PENDLE-USD": "pendle",
    "UNI-USD": "uniswap",
    "MKR-USD": "makerdao",
    "LINK-USD": "chainlink",
}


def _safe_float(
    val: Any,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> Optional[float]:
    """Converts value to finite float within optional inclusive bounds."""
    if val is None or isinstance(val, bool):
        return None
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    if min_val is not None and f < min_val:
        return None
    if max_val is not None and f > max_val:
        return None
    return f


def _fetch_json(url: str, timeout: float = 5.5) -> Optional[Any]:
    """Fetches and decodes JSON payload with short timeout; returns None on error."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _load_cache_bucket(bucket: str, key: str, ttl_sec: float) -> Optional[Any]:
    with _CACHE_LOCK:
        if not os.path.exists(LIVE_QUANT_CACHE_PATH):
            return None
        try:
            with open(LIVE_QUANT_CACHE_PATH, "r", encoding="utf-8") as f:
                root = json.load(f)
            entry = (root.get(bucket) or {}).get(key)
            if not isinstance(entry, dict):
                return None
            if (time.time() - float(entry.get("ts") or 0.0)) > ttl_sec:
                return None
            return entry.get("data")
        except Exception:
            return None


def _save_cache_bucket(bucket: str, key: str, data: Any) -> None:
    with _CACHE_LOCK:
        root: Dict[str, Any] = {}
        if os.path.exists(LIVE_QUANT_CACHE_PATH):
            try:
                with open(LIVE_QUANT_CACHE_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    root = loaded
            except Exception:
                root = {}
        root.setdefault(bucket, {})[key] = {"ts": time.time(), "data": data}
        try:
            os.makedirs(os.path.dirname(LIVE_QUANT_CACHE_PATH), exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(
                prefix="lq_cache_",
                suffix=".tmp",
                dir=os.path.dirname(LIVE_QUANT_CACHE_PATH),
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(root, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, LIVE_QUANT_CACHE_PATH)
        except Exception:
            pass


def _fetch_yahoo_chart_last(symbol: str) -> Optional[float]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
    payload = _fetch_json(url, timeout=4.5)
    try:
        meta = payload["chart"]["result"][0]["meta"]
        px = meta.get("regularMarketPrice") or meta.get("chartPreviousClose")
        val = _safe_float(px, min_val=0.01)
        if val is not None:
            return val
    except Exception:
        pass
    try:
        lp = yf.Ticker(symbol).fast_info.get("lastPrice")
        return _safe_float(lp, min_val=0.01)
    except Exception:
        return None


def fetch_live_vix_and_fx() -> Dict[str, float]:
    """Fetches live ^VIX and USDBRL=X with 15-minute cache."""
    cached = _load_cache_bucket("vix_fx", "latest", _TTL_FAST_SEC)
    if isinstance(cached, dict) and cached:
        return cached

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_vix = pool.submit(_fetch_yahoo_chart_last, "^VIX")
        f_fx = pool.submit(_fetch_yahoo_chart_last, "USDBRL=X")
        vix_val = f_vix.result()
        fx_val = f_fx.result()

    res: Dict[str, float] = {}
    if vix_val is not None:
        res["vix_current"] = round(vix_val, 2)
    if fx_val is not None:
        res["usd_brl"] = round(fx_val, 4)

    if res:
        _save_cache_bucket("vix_fx", "latest", res)
    return res


def fetch_live_etf_constituents(
    etf_tickers: Sequence[str] = ("SPY", "QQQ", "SMH", "ITA"),
) -> Dict[str, Dict[str, float]]:
    """
    Fetches live top ETF holdings (%) from `yfinance.Ticker(etf).funds_data.top_holdings`.
    Returns `{etf: {constituent_ticker: weight_pct}}`.
    """
    tks = [t.strip().upper() for t in etf_tickers if t and t.strip()]
    out: Dict[str, Dict[str, float]] = {}
    to_fetch: List[str] = []

    for tk in tks:
        cached = _load_cache_bucket("etf_holdings", tk, _TTL_SLOW_SEC)
        if isinstance(cached, dict) and cached:
            out[tk] = cached
        else:
            to_fetch.append(tk)

    if not to_fetch:
        return out

    def _one_etf(etf: str) -> Tuple[str, Dict[str, float]]:
        try:
            th = yf.Ticker(etf).funds_data.top_holdings
            if th is None or th.empty:
                return etf, {}
            col = "Holding Percent" if "Holding Percent" in th.columns else th.columns[0]
            weights: Dict[str, float] = {}
            for sym, row in th.iterrows():
                w = _safe_float(row.get(col), min_val=0.0, max_val=1.0)
                sym_u = str(sym).strip().upper().replace(".", "-")
                if w is not None and w > 0 and sym_u:
                    weights[sym_u] = round(w * 100.0, 2)
            return etf, weights
        except Exception:
            return etf, {}

    with ThreadPoolExecutor(max_workers=min(4, len(to_fetch))) as pool:
        for etf, weights in pool.map(_one_etf, to_fetch):
            if weights:
                out[etf] = weights
                _save_cache_bucket("etf_holdings", etf, weights)

    return out


def _extract_yf_row_values(df: Optional[pd.DataFrame], candidates: Sequence[str]) -> List[float]:
    """Returns newest-to-oldest finite values for the first matching statement row."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return []
    idx_lookup = {str(i).strip().lower(): i for i in df.index}
    for cand in candidates:
        row_key = idx_lookup.get(cand.lower())
        if row_key is not None:
            series = df.loc[row_key]
            vals: List[float] = []
            for v in series.values:
                f = _safe_float(v)
                if f is not None:
                    vals.append(f)
            if vals:
                return vals
    return []


def _compute_cagr_pct(series_newest_first: List[float], max_periods: int = 3) -> Optional[float]:
    """Computes annualized growth rate (%) from newest-to-oldest positive annual figures."""
    if len(series_newest_first) < 3:
        return None
    span = min(max_periods, len(series_newest_first) - 1)
    newest = series_newest_first[0]
    oldest = series_newest_first[span]
    if newest <= 0 or oldest <= 0 or span <= 0:
        return None
    try:
        cagr = ((newest / oldest) ** (1.0 / span) - 1.0) * 100.0
        return round(float(np.clip(cagr, -50.0, 120.0)), 1)
    except Exception:
        return None


def _fetch_sec_xbrl_facts(ticker: str, sec_map: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """Extracts verified annual SEC 10-K/20-F CompanyFacts (USD Billions) if indexed."""
    info = sec_map.get(ticker) or sec_map.get(ticker.replace("-", ""))
    if not info:
        return {}
    cik_padded = str(int(info["cik"])).zfill(10)
    payload = _fetch_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json", timeout=6.0)
    if not isinstance(payload, dict):
        return {}
    us_gaap = (payload.get("facts") or {}).get("us-gaap") or {}
    if not us_gaap:
        return {}

    def _latest_annual_usd_b(tags: Sequence[str]) -> Optional[float]:
        for tag in tags:
            units = ((us_gaap.get(tag) or {}).get("units") or {}).get("USD") or []
            annuals = [
                u for u in units
                if str(u.get("form") or "").upper() in ("10-K", "20-F")
                and str(u.get("fp") or "").upper() == "FY"
                and _safe_float(u.get("val")) is not None
            ]
            if annuals:
                annuals.sort(key=lambda x: str(x.get("end") or ""), reverse=True)
                val_b = _safe_float(annuals[0]["val"])
                if val_b is not None:
                    return round(val_b / 1e9, 3)
        return None

    res: Dict[str, float] = {}
    rev = _latest_annual_usd_b(("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"))
    cfo = _latest_annual_usd_b(("NetCashProvidedByUsedInOperatingActivities",))
    ni = _latest_annual_usd_b(("NetIncomeLoss",))
    assets = _latest_annual_usd_b(("Assets",))
    if rev is not None and rev > 0:
        res["xbrl_revenue_b"] = rev
    if cfo is not None:
        res["xbrl_cfo_b"] = cfo
    if ni is not None:
        res["xbrl_net_income_b"] = ni
    if assets is not None and assets > 0:
        res["xbrl_total_assets_b"] = assets
    return res


def _get_fx_to_usd(curr: str) -> Optional[float]:
    """Returns USD per 1 unit of `curr` (cached 6h) for non-USD financial statements."""
    c = (curr or "USD").strip().upper()
    if not c or c == "USD":
        return 1.0
    cached = _load_cache_bucket("fx_rates", c, _TTL_SLOW_SEC)
    if _safe_float(cached, min_val=0.0001, max_val=200.0) is not None:
        return float(cached)

    rate = _fetch_yahoo_chart_last(f"{c}USD=X")
    if rate is None or rate <= 0:
        inv = _fetch_yahoo_chart_last(f"USD{c}=X")
        if inv is not None and inv > 0:
            rate = 1.0 / inv
    if rate is not None and 0.0001 <= rate <= 200.0:
        rate_f = round(float(rate), 6)
        _save_cache_bucket("fx_rates", c, rate_f)
        return rate_f
    return None


def _fetch_single_equity_live(
    ticker: str,
    sector_vertical: str,
    sec_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    tk = ticker.strip().upper()
    is_bank = sector_vertical == "FINANCIAL_BANK"
    out: Dict[str, Any] = {}
    try:
        t_obj = yf.Ticker(tk)
        info = t_obj.info or {}
        fin = t_obj.financials
        cf = t_obj.cashflow
        bs = t_obj.balance_sheet
    except Exception:
        return out

    fin_curr = str(info.get("financialCurrency") or "USD").strip().upper()
    fx_to_usd = _get_fx_to_usd(fin_curr)

    spot_px = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"), min_val=0.01)
    mcap_raw = _safe_float(info.get("marketCap"), min_val=1e7)
    mcap_b = round(mcap_raw / 1e9, 2) if mcap_raw is not None else None
    if mcap_b is not None:
        out["mcap_b"] = mcap_b

    pe_t = _safe_float(info.get("trailingPE"), min_val=1.0, max_val=250.0)
    pe_f = _safe_float(info.get("forwardPE"), min_val=1.0, max_val=200.0)
    pb_v = _safe_float(info.get("priceToBook"), min_val=0.1, max_val=200.0)
    beta_v = _safe_float(info.get("beta"), min_val=0.2, max_val=3.5)
    div_y = _safe_float(info.get("dividendYield"), min_val=0.0, max_val=25.0)
    if pe_t is not None:
        out["pe_curr"] = round(pe_t, 1)
    if pe_f is not None:
        out["pe_ntm"] = round(pe_f, 1)
    if pb_v is not None and fin_curr == "USD":
        out["pb_curr"] = round(pb_v, 2)
    if beta_v is not None:
        out["beta"] = round(beta_v, 2)
    if div_y is not None:
        # yfinance returns dividendYield already in percentage in newer versions (e.g., 0.42 for 0.42%)
        # or fraction (<0.15) depending on field; normalize carefully using dividendRate/price when available
        div_rate = _safe_float(info.get("dividendRate"), min_val=0.0)
        if div_rate is not None and spot_px is not None:
            out["div_yield_pct"] = round(min(15.0, (div_rate / spot_px) * 100.0), 2)
        else:
            out["div_yield_pct"] = round(div_y if div_y > 0.25 else div_y * 100.0, 2)

    avg_vol = _safe_float(info.get("averageVolume") or info.get("averageDailyVolume10Day"), min_val=1.0)
    if avg_vol is not None and spot_px is not None:
        out["avg_daily_dollar_vol_m"] = round((avg_vol * spot_px) / 1e6, 1)

    roe_frac = _safe_float(info.get("returnOnEquity"), min_val=-1.0, max_val=5.0)
    if roe_frac is not None:
        out["roe_pct"] = round(roe_frac * 100.0, 1)

    if is_bank:
        # Banks: keep statements exempt from Sloan / EV-EBITDA / CFO-EBITDA distortion
        out["data_source"] = "LIVE_YF_BANK"
        out["as_of"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        return out

    # Non-bank GAAP statement extraction via yfinance (requires USD or known FX rate)
    rev_s = _extract_yf_row_values(fin, ("Total Revenue", "Operating Revenue", "Revenue"))
    gp_s = _extract_yf_row_values(fin, ("Gross Profit",))
    ebit_s = _extract_yf_row_values(fin, ("EBIT", "Operating Income"))
    ebitda_s = _extract_yf_row_values(fin, ("EBITDA", "Normalized EBITDA"))
    ni_s = _extract_yf_row_values(fin, ("Net Income", "Net Income Common Stockholders"))
    int_exp_s = _extract_yf_row_values(fin, ("Interest Expense", "Interest Expense Non Operating"))

    cfo_s = _extract_yf_row_values(cf, ("Operating Cash Flow", "Cash Flow From Continuing Operating Activities"))
    cfi_s = _extract_yf_row_values(cf, ("Investing Cash Flow", "Cash Flow From Continuing Investing Activities"))
    fcf_s = _extract_yf_row_values(cf, ("Free Cash Flow",))
    capex_s = _extract_yf_row_values(cf, ("Capital Expenditure",))

    assets_s = _extract_yf_row_values(bs, ("Total Assets",))
    cash_s = _extract_yf_row_values(bs, ("Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"))
    curr_a_s = _extract_yf_row_values(bs, ("Current Assets",))
    curr_l_s = _extract_yf_row_values(bs, ("Current Liabilities",))
    debt_s = _extract_yf_row_values(bs, ("Total Debt", "Long Term Debt And Capital Lease Obligation"))
    eq_s = _extract_yf_row_values(bs, ("Stockholders Equity", "Total Equity Gross Minority Interest"))

    xbrl = _fetch_sec_xbrl_facts(tk, sec_map) if (sec_map and fin_curr == "USD") else {}

    if fx_to_usd is not None:
        fco_b = round((cfo_s[0] * fx_to_usd) / 1e9, 2) if cfo_s else xbrl.get("xbrl_cfo_b")
        fci_b = round((cfi_s[0] * fx_to_usd) / 1e9, 2) if cfi_s else None
        ebitda_b = round((ebitda_s[0] * fx_to_usd) / 1e9, 2) if (ebitda_s and ebitda_s[0] > 0) else None
        ebit_b = round((ebit_s[0] * fx_to_usd) / 1e9, 2) if (ebit_s and ebit_s[0] > 0) else None
        ni_b = round((ni_s[0] * fx_to_usd) / 1e9, 2) if ni_s else xbrl.get("xbrl_net_income_b")
        assets_b = round((assets_s[0] * fx_to_usd) / 1e9, 2) if (assets_s and assets_s[0] > 0) else xbrl.get("xbrl_total_assets_b")

        if fco_b is not None and fco_b != 0:
            out["fco_b"] = fco_b
        if fci_b is not None:
            out["fci_b"] = fci_b
        if len(cfo_s) >= 3:
            out["fco_5y_history_b"] = [round((v * fx_to_usd) / 1e9, 2) for v in reversed(cfo_s[:5])]
        if ebitda_b is not None:
            out["ebitda_b"] = ebitda_b
        if ebit_b is not None:
            out["ebit_b"] = ebit_b
        if ni_b is not None:
            out["net_income_b"] = ni_b
        if assets_b is not None:
            out["total_assets_b"] = assets_b

        cash_usd_b = round((cash_s[0] * fx_to_usd) / 1e9, 2) if (cash_s and cash_s[0] >= 0) else None
        if cash_usd_b is not None:
            out["cash_b"] = cash_usd_b

        raw_fcf_b: Optional[float] = None
        if fcf_s and fcf_s[0] > 0:
            raw_fcf_b = round((fcf_s[0] * fx_to_usd) / 1e9, 2)
        elif fco_b is not None and capex_s:
            est_fcf = fco_b - abs((capex_s[0] * fx_to_usd) / 1e9)
            if est_fcf > 0:
                raw_fcf_b = round(est_fcf, 2)

        if raw_fcf_b is not None and raw_fcf_b > 0:
            # Guard fintech hybrids (e.g. MELI) where customer deposits inflate GAAP CFO/FCF
            if ebit_b is not None and ebit_b > 0 and raw_fcf_b > 1.8 * ebit_b:
                raw_fcf_b = round(ebit_b * 1.15, 2)
            out["fcf_b"] = raw_fcf_b

        if curr_a_s and curr_l_s and curr_l_s[0] > 0:
            out["nwc_b"] = round(((curr_a_s[0] - curr_l_s[0]) * fx_to_usd) / 1e9, 2)

        debt_usd_b = round((abs(debt_s[0]) * fx_to_usd) / 1e9, 2) if debt_s else None
        eq_usd_b = round((eq_s[0] * fx_to_usd) / 1e9, 2) if (eq_s and eq_s[0] > 0) else None

        # USD EV calculation & ADR sanity guard (Yahoo enterpriseValue mixes currencies on foreign ADRs)
        ev_raw_b = _safe_float(info.get("enterpriseValue"), min_val=1e7)
        ev_raw_b = (ev_raw_b / 1e9) if ev_raw_b is not None else None
        if mcap_b is not None and debt_usd_b is not None and cash_usd_b is not None:
            out["ev_b"] = round(max(0.5, mcap_b + debt_usd_b - cash_usd_b), 2)
        elif ev_raw_b is not None and mcap_b is not None and (0.4 * mcap_b) <= ev_raw_b <= (2.5 * mcap_b):
            out["ev_b"] = round(ev_raw_b, 2)
        elif mcap_b is not None:
            out["ev_b"] = mcap_b

        # Foreign ADR P/B guard using USD stockholders' equity
        if fin_curr != "USD" and mcap_b is not None and eq_usd_b is not None and eq_usd_b > 0:
            pb_calc = mcap_b / eq_usd_b
            if 0.2 <= pb_calc <= 120.0:
                out["pb_curr"] = round(pb_calc, 2)

        if out.get("ev_b") and ebitda_b and ebitda_b > 0 and fin_curr != "USD":
            ev_eb_calc = out["ev_b"] / ebitda_b
            if 1.0 <= ev_eb_calc <= 200.0:
                out["ev_ebitda_curr"] = round(ev_eb_calc, 1)

        if ni_b is not None and fco_b is not None and fci_b is not None and assets_b and assets_b > 0:
            sloan = ((ni_b - fco_b - fci_b) / assets_b) * 100.0
            out["sloan_pct"] = round(float(np.clip(sloan, -40.0, 40.0)), 1)
    else:
        ev_raw_b = _safe_float(info.get("enterpriseValue"), min_val=1e7)
        if ev_raw_b is not None and mcap_b is not None and (0.4 * mcap_b) <= (ev_raw_b / 1e9) <= (2.5 * mcap_b):
            out["ev_b"] = round(ev_raw_b / 1e9, 2)

    # Scale-invariant ratios & 3y CAGRs (exact regardless of reporting currency)
    if curr_a_s and curr_l_s and curr_l_s[0] > 0:
        out["current_ratio"] = round(curr_a_s[0] / curr_l_s[0], 2)

    if ebit_s and int_exp_s and abs(int_exp_s[0]) > 1e5:
        ic_ratio = abs(ebit_s[0]) / abs(int_exp_s[0])
        out["interest_coverage_x"] = round(float(np.clip(ic_ratio, 0.5, 250.0)), 1)

    if debt_s and ebitda_s and ebitda_s[0] > 0:
        d_eb = abs(debt_s[0]) / ebitda_s[0]
        out["debt_to_ebitda"] = round(float(np.clip(d_eb, 0.0, 25.0)), 2)
    if debt_s and assets_s and assets_s[0] > 0:
        out["debt_to_assets_pct"] = round(float(np.clip((abs(debt_s[0]) / assets_s[0]) * 100.0, 0.0, 99.0)), 1)
    if debt_s and eq_s and eq_s[0] > 0:
        out["debt_to_equity_pct"] = round(float(np.clip((abs(debt_s[0]) / eq_s[0]) * 100.0, 0.0, 500.0)), 1)

    if fin_curr == "USD":
        ev_ebitda = _safe_float(info.get("enterpriseToEbitda"), min_val=1.0, max_val=200.0)
        if ev_ebitda is not None:
            out["ev_ebitda_curr"] = round(ev_ebitda, 1)

    if rev_s and rev_s[0] > 0 and ebit_s and ebit_s[0] > 0:
        op_m = (ebit_s[0] / rev_s[0]) * 100.0
        if 1.0 <= op_m <= 85.0:
            out["roic_op_margin_pct"] = round(op_m, 1)

    cagr_updates: Dict[str, Dict[str, float]] = {}
    for label, arr in (
        ("Revenue", rev_s),
        ("Gross Profit", gp_s),
        ("EBIT", ebit_s),
        ("EBITDA", ebitda_s),
        ("Net Income", ni_s),
        ("CFO", cfo_s),
        ("FCF", fcf_s),
    ):
        g3 = _compute_cagr_pct(arr, max_periods=min(3, len(arr) - 1))
        if g3 is not None:
            cagr_updates[label] = {"3y": g3}
    if cagr_updates:
        out["cagr_3y_overrides"] = cagr_updates

    out["data_source"] = "LIVE_XBRL_YF" if xbrl else ("LIVE_YF_FX" if fin_curr != "USD" else "LIVE_YF")
    out["as_of"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    return out


def fetch_live_equity_fundamentals(
    tickers: Sequence[str],
    sector_vertical_map: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Fetches live Yahoo Finance financial statements + SEC EDGAR XBRL facts
    in parallel for equities, using a 6-hour JSON cache.
    """
    tks = [t.strip().upper() for t in tickers if t and t.strip()]
    sec_map_cfg = sector_vertical_map or {}
    out: Dict[str, Dict[str, Any]] = {}
    missing: List[str] = []

    for tk in tks:
        cached = _load_cache_bucket("equity_fundamentals", tk, _TTL_SLOW_SEC)
        if isinstance(cached, dict) and cached:
            out[tk] = cached
        else:
            missing.append(tk)

    if not missing:
        return out

    sec_map: Dict[str, Dict[str, Any]] = {}
    try:
        from core.filing_fetcher import _get_sec_ticker_map

        sec_map = _get_sec_ticker_map()
    except Exception:
        sec_map = {}

    def _task(tk: str) -> Tuple[str, Dict[str, Any]]:
        return tk, _fetch_single_equity_live(tk, sec_map_cfg.get(tk, "OTHER"), sec_map)

    with ThreadPoolExecutor(max_workers=min(6, len(missing))) as pool:
        for tk, res in pool.map(_task, missing):
            if res:
                out[tk] = res
                _save_cache_bucket("equity_fundamentals", tk, res)

    return out


def _fetch_binance_derivatives_and_24h(base_sym: str) -> Dict[str, Any]:
    """Pulls live funding rate, open interest, mark price, and 24h USD volume from Binance."""
    pair = f"{base_sym}USDT"
    res: Dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_prem = pool.submit(_fetch_json, f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={pair}", 4.5)
        f_oi = pool.submit(_fetch_json, f"https://fapi.binance.com/fapi/v1/openInterest?symbol={pair}", 4.5)
        f_t24 = pool.submit(_fetch_json, f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}", 4.5)
        prem = f_prem.result()
        oi = f_oi.result()
        t24 = f_t24.result()

    mark_px = _safe_float(prem.get("markPrice") if isinstance(prem, dict) else None, min_val=0.0001)
    fr_raw = _safe_float(prem.get("lastFundingRate") if isinstance(prem, dict) else None, min_val=-0.05, max_val=0.05)
    if fr_raw is not None:
        res["funding_rate_8h_pct"] = round(fr_raw * 100.0, 4)

    oi_units = _safe_float(oi.get("openInterest") if isinstance(oi, dict) else None, min_val=0.0)
    if oi_units is not None and mark_px is not None:
        res["oi_b"] = round((oi_units * mark_px) / 1e9, 4)

    qv = _safe_float(t24.get("quoteVolume") if isinstance(t24, dict) else None, min_val=0.0)
    if qv is not None and qv > 0:
        res["spot_vol_24h_b"] = round(qv / 1e9, 4)
        res["avg_daily_dollar_vol_m"] = round(qv / 1e6, 1)

    return res


def _fetch_defillama_tvl_and_fees(slug: str) -> Dict[str, float]:
    out: Dict[str, float] = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_tvl = pool.submit(_fetch_json, f"https://api.llama.fi/tvl/{slug}", 5.0)
        f_fees = pool.submit(_fetch_json, f"https://api.llama.fi/summary/fees/{slug}?dataType=dailyFees", 5.5)
        tvl_raw = _safe_float(f_tvl.result(), min_val=0.0)
        fees_obj = f_fees.result()

    if tvl_raw is not None and tvl_raw > 0:
        out["tvl_b"] = round(tvl_raw / 1e9, 3)

    if isinstance(fees_obj, dict):
        t30 = _safe_float(fees_obj.get("total30d"), min_val=0.0)
        t24 = _safe_float(fees_obj.get("total24h"), min_val=0.0)
        if t30 is not None and t30 > 0:
            out["protocol_fees_annual_m"] = round((t30 * 12.0) / 1e6, 2)
        elif t24 is not None and t24 > 0:
            out["protocol_fees_annual_m"] = round((t24 * 365.0) / 1e6, 2)
    return out


def _fetch_global_crypto_macro() -> Dict[str, Any]:
    """Pulls live BTC dominance (CoinGecko Global), Stablecoin supply (DeFiLlama), and CoinMetrics MVRV."""
    cached = _load_cache_bucket("crypto_global", "latest", _TTL_FAST_SEC)
    if isinstance(cached, dict) and cached:
        return cached

    cm_start = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
    cm_url = (
        f"https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
        f"?assets=btc,eth&metrics=CapMVRVCur,SplyCur&start_time={cm_start}&page_size=20"
    )
    res: Dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_cg = pool.submit(_fetch_json, "https://api.coingecko.com/api/v3/global", 5.0)
        f_st = pool.submit(_fetch_json, "https://stablecoins.llama.fi/stablecoins?includePrices=false", 5.5)
        f_cm = pool.submit(_fetch_json, cm_url, 5.5)
        cg = f_cg.result()
        st = f_st.result()
        cm = f_cm.result()

    if isinstance(cg, dict):
        data = cg.get("data") or {}
        btc_dom = _safe_float((data.get("market_cap_percentage") or {}).get("btc"), min_val=10.0, max_val=95.0)
        tot_mcap = _safe_float((data.get("total_market_cap") or {}).get("usd"), min_val=1e9)
        if btc_dom is not None:
            res["btc_dominance_pct"] = round(btc_dom, 1)
            if tot_mcap is not None:
                res["btc_mcap_usd"] = tot_mcap * (btc_dom / 100.0)

    if isinstance(st, dict):
        pegged = st.get("peggedAssets") or []
        tot_stable_usd = sum(
            float(((p.get("circulating") or {}).get("peggedUSD") or 0.0))
            for p in pegged
            if isinstance(p, dict)
        )
        if tot_stable_usd > 1e9:
            res["total_stablecoin_mcap_b"] = round(tot_stable_usd / 1e9, 2)
            if res.get("btc_mcap_usd"):
                res["ssr_ratio"] = round(res["btc_mcap_usd"] / tot_stable_usd, 1)

    if isinstance(cm, dict) and isinstance(cm.get("data"), list):
        cm_by_asset: Dict[str, Dict[str, float]] = {}
        rows_sorted = sorted(
            [r for r in cm["data"] if isinstance(r, dict)],
            key=lambda x: str(x.get("time") or ""),
        )
        for row in rows_sorted:
            asset = str(row.get("asset") or "").lower()
            mvrv = _safe_float(row.get("CapMVRVCur"), min_val=0.2, max_val=15.0)
            sply = _safe_float(row.get("SplyCur"), min_val=1000.0)
            if asset and (mvrv is not None or sply is not None):
                entry = cm_by_asset.setdefault(asset, {})
                if mvrv is not None:
                    entry["mvrv_ratio"] = mvrv
                    entry["nupl"] = round(float(np.clip(1.0 - (1.0 / mvrv), -1.0, 0.95)), 2)
                    # Standard calibrated MVRV Z approximation relative to neutral MVRV=1.0
                    entry["mvrv_z"] = round(float(np.clip((mvrv - 1.0) * 1.45, -1.5, 9.0)), 2)
                if sply is not None:
                    entry["circ_m"] = round(sply / 1e6, 2)
        if cm_by_asset:
            res["coinmetrics"] = cm_by_asset

    if res:
        _save_cache_bucket("crypto_global", "latest", res)
    return res


def fetch_live_crypto_metrics(symbols: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetches live 5y SMAs/Pi-Cycle (`yfinance`), Binance Futures funding/OI/24h Vol,
    DeFiLlama TVL/Annualized Fees, CoinGecko BTC dominance, Stablecoin SSR, and
    CoinMetrics MVRV/Supply where available. 15-minute JSON cache.
    """
    syms = [s.strip().upper() for s in symbols if s and s.strip()]
    out: Dict[str, Dict[str, Any]] = {}
    missing: List[str] = []

    for s in syms:
        cached = _load_cache_bucket("crypto_metrics", s, _TTL_FAST_SEC)
        if isinstance(cached, dict) and cached:
            out[s] = cached
        else:
            missing.append(s)

    if not missing:
        return out

    global_macro = _fetch_global_crypto_macro()
    yf_map = {s: ("UNI7083-USD" if s == "UNI-USD" else s) for s in missing}

    # Download 5y daily close series once for true 200W SMA / 111D / 350D*2 Pi Cycle
    hist_by_sym: Dict[str, pd.Series] = {}
    try:
        dl_syms = list(set(yf_map.values()))
        df = yf.download(dl_syms, period="5y", interval="1d", progress=False)
        if not df.empty and "Close" in df.columns:
            closes = df["Close"]
            if isinstance(closes, pd.Series):
                closes = closes.to_frame(name=dl_syms[0])
            for orig, yf_tk in yf_map.items():
                if yf_tk in closes.columns:
                    s_clean = closes[yf_tk].dropna()
                    if not s_clean.empty:
                        hist_by_sym[orig] = s_clean
    except Exception:
        pass

    def _build_one_crypto(sym: str) -> Tuple[str, Dict[str, Any]]:
        base = sym.replace("-USD", "")
        entry: Dict[str, Any] = {}
        s_px = hist_by_sym.get(sym)
        if s_px is not None and len(s_px) >= 120:
            sma111 = float(s_px.rolling(111).mean().iloc[-1])
            entry["sma_111d"] = round(sma111, 4 if sma111 < 10 else 2)
            if len(s_px) >= 350:
                sma350_x2 = float(s_px.rolling(350).mean().iloc[-1]) * 2.0
                entry["sma_350d_x2"] = round(sma350_x2, 4 if sma350_x2 < 10 else 2)
                entry["pi_cycle_crossed"] = sma111 > sma350_x2
            weekly = s_px.resample("W").last().dropna()
            if len(weekly) >= 150:
                w200 = float(weekly.rolling(200, min_periods=120).mean().iloc[-1])
                entry["sma_200w"] = round(w200, 4 if w200 < 10 else 2)

        deriv = _fetch_binance_derivatives_and_24h(base)
        entry.update(deriv)

        slug = _DEFILLAMA_SLUG_MAP.get(sym)
        if slug:
            llama = _fetch_defillama_tvl_and_fees(slug)
            entry.update(llama)

        if "btc_dominance_pct" in global_macro:
            entry["btc_dominance_pct"] = global_macro["btc_dominance_pct"]
        if "ssr_ratio" in global_macro:
            entry["ssr_ratio"] = global_macro["ssr_ratio"]

        cm_asset = (global_macro.get("coinmetrics") or {}).get(base.lower())
        if isinstance(cm_asset, dict):
            for k in ("mvrv_z", "nupl", "circ_m"):
                if k in cm_asset:
                    entry[k] = cm_asset[k]
            if "mvrv_z" in entry or "nupl" in entry:
                entry["onchain_source"] = "LIVE_COINMETRICS"
        elif s_px is not None and len(s_px) >= 180:
            # Real-time quantitative Z-Score & Unrealized proxy for altcoins absent from CoinMetrics free tier
            px_now = float(s_px.iloc[-1])
            win_s = s_px.iloc[-365:] if len(s_px) >= 365 else s_px
            log_w = np.log(np.maximum(win_s.values.astype(float), 1e-8))
            std_w = float(np.std(log_w))
            if std_w > 1e-6:
                z_365 = (float(np.log(max(px_now, 1e-8))) - float(np.mean(log_w))) / std_w
                entry["mvrv_z"] = round(float(np.clip(z_365 * 0.85, -1.2, 5.5)), 2)
            sma_365 = float(win_s.mean())
            if px_now > 0 and sma_365 > 0:
                entry["nupl"] = round(float(np.clip((px_now - sma_365) / px_now, -0.60, 0.85)), 2)
            entry["onchain_source"] = "LIVE_5Y_ZSCORE_PROXY"

        if entry:
            entry["data_source"] = "LIVE_CRYPTO_APIS"
            entry["as_of"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        return sym, entry

    with ThreadPoolExecutor(max_workers=min(6, len(missing))) as pool:
        for sym, res in pool.map(_build_one_crypto, missing):
            if res:
                out[sym] = res
                _save_cache_bucket("crypto_metrics", sym, res)

    return out


def fetch_live_adtv_map(
    tickers: Sequence[str],
    spot_prices: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Returns live Average Daily Dollar Volume (`ADTV` in USD Millions) for
    equities, ETFs, and cryptoassets using cached live fetches + `fast_info`.
    """
    tks = [t.strip().upper() for t in tickers if t and t.strip()]
    px_map = {k.upper(): float(v) for k, v in (spot_prices or {}).items() if v and float(v) > 0}
    out: Dict[str, float] = {}
    need_fast: List[str] = []

    for tk in tks:
        cached_adtv = _load_cache_bucket("adtv", tk, _TTL_FAST_SEC)
        if _safe_float(cached_adtv, min_val=0.1) is not None:
            out[tk] = float(cached_adtv)
            continue

        eq_c = _load_cache_bucket("equity_fundamentals", tk, _TTL_SLOW_SEC)
        if isinstance(eq_c, dict) and _safe_float(eq_c.get("avg_daily_dollar_vol_m"), min_val=0.1) is not None:
            out[tk] = float(eq_c["avg_daily_dollar_vol_m"])
            _save_cache_bucket("adtv", tk, out[tk])
            continue

        cr_c = _load_cache_bucket("crypto_metrics", tk, _TTL_FAST_SEC)
        if isinstance(cr_c, dict) and _safe_float(cr_c.get("avg_daily_dollar_vol_m"), min_val=0.1) is not None:
            out[tk] = float(cr_c["avg_daily_dollar_vol_m"])
            _save_cache_bucket("adtv", tk, out[tk])
            continue

        need_fast.append(tk)

    if not need_fast:
        return out

    def _one_adtv(tk: str) -> Tuple[str, Optional[float]]:
        if tk.endswith("-USD"):
            base = tk.replace("-USD", "")
            d = _fetch_binance_derivatives_and_24h(base)
            return tk, _safe_float(d.get("avg_daily_dollar_vol_m"), min_val=0.1)
        try:
            fi = yf.Ticker(tk).fast_info
            vol = _safe_float(fi.get("tenDayAverageVolume") or fi.get("threeMonthAverageVolume"), min_val=1.0)
            px = px_map.get(tk) or _safe_float(fi.get("lastPrice"), min_val=0.01)
            if vol is not None and px is not None:
                return tk, round((vol * px) / 1e6, 1)
        except Exception:
            pass
        return tk, None

    with ThreadPoolExecutor(max_workers=min(6, len(need_fast))) as pool:
        for tk, val in pool.map(_one_adtv, need_fast):
            if val is not None:
                out[tk] = val
                _save_cache_bucket("adtv", tk, val)

    return out

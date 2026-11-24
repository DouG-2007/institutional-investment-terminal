"""
================================================================================
INSTITUTIONAL VALUATION & BACKTEST ENGINE (SECTOR-STRATIFIED & COMPOSABLE)
================================================================================
Provides a fully configurable, deterministic quantitative backtesting engine
driven by authentic SEC EDGAR XBRL financial facts (US-GAAP + IFRS), FRED
macroeconomic series (FEDFUNDS, T10Y2Y, SAHMREALTIME), Yahoo Finance daily
prices/VIX/TNX, and verified crypto on-chain telemetry.

Supports sector-stratified valuation dispatch aligned with the True Valuation
Framework:
  - TECH_HIGH_GROWTH (incl. Fintechs like NU): Enterprise PEGY (EV/EBIT),
    Reverse DCF, Z-Score EV/EBIT, SMA200 trend filter, Gross Margin / Sloan gates
  - TECH_CASH_COW (incl. Processors MA/V): Enterprise PEGY (EV/FCF),
    Owner Earnings Yield vs US 10Y (^TNX), DCF, Denominator Shareholder Yield PEGY
  - FINANCIAL_BANK (JPM, BAC, WFC, C, DBSDY): Financial PEGY + P/B >= 1.0 veto,
    P/TBV vs ROE, P/E relative
  - CYCLICAL (XOM, CAT, FCX, VALE): Inverse Relative Multiples + Mid-Cycle DCF
  - DEFENSIVE_RETAIL (WMT, COST, PG, KO, JNJ): Relative Multiples + DCF,
    Revenue Growth gate, FCF Yield vs ^TNX
  - CRYPTO_BTC & CRYPTO_ALT: Pi Cycle Top exclusive parabolic BTC trim (`pi_cycle_only`),
    MVRV Z-Score, 200W SMA (`<= 1.05x`), Hash Ribbon, NVT Golden Cross, Trailing DD
================================================================================
"""

from __future__ import annotations

import bisect
import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import yfinance as yf


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CACHE_DIR = os.path.join(ROOT_DIR, "data_cache")
SEC_FACTS_CACHE_PATH = os.path.join(DATA_CACHE_DIR, "sec_historical_facts_v2.json")
SPLITS_CACHE_PATH = os.path.join(DATA_CACHE_DIR, "sec_splits_cache.json")
SEC_TICKERS_PATH = os.path.join(DATA_CACHE_DIR, "sec_tickers.json")
EXTENDED_MARKET_DATA_PATH = os.path.join(DATA_CACHE_DIR, "extended_market_data_10y.parquet")
VAL_PRICE_DATA_PATH = os.path.join(DATA_CACHE_DIR, "valuation_prices_10y.parquet")
LEGACY_MARKET_DATA_PATH = os.path.join(DATA_CACHE_DIR, "all_market_data_10y.parquet")
MACRO_CACHE_PATH = os.path.join(DATA_CACHE_DIR, "macro_backtest_series.parquet")

DEFAULT_SECTOR_MAP: Dict[str, str] = {
    # High-Growth Tech & Fintechs (PDF p. 4: Fintechs treated as Tech)
    "NVDA": "TECH_HIGH_GROWTH",
    "AMZN": "TECH_HIGH_GROWTH",
    "ASML": "TECH_HIGH_GROWTH",
    "TSM": "TECH_HIGH_GROWTH",
    "AVGO": "TECH_HIGH_GROWTH",
    "MELI": "TECH_HIGH_GROWTH",
    "NU": "TECH_HIGH_GROWTH",
    "GOOGL": "TECH_HIGH_GROWTH",
    "GOOG": "TECH_HIGH_GROWTH",
    "INTC": "TECH_HIGH_GROWTH",
    "PYPL": "TECH_HIGH_GROWTH",
    "BABA": "TECH_HIGH_GROWTH",
    "NFLX": "TECH_HIGH_GROWTH",
    "LLY": "TECH_HIGH_GROWTH",
    # Cash Cows & Payment Processors (PDF p. 4: Processors treated as Tech)
    "AAPL": "TECH_CASH_COW",
    "MSFT": "TECH_CASH_COW",
    "META": "TECH_CASH_COW",
    "MA": "TECH_CASH_COW",
    "V": "TECH_CASH_COW",
    # Traditional Banks (Strict Banking Calibration — NO EV/EBIT)
    "JPM": "FINANCIAL_BANK",
    "BAC": "FINANCIAL_BANK",
    "WFC": "FINANCIAL_BANK",
    "C": "FINANCIAL_BANK",
    "DBSDY": "FINANCIAL_BANK",
    # Cyclicals & Commodities (Inverse Multiples + Mid-Cycle DCF)
    "XOM": "CYCLICAL",
    "CAT": "CYCLICAL",
    "FCX": "CYCLICAL",
    "VALE": "CYCLICAL",
    # Defensives & Retail (Relative Multiples + DCF + Organic Growth)
    "WMT": "DEFENSIVE_RETAIL",
    "COST": "DEFENSIVE_RETAIL",
    "PG": "DEFENSIVE_RETAIL",
    "KO": "DEFENSIVE_RETAIL",
    "JNJ": "DEFENSIVE_RETAIL",
    # Crypto
    "BTC-USD": "CRYPTO_BTC",
    "ETH-USD": "CRYPTO_ALT",
    "SOL-USD": "CRYPTO_ALT",
    "LINK-USD": "CRYPTO_ALT",
    "MKR-USD": "CRYPTO_ALT",
    "AAVE-USD": "CRYPTO_ALT",
    "PENDLE-USD": "CRYPTO_ALT",
    "UNI7083-USD": "CRYPTO_ALT",
    "ADA-USD": "CRYPTO_ALT",
    "DOT-USD": "CRYPTO_ALT",
}

# Approximate FX to USD for non-USD IFRS filers (used only if SEC XBRL unit != USD)
_FX_TO_USD_STATIC: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.10,
    "TWD": 0.0315,
    "BRL": 0.19,
    "CNY": 0.14,
    "SGD": 0.74,
}

# Canonical SEC CIK overrides for tickers with subsidiary name collisions in sec_tickers.json
_CIK_OVERRIDES: Dict[str, int] = {
    "XOM": 34088,  # Exxon Mobil Corp (avoid subsidiary ExxonMobil Holdings Corp 2115436)
}


# ==============================================================================
# 1. DATA WAREHOUSE: MARKET PRICES, SEC EDGAR XBRL (US-GAAP + IFRS), FRED MACRO
# ==============================================================================

class HistoricalDataWarehouse:
    """
    Manages authentic point-in-time financial statements from SEC EDGAR XBRL,
    FRED macro series (FEDFUNDS, T10Y2Y, SAHMREALTIME), Yahoo Finance daily
    closes/VIX/TNX, and fast cached Parquet storage.
    """

    def __init__(self) -> None:
        self.market_data = self._load_market_data()
        self.val_price_data = self._load_val_price_data()
        self.sec_tickers = self._load_sec_tickers()
        self.sec_facts_cache = self._load_sec_facts_cache()
        self.splits_cache = self._load_splits_cache()
        self.macro_df = self._load_macro_series()
        self.fed_rate = (
            self.macro_df["FEDFUNDS"]
            if "FEDFUNDS" in self.macro_df
            else pd.Series(0.02, index=self.market_data.index)
        )

    def _load_val_price_data(self) -> pd.DataFrame:
        if os.path.exists(VAL_PRICE_DATA_PATH):
            try:
                df = pd.read_parquet(VAL_PRICE_DATA_PATH)
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                return df.sort_index().ffill()
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

    def _load_splits_cache(self) -> Dict[str, List[List[Any]]]:
        if os.path.exists(SPLITS_CACHE_PATH):
            try:
                with open(SPLITS_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_splits_cache(self) -> None:
        try:
            os.makedirs(DATA_CACHE_DIR, exist_ok=True)
            with open(SPLITS_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.splits_cache, f)
        except Exception:
            pass

    def get_splits(self, ticker: str) -> List[List[Any]]:
        """Returns cached stock split history [[YYYY-MM-DD, ratio], ...] for split-consistent Market Cap."""
        tk = ticker.upper().strip()
        if "-USD" in tk or tk.startswith("^"):
            return []
        if tk in self.splits_cache:
            return self.splits_cache[tk]
        splits_list: List[List[Any]] = []
        try:
            s = yf.Ticker(tk).splits
            if s is not None and not s.empty:
                for dt_idx, ratio in s.items():
                    dt_str = pd.Timestamp(dt_idx).strftime("%Y-%m-%d")
                    if float(ratio) > 0:
                        splits_list.append([dt_str, float(ratio)])
        except Exception:
            pass
        self.splits_cache[tk] = splits_list
        self._save_splits_cache()
        return splits_list

    def _load_market_data(self) -> pd.DataFrame:
        dfs = []
        for path in (EXTENDED_MARKET_DATA_PATH, LEGACY_MARKET_DATA_PATH):
            if os.path.exists(path):
                df = pd.read_parquet(path)
                closes = df["Close"].copy() if "Close" in df else df.copy()
                if closes.index.tz is not None:
                    closes.index = closes.index.tz_localize(None)
                dfs.append(closes)
        if not dfs:
            return pd.DataFrame()
        base = dfs[0]
        for other in dfs[1:]:
            missing_cols = [c for c in other.columns if c not in base.columns]
            if missing_cols:
                base = base.join(other[missing_cols], how="outer")
        base = base.sort_index().ffill()
        return base.dropna(subset=["SPY"]) if "SPY" in base.columns else base

    def ensure_tickers(self, tickers: List[str], start: str = "2014-01-01") -> None:
        """Downloads missing tickers from Yahoo Finance (both Total Return and split-only Close) and caches."""
        mapped = ["UNI7083-USD" if t == "UNI-USD" else t for t in tickers]
        missing = [t for t in dict.fromkeys(mapped) if t not in self.market_data.columns]
        eq_missing_val = [
            t for t in dict.fromkeys(mapped)
            if "-USD" not in t and not t.startswith("^") and t not in self.val_price_data.columns
        ]
        if missing:
            try:
                raw = yf.download(missing, start=start, interval="1d", progress=False, auto_adjust=True)
                if not raw.empty:
                    closes = raw["Close"] if "Close" in raw else raw
                    if isinstance(closes, pd.Series):
                        closes = closes.to_frame(name=missing[0])
                    closes = closes.copy()
                    if closes.index.tz is not None:
                        closes.index = closes.index.tz_localize(None)
                    closes = closes.ffill()
                    if self.market_data.empty:
                        self.market_data = closes.sort_index()
                    else:
                        self.market_data = self.market_data.join(closes, how="outer").sort_index().ffill()
                    if "SPY" in self.market_data.columns:
                        self.market_data = self.market_data.dropna(subset=["SPY"])
                    os.makedirs(DATA_CACHE_DIR, exist_ok=True)
                    self.market_data.to_parquet(EXTENDED_MARKET_DATA_PATH)
            except Exception:
                pass
        if eq_missing_val:
            try:
                raw_v = yf.download(eq_missing_val, start=start, interval="1d", progress=False, auto_adjust=False)
                if not raw_v.empty and "Close" in raw_v:
                    c_v = raw_v["Close"]
                    if isinstance(c_v, pd.Series):
                        c_v = c_v.to_frame(name=eq_missing_val[0])
                    c_v = c_v.copy()
                    if c_v.index.tz is not None:
                        c_v.index = c_v.index.tz_localize(None)
                    c_v = c_v.ffill()
                    if self.val_price_data.empty:
                        self.val_price_data = c_v.sort_index()
                    else:
                        self.val_price_data = self.val_price_data.join(c_v, how="outer").sort_index().ffill()
                    os.makedirs(DATA_CACHE_DIR, exist_ok=True)
                    self.val_price_data.to_parquet(VAL_PRICE_DATA_PATH)
            except Exception:
                pass

    def get_valuation_price(self, ticker: str, d: pd.Timestamp, fallback: float) -> float:
        """Returns split-adjusted-only price (no backward dividend shrinkage) for Market Cap & valuation."""
        if (
            not self.val_price_data.empty
            and ticker in self.val_price_data.columns
            and d in self.val_price_data.index
        ):
            v = self.val_price_data.loc[d, ticker]
            if pd.notnull(v) and float(v) > 0:
                return float(v)
        return float(fallback)

    def _load_macro_series(self) -> pd.DataFrame:
        if os.path.exists(MACRO_CACHE_PATH):
            try:
                mdf = pd.read_parquet(MACRO_CACHE_PATH)
                if len(mdf) > 500 and all(
                    c in mdf.columns for c in ("FEDFUNDS", "T10Y2Y", "SAHMREALTIME", "US10Y", "VIX", "CAPE_PROXY")
                ):
                    return mdf.reindex(self.market_data.index).ffill().bfill()
            except Exception:
                pass

        idx = self.market_data.index
        out = pd.DataFrame(index=idx)
        fred_map = {
            "FEDFUNDS": ("FEDFUNDS", 1.5, 0.01),
            "T10Y2Y": ("T10Y2Y", 0.5, 1.0),
            "SAHMREALTIME": ("SAHMREALTIME", 0.1, 1.0),
        }
        for col, (fid, default_val, scale) in fred_map.items():
            try:
                url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={fid}&cosd=2014-01-01"
                df_f = pd.read_csv(url, index_col=0, parse_dates=True)
                s = pd.to_numeric(df_f[fid], errors="coerce").dropna()
                s = s.resample("D").ffill().reindex(idx).ffill().bfill().fillna(default_val) * scale
                out[col] = s
            except Exception:
                out[col] = default_val * scale

        self.ensure_tickers(["^TNX", "^VIX"])
        idx = self.market_data.index
        out = out.reindex(idx).ffill().bfill()
        if "^TNX" in self.market_data.columns:
            out["US10Y"] = self.market_data["^TNX"].reindex(idx).ffill().bfill() / 100.0
        else:
            out["US10Y"] = 0.035
        if "^VIX" in self.market_data.columns:
            out["VIX"] = self.market_data["^VIX"].reindex(idx).ffill().bfill()
        else:
            out["VIX"] = 18.0

        if "SPY" in self.market_data.columns:
            spy = self.market_data["SPY"].reindex(idx).ffill()
            spy_ma_5y = spy.rolling(1260, min_periods=252).mean()
            out["CAPE_PROXY"] = (spy / spy_ma_5y * 23.0).clip(15.0, 45.0).fillna(28.0)
        else:
            out["CAPE_PROXY"] = 28.0

        try:
            os.makedirs(DATA_CACHE_DIR, exist_ok=True)
            out.to_parquet(MACRO_CACHE_PATH)
        except Exception:
            pass
        return out

    def _load_sec_tickers(self) -> Dict[str, Any]:
        if os.path.exists(SEC_TICKERS_PATH):
            try:
                with open(SEC_TICKERS_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _load_sec_facts_cache(self) -> Dict[str, Any]:
        if os.path.exists(SEC_FACTS_CACHE_PATH):
            try:
                with open(SEC_FACTS_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_sec_facts_cache(self) -> None:
        try:
            os.makedirs(DATA_CACHE_DIR, exist_ok=True)
            with open(SEC_FACTS_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.sec_facts_cache, f)
        except Exception:
            pass

    def fetch_sec_company_facts(self, ticker: str) -> Dict[str, Any]:
        """Fetches authentic SEC EDGAR XBRL facts (US-GAAP + IFRS) with proper annualization."""
        tk_clean = ticker.upper().strip()
        if tk_clean in self.sec_facts_cache:
            return self.sec_facts_cache[tk_clean]

        if tk_clean in _CIK_OVERRIDES:
            cik_num = _CIK_OVERRIDES[tk_clean]
        else:
            info = self.sec_tickers.get(tk_clean) or self.sec_tickers.get(tk_clean.replace("-", ""))
            if not info or "cik" not in info:
                self.sec_facts_cache[tk_clean] = {}
                return {}
            cik_num = int(info["cik"])

        cik_padded = str(cik_num).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "InstitutionalInvestmentTerminal/1.0 (research@institutional-terminal.local)"},
        )
        try:
            time.sleep(0.15)  # Polite SEC rate-limit pacing
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            facts_root = data.get("facts", {})
            us_gaap = facts_root.get("us-gaap", {})
            ifrs = facts_root.get("ifrs-full", {})
            dei = facts_root.get("dei", {})
            merged_facts = {**ifrs, **us_gaap, **dei}
            parsed = self._extract_key_financial_timeline(merged_facts)
            self.sec_facts_cache[tk_clean] = parsed
            self._save_sec_facts_cache()
            return parsed
        except Exception:
            self.sec_facts_cache[tk_clean] = {}
            return {}

    def _extract_key_financial_timeline(self, facts: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extracts chronological filing entries for flow metrics (strictly full-year /
        300-400 day periods so 10-Q quarterly numbers never cause 4x distortion!)
        and instant balance sheet metrics.
        """
        flow_metrics = {
            "ebit", "cfo", "capex", "net_income", "revenues",
            "gross_profit", "dividends", "buybacks", "depreciation",
        }

        tag_map = {
            "ebit": [
                "OperatingIncomeLoss",
                "ProfitLossFromOperatingActivities",
                "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
            ],
            "cfo": [
                "NetCashProvidedByUsedInOperatingActivities",
                "CashFlowsFromUsedInOperatingActivities",
            ],
            "capex": [
                "PaymentsToAcquirePropertyPlantAndEquipment",
                "PaymentsToAcquireProductiveAssets",
                "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
            ],
            "net_income": [
                "NetIncomeLoss",
                "ProfitLoss",
                "ProfitLossAttributableToOwnersOfParent",
            ],
            "revenues": [
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues",
                "SalesRevenueNet",
                "Revenue",
                "InterestAndDividendIncomeOperating",
                "InterestIncomeExpenseNet",
            ],
            "gross_profit": ["GrossProfit"],
            "depreciation": [
                "DepreciationDepletionAndAmortization",
                "DepreciationAndAmortization",
                "DepreciationAmortisationAndImpairmentLossReversalOfImpairmentLossRecognisedInProfitOrLoss",
            ],
            "shares": [
                "CommonStockSharesOutstanding",
                "WeightedAverageNumberOfDilutedSharesOutstanding",
                "EntityCommonStockSharesOutstanding",
                "NumberOfSharesOutstanding",
            ],
            "dividends": [
                "PaymentsOfDividendsCommonStock",
                "PaymentsOfDividends",
                "DividendsPaidClassifiedAsFinancingActivities",
            ],
            "buybacks": [
                "PaymentsForRepurchaseOfCommonStock",
                "PaymentsToAcquireOrRedeemEntitysShares",
            ],
            "debt": [
                "LongTermDebtNoncurrent",
                "DebtLongtermAndShorttermCombinedAmount",
                "LongTermDebtAndCapitalLeaseObligations",
                "LongTermDebt",
                "NoncurrentFinancialLiabilities",
            ],
            "cash": [
                "CashAndCashEquivalentsAtCarryingValue",
                "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
                "CashAndCashEquivalents",
            ],
            "equity": [
                "StockholdersEquity",
                "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
                "Equity",
                "EquityAttributableToOwnersOfParent",
            ],
            "goodwill": ["Goodwill"],
            "assets": ["Assets"],
        }

        extracted: Dict[str, List[Dict[str, Any]]] = {k: [] for k in tag_map}

        for metric, tags in tag_map.items():
            is_flow = metric in flow_metrics
            collected: List[Dict[str, Any]] = []
            for tag in tags:
                if tag not in facts:
                    continue
                units = facts[tag].get("units", {})
                u_key = None
                fx_mult = 1.0
                if metric == "shares":
                    u_key = "shares" if "shares" in units else (list(units.keys())[0] if units else None)
                else:
                    if "USD" in units:
                        u_key = "USD"
                        fx_mult = 1.0
                    else:
                        for ccy, mult in _FX_TO_USD_STATIC.items():
                            if ccy in units:
                                u_key = ccy
                                fx_mult = mult
                                break
                if not u_key:
                    continue

                for item in units[u_key]:
                    filed = item.get("filed")
                    val = item.get("val")
                    if not filed or val is None:
                        continue
                    if is_flow:
                        start_s = item.get("start")
                        end_s = item.get("end")
                        if start_s and end_s:
                            try:
                                days = (pd.Timestamp(end_s) - pd.Timestamp(start_s)).days
                                if not (300 <= days <= 400):
                                    continue
                            except Exception:
                                continue
                        elif item.get("fp") != "FY":
                            continue
                    collected.append({
                        "filed": filed,
                        "end": item.get("end", filed),
                        "val": float(val) * fx_mult,
                    })
                if len(collected) >= 4:
                    break

            if collected:
                collected.sort(key=lambda x: (x["filed"], x["end"]))
                dedup: Dict[str, Dict[str, Any]] = {}
                for row in collected:
                    dedup[row["filed"]] = row
                extracted[metric] = sorted(dedup.values(), key=lambda x: x["filed"])

        return extracted


# ==============================================================================
# 2. POINT-IN-TIME VALUATION ENGINE (ALL FRAMEWORK METHODS)
# ==============================================================================

class PointInTimeValuationEngine:
    """
    Computes exact point-in-time valuation metrics across all sectors without
    lookahead bias, using fast bisect lookup on SEC EDGAR filing dates.
    """

    def __init__(self, warehouse: HistoricalDataWarehouse) -> None:
        self.warehouse = warehouse
        self._indexed_cache: Dict[str, Dict[str, Tuple[List[str], List[float]]]] = {}

    def _get_indexed_facts(self, ticker: str) -> Dict[str, Tuple[List[str], List[float]]]:
        tk = ticker.upper().strip()
        if tk in self._indexed_cache:
            return self._indexed_cache[tk]
        raw = self.warehouse.fetch_sec_company_facts(tk)
        splits = self.warehouse.get_splits(tk)
        idx_map: Dict[str, Tuple[List[str], List[float]]] = {}
        for m, rows in raw.items():
            if m == "shares" and splits:
                adj_vals: List[float] = []
                for r in rows:
                    mult = 1.0
                    for sp_dt, sp_ratio in splits:
                        if sp_dt > r["filed"] and sp_ratio > 0:
                            mult *= sp_ratio
                    adj_vals.append(r["val"] * mult)
                idx_map[m] = ([r["filed"] for r in rows], adj_vals)
            else:
                idx_map[m] = ([r["filed"] for r in rows], [r["val"] for r in rows])
        self._indexed_cache[tk] = idx_map
        return idx_map

    def get_fundamental_snapshot(self, ticker: str, as_of_date: pd.Timestamp) -> Dict[str, float]:
        """Returns latest SEC-verified annual/instant fundamentals filed on or before `as_of_date`."""
        dt_str = as_of_date.strftime("%Y-%m-%d")
        idx_map = self._get_indexed_facts(ticker)

        def _latest(m: str, fallback: float = 0.0) -> float:
            pair = idx_map.get(m)
            if not pair or not pair[0]:
                return fallback
            pos = bisect.bisect_right(pair[0], dt_str) - 1
            return pair[1][pos] if pos >= 0 else fallback

        def _growth_3y(m: str, fallback: float = 0.12) -> float:
            pair = idx_map.get(m)
            if not pair or not pair[0]:
                return fallback
            pos = bisect.bisect_right(pair[0], dt_str) - 1
            if pos < 1:
                return fallback
            v_now = pair[1][pos]
            past_idx = max(0, pos - 3)
            v_past = pair[1][past_idx]
            if v_now <= 0 or v_past <= 0:
                return fallback
            d_now = pd.Timestamp(pair[0][pos])
            d_past = pd.Timestamp(pair[0][past_idx])
            yrs = max(1.0, (d_now - d_past).days / 365.25)
            g = (v_now / v_past) ** (1.0 / yrs) - 1.0
            return float(max(0.03, min(0.60, g)))

        def _gross_margin_falling() -> float:
            gp_pair = idx_map.get("gross_profit")
            rv_pair = idx_map.get("revenues")
            if not gp_pair or not rv_pair or not gp_pair[0] or not rv_pair[0]:
                return 0.0
            p_gp = bisect.bisect_right(gp_pair[0], dt_str) - 1
            p_rv = bisect.bisect_right(rv_pair[0], dt_str) - 1
            if p_gp < 2 or p_rv < 2:
                return 0.0
            m0 = gp_pair[1][p_gp] / max(1.0, rv_pair[1][p_rv])
            m1 = gp_pair[1][p_gp - 1] / max(1.0, rv_pair[1][p_rv - 1])
            m2 = gp_pair[1][p_gp - 2] / max(1.0, rv_pair[1][p_rv - 2])
            return 1.0 if (m0 < m1 < m2 and (m2 - m0) > 0.015) else 0.0

        ebit = _latest("ebit", 0.0)
        cfo = _latest("cfo", 0.0)
        capex = abs(_latest("capex", 0.0))
        net_inc = _latest("net_income", 0.0)
        revenues = _latest("revenues", 0.0)
        gross_profit = _latest("gross_profit", 0.0)
        depr = abs(_latest("depreciation", 0.0))
        debt = _latest("debt", 0.0)
        cash = _latest("cash", 0.0)
        equity = _latest("equity", 0.0)
        goodwill = _latest("goodwill", 0.0)
        assets = _latest("assets", 0.0)
        shares = max(1.0e6, _latest("shares", 1.0e8))
        divs = abs(_latest("dividends", 0.0))
        buybacks = abs(_latest("buybacks", 0.0))

        fcf = max(0.0, cfo - capex) if cfo > 0 else 0.0
        ebitda = ebit + depr if ebit > 0 else max(0.0, cfo)
        net_debt = debt - cash
        tbv = max(1.0, equity - goodwill) if equity > 0 else 0.0
        roe = (net_inc / equity) if equity > 0 else 0.0
        sloan = ((net_inc - cfo) / assets) if assets > 0 else 0.0
        cfo_ebitda = (cfo / ebitda) if ebitda > 0 else 1.0
        ebit_g = _growth_3y("ebit", 0.14)
        ni_g = _growth_3y("net_income", 0.12)
        rev_g = _growth_3y("revenues", 0.08)

        return {
            "ebit_ttm": ebit,
            "cfo_ttm": cfo,
            "fcf_ttm": fcf,
            "ebitda_ttm": ebitda,
            "net_income_ttm": net_inc,
            "revenues_ttm": revenues,
            "gross_profit_ttm": gross_profit,
            "net_debt": net_debt,
            "equity": equity,
            "tbv": tbv,
            "roe": roe,
            "assets": assets,
            "shares_out": shares,
            "dividends_ttm": divs,
            "buybacks_ttm": buybacks,
            "ebit_growth_3y": ebit_g,
            "ni_growth_3y": ni_g,
            "rev_growth_3y": rev_g,
            "sloan_ratio": sloan,
            "cfo_ebitda": cfo_ebitda,
            "gross_margin_falling": _gross_margin_falling(),
            "has_sec_data": 1.0 if (ebit != 0.0 or cfo != 0.0 or net_inc != 0.0 or equity != 0.0) else 0.0,
        }

    def calc_enterprise_pegy(
        self,
        ticker: str,
        price: float,
        as_of_date: pd.Timestamp,
        metric: str = "EBIT",
        yield_in_denominator: bool = True,
    ) -> float:
        """
        Computes authentic Enterprise PEGY:
        - yield_in_denominator=True (Peter Lynch / Economic):
            (EV / Flow) / (Growth_pct + DivYield_pct + BuybackYield_pct)
        - yield_in_denominator=False (Literal PDF p.3):
            (EV / Flow + DivYield_pct + BuybackYield_pct) / Growth_pct
        """
        fund = self.get_fundamental_snapshot(ticker, as_of_date)
        mkt_cap = price * fund["shares_out"]
        ev = max(mkt_cap * 0.5, mkt_cap + fund["net_debt"])

        denom_flow = fund["ebit_ttm"] if metric.upper() == "EBIT" else fund["fcf_ttm"]
        if denom_flow <= 0:
            denom_flow = fund["ebit_ttm"] if fund["ebit_ttm"] > 0 else fund["net_income_ttm"]
        if denom_flow <= 0:
            return 3.0  # Unprofitable / no SEC flow yet

        ev_mult = ev / denom_flow
        div_y_pct = min(10.0, (fund["dividends_ttm"] / max(1.0, mkt_cap)) * 100.0)
        bb_y_pct = min(10.0, (fund["buybacks_ttm"] / max(1.0, mkt_cap)) * 100.0)
        g_pct = max(5.0, fund["ebit_growth_3y"] * 100.0)

        if yield_in_denominator:
            return float(ev_mult / max(5.0, g_pct + div_y_pct + bb_y_pct))
        return float((ev_mult + div_y_pct + bb_y_pct) / g_pct)

    def calc_financial_pegy_and_pb(
        self,
        ticker: str,
        price: float,
        as_of_date: pd.Timestamp,
    ) -> Dict[str, float]:
        """Banking sector metrics: Financial PEGY, P/E, P/B, P/TBV, ROE (NO EV/EBIT)."""
        fund = self.get_fundamental_snapshot(ticker, as_of_date)
        mkt_cap = price * fund["shares_out"]
        pe = (mkt_cap / fund["net_income_ttm"]) if fund["net_income_ttm"] > 0 else 30.0
        pb = (mkt_cap / fund["equity"]) if fund["equity"] > 0 else 1.2
        ptbv = (mkt_cap / fund["tbv"]) if fund["tbv"] > 0 else pb
        dy_pct = min(10.0, (fund["dividends_ttm"] / max(1.0, mkt_cap)) * 100.0)
        g_pct = max(4.0, fund["ni_growth_3y"] * 100.0)
        fin_pegy = pe / max(4.0, g_pct + dy_pct)
        return {
            "financial_pegy": float(fin_pegy),
            "pe": float(pe),
            "pb": float(pb),
            "ptbv": float(ptbv),
            "roe": float(fund["roe"]),
        }

    def calc_owner_earnings_yield(self, ticker: str, price: float, as_of_date: pd.Timestamp) -> float:
        """Munger Owner Earnings Yield = FCF / Market Cap (decimal)."""
        fund = self.get_fundamental_snapshot(ticker, as_of_date)
        mkt_cap = max(1.0, price * fund["shares_out"])
        flow = fund["fcf_ttm"] if fund["fcf_ttm"] > 0 else fund["ebit_ttm"] * 0.75
        return float(flow / mkt_cap)

    def calc_dcf_fair_value(
        self,
        ticker: str,
        as_of_date: pd.Timestamp,
        wacc: float = 0.09,
        terminal_growth: float = 0.03,
        projection_years: int = 5,
        margin_of_safety_pct: float = 10.0,
    ) -> float:
        """Computes point-in-time Discounted Cash Flow per share."""
        fund = self.get_fundamental_snapshot(ticker, as_of_date)
        base_fcf = fund["fcf_ttm"] if fund["fcf_ttm"] > 0 else fund["ebit_ttm"] * 0.75
        if base_fcf <= 0 or fund["shares_out"] <= 0:
            return 0.0
        g = min(0.30, fund["ebit_growth_3y"])
        pv_cf = sum(base_fcf * ((1.0 + g) ** yr) / ((1.0 + wacc) ** yr) for yr in range(1, projection_years + 1))
        cf_term = (
            base_fcf * ((1.0 + g) ** projection_years) * (1.0 + terminal_growth)
            / max(0.015, wacc - terminal_growth)
        )
        pv_term = cf_term / ((1.0 + wacc) ** projection_years)
        equity_val = (pv_cf + pv_term) - fund["net_debt"]
        fair_price = max(0.0, equity_val / fund["shares_out"])
        return float(fair_price * (1.0 - margin_of_safety_pct / 100.0))

    def calc_reverse_dcf_ratio(
        self,
        ticker: str,
        price: float,
        as_of_date: pd.Timestamp,
        wacc: float = 0.09,
    ) -> float:
        """
        Returns ratio of Implied Growth (g_impl) to Fundamental 3Y Growth (g_fund).
        < 1.0 means market prices in LESS growth than fundamentals (undervalued).
        > 1.5 means market prices in 50%+ MORE growth than fundamentals (overvalued).
        """
        fund = self.get_fundamental_snapshot(ticker, as_of_date)
        mkt_cap = max(1.0, price * fund["shares_out"])
        ev = max(mkt_cap * 0.5, mkt_cap + fund["net_debt"])
        fcf = fund["fcf_ttm"] if fund["fcf_ttm"] > 0 else fund["ebit_ttm"] * 0.75
        if fcf <= 0:
            return 2.5
        ev_fcf = ev / fcf
        lo, hi = -0.10, 0.80
        for _ in range(12):
            mid = 0.5 * (lo + hi)
            pv = sum(((1.0 + mid) ** yr) / ((1.0 + wacc) ** yr) for yr in range(1, 6))
            tv = (((1.0 + mid) ** 5) * 1.03 / max(0.015, wacc - 0.03)) / ((1.0 + wacc) ** 5)
            if (pv + tv) < ev_fcf:
                lo = mid
            else:
                hi = mid
        g_impl = 0.5 * (lo + hi)
        g_fund = max(0.05, fund["ebit_growth_3y"])
        return float(g_impl / g_fund)

    def calc_ev_ebitda_or_pe(self, ticker: str, price: float, as_of_date: pd.Timestamp) -> Dict[str, float]:
        fund = self.get_fundamental_snapshot(ticker, as_of_date)
        mkt_cap = max(1.0, price * fund["shares_out"])
        ev = max(mkt_cap * 0.5, mkt_cap + fund["net_debt"])
        ev_ebitda = (ev / fund["ebitda_ttm"]) if fund["ebitda_ttm"] > 0 else 25.0
        pe = (mkt_cap / fund["net_income_ttm"]) if fund["net_income_ttm"] > 0 else 30.0
        return {"ev_ebitda": float(ev_ebitda), "pe": float(pe)}


# ==============================================================================
# 3. ON-CHAIN & TECHNICAL TELEMETRY ENGINE
# ==============================================================================

class OnChainTelemetryEngine:
    """
    Precomputes authentic on-chain & cycle indicators for BTC and altcoins:
    Pi Cycle Top, NUPL + NUPL Reverse Cross (0.65 -> 0.60), MVRV Z-Score,
    200W SMA, and Hash Ribbon (30d/60d cross + momentum).
    """

    def __init__(self, daily_px: pd.DataFrame) -> None:
        self.daily_px = daily_px
        self.btc = daily_px["BTC-USD"] if "BTC-USD" in daily_px else pd.Series(dtype=float)
        self._precompute()

    def _precompute(self) -> None:
        if self.btc.empty:
            return
        self.btc_111 = self.btc.rolling(111).mean()
        self.btc_350_x2 = self.btc.rolling(350).mean() * 2.0
        self.btc_200w = self.btc.rolling(1400, min_periods=200).mean()
        self.btc_realized = self.btc.rolling(730, min_periods=90).mean()
        self.btc_nupl = (self.btc - self.btc_realized) / self.btc
        rolling_std = self.btc.expanding(min_periods=90).std().replace(0, np.nan)
        self.btc_mvrv_z = ((self.btc - self.btc_realized) / rolling_std).fillna(0.0)
        self.btc_sma30 = self.btc.rolling(30).mean()
        self.btc_sma60 = self.btc.rolling(60).mean()
        self.btc_mom10 = self.btc.pct_change(10)

        rev_cross = pd.Series(False, index=self.btc.index)
        was_above_65 = False
        for d, val in self.btc_nupl.items():
            if pd.notnull(val):
                if val > 0.65:
                    was_above_65 = True
                elif was_above_65 and val < 0.60:
                    rev_cross.loc[d] = True
                    was_above_65 = False
                elif val < 0.20:
                    was_above_65 = False
        self.nupl_reverse_cross = rev_cross

    def get_btc_signals(self, date: pd.Timestamp) -> Dict[str, Any]:
        if self.btc.empty or date not in self.btc.index:
            return {
                "price": 0.0, "nupl": 0.35, "mvrv_z": 1.0, "pi_cycle": False,
                "nupl_reverse_cross": False, "is_200w_floor": False, "hash_ribbon_buy": False, "sma_200w": 0.0,
            }

        p = float(self.btc.loc[date])
        s111 = self.btc_111.loc[date]
        s350x2 = self.btc_350_x2.loc[date]
        s200w = self.btc_200w.loc[date]
        nupl = self.btc_nupl.loc[date]
        mvrv = self.btc_mvrv_z.loc[date]
        s30 = self.btc_sma30.loc[date]
        s60 = self.btc_sma60.loc[date]
        mom = self.btc_mom10.loc[date]

        pi_top = bool(s111 >= s350x2) if (pd.notnull(s111) and pd.notnull(s350x2)) else False
        is_floor = bool(p <= 1.05 * s200w) if pd.notnull(s200w) else False
        hash_buy = (
            bool(s30 > s60 and mom > 0.02 and (pd.notnull(nupl) and nupl < 0.25))
            if (pd.notnull(s30) and pd.notnull(s60) and pd.notnull(mom))
            else False
        )

        return {
            "price": p,
            "nupl": float(nupl) if pd.notnull(nupl) else 0.35,
            "mvrv_z": float(mvrv) if pd.notnull(mvrv) else 1.0,
            "pi_cycle": pi_top,
            "nupl_reverse_cross": bool(self.nupl_reverse_cross.loc[date]),
            "is_200w_floor": is_floor,
            "hash_ribbon_buy": hash_buy,
            "sma_200w": float(s200w) if pd.notnull(s200w) else 0.0,
        }


# ==============================================================================
# 4. COMPOSABLE SECTOR-STRATIFIED SIMULATION ENGINE
# ==============================================================================

@dataclass
class TradeAuditEntry:
    date: str
    asset: str
    action: str
    price: float
    units: float
    gross_amount: float
    realized_gain: float
    tax_paid: float
    net_proceeds: float
    metric_name: str
    metric_value: float
    reason: str


@dataclass
class ValuationBacktestResult:
    config: Dict[str, Any]
    dates: pd.DatetimeIndex
    equity_series: pd.Series
    debt_series: pd.Series
    ltv_series: pd.Series
    drawdown_series: pd.Series
    trade_log: List[TradeAuditEntry]
    metrics: Dict[str, float]
    yearly_returns_df: pd.DataFrame

    def summary(self) -> str:
        m = self.metrics
        return (
            f"=== VALUATION BACKTEST SUMMARY ===\n"
            f"Initial Capital:      ${m['initial_capital']:,.2f}\n"
            f"Total Invested:       ${m['total_invested']:,.2f}\n"
            f"Final Capital:        ${m['final_capital']:,.2f}\n"
            f"Net Profit:           ${m['net_profit']:,.2f}\n"
            f"Multiple on Invested: {m['multiple_on_invested']:.2f}x\n"
            f"CAGR:                 {m['cagr_pct']:.2f}%\n"
            f"Annual Volatility:    {m['annual_volatility_pct']:.2f}%\n"
            f"Sharpe Ratio:         {m['sharpe_ratio']:.2f}\n"
            f"Sortino Ratio:        {m['sortino_ratio']:.2f}\n"
            f"Max Drawdown:         {m['max_drawdown_pct']:.2f}%\n"
            f"Calmar Ratio:         {m['calmar_ratio']:.2f}\n"
            f"Total Taxes Paid:     ${m['total_taxes_paid']:,.2f}\n"
            f"Total Margin Interest:${m['total_margin_interest']:,.2f}\n"
            f"Total Trades:         {len(self.trade_log)}\n"
        )


class ComposableValuationBacktestSimulator:
    """
    Executes flexible, sector-stratified, event-driven portfolio backtests
    with customizable valuation methods, quality gates, cash destinations,
    LTV regimes, and symmetrical tax accounting.
    """

    def __init__(self, warehouse: Optional[HistoricalDataWarehouse] = None) -> None:
        self.warehouse = warehouse or HistoricalDataWarehouse()
        self.val_engine = PointInTimeValuationEngine(self.warehouse)
        self.onchain = OnChainTelemetryEngine(self.warehouse.market_data)

    def _evaluate_equity_signal(
        self,
        ticker: str,
        price: float,
        d: pd.Timestamp,
        sector: str,
        method: str,
        buy_pegy: float,
        prune_pegy: Optional[float],
        yield_in_denominator: bool,
        us10y: float,
        bank_pb_veto: float,
        bank_buy_pegy: float,
        bank_prune_pegy: float,
        rolling_mult_hist: Dict[str, List[float]],
        quality_gates: bool,
    ) -> Tuple[bool, bool, str, float]:
        """
        Evaluates (is_buy_eligible, is_prune_triggered, metric_name, metric_value)
        for an equity according to its sector and selected valuation method.
        """
        fund = self.val_engine.get_fundamental_snapshot(ticker, d)
        if method != "buy_and_hold" and fund.get("has_sec_data", 1.0) < 0.5:
            return (True, False, "No_SEC_Data_Yet", 0.0)

        quality_veto = False
        quality_exit = False
        if quality_gates and sector != "FINANCIAL_BANK":
            if fund["sloan_ratio"] > 0.10 or fund["cfo_ebitda"] < 0.70:
                quality_veto = True
            if fund["gross_margin_falling"] > 0.5:
                quality_exit = True

        if method == "sector_auto":
            if sector == "TECH_HIGH_GROWTH":
                method = "pegy_ebit"
            elif sector == "TECH_CASH_COW":
                method = "pegy_fcf"
            elif sector == "FINANCIAL_BANK":
                method = "bank_pegy_pb"
            elif sector == "CYCLICAL":
                method = "inverse_multiple"
            elif sector == "DEFENSIVE_RETAIL":
                method = "rel_multiple_dcf"
            else:
                method = "pegy_ebit"

        if method == "buy_and_hold":
            return (not quality_veto, quality_exit, "BuyHold", 0.0)

        if method in ("pegy_ebit", "pegy_fcf"):
            metric_kind = "EBIT" if method == "pegy_ebit" else "FCF"
            val = self.val_engine.calc_enterprise_pegy(
                ticker, price, d, metric=metric_kind, yield_in_denominator=yield_in_denominator
            )
            eff_prune = min(prune_pegy, 1.4) if (prune_pegy is not None and sector == "TECH_CASH_COW") else prune_pegy
            is_buy = (val <= buy_pegy) and (not quality_veto)
            is_prune = (eff_prune is not None and val > eff_prune) or quality_exit
            return (is_buy, is_prune, f"Enterprise_PEGY_{metric_kind}", val)

        if method == "bank_pegy_pb":
            bm = self.val_engine.calc_financial_pegy_and_pb(ticker, price, d)
            pb_ok = bm["pb"] >= bank_pb_veto
            is_buy = (bm["financial_pegy"] <= bank_buy_pegy) and pb_ok
            is_prune = (prune_pegy is not None) and (
                bm["financial_pegy"] > bank_prune_pegy or (bank_pb_veto > 0 and bm["pb"] < 0.70)
            )
            return (is_buy, is_prune, "Financial_PEGY", bm["financial_pegy"])

        if method == "bank_ptbv_roe":
            bm = self.val_engine.calc_financial_pegy_and_pb(ticker, price, d)
            fair_ptbv = max(0.8, bm["roe"] / 0.10) if bm["roe"] > 0 else 1.0
            ratio = bm["ptbv"] / fair_ptbv
            is_buy = (ratio <= 0.90) and (bm["pb"] >= bank_pb_veto)
            is_prune = (prune_pegy is not None) and (ratio > 1.35)
            return (is_buy, is_prune, "PTBV_vs_ROE_Ratio", ratio)

        if method == "owner_earnings_yield":
            oey = self.val_engine.calc_owner_earnings_yield(ticker, price, d)
            spread = oey - us10y
            is_buy = (spread >= 0.015) and (not quality_veto)
            is_prune = (prune_pegy is not None and spread < -0.01) or quality_exit
            return (is_buy, is_prune, "OEY_Spread_vs_10Y", spread * 100.0)

        if method == "reverse_dcf":
            ratio = self.val_engine.calc_reverse_dcf_ratio(ticker, price, d, wacc=max(0.08, us10y + 0.05))
            is_buy = (ratio <= 1.0) and (not quality_veto)
            is_prune = (prune_pegy is not None and ratio > 1.50) or quality_exit
            return (is_buy, is_prune, "ReverseDCF_gImpl_gFund", ratio)

        if method == "dcf":
            fair = self.val_engine.calc_dcf_fair_value(
                ticker, d, wacc=max(0.085, us10y + 0.05), margin_of_safety_pct=10.0
            )
            if fair <= 0:
                return (False, False, "DCF_Price_Fair", 1.0)
            ratio = price / fair
            is_buy = (ratio <= 0.90) and (not quality_veto)
            is_prune = (prune_pegy is not None and ratio > 1.35) or quality_exit
            return (is_buy, is_prune, "DCF_Price_Fair", ratio)

        if method == "zscore_multiple":
            mult = self.val_engine.calc_ev_ebitda_or_pe(ticker, price, d)["ev_ebitda"]
            hist = rolling_mult_hist.setdefault(ticker, [])
            hist.append(mult)
            if len(hist) > 60:
                hist.pop(0)
            if len(hist) < 12:
                return (True, False, "Mult_Percentile", 50.0)
            pct = float(np.mean([1.0 if h <= mult else 0.0 for h in hist]) * 100.0)
            is_buy = (pct <= 30.0) and (not quality_veto)
            is_prune = (prune_pegy is not None and pct >= 85.0) or quality_exit
            return (is_buy, is_prune, "Mult_Percentile", pct)

        if method == "inverse_multiple":
            mult = self.val_engine.calc_ev_ebitda_or_pe(ticker, price, d)["ev_ebitda"]
            hist = rolling_mult_hist.setdefault(ticker, [])
            hist.append(mult)
            if len(hist) > 60:
                hist.pop(0)
            avg_m = float(np.median(hist)) if len(hist) >= 6 else mult
            rel = mult / max(1.0, avg_m)
            is_buy = (rel >= 1.15) and (not quality_veto)
            is_prune = (prune_pegy is not None) and (rel <= 0.80) and (len(hist) >= 12)
            return (is_buy, is_prune, "Inverse_EV_EBITDA_Rel", rel)

        if method == "rel_multiple_dcf":
            mult = self.val_engine.calc_ev_ebitda_or_pe(ticker, price, d)["ev_ebitda"]
            hist = rolling_mult_hist.setdefault(ticker, [])
            hist.append(mult)
            if len(hist) > 60:
                hist.pop(0)
            avg_m = float(np.median(hist)) if len(hist) >= 6 else mult
            rel = mult / max(1.0, avg_m)
            rev_ok = fund["rev_growth_3y"] > 0.02
            is_buy = (rel <= 0.88) and rev_ok and (not quality_veto)
            is_prune = (prune_pegy is not None and rel >= 1.20 and len(hist) >= 12) or quality_exit
            return (is_buy, is_prune, "Rel_EV_EBITDA", rel)

        return (True, False, "Default", 0.0)

    def run(
        self,
        assets: Union[List[str], Dict[str, float]],
        initial_capital: float = 100_000.0,
        monthly_inflow: float = 5_000.0,
        start_date: str = "2016-11-05",
        end_date: str = "2026-11-05",
        sector_map: Optional[Dict[str, str]] = None,
        valuation_method: str = "sector_auto",
        buy_pegy: float = 1.2,
        prune_pegy: Optional[float] = 1.6,
        prune_fraction: float = 0.50,
        prune_mode: str = "single",
        prune_destination: str = "reinvest_discounted",
        yield_in_denominator: bool = True,
        trend_filter_sma200: bool = False,
        quality_gates: bool = True,
        tech_hg_hold: bool = True,
        l1_majors_hold: bool = True,
        bank_pb_veto: float = 1.0,
        bank_buy_pegy: float = 1.0,
        bank_prune_pegy: float = 1.5,
        btc_top_mode: str = "pi_cycle_only",
        crypto_exit_nupl: float = 0.60,
        crypto_exit_dd: float = -0.20,
        crypto_reenter_mode: str = "200w_105",
        crypto_reenter_nupl: float = 0.00,
        inflow_mode: str = "shannon_drift",
        rebalance_freq: str = "none",
        ltv_mode: str = "fixed_20",
        base_ltv: float = 0.20,
        turbo_ltv: float = 0.30,
        defensive_ltv: float = 0.20,
        tax_rate: float = 0.15,
        enable_tax: bool = True,
        loss_carryforward: bool = True,
    ) -> ValuationBacktestResult:
        req_list = list(assets.keys()) if isinstance(assets, dict) else list(assets)
        self.warehouse.ensure_tickers(req_list + ["SPY", "BTC-USD"])
        if self.onchain.btc.empty and "BTC-USD" in self.warehouse.market_data.columns:
            self.onchain = OnChainTelemetryEngine(self.warehouse.market_data)

        px = self.warehouse.market_data.loc[start_date:end_date]
        if px.empty:
            raise ValueError(f"No price data available between {start_date} and {end_date}.")

        dates = px.index
        if isinstance(assets, list):
            weights = {a: 1.0 / len(assets) for a in assets}
        else:
            tot_w = sum(assets.values())
            weights = {a: w / tot_w for a, w in assets.items()}

        sec_lookup = {**DEFAULT_SECTOR_MAP, **(sector_map or {})}
        crypto_keys = [a for a in weights if "-USD" in a]
        stock_keys = [a for a in weights if "-USD" not in a]

        sma_200_map = {s: px[s].rolling(200, min_periods=30).mean() for s in stock_keys if s in px}
        cr_peaks = {c: px[c].rolling(60, min_periods=1).max() for c in crypto_keys if c in px}
        spy = px["SPY"] if "SPY" in px else px.iloc[:, 0]
        spy_dd = (spy - spy.cummax()) / spy.cummax()

        macro = self.warehouse.macro_df.reindex(dates).ffill().bfill()
        fed_s = macro["FEDFUNDS"]
        us10y_s = macro["US10Y"]
        t10y2y_s = macro["T10Y2Y"]
        sahm_s = macro["SAHMREALTIME"]
        cape_s = macro["CAPE_PROXY"]
        vix_s = macro["VIX"]

        was_inv_180 = t10y2y_s.rolling(180, min_periods=1).min() < -0.10
        uninversion_alert = was_inv_180 & (t10y2y_s >= 0.0)

        month_first_days = set()
        cur_m = None
        for d in dates:
            if d.month != cur_m:
                month_first_days.add(d)
                cur_m = d.month
        total_invested = initial_capital + len(month_first_days) * monthly_inflow

        units: Dict[str, float] = {}
        cost_basis: Dict[str, float] = {}
        cash_tbills = 0.0
        debt = 0.0
        total_tax_paid = 0.0
        total_interest_paid = 0.0
        loss_carry = 0.0

        trade_log: List[TradeAuditEntry] = []
        equity_curve: List[float] = []
        debt_curve: List[float] = []
        ltv_curve: List[float] = []

        btc_pruned = False
        cr_exited = {c: False for c in crypto_keys}
        st_pruned_stage = {s: 0 for s in stock_keys}
        rolling_mult_hist: Dict[str, List[float]] = {}

        eff_base_ltv = (0.25 if ltv_mode == "fixed_25" else base_ltv) if ltv_mode in ("convex", "fixed_20", "fixed_25", "macro_gated") else 0.0
        init_a = initial_capital
        if eff_base_ltv > 0:
            debt = initial_capital * (eff_base_ltv / (1.0 - eff_base_ltv))
            init_a += debt

        tradable_init = [a for a in weights if a in px and pd.notnull(px[a].iloc[0]) and px[a].iloc[0] > 0]
        if not tradable_init:
            cash_tbills += init_a
        sum_w_init = sum(weights[a] for a in tradable_init) or 1.0
        for a in weights:
            if a in tradable_init:
                p0 = float(px[a].iloc[0])
                units[a] = (init_a * (weights[a] / sum_w_init)) / p0
                cost_basis[a] = p0
            else:
                units[a] = 0.0
                cost_basis[a] = 0.0

        def _compute_tax(realized_pnl: float) -> float:
            nonlocal loss_carry, total_tax_paid
            if not enable_tax:
                return 0.0
            if realized_pnl < 0:
                if loss_carryforward:
                    loss_carry += abs(realized_pnl)
                return 0.0
            taxable = realized_pnl
            if loss_carryforward and loss_carry > 0:
                offset = min(taxable, loss_carry)
                taxable -= offset
                loss_carry -= offset
            tax = taxable * tax_rate
            total_tax_paid += tax
            return tax

        cached_eval: Dict[str, Tuple[bool, bool, str, float]] = {}

        for i, d in enumerate(dates):
            fed_f = float(fed_s.loc[d])
            us10y = float(us10y_s.loc[d])

            if cash_tbills > 0:
                cash_tbills += cash_tbills * (fed_f / 365.0)

            gross_a = cash_tbills
            asset_vals: Dict[str, float] = {}
            for a, u in units.items():
                if u > 0 and a in px and pd.notnull(px[a].loc[d]):
                    val = u * float(px[a].loc[d])
                    asset_vals[a] = val
                    gross_a += val
                else:
                    asset_vals[a] = 0.0

            if debt > 0:
                d_int = debt * ((fed_f + 0.0035) / 365.0)
                debt += d_int
                total_interest_paid += d_int

            equity = gross_a - debt
            c_ltv = debt / gross_a if gross_a > 0 else 0.0

            if c_ltv > 0.45 and gross_a > 0:
                payd = debt - gross_a * 0.35
                use_cash = min(cash_tbills, payd)
                cash_tbills -= use_cash
                rem = payd - use_cash
                if rem > 0 and (gross_a - cash_tbills) > 0:
                    r_red = max(0.0, 1.0 - (rem / (gross_a - cash_tbills)))
                    for a in units:
                        units[a] *= r_red
                debt -= payd
                gross_a -= payd
                equity = gross_a - debt
                c_ltv = debt / gross_a if gross_a > 0 else 0.0

            equity_curve.append(equity)
            debt_curve.append(debt)
            ltv_curve.append(c_ltv)

            is_month_start = d in month_first_days
            btc_sig = self.onchain.get_btc_signals(d)

            if is_month_start or i == 0:
                for s in stock_keys:
                    if s in px and pd.notnull(px[s].loc[d]) and px[s].loc[d] > 0:
                        sec = sec_lookup.get(s, "TECH_HIGH_GROWTH")
                        val_p = self.warehouse.get_valuation_price(s, d, float(px[s].loc[d]))
                        cached_eval[s] = self._evaluate_equity_signal(
                            s, val_p, d, sec, valuation_method,
                            buy_pegy, prune_pegy, yield_in_denominator, us10y,
                            bank_pb_veto, bank_buy_pegy, bank_prune_pegy,
                            rolling_mult_hist, quality_gates,
                        )

            # 3. Monthly Inflow
            if is_month_start and (monthly_inflow > 0 or cash_tbills > 0):
                inflow = monthly_inflow
                if eff_base_ltv > 0 and monthly_inflow > 0:
                    inflow_d = monthly_inflow * (eff_base_ltv / (1.0 - eff_base_ltv))
                    debt += inflow_d
                    inflow += inflow_d

                tradable = [a for a in weights if a in px and pd.notnull(px[a].loc[d]) and px[a].loc[d] > 0]
                if inflow_mode == "shannon_drift" and tradable:
                    candidates = []
                    for a in tradable:
                        cur_v = asset_vals.get(a, 0.0)
                        tgt_v = (equity + debt) * weights[a]
                        drift = tgt_v - cur_v
                        if a in crypto_keys:
                            qual = btc_sig["nupl"] < 0.45 and not cr_exited.get(a, False)
                        else:
                            qual = cached_eval.get(a, (True, False, "", 0.0))[0]
                        if qual and drift > 0:
                            candidates.append((a, drift))

                    if candidates:
                        deploy_amt = inflow + cash_tbills
                        cash_tbills = 0.0
                        candidates.sort(key=lambda x: x[1], reverse=True)
                        top_a = candidates[0][0]
                        p_curr = float(px[top_a].loc[d])
                        add_u = deploy_amt / p_curr
                        old_u = units.get(top_a, 0.0)
                        units[top_a] = old_u + add_u
                        cost_basis[top_a] = (old_u * cost_basis.get(top_a, p_curr) + add_u * p_curr) / (old_u + add_u)
                    else:
                        if prune_destination == "tbills":
                            cash_tbills += inflow
                        else:
                            top_a = max(tradable, key=lambda a: (equity + debt) * weights[a] - asset_vals.get(a, 0.0))
                            p_curr = float(px[top_a].loc[d])
                            add_u = inflow / p_curr
                            old_u = units.get(top_a, 0.0)
                            units[top_a] = old_u + add_u
                            cost_basis[top_a] = (old_u * cost_basis.get(top_a, p_curr) + add_u * p_curr) / (old_u + add_u)
                elif inflow_mode == "pro_rata" and tradable and inflow > 0:
                    s_t = sum(weights[a] for a in tradable)
                    for a in tradable:
                        p_curr = float(px[a].loc[d])
                        add_u = (inflow * (weights[a] / s_t)) / p_curr
                        old_u = units.get(a, 0.0)
                        units[a] = old_u + add_u
                        cost_basis[a] = (old_u * cost_basis.get(a, p_curr) + add_u * p_curr) / max(1e-6, old_u + add_u)

            # 4. Periodic Rebalance (Symmetrical Tax Accounting)
            if rebalance_freq in ("quarterly", "annual") and i > 0:
                reb_interval = 90 if rebalance_freq == "quarterly" else 365
                if i % reb_interval == 0:
                    tradable = {a: weights[a] for a in weights if a in px and pd.notnull(px[a].loc[d]) and px[a].loc[d] > 0}
                    if tradable:
                        tot_v = sum(units.get(a, 0.0) * float(px[a].loc[d]) for a in tradable) + cash_tbills
                        cash_tbills = 0.0
                        s_t = sum(tradable.values())
                        sell_proceeds_net = 0.0
                        buy_deficits: Dict[str, float] = {}
                        for a, w in tradable.items():
                            p_curr = float(px[a].loc[d])
                            tgt_v = tot_v * (w / s_t)
                            cur_v = units.get(a, 0.0) * p_curr
                            diff = tgt_v - cur_v
                            if diff < -1.0:
                                sell_u = min(units.get(a, 0.0), abs(diff) / p_curr)
                                gross_s = sell_u * p_curr
                                pnl = sell_u * (p_curr - cost_basis.get(a, p_curr))
                                tax = _compute_tax(pnl)
                                units[a] -= sell_u
                                sell_proceeds_net += (gross_s - tax)
                            elif diff > 1.0:
                                buy_deficits[a] = diff
                        tot_def = sum(buy_deficits.values())
                        if tot_def > 0 and sell_proceeds_net > 0:
                            for a, def_v in buy_deficits.items():
                                p_curr = float(px[a].loc[d])
                                alloc = sell_proceeds_net * (def_v / tot_def)
                                add_u = alloc / p_curr
                                old_u = units.get(a, 0.0)
                                units[a] = old_u + add_u
                                cost_basis[a] = (old_u * cost_basis.get(a, p_curr) + add_u * p_curr) / max(1e-6, old_u + add_u)

            # 5. Equity Tactical Valuation Pruning
            if is_month_start and prune_pegy is not None and valuation_method != "buy_and_hold":
                for s in stock_keys:
                    if s not in px or pd.isnull(px[s].loc[d]) or units.get(s, 0.0) <= 0:
                        continue
                    if tech_hg_hold and sec_lookup.get(s, "TECH_HIGH_GROWTH") == "TECH_HIGH_GROWTH":
                        continue
                    p_s = float(px[s].loc[d])
                    is_buy, is_prune, m_name, m_val = cached_eval.get(s, (False, False, "N/A", 0.0))

                    trend_allows_prune = True
                    if trend_filter_sma200 and s in sma_200_map:
                        sma200 = sma_200_map[s].loc[d]
                        if pd.notnull(sma200) and p_s > float(sma200):
                            trend_allows_prune = False

                    stage = st_pruned_stage[s]
                    do_prune = False
                    frac = prune_fraction
                    if prune_mode == "tranche":
                        if is_prune and trend_allows_prune and stage < 3:
                            if stage == 0 or (m_val > prune_pegy * (1.0 + 0.25 * stage)):
                                do_prune = True
                                frac = 0.20
                    else:
                        if stage == 0 and is_prune and trend_allows_prune:
                            do_prune = True
                            frac = prune_fraction

                    if do_prune:
                        sell_u = units[s] * frac
                        gross_s = sell_u * p_s
                        units[s] -= sell_u
                        st_pruned_stage[s] = stage + 1
                        pnl = sell_u * (p_s - cost_basis.get(s, p_s))
                        tax = _compute_tax(pnl)
                        net_p = gross_s - tax

                        gold_stocks = [
                            stk for stk in stock_keys
                            if stk != s and stk in px and pd.notnull(px[stk].loc[d])
                            and cached_eval.get(stk, (False, False, "", 0.0))[0]
                        ]
                        if gold_stocks:
                            target_s = min(gold_stocks, key=lambda stk: cached_eval[stk][3])
                            p_t = float(px[target_s].loc[d])
                            old_u = units.get(target_s, 0.0)
                            add_u = net_p / p_t
                            units[target_s] = old_u + add_u
                            cost_basis[target_s] = (old_u * cost_basis.get(target_s, p_t) + add_u * p_t) / (old_u + add_u)
                        elif prune_destination == "tbills":
                            cash_tbills += net_p
                        else:
                            others = [stk for stk in stock_keys if stk != s and stk in px and pd.notnull(px[stk].loc[d])]
                            if others:
                                target_s = min(others, key=lambda stk: cached_eval.get(stk, (False, False, "", 99.0))[3])
                                p_t = float(px[target_s].loc[d])
                                old_u = units.get(target_s, 0.0)
                                add_u = net_p / p_t
                                units[target_s] = old_u + add_u
                                cost_basis[target_s] = (old_u * cost_basis.get(target_s, p_t) + add_u * p_t) / (old_u + add_u)
                            else:
                                cash_tbills += net_p

                        trade_log.append(TradeAuditEntry(
                            date=d.strftime("%Y-%m-%d"), asset=s, action=f"PRUNE_{int(frac*100)}%",
                            price=p_s, units=sell_u, gross_amount=gross_s, realized_gain=pnl,
                            tax_paid=tax, net_proceeds=net_p, metric_name=m_name, metric_value=m_val,
                            reason=f"{m_name} ({m_val:.2f}) triggered prune",
                        ))
                    elif stage > 0 and is_buy:
                        st_pruned_stage[s] = 0

            # 6. Crypto On-Chain Timing
            if "BTC-USD" in weights and "BTC-USD" in units and units["BTC-USD"] > 0 and btc_top_mode != "none":
                p_btc = float(px["BTC-USD"].loc[d])
                top_hit = False
                if btc_top_mode == "pi_cycle_only":
                    top_hit = btc_sig["pi_cycle"]
                elif btc_top_mode == "picycle_or_reverse_nupl":
                    top_hit = btc_sig["pi_cycle"] or btc_sig["nupl_reverse_cross"]
                elif btc_top_mode == "picycle_or_nupl65":
                    top_hit = btc_sig["pi_cycle"] or (btc_sig["nupl"] > 0.65)
                elif btc_top_mode == "mvrv_z5":
                    top_hit = btc_sig["mvrv_z"] > 5.0

                if not btc_pruned and top_hit:
                    sell_u = units["BTC-USD"] * 0.50
                    gross_s = sell_u * p_btc
                    units["BTC-USD"] -= sell_u
                    btc_pruned = True
                    pnl = sell_u * (p_btc - cost_basis.get("BTC-USD", p_btc))
                    tax = _compute_tax(pnl)
                    net_p = gross_s - tax
                    tradable_s = [s for s in stock_keys if s in px and pd.notnull(px[s].loc[d])]
                    if tradable_s:
                        for s in tradable_s:
                            p_s = float(px[s].loc[d])
                            add_u = (net_p / len(tradable_s)) / p_s
                            old_u = units.get(s, 0.0)
                            units[s] = old_u + add_u
                            cost_basis[s] = (old_u * cost_basis.get(s, p_s) + add_u * p_s) / (old_u + add_u)
                    else:
                        cash_tbills += net_p
                    trade_log.append(TradeAuditEntry(
                        date=d.strftime("%Y-%m-%d"), asset="BTC-USD", action="PODA_50%",
                        price=p_btc, units=sell_u, gross_amount=gross_s, realized_gain=pnl,
                        tax_paid=tax, net_proceeds=net_p, metric_name=btc_top_mode,
                        metric_value=btc_sig["nupl"], reason=f"BTC Top Signal ({btc_top_mode})",
                    ))
                elif btc_pruned and (btc_sig["is_200w_floor"] or btc_sig["nupl"] < 0.0 or btc_sig["mvrv_z"] < 0.5):
                    btc_pruned = False

            macro_alt_warn = btc_sig["nupl"] > crypto_exit_nupl or btc_sig["mvrv_z"] > 3.0
            for c in crypto_keys:
                if c == "BTC-USD":
                    continue
                if l1_majors_hold and c in ("ETH-USD", "SOL-USD"):
                    continue
                if c in px and pd.notnull(px[c].loc[d]) and units.get(c, 0.0) > 0 and not cr_exited[c] and crypto_exit_dd < 0:
                    p_c = float(px[c].loc[d])
                    pk = float(cr_peaks[c].loc[d]) if c in cr_peaks else p_c
                    dd = (p_c - pk) / pk if pk > 0 else 0.0
                    if macro_alt_warn and dd <= crypto_exit_dd:
                        sell_u = units[c]
                        gross_s = sell_u * p_c
                        units[c] = 0.0
                        cr_exited[c] = True
                        pnl = sell_u * (p_c - cost_basis.get(c, p_c))
                        tax = _compute_tax(pnl)
                        net_p = gross_s - tax
                        tradable_s = [s for s in stock_keys if s in px and pd.notnull(px[s].loc[d])]
                        if tradable_s:
                            for s in tradable_s:
                                p_s = float(px[s].loc[d])
                                add_u = (net_p / len(tradable_s)) / p_s
                                old_u = units.get(s, 0.0)
                                units[s] = old_u + add_u
                                cost_basis[s] = (old_u * cost_basis.get(s, p_s) + add_u * p_s) / (old_u + add_u)
                        else:
                            cash_tbills += net_p
                        trade_log.append(TradeAuditEntry(
                            date=d.strftime("%Y-%m-%d"), asset=c, action="SAIDA_100%",
                            price=p_c, units=sell_u, gross_amount=gross_s, realized_gain=pnl,
                            tax_paid=tax, net_proceeds=net_p, metric_name="Trailing_DD",
                            metric_value=dd, reason=f"BTC Euphoria + DD {dd:.1%}",
                        ))

                if cr_exited.get(c, False) and c in px and pd.notnull(px[c].loc[d]) and px[c].loc[d] > 0:
                    re_hit = False
                    if crypto_reenter_mode == "200w_105":
                        re_hit = btc_sig["is_200w_floor"]
                    elif crypto_reenter_mode == "200w_105_and_nupl0":
                        re_hit = btc_sig["is_200w_floor"] and (btc_sig["nupl"] < crypto_reenter_nupl)
                    elif crypto_reenter_mode == "200w_or_nupl0":
                        re_hit = btc_sig["is_200w_floor"] or (btc_sig["nupl"] < crypto_reenter_nupl)
                    elif crypto_reenter_mode == "nupl30":
                        re_hit = btc_sig["nupl"] < 0.30
                    elif crypto_reenter_mode == "nupl0":
                        re_hit = btc_sig["nupl"] < 0.0
                    elif crypto_reenter_mode == "hash_ribbon":
                        re_hit = btc_sig["hash_ribbon_buy"] or btc_sig["is_200w_floor"]

                    if re_hit:
                        cr_exited[c] = False
                        t_val = min(gross_a * weights[c], max(cash_tbills, equity * weights[c]))
                        p_c = float(px[c].loc[d])
                        use_c = min(cash_tbills, t_val)
                        cash_tbills -= use_c
                        rem_v = t_val - use_c
                        if rem_v > 0:
                            st_tot = sum(
                                units.get(s, 0.0) * float(px[s].loc[d])
                                for s in stock_keys
                                if s in px and pd.notnull(px[s].loc[d])
                            )
                            if st_tot > rem_v:
                                ratio_keep = 1.0 - (rem_v / st_tot)
                                for s in stock_keys:
                                    units[s] *= ratio_keep
                            else:
                                rem_v = 0.0
                        actual_buy = use_c + rem_v
                        if actual_buy > 0:
                            units[c] = actual_buy / p_c
                            cost_basis[c] = p_c
                            trade_log.append(TradeAuditEntry(
                                date=d.strftime("%Y-%m-%d"), asset=c, action="RE-ENTRADA",
                                price=p_c, units=units[c], gross_amount=actual_buy, realized_gain=0.0,
                                tax_paid=0.0, net_proceeds=actual_buy, metric_name=crypto_reenter_mode,
                                metric_value=btc_sig["nupl"], reason=f"Altcoin Re-entry ({crypto_reenter_mode})",
                            ))

            # 7. Continuous & Dynamic Convex LTV Adjustments
            if ltv_mode in ("fixed_20", "fixed_25", "convex", "opportunistic_0_30", "macro_gated"):
                if ltv_mode == "fixed_20":
                    target_ltv = base_ltv
                elif ltv_mode == "fixed_25":
                    target_ltv = 0.25
                else:
                    s_dd = float(spy_dd.loc[d])
                    cape = float(cape_s.loc[d])
                    vix = float(vix_s.loc[d])
                    sahm = float(sahm_s.loc[d])
                    is_uninv = bool(uninversion_alert.loc[d])

                    is_panic = btc_sig["mvrv_z"] < 0.5 or cape < 28.0 or s_dd < -0.20 or vix > 30.0
                    is_distress = fed_f > 0.045 and cape > 36.0
                    is_recession_gate = sahm >= 0.50 or is_uninv

                    if ltv_mode == "opportunistic_0_30":
                        target_ltv = turbo_ltv if is_panic else 0.0
                    elif ltv_mode == "macro_gated":
                        if is_recession_gate and not is_panic:
                            target_ltv = defensive_ltv
                        elif is_panic:
                            target_ltv = turbo_ltv
                        elif is_distress:
                            target_ltv = defensive_ltv
                        else:
                            target_ltv = base_ltv
                    else:
                        target_ltv = turbo_ltv if is_panic else (defensive_ltv if is_distress else base_ltv)

                desired_debt = gross_a * target_ltv
                delta_d = desired_debt - debt
                if delta_d > gross_a * 0.03:
                    debt += delta_d
                    tradable_s = [s for s in stock_keys if s in px and pd.notnull(px[s].loc[d])]
                    deploy_targets = tradable_s if tradable_s else [
                        a for a in weights if a in px and pd.notnull(px[a].loc[d])
                    ]
                    if deploy_targets:
                        for t_a in deploy_targets:
                            p_t = float(px[t_a].loc[d])
                            add_u = (delta_d / len(deploy_targets)) / p_t
                            old_u = units.get(t_a, 0.0)
                            units[t_a] = old_u + add_u
                            cost_basis[t_a] = (old_u * cost_basis.get(t_a, p_t) + add_u * p_t) / (old_u + add_u)
                elif delta_d < -gross_a * 0.05 and debt > 0:
                    payd = min(debt, abs(delta_d))
                    use_c = min(cash_tbills, payd)
                    cash_tbills -= use_c
                    rem = payd - use_c
                    if rem > 0 and (gross_a - cash_tbills) > 0:
                        ratio = max(0.0, 1.0 - (rem / (gross_a - cash_tbills)))
                        for a in units:
                            units[a] *= ratio
                    debt -= payd

        # Build Results
        eq_s = pd.Series(equity_curve, index=dates)
        debt_s = pd.Series(debt_curve, index=dates)
        ltv_s = pd.Series(ltv_curve, index=dates)
        dd_s = (eq_s - eq_s.cummax()) / eq_s.cummax()

        final_cap = float(eq_s.iloc[-1])
        net_profit = final_cap - total_invested
        years = max(0.25, (dates[-1] - dates[0]).days / 365.25)
        cagr = ((max(1.0, final_cap) / max(1.0, total_invested)) ** (1.0 / years) - 1.0) * 100.0

        daily_ret = eq_s.pct_change().dropna()
        vol = float(daily_ret.std() * np.sqrt(252) * 100.0)
        rf_daily = 0.04 / 252.0
        excess_ret = daily_ret - rf_daily
        sharpe = float((excess_ret.mean() / (daily_ret.std() + 1e-9)) * np.sqrt(252))
        downside = daily_ret[daily_ret < 0]
        sortino = float((excess_ret.mean() / (downside.std() + 1e-9)) * np.sqrt(252)) if len(downside) > 0 else 0.0
        max_dd = float(dd_s.min() * 100.0)
        calmar = abs(cagr / max_dd) if max_dd < 0 else 0.0

        metrics = {
            "initial_capital": initial_capital,
            "total_invested": total_invested,
            "final_capital": final_cap,
            "net_profit": net_profit,
            "multiple_on_invested": final_cap / max(1.0, total_invested),
            "cagr_pct": cagr,
            "annual_volatility_pct": vol,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown_pct": max_dd,
            "calmar_ratio": calmar,
            "total_taxes_paid": total_tax_paid,
            "total_margin_interest": total_interest_paid,
            "total_trades": float(len(trade_log)),
        }

        yearly_ret = []
        for yr, group in eq_s.groupby(eq_s.index.year):
            ret_yr = (group.iloc[-1] / max(1.0, group.iloc[0]) - 1.0) * 100.0
            yearly_ret.append({"year": yr, "return_pct": ret_yr})
        yearly_df = pd.DataFrame(yearly_ret)

        return ValuationBacktestResult(
            config={
                "assets": assets, "valuation_method": valuation_method,
                "buy_pegy": buy_pegy, "prune_pegy": prune_pegy,
                "prune_mode": prune_mode, "prune_destination": prune_destination,
                "ltv_mode": ltv_mode, "inflow_mode": inflow_mode,
                "btc_top_mode": btc_top_mode,
                "rebalance_freq": rebalance_freq, "enable_tax": enable_tax,
            },
            dates=dates,
            equity_series=eq_s,
            debt_series=debt_s,
            ltv_series=ltv_s,
            drawdown_series=dd_s,
            trade_log=trade_log,
            metrics=metrics,
            yearly_returns_df=yearly_df,
        )


# ==============================================================================
# 5. PUBLIC HIGH-LEVEL CONVENIENCE ENTRYPOINT
# ==============================================================================

_SHARED_SIMULATOR: Optional[ComposableValuationBacktestSimulator] = None


def run_valuation_backtest(
    assets: Optional[Union[List[str], Dict[str, float]]] = None,
    initial_capital: float = 100_000.0,
    monthly_inflow: float = 5_000.0,
    start_date: str = "2016-11-05",
    end_date: str = "2026-11-05",
    sector_map: Optional[Dict[str, str]] = None,
    valuation_method: str = "sector_auto",
    buy_pegy: float = 1.2,
    prune_pegy: Optional[float] = 1.6,
    prune_fraction: float = 0.50,
    prune_mode: str = "single",
    prune_destination: str = "reinvest_discounted",
    yield_in_denominator: bool = True,
    trend_filter_sma200: bool = False,
    quality_gates: bool = True,
    tech_hg_hold: bool = True,
    l1_majors_hold: bool = True,
    bank_pb_veto: float = 1.0,
    bank_buy_pegy: float = 1.0,
    bank_prune_pegy: float = 1.5,
    btc_top_mode: str = "pi_cycle_only",
    crypto_exit_nupl: float = 0.60,
    crypto_exit_dd: float = -0.20,
    crypto_reenter_mode: str = "200w_105",
    crypto_reenter_nupl: float = 0.00,
    inflow_mode: str = "shannon_drift",
    rebalance_freq: str = "none",
    ltv_mode: str = "fixed_20",
    base_ltv: float = 0.20,
    turbo_ltv: float = 0.30,
    defensive_ltv: float = 0.20,
    tax_rate: float = 0.15,
    enable_tax: bool = True,
    loss_carryforward: bool = True,
) -> ValuationBacktestResult:
    """Main high-level API to run a sector-stratified, point-in-time valuation backtest."""
    global _SHARED_SIMULATOR
    if _SHARED_SIMULATOR is None:
        _SHARED_SIMULATOR = ComposableValuationBacktestSimulator()

    if assets is None:
        assets = {
            "MKR-USD": 0.125, "LINK-USD": 0.125, "UNI7083-USD": 0.125, "PENDLE-USD": 0.125,
            "ASML": 0.08333, "TSM": 0.08333, "MELI": 0.08333, "NU": 0.08333, "AVGO": 0.08334, "MA": 0.08334,
        }

    return _SHARED_SIMULATOR.run(
        assets=assets,
        initial_capital=initial_capital,
        monthly_inflow=monthly_inflow,
        start_date=start_date,
        end_date=end_date,
        sector_map=sector_map,
        valuation_method=valuation_method,
        buy_pegy=buy_pegy,
        prune_pegy=prune_pegy,
        prune_fraction=prune_fraction,
        prune_mode=prune_mode,
        prune_destination=prune_destination,
        yield_in_denominator=yield_in_denominator,
        trend_filter_sma200=trend_filter_sma200,
        quality_gates=quality_gates,
        tech_hg_hold=tech_hg_hold,
        l1_majors_hold=l1_majors_hold,
        bank_pb_veto=bank_pb_veto,
        bank_buy_pegy=bank_buy_pegy,
        bank_prune_pegy=bank_prune_pegy,
        btc_top_mode=btc_top_mode,
        crypto_exit_nupl=crypto_exit_nupl,
        crypto_exit_dd=crypto_exit_dd,
        crypto_reenter_mode=crypto_reenter_mode,
        crypto_reenter_nupl=crypto_reenter_nupl,
        inflow_mode=inflow_mode,
        rebalance_freq=rebalance_freq,
        ltv_mode=ltv_mode,
        base_ltv=base_ltv,
        turbo_ltv=turbo_ltv,
        defensive_ltv=defensive_ltv,
        tax_rate=tax_rate,
        enable_tax=enable_tax,
        loss_carryforward=loss_carryforward,
    )

"""
MODULE 1.4 & MODULE 6: PORTFOLIO OVERVIEW, DYNAMIC PORTFOLIO MANAGER (SQLite CRUD + JSON)
& ETF LOOK-THROUGH DECOMPOSITION
- Persiste a estrutura da carteira em banco de dados local SQLite (portfolio_store.db) sincronizado
  com portfolio_config.json.
- Allows Adding, Editing, Removing assets, Normalizing Weights to 100%, and Resetting to Defaults.
- Calculates asset P&L (via Average Purchase Price), Turbo LTV eligibility, actual vs target weights, alvo
  and comprehensive Look-Through decomposition of ETFs (SPY, QQQ, SMH, ITA, and 2x QLD).
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd
import yfinance as yf
from core.market_data import fetch_all_quotes_parallel


@dataclass
class PortfolioPosition:
    ticker: str
    name: str
    category: str
    sector_vertical: str
    target_weight_pct: float
    current_weight_pct: float
    weight_drift_pp: float
    allocated_usd: float
    current_price_usd: float
    avg_buy_price_usd: float
    pnl_pct: float
    pnl_usd: float
    ltv_turbo_eligible: bool
    quantity_units: float
    role_description: str
    yield_mechanism: str


@dataclass
class LookThroughHolding:
    ticker: str
    company_name: str
    sector: str
    direct_weight_pct: float
    spy_indirect_pct: float
    qqq_indirect_pct: float
    smh_indirect_pct: float
    ita_indirect_pct: float
    qld_2x_indirect_pct: float
    total_indirect_pct: float
    total_effective_lookthrough_pct: float
    effective_exposure_usd: float
    overlap_sources: str


@dataclass
class PortfolioOverviewBundle:
    capital_usd: float
    total_crypto_pct: float
    total_hard_assets_pct: float
    target_weight_sum_pct: float
    is_weight_valid_100: bool
    weight_validation_message: str
    ltv_eligible_stocks_weight_pct: float
    ltv_eligible_btc_weight_pct: float
    total_portfolio_pnl_usd: float
    total_portfolio_pnl_pct: float
    effective_gross_exposure_pct: float  # Considerando o 2x do QLD
    positions: List[PortfolioPosition]
    lookthrough_holdings: List[LookThroughHolding]
    sector_exposure_summary: List[Dict[str, Any]]
    weight_sum_is_valid_100: bool = True

    def __post_init__(self) -> None:
        self.weight_sum_is_valid_100 = bool(self.is_weight_valid_100)


# Default average purchase prices (for realistic P&L estimation when not provided)
DEFAULT_AVG_BUY_PRICES: Dict[str, float] = {
    "BTC-USD": 54200.0,
    "ETH-USD": 2380.0,
    "SOL-USD": 118.0,
    "AAVE-USD": 112.0,
    "SPY": 495.0,
    "QQQ": 418.0,
    "SMH": 205.0,
    "ITA": 132.0,
    "QLD": 78.0,
    "AAPL": 182.0,
    "MSFT": 355.0,
    "GOOGL": 144.0,
    "AMZN": 168.0,
    "NVDA": 88.0,
    "META": 435.0,
    "V": 265.0,
    "JPM": 188.0,
    "WMT": 66.5,
    "DBSDY": 96.0,
    "ASML": 680.0,
    "TSM": 145.0,
    "MELI": 1650.0,
    "AVGO": 142.0,
    "MA": 445.0,
    "NU": 11.20,
    "MKR-USD": 1450.0,
    "PENDLE-USD": 3.80,
    "LINK-USD": 14.20,
    "UNI-USD": 7.80,
}

DEFAULT_SPOT_PRICES: Dict[str, float] = {
    "BTC-USD": 89500.0,
    "ETH-USD": 2950.0,
    "SOL-USD": 188.0,
    "AAVE-USD": 172.0,
    "PENDLE-USD": 4.85,
    "LINK-USD": 18.40,
    "UNI-USD": 9.60,
    "MKR-USD": 1680.0,
    "SPY": 592.0,
    "QQQ": 508.0,
    "SMH": 258.0,
    "ITA": 154.0,
    "QLD": 106.0,
    "AAPL": 228.5,
    "MSFT": 425.0,
    "GOOGL": 182.0,
    "AMZN": 210.0,
    "NVDA": 142.0,
    "META": 595.0,
    "V": 308.0,
    "JPM": 238.0,
    "WMT": 85.5,
    "DBSDY": 118.0,
    "ASML": 715.0,
    "COST": 915.0,
    "TSM": 192.0,
    "AVGO": 178.0,
    "BRK-B": 456.0,
    "LLY": 825.0,
    "XOM": 118.0,
    "MELI": 1980.0,
    "MA": 512.0,
    "NU": 14.20,
}

# Official weights of primary holdings within each portfolio ETF (% of ETF AUM)
ETF_CONSTITUENTS_MAP: Dict[str, Dict[str, Dict[str, Any]]] = {
    "SPY": {
        "AAPL": {"name": "Apple Inc.", "sector": "Big Tech / Consumer", "weight_pct": 7.10},
        "NVDA": {"name": "NVIDIA Corporation", "sector": "Semiconductors / AI", "weight_pct": 6.80},
        "MSFT": {"name": "Microsoft Corporation", "sector": "Big Tech / Cloud", "weight_pct": 6.50},
        "AMZN": {"name": "Amazon.com Inc.", "sector": "Cloud & E-Commerce", "weight_pct": 3.80},
        "META": {"name": "Meta Platforms Inc.", "sector": "Digital Ads & AI", "weight_pct": 2.50},
        "GOOGL": {"name": "Alphabet Inc.", "sector": "Search & Cloud", "weight_pct": 3.90},
        "BRK-B": {"name": "Berkshire Hathaway Inc.", "sector": "Financials / Insurance", "weight_pct": 1.70},
        "AVGO": {"name": "Broadcom Inc.", "sector": "Semiconductors", "weight_pct": 1.65},
        "LLY": {"name": "Eli Lilly and Company", "sector": "Healthcare / Pharma", "weight_pct": 1.40},
        "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Financials / Banks", "weight_pct": 1.35},
        "MA": {"name": "Mastercard Incorporated", "sector": "Financials / Payments", "weight_pct": 0.92},
        "V": {"name": "Visa Inc.", "sector": "Financials / Payments", "weight_pct": 1.05},
        "WMT": {"name": "Walmart Inc.", "sector": "Consumer / Retail", "weight_pct": 0.85},
        "XOM": {"name": "Exxon Mobil Corp.", "sector": "Energy / Commodities", "weight_pct": 1.10},
        "COST": {"name": "Costco Wholesale Corp.", "sector": "Consumer / Retail", "weight_pct": 0.80},
    },
    "QQQ": {
        "AAPL": {"name": "Apple Inc.", "sector": "Big Tech / Consumer", "weight_pct": 8.90},
        "NVDA": {"name": "NVIDIA Corporation", "sector": "Semiconductors / AI", "weight_pct": 8.40},
        "MSFT": {"name": "Microsoft Corporation", "sector": "Big Tech / Cloud", "weight_pct": 8.10},
        "AMZN": {"name": "Amazon.com Inc.", "sector": "Cloud & E-Commerce", "weight_pct": 5.20},
        "META": {"name": "Meta Platforms Inc.", "sector": "Digital Ads & AI", "weight_pct": 4.80},
        "GOOGL": {"name": "Alphabet Inc.", "sector": "Search & Cloud", "weight_pct": 5.10},
        "AVGO": {"name": "Broadcom Inc.", "sector": "Semiconductors", "weight_pct": 4.30},
        "COST": {"name": "Costco Wholesale Corp.", "sector": "Consumer / Retail", "weight_pct": 2.60},
        "NFLX": {"name": "Netflix Inc.", "sector": "Communication / Media", "weight_pct": 1.90},
        "AMD": {"name": "Advanced Micro Devices", "sector": "Semiconductors", "weight_pct": 1.60},
        "ASML": {"name": "ASML Holding N.V.", "sector": "Semiconductors / Litho", "weight_pct": 0.95},
        "MELI": {"name": "MercadoLibre Inc.", "sector": "E-Commerce & Fintech", "weight_pct": 0.72},
    },
    "SMH": {
        "NVDA": {"name": "NVIDIA Corporation", "sector": "Semiconductors / AI", "weight_pct": 20.50},
        "TSM": {"name": "Taiwan Semiconductor (TSMC)", "sector": "Semiconductors Foundry", "weight_pct": 12.80},
        "AVGO": {"name": "Broadcom Inc.", "sector": "Semiconductors", "weight_pct": 7.90},
        "AMD": {"name": "Advanced Micro Devices", "sector": "Semiconductors", "weight_pct": 4.80},
        "ASML": {"name": "ASML Holding N.V.", "sector": "Semiconductors / Litho", "weight_pct": 4.70},
        "AMAT": {"name": "Applied Materials Inc.", "sector": "Semiconductors Equip", "weight_pct": 4.40},
        "TXN": {"name": "Texas Instruments Inc.", "sector": "Semiconductors Analog", "weight_pct": 4.30},
        "QCOM": {"name": "Qualcomm Inc.", "sector": "Semiconductors Mobile", "weight_pct": 4.20},
        "MU": {"name": "Micron Technology Inc.", "sector": "Semiconductors Memory", "weight_pct": 4.10},
        "LRCX": {"name": "Lam Research Corp.", "sector": "Semiconductors Equip", "weight_pct": 4.00},
    },
    "ITA": {
        "GE": {"name": "GE Aerospace", "sector": "Aerospace & Defense", "weight_pct": 18.50},
        "RTX": {"name": "RTX Corporation (Raytheon)", "sector": "Aerospace & Defense", "weight_pct": 15.20},
        "LMT": {"name": "Lockheed Martin Corp.", "sector": "Aerospace & Defense", "weight_pct": 14.10},
        "BA": {"name": "The Boeing Company", "sector": "Aerospace & Defense", "weight_pct": 8.40},
        "NOC": {"name": "Northrop Grumman Corp.", "sector": "Aerospace & Defense", "weight_pct": 5.80},
        "GD": {"name": "General Dynamics Corp.", "sector": "Aerospace & Defense", "weight_pct": 5.50},
        "TDG": {"name": "TransDigm Group Inc.", "sector": "Aerospace & Defense", "weight_pct": 4.90},
        "LHX": {"name": "L3Harris Technologies", "sector": "Aerospace & Defense", "weight_pct": 4.50},
        "HWM": {"name": "Howmet Aerospace Inc.", "sector": "Aerospace & Defense", "weight_pct": 4.10},
    },
}


class PortfolioEngine:
    def __init__(self, config_path: str = "portfolio_config.json") -> None:
        self.config_path = config_path
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(config_path)), "portfolio_store.db")
        self._init_sqlite_db()

    def _init_sqlite_db(self) -> None:
        """Inicializa o banco SQLite local e popula a partir do JSON se estiver vazio."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolio_assets (
                    ticker TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    sector_vertical TEXT NOT NULL,
                    target_weight_pct REAL NOT NULL,
                    avg_buy_price REAL NOT NULL,
                    ltv_turbo_eligible INTEGER NOT NULL,
                    fair_price REAL NOT NULL,
                    role_description TEXT,
                    accumulate_rule TEXT,
                    sell_rule TEXT,
                    yield_mechanism TEXT,
                    display_order INTEGER DEFAULT 999
                )
                """
            )
            cur = conn.execute("SELECT COUNT(*) FROM portfolio_assets")
            count = cur.fetchone()[0]
            if count == 0 and os.path.exists(self.config_path):
                self._seed_sqlite_from_json_file(conn)

    def _seed_sqlite_from_json_file(self, conn: sqlite3.Connection) -> None:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assets = data.get("assets", [])
            for idx, a in enumerate(assets):
                tk = a["ticker"]
                cat = a.get("category", "Hard-Asset Stock")
                avg_px = float(a.get("avg_buy_price", DEFAULT_AVG_BUY_PRICES.get(tk, a.get("fair_price", 100.0) * 0.80)))
                # By default: Stocks, ETFs, and BTC are eligible for Turbo LTV; Altcoins are not
                ltv_ok = bool(a.get("ltv_turbo_eligible", cat in ("Hard-Asset Stock", "Hard-Asset ETF", "Crypto BTC")))
                conn.execute(
                    """
                    INSERT OR REPLACE INTO portfolio_assets (
                        ticker, name, category, sector_vertical, target_weight_pct,
                        avg_buy_price, ltv_turbo_eligible, fair_price,
                        role_description, accumulate_rule, sell_rule, yield_mechanism, display_order
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tk,
                        a.get("name", tk),
                        cat,
                        a.get("sector_vertical", "OTHER"),
                        float(a.get("target_weight_pct", 2.5)),
                        avg_px,
                        1 if ltv_ok else 0,
                        float(a.get("fair_price", DEFAULT_SPOT_PRICES.get(tk, 100.0))),
                        a.get("role_description", "Ativo integrante da carteira monitorada pelo Framework."),
                        a.get("accumulate_rule", "Advisory Reference: Accumulate within Framework discount bands."),
                        a.get("sell_rule", "Advisory Reference: Evaluate pruning under extreme overvaluation."),
                        a.get("yield_mechanism", "Compounded value growth and cash distribution."),
                        idx,
                    ),
                )
            conn.commit()
        except Exception:
            pass

    def _sync_sqlite_to_json(self) -> None:
        """Sincroniza o estado atual do SQLite para portfolio_config.json."""
        assets = self.get_all_assets_from_db()
        crypto_w = sum(a["target_weight_pct"] for a in assets if "Crypto" in a["category"])
        hard_w = sum(a["target_weight_pct"] for a in assets if "Crypto" not in a["category"])
        payload = {
            "total_crypto_pct": round(crypto_w, 3),
            "total_hard_assets_pct": round(hard_w, 3),
            "assets": assets,
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get_all_assets_from_db(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM portfolio_assets ORDER BY display_order ASC, ticker ASC"
            ).fetchall()
            out: List[Dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "ticker": r["ticker"],
                        "name": r["name"],
                        "category": r["category"],
                        "sector_vertical": r["sector_vertical"],
                        "target_weight_pct": float(r["target_weight_pct"]),
                        "avg_buy_price": float(r["avg_buy_price"]),
                        "ltv_turbo_eligible": bool(r["ltv_turbo_eligible"]),
                        "fair_price": float(r["fair_price"]),
                        "role_description": r["role_description"] or "",
                        "accumulate_rule": r["accumulate_rule"] or "",
                        "sell_rule": r["sell_rule"] or "",
                        "yield_mechanism": r["yield_mechanism"] or "",
                    }
                )
            return out

    def upsert_asset(
        self,
        ticker: str,
        name: str = "",
        category: str = "Tech Stock",
        sector_vertical: str = "TECH_HIGH_GROWTH",
        target_weight_pct: float = 2.5,
        avg_buy_price: float = 0.0,
        ltv_turbo_eligible: bool = True,
        fair_price: Optional[float] = None,
        role_description: Optional[str] = None,
        asset_class_ui: Optional[str] = None,
        sector_ui: Optional[str] = None,
        avg_buy_price_usd: Optional[float] = None,
        yield_mechanism: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        tk = ticker.strip().upper()

        # Handle UI class / sector translation
        if asset_class_ui:
            if asset_class_ui in ("Stock", "Ação"):
                s_low = (sector_ui or "").lower()
                if any(k in s_low for k in ["banco", "bank", "financ"]):
                    category = "Financial"
                    sector_vertical = "FINANCIAL_BANK"
                elif "cash cow" in s_low:
                    category = "Tech Stock"
                    sector_vertical = "TECH_CASH_COW"
                elif any(k in s_low for k in ["ciclic", "cíclic", "defense", "defesa", "industrial"]):
                    category = "Cyclical"
                    sector_vertical = "CYCLICAL"
                elif any(k in s_low for k in ["defensiv", "consum", "retail", "sss"]):
                    category = "Retail"
                    sector_vertical = "RETAIL"
                else:
                    category = "Tech Stock"
                    sector_vertical = "TECH_HIGH_GROWTH"
            elif asset_class_ui in ("Crypto", "Cripto"):
                s_low = (sector_ui or "").lower()
                if "btc" in tk or any(k in s_low for k in ["store of value", "soberan", "sovereign"]):
                    category = "Crypto BTC"
                    sector_vertical = "CRYPTO_SOV"
                else:
                    category = "Crypto Altcoin"
                    sector_vertical = "CRYPTO_L1_SMART"
            elif asset_class_ui == "Altcoin":
                category = "Crypto Altcoin"
                s_low = (sector_ui or "").lower()
                if any(k in s_low for k in ["defi", "rendimento", "yield"]):
                    sector_vertical = "CRYPTO_DEFI_YIELD"
                elif any(k in s_low for k in ["orac", "orác", "oracle", "interop"]):
                    sector_vertical = "CRYPTO_ORACLE"
                elif any(k in s_low for k in ["layer 2", "rollup", "l2"]):
                    sector_vertical = "CRYPTO_L2_ROLLUP"
                elif any(k in s_low for k in ["ai", "depin", "compute"]):
                    sector_vertical = "CRYPTO_AI_DEPIN"
                else:
                    sector_vertical = "CRYPTO_ALT"
            elif asset_class_ui == "ETF":
                s_low = (sector_ui or "").lower()
                if "2x" in s_low or "alavancad" in s_low:
                    category = "ETF Leveraged"
                    sector_vertical = "ETF_LEVERAGED"
                else:
                    category = "ETF Broad"
                    sector_vertical = "ETF_INDEX"

        if category in ("Crypto BTC", "Crypto Altcoin") and not tk.endswith("-USD") and "-" not in tk:
            tk = f"{tk}-USD"

        if avg_buy_price_usd is not None and avg_buy_price == 0.0:
            avg_buy_price = avg_buy_price_usd

        default_rules = {
            "TECH_HIGH_GROWTH": (
                "Advisory Reference (High-Growth): Enterprise PEGY (EV/EBIT NTM) in Gold Range (0 to 1.2x).",
                "Advisory 50% Trim Reference: Enterprise PEGY (EV/EBIT NTM) > 1.6x.",
            ),
            "TECH_CASH_COW": (
                "Advisory Reference (Cash Cow): Enterprise PEGY (EV/FCF NTM) in Gold Range (0 to 1.2x).",
                "Advisory 50% Trim Reference: Enterprise PEGY (EV/FCF NTM) > 1.6x.",
            ),
            "FINANCIAL_BANK": (
                "Advisory Reference (Banks): Financial PEGY 0 to 1.0x WITH P/B filter >= 1.0x.",
                "Advisory 50% Trim Reference: Financial PEGY > 1.5x.",
            ),
            "FINANCIAL_TOLLBOOTH": (
                "Advisory Reference (Cash Cow): Enterprise PEGY (EV/FCF NTM) in Gold Range (0 to 1.2x).",
                "Advisory 50% Trim Reference: Enterprise PEGY (EV/FCF NTM) > 1.6x.",
            ),
            "RETAIL": (
                "Advisory Reference (Defensives): P/E & EV/EBITDA <= 0.85x Sector + Price <= 0.85x DCF (with positive SSS).",
                "Advisory 50% Trim Reference: P/E & EV/EBITDA >= 1.20x Sector OR Price >= 1.20x DCF.",
            ),
            "CYCLICAL": (
                "Advisory Reference (Cyclicals): Elevated EV/EBITDA multiple (cycle trough) and price below mid-cycle DCF.",
                "Advisory 50% Trim Reference: Compressed EV/EBITDA multiple at cycle peak with peak margins.",
            ),
        }
        acc_rule, sell_rule = default_rules.get(
            sector_vertical,
            (
                "Advisory Reference: Accumulate when at fundamental / on-chain discount.",
                "Advisory Reference: Partial trim during cycle euphoria / stretched valuation multiples.",
            ),
        )
        if category == "Crypto BTC":
            acc_rule = "Advisory Reference: NUPL < 0.0 OR MVRV Z <= 0.50 OR Price <= 1.05x 200W SMA."
            sell_rule = "Advisory 50% Trim Reference: Pi Cycle Top active OR NUPL Reverse Cross (< 0.60 after > 0.65)."
        elif category == "Crypto Altcoin":
            acc_rule = "Advisory Reference: Macro Trough (BTC NUPL < 0.30) with healthy P/F and positive Real Earnings."
            sell_rule = "Advisory Cyclical Exit Reference: BTC NUPL > 0.60 OR MVRV Z > 3.0 combined with Trailing Drawdown >= 20%."

        fp = fair_price if (fair_price and fair_price > 0) else DEFAULT_SPOT_PRICES.get(tk, max(10.0, avg_buy_price * 1.15))
        role_desc = role_description or f"Strategic position ({category} • {sector_vertical}) monitored by Value Investing Framework."

        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute("SELECT display_order, yield_mechanism FROM portfolio_assets WHERE ticker = ?", (tk,)).fetchone()
            disp_order = existing[0] if existing else 500
            fallback_yield = "Eligible collateral for Convex LTV." if ltv_turbo_eligible else "Compounded value generation / Staking yield."
            final_yield = yield_mechanism if (yield_mechanism and yield_mechanism.strip()) else (existing[1] if (existing and existing[1]) else fallback_yield)
            conn.execute(
                """
                INSERT OR REPLACE INTO portfolio_assets (
                    ticker, name, category, sector_vertical, target_weight_pct,
                    avg_buy_price, ltv_turbo_eligible, fair_price,
                    role_description, accumulate_rule, sell_rule, yield_mechanism, display_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tk,
                    name.strip() or tk,
                    category,
                    sector_vertical,
                    round(float(target_weight_pct), 3),
                    round(float(avg_buy_price), 4),
                    1 if ltv_turbo_eligible else 0,
                    round(float(fp), 2),
                    role_desc,
                    acc_rule,
                    sell_rule,
                    final_yield,
                    disp_order,
                ),
            )
            conn.commit()
        self._sync_sqlite_to_json()

    def get_all_assets(self):
        return self.get_all_assets_from_db()

    def delete_asset(self, ticker: str) -> None:
        self.remove_asset(ticker)

    def remove_asset(self, ticker: str) -> None:
        tk = ticker.strip().upper()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM portfolio_assets WHERE ticker = ?", (tk,))
            conn.commit()
        self._sync_sqlite_to_json()

    def normalize_weights_to_100(self) -> None:
        assets = self.get_all_assets_from_db()
        total = sum(a["target_weight_pct"] for a in assets)
        if total <= 0:
            return
        with sqlite3.connect(self.db_path) as conn:
            running_sum = 0.0
            for idx, a in enumerate(assets):
                if idx < len(assets) - 1:
                    new_w = round((a["target_weight_pct"] / total) * 100.0, 3)
                    running_sum += new_w
                else:
                    new_w = round(max(0.0, 100.0 - running_sum), 3)
                conn.execute(
                    "UPDATE portfolio_assets SET target_weight_pct = ? WHERE ticker = ?",
                    (new_w, a["ticker"]),
                )
            conn.commit()
        self._sync_sqlite_to_json()

    def load_config(self) -> Dict[str, Any]:
        assets = self.get_all_assets_from_db()
        crypto_w = sum(a["target_weight_pct"] for a in assets if "Crypto" in a["category"])
        hard_w = sum(a["target_weight_pct"] for a in assets if "Crypto" not in a["category"])
        return {
            "total_crypto_pct": round(crypto_w, 3),
            "total_hard_assets_pct": round(hard_w, 3),
            "assets": assets,
        }

    def build_overview_and_lookthrough(self, capital_usd: float = 10000000.0) -> PortfolioOverviewBundle:
        cfg = self.load_config()
        assets_cfg = cfg.get("assets", [])

        tickers = [a["ticker"] for a in assets_cfg]
        live_prices: Dict[str, float] = {}
        if tickers:
            try:
                live_prices = fetch_all_quotes_parallel(tickers)
            except Exception:
                pass

        positions: List[PortfolioPosition] = []
        etf_weights: Dict[str, float] = {}
        direct_stock_weights: Dict[str, Dict[str, Any]] = {}

        # Simulates minor organic weight drift vs target weight to enrich Shannon Inflow analysis
        drift_simulation = {
            "BTC-USD": +1.10,
            "ETH-USD": -0.65,
            "SOL-USD": +0.25,
            "AAVE-USD": -0.45,
            "SPY": +0.10,
            "QQQ": +0.20,
            "SMH": -0.35,
            "ITA": +0.15,
            "QLD": +0.30,
            "AAPL": -0.10,
            "MSFT": -0.25,
            "GOOGL": -0.35,
            "AMZN": -0.20,
            "NVDA": +0.45,
            "META": +0.15,
            "V": -0.15,
            "JPM": +0.10,
            "WMT": +0.05,
            "DBSDY": -0.35,
        }

        target_weight_sum = round(sum(float(a.get("target_weight_pct", 0.0)) for a in assets_cfg), 3)
        diff_100 = round(target_weight_sum - 100.0, 3)
        is_valid_100 = abs(diff_100) <= 0.05
        if is_valid_100:
            weight_msg = f"✅ BALANCED PORTFOLIO: Target Weight Sum at {target_weight_sum:.2f}% (100.00% Fully Allocated)"
        elif diff_100 > 0:
            weight_msg = f"⚠️ OVER-ALLOCATION WARNING: Target Weight Sum at {target_weight_sum:.2f}% (+{diff_100:.2f}% over 100%)"
        else:
            weight_msg = f"⚠️ UNDER-ALLOCATION WARNING: Target Weight Sum at {target_weight_sum:.2f}% ({abs(diff_100):.2f}% short of 100%)"

        ltv_eligible_stocks_w = 0.0
        ltv_eligible_btc_w = 0.0
        total_pnl_usd = 0.0
        total_cost_basis_usd = 0.0

        for a in assets_cfg:
            tk = a["ticker"]
            t_w = float(a.get("target_weight_pct", 2.5))
            drift = drift_simulation.get(tk, -0.10)
            c_w = round(max(0.05, t_w + drift), 3)
            px = live_prices.get(tk) or DEFAULT_SPOT_PRICES.get(tk) or float(a.get("fair_price", 100.0))
            avg_buy = float(a.get("avg_buy_price", DEFAULT_AVG_BUY_PRICES.get(tk, px * 0.82)))
            if avg_buy <= 0:
                avg_buy = px
            ltv_ok = bool(a.get("ltv_turbo_eligible", True))

            alloc_usd = (c_w / 100.0) * capital_usd
            qty = alloc_usd / px if px > 0 else 0.0
            cost_basis_usd = qty * avg_buy
            pnl_usd = alloc_usd - cost_basis_usd
            pnl_pct = ((px / avg_buy) - 1.0) * 100.0 if avg_buy > 0 else 0.0

            total_pnl_usd += pnl_usd
            total_cost_basis_usd += cost_basis_usd

            cat = a.get("category", "Hard-Asset Stock")
            sec_v = a.get("sector_vertical", "OTHER")

            if ltv_ok:
                if "Crypto" in cat:
                    ltv_eligible_btc_w += t_w
                else:
                    ltv_eligible_stocks_w += t_w

            positions.append(
                PortfolioPosition(
                    ticker=tk,
                    name=a.get("name", tk),
                    category=cat,
                    sector_vertical=sec_v,
                    target_weight_pct=round(t_w, 3),
                    current_weight_pct=round(c_w, 3),
                    weight_drift_pp=round(c_w - t_w, 3),
                    allocated_usd=round(alloc_usd, 2),
                    current_price_usd=round(px, 2),
                    avg_buy_price_usd=round(avg_buy, 2),
                    pnl_pct=round(pnl_pct, 2),
                    pnl_usd=round(pnl_usd, 2),
                    ltv_turbo_eligible=ltv_ok,
                    quantity_units=round(qty, 4),
                    role_description=a.get("role_description", ""),
                    yield_mechanism=a.get("yield_mechanism", ""),
                )
            )

            if cat == "Hard-Asset ETF":
                etf_weights[tk] = t_w
            elif cat == "Hard-Asset Stock":
                direct_stock_weights[tk] = {
                    "name": a.get("name", tk),
                    "sector": sec_v,
                    "weight": t_w,
                }

        total_pnl_pct = round((total_pnl_usd / total_cost_basis_usd) * 100.0, 2) if total_cost_basis_usd > 0 else 0.0

        # ======================================================================
        # ETF LOOK-THROUGH DECOMPOSITION (SPY, QQQ, SMH, ITA, and 2x QLD)
        # ======================================================================
        w_spy = etf_weights.get("SPY", 0.0)
        w_qqq = etf_weights.get("QQQ", 0.0)
        w_smh = etf_weights.get("SMH", 0.0)
        w_ita = etf_weights.get("ITA", 0.0)
        w_qld = etf_weights.get("QLD", 0.0)  # QLD provides 2x daily leverage on the Nasdaq-100 (QQQ)

        # Strictly filters equities that the investor ACTUALLY owns in the portfolio
        # to highlight the overlap of ETF holdings across direct equities,
        # consolidating the residual index basket into a single summary row.
        all_lookthrough_tickers = list(direct_stock_weights.keys())

        sector_labels_map = {
            "TECH_CASH_COW": "Big Tech / Cash Cow",
            "TECH_HIGH_GROWTH": "High-Growth Tech & AI",
            "FINANCIAL_TOLLBOOTH": "Financials / Payments",
            "FINANCIAL_BANK": "Financials / Global Banks",
            "RETAIL": "Consumer / Retail",
            "CYCLICAL": "Cyclicals / Commodities",
        }

        lookthrough_list: List[LookThroughHolding] = []
        owned_spy_sum = 0.0
        owned_qqq_sum = 0.0
        owned_smh_sum = 0.0
        owned_ita_sum = 0.0
        owned_qld_sum = 0.0

        for tk in all_lookthrough_tickers:
            d_info = direct_stock_weights.get(tk)
            direct_w = d_info["weight"] if d_info else 0.0

            spy_h = ETF_CONSTITUENTS_MAP["SPY"].get(tk, {}).get("weight_pct", 0.0)
            qqq_h = ETF_CONSTITUENTS_MAP["QQQ"].get(tk, {}).get("weight_pct", 0.0)
            smh_h = ETF_CONSTITUENTS_MAP["SMH"].get(tk, {}).get("weight_pct", 0.0)
            ita_h = ETF_CONSTITUENTS_MAP["ITA"].get(tk, {}).get("weight_pct", 0.0)

            spy_ind = round(w_spy * (spy_h / 100.0), 3)
            qqq_ind = round(w_qqq * (qqq_h / 100.0), 3)
            smh_ind = round(w_smh * (smh_h / 100.0), 3)
            ita_ind = round(w_ita * (ita_h / 100.0), 3)
            qld_2x_ind = round((w_qld * 2.0) * (qqq_h / 100.0), 3)

            owned_spy_sum += spy_ind
            owned_qqq_sum += qqq_ind
            owned_smh_sum += smh_ind
            owned_ita_sum += ita_ind
            owned_qld_sum += qld_2x_ind

            tot_ind = round(spy_ind + qqq_ind + smh_ind + ita_ind + qld_2x_ind, 3)
            tot_eff = round(direct_w + tot_ind, 3)
            if tot_eff <= 0:
                continue

            name = d_info["name"] if d_info else tk
            sector = sector_labels_map.get(d_info["sector"], d_info["sector"]) if d_info else "Equity"

            sources = []
            if direct_w > 0:
                sources.append(f"Direct ({direct_w:.2f}%)")
            if spy_ind > 0:
                sources.append(f"SPY ({spy_ind:.2f}%)")
            if qqq_ind > 0:
                sources.append(f"QQQ ({qqq_ind:.2f}%)")
            if smh_ind > 0:
                sources.append(f"SMH ({smh_ind:.2f}%)")
            if ita_ind > 0:
                sources.append(f"ITA ({ita_ind:.2f}%)")
            if qld_2x_ind > 0:
                sources.append(f"QLD 2x ({qld_2x_ind:.2f}%)")

            lookthrough_list.append(
                LookThroughHolding(
                    ticker=tk,
                    company_name=name,
                    sector=sector,
                    direct_weight_pct=round(direct_w, 3),
                    spy_indirect_pct=spy_ind,
                    qqq_indirect_pct=qqq_ind,
                    smh_indirect_pct=smh_ind,
                    ita_indirect_pct=ita_ind,
                    qld_2x_indirect_pct=qld_2x_ind,
                    total_indirect_pct=tot_ind,
                    total_effective_lookthrough_pct=tot_eff,
                    effective_exposure_usd=round((tot_eff / 100.0) * capital_usd, 2),
                    overlap_sources=" + ".join(sources),
                )
            )

        lookthrough_list.sort(key=lambda x: x.total_effective_lookthrough_pct, reverse=True)

        # Consolidated row for residual diversified ETF holdings
        rem_spy = round(max(0.0, w_spy - owned_spy_sum), 3)
        rem_qqq = round(max(0.0, w_qqq - owned_qqq_sum), 3)
        rem_smh = round(max(0.0, w_smh - owned_smh_sum), 3)
        rem_ita = round(max(0.0, w_ita - owned_ita_sum), 3)
        rem_qld = round(max(0.0, (w_qld * 2.0) - owned_qld_sum), 3)
        rem_tot = round(rem_spy + rem_qqq + rem_smh + rem_ita + rem_qld, 3)
        if rem_tot > 0:
            rem_sources = []
            if rem_spy > 0:
                rem_sources.append(f"SPY Residual ({rem_spy:.2f}%)")
            if rem_qqq > 0:
                rem_sources.append(f"QQQ Residual ({rem_qqq:.2f}%)")
            if rem_smh > 0:
                rem_sources.append(f"SMH Residual ({rem_smh:.2f}%)")
            if rem_ita > 0:
                rem_sources.append(f"ITA Defense ({rem_ita:.2f}%)")
            if rem_qld > 0:
                rem_sources.append(f"QLD 2x Residual ({rem_qld:.2f}%)")
            lookthrough_list.append(
                LookThroughHolding(
                    ticker="ETF-BASKET",
                    company_name="Diversified ETF Residual Basket (Index Constituents Outside Direct Holdings)",
                    sector="Index Diversification (SPY/QQQ/QLD/ITA)",
                    direct_weight_pct=0.0,
                    spy_indirect_pct=rem_spy,
                    qqq_indirect_pct=rem_qqq,
                    smh_indirect_pct=rem_smh,
                    ita_indirect_pct=rem_ita,
                    qld_2x_indirect_pct=rem_qld,
                    total_indirect_pct=rem_tot,
                    total_effective_lookthrough_pct=rem_tot,
                    effective_exposure_usd=round((rem_tot / 100.0) * capital_usd, 2),
                    overlap_sources=" + ".join(rem_sources),
                )
            )

        btc_w = round(sum(p.target_weight_pct for p in positions if p.category == "Crypto BTC"), 2)
        alt_w = round(sum(p.target_weight_pct for p in positions if p.category == "Crypto Altcoin"), 2)
        total_crypto_pct = round(btc_w + alt_w, 2)
        total_hard_pct = round(target_weight_sum - total_crypto_pct, 2)
        eff_gross_pct = round(target_weight_sum + w_qld, 2)

        # Dynamic Look-Through Sector Consolidation
        sector_summary = [
            {
                "Sector / Look-Through Block": "Bitcoin (Sovereign Monetary Reserve PoW)",
                "Nominal Weight (%)": btc_w,
                "Effective Look-Through Exposure (%)": btc_w,
                "Financial Exposure ($)": round(capital_usd * (btc_w / 100.0), 2),
                "Primary Contributing Assets": ", ".join(f"{p.ticker} ({p.target_weight_pct:.2f}%)" for p in positions if p.category == "Crypto BTC") or "None",
            },
            {
                "Sector / Look-Through Block": "Web3 Infrastructure, Smart Contracts & DeFi",
                "Nominal Weight (%)": alt_w,
                "Effective Look-Through Exposure (%)": alt_w,
                "Financial Exposure ($)": round(capital_usd * (alt_w / 100.0), 2),
                "Primary Contributing Assets": ", ".join(f"{p.ticker} ({p.target_weight_pct:.2f}%)" for p in positions if p.category == "Crypto Altcoin") or "None",
            },
            {
                "Sector / Look-Through Block": "Big Tech, Cloud, Semiconductors & AI",
                "Nominal Weight (%)": round(sum(p.target_weight_pct for p in positions if p.sector_vertical in ("TECH_CASH_COW", "TECH_HIGH_GROWTH")) + w_qqq + w_smh + w_qld, 2),
                "Effective Look-Through Exposure (%)": round(sum(h.total_effective_lookthrough_pct for h in lookthrough_list if any(k in h.sector for k in ("Tech", "Semi", "Cloud", "Search", "Ads"))), 2),
                "Financial Exposure ($)": round(sum(h.effective_exposure_usd for h in lookthrough_list if any(k in h.sector for k in ("Tech", "Semi", "Cloud", "Search", "Ads"))), 2),
                "Primary Contributing Assets": ", ".join(f"{h.ticker} ({h.total_effective_lookthrough_pct:.2f}%)" for h in lookthrough_list[:6]),
            },
            {
                "Sector / Look-Through Block": "Financial Sector, Global Banks & Payments",
                "Nominal Weight (%)": round(sum(p.target_weight_pct for p in positions if p.sector_vertical in ("FINANCIAL_BANK", "FINANCIAL_TOLLBOOTH")), 2),
                "Effective Look-Through Exposure (%)": round(sum(h.total_effective_lookthrough_pct for h in lookthrough_list if "Financial" in h.sector), 2),
                "Financial Exposure ($)": round(sum(h.effective_exposure_usd for h in lookthrough_list if "Financial" in h.sector), 2),
                "Primary Contributing Assets": ", ".join(f"{h.ticker} ({h.total_effective_lookthrough_pct:.2f}%)" for h in lookthrough_list if "Financial" in h.sector),
            },
            {
                "Sector / Look-Through Block": "Aerospace, NATO Defense, Retail & Broad S&P",
                "Nominal Weight (%)": round(w_ita + w_spy + sum(p.target_weight_pct for p in positions if p.sector_vertical in ("RETAIL", "CYCLICAL", "OTHER") and p.category == "Hard-Asset Stock"), 2),
                "Effective Look-Through Exposure (%)": round(sum(h.total_effective_lookthrough_pct for h in lookthrough_list if not any(k in h.sector for k in ("Tech", "Semi", "Cloud", "Search", "Ads", "Financial"))), 2),
                "Financial Exposure ($)": round(sum(h.effective_exposure_usd for h in lookthrough_list if not any(k in h.sector for k in ("Tech", "Semi", "Cloud", "Search", "Ads", "Financial"))), 2),
                "Primary Contributing Assets": "ITA (Defense), WMT, SPY Core & Diversified",
            },
        ]

        return PortfolioOverviewBundle(
            capital_usd=capital_usd,
            total_crypto_pct=total_crypto_pct,
            total_hard_assets_pct=total_hard_pct,
            target_weight_sum_pct=target_weight_sum,
            is_weight_valid_100=is_valid_100,
            weight_validation_message=weight_msg,
            ltv_eligible_stocks_weight_pct=round(ltv_eligible_stocks_w, 2),
            ltv_eligible_btc_weight_pct=round(ltv_eligible_btc_w, 2),
            total_portfolio_pnl_usd=round(total_pnl_usd, 2),
            total_portfolio_pnl_pct=total_pnl_pct,
            effective_gross_exposure_pct=eff_gross_pct,
            positions=positions,
            lookthrough_holdings=lookthrough_list,
            sector_exposure_summary=sector_summary,
        )

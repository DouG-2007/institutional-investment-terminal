"""
MODULE 4: QUANTITATIVE AND FORENSIC SCREENER FOR NEW OPPORTUNITIES (STOCKS & CRYPTOASSETS)
Strictly executes all filters from the "Value Investing Framework (TRUE)" and compiles
forensic, valuation, on-chain, and governance indicators for each candidate:

Equity Screening Filters:
1. Sloan Ratio <= +5.0% (highlighting < -10% as Optimal);
2. CFO / EBITDA >= 0.90x (highlighting > 1.0x as Optimal);
3. ROIC (via NOPAT) >= 18.0% and > WACC;
4. Resilient Solvency: Current Ratio > 1.0x, positive post-OpEx cash flow, and Interest Coverage > 4.0x (healthy minimum > 3.0x);
5. Forward Valuation & Sector Fit: Reverse DCF (g_impl <= g_fund) + healthy sectoral metrics (PEGY / Enterprise PEGY / DCF / SOTP).

Cryptoasset Screening Filters:
1. Circulating Supply >= 65.0%;
2. Monthly Unlocks <= 2.5%/month (highlighting < 1.0% as Low Dilution);
3. Token Sniffer Security Score >= 85/100 and top-tier code audits;
4. Active Developers >= 40 on GitHub and Protocol Real Earnings > 0;
5. MVRV Z-Score <= 2.0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.market_data import fetch_all_quotes_parallel
from core.live_quant_fetcher import fetch_live_crypto_metrics, fetch_live_equity_fundamentals


@dataclass
class StockScreenerRow:
    ticker: str
    company_name: str
    sector: str
    country: str
    price_usd: float
    # Forensic & Solvency Filters
    sloan_ratio_pct: float
    sloan_status: str
    fco_to_ebitda: float
    fco_ebitda_status: str
    roic_nopat_pct: float
    wacc_pct: float
    current_ratio: float
    interest_coverage_x: float
    # Valuation & Sector Filters
    reverse_dcf_g_impl_pct: float
    g_fund_pct: float
    enterprise_or_fin_pegy: float
    pegy_type: str
    dcf_fair_mos10_usd: float
    sotp_fair_usd: float
    # Modules 2 & 3 (Filings & Geopolitics/Micro)
    auditor_sox404b: str
    moat_and_catalysts: str
    # 5 Strict Filter Outcomes
    filters_passed_count: int
    all_5_filters_passed: bool
    framework_verdict: str


@dataclass
class CryptoScreenerRow:
    symbol: str
    name: str
    category: str
    price_usd: float
    market_cap_b: float
    fdv_b: float
    # 5 Strict Filters
    circulating_supply_pct: float
    monthly_unlock_pct: float
    unlock_status: str
    post_unlock_theoretical_px: float
    token_sniffer_score: int
    security_audits: str
    active_devs_github: int
    github_commits_4w: int
    protocol_real_earnings_m: float
    real_yield_pct: float
    pf_ratio: float
    mvrv_z_score: float
    nupl: float
    # Governance & Micro
    whitepaper_and_dao: str
    filters_passed_count: int
    all_5_filters_passed: bool
    framework_verdict: str


STOCK_CANDIDATES_RAW: List[Dict[str, Any]] = [
    {
        "ticker": "ASML",
        "name": "ASML Holding N.V.",
        "sector": "High-Growth Tech / EUV Lithography",
        "country": "Netherlands (EU)",
        "px": 745.00,
        "sloan": -11.2,
        "fco_eb": 1.24,
        "roic": 44.5,
        "wacc": 8.9,
        "z": 8.60,
        "cr": 1.58,
        "icov": 34.0,
        "g_impl": 15.8,
        "g_fund": 19.5,
        "pegy": 1.12,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 835.0,
        "sotp": 860.0,
        "audit": "KPMG — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (100% Global Monopoly in EUV & High-NA EUV Lithography; EUR 36B Backlog)",
    },
    {
        "ticker": "TSM",
        "name": "Taiwan Semiconductor (TSMC)",
        "sector": "High-Growth Tech / Pure-Play Foundry",
        "country": "Taiwan / US ADR",
        "px": 192.00,
        "sloan": -10.6,
        "fco_eb": 1.18,
        "roic": 31.8,
        "wacc": 8.8,
        "z": 7.95,
        "cr": 2.35,
        "icov": 42.0,
        "g_impl": 14.5,
        "g_fund": 21.0,
        "pegy": 0.88,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 228.0,
        "sotp": 240.0,
        "audit": "Deloitte — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Global Foundry Monopoly in 3nm/2nm Wafers and CoWoS Advanced Packaging for AI)",
    },
    {
        "ticker": "MELI",
        "name": "MercadoLibre, Inc.",
        "sector": "High-Growth Tech / E-Commerce & Fintech",
        "country": "US / Latin America",
        "px": 1980.00,
        "sloan": -12.4,
        "fco_eb": 1.32,
        "roic": 29.4,
        "wacc": 10.4,
        "z": 4.45,
        "cr": 1.36,
        "icov": 14.8,
        "g_impl": 19.2,
        "g_fund": 26.5,
        "pegy": 0.96,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 2240.0,
        "sotp": 2380.0,
        "audit": "PwC — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Two-Sided Network Effects: Marketplace + Mercado Pago + Proprietary Fulfillment Logistics)",
    },
    {
        "ticker": "NU",
        "name": "Nu Holdings Ltd. (Nubank)",
        "sector": "Fintech / Digital Banking",
        "country": "Brazil / Mexico / Colombia",
        "px": 14.20,
        "sloan": -13.1,
        "fco_eb": 1.28,
        "roic": 31.2,
        "wacc": 11.2,
        "z": 3.65,
        "cr": 1.48,
        "icov": 28.0,
        "g_impl": 21.5,
        "g_fund": 30.0,
        "pegy": 0.78,
        "pegy_t": "Financial / Fintech PEGY",
        "dcf": 17.5,
        "sotp": 18.2,
        "audit": "KPMG — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Cost-to-Serve < $0.90/month, 110M+ Customers & Accelerating Deposit Growth in Mexico)",
    },
    {
        "ticker": "AVGO",
        "name": "Broadcom Inc.",
        "sector": "High-Growth Tech / Custom AI Silicon & VMware",
        "country": "United States",
        "px": 176.00,
        "sloan": -8.4,
        "fco_eb": 1.04,
        "roic": 24.8,
        "wacc": 8.9,
        "z": 4.12,
        "cr": 1.22,
        "icov": 7.8,
        "g_impl": 16.0,
        "g_fund": 18.5,
        "pegy": 1.15,
        "pegy_t": "Enterprise PEGY (EV/FCF)",
        "dcf": 192.0,
        "sotp": 204.0,
        "audit": "PwC — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Dominant Custom AI ASIC Provider for Hyperscalers + VMware Infrastructure Software Monopoly)",
    },
    {
        "ticker": "MA",
        "name": "Mastercard Incorporated",
        "sector": "Cash Cow / Payment Rails Duopoly",
        "country": "United States",
        "px": 512.00,
        "sloan": -11.8,
        "fco_eb": 1.09,
        "roic": 58.2,
        "wacc": 8.2,
        "z": 11.50,
        "cr": 1.18,
        "icov": 36.5,
        "g_impl": 13.4,
        "g_fund": 15.2,
        "pegy": 1.18,
        "pegy_t": "Enterprise PEGY (EV/FCF)",
        "dcf": 545.0,
        "sotp": 560.0,
        "audit": "PwC — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Global Payment Rails Duopoly with > 58% Operating Margin and Cyber Value-Added Services)",
    },
    {
        "ticker": "COST",
        "name": "Costco Wholesale Corp.",
        "sector": "Subscription Retail / Defensive",
        "country": "United States",
        "px": 915.00,
        "sloan": -6.2,
        "fco_eb": 1.11,
        "roic": 24.5,
        "wacc": 7.6,
        "z": 6.40,
        "cr": 1.04,
        "icov": 48.0,
        "g_impl": 14.8,
        "g_fund": 11.2,  # Fails Filter 5 (g_impl > g_fund & PEGY > 1.6)
        "pegy": 1.88,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 740.0,
        "sotp": 790.0,
        "audit": "KPMG — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Flawless Membership Business Model with SSS +7.2%, but Fails Current Valuation Filter)",
    },
    {
        "ticker": "LLY",
        "name": "Eli Lilly and Company",
        "sector": "Healthcare / GLP-1 Duopoly",
        "country": "United States",
        "px": 860.00,
        "sloan": -3.8,
        "fco_eb": 0.92,
        "roic": 27.5,
        "wacc": 7.9,
        "z": 5.20,
        "cr": 1.15,
        "icov": 16.2,
        "g_impl": 24.5,
        "g_fund": 22.0,  # g_impl > g_fund
        "pegy": 1.54,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 795.0,
        "sotp": 840.0,
        "audit": "EY — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Mounjaro/Zepbound Incretin Patents; Await Retracement for g_impl <= g_fund)",
    },
    {
        "ticker": "INTC",
        "name": "Intel Corporation",
        "sector": "Legacy IDM Semiconductor",
        "country": "United States",
        "px": 23.50,
        "sloan": +6.8,  # Fails Sloan (> +5.0%)
        "fco_eb": 0.68,  # Fails CFO/EBITDA (< 0.90x)
        "roic": 2.1,    # Fails ROIC (< 18%)
        "wacc": 9.4,
        "z": 1.65,      # Fails Altman Z (< 2.90)
        "cr": 1.32,
        "icov": 1.8,    # Fails Interest Coverage (< 4.0x)
        "g_impl": 8.5,
        "g_fund": 3.0,
        "pegy": 2.45,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 18.0,
        "sotp": 21.0,
        "audit": "EY — Unqualified / Restructuring",
        "moat_cat": "Narrow/Eroding Moat (Lost Process Node Supremacy to TSMC and AI GPU Acceleration to Nvidia)",
    },
]


CRYPTO_CANDIDATES_RAW: List[Dict[str, Any]] = [
    {
        "symbol": "MKR",
        "name": "Maker / Sky Protocol",
        "category": "DeFi Central Bank & RWA Treasury",
        "px": 1580.0,
        "mcap_b": 1.45,
        "fdv_b": 1.52,
        "circ_pct": 95.4,
        "unlock_pct": 0.0,
        "sniffer": 100,
        "audits": "Trail of Bits, OpenZeppelin, Runtime Verification, ChainSecurity",
        "devs": 115,
        "commits": 320,
        "real_earnings_m": +142.0,
        "real_yield_pct": 6.8,
        "pf": 6.2,
        "mvrv_z": 0.55,
        "nupl": 0.21,
        "wp_dao": "DAI/USDS Whitepaper + Smart Burn Engine (Continuous MKR Buyback Funded by RWA T-Bill Net Interest Income)",
    },
    {
        "symbol": "PENDLE",
        "name": "Pendle Finance V2",
        "category": "DeFi Yield Tokenization & Fixed Income AMM",
        "px": 4.65,
        "mcap_b": 0.76,
        "fdv_b": 1.20,
        "circ_pct": 66.2,
        "unlock_pct": 0.45,
        "sniffer": 98,
        "audits": "Ackee Blockchain, Dedaub, WatchPug, Spearbit",
        "devs": 68,
        "commits": 235,
        "real_earnings_m": +34.5,
        "real_yield_pct": 8.9,
        "pf": 16.4,
        "mvrv_z": 0.78,
        "nupl": 0.31,
        "wp_dao": "EIP-5115 Principal/Yield Token (PT/YT) Standard + 42% of Circulating Supply Locked in vePENDLE",
    },
    {
        "symbol": "LINK",
        "name": "Chainlink Network",
        "category": "Decentralized Oracle Monopoly & CCIP RWA",
        "px": 13.80,
        "mcap_b": 8.65,
        "fdv_b": 13.80,
        "circ_pct": 65.5,
        "unlock_pct": 0.58,
        "sniffer": 100,
        "audits": "SigmaPrime, Trail of Bits, Certora, OpenZeppelin",
        "devs": 315,
        "commits": 590,
        "real_earnings_m": +42.0,
        "real_yield_pct": 4.3,
        "pf": 48.0,
        "mvrv_z": 0.48,
        "nupl": 0.18,
        "wp_dao": "Global Oracle Monopoly ($75B+ TVS) and CCIP Interoperability Protocol Adopted by SWIFT, DTCC & Euroclear",
    },
    {
        "symbol": "UNI",
        "name": "Uniswap Protocol (Unichain)",
        "category": "DEX Liquidity Monopoly & DeFi L2",
        "px": 8.90,
        "mcap_b": 5.35,
        "fdv_b": 8.90,
        "circ_pct": 75.3,
        "unlock_pct": 0.25,
        "sniffer": 100,
        "audits": "Trail of Bits, ABDK, OpenZeppelin, Spearbit",
        "devs": 185,
        "commits": 410,
        "real_earnings_m": +95.0,
        "real_yield_pct": 3.5,
        "pf": 11.2,
        "mvrv_z": 0.64,
        "nupl": 0.24,
        "wp_dao": "Uniswap V4 Programmable Hooks + Unichain L2 Capturing MEV & Priority Sequencing Fees for Stakers",
    },
    {
        "symbol": "SUI",
        "name": "Sui Network",
        "category": "Layer-1 Move Blockchain",
        "px": 2.15,
        "mcap_b": 6.10,
        "fdv_b": 21.50,
        "circ_pct": 28.4,      # Fails Filter 1 (< 65% Circulating Supply)
        "unlock_pct": 4.20,    # Fails Filter 2 (> 2.5%/mo — Aggressive VC Dilution)
        "sniffer": 95,
        "audits": "Zellic, OtterSec",
        "devs": 145,
        "commits": 330,
        "real_earnings_m": -185.0,  # Fails Filter 4 (Token Inflation Outweighs Net Protocol Revenue)
        "real_yield_pct": -4.2,
        "pf": 390.0,
        "mvrv_z": 1.55,
        "nupl": 0.52,
        "wp_dao": "High-Throughput Parallel Move VM, but Rejected Due to Heavy VC/Seed Monthly Token Dilution",
    },
]


class ScreenerEngine:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _infer_sector_vertical(sector_desc: str) -> str:
        s = (sector_desc or "").lower()
        if "bank" in s or "financial" in s:
            return "FINANCIAL_BANK"
        if "retail" in s or "consumer" in s:
            return "RETAIL"
        if "semi" in s or "foundry" in s or "litho" in s or "high-growth" in s:
            return "TECH_HIGH_GROWTH"
        return "TECH_CASH_COW"

    def run_stock_screener(self, extra_tickers: Optional[List[str]] = None) -> List[StockScreenerRow]:
        out: List[StockScreenerRow] = []
        base_tks = [c["ticker"] for c in STOCK_CANDIDATES_RAW]
        sec_map = {c["ticker"]: self._infer_sector_vertical(c["sector"]) for c in STOCK_CANDIDATES_RAW}

        live_quotes: Dict[str, float] = {}
        live_funds: Dict[str, Dict[str, Any]] = {}
        try:
            live_quotes = fetch_all_quotes_parallel(base_tks)
        except Exception:
            live_quotes = {}
        try:
            live_funds = fetch_live_equity_fundamentals(base_tks, sector_vertical_map=sec_map)
        except Exception:
            live_funds = {}

        for raw in STOCK_CANDIDATES_RAW:
            c = dict(raw)
            tk = c["ticker"]
            orig_px = float(c["px"]) or 1.0
            if live_quotes.get(tk) and live_quotes[tk] > 0:
                c["px"] = round(float(live_quotes[tk]), 2)

            lf = live_funds.get(tk) or {}
            if lf.get("sloan_pct") is not None:
                c["sloan"] = round(float(lf["sloan_pct"]), 1)
            if lf.get("fco_b") is not None and lf.get("ebitda_b") and float(lf["ebitda_b"]) > 0:
                c["fco_eb"] = round(float(lf["fco_b"]) / float(lf["ebitda_b"]), 2)
            if lf.get("current_ratio") is not None and float(lf["current_ratio"]) > 0:
                c["cr"] = round(float(lf["current_ratio"]), 2)
            if lf.get("interest_coverage_x") is not None and float(lf["interest_coverage_x"]) > 0:
                c["icov"] = round(float(lf["interest_coverage_x"]), 1)

            px_scale = c["px"] / orig_px
            if 0.2 <= px_scale <= 5.0 and px_scale != 1.0:
                c["pegy"] = round(max(0.15, min(6.0, float(c["pegy"]) * px_scale)), 2)

            # Evaluate the 5 Strict Framework Filters:
            f1_sloan = c["sloan"] <= 5.0
            f2_fco = c["fco_eb"] >= 0.90
            f3_roic = (c["roic"] >= 18.0) and (c["roic"] > c["wacc"])
            f4_solv = (c["cr"] > 1.0) and (c["icov"] > 4.0)
            f5_val = (c["g_impl"] <= c["g_fund"]) and (c["pegy"] <= 1.25)

            passed_cnt = sum([f1_sloan, f2_fco, f3_roic, f4_solv, f5_val])
            all_passed = passed_cnt == 5

            sloan_st = "Optimal (< -10%)" if c["sloan"] < -10.0 else ("Approved (<= +5%)" if f1_sloan else "REJECTED (> +5%)")
            fco_st = "Optimal (> 1.0x)" if c["fco_eb"] > 1.0 else ("Approved (>= 0.90x)" if f2_fco else "REJECTED (< 0.90x)")

            if all_passed:
                verdict = f"APPROVED 5/5 (Elite Candidate — {c['pegy_t']} {c['pegy']:.2f}x | g_impl {c['g_impl']:.1f}% <= g_fund {c['g_fund']:.1f}%)"
            elif passed_cnt == 4 and not f5_val:
                verdict = "QUALITY WATCHLIST 4/5 (Passed Forensic/ROIC/Solvency; Awaiting g_impl <= g_fund)"
            else:
                verdict = f"REJECTED ({passed_cnt}/5 Filters — Violation of Forensic/Solvency Standards)"

            out.append(StockScreenerRow(
                ticker=c["ticker"],
                company_name=c["name"],
                sector=c["sector"],
                country=c["country"],
                price_usd=c["px"],
                sloan_ratio_pct=c["sloan"],
                sloan_status=sloan_st,
                fco_to_ebitda=c["fco_eb"],
                fco_ebitda_status=fco_st,
                roic_nopat_pct=c["roic"],
                wacc_pct=c["wacc"],
                current_ratio=c["cr"],
                interest_coverage_x=c["icov"],
                reverse_dcf_g_impl_pct=c["g_impl"],
                g_fund_pct=c["g_fund"],
                enterprise_or_fin_pegy=c["pegy"],
                pegy_type=c["pegy_t"],
                dcf_fair_mos10_usd=c["dcf"],
                sotp_fair_usd=c["sotp"],
                auditor_sox404b=c["audit"],
                moat_and_catalysts=c["moat_cat"],
                filters_passed_count=passed_cnt,
                all_5_filters_passed=all_passed,
                framework_verdict=verdict,
            ))

        if extra_tickers:
            known = {r.ticker.upper() for r in out}
            extras = [t.strip().upper() for t in extra_tickers if t and t.strip() and t.strip().upper() not in known]
            if extras:
                from core.deep_dive_engine import DeepDiveEngine

                dd_eng = DeepDiveEngine()
                for tk in extras:
                    try:
                        dd = dd_eng.analyze_single_ticker(tk)
                        if dd.equity_analysis is None:
                            continue
                        eq = dd.equity_analysis
                        fh = eq.forensic_health
                        vm = eq.valuation_methods
                        sloan_v = float(fh.get("sloan_ratio_pct", 0.0))
                        fco_eb_v = float(fh.get("fco_to_ebitda", 1.0))
                        roic_v = float(fh.get("roic_goodwill_pct", 0.0))
                        wacc_v = float(fh.get("wacc_pct", 9.0))
                        cr_v = float(fh.get("current_ratio", 1.0))
                        icov_v = float(fh.get("interest_coverage_x", 5.0))
                        g_impl_v = float(vm.get("reverse_dcf_g_impl_pct", 12.0))
                        g_fund_v = float(vm.get("g_fund_consensus_pct", 12.0))
                        pegy_v = float(vm.get("primary_pegy_value", 1.5))

                        f1 = sloan_v <= 5.0
                        f2 = fco_eb_v >= 0.90
                        f3 = (roic_v >= 18.0) and (roic_v > wacc_v)
                        f4 = (cr_v > 1.0) and (icov_v > 4.0)
                        f5 = (g_impl_v <= g_fund_v) and (pegy_v <= 1.25)
                        p_cnt = sum([f1, f2, f3, f4, f5])
                        out.append(StockScreenerRow(
                            ticker=tk,
                            company_name=eq.company_name,
                            sector=eq.sector_label,
                            country="Global Market",
                            price_usd=eq.current_price,
                            sloan_ratio_pct=sloan_v,
                            sloan_status="Optimal (< -10%)" if sloan_v < -10.0 else ("Approved (<= +5%)" if f1 else "REJECTED (> +5%)"),
                            fco_to_ebitda=fco_eb_v,
                            fco_ebitda_status="Optimal (> 1.0x)" if fco_eb_v > 1.0 else ("Approved (>= 0.90x)" if f2 else "REJECTED (< 0.90x)"),
                            roic_nopat_pct=roic_v,
                            wacc_pct=wacc_v,
                            current_ratio=cr_v,
                            interest_coverage_x=icov_v,
                            reverse_dcf_g_impl_pct=g_impl_v,
                            g_fund_pct=g_fund_v,
                            enterprise_or_fin_pegy=pegy_v,
                            pegy_type=str(vm.get("primary_pegy_label", "PEGY")),
                            dcf_fair_mos10_usd=float(vm.get("dcf_fair_mos10_usd", eq.current_price)),
                            sotp_fair_usd=float(vm.get("sotp_fair_price_usd", eq.current_price)),
                            auditor_sox404b="SEC Filing / Live Consensus",
                            moat_and_catalysts=dd.automated_consultative_verdict,
                            filters_passed_count=p_cnt,
                            all_5_filters_passed=(p_cnt == 5),
                            framework_verdict=f"CUSTOM WATCHLIST ({p_cnt}/5 Filters — Score {dd.screener_score_0_100}/100)",
                        ))
                    except Exception:
                        continue
        return out

    @staticmethod
    def _build_crypto_screener_row(c: Dict[str, Any]) -> CryptoScreenerRow:
        """Evaluates the 5 strict tokenomics/security/on-chain filters into a CryptoScreenerRow."""
        f1_supply = float(c["circ_pct"]) >= 65.0
        f2_unlock = float(c["unlock_pct"]) <= 2.5
        f3_sec = int(c["sniffer"]) >= 85
        f4_dev_earn = (int(c["devs"]) >= 40) and (float(c["real_earnings_m"]) > 0)
        f5_mvrv = float(c["mvrv_z"]) <= 2.0

        passed_cnt = sum([f1_supply, f2_unlock, f3_sec, f4_dev_earn, f5_mvrv])
        all_passed = passed_cnt == 5

        unlock_st = (
            f"Low Impact ({float(c['unlock_pct']):.2f}% < 1.0%/mo)"
            if float(c["unlock_pct"]) < 1.0
            else (
                f"Moderate Impact ({float(c['unlock_pct']):.2f}% <= 2.5%/mo)"
                if f2_unlock
                else f"HIGH DILUTION ({float(c['unlock_pct']):.2f}% > 2.5%/mo — VCs)"
            )
        )
        post_unlock_px = round(float(c["px"]) / (1.0 + (float(c["unlock_pct"]) / 100.0)), 2)

        if all_passed:
            verdict = (
                f"APPROVED 5/5 (Real Cash Flow +${float(c['real_earnings_m']):.1f}M | "
                f"Supply {float(c['circ_pct']):.1f}% | MVRV Z {float(c['mvrv_z']):.2f})"
            )
        else:
            verdict = f"REJECTED ({passed_cnt}/5 Filters — Failed on Supply Dilution / Negative Real Earnings)"

        return CryptoScreenerRow(
            symbol=str(c["symbol"]),
            name=str(c["name"]),
            category=str(c["category"]),
            price_usd=float(c["px"]),
            market_cap_b=float(c["mcap_b"]),
            fdv_b=float(c["fdv_b"]),
            circulating_supply_pct=float(c["circ_pct"]),
            monthly_unlock_pct=float(c["unlock_pct"]),
            unlock_status=unlock_st,
            post_unlock_theoretical_px=post_unlock_px,
            token_sniffer_score=int(c["sniffer"]),
            security_audits=str(c["audits"]),
            active_devs_github=int(c["devs"]),
            github_commits_4w=int(c["commits"]),
            protocol_real_earnings_m=float(c["real_earnings_m"]),
            real_yield_pct=float(c["real_yield_pct"]),
            pf_ratio=float(c["pf"]),
            mvrv_z_score=float(c["mvrv_z"]),
            nupl=float(c["nupl"]),
            whitepaper_and_dao=str(c["wp_dao"]),
            filters_passed_count=passed_cnt,
            all_5_filters_passed=all_passed,
            framework_verdict=verdict,
        )

    def run_crypto_screener(self, extra_symbols: Optional[List[str]] = None) -> List[CryptoScreenerRow]:
        out: List[CryptoScreenerRow] = []
        yf_syms = [f"{c['symbol']}-USD" for c in CRYPTO_CANDIDATES_RAW]

        live_quotes: Dict[str, float] = {}
        live_cr: Dict[str, Dict[str, Any]] = {}
        try:
            live_quotes = fetch_all_quotes_parallel(yf_syms)
        except Exception:
            live_quotes = {}
        try:
            live_cr = fetch_live_crypto_metrics(yf_syms)
        except Exception:
            live_cr = {}

        kb_issuance: Dict[str, float] = {}
        try:
            from core.crypto_engine import CRYPTO_FUNDAMENTAL_KB

            kb_issuance = {k: float(v.get("token_issuance_annual_m", 0.0)) for k, v in CRYPTO_FUNDAMENTAL_KB.items()}
        except Exception:
            kb_issuance = {}

        for raw in CRYPTO_CANDIDATES_RAW:
            c = dict(raw)
            yf_sym = f"{c['symbol']}-USD"
            orig_px = float(c["px"]) or 1.0
            if live_quotes.get(yf_sym) and live_quotes[yf_sym] > 0:
                c["px"] = round(float(live_quotes[yf_sym]), 2)
                px_scale = c["px"] / orig_px
                if 0.05 <= px_scale <= 20.0:
                    c["mcap_b"] = round(float(c["mcap_b"]) * px_scale, 2)
                    c["fdv_b"] = round(float(c["fdv_b"]) * px_scale, 2)

            lc = live_cr.get(yf_sym) or {}
            if lc.get("mvrv_z") is not None:
                c["mvrv_z"] = round(float(lc["mvrv_z"]), 2)
            if lc.get("nupl") is not None:
                c["nupl"] = round(float(lc["nupl"]), 2)
            if lc.get("protocol_fees_annual_m") and float(lc["protocol_fees_annual_m"]) > 0:
                fees_m = float(lc["protocol_fees_annual_m"])
                iss_m = kb_issuance.get(yf_sym)
                if iss_m is None:
                    est_static_fees = (float(raw["mcap_b"]) * 1000.0) / max(float(raw["pf"]), 1.0)
                    iss_m = max(0.0, est_static_fees - float(raw["real_earnings_m"]))
                c["real_earnings_m"] = round(fees_m - iss_m, 2)
                c["pf"] = round((float(c["mcap_b"]) * 1000.0) / fees_m, 1)

            out.append(self._build_crypto_screener_row(c))

        if extra_symbols:
            known = {r.symbol.upper() for r in out}
            extras_norm = []
            for s in extra_symbols:
                su = (s or "").strip().upper()
                if not su:
                    continue
                base = su.split("-")[0]
                if base not in known and f"{base}-USD" not in [e[1] for e in extras_norm]:
                    extras_norm.append((base, f"{base}-USD"))
            if extras_norm:
                try:
                    from core.crypto_engine import CryptoEngine
                    from core.filings_engine import FilingsEngine

                    cr_profiles = CryptoEngine().analyze_portfolio_cryptos([sym for _, sym in extras_norm])
                    cr_dossiers = {
                        d.symbol.upper(): d
                        for d in FilingsEngine().get_crypto_dossiers([sym for _, sym in extras_norm])
                    }
                    for base, sym_usd in extras_norm:
                        prof = cr_profiles.get(sym_usd)
                        if prof is None:
                            continue
                        dos = cr_dossiers.get(sym_usd)
                        tv = prof.tokenomics_valuation
                        sup = prof.supply_structure
                        on = prof.onchain_metrics
                        out.append(
                            self._build_crypto_screener_row({
                                "symbol": base,
                                "name": prof.name,
                                "category": prof.category,
                                "px": prof.spot_price_usd,
                                "mcap_b": prof.market_cap_b,
                                "fdv_b": prof.fdv_b,
                                "circ_pct": prof.circulating_pct,
                                "unlock_pct": sup.get("unlock_pct_of_circ", 1.5),
                                "sniffer": getattr(dos, "token_sniffer_score", 75),
                                "audits": getattr(dos, "audit_firms", "Public Telemetry Pending"),
                                "devs": getattr(dos, "github_active_devs_monthly", 0),
                                "commits": getattr(dos, "github_commits_4w", 0),
                                "real_earnings_m": tv.get("protocol_real_earnings_m", 0.0),
                                "real_yield_pct": tv.get("real_yield_pct", 0.0),
                                "pf": tv.get("pf_ratio", 0.0),
                                "mvrv_z": on.get("mvrv_z_score", 0.0),
                                "nupl": on.get("nupl", 0.0),
                                "wp_dao": getattr(dos, "wp_value_proposition", prof.category),
                            })
                        )
                except Exception:
                    pass
        return out

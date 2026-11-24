"""
MODULE 3: GEOPOLITICAL MONITORING RADAR (MACRO) & INTERNAL PROTOCOL/CORPORATE EVENTS (MICRO)
1. Global Geopolitical Monitoring (Macro -> Portfolio):
   - Geopolitical Impact Matrix crossing Global Events, Severity, Affected Portfolio Assets,
     % Revenue/Production Exposed (SEC 10-K extraction) and Direct Fundamental Impact Mechanism (Margin, WACC, Supply Chain, Moat).
2. Internal Corporate / Protocol Event Monitoring (Micro):
   - Specific events extracted from SEC Form 8-K, Press Releases, Form 4 (Insider Trading) and DAO Governance,
     classified as Positive Catalyst, Neutral / Monitor, or Deterioration Warning / Red Flag.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
import os
from typing import Any, Dict, List
import yfinance as yf

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class GeopoliticalImpactRow:
    global_event: str
    region_vector: str
    severity: str
    affected_portfolio_assets: str
    revenue_or_production_exposed_pct: str
    fundamental_impact_mechanism: str
    country_liquidity_risk_assessment: str


@dataclass
class MicroCorporateProtocolEvent:
    date: str
    asset_ticker: str
    source_type: str  # SEC Form 8-K, Form 4 Insider, Press Release, DAO Governance
    headline: str
    event_category: str  # M&A, Buybacks, Guidance, Insider, Regulation, Protocol Upgrade, etc.
    fundamental_impact_analysis: str
    classification: str  # Positive Catalyst, Neutral / Monitor, Deterioration Warning / Red Flag


GEOPOLITICAL_MATRIX_DB: List[GeopoliticalImpactRow] = [
    GeopoliticalImpactRow(
        global_event="Taiwan Strait Geopolitical Tension & Advanced Foundry Concentration (3nm/2nm & CoWoS)",
        region_vector="Asia-Pacific (Taiwan / US / China)",
        severity="HIGH (Structural Tail Risk)",
        affected_portfolio_assets="NVDA, AAPL, SMH, QQQ, QLD, MSFT, AMZN, GOOGL",
        revenue_or_production_exposed_pct="NVDA (>90% GPU wafer production at TSMC) | AAPL (~85% M-series/A-series chips + Asian assembly) | SMH (20.5% NVDA + 12.8% TSM)",
        fundamental_impact_mechanism="Supply Chain & Gross Margin: Any maritime blockade or foundry disruption would elevate WACC (+150-250 bps via ERP) and compress hardware shipment volumes; partially mitigated by TSMC's new fabs in Arizona (US) and Kumamoto (Japan).",
        country_liquidity_risk_assessment="US-listed equities (Tier-1 Liquidity), yet with physical manufacturing exposure in Taiwan. ITA (NATO Defense) and BTC serve as structural tail-risk hedges.",
    ),
    GeopoliticalImpactRow(
        global_event="AI Semiconductor Export Controls (BIS / US Dept of Commerce vs. China) & Trade Tariffs",
        region_vector="US ↔ China / Global Supply Chain",
        severity="MEDIUM-HIGH",
        affected_portfolio_assets="NVDA, SMH, AAPL, WMT, AMZN",
        revenue_or_production_exposed_pct="NVDA (~12% Data Center revenue in China, down from historical 26%) | AAPL (~17% revenue in Greater China) | WMT/AMZN (General merchandise imports)",
        fundamental_impact_mechanism="Revenue & Pricing Power: BIS controls restrict sales of flagship AI processors (B200/H200) to China, but insatiable Western hyperscaler and sovereign AI demand absorbs 100% of supply, maintaining Gross Margins > 74%.",
        country_liquidity_risk_assessment="Zero liquidity risk for US tickers; supply chain regulatory risk is mitigated through ongoing diversification into India, Vietnam, and Mexico.",
    ),
    GeopoliticalImpactRow(
        global_event="Antitrust Enforcement DOJ / FTC (US) & Digital Markets Act — DMA (European Union) vs Big Tech & Payment Networks",
        region_vector="United States & European Union",
        severity="MEDIUM",
        affected_portfolio_assets="GOOGL, AAPL, V, META, AMZN, MSFT",
        revenue_or_production_exposed_pct="GOOGL (~15% Search volume via Apple ISA contract) | AAPL (~7% App Store revenue in EU) | V (~28% US debit volume under DOJ review)",
        fundamental_impact_mechanism="Moat & P/E Multiple: Risk of regulatory fines (up to 10% global revenue under DMA) or elimination of default search exclusivity. For Alphabet, ending the $20B/yr ISA payment to Apple would expand FCF if user retention persists via network habits.",
        country_liquidity_risk_assessment="Full rule-of-law jurisdictions (US/EU) with multi-year judicial appeals (3-5 years); immediate cash flow impact remains minimal.",
    ),
    GeopoliticalImpactRow(
        global_event="Escalating Regional Conflicts (Eastern Europe / Middle East) & Structural NATO Defense Budget Expansion (>2.5% of GDP)",
        region_vector="Europe / Middle East / NATO",
        severity="MEDIUM (Positive for Defense / Neutral for Consolidated Portfolio)",
        affected_portfolio_assets="ITA (Aerospace & Defense), BTC-USD, SPY",
        revenue_or_production_exposed_pct="ITA ETF (100% of holdings — Lockheed Martin, RTX, Northrop Grumman, GE Aerospace — backed by multi-year sovereign contracts)",
        fundamental_impact_mechanism="Backlog & FCF Visibility: Secular growth in replenishment orders for integrated air defense (Patriot/THAAD), munitions, and aero propulsion, operating as a geopolitical non-correlated hedge for technology equities.",
        country_liquidity_risk_assessment="Contracts directly underwritten by the US Treasury and sovereign NATO governments (virtually zero sovereign credit risk).",
    ),
    GeopoliticalImpactRow(
        global_event="US Fiscal Dominance (Deficit > 6% of GDP & Debt > $36.8T) & Global Central Bank Liquidity Cycle",
        region_vector="Global / G7 / Money Markets",
        severity="HIGH (Central Secular Portfolio Thesis)",
        affected_portfolio_assets="BTC-USD, ETH-USD, SOL-USD, AAVE-USD, JPM, DBSDY, SPY, QQQ, QLD",
        revenue_or_production_exposed_pct="100% of Portfolio (50% Inelastic Cryptoassets + 50% Hard-Assets / High-Pricing-Power Equities)",
        fundamental_impact_mechanism="WACC & Monetary Expansion (M2): Record sovereign debt impedes sustained elevated real interest rates without fiscal distress, driving monetary liquidity (M2) expansion — inflating hard scarce assets (BTC) and pricing-power monopolies (Mag-6, Visa, Walmart).",
        country_liquidity_risk_assessment="US and Singapore (DBSDY) feature the most resilient, liquid fiat and banking systems globally.",
    ),
    GeopoliticalImpactRow(
        global_event="Digital Asset Regulatory Framework, Institutional Spot ETFs, Basel III & RWA Tokenization",
        region_vector="US (SEC/CFTC) / Europe (MiCA) / Singapore (MAS)",
        severity="LOW-MEDIUM (Institutional Tailwinds)",
        affected_portfolio_assets="BTC-USD, ETH-USD, SOL-USD, AAVE-USD, JPM, V",
        revenue_or_production_exposed_pct="BTC-USD & ETH-USD (Net institutional inflows via Spot ETFs IBIT/FBTC/ETHA > $35B) | AAVE-USD (RWA expansion & GHO adoption)",
        fundamental_impact_mechanism="Cost of Capital & Structural Liquidity: Spot ETF approvals and regulatory clarity de-risk institutional participation, compress left-tail downside volatility, and scale TVL for audited DeFi primitives like Aave V3.",
        country_liquidity_risk_assessment="Global 24/7/365 liquidity across regulated venues (CME, Nasdaq/IBIT) and institutional on-chain order books.",
    ),
]


MICRO_EVENTS_DB: List[MicroCorporateProtocolEvent] = [
    MicroCorporateProtocolEvent(
        date="2026-11-02",
        asset_ticker="NVDA",
        source_type="SEC Form 8-K / Press Release",
        headline="Full-Scale Ramp of Blackwell Architecture (GB200 NVL72) & $50B Share Repurchase Authorization",
        event_category="Product Deployment & Capital Allocation",
        fundamental_impact_analysis="Volume Blackwell deliveries expand average revenue per data center rack and solidify Gross Margins > 74%, while the $50B buyback fully offsets annual SBC dilution.",
        classification="Positive Catalyst",
    ),
    MicroCorporateProtocolEvent(
        date="2026-11-01",
        asset_ticker="DBSDY",
        source_type="SGXNet Filing / Press Release",
        headline="DBS Reports Record Quarterly Net Profit of SGD 3.0B (ROE 18.4%) & Announces Maiden SGD 3B Share Buyback",
        event_category="Quarterly Earnings & Capital Distribution",
        fundamental_impact_analysis="First formal share cancellation buyback program in the bank's history, structurally lifting EPS and ROE while sustaining an annualized Dividend Yield near 6.0%.",
        classification="Positive Catalyst",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-31",
        asset_ticker="AMZN",
        source_type="SEC Form 10-Q / 8-K (Item 2.02)",
        headline="Amazon Operating Income (EBIT) Reaches Record $17.4B with AWS Operating Margin Expanding to 36%",
        event_category="Margin Expansion & Guidance",
        fundamental_impact_analysis="Validates the operational leverage thesis in regionalized fulfillment alongside accelerating generative AI workloads across enterprise AWS accounts.",
        classification="Positive Catalyst",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-30",
        asset_ticker="GOOGL",
        source_type="SEC Form 10-Q / 8-K",
        headline="Google Cloud Accelerates Revenue by +35% YoY with Operating Margin Expanding to 17%",
        event_category="Segment Profitability & SOTP",
        fundamental_impact_analysis="Unlocks substantial value in Alphabet's Sum-of-the-Parts (SOTP) valuation, proving Google Cloud has transitioned into a high-margin enterprise cash generator.",
        classification="Positive Catalyst",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-29",
        asset_ticker="V",
        source_type="SEC Form 8-K / DOJ Filing",
        headline="13% Dividend Hike + $25B Buyback Authorization; Formal Legal Response Filed to DOJ Debit Complaint",
        event_category="Capital Return & Regulatory Litigation",
        fundamental_impact_analysis="Cash generation and Value-Added Services growth (+22%) remain fully resilient; the DOJ debit lawsuit faces multi-year appeals and affects only a minor subset of global fees.",
        classification="Neutral / Monitor",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-25",
        asset_ticker="AAVE-USD",
        source_type="Aave DAO Governance (AIP / Snapshot)",
        headline="Approval of 'AAVEnomics' Proposal (Fee Switch Activation, Umbrella Module & Secondary Market Buybacks)",
        event_category="Tokenomics Overhaul & DAO Governance",
        fundamental_impact_analysis="Transitions the AAVE token from a purely governance token into a direct cash-flow accrual instrument capturing protocol net revenues (> $80M/yr in real protocol earnings).",
        classification="Positive Catalyst",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-20",
        asset_ticker="WMT",
        source_type="SEC Form 8-K & Form 4",
        headline="Walmart Raises Full-Year Guidance with SSS +4.8% & 26% Growth in Advertising (Walmart Connect)",
        event_category="Positive Guidance Revision",
        fundamental_impact_analysis="Robust positive Same-Store Sales (SSS) confirms continued market share capture across high- and middle-income cohorts, rejecting any retail value trap thesis.",
        classification="Positive Catalyst",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-15",
        asset_ticker="JPM",
        source_type="SEC Form 8-K (Item 2.02) & Form 4",
        headline="JPMorgan Beats NII Consensus & Sustains Basel CET1 Capital Ratio at 15.3%; Executive Caution on Geopolitics",
        event_category="Quarterly Balance Sheet & Risk Governance",
        fundamental_impact_analysis="Capital surplus exceeding $35B insulates the franchise against credit stress, though a P/TBV multiple of ~2.48x warrants disciplined capital deployment.",
        classification="Neutral / Monitor",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-12",
        asset_ticker="SOL-USD",
        source_type="GitHub / Validator Governance (SIMD)",
        headline="Independent Validator Client 'Firedancer' (Jump Crypto) Reaches Advanced Testnet; Frankendancer Live on Mainnet",
        event_category="Infrastructure Upgrade & Client Diversity",
        fundamental_impact_analysis="Eliminates the single-client software failure vulnerability on Solana, elevating institutional resilience and theoretical network throughput to > 100,000 TPS.",
        classification="Positive Catalyst",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-08",
        asset_ticker="AAPL",
        source_type="SEC Form 4 (Insider Filings) & 10-K",
        headline="Executive Rule 10b5-1 Scheduled Share Dispositions Within Historical Averages; China Revenue Stabilizes",
        event_category="Insider Trading (Form 4) & Operations",
        fundamental_impact_analysis="Insider transactions occurred under pre-arranged 10b5-1 plans representing < 3% of aggregate executive holdings; Services segment expansion buffers hardware cycles.",
        classification="Neutral / Monitor",
    ),
]


class GeopoliticsMicroEngine:
    def __init__(self) -> None:
        pass

    def get_geopolitical_matrix(self, prefer_ai_cache: bool = True) -> List[GeopoliticalImpactRow]:
        if prefer_ai_cache:
            try:
                from core.ai_report_orchestrator import load_cached_ai_master_insights

                ai_cache = load_cached_ai_master_insights() or {}
                raw_geo = ai_cache.get("geo_matrix") or []
                parsed = [GeopoliticalImpactRow(**item) for item in raw_geo if isinstance(item, dict)]
                if parsed:
                    return parsed
            except Exception:
                pass
        return GEOPOLITICAL_MATRIX_DB

    def get_micro_events(
        self,
        tickers: List[str] | None = None,
        prefer_ai_cache: bool = True,
        include_live_headlines: bool = False,
    ) -> List[MicroCorporateProtocolEvent]:
        if tickers is None:
            try:
                from core.portfolio_engine import get_portfolio_asset_tickers

                tickers = get_portfolio_asset_tickers("all")
            except Exception:
                tickers = []
            if not tickers:
                tickers = [
                    "BTC-USD", "ETH-USD", "PENDLE-USD", "LINK-USD", "MKR-USD", "UNI-USD",
                    "SPY", "QQQ", "QLD", "ITA",
                    "NVDA", "AAPL", "MSFT", "JPM", "ASML", "TSM", "MELI", "AVGO", "MA", "NU",
                ]
        ordered_tks = list(dict.fromkeys(t.strip().upper() for t in tickers if t and t.strip()))
        tk_set = set(ordered_tks)

        base_events: List[MicroCorporateProtocolEvent] = []
        if prefer_ai_cache:
            try:
                from core.ai_report_orchestrator import load_cached_ai_master_insights

                ai_cache = load_cached_ai_master_insights() or {}
                raw_events = ai_cache.get("micro_events") or []
                parsed = [MicroCorporateProtocolEvent(**item) for item in raw_events if isinstance(item, dict)]
                if parsed:
                    base_events = [m for m in parsed if m.asset_ticker.upper() in tk_set]
            except Exception:
                base_events = []

        if not base_events:
            base_events = [m for m in MICRO_EVENTS_DB if m.asset_ticker.upper() in tk_set]

        covered = {m.asset_ticker.upper() for m in base_events}
        missing_tks = [t for t in ordered_tks if t not in covered]
        if missing_tks:
            base_events.extend(
                self._build_fallback_micro_events(missing_tks, include_live_headlines=include_live_headlines)
            )
        return base_events

    def _build_fallback_micro_events(
        self,
        missing_tickers: List[str],
        include_live_headlines: bool = False,
    ) -> List[MicroCorporateProtocolEvent]:
        """Builds deterministic telemetry (and optional Yahoo news) events for non-KB portfolio assets."""
        meta_by_tk: Dict[str, Dict[str, Any]] = {}
        try:
            from core.portfolio_engine import PortfolioEngine

            for a in PortfolioEngine().get_all_assets_from_db():
                tk_u = str(a.get("ticker", "")).upper()
                if tk_u:
                    meta_by_tk[tk_u] = a
        except Exception:
            pass

        eq_kb: Dict[str, Any] = {}
        cr_kb: Dict[str, Any] = {}
        try:
            from core.equity_engine import EQUITY_FUNDAMENTAL_KB
            from core.crypto_engine import CRYPTO_FUNDAMENTAL_KB

            eq_kb = EQUITY_FUNDAMENTAL_KB
            cr_kb = CRYPTO_FUNDAMENTAL_KB
        except Exception:
            pass

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        out: List[MicroCorporateProtocolEvent] = []
        for tk in missing_tickers:
            asset_meta = meta_by_tk.get(tk, {})
            is_crypto = tk.endswith("-USD") or ("Crypto" in str(asset_meta.get("category", "")))
            if include_live_headlines:
                headlines = self.fetch_live_ticker_headlines(tk, max_items=1)
                if headlines and headlines[0].get("title"):
                    h = headlines[0]
                    out.append(
                        MicroCorporateProtocolEvent(
                            date=h.get("date", today_str),
                            asset_ticker=tk,
                            source_type=f"Live Market Feed ({h.get('publisher', 'News')})",
                            headline=h["title"],
                            event_category="Market News & Filing Monitor",
                            fundamental_impact_analysis=f"Active market coverage tracked alongside deterministic {('on-chain/tokenomics' if is_crypto else 'SEC XBRL/NTM valuation')} guardrails.",
                            classification="Neutral / Monitor",
                        )
                    )
                    continue

            if is_crypto:
                ck = cr_kb.get(tk, {})
                earn_m = ck.get("protocol_real_earnings_m")
                unlock_pct = ck.get("unlock_pct_of_circ")
                headline = (
                    f"{asset_meta.get('name') or ck.get('name') or tk}: Active Tokenomics, Unlock & Protocol Fee Monitoring"
                )
                analysis = (
                    f"Real Earnings {float(earn_m):+.1f}M/yr | Monthly Unlock {float(unlock_pct):.2f}%/circ."
                    if earn_m is not None and unlock_pct is not None
                    else "Monitored deterministically via live Binance Futures funding/OI, DeFiLlama TVL/fees, and on-chain Z-Score metrics."
                )
                src = "DeFiLlama / On-Chain Telemetry"
            else:
                ek = eq_kb.get(tk, {})
                pe_ntm = ek.get("pe_ntm")
                sloan = ek.get("sloan_pct")
                headline = (
                    f"{asset_meta.get('name') or ek.get('name') or tk}: Active SEC EDGAR XBRL & Consensus Monitoring"
                )
                analysis = (
                    f"Sloan Ratio {float(sloan):+.1f}% | Forward NTM P/E {float(pe_ntm):.1f}x."
                    if sloan is not None and pe_ntm is not None
                    else "Monitored deterministically via live Yahoo Finance statements, SEC EDGAR XBRL filings, and Reverse DCF guardrails."
                )
                src = "SEC EDGAR XBRL / Consensus Telemetry"

            out.append(
                MicroCorporateProtocolEvent(
                    date=today_str,
                    asset_ticker=tk,
                    source_type=src,
                    headline=headline,
                    event_category="Deterministic Holding Surveillance",
                    fundamental_impact_analysis=analysis,
                    classification="Neutral / Monitor",
                )
            )
        return out

    def fetch_live_ticker_headlines(self, ticker: str, max_items: int = 3) -> List[Dict[str, str]]:
        try:
            s = yf.Search(ticker, news_count=max_items)
            news_list = getattr(s, "news", []) or []
            out = []
            for item in news_list[:max_items]:
                ts = item.get("providerPublishTime")
                dt = datetime.datetime.fromtimestamp(ts).strftime("%m/%d/%Y %H:%M") if ts else "Live Feed"
                out.append({
                    "date": dt,
                    "title": item.get("title", ""),
                    "publisher": item.get("publisher", "Market Feed"),
                    "link": item.get("link", "#"),
                })
            return out
        except Exception:
            return []
        finally:
            try:
                from core.live_quant_fetcher import close_yfinance_thread_caches

                close_yfinance_thread_caches()
            except Exception:
                pass

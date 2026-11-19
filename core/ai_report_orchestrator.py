"""
================================================================================
AI MASTER REPORT ORCHESTRATOR — FULL-PORTFOLIO QUALITATIVE INTELLIGENCE LAYER
================================================================================
Synthesizes ALL qualitative insights, matrices, corporate/crypto signals, and
micro/geopolitical intelligence across the 7-section 360° Master Report via
batched `google-genai` Interactions API Structured Outputs (`store=False`), while
preserving 100% deterministic Python math for every quantitative calculation.

Dual Persistent Caching Architecture:
1. `data_cache/custom_filings_cache.json` (7-day TTL, per-asset SEC/Crypto dossiers)
2. `data_cache/ai_master_insights_cache.json` (24-hour TTL, keyed by portfolio_sig)

Gracefully falls back to deterministic/static baselines per-section if
`GEMINI_API_KEY` is absent or any transient API error occurs.
================================================================================
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
import json
import logging
import os
import tempfile
import threading
import time
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

from core.filings_engine import (
    CryptoDocumentaryDossier,
    EquityDocumentaryDossier,
    FilingsEngine,
)
from core.gemini_client import (
    ROOT_DIR,
    _generate_structured_with_model,
    generate_pdf_executive_synthesis,
    is_gemini_configured,
)
from core.geopolitics_micro_engine import (
    GeopoliticalImpactRow,
    GeopoliticsMicroEngine,
    MicroCorporateProtocolEvent,
)
from core.intelligence_reports_engine import (
    CorporateSignalAndMADossier,
    CryptoInternalDevAndUpgradeDossier,
    DeFiMacroCycleIndicatorRow,
    DeFiNarrativeRow,
    HardAssetMacroSensitivityRow,
    IndustryTechDisruptionRow,
    IntelligenceReportsEngine,
)

logger = logging.getLogger(__name__)

AI_MASTER_INSIGHTS_CACHE_PATH = os.path.join(
    ROOT_DIR, "data_cache", "ai_master_insights_cache.json"
)
_ORCH_CACHE_LOCK = threading.Lock()
DEFAULT_INSIGHTS_TTL_HOURS = 24.0
DEFAULT_FILINGS_TTL_DAYS = 7.0

_COMMON_GROUNDING_RULES = (
    "IRONCLAD INSTITUTIONAL RULES:\n"
    "1. Write exclusively in crisp, concise institutional English suitable for dense A4 landscape PDF tables.\n"
    "2. Cite ONLY exact numbers, percentages, prices, and ratios present in the provided JSON payload, SEC/protocol filings, or fetched headlines — NEVER invent, extrapolate, or estimate missing metrics.\n"
    "3. NEVER compute or reference Altman Z-Score.\n"
    "4. Banking calibration (FINANCIAL_BANK: JPM, NU, DBSDY): use P/TBV vs. ROE, Financial PEGY, Basel CET1/LCR, and P/B >= 1.0x veto; never reference EV/EBITDA or CFO/EBITDA for banks.\n"
    "5. All strategic takeaways are strictly consultative / non-binding (never automated trading).\n"
    "6. Keep every table cell focused and concise (1–2 crisp sentences, ~140–240 chars) to prevent PDF clipping."
)


# ==============================================================================
# PYDANTIC STRUCTURED OUTPUT SCHEMAS (1-TO-1 MATCH WITH REPORT DATACLASSES)
# ==============================================================================


class GeopoliticalImpactItemSchema(BaseModel):
    global_event: str = Field(description="Concise name of current geopolitical or macro-trade vector.")
    region_vector: str = Field(description="Geographic vector, e.g., US <-> China, Middle East, Taiwan Strait.")
    severity: str = Field(description="Severity tag: HIGH, MEDIUM-HIGH, MEDIUM, or LOW.")
    affected_portfolio_assets: str = Field(description="Comma-separated portfolio tickers directly affected.")
    revenue_or_production_exposed_pct: str = Field(description="Verified supply-chain or revenue exposure summary from filings/payload.")
    fundamental_impact_mechanism: str = Field(description="Transmission channel on gross margin, WACC, CapEx, or moat.")
    country_liquidity_risk_assessment: str = Field(description="Listing jurisdiction liquidity and hedging posture.")


class IndustryDisruptionItemSchema(BaseModel):
    mega_trend: str = Field(description="Structural multi-year technological or economic shift.")
    time_horizon: str = Field(description="Horizon tag, e.g., 2026–2030 (Structural).")
    disruption_mechanism: str = Field(description="How unit economics, capital allocation, or moats are shifting.")
    winners_in_portfolio: str = Field(description="Portfolio tickers positioned as structural beneficiaries.")
    vulnerable_or_hedged_assets: str = Field(description="Portfolio tickers facing transition risks or natural hedges.")
    quantitative_kpi_to_watch: str = Field(description="Key measurable KPIs grounded in payload metrics.")


class MacroGeoAndDisruptionsSchema(BaseModel):
    geopolitical_matrix: List[GeopoliticalImpactItemSchema] = Field(min_length=4, max_length=6)
    industry_tech_disruptions: List[IndustryDisruptionItemSchema] = Field(min_length=4, max_length=6)


class HardAssetMacroSensitivityItemSchema(BaseModel):
    ticker: str = Field(description="Exact uppercase portfolio ticker.")
    company_name: str = Field(description="Company or ETF name.")
    interest_rate_sensitivity: str = Field(description="Sensitivity to US 10Y / policy rates using ROIC vs WACC, debt/cash, or duration.")
    usd_dxy_and_fx_sensitivity: str = Field(description="Exposure to DXY / FX translation grounded in filing disclosures.")
    tariff_and_supply_chain_exposure: str = Field(description="Exposure to trade tariffs, BIS controls, or foundry concentration.")
    energy_and_ai_capex_linkage: str = Field(description="Linkage to AI CapEx, power demand, or automation productivity.")
    net_macro_positioning_verdict: str = Field(description="Concise 6–12 word macro positioning badge/verdict.")


class HardAssetMacroSensitivityBatchSchema(BaseModel):
    rows: List[HardAssetMacroSensitivityItemSchema] = Field(min_length=1)


class DeFiCycleInterpretationSchema(BaseModel):
    indicator_index: int = Field(ge=0, le=3, description="Zero-based index (0..3) matching the input indicator.")
    cycle_phase_signal: str = Field(description="Short phase diagnosis badge/phrase grounded in the live reading.")
    portfolio_tactical_implication: str = Field(description="Consultative tactical implication for the portfolio's crypto sleeves.")


class DeFiNarrativeItemSchema(BaseModel):
    narrative_name: str = Field(description="Core DeFi/Crypto narrative active in the current cycle.")
    cycle_momentum: str = Field(description="One of: Strong Acceleration, Institutional Consolidation, Emerging, Maturation.")
    dune_defillama_evidence: str = Field(description="On-chain TVL, Real Earnings, stablecoin, or protocol telemetry evidence from payload.")
    core_technology_shift: str = Field(description="Architectural shift driving value capture.")
    portfolio_crypto_impact: str = Field(description="Portfolio crypto tickers directly exposed.")
    risk_and_invalidator: str = Field(description="Primary technical, dilution, or regulatory invalidator.")


class DeFiIntelligenceBatchSchema(BaseModel):
    cycle_interpretations: List[DeFiCycleInterpretationSchema] = Field(min_length=4, max_length=4)
    defi_narratives: List[DeFiNarrativeItemSchema] = Field(min_length=4, max_length=6)


class EquityQualitativeItemSchema(BaseModel):
    ticker: str = Field(description="Exact uppercase equity ticker.")
    company_name: str = Field(description="Official company name.")
    # Section 4.2 fields (never overwrite mechanical roic_op_margin_pct / roic_cap_turnover_x)
    sector_particularity_lens: str = Field(description="Sector-calibrated valuation & forensic lens for this business.")
    roic_central_pillar: str = Field(description="Primary driver of ROIC spread (Pricing Power, Capital Turnover, Scale, or NII).")
    moat_classification: str = Field(description="Wide/Narrow moat classification citing concrete durability pillars.")
    porter_5_forces: str = Field(description="Concise synthesis of Porter's 5 Forces & supplier/buyer bargaining power.")
    common_size_peer_comparison: str = Field(description="Common-size margin & capital efficiency standing vs. industry peers.")
    ceo_skin_in_the_game: str = Field(description="Leadership alignment, insider/founder ownership, and SBC discipline.")
    capital_allocation_history: str = Field(description="Track record across R&D, CapEx, buybacks, dividends, and M&A.")
    tag_along_governance: str = Field(description="Shareholder rights, share class governance, and board oversight.")
    # Section 4.3 fields (Corporate Signal vs. Noise & M&A)
    guidance_delta_summary: str = Field(description="Recent guidance trajectory, revenue drivers, and margin outlook.")
    ceo_cfo_internal_commentary: str = Field(description="Key executive commentary from MD&A/calls/recent 8-K filings.")
    qa_analyst_clashes: str = Field(description="Primary institutional debates, Item 1A risks, and sell-side scrutiny.")
    operational_moat_shifts: str = Field(description="Structural competitive shifts in technology, ecosystem, or cost structure.")
    ma_and_strategic_deals: str = Field(description="Material M&A, joint ventures, strategic alliances, or organic CapEx focus.")
    payment_structure_and_dilution: str = Field(description="Deal financing (cash vs stock) and SBC/buyback net dilution balance.")
    goodwill_and_impairment_risk: str = Field(description="Goodwill balance context and impairment cushion vs. FCF.")
    antitrust_and_regulatory_status: str = Field(description="Active antitrust, DOJ/EC, BIS, or regulatory contingencies.")


class EquityQualitativeBatchSchema(BaseModel):
    items: List[EquityQualitativeItemSchema] = Field(min_length=1)


class CryptoDevItemSchema(BaseModel):
    symbol: str = Field(description="Normalized symbol with -USD suffix (e.g., BTC-USD, AAVE-USD).")
    protocol_name: str = Field(description="Official protocol or network name.")
    founder_core_dev_signals: str = Field(description="Core dev commit momentum, active devs, and roadmap signals from payload.")
    upcoming_protocol_upgrades: str = Field(description="Key protocol upgrades, EIPs/SIMDs/AIPs, or scaling milestones.")
    architecture_and_fee_switch_changes: str = Field(description="Fee capture, burn, staking Real Yield, or tokenomics mechanics.")
    unlock_schedule_30_60_90d: str = Field(description="30/60/90-day supply emission / unlock context grounded in payload metrics.")
    whale_and_vc_concentration: str = Field(description="Staking lockups, skin-in-the-game %, and holder/VC distribution notes.")
    active_dao_proposals_impact: str = Field(description="Recent DAO / Snapshot governance activity and economic alignment.")


class CryptoDevBatchSchema(BaseModel):
    items: List[CryptoDevItemSchema] = Field(min_length=1)


class MicroEventItemSchema(BaseModel):
    date: str = Field(description="Event date in YYYY-MM-DD format (or 'Recent' if undated).")
    asset_ticker: str = Field(description="Portfolio asset ticker (e.g., NVDA, BTC-USD).")
    source_type: str = Field(description="Source classification, e.g., Live Market News / SEC 8-K / Protocol Governance.")
    headline: str = Field(description="Concise factual headline grounded in the fetched news or filing summary.")
    event_category: str = Field(description="Category such as Earnings & Guidance, M&A, Regulation, Protocol Upgrade, or Macro.")
    fundamental_impact_analysis: str = Field(description="Concise impact on moat, FCF, WACC, or tokenomics.")
    classification: Literal[
        "Positive Catalyst",
        "Neutral / Monitor",
        "Deterioration Warning / Red Flag",
    ] = Field(description="Strict 3-way event classification.")


class MicroEventsBatchSchema(BaseModel):
    events: List[MicroEventItemSchema] = Field(min_length=6, max_length=14)


# ==============================================================================
# ATOMIC DISK CACHE HELPERS
# ==============================================================================


def _load_insights_cache_unlocked() -> Optional[Dict[str, Any]]:
    if not os.path.exists(AI_MASTER_INSIGHTS_CACHE_PATH):
        return None
    try:
        with open(AI_MASTER_INSIGHTS_CACHE_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return raw if isinstance(raw, dict) else None
    except Exception:
        return None


def load_cached_ai_master_insights() -> Optional[Dict[str, Any]]:
    """Fast thread-safe read of persisted Master AI insights cache (<5ms)."""
    with _ORCH_CACHE_LOCK:
        return _load_insights_cache_unlocked()


def save_ai_master_insights_cache(payload: Dict[str, Any]) -> None:
    with _ORCH_CACHE_LOCK:
        try:
            cache_dir = os.path.dirname(AI_MASTER_INSIGHTS_CACHE_PATH)
            os.makedirs(cache_dir, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(prefix=".ai_master_", suffix=".tmp", dir=cache_dir)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)
                os.replace(tmp_path, AI_MASTER_INSIGHTS_CACHE_PATH)
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
        except Exception as exc:
            logger.warning("Failed to save AI master insights cache: %s", type(exc).__name__)


def clear_ai_master_insights_cache() -> None:
    with _ORCH_CACHE_LOCK:
        try:
            if os.path.exists(AI_MASTER_INSIGHTS_CACHE_PATH):
                os.remove(AI_MASTER_INSIGHTS_CACHE_PATH)
        except OSError:
            pass


# ==============================================================================
# LIVE CONTEXT BUILDERS & ORCHESTRATOR
# ==============================================================================


def _collect_live_portfolio_headlines(tickers: List[str], max_per_ticker: int = 3) -> Dict[str, List[Dict[str, str]]]:
    """Fetches recent live headlines in parallel across active portfolio assets."""
    geo_eng = GeopoliticsMicroEngine()
    clean_tks = [t.strip().upper() for t in dict.fromkeys(tickers) if t and t.strip()]
    out: Dict[str, List[Dict[str, str]]] = {}
    if not clean_tks:
        return out

    def _one(tk: str) -> Tuple[str, List[Dict[str, str]]]:
        try:
            items = geo_eng.fetch_live_ticker_headlines(tk, max_items=max_per_ticker)
            return tk, items or []
        except Exception:
            return tk, []

    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = [pool.submit(_one, tk) for tk in clean_tks]
        for fut in as_completed(futs):
            try:
                tk, items = fut.result()
                if items:
                    out[tk] = items
            except Exception:
                pass
    return out


def _compact_macro_snapshot(macro: Any) -> Dict[str, Any]:
    sp = getattr(macro, "sahm_paired", {}) or {}
    sos = getattr(macro, "sos_indicator", {}) or {}
    yc = getattr(macro, "yield_curve", {}) or {}
    mon = getattr(macro, "monetary_aggregates", {}) or {}
    pmi = getattr(macro, "pmi_analysis", {}) or {}
    return {
        "cycle_phase": getattr(macro, "cycle_phase", ""),
        "sahm_pct": sp.get("sahm_current_pct"),
        "sahm_verdict": sp.get("paired_verdict"),
        "icsa": sp.get("icsa_current"),
        "sos_current": sos.get("sos_current"),
        "pmi_services": pmi.get("pmi_services_current"),
        "pmi_mfg": pmi.get("pmi_manufacturing_current"),
        "us10y_pct": yc.get("us10y_pct"),
        "us2y_pct": yc.get("us2y_pct"),
        "spread_10y_2y_bps": yc.get("spread_10y_2y_bps"),
        "m2_trillions": mon.get("m2_trillions"),
        "dxy": mon.get("dxy_current"),
    }


def _compact_equity_payload(
    eq: Any,
    filing: Optional[EquityDocumentaryDossier],
    headlines: List[Dict[str, str]],
) -> Dict[str, Any]:
    fh = getattr(eq, "forensic_health", {}) or {}
    vm = getattr(eq, "valuation_methods", {}) or {}
    qs = getattr(eq, "qualitative_strategy", {}) or {}
    is_bank = "BANK" in str(getattr(eq, "sector_vertical", "")).upper()

    base: Dict[str, Any] = {
        "ticker": eq.ticker,
        "company_name": eq.company_name,
        "sector_vertical": eq.sector_vertical,
        "sector_label": eq.sector_label,
        "spot_usd": round(float(eq.current_price), 2),
        "market_cap_b": round(float(eq.market_cap_b), 2),
        "roic_goodwill_pct": fh.get("roic_goodwill_pct"),
        "wacc_pct": fh.get("wacc_pct"),
        "roic_op_margin_pct": qs.get("roic_op_margin_pct"),
        "roic_cap_turnover_x": qs.get("roic_cap_turnover_x"),
        "rd_to_sales_pct": qs.get("rd_to_sales_pct"),
        "gross_margin_current_pct": qs.get("gross_margin_current_pct"),
        "gross_margin_5y_delta_pp": qs.get("gross_margin_5y_delta_pp"),
        "g_impl_pct": vm.get("reverse_dcf_g_impl_pct"),
        "g_fund_pct": vm.get("g_fund_projected_pct"),
        "pegy": vm.get("primary_pegy_label"),
        "sotp_usd": vm.get("sotp_fair_price_usd"),
    }
    if is_bank:
        base["ptbv_current"] = vm.get("ptbv_current")
        base["pb_current"] = vm.get("pb_current")
        base["roe_pct"] = fh.get("roe_dupont_pct")
    else:
        base["sloan_ratio_pct"] = fh.get("sloan_ratio_pct")
        base["cfo_to_ebitda"] = fh.get("fco_to_ebitda")
        base["debt_to_ebitda"] = fh.get("debt_to_ebitda")
        base["interest_coverage_x"] = fh.get("interest_coverage_x")

    if filing is not None:
        base["filing_summary"] = {
            "annual_form": filing.filing_form_annual,
            "quarterly_form": filing.filing_form_quarterly,
            "auditor": f"{filing.auditor_firm} | {filing.auditor_opinion}",
            "sox_404b": filing.sox_404b_controls,
            "mda_growth": filing.mda_growth_decomposition,
            "mda_margins": filing.mda_segment_profitability,
            "mda_backlog_rpo": filing.mda_backlog_rpo,
            "mda_capex": filing.mda_capex_plan,
            "risks_1a": filing.item_1a_specific_risks,
            "litigation": filing.footnote_contingencies_litigation,
            "sbc": filing.footnote_sbc_impact,
            "debt": filing.footnote_debt_maturity_schedule,
            "ma_deals": getattr(filing, "ma_and_strategic_deals", ""),
            "ma_goodwill": getattr(filing, "ma_payment_and_goodwill", ""),
            "analyst_target_usd": filing.analyst_target_mean_usd,
            "analyst_dist": filing.analyst_recommendations_dist,
            "eps_revisions": filing.analyst_eps_revisions_30d_90d,
        }
    if headlines:
        base["recent_headlines"] = [f"[{h.get('date', '')}] {h.get('title', '')}" for h in headlines[:3]]
    return base


def _compact_crypto_payload(
    sym: str,
    cp: Any,
    filing: Optional[CryptoDocumentaryDossier],
    headlines: List[Dict[str, str]],
) -> Dict[str, Any]:
    om = getattr(cp, "onchain_metrics", {}) or {}
    tv = getattr(cp, "tokenomics_valuation", {}) or {}
    ss = getattr(cp, "supply_structure", {}) or {}
    base: Dict[str, Any] = {
        "symbol": sym,
        "name": cp.name,
        "spot_usd": round(float(cp.spot_price_usd), 2),
        "circulating_pct": round(float(cp.circulating_pct), 1),
        "mvrv_z": om.get("mvrv_z_score"),
        "nupl": om.get("nupl"),
        "asopr": om.get("asopr"),
        "protocol_real_earnings_m": tv.get("protocol_real_earnings_m"),
        "real_yield_pct": tv.get("real_yield_pct"),
        "tvl_m": tv.get("tvl_m"),
        "unlock_30d_pct": ss.get("unlock_pct_of_circ"),
        "post_unlock_price_usd": ss.get("theoretical_post_unlock_price_usd"),
    }
    if filing is not None:
        base["protocol_dossier"] = {
            "whitepaper": filing.wp_title_author,
            "value_prop": filing.wp_value_proposition,
            "consensus": filing.wp_consensus_architecture,
            "value_accrual": filing.wp_value_accrual_mechanism,
            "github_repos": filing.github_core_repos,
            "github_commits_4w": filing.github_commits_4w,
            "github_active_devs": filing.github_active_devs_monthly,
            "governance": filing.deepdao_status,
            "proposals": filing.recent_governance_proposals,
            "locked_pct": filing.skin_in_the_game_locked_pct,
            "lock_details": filing.skin_in_the_game_details,
            "token_sniffer": filing.token_sniffer_score,
            "audits": filing.audit_firms,
            "exploits": filing.exploit_history,
        }
    if headlines:
        base["recent_headlines"] = [f"[{h.get('date', '')}] {h.get('title', '')}" for h in headlines[:3]]
    return base


class AIReportOrchestrator:
    """Orchestrates full-portfolio AI filing hydration + batched narrative/matrix generation."""

    def __init__(self) -> None:
        self.filings_engine = FilingsEngine()
        self.intel_engine = IntelligenceReportsEngine()
        self.geo_engine = GeopoliticsMicroEngine()

    def _hydrate_defi_cycle_rows(
        self,
        cryptos: Dict[str, Any],
        ai_interps: List[Dict[str, Any]],
    ) -> List[DeFiMacroCycleIndicatorRow]:
        """Always computes exact mechanical readings in Python; overlays ONLY AI narrative columns."""
        base_rows = self.intel_engine.build_defi_cycle_indicators(cryptos)
        by_idx = {
            int(item["indicator_index"]): item
            for item in (ai_interps or [])
            if isinstance(item, dict) and "indicator_index" in item
        }
        out: List[DeFiMacroCycleIndicatorRow] = []
        for idx, row in enumerate(base_rows):
            ov = by_idx.get(idx)
            if ov:
                out.append(
                    DeFiMacroCycleIndicatorRow(
                        indicator_name=row.indicator_name,
                        current_reading=row.current_reading,
                        historical_band_ref=row.historical_band_ref,
                        cycle_phase_signal=str(ov.get("cycle_phase_signal") or row.cycle_phase_signal),
                        portfolio_tactical_implication=str(
                            ov.get("portfolio_tactical_implication") or row.portfolio_tactical_implication
                        ),
                    )
                )
            else:
                out.append(row)
        return out

    def _deserialize_bundle(
        self,
        raw_cache: Dict[str, Any],
        equities: List[Any],
        cryptos: Dict[str, Any],
        eq_filings: List[EquityDocumentaryDossier],
        cr_filings: List[CryptoDocumentaryDossier],
        filings_hydration: Dict[str, Any],
        from_cache: bool,
    ) -> Dict[str, Any]:
        geo_matrix = [
            GeopoliticalImpactRow(**item)
            for item in (raw_cache.get("geo_matrix") or [])
            if isinstance(item, dict)
        ] or self.geo_engine.get_geopolitical_matrix(prefer_ai_cache=False)

        disruptions = [
            IndustryTechDisruptionRow(**item)
            for item in (raw_cache.get("disruptions") or [])
            if isinstance(item, dict)
        ] or self.intel_engine.get_industry_tech_disruptions()

        macro_sensitivity = [
            HardAssetMacroSensitivityRow(**item)
            for item in (raw_cache.get("macro_sensitivity") or [])
            if isinstance(item, dict)
        ]

        defi_cycle_rows = self._hydrate_defi_cycle_rows(
            cryptos=cryptos,
            ai_interps=raw_cache.get("defi_cycle_interpretations") or [],
        )

        defi_narratives = [
            DeFiNarrativeRow(**item)
            for item in (raw_cache.get("defi_narratives") or [])
            if isinstance(item, dict)
        ] or self.intel_engine.get_defi_narratives()

        eq_qual_overrides: Dict[str, Dict[str, str]] = {
            str(k).upper(): dict(v)
            for k, v in (raw_cache.get("equity_qualitative_overrides") or {}).items()
            if isinstance(v, dict)
        }

        corporate_signal_ma: Dict[str, CorporateSignalAndMADossier] = {}
        for k, v in (raw_cache.get("corporate_signal_ma") or {}).items():
            if isinstance(v, dict):
                try:
                    corporate_signal_ma[str(k).upper()] = CorporateSignalAndMADossier(**v)
                except Exception:
                    pass

        crypto_dev_dossiers: Dict[str, CryptoInternalDevAndUpgradeDossier] = {}
        for k, v in (raw_cache.get("crypto_dev_dossiers") or {}).items():
            if isinstance(v, dict):
                try:
                    crypto_dev_dossiers[str(k).upper()] = CryptoInternalDevAndUpgradeDossier(**v)
                except Exception:
                    pass

        micro_events = [
            MicroCorporateProtocolEvent(**item)
            for item in (raw_cache.get("micro_events") or [])
            if isinstance(item, dict)
        ] or self.geo_engine.get_micro_events(prefer_ai_cache=False)

        return {
            "enabled": True,
            "generated_at": float(raw_cache.get("generated_at") or time.time()),
            "portfolio_sig": str(raw_cache.get("portfolio_sig") or ""),
            "models_used": list(raw_cache.get("models_used") or []),
            "from_cache": from_cache,
            "section_status": dict(raw_cache.get("section_status") or {}),
            "filings_hydration": filings_hydration,
            "eq_filings": eq_filings,
            "cr_filings": cr_filings,
            "geo_matrix": geo_matrix,
            "micro_events": micro_events,
            "executive_summary": raw_cache.get("executive_summary"),
            "disruptions": disruptions,
            "macro_sensitivity": macro_sensitivity,
            "defi_cycle_rows": defi_cycle_rows,
            "defi_narratives": defi_narratives,
            "equity_qualitative_overrides": eq_qual_overrides,
            "corporate_signal_ma": corporate_signal_ma,
            "crypto_dev_dossiers": crypto_dev_dossiers,
        }

    def build_complete_ai_master_bundle(
        self,
        macro: Any,
        portfolio: Any,
        equities: List[Any],
        cryptos: Dict[str, Any],
        risk_timing: Any,
        portfolio_sig: str,
        force_refresh_insights: bool = False,
        force_refresh_filings: bool = False,
        insights_ttl_hours: float = DEFAULT_INSIGHTS_TTL_HOURS,
        filings_ttl_days: float = DEFAULT_FILINGS_TTL_DAYS,
        progress_cb: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        Ensures every active portfolio asset has an AI-hydrated documentary dossier
        and synthesizes all qualitative matrices/insights across Sections 1, 3, 4 & 5.
        """
        def _notify(msg: str, pct: float) -> None:
            if progress_cb is not None:
                try:
                    progress_cb(msg, max(0.0, min(1.0, float(pct))))
                except Exception:
                    pass

        if not is_gemini_configured():
            return {"enabled": False, "error": "GEMINI_API_KEY not configured"}

        equity_tickers = [e.ticker.strip().upper() for e in equities if getattr(e, "ticker", "")]
        crypto_symbols = [sym.strip().upper() for sym in cryptos.keys() if sym]

        # ----------------------------------------------------------------------
        # STAGE 1: AUTOMATIC FULL-PORTFOLIO FILING HYDRATION (CUSTOM CACHE 7D TTL)
        # ----------------------------------------------------------------------
        cov = self.filings_engine.get_ai_dossier_coverage(
            equity_tickers=equity_tickers,
            crypto_symbols=crypto_symbols,
            ttl_days=filings_ttl_days,
        )
        need_hydration = force_refresh_filings or bool(cov["stale_equities"] or cov["stale_cryptos"])
        if need_hydration:
            stale_n = len(equity_tickers) + len(crypto_symbols) if force_refresh_filings else (
                len(cov["stale_equities"]) + len(cov["stale_cryptos"])
            )
            _notify(f"Hydrating {stale_n} portfolio SEC & Crypto protocol dossiers via Gemini...", 0.05)

            def _fil_cb(sym: str, done_idx: int, tot: int) -> None:
                frac = 0.05 + 0.30 * (done_idx / max(tot, 1))
                _notify(f"Extracted dossier {done_idx}/{tot}: {sym}", frac)

            filings_hydration = self.filings_engine.hydrate_portfolio_dossiers_ai(
                equity_tickers=equity_tickers,
                crypto_symbols=crypto_symbols,
                force_refresh=force_refresh_filings,
                ttl_days=filings_ttl_days,
                max_workers=2,
                progress_cb=_fil_cb,
            )
        else:
            filings_hydration = {
                "hydrated_equities": [],
                "hydrated_cryptos": [],
                "failed": {},
                "total_ai_equities": cov["ai_equity_count"],
                "total_ai_cryptos": cov["ai_crypto_count"],
                "from_cache": True,
            }
            _notify(
                f"Loaded {cov['ai_equity_count']} Equity + {cov['ai_crypto_count']} Crypto AI dossiers from cache.",
                0.35,
            )

        eq_filings = self.filings_engine.get_equity_dossiers(equity_tickers)
        cr_filings = self.filings_engine.get_crypto_dossiers(crypto_symbols)
        eq_filing_map = {d.ticker.upper(): d for d in eq_filings}
        cr_filing_map = {c.symbol.upper(): c for c in cr_filings}

        # ----------------------------------------------------------------------
        # CACHE CHECK FOR NARRATIVE MATRICES (24H TTL, PORTFOLIO-SIGNATURE SCOPED)
        # ----------------------------------------------------------------------
        now = time.time()
        ttl_sec = max(300.0, float(insights_ttl_hours) * 3600.0)
        cached = load_cached_ai_master_insights()
        required_keys = (
            "geo_matrix",
            "disruptions",
            "macro_sensitivity",
            "defi_cycle_interpretations",
            "defi_narratives",
            "equity_qualitative_overrides",
            "corporate_signal_ma",
            "crypto_dev_dossiers",
            "micro_events",
            "executive_summary",
        )
        if (
            not force_refresh_insights
            and isinstance(cached, dict)
            and cached.get("portfolio_sig") == portfolio_sig
            and (now - float(cached.get("generated_at") or 0.0)) < ttl_sec
            and all(bool(cached.get(k)) for k in required_keys)
        ):
            _notify("Loaded all Master AI insights & matrices from local 24h cache.", 1.0)
            return self._deserialize_bundle(
                raw_cache=cached,
                equities=equities,
                cryptos=cryptos,
                eq_filings=eq_filings,
                cr_filings=cr_filings,
                filings_hydration=filings_hydration,
                from_cache=True,
            )

        # ----------------------------------------------------------------------
        # STAGE 2: COLLECT LIVE NEWS HEADLINES + MACRO/DEFI TELEMETRY
        # ----------------------------------------------------------------------
        _notify("Fetching live headlines & DeFiLlama telemetry across portfolio...", 0.38)
        all_tickers = [p.ticker for p in getattr(portfolio, "positions", [])] or (equity_tickers + crypto_symbols)
        headlines_by_tk = _collect_live_portfolio_headlines(all_tickers, max_per_ticker=3)
        macro_snap = _compact_macro_snapshot(macro)
        llama_stats = self.intel_engine.fetch_live_defillama_macro_stats()
        models_used: List[str] = []
        section_status: Dict[str, str] = {}

        def _record_model(m: Optional[str]) -> None:
            if m and m not in models_used:
                models_used.append(m)

        # Preserve prior cached sections if an individual stage hits a transient error
        prev_cache = cached if (isinstance(cached, dict) and cached.get("portfolio_sig") == portfolio_sig and not force_refresh_insights) else {}
        out_cache: Dict[str, Any] = {
            "generated_at": now,
            "portfolio_sig": portfolio_sig,
            "models_used": models_used,
            "section_status": section_status,
            "geo_matrix": prev_cache.get("geo_matrix", []),
            "disruptions": prev_cache.get("disruptions", []),
            "macro_sensitivity": prev_cache.get("macro_sensitivity", []),
            "defi_cycle_interpretations": prev_cache.get("defi_cycle_interpretations", []),
            "defi_narratives": prev_cache.get("defi_narratives", []),
            "equity_qualitative_overrides": prev_cache.get("equity_qualitative_overrides", {}),
            "corporate_signal_ma": prev_cache.get("corporate_signal_ma", {}),
            "crypto_dev_dossiers": prev_cache.get("crypto_dev_dossiers", {}),
            "micro_events": prev_cache.get("micro_events", []),
            "executive_summary": prev_cache.get("executive_summary"),
        }

        non_crypto_positions = [
            {
                "ticker": p.ticker,
                "name": p.name,
                "category": p.category,
                "sector_vertical": p.sector_vertical,
                "target_weight_pct": round(float(p.target_weight_pct), 2),
                "current_weight_pct": round(float(p.current_weight_pct), 2),
            }
            for p in getattr(portfolio, "positions", [])
            if not any(k in str(p.category) for k in ("Crypto", "Altcoin", "Cripto"))
        ]
        eq_by_tk = {e.ticker.upper(): e for e in equities}
        for pos in non_crypto_positions:
            eq_obj = eq_by_tk.get(pos["ticker"].upper())
            if eq_obj is not None:
                fh = eq_obj.forensic_health or {}
                pos["roic_pct"] = fh.get("roic_goodwill_pct")
                pos["wacc_pct"] = fh.get("wacc_pct")
                pos["debt_to_ebitda"] = fh.get("debt_to_ebitda")
            dos = eq_filing_map.get(pos["ticker"].upper())
            if dos is not None:
                pos["risks_1a"] = dos.item_1a_specific_risks[:240]
                pos["mda_growth"] = dos.mda_growth_decomposition[:180]

        # ----------------------------------------------------------------------
        # STAGE 3A: GEOPOLITICAL MATRIX & INDUSTRY TECH DISRUPTIONS
        # ----------------------------------------------------------------------
        _notify("Synthesizing Section 1: Geopolitical Matrix & Tech Disruptions...", 0.45)
        geo_payload = {
            "macro": macro_snap,
            "portfolio_positions": non_crypto_positions + [
                {"ticker": s, "name": cryptos[s].name, "spot_usd": round(float(cryptos[s].spot_price_usd), 2)}
                for s in crypto_symbols
            ],
            "lookthrough_top": [
                {"ticker": h.ticker, "effective_pct": round(float(h.total_effective_lookthrough_pct), 2)}
                for h in getattr(portfolio, "lookthrough_holdings", [])[:15]
            ],
            "recent_headlines": {k: [x.get("title", "") for x in v[:2]] for k, v in list(headlines_by_tk.items())[:14]},
        }
        geo_res, geo_mdl = _generate_structured_with_model(
            input_payload=(
                "Synthesize the Global Geopolitical Impact Matrix (5-6 vectors) and Industry Tech Disruptions "
                "(5-6 megatrends) strictly tailored to this portfolio and macro snapshot:\n\n"
                + json.dumps(geo_payload, ensure_ascii=False)
            ),
            schema_cls=MacroGeoAndDisruptionsSchema,
            system_instruction=(
                "You are a Senior Macro & Geopolitical Risk Strategist for an Institutional Investment Terminal.\n"
                + _COMMON_GROUNDING_RULES
            ),
            temperature=0.15,
            max_output_tokens=4500,
            timeout_sec=50.0,
        )
        if geo_res is not None:
            _record_model(geo_mdl)
            out_cache["geo_matrix"] = [x.model_dump() for x in geo_res.geopolitical_matrix]
            out_cache["disruptions"] = [x.model_dump() for x in geo_res.industry_tech_disruptions]
            section_status["geo_matrix"] = "AI"
            section_status["disruptions"] = "AI"
        else:
            section_status["geo_matrix"] = "Fallback"
            section_status["disruptions"] = "Fallback"

        # ----------------------------------------------------------------------
        # STAGE 3B: HARD-ASSET MACRO SENSITIVITY MATRIX
        # ----------------------------------------------------------------------
        _notify("Synthesizing Section 1: Hard-Asset Macro Sensitivity Matrix...", 0.54)
        if non_crypto_positions:
            sens_payload = {"macro": macro_snap, "hard_assets": non_crypto_positions}
            sens_res, sens_mdl = _generate_structured_with_model(
                input_payload=(
                    "Generate one HardAssetMacroSensitivityRow for EVERY ticker in `hard_assets` (preserve exact ticker symbols):\n\n"
                    + json.dumps(sens_payload, ensure_ascii=False)
                ),
                schema_cls=HardAssetMacroSensitivityBatchSchema,
                system_instruction=(
                    "You are an Institutional Equity & ETF Macro Sensitivity Analyst.\n"
                    + _COMMON_GROUNDING_RULES
                ),
                temperature=0.15,
                max_output_tokens=5000,
                timeout_sec=55.0,
            )
            if sens_res is not None:
                _record_model(sens_mdl)
                out_cache["macro_sensitivity"] = [r.model_dump() for r in sens_res.rows]
                section_status["macro_sensitivity"] = "AI"
            else:
                section_status["macro_sensitivity"] = "Fallback"

        # ----------------------------------------------------------------------
        # STAGE 4: CRYPTO DEFI CYCLE INTERPRETATIONS & NARRATIVE RADAR (SEC 3)
        # ----------------------------------------------------------------------
        _notify("Synthesizing Section 3: DeFi Cycle Compass & Narrative Radar...", 0.62)
        base_cycle = self.intel_engine.build_defi_cycle_indicators(cryptos)
        defi_payload = {
            "macro": macro_snap,
            "defillama_live": llama_stats,
            "cycle_indicators_deterministic": [
                {
                    "indicator_index": idx,
                    "indicator_name": r.indicator_name,
                    "current_reading": r.current_reading,
                    "historical_band_ref": r.historical_band_ref,
                }
                for idx, r in enumerate(base_cycle)
            ],
            "portfolio_cryptos": [
                _compact_crypto_payload(sym, cryptos[sym], cr_filing_map.get(sym), headlines_by_tk.get(sym, []))
                for sym in crypto_symbols
            ],
        }
        defi_res, defi_mdl = _generate_structured_with_model(
            input_payload=(
                "Interpret all 4 deterministic crypto cycle indicators (indices 0..3) and synthesize 5-6 active "
                "DeFi/Crypto narratives grounded in the live DeFiLlama and on-chain metrics:\n\n"
                + json.dumps(defi_payload, ensure_ascii=False)
            ),
            schema_cls=DeFiIntelligenceBatchSchema,
            system_instruction=(
                "You are a Senior On-Chain & DeFi Macro Strategist.\n"
                + _COMMON_GROUNDING_RULES
            ),
            temperature=0.15,
            max_output_tokens=4500,
            timeout_sec=50.0,
        )
        if defi_res is not None:
            _record_model(defi_mdl)
            out_cache["defi_cycle_interpretations"] = [x.model_dump() for x in defi_res.cycle_interpretations]
            out_cache["defi_narratives"] = [x.model_dump() for x in defi_res.defi_narratives]
            section_status["defi_cycle"] = "AI"
            section_status["defi_narratives"] = "AI"
        else:
            section_status["defi_cycle"] = "Fallback"
            section_status["defi_narratives"] = "Fallback"

        # ----------------------------------------------------------------------
        # STAGE 5: EQUITY MOATS, PORTER'S 5 FORCES, CALLS Q&A & M&A (SEC 4.2/4.3)
        # ----------------------------------------------------------------------
        _notify("Synthesizing Section 4: Corporate Moats, Porter 5 Forces, Calls Q&A & M&A...", 0.72)
        eq_qual_map: Dict[str, Dict[str, str]] = dict(out_cache.get("equity_qualitative_overrides") or {})
        corp_ma_map: Dict[str, Dict[str, Any]] = dict(out_cache.get("corporate_signal_ma") or {})
        eq_chunks = [equities[i : i + 5] for i in range(0, len(equities), 5)]
        eq_ok_chunks = 0
        for chunk_idx, chunk in enumerate(eq_chunks):
            chunk_payload = [
                _compact_equity_payload(e, eq_filing_map.get(e.ticker.upper()), headlines_by_tk.get(e.ticker.upper(), []))
                for e in chunk
            ]
            eq_res, eq_mdl = _generate_structured_with_model(
                input_payload=(
                    "For EVERY company in this batch, synthesize Section 4.2 (Sector Lens, ROIC Pillar, Moats, "
                    "Porter's 5 Forces, Common Size vs Peers, Governance) and Section 4.3 (Earnings Guidance Delta, "
                    "CEO/CFO Commentary, Analyst Debates, M&A/Goodwill/Antitrust), grounded strictly in the provided "
                    "deterministic metrics, SEC filings, and headlines:\n\n"
                    + json.dumps(chunk_payload, ensure_ascii=False)
                ),
                schema_cls=EquityQualitativeBatchSchema,
                system_instruction=(
                    "You are an Institutional Forensic Equity & Competitive Strategy Analyst.\n"
                    + _COMMON_GROUNDING_RULES
                ),
                temperature=0.15,
                max_output_tokens=6000,
                timeout_sec=55.0,
            )
            if eq_res is not None:
                _record_model(eq_mdl)
                eq_ok_chunks += 1
                for item in eq_res.items:
                    tk_u = item.ticker.strip().upper()
                    eq_qual_map[tk_u] = {
                        "sector_particularity_lens": item.sector_particularity_lens,
                        "roic_central_pillar": item.roic_central_pillar,
                        "moat_classification": item.moat_classification,
                        "porter_5_forces": item.porter_5_forces,
                        "common_size_peer_comparison": item.common_size_peer_comparison,
                        "ceo_skin_in_the_game": item.ceo_skin_in_the_game,
                        "capital_allocation_history": item.capital_allocation_history,
                        "tag_along_governance": item.tag_along_governance,
                    }
                    corp_ma_map[tk_u] = {
                        "ticker": tk_u,
                        "company_name": item.company_name,
                        "guidance_delta_summary": item.guidance_delta_summary,
                        "ceo_cfo_internal_commentary": item.ceo_cfo_internal_commentary,
                        "qa_analyst_clashes": item.qa_analyst_clashes,
                        "operational_moat_shifts": item.operational_moat_shifts,
                        "ma_and_strategic_deals": item.ma_and_strategic_deals,
                        "payment_structure_and_dilution": item.payment_structure_and_dilution,
                        "goodwill_and_impairment_risk": item.goodwill_and_impairment_risk,
                        "antitrust_and_regulatory_status": item.antitrust_and_regulatory_status,
                    }
            if chunk_idx + 1 < len(eq_chunks):
                time.sleep(0.3)

        out_cache["equity_qualitative_overrides"] = eq_qual_map
        out_cache["corporate_signal_ma"] = corp_ma_map
        section_status["equity_qualitative"] = "AI" if eq_ok_chunks == len(eq_chunks) and eq_chunks else (
            "Partial AI" if eq_ok_chunks > 0 else "Fallback"
        )

        # ----------------------------------------------------------------------
        # STAGE 6: CRYPTO CORE DEVS, UPGRADES & UNLOCK GOVERNANCE (SEC 5.2)
        # ----------------------------------------------------------------------
        _notify("Synthesizing Section 5: Crypto Core Dev Signals & Governance...", 0.82)
        if crypto_symbols:
            cr_payload = [
                _compact_crypto_payload(sym, cryptos[sym], cr_filing_map.get(sym), headlines_by_tk.get(sym, []))
                for sym in crypto_symbols
            ]
            cr_res, cr_mdl = _generate_structured_with_model(
                input_payload=(
                    "For EVERY cryptoasset in this payload, synthesize Core Dev signals, Protocol Upgrades, "
                    "Fee Switch/Value Accrual mechanics, 30/60/90d Unlock context, Whale/VC concentration, and DAO Impact:\n\n"
                    + json.dumps(cr_payload, ensure_ascii=False)
                ),
                schema_cls=CryptoDevBatchSchema,
                system_instruction=(
                    "You are a Senior Crypto Protocol Architecture & Tokenomics Analyst.\n"
                    + _COMMON_GROUNDING_RULES
                ),
                temperature=0.15,
                max_output_tokens=4500,
                timeout_sec=50.0,
            )
            if cr_res is not None:
                _record_model(cr_mdl)
                cr_dev_map: Dict[str, Dict[str, Any]] = {}
                for item in cr_res.items:
                    su = item.symbol.strip().upper()
                    if "-" not in su:
                        su = f"{su}-USD"
                    d_item = item.model_dump()
                    d_item["symbol"] = su
                    cr_dev_map[su] = d_item
                out_cache["crypto_dev_dossiers"] = cr_dev_map
                section_status["crypto_dev"] = "AI"
            else:
                section_status["crypto_dev"] = "Fallback"

        # ----------------------------------------------------------------------
        # STAGE 7: MATERIAL MICRO EVENTS ACROSS EQUITIES & CRYPTO (SECS 4.4 / 5.3)
        # ----------------------------------------------------------------------
        _notify("Synthesizing Sections 4.4 & 5.3: Live Material Micro Events...", 0.89)
        micro_payload = {
            "live_headlines_by_ticker": headlines_by_tk,
            "equity_filing_notes": [
                {
                    "ticker": d.ticker,
                    "forms": f"{d.filing_form_annual} / {d.filing_form_quarterly}",
                    "ma": getattr(d, "ma_and_strategic_deals", "")[:180],
                    "eps_rev": d.analyst_eps_revisions_30d_90d[:140],
                }
                for d in eq_filings
            ],
            "crypto_governance_notes": [
                {
                    "symbol": c.symbol,
                    "proposals": c.recent_governance_proposals[:180],
                    "commits_4w": c.github_commits_4w,
                }
                for c in cr_filings
            ],
        }
        micro_res, micro_mdl = _generate_structured_with_model(
            input_payload=(
                "Synthesize 10–14 material Corporate (equity tickers) and Crypto Protocol (SYMBOL-USD) micro events "
                "from the live headlines and filing summaries below, covering both equities and cryptos:\n\n"
                + json.dumps(micro_payload, ensure_ascii=False)
            ),
            schema_cls=MicroEventsBatchSchema,
            system_instruction=(
                "You are an Institutional Corporate Filings & Protocol Governance Event Analyst.\n"
                + _COMMON_GROUNDING_RULES
            ),
            temperature=0.15,
            max_output_tokens=4500,
            timeout_sec=50.0,
        )
        if micro_res is not None:
            _record_model(micro_mdl)
            out_cache["micro_events"] = [ev.model_dump() for ev in micro_res.events]
            section_status["micro_events"] = "AI"
        else:
            section_status["micro_events"] = "Fallback"

        # ----------------------------------------------------------------------
        # STAGE 8: SECTION 1.0 EXECUTIVE AI THESIS & CROSS-ASSET SYNTHESIS
        # ----------------------------------------------------------------------
        _notify("Synthesizing Section 1.0: Executive AI Thesis & Cross-Asset Risk...", 0.95)
        geo_objs = [
            GeopoliticalImpactRow(**item)
            for item in (out_cache.get("geo_matrix") or [])
            if isinstance(item, dict)
        ] or self.geo_engine.get_geopolitical_matrix(prefer_ai_cache=False)

        exec_summary = generate_pdf_executive_synthesis(
            macro=macro,
            portfolio=portfolio,
            equities=equities,
            cryptos=cryptos,
            geo_matrix=geo_objs,
            risk_timing=risk_timing,
        )
        if exec_summary is not None:
            _record_model(exec_summary.get("model_used"))
            out_cache["executive_summary"] = exec_summary
            section_status["executive_summary"] = "AI"
        else:
            section_status["executive_summary"] = "Fallback"

        out_cache["generated_at"] = time.time()
        out_cache["models_used"] = models_used
        out_cache["section_status"] = section_status
        save_ai_master_insights_cache(out_cache)
        _notify("All AI Master Report insights & dossiers ready.", 1.0)

        return self._deserialize_bundle(
            raw_cache=out_cache,
            equities=equities,
            cryptos=cryptos,
            eq_filings=eq_filings,
            cr_filings=cr_filings,
            filings_hydration=filings_hydration,
            from_cache=False,
        )

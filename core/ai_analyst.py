"""
================================================================================
AI PORTFOLIO ANALYST — READ-ONLY GOOGLE ANTIGRAVITY SDK AGENT
================================================================================
Provides a conversational institutional analyst embedded in Tab 5 of `app.py`.

SECURITY & ARCHITECTURAL INVARIANTS:
1. STRICTLY READ-ONLY SANDBOX:
   - `CapabilitiesConfig(enable_subagents=False, enabled_tools=types.BuiltinTools.none())`
   - `policies=[policy.deny_all(), *(policy.allow(fn.__name__) for fn in custom_tools)]`
   - ZERO shell access (`run_command`), ZERO file creation/edits (`create_file`,
     `edit_file`), ZERO subagent spawning, ZERO SQLite writes.
2. STRICT DETERMINISTIC GROUNDING:
   - Equipped exclusively with 6 Python Custom Tools connected directly to our
     deterministic engines (`portfolio_engine`, `deep_dive_engine`, `macro_engine`,
     `risk_timing_engine`, `screener_engine`, `geopolitics_micro_engine`).
   - System instructions strictly forbid inventing or estimating financial numbers.
3. GRACEFUL DEGRADATION:
   - If GEMINI_API_KEY is absent or the agent runtime fails, returns a clean,
     non-crashing error payload while leaving Tabs 1-4 100% functional.
================================================================================
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import json
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.gemini_client import ROOT_DIR, get_gemini_api_key

AI_SESSIONS_DIR = os.path.abspath(os.path.join(ROOT_DIR, "data_cache", "ai_sessions"))
_ENGINE_CACHE_TTL_SEC = 120.0
_MODEL_COOLDOWN_SEC = 300.0
DEFAULT_AGENT_FALLBACK_CHAIN: Tuple[str, ...] = ("gemini-3.5-flash-lite", "gemini-3.1-flash-lite")

_UNHEALTHY_LOCK = threading.Lock()
_UNHEALTHY_MODEL_UNTIL: Dict[str, float] = {}


def _model_key(model_name: Optional[str]) -> str:
    return model_name or "gemini-3.8-flash"


def _is_in_cooldown(model_name: Optional[str]) -> bool:
    key = _model_key(model_name)
    now = time.monotonic()
    with _UNHEALTHY_LOCK:
        until = _UNHEALTHY_MODEL_UNTIL.get(key)
        if until is None:
            return False
        if now >= until:
            _UNHEALTHY_MODEL_UNTIL.pop(key, None)
            return False
        return True


def _mark_unhealthy(model_name: Optional[str]) -> None:
    key = _model_key(model_name)
    with _UNHEALTHY_LOCK:
        _UNHEALTHY_MODEL_UNTIL[key] = time.monotonic() + _MODEL_COOLDOWN_SEC


@dataclass
class AnalystTurnResult:
    answer_text: str
    conversation_id: Optional[str] = None
    tools_invoked: List[str] = field(default_factory=list)
    model_used: Optional[str] = None
    error: Optional[str] = None


ANALYST_SYSTEM_INSTRUCTIONS = """
You are the Institutional Quantitative & Forensic Portfolio Analyst for this 360° Investment Terminal.

CORE METHODOLOGY (STRICTLY ENFORCED):
1. Equity Forensics: Judge earnings quality via Sloan Ratio (<= +5% pass, < -10% optimal), CFO/EBITDA (>= 0.90x pass, > 1.0x optimal), NWC vs. historical CFO CV, ROIC (NOPAT w/ Goodwill) vs. WACC, DuPont 3 Pillars, Current Ratio (> 1.0x), Interest Coverage (> 3.0x / > 4.0x), and Debt/EBITDA. NEVER compute or reference Altman Z-Score.
2. Sector-Strict Valuation (Forward NTM): Evaluate all 8 valuation models side-by-side (Forward DCF w/ 10% Margin of Safety, paired Reverse DCF checking g_impl <= g_fund, Owner Earnings Yield vs. US 10Y, Forward Multiples [inverted for cyclicals], EVA, Sector-Strict PEGY, Magic Formula, SOTP). For Banks (FINANCIAL_BANK: JPM, DBSDY, BAC, WFC, C), CFO/EBITDA and EV/EBITDA do not apply — evaluate P/TBV vs. ROE, Financial PEGY (0–1.0x), Basel CET1/LCR, and enforce the P/B >= 1.0x veto. Fintechs (NU) and high-CapEx AI infrastructure leaders (GOOGL) map to TECH_HIGH_GROWTH (Enterprise PEGY EV/EBIT NTM); mature Cash Cows & processors (AAPL, MSFT, META, MA, V) map to TECH_CASH_COW (EV/FCF NTM). Parity-backtested asymmetric pruning: TECH_HIGH_GROWTH has 0% valuation pruning (Hold compounding winners; valuation guides buys only), whereas Cash Cows trim 50% at Enterprise PEGY > 1.4x (and Banks/Cyclicals/Defensives at 1.5x / 0.80x / 1.20x) coupled with Quality Gates (Sloan <= +10%, CFO/EBITDA >= 0.70x, Gross Margin stability).
3. Crypto & DeFi Intelligence: Evaluate MVRV Z-Score (<= 2.0), NUPL, aSOPR (1.0 bull support / bear resistance), Pi Cycle Top, 200W SMA, NVM Ratio, NVT Golden Cross, Protocol Real Earnings (Annual Fees - Token Issuance), Real Yield, 30d unlocks (<= 2.5%/mo), Theoretical Post-Dilution Price, GitHub Commits/Active Devs, and Token Sniffer (>= 85/100). Asymmetric exit/re-entry: BTC performs 50% trims on Pi Cycle / NUPL reverse cross; L1 Majors (ETH, SOL) follow full-cycle 0% pruning Hold; DeFi/Mid-Caps trigger 100% exit on (BTC NUPL > 0.60 or MVRV > 3.0) + Trailing DD >= 20% and re-enter strictly when BTC <= 1.05x 200W SMA (confirmed w/ NUPL < 0.0).
4. Governance, Shannon's Demon & Convex LTV: Recommendations are STRICTLY CONSULTATIVE / NON-BINDING (never automated trading). Rebalancing uses Shannon's Demon Inflows to discounted underweight assets (zero tax-drag, vs. Tax-Drag Hurdle Rate). Continuous LTV policy: 20% structural base (expandable up to 25% tactical wealth ceiling, no 10% defensive drop), 28–30% turbo trigger in acute panic (BTC MVRV Z < 0.5 / CAPE < 28x), 45%–50% Hard-Cap safety ceiling, and altcoins are strictly barred as debt collateral.

IRONCLAD GROUNDING RULES:
- You operate in STRICT READ-ONLY MODE with NO file/shell tools.
- You MUST call your Python quantitative tools before stating ANY figure, price, weight, score, ratio, macro indicator, backtest/VaR metric, or simulation result.
- Use `get_backtest_and_risk_metrics` whenever asked about historical CAGR/Sharpe/Sortino/Calmar, VaR/CVaR tail risk, cross-asset correlations, Shannon vs. Passive DCA alpha, or historical crisis stress-tests.
- Cite ONLY exact figures returned by your tools in this conversation. NEVER compute, approximate, extrapolate, or invent missing metrics. If a metric is absent from tool results, explicitly state that it is unavailable.
- Respond concisely and clearly in institutional language matching the user's language (English or Portuguese). Use structured bullet points or compact tables when summarizing quantitative diagnostics.
""".strip()


class _DeterministicToolBackend:
    """Thread-safe short-TTL cache over deterministic core engines for agent tool calls."""

    def __init__(self, default_capital_usd: float = 100_000.0) -> None:
        self.default_capital_usd = float(default_capital_usd)
        self._lock = threading.Lock()
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def _get_cached(self, key: str, loader: Callable[[], Any]) -> Any:
        now = time.monotonic()
        with self._lock:
            entry = self._cache.get(key)
            if entry and (now - entry[0]) < _ENGINE_CACHE_TTL_SEC:
                return entry[1]
        val = loader()
        with self._lock:
            self._cache[key] = (now, val)
        return val

    def _macro(self) -> Any:
        from core.macro_engine import MacroEngine

        return self._get_cached("macro", lambda: MacroEngine().run_macro_aggregation())

    def _portfolio(self, capital_usd: float) -> Any:
        from core.portfolio_engine import PortfolioEngine

        cap = round(float(capital_usd), 2)
        return self._get_cached(
            f"portfolio:{cap}",
            lambda: PortfolioEngine().build_overview_and_lookthrough(capital_usd=cap),
        )

    def _equities(self) -> List[Any]:
        from core.equity_engine import EquityEngine

        rf = float(self._macro().yield_curve.get("us10y_pct", 4.42))
        return self._get_cached(
            f"equities:{rf:.3f}",
            lambda: EquityEngine(risk_free_rate_pct=rf).analyze_portfolio_equities(),
        )

    def _cryptos(self) -> Dict[str, Any]:
        from core.crypto_engine import CryptoEngine

        return self._get_cached("cryptos", lambda: CryptoEngine().analyze_portfolio_cryptos())

    def _risk_timing(self, capital_usd: float) -> Any:
        from core.risk_timing_engine import RiskTimingEngine

        cap = round(float(capital_usd), 2)
        return self._get_cached(
            f"risk_timing:{cap}",
            lambda: RiskTimingEngine().build_risk_and_consultative_timing(
                portfolio=self._portfolio(cap),
                equities=self._equities(),
                cryptos=self._cryptos(),
            ),
        )


def build_readonly_custom_tools(
    default_capital_usd: float = 100_000.0,
    tracker: Optional[List[str]] = None,
) -> List[Callable[..., str]]:
    """
    Constructs the 7 read-only Python Custom Tools bound to a shared deterministic
    TTL-cached backend and an optional per-turn invocation tracker list.
    """
    backend = _DeterministicToolBackend(default_capital_usd=default_capital_usd)

    def _record(name: str) -> None:
        if tracker is not None:
            tracker.append(name)

    def get_portfolio_snapshot(capital_usd: Optional[float] = None) -> str:
        """Reads current holdings from SQLite (read-only), live quotes, P&L, 100% weight check, Look-Through overlap, and sector breakdown.

        Args:
            capital_usd: Base portfolio capital in USD (defaults to active terminal capital).
        """
        _record("get_portfolio_snapshot")
        cap = float(capital_usd) if (capital_usd and capital_usd > 0) else backend.default_capital_usd
        port = backend._portfolio(cap)
        payload = {
            "capital_usd": round(port.capital_usd, 2),
            "total_crypto_pct": round(port.total_crypto_pct, 2),
            "total_hard_assets_pct": round(port.total_hard_assets_pct, 2),
            "target_weight_sum_pct": round(port.target_weight_sum_pct, 2),
            "is_weight_valid_100": bool(port.is_weight_valid_100),
            "weight_validation_message": port.weight_validation_message,
            "effective_gross_exposure_pct_with_qld_2x": round(port.effective_gross_exposure_pct, 2),
            "total_portfolio_pnl_pct": round(port.total_portfolio_pnl_pct, 2),
            "total_portfolio_pnl_usd": round(port.total_portfolio_pnl_usd, 2),
            "ltv_eligible_stocks_weight_pct": round(port.ltv_eligible_stocks_weight_pct, 2),
            "ltv_eligible_btc_weight_pct": round(port.ltv_eligible_btc_weight_pct, 2),
            "positions": [
                {
                    "ticker": p.ticker,
                    "name": p.name,
                    "category": p.category,
                    "sector_vertical": p.sector_vertical,
                    "target_weight_pct": round(p.target_weight_pct, 2),
                    "current_weight_pct": round(p.current_weight_pct, 2),
                    "weight_drift_pp": round(p.weight_drift_pp, 2),
                    "avg_buy_price_usd": round(p.avg_buy_price_usd, 2),
                    "current_price_usd": round(p.current_price_usd, 2),
                    "pnl_pct": round(p.pnl_pct, 2),
                    "allocated_usd": round(p.allocated_usd, 2),
                    "ltv_turbo_eligible": bool(p.ltv_turbo_eligible),
                }
                for p in port.positions
            ],
            "top_lookthrough_exposures": [
                {
                    "ticker": h.ticker,
                    "company_name": h.company_name,
                    "direct_weight_pct": round(h.direct_weight_pct, 2),
                    "total_indirect_pct": round(h.total_indirect_pct, 2),
                    "total_effective_lookthrough_pct": round(h.total_effective_lookthrough_pct, 2),
                    "effective_exposure_usd": round(h.effective_exposure_usd, 2),
                    "overlap_sources": h.overlap_sources,
                }
                for h in port.lookthrough_holdings[:12]
            ],
            "sector_exposure_summary": port.sector_exposure_summary,
        }
        return json.dumps(payload, ensure_ascii=False)

    def audit_single_asset(ticker: str) -> str:
        """Runs the complete deterministic Deep Dive audit on any Stock, ETF, or Cryptoasset (5-filter funnel, 0-100 score, forensic accounting/on-chain, Forward NTM valuations, and SEC/Whitepaper dossier).

        Args:
            ticker: Ticker symbol such as NVDA, JPM, ASML, MELI, SPY, BTC, ETH, PENDLE-USD.
        """
        _record("audit_single_asset")
        from core.deep_dive_engine import DeepDiveEngine

        port = backend._portfolio(backend.default_capital_usd)
        rf = float(backend._macro().yield_curve.get("us10y_pct", 4.42))
        dd = DeepDiveEngine(risk_free_rate_pct=rf).analyze_single_ticker(
            user_ticker=ticker,
            portfolio=port,
        )
        out: Dict[str, Any] = {
            "normalized_ticker": dd.normalized_ticker,
            "asset_class": dd.asset_class,
            "framework_category_label": dd.framework_category_label,
            "in_current_portfolio": bool(dd.in_current_portfolio),
            "sovereign_multiple_name": dd.sovereign_multiple_name,
            "sovereign_multiple_value": dd.sovereign_multiple_value,
            "sovereign_multiple_status": dd.sovereign_multiple_status,
            "screener_score_0_100": dd.screener_score_0_100,
            "regime_classification": dd.regime_classification,
            "automated_consultative_verdict": dd.automated_consultative_verdict,
            "filters_breakdown": [
                {
                    "step": f.step_number,
                    "filter_name": f.filter_name,
                    "calculated_value": f.calculated_value,
                    "strict_criterion": f.strict_criterion,
                    "passed": bool(f.passed),
                    "score": f"{f.score_points}/{f.max_points}",
                    "diagnostic_note": f.diagnostic_note,
                }
                for f in dd.screener_filters_breakdown
            ],
            "risk_and_timing_context": dd.risk_and_timing_context,
        }
        if dd.equity_analysis is not None:
            eq = dd.equity_analysis
            out["equity_forensic_health"] = {
                k: v for k, v in eq.forensic_health.items() if k != "fco_5y_history_b"
            }
            out["equity_valuation_methods"] = eq.valuation_methods
            out["equity_qualitative_strategy"] = {
                k: v for k, v in eq.qualitative_strategy.items() if k != "gm_5y_series"
            }
            out["equity_cagr_matrix"] = eq.cagr_matrix_12_kpis
        if dd.equity_dossier is not None:
            ed = dd.equity_dossier
            out["sec_filing_dossier"] = {
                "annual_form": ed.filing_form_annual,
                "quarterly_form": ed.filing_form_quarterly,
                "auditor_firm": ed.auditor_firm,
                "auditor_opinion": ed.auditor_opinion,
                "sox_404b": ed.sox_404b_controls,
                "mda_growth_decomposition": ed.mda_growth_decomposition,
                "mda_segment_profitability": ed.mda_segment_profitability,
                "mda_backlog_rpo": ed.mda_backlog_rpo,
                "mda_capex_plan": ed.mda_capex_plan,
                "item_1a_specific_risks": ed.item_1a_specific_risks,
                "footnote_contingencies_litigation": ed.footnote_contingencies_litigation,
                "footnote_sbc_impact": ed.footnote_sbc_impact,
                "footnote_revenue_recognition": ed.footnote_revenue_recognition,
                "footnote_debt_maturity": ed.footnote_debt_maturity_schedule,
                "analyst_target_mean_usd": ed.analyst_target_mean_usd,
                "analyst_recommendations_dist": ed.analyst_recommendations_dist,
                "analyst_eps_revisions_30d_90d": ed.analyst_eps_revisions_30d_90d,
                "ma_and_strategic_deals": getattr(ed, "ma_and_strategic_deals", ""),
                "ma_payment_and_goodwill": getattr(ed, "ma_payment_and_goodwill", ""),
            }
        if dd.corporate_signal_ma is not None:
            sm = dd.corporate_signal_ma
            out["corporate_signal_and_ma"] = {
                "guidance_delta_summary": sm.guidance_delta_summary,
                "ceo_cfo_internal_commentary": sm.ceo_cfo_internal_commentary,
                "qa_analyst_clashes": sm.qa_analyst_clashes,
                "operational_moat_shifts": sm.operational_moat_shifts,
                "ma_and_strategic_deals": sm.ma_and_strategic_deals,
                "payment_structure_and_dilution": sm.payment_structure_and_dilution,
                "goodwill_and_impairment_risk": sm.goodwill_and_impairment_risk,
                "antitrust_and_regulatory_status": sm.antitrust_and_regulatory_status,
            }
        if dd.crypto_profile is not None:
            cp = dd.crypto_profile
            out["crypto_profile"] = {
                "spot_price_usd": cp.spot_price_usd,
                "market_cap_b": cp.market_cap_b,
                "fdv_b": cp.fdv_b,
                "circulating_pct": cp.circulating_pct,
                "onchain_metrics": cp.onchain_metrics,
                "mining_metrics": cp.mining_metrics,
                "tokenomics_valuation": cp.tokenomics_valuation,
                "supply_structure": cp.supply_structure,
                "derivatives_sentiment": cp.derivatives_sentiment,
            }
        if dd.crypto_dossier is not None:
            cf = dd.crypto_dossier
            out["crypto_technical_dossier"] = {
                "wp_title_author": cf.wp_title_author,
                "wp_value_proposition": cf.wp_value_proposition,
                "wp_consensus_architecture": cf.wp_consensus_architecture,
                "wp_value_accrual": cf.wp_value_accrual_mechanism,
                "github_core_repos": cf.github_core_repos,
                "github_commits_4w": cf.github_commits_4w,
                "github_active_devs_monthly": cf.github_active_devs_monthly,
                "deepdao_status": cf.deepdao_status,
                "recent_governance_proposals": cf.recent_governance_proposals,
                "skin_in_the_game_locked_pct": cf.skin_in_the_game_locked_pct,
                "token_sniffer_score": cf.token_sniffer_score,
                "audit_firms": cf.audit_firms,
                "exploit_history": cf.exploit_history,
            }
        if dd.crypto_internal_dev is not None:
            dv = dd.crypto_internal_dev
            out["crypto_upgrades_and_unlocks"] = {
                "founder_core_dev_signals": dv.founder_core_dev_signals,
                "upcoming_protocol_upgrades": dv.upcoming_protocol_upgrades,
                "architecture_and_fee_switch_changes": dv.architecture_and_fee_switch_changes,
                "unlock_schedule_30_60_90d": dv.unlock_schedule_30_60_90d,
                "whale_and_vc_concentration": dv.whale_and_vc_concentration,
                "active_dao_proposals_impact": dv.active_dao_proposals_impact,
            }
        return json.dumps(out, ensure_ascii=False, default=str)

    def get_macro_and_geopolitics() -> str:
        """Fetches deterministic U.S. & global macro indicators (GDP, CPI, Fed Funds, Sahm Rule + Payroll + ICSA, SOS, PMI Services/Mfg, 10Y-2Y Yield Curve, M2/DXY), plus geopolitical tail-risk matrix and recent 8-K/Form 4/DAO events."""
        _record("get_macro_and_geopolitics")
        from core.geopolitics_micro_engine import GeopoliticsMicroEngine

        m = backend._macro()
        geo_eng = GeopoliticsMicroEngine()
        geo_rows = geo_eng.get_geopolitical_matrix()
        micro_rows = geo_eng.get_micro_events()
        payload = {
            "timestamp": m.timestamp,
            "cycle_phase": m.cycle_phase,
            "lagging_indicators": m.basic_metrics,
            "sahm_paired": m.sahm_paired,
            "sos_indicator": m.sos_indicator,
            "pmi_analysis": m.pmi_analysis,
            "yield_curve": m.yield_curve,
            "monetary_aggregates": m.monetary_aggregates,
            "geopolitical_impact_matrix": [
                {
                    "global_event": g.global_event,
                    "region_vector": g.region_vector,
                    "severity": g.severity,
                    "affected_portfolio_assets": g.affected_portfolio_assets,
                    "revenue_exposed_pct": g.revenue_or_production_exposed_pct,
                    "fundamental_mechanism": g.fundamental_impact_mechanism,
                    "country_liquidity_risk": g.country_liquidity_risk_assessment,
                }
                for g in geo_rows
            ],
            "recent_micro_events": [
                {
                    "date": ev.date,
                    "asset_ticker": ev.asset_ticker,
                    "source_type": ev.source_type,
                    "headline": ev.headline,
                    "event_category": ev.event_category,
                    "classification": ev.classification,
                    "fundamental_impact": ev.fundamental_impact_analysis,
                }
                for ev in micro_rows
            ],
        }
        return json.dumps(payload, ensure_ascii=False, default=str)

    def simulate_shannon_inflow(
        inflow_usd: float = 10_000.0,
        capital_usd: Optional[float] = None,
    ) -> str:
        """Simulates Shannon's Demon fresh capital allocation exclusively into qualified discounted/underweight holdings (zero tax-drag vs. Tax-Drag Hurdle Rate).

        Args:
            inflow_usd: Fresh capital inflow amount in USD to deploy (e.g., 10000.0).
            capital_usd: Optional base portfolio capital in USD.
        """
        _record("simulate_shannon_inflow")
        cap = float(capital_usd) if (capital_usd and capital_usd > 0) else backend.default_capital_usd
        inflow = max(0.0, float(inflow_usd))
        rt = backend._risk_timing(cap)

        all_rows = rt.consultative_asset_timing_table
        eligible_rows = [r for r in all_rows if r.shannon_inflow_eligible]
        used_fallback = False
        if not eligible_rows:
            eligible_rows = all_rows[:5]
            used_fallback = True
        total_w = sum(r.target_weight_pct for r in eligible_rows) or 1.0

        allocations = [
            {
                "ticker": r.asset_ticker,
                "name": r.asset_name,
                "vertical": r.framework_category,
                "target_weight_pct": round(r.target_weight_pct, 2),
                "current_weight_pct": round(r.current_weight_pct, 2),
                "weight_drift_pp": round(r.weight_drift_pp, 2),
                "primary_indicator_current": r.primary_indicator_current,
                "consultative_status": r.consultative_status_vs_reference,
                "shannon_inflow_eligible": bool(r.shannon_inflow_eligible),
                "inflow_share_pct": round((r.target_weight_pct / total_w) * 100.0, 2),
                "suggested_inflow_usd": round(inflow * (r.target_weight_pct / total_w), 2),
                "tax_drag_hurdle_rate_pct": round(r.tax_drag_hurdle_rate_pct, 2),
            }
            for r in eligible_rows
        ]
        payload = {
            "inflow_usd": round(inflow, 2),
            "base_capital_usd": round(cap, 2),
            "qualified_count": len([r for r in all_rows if r.shannon_inflow_eligible]),
            "used_fallback_watchlist": used_fallback,
            "note": "Consultative only — zero automated execution and zero tax-drag.",
            "suggested_allocations": allocations,
        }
        return json.dumps(payload, ensure_ascii=False)

    def simulate_ltv_stress_test(
        shock_equities_pct: float = -25.0,
        shock_btc_pct: float = -40.0,
        initial_ltv_pct: float = 20.0,
        capital_usd: Optional[float] = None,
    ) -> str:
        """Simulates severe market drawdowns on eligible Equities/ETFs and Bitcoin to compute post-shock LTV against the 50% Hard-Cap and Aave V3 Health Factor.

        Args:
            shock_equities_pct: Percentage drawdown/shock on Stocks/ETFs (e.g., -25.0 or -35.0).
            shock_btc_pct: Percentage drawdown/shock on Bitcoin/crypto (e.g., -40.0 or -50.0).
            initial_ltv_pct: Starting Global LTV % prior to shock (0 to 35, default 20.0).
            capital_usd: Optional base portfolio capital in USD.
        """
        _record("simulate_ltv_stress_test")
        cap = float(capital_usd) if (capital_usd and capital_usd > 0) else backend.default_capital_usd
        port = backend._portfolio(cap)
        rt = backend._risk_timing(cap)

        collat_stocks_usd = cap * (port.ltv_eligible_stocks_weight_pct / 100.0)
        collat_btc_usd = cap * (port.ltv_eligible_btc_weight_pct / 100.0)
        non_collat_pct = max(
            0.0,
            100.0 - port.ltv_eligible_stocks_weight_pct - port.ltv_eligible_btc_weight_pct,
        )
        sim_debt_usd = cap * (float(initial_ltv_pct) / 100.0)
        stressed_collat_usd = (
            collat_stocks_usd * (1.0 + float(shock_equities_pct) / 100.0)
            + collat_btc_usd * (1.0 + float(shock_btc_pct) / 100.0)
        )
        stressed_portfolio_usd = (
            stressed_collat_usd
            + cap * (non_collat_pct / 100.0) * (1.0 + float(shock_btc_pct) / 100.0)
        )
        resulting_ltv_pct = (
            (sim_debt_usd / max(1.0, stressed_portfolio_usd)) * 100.0
            if sim_debt_usd > 0
            else 0.0
        )
        resulting_hf = (
            min(9.99, 0.78 / max(0.01, resulting_ltv_pct / 100.0))
            if resulting_ltv_pct > 0
            else 9.99
        )
        breaches_hard_cap = resulting_ltv_pct >= 50.0
        payload = {
            "inputs": {
                "capital_usd": round(cap, 2),
                "shock_equities_pct": round(float(shock_equities_pct), 2),
                "shock_btc_pct": round(float(shock_btc_pct), 2),
                "initial_ltv_pct": round(float(initial_ltv_pct), 2),
            },
            "stress_result": {
                "simulated_debt_usd": round(sim_debt_usd, 2),
                "post_shock_eligible_collateral_usd": round(stressed_collat_usd, 2),
                "post_shock_portfolio_usd": round(stressed_portfolio_usd, 2),
                "resulting_ltv_pct": round(resulting_ltv_pct, 2),
                "hard_cap_limit_pct": 50.0,
                "breaches_50pct_hard_cap": breaches_hard_cap,
                "estimated_aave_health_factor": round(resulting_hf, 2),
                "liquidation_threshold_hf": 1.00,
                "safety_verdict": (
                    "CRITICAL BREACH (>= 50% Hard-Cap)"
                    if breaches_hard_cap
                    else ("CAUTION (35%–50% Zone)" if resulting_ltv_pct > 35.0 else "SAFE (< 35% LTV & Healthy Margin)")
                ),
            },
            "current_convex_ltv_panel": rt.convex_ltv_panel,
            "aave_v3_stress_table": rt.aave_v3_stress_test_table,
            "performance_risk_metrics": rt.performance_risk_metrics,
        }
        return json.dumps(payload, ensure_ascii=False, default=str)

    def run_opportunity_screener(asset_type: str = "all") -> str:
        """Runs the strict 5-filter quantitative & forensic screener for external/watchlist equity and crypto candidates.

        Args:
            asset_type: Filter scope — 'stocks', 'crypto', or 'all' (default).
        """
        _record("run_opportunity_screener")
        from core.screener_engine import ScreenerEngine

        eng = ScreenerEngine()
        mode = (asset_type or "all").strip().lower()
        out: Dict[str, Any] = {}
        if mode in ("all", "stocks", "equities", "stock"):
            rows = eng.run_stock_screener()
            out["stocks_screener"] = [
                {
                    "ticker": r.ticker,
                    "company_name": r.company_name,
                    "sector": r.sector,
                    "price_usd": round(r.price_usd, 2),
                    "sloan_ratio_pct": round(r.sloan_ratio_pct, 2),
                    "cfo_to_ebitda": round(r.fco_to_ebitda, 2),
                    "roic_nopat_pct": round(r.roic_nopat_pct, 2),
                    "wacc_pct": round(r.wacc_pct, 2),
                    "g_impl_pct": round(r.reverse_dcf_g_impl_pct, 2),
                    "g_fund_pct": round(r.g_fund_pct, 2),
                    "pegy": f"{r.enterprise_or_fin_pegy:.2f}x ({r.pegy_type})",
                    "dcf_mos10_usd": round(r.dcf_fair_mos10_usd, 2),
                    "sotp_fair_usd": round(r.sotp_fair_usd, 2),
                    "filters_passed": f"{r.filters_passed_count}/5",
                    "all_5_passed": bool(r.all_5_filters_passed),
                    "verdict": r.framework_verdict,
                }
                for r in rows
            ]
        if mode in ("all", "crypto", "cryptos", "tokens"):
            c_rows = eng.run_crypto_screener()
            out["crypto_screener"] = [
                {
                    "symbol": c.symbol,
                    "name": c.name,
                    "category": c.category,
                    "price_usd": round(c.price_usd, 2),
                    "circulating_supply_pct": round(c.circulating_supply_pct, 2),
                    "monthly_unlock_pct": round(c.monthly_unlock_pct, 2),
                    "token_sniffer_score": c.token_sniffer_score,
                    "github_active_devs": c.active_devs_github,
                    "protocol_real_earnings_m": round(c.protocol_real_earnings_m, 2),
                    "mvrv_z_score": round(c.mvrv_z_score, 2),
                    "filters_passed": f"{c.filters_passed_count}/5",
                    "all_5_passed": bool(c.all_5_filters_passed),
                    "verdict": c.framework_verdict,
                }
                for c in c_rows
            ]
        return json.dumps(out, ensure_ascii=False)

    def get_backtest_and_risk_metrics(capital_usd: Optional[float] = None) -> str:
        """Runs or reads the 3-year historical daily portfolio backtest and tail-risk metrics (CAGR, Volatility, Sharpe, Sortino, MaxDD, Calmar, Daily VaR/CVaR 95% & 99%, Top/Bottom cross-asset correlations, Shannon Inflow vs. Passive DCA alpha, and crisis stress-tests).

        Args:
            capital_usd: Base capital in USD (defaults to active portfolio simulation capital).
        """
        _record("get_backtest_and_risk_metrics")
        from core.backtest_engine import run_portfolio_backtest

        cap = float(capital_usd) if capital_usd and capital_usd > 0 else float(default_capital_usd)
        macro = backend._macro()
        port = backend._portfolio(cap)
        rf_pct = float(macro.yield_curve.get("us10y_pct", 4.42))
        vix_now = float(macro.monetary_aggregates.get("vix_current", 18.4))
        bt = run_portfolio_backtest(port.positions, capital_usd=cap, risk_free_rate_pct=rf_pct)

        corr_df = bt.get("corr_matrix_df")
        corr_pairs: List[Dict[str, Any]] = []
        if corr_df is not None and not corr_df.empty:
            cols = list(corr_df.columns)
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    corr_pairs.append({
                        "pair": f"{cols[i]} / {cols[j]}",
                        "corr": round(float(corr_df.iloc[i, j]), 2),
                    })
            corr_pairs.sort(key=lambda x: x["corr"], reverse=True)

        payload = {
            "data_source": bt.get("data_source"),
            "period_days": bt.get("period_days"),
            "assets_covered": bt.get("assets_covered"),
            "vix_current": vix_now,
            "portfolio_cagr_pct": bt.get("portfolio_cagr_pct"),
            "annualized_vol_pct": bt.get("annualized_vol_pct"),
            "sharpe_ratio": bt.get("sharpe_ratio"),
            "sortino_ratio": bt.get("sortino_ratio"),
            "max_drawdown_pct": bt.get("max_drawdown_pct"),
            "calmar_ratio": bt.get("calmar_ratio"),
            "spy_cagr_pct": bt.get("spy_cagr_pct"),
            "btc_cagr_pct": bt.get("btc_cagr_pct"),
            "var_95_daily_pct": bt.get("var_95_daily_pct"),
            "cvar_95_daily_pct": bt.get("cvar_95_daily_pct"),
            "var_99_daily_pct": bt.get("var_99_daily_pct"),
            "cvar_99_daily_pct": bt.get("cvar_99_daily_pct"),
            "shannon_vs_passive_dca": bt.get("shannon_vs_bh"),
            "stress_tests": bt.get("stress_tests"),
            "highest_correlations": corr_pairs[:5],
            "lowest_correlations": list(reversed(corr_pairs[-5:])) if len(corr_pairs) >= 5 else corr_pairs,
        }
        return json.dumps(payload, ensure_ascii=False, default=str)

    return [
        get_portfolio_snapshot,
        audit_single_asset,
        get_macro_and_geopolitics,
        simulate_shannon_inflow,
        simulate_ltv_stress_test,
        run_opportunity_screener,
        get_backtest_and_risk_metrics,
    ]


def build_readonly_agent_config(
    api_key: Optional[str] = None,
    conversation_id: Optional[str] = None,
    default_capital_usd: float = 100_000.0,
    tracker: Optional[List[str]] = None,
    model_override: Optional[str] = None,
    max_api_retries: int = 1,
) -> Any:
    """
    Constructs a strictly locked-down, read-only `LocalAgentConfig` using
    Google Antigravity SDK (`BuiltinTools.none()`, `enable_subagents=False`,
    and `policy.deny_all()` + explicit custom tool allowlist).
    """
    from google.antigravity import LocalAgentConfig, types
    from google.antigravity.hooks import policy

    os.makedirs(AI_SESSIONS_DIR, exist_ok=True)
    custom_tools = build_readonly_custom_tools(
        default_capital_usd=default_capital_usd,
        tracker=tracker,
    )

    cfg_kwargs: Dict[str, Any] = {
        "system_instructions": types.TemplatedSystemInstructions(
            identity=ANALYST_SYSTEM_INSTRUCTIONS
        ),
        "capabilities": types.CapabilitiesConfig(
            enable_subagents=False,
            enabled_tools=types.BuiltinTools.none(),
        ),
        "tools": custom_tools,
        "policies": [
            policy.deny_all(),
            *(policy.allow(fn.__name__) for fn in custom_tools),
        ],
        "budget_config": types.BudgetConfig(max_model_calls=8, max_tool_calls=12),
        "retry_config": types.RetryConfig(
            api_retry=types.ModelAPIRetryConfig(
                max_retries=max(0, int(max_api_retries)),
                initial_sleep_duration_ms=600,
                exponential_multiplier=2.0,
            ),
        ),
        "save_dir": AI_SESSIONS_DIR,
    }
    if api_key:
        cfg_kwargs["api_key"] = api_key
    if model_override and model_override.strip():
        cfg_kwargs["model"] = model_override.strip()
    if conversation_id:
        cfg_kwargs["conversation_id"] = conversation_id

    return LocalAgentConfig(**cfg_kwargs)


def _run_async(coro: Any) -> Any:
    """Runs an async coroutine safely from Streamlit's sync script thread."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result_box: Dict[str, Any] = {}
    err_box: Dict[str, BaseException] = {}

    def _worker() -> None:
        try:
            result_box["value"] = asyncio.run(coro)
        except BaseException as exc:  # noqa: BLE001
            err_box["err"] = exc

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join()
    if "err" in err_box:
        raise err_box["err"]
    return result_box.get("value")


class InstitutionalAIAnalyst:
    """Streamlit-facing façade around the read-only Google Antigravity Agent."""

    def is_available(self) -> Tuple[bool, str]:
        if not get_gemini_api_key():
            return (
                False,
                "GEMINI_API_KEY is not configured in .env (obtain a key at https://aistudio.google.com/app/api-keys).",
            )
        try:
            from google.antigravity import Agent, LocalAgentConfig  # noqa: F401
        except Exception as exc:
            return False, f"google-antigravity SDK unavailable: {type(exc).__name__}"
        return True, "Ready (Google Antigravity SDK — Strictly Read-Only Tool Sandbox)"

    def _resolve_candidate_models(self, preferred_model: Optional[str] = None) -> List[Optional[str]]:
        pref = (preferred_model or "").strip()
        if pref.lower() in ("", "auto"):
            env_model = os.environ.get("ANTIGRAVITY_MODEL", "").strip()
            raw_candidates: List[Optional[str]] = [
                env_model if env_model else None,
                *DEFAULT_AGENT_FALLBACK_CHAIN,
            ]
        else:
            raw_candidates = [pref, *DEFAULT_AGENT_FALLBACK_CHAIN]

        deduped: List[Optional[str]] = []
        seen_keys = set()
        for c in raw_candidates:
            k = _model_key(c)
            if k not in seen_keys:
                seen_keys.add(k)
                deduped.append(c)

        healthy = [c for c in deduped if not _is_in_cooldown(c)]
        return healthy if healthy else deduped

    def ask(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        capital_usd: float = 100_000.0,
        preferred_model: Optional[str] = None,
    ) -> AnalystTurnResult:
        q = (question or "").strip()
        if not q:
            return AnalystTurnResult(
                answer_text="Please enter an analytical question for the AI Portfolio Analyst.",
                conversation_id=conversation_id,
                error="Empty prompt",
            )

        ok, msg = self.is_available()
        if not ok:
            return AnalystTurnResult(
                answer_text="",
                conversation_id=conversation_id,
                error=msg,
            )

        api_key = get_gemini_api_key()
        candidates = self._resolve_candidate_models(preferred_model=preferred_model)
        last_error: Optional[BaseException] = None
        last_tools: List[str] = []

        async def _execute_turn(
            model_choice: Optional[str],
            is_final: bool,
            tracker: List[str],
        ) -> Tuple[str, Optional[str]]:
            from google.antigravity import Agent

            cfg = build_readonly_agent_config(
                api_key=api_key,
                conversation_id=conversation_id,
                default_capital_usd=capital_usd,
                tracker=tracker,
                model_override=model_choice,
                max_api_retries=1 if is_final else 0,
            )
            chat_timeout = 60.0 if is_final else 25.0
            async with Agent(config=cfg) as agent:
                response = await asyncio.wait_for(agent.chat(q), timeout=chat_timeout)
                text = (await asyncio.wait_for(response.text(), timeout=30.0) or "").strip()
                conv_id = getattr(agent, "conversation_id", None) or conversation_id
                return text, conv_id

        for idx, candidate in enumerate(candidates):
            is_final = idx == (len(candidates) - 1)
            tools_invoked: List[str] = []
            try:
                answer, next_conv_id = _run_async(
                    _execute_turn(candidate, is_final=is_final, tracker=tools_invoked)
                )
                if not answer:
                    answer = "No textual response returned by the agent. Try rephrasing or starting a new session."
                seen = set()
                ordered_tools = [t for t in tools_invoked if not (t in seen or seen.add(t))]
                return AnalystTurnResult(
                    answer_text=answer,
                    conversation_id=next_conv_id,
                    tools_invoked=ordered_tools,
                    model_used=_model_key(candidate),
                )
            except Exception as exc:
                last_error = exc
                last_tools = tools_invoked
                err_str = f"{type(exc).__name__}: {exc}".upper()
                transient = (
                    isinstance(exc, TimeoutError)
                    or "TIMEOUT" in err_str
                    or "503" in err_str
                    or "UNAVAILABLE" in err_str
                    or "429" in err_str
                    or "RESOURCE_EXHAUSTED" in err_str
                )
                if transient:
                    _mark_unhealthy(candidate)
                if transient and not is_final:
                    continue
                break

        err_raw = str(last_error or "")
        if isinstance(last_error, TimeoutError) or "TIMEOUT" in type(last_error).__name__.upper():
            friendly = (
                "AI Analyst timed out waiting across available hosted Gemini models. "
                "Deterministic Tabs 1–4 remain 100% functional; please retry shortly."
            )
        elif "503" in err_raw or "UNAVAILABLE" in err_raw:
            friendly = (
                "All fallback Gemini Agent models are temporarily experiencing high demand (HTTP 503). "
                "Please retry in a few moments. Deterministic Tabs 1–4 remain 100% operational."
            )
        elif "429" in err_raw or "RESOURCE_EXHAUSTED" in err_raw:
            friendly = (
                "Gemini API quota limit hit on available models (HTTP 429). "
                "Check your Google AI Studio quota or select `gemini-3.5-flash-lite`. "
                "Deterministic Tabs 1–4 remain 100% operational."
            )
        else:
            friendly = f"Agent execution error ({type(last_error).__name__}): {last_error}"

        return AnalystTurnResult(
            answer_text="",
            conversation_id=conversation_id,
            tools_invoked=last_tools,
            error=friendly,
        )

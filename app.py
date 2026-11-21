"""
TERMINAL INSTITUCIONAL — CENTRAL DO RELATÓRIO MASTER 360° & MÓDULOS DE INTERVENÇÃO ATIVA
Arquitetura Enxuta e Sem Redundâncias:
- Toda a densidade analítica, macroeconômica, contábil forense, valuation multi-métodos Forward (NTM),
  gráficos vetoriais, dossiês SEC 10-K/M&A/Calls/Porter, Whitepapers/Core Devs/Unlocks, DeFi State of the Union
  e Screener está unificada em UM ÚNICO RELATÓRIO MASTER MULTI-COMPLETO (.PDF) dividido em 7 Seções.
- A interface do aplicativo concentra-se estritamente nos módulos que exigem intervenção ativa do usuário:
  1. Emissão e Download em 1 Clique do Relatório Master Multi-Completo 360° (.PDF) + Refresh Ao Vivo;
  2. Gestor Dinâmico de Portfólio (CRUD SQLite: Adicionar, Editar, Remover e Normalizar Pesos em 100%);
  3. Deep Dive Analyzer Individual (Stock & Crypto Picker sob demanda + PDF Individual);
  4. Simuladores Interativos (Shannon Inflow & Stress-Test de LTV) e Chave Liga/Desliga (ON/OFF) do Notificador.
"""

from __future__ import annotations

import datetime
import html
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.macro_engine import MacroEngine, MacroDataBundle
from core.portfolio_engine import PortfolioEngine, PortfolioOverviewBundle
from core.equity_engine import EquityEngine, EquityFullAnalysis
from core.crypto_engine import CryptoEngine, CryptoFullProfile
from core.filings_engine import FilingsEngine, EquityDocumentaryDossier, CryptoDocumentaryDossier
from core.geopolitics_micro_engine import GeopoliticsMicroEngine, GeopoliticalImpactRow, MicroCorporateProtocolEvent
from core.screener_engine import ScreenerEngine, StockScreenerRow, CryptoScreenerRow
from core.risk_timing_engine import RiskTimingEngine, RiskLeverageTimingBundle
from core.deep_dive_engine import DeepDiveEngine, DeepDiveResultBundle
from core.pdf_exporter import InstitutionalPDFExporter
from core.background_notifier import BackgroundNotifierEngine
from core.gemini_client import is_gemini_configured
from core.ai_analyst import InstitutionalAIAnalyst
from core.ai_report_orchestrator import AIReportOrchestrator, clear_ai_master_insights_cache
from core.backtest_engine import run_portfolio_backtest
from core.excel_exporter import build_institutional_excel_bytes
from core.live_quant_fetcher import fetch_live_adtv_map, fetch_live_vix_and_fx
from core.charts import (
    build_banks_ptbv_vs_roe_scatter,
    build_btc_asopr_chart,
    build_btc_picycle_200w_hashribbon_mmc_chart,
    build_crypto_github_and_earnings_chart,
    build_crypto_mvrv_nupl_chart,
    build_crypto_nvm_and_cdd_chart,
    build_crypto_onchain_gauges_chart,
    build_deep_dive_dupont_and_margins_chart,
    build_deep_dive_forensic_5y_chart,
    build_deep_dive_valuation_cockpit_chart,
    build_macro_comprehensive_chart,
    build_multi_method_valuation_chart,
    build_portfolio_equity_curve_chart,
    build_portfolio_weight_gauge_chart,
    build_yield_curve_and_icsa_chart,
)


st.set_page_config(
    page_title="360° Master Report Hub & Active Intervention — Value Investing Framework",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_clean_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .block-container {
            padding-top: 1.1rem !important;
            padding-bottom: 2.2rem !important;
            max-width: 97% !important;
        }
        .inst-banner {
            background: linear-gradient(135deg, #0B1120 0%, #1E293B 65%, #0F172A 100%);
            border: 1px solid #334155;
            border-left: 5px solid #3B82F6;
            border-radius: 10px;
            padding: 1.05rem 1.35rem;
            margin-bottom: 1.0rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.22);
        }
        .inst-banner h1 {
            color: #F8FAFC !important;
            font-size: 1.38rem !important;
            font-weight: 800 !important;
            margin: 0 0 0.25rem 0 !important;
            letter-spacing: -0.02em;
        }
        .inst-banner p {
            color: #94A3B8 !important;
            font-size: 0.87rem !important;
            margin: 0 !important;
            line-height: 1.45;
        }
        .section-header {
            background: linear-gradient(90deg, #0F172A 0%, #1E293B 100%);
            border-left: 4px solid #10B981;
            border-top: 1px solid #334155;
            border-right: 1px solid #334155;
            border-bottom: 1px solid #334155;
            padding: 0.6rem 1.0rem;
            border-radius: 7px;
            margin-top: 1.0rem;
            margin-bottom: 0.75rem;
        }
        .section-header h3 {
            color: #F1F5F9 !important;
            font-size: 0.98rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
        }
        .section-header span {
            color: #94A3B8 !important;
            font-size: 0.79rem !important;
            display: block;
            margin-top: 0.12rem;
        }
        .kpi-card {
            background: #0F172A;
            border: 1px solid #1E293B;
            border-top: 3px solid #3B82F6;
            border-radius: 8px;
            padding: 0.8rem 0.95rem;
            height: 100%;
        }
        .kpi-card.emerald { border-top-color: #10B981; }
        .kpi-card.amber { border-top-color: #F59E0B; }
        .kpi-card.purple { border-top-color: #8B5CF6; }
        .kpi-title {
            color: #94A3B8;
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.25rem;
        }
        .kpi-value {
            color: #F8FAFC;
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.15rem;
            font-weight: 800;
            line-height: 1.2;
            margin-bottom: 0.2rem;
        }
        .kpi-sub {
            color: #CBD5E1;
            font-size: 0.75rem;
            line-height: 1.35;
        }
        .insight-callout {
            background: rgba(30, 41, 59, 0.78);
            border: 1px solid #334155;
            border-left: 4px solid #3B82F6;
            border-radius: 8px;
            padding: 0.75rem 1.0rem;
            margin: 0.55rem 0 0.85rem 0;
            color: #E2E8F0;
            font-size: 0.84rem;
            line-height: 1.5;
        }
        /* Tabelas HTML Amplas — ZERO Texto Espremido ou Palavras Quebradas no Meio */
        .inst-table-wrap {
            width: 100%;
            overflow-x: auto;
            border-radius: 8px;
            border: 1px solid #1E293B;
            margin-bottom: 0.9rem;
            background: #0B1120;
        }
        table.inst-html-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
            color: #E2E8F0;
            table-layout: auto;
        }
        table.inst-html-table thead tr {
            background: #1E293B;
            border-bottom: 2px solid #334155;
        }
        table.inst-html-table th {
            padding: 0.6rem 0.8rem;
            text-align: left;
            font-weight: 700;
            color: #93C5FD;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            word-break: normal !important;
            overflow-wrap: break-word !important;
            hyphens: none !important;
            vertical-align: bottom;
        }
        table.inst-html-table td {
            padding: 0.58rem 0.8rem;
            border-bottom: 1px solid #1E293B;
            vertical-align: top;
            line-height: 1.45;
            word-break: normal !important;
            overflow-wrap: break-word !important;
            hyphens: none !important;
        }
        table.inst-html-table tbody tr:nth-child(even) {
            background: rgba(15, 23, 42, 0.65);
        }
        .st-badge {
            display: inline-block;
            padding: 0.14rem 0.5rem;
            border-radius: 5px;
            font-size: 0.73rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            white-space: nowrap;
        }
        .st-badge.green { background: rgba(16, 185, 129, 0.18); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); }
        .st-badge.amber { background: rgba(245, 158, 11, 0.18); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4); }
        .st-badge.red   { background: rgba(239, 68, 68, 0.18); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.4); }
        .st-badge.blue  { background: rgba(59, 130, 246, 0.18); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.4); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _classify_badge(val_str: str) -> str:
    s = val_str.lower()
    if any(k in s for k in ["ótimo", "ouro", "aprovado", "positivo", "boa", "segura", "sim", "sweet spot", "baixo", "100%", "blindada", "great", "optimal", "gold", "approved", "positive", "safe", "yes", "low", "shielded"]):
        return "green"
    if any(k in s for k in ["ruim", "reprovado", "alerta", "crise", "recessão", "negativo", "cuidado", "veto", "alto risco", "bad", "rejected", "warning", "crisis", "recession", "negative", "caution", "high risk", "no", "não"]):
        return "red"
    if any(k in s for k in ["neutro", "ok", "misto", "moderado", "aguardar", "neutral", "mixed", "moderate", "hold", "monitor"]):
        return "amber"
    return "blue"


def render_clean_table(df: pd.DataFrame, badge_cols: Optional[List[str]] = None) -> None:
    """Renderiza tabela HTML limpa com no máximo 6-7 colunas e sem jamais espremer texto em badges."""
    badge_cols = badge_cols or []
    headers_html = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    rows_html = []
    for _, row in df.iterrows():
        cells = []
        for idx, col in enumerate(df.columns):
            raw_val = "" if pd.isna(row[col]) else str(row[col])
            esc_val = html.escape(raw_val)
            if col in badge_cols and len(raw_val) <= 28:
                b_cls = _classify_badge(raw_val)
                cells.append(f'<td><span class="st-badge {b_cls}">{esc_val}</span></td>')
            elif idx == 0 and len(raw_val) <= 18:
                cells.append(f'<td><span class="st-badge blue">{esc_val}</span></td>')
            else:
                cells.append(f"<td>{esc_val}</td>")
        rows_html.append(f"<tr>{''.join(cells)}</tr>")
    st.markdown(
        f'<div class="inst-table-wrap"><table class="inst-html-table">'
        f"<thead><tr>{headers_html}</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def render_kpi_card(title: str, value: str, subtitle: str, tone: str = "blue") -> None:
    st.markdown(
        f"""
        <div class="kpi-card {tone}">
            <div class="kpi-title">{html.escape(title)}</div>
            <div class="kpi-value">{html.escape(value)}</div>
            <div class="kpi-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str = "") -> None:
    sub_html = f"<span>{html.escape(subtitle)}</span>" if subtitle else ""
    st.markdown(
        f'<div class="section-header"><h3>{html.escape(title)}</h3>{sub_html}</div>',
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=900, show_spinner=False)
def load_full_intelligence_bundle(
    capital_usd: float,
    db_sig: str,
    refresh_token: int,
    tax_rate_pct: float = 15.0,
) -> Dict[str, Any]:
    _ = (db_sig, refresh_token)
    macro_eng = MacroEngine()
    macro_bundle = macro_eng.run_macro_aggregation()

    port_eng = PortfolioEngine()
    port_bundle = port_eng.build_overview_and_lookthrough(capital_usd=capital_usd)

    rf_rate = macro_bundle.yield_curve.get("us10y_pct", 4.42)
    eq_eng = EquityEngine(risk_free_rate_pct=rf_rate)
    eq_list = eq_eng.analyze_portfolio_equities()

    cr_eng = CryptoEngine()
    cr_dict = cr_eng.analyze_portfolio_cryptos()

    fil_eng = FilingsEngine()
    eq_filings = fil_eng.get_equity_dossiers()
    cr_filings = fil_eng.get_crypto_dossiers()

    geo_eng = GeopoliticsMicroEngine()
    geo_matrix = geo_eng.get_geopolitical_matrix(prefer_ai_cache=False)
    micro_events = geo_eng.get_micro_events(prefer_ai_cache=False)

    scr_eng = ScreenerEngine()
    stk_screener = scr_eng.run_stock_screener()
    cr_screener = scr_eng.run_crypto_screener()

    vix_fx = fetch_live_vix_and_fx()
    fed_funds_pct = float(macro_bundle.monetary_aggregates.get("fed_funds_rate_pct", 4.25))
    vix_curr = float(macro_bundle.monetary_aggregates.get("vix_current", vix_fx.get("vix_current", 18.4)))
    fx_usd_brl = float(macro_bundle.monetary_aggregates.get("usd_brl_fx", vix_fx.get("usd_brl", 5.85)))

    backtest_res = run_portfolio_backtest(
        positions=port_bundle.positions,
        capital_usd=capital_usd,
        risk_free_rate_pct=fed_funds_pct,
    )
    live_adtv = fetch_live_adtv_map(
        [p.ticker for p in port_bundle.positions],
        {p.ticker: p.current_price_usd for p in port_bundle.positions},
    )

    rt_eng = RiskTimingEngine()
    rt_bundle = rt_eng.build_risk_and_consultative_timing(
        portfolio=port_bundle,
        equities=eq_list,
        cryptos=cr_dict,
        fed_funds_rate_pct=fed_funds_pct,
        vix_current=vix_curr,
        capital_gains_tax_rate_pct=tax_rate_pct,
        backtest_metrics=backtest_res,
        live_adtv_map_m=live_adtv,
    )

    return {
        "macro": macro_bundle,
        "portfolio": port_bundle,
        "equities": eq_list,
        "cryptos": cr_dict,
        "eq_filings": eq_filings,
        "cr_filings": cr_filings,
        "geo_matrix": geo_matrix,
        "micro_events": micro_events,
        "stock_screener": stk_screener,
        "crypto_screener": cr_screener,
        "risk_timing": rt_bundle,
        "backtest": backtest_res,
        "fx_usd_brl": fx_usd_brl,
        "vix_current": vix_curr,
        "fed_funds_rate_pct": fed_funds_pct,
    }


def main() -> None:
    inject_clean_css()

    if "refresh_token" not in st.session_state:
        st.session_state["refresh_token"] = 0
    if "deep_dive_ticker" not in st.session_state:
        st.session_state["deep_dive_ticker"] = "NVDA"
    if "ai_chat_history" not in st.session_state:
        st.session_state["ai_chat_history"] = []
    if "ai_conversation_id" not in st.session_state:
        st.session_state["ai_conversation_id"] = None
    if "ai_pending_prompt" not in st.session_state:
        st.session_state["ai_pending_prompt"] = None
    if "ai_pdf_cache" not in st.session_state:
        st.session_state["ai_pdf_cache"] = {}
    if "det_pdf_cache" not in st.session_state:
        st.session_state["det_pdf_cache"] = {}

    port_eng_live = PortfolioEngine()
    db_assets_live = port_eng_live.get_all_assets()
    tx_count_live = len(port_eng_live.get_transactions())
    db_sig = "|".join(
        f"{a['ticker']}:{a['target_weight_pct']:.2f}:{a['avg_buy_price']:.2f}:{int(a['ltv_turbo_eligible'])}"
        for a in db_assets_live
    ) + f"|tx:{tx_count_live}"

    # Lean sidebar: Base capital, Tax-Drag rate, FX display, Live Refresh & 1-Click Master PDF
    with st.sidebar:
        st.markdown("### 🏛️ Master Report Controls")
        capital_usd = st.number_input(
            "Base Calculation Capital (USD)",
            min_value=10_000.0,
            max_value=100_000_000.0,
            value=100_000.0,
            step=10_000.0,
            format="%.0f",
        )
        tax_rate_pct = st.number_input(
            "Capital Gains Tax Rate (%) — Tax-Drag",
            min_value=0.0,
            max_value=35.0,
            value=15.0,
            step=0.5,
            format="%.1f",
            help="Used deterministically to compute Tax-Drag Hurdle Rate (e.g., 15% BR foreign/crypto or US LTCG).",
        )
        display_ccy = st.selectbox(
            "UI Display Currency",
            ["USD", "BRL (Live FX)"],
            index=0,
            key="sidebar_display_ccy",
        )
        if st.button("🔄 Refresh Live Quotes & Recalculate PDF", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.session_state["ai_pdf_cache"] = {}
            st.session_state["det_pdf_cache"] = {}
            st.session_state["refresh_token"] += 1
            st.rerun()

    with st.spinner("Loading 360° Quantitative & Forensic Engine Bundle..."):
        bundle = load_full_intelligence_bundle(
            capital_usd=capital_usd,
            db_sig=db_sig,
            refresh_token=st.session_state["refresh_token"],
            tax_rate_pct=tax_rate_pct,
        )

    macro: MacroDataBundle = bundle["macro"]
    portfolio: PortfolioOverviewBundle = bundle["portfolio"]
    equities: List[EquityFullAnalysis] = bundle["equities"]
    cryptos: Dict[str, CryptoFullProfile] = bundle["cryptos"]
    risk_timing: RiskLeverageTimingBundle = bundle["risk_timing"]
    backtest_res: Dict[str, Any] = bundle.get("backtest") or {}
    fx_usd_brl: float = float(bundle.get("fx_usd_brl") or 5.85)
    ccy_mult = fx_usd_brl if display_ccy.startswith("BRL") else 1.0
    ccy_prefix = "R$" if display_ccy.startswith("BRL") else "$"

    with st.sidebar:
        sidebar_dl_placeholder = st.empty()
        st.markdown(
            f"**Live Macro Telemetry:** VIX `{bundle.get('vix_current', 18.4):.2f}` | "
            f"US10Y `{macro.yield_curve.get('us10y_pct', 4.42):.2f}%` | "
            f"Fed `{bundle.get('fed_funds_rate_pct', 4.25):.2f}%` | "
            f"USD/BRL `{fx_usd_brl:.2f}`"
        )
        st.caption(
            f"Last synchronization: **{macro.timestamp}** | "
            f"**{len(portfolio.positions)} Holdings** in SQLite Portfolio."
        )

    st.markdown(
        f"""
        <div class="inst-banner">
            <h1>🏛️ 360° MASTER REPORT HUB &amp; ACTIVE INTERVENTION MODULES</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "📄 1. Master Consolidated Report (.PDF)",
        "⚙️ 2. Portfolio Manager (SQLite CRUD)",
        "🔎 3. Single-Asset Deep Dive (Stock & Crypto Picker)",
        "🎛️ 4. Simulators (Inflow & LTV) & Notifier (ON/OFF)",
        "🤖 5. AI Portfolio Analyst",
    ])

    gemini_ready = is_gemini_configured()
    active_master_pdf_bytes: Optional[bytes] = None

    # ==========================================================================
    # TAB 1: MASTER CONSOLIDATED REPORT CENTRAL EMISSION (.PDF)
    # ==========================================================================
    with tabs[0]:
        render_kpi_card(
            "Portfolio Structural Allocation",
            f"{portfolio.total_crypto_pct:.0f}% Crypto  |  {portfolio.total_hard_assets_pct:.0f}% Hard-Assets",
            f"Active Monitoring of {len(portfolio.positions)} Portfolio Positions",
            tone="blue",
        )

        st.markdown("<div style='height:0.65rem;'></div>", unsafe_allow_html=True)

        include_ai_master = st.toggle(
            "✨ AI-Powered Master Report (All Insights, Matrices, Events & Portfolio Dossiers)",
            value=gemini_ready,
            disabled=not gemini_ready,
            key="toggle_include_ai_pdf",
            help=(
                "Automatically hydrates SEC EDGAR & Crypto protocol dossiers for your entire active portfolio "
                "(7d cache) and synthesizes ALL qualitative insights, geopolitical/macro matrices, moats, "
                "calls Q&A, M&A, and live micro events via Gemini (24h cache), while keeping 100% of "
                "financial calculations deterministic in Python."
                if gemini_ready
                else "Configure GEMINI_API_KEY in .env to enable automatic full-portfolio AI insights and dossiers."
            ),
        )
        if not gemini_ready:
            st.caption("ℹ️ `GEMINI_API_KEY` not detected in `.env` — Master PDF runs in 100% deterministic mode.")

        force_refresh_insights = False
        force_refresh_filings = False
        is_economic_mode = False
        if include_ai_master and gemini_ready:
            ai_profile = st.radio(
                "AI Execution Profile",
                [
                    "Economic / Fast Batch (Use Cached/Static Filings + AI Matrices — Saves Free-Tier Quota)",
                    "Full Deep Hydration (Auto-Fetch Fresh Filings Across Portfolio + AI Matrices)",
                ],
                index=0,
                horizontal=True,
                key="ai_exec_profile_radio",
            )
            is_economic_mode = ai_profile.startswith("Economic")

            ai_ctrl_c1, ai_ctrl_c2 = st.columns(2)
            with ai_ctrl_c1:
                if st.button(
                    "🧠 Regenerate All AI Insights (Matrices, Moats, Events & Thesis)",
                    key="btn_regen_all_ai_insights",
                    use_container_width=True,
                ):
                    force_refresh_insights = True
                    clear_ai_master_insights_cache()
                    st.session_state["ai_pdf_cache"] = {}
            with ai_ctrl_c2:
                if st.button(
                    "📑 Force Re-Fetch All Portfolio SEC & Crypto Filings",
                    key="btn_refetch_all_filings",
                    use_container_width=True,
                ):
                    force_refresh_filings = True
                    force_refresh_insights = True
                    clear_ai_master_insights_cache()
                    st.session_state["ai_pdf_cache"] = {}

        ai_bundle: Optional[Dict[str, Any]] = None
        ai_exec_summary: Optional[Dict[str, Any]] = None
        if include_ai_master and gemini_ready:
            ai_cache_key = f"{db_sig}|{st.session_state['refresh_token']}|{capital_usd:.0f}|{tax_rate_pct:.1f}|{int(is_economic_mode)}"
            cached_entry = None if (force_refresh_insights or force_refresh_filings) else st.session_state["ai_pdf_cache"].get(ai_cache_key)
            if cached_entry is None:
                with st.status("Running Full-Portfolio AI Intelligence & Compiling 360° Master PDF...", expanded=True) as status_box:
                    prog_bar = st.progress(0.0)
                    prog_label = st.empty()

                    def _on_ai_progress(msg: str, frac: float) -> None:
                        prog_bar.progress(max(0.0, min(1.0, float(frac))))
                        prog_label.caption(msg)

                    ai_bundle = AIReportOrchestrator().build_complete_ai_master_bundle(
                        macro=macro,
                        portfolio=portfolio,
                        equities=equities,
                        cryptos=cryptos,
                        risk_timing=risk_timing,
                        portfolio_sig=db_sig,
                        force_refresh_insights=force_refresh_insights,
                        force_refresh_filings=force_refresh_filings,
                        skip_filing_hydration=(is_economic_mode and not force_refresh_filings),
                        progress_cb=_on_ai_progress,
                    )
                    if ai_bundle and ai_bundle.get("enabled"):
                        prog_label.caption("Compiling 7-Section Vector PDF with AI Insights & Portfolio Dossiers...")
                        ai_exec_summary = ai_bundle.get("executive_summary")
                        ai_pdf_exp = InstitutionalPDFExporter()
                        ai_pdf_bytes = ai_pdf_exp.generate_pdf_bytes(
                            macro=macro,
                            portfolio=portfolio,
                            equities=equities,
                            cryptos=cryptos,
                            eq_filings=ai_bundle.get("eq_filings") or bundle["eq_filings"],
                            cr_filings=ai_bundle.get("cr_filings") or bundle["cr_filings"],
                            geo_matrix=ai_bundle.get("geo_matrix") or bundle["geo_matrix"],
                            micro_events=ai_bundle.get("micro_events") or bundle["micro_events"],
                            stock_screener=bundle["stock_screener"],
                            crypto_screener=bundle["crypto_screener"],
                            risk_timing=risk_timing,
                            ai_executive_summary=ai_exec_summary,
                            ai_report_bundle=ai_bundle,
                        )
                        st.session_state["ai_pdf_cache"][ai_cache_key] = {
                            "ai_bundle": ai_bundle,
                            "summary": ai_exec_summary,
                            "pdf_bytes": ai_pdf_bytes,
                        }
                        active_master_pdf_bytes = ai_pdf_bytes
                        fh_info = ai_bundle.get("filings_hydration") or {}
                        if fh_info.get("hydrated_equities") or fh_info.get("hydrated_cryptos"):
                            load_full_intelligence_bundle.clear()
                        status_box.update(
                            label="✅ AI-Powered 360° Master Report Ready (All Qualitative Sections & Portfolio Dossiers Hydrated)",
                            state="complete",
                            expanded=False,
                        )
                    else:
                        status_box.update(
                            label="⚠️ Gemini API unreachable — fell back gracefully to deterministic Master PDF.",
                            state="error",
                            expanded=False,
                        )
            else:
                ai_bundle = cached_entry.get("ai_bundle")
                ai_exec_summary = cached_entry.get("summary")
                active_master_pdf_bytes = cached_entry.get("pdf_bytes")

        if active_master_pdf_bytes is None:
            det_cache_key = f"{db_sig}|{st.session_state['refresh_token']}|{capital_usd:.0f}|{tax_rate_pct:.1f}"
            det_pdf_bytes = st.session_state["det_pdf_cache"].get(det_cache_key)
            if det_pdf_bytes is None:
                with st.spinner("Compiling 360° Deterministic Master Report (.PDF)..."):
                    det_pdf_bytes = InstitutionalPDFExporter().generate_pdf_bytes(
                        macro=macro,
                        portfolio=portfolio,
                        equities=equities,
                        cryptos=cryptos,
                        eq_filings=bundle["eq_filings"],
                        cr_filings=bundle["cr_filings"],
                        geo_matrix=bundle["geo_matrix"],
                        micro_events=bundle["micro_events"],
                        stock_screener=bundle["stock_screener"],
                        crypto_screener=bundle["crypto_screener"],
                        risk_timing=risk_timing,
                    )
                    st.session_state["det_pdf_cache"][det_cache_key] = det_pdf_bytes
            active_master_pdf_bytes = det_pdf_bytes

        with sidebar_dl_placeholder.container():
            st.download_button(
                label="📥 DOWNLOAD 360° MASTER REPORT (.PDF)",
                data=active_master_pdf_bytes,
                file_name="Master_Institutional_Report_360.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
                key="btn_sidebar_master_pdf",
            )

        c_dl1, c_dl2 = st.columns([2, 1])
        with c_dl1:
            st.download_button(
                label="📥 DOWNLOAD 360° MASTER REPORT (.PDF — ALL 7 SECTIONS)",
                data=active_master_pdf_bytes,
                file_name="Master_Institutional_Report_360.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
                key="btn_main_master_pdf",
            )
        with c_dl2:
            if st.button("🔄 Recalculate with Live Market Quotes", use_container_width=True, key="btn_main_refresh"):
                st.cache_data.clear()
                st.session_state["ai_pdf_cache"] = {}
                st.session_state["det_pdf_cache"] = {}
                st.session_state["refresh_token"] += 1
                st.rerun()

        if ai_bundle and ai_bundle.get("enabled"):
            with st.expander("🧠 AI Insights Coverage & Executive Thesis Preview", expanded=False):
                sec_status = ai_bundle.get("section_status") or {}
                fh_info = ai_bundle.get("filings_hydration") or {}
                gen_ts = ai_bundle.get("generated_at")
                gen_str = (
                    datetime.datetime.fromtimestamp(float(gen_ts)).strftime("%Y-%m-%d %H:%M:%S")
                    if gen_ts
                    else "N/A"
                )
                cov_rows = [
                    {"Pipeline / Section": k, "Mode": v}
                    for k, v in sec_status.items()
                ]
                cov_rows.append({
                    "Pipeline / Section": "portfolio_sec_filings_hydrated",
                    "Mode": f"{fh_info.get('total_ai_equities', len(ai_bundle.get('eq_filings') or []))}/{len(equities)} AI Dossiers",
                })
                cov_rows.append({
                    "Pipeline / Section": "portfolio_crypto_dossiers_hydrated",
                    "Mode": f"{fh_info.get('total_ai_cryptos', len(ai_bundle.get('cr_filings') or []))}/{len(cryptos)} AI Dossiers",
                })
                render_clean_table(pd.DataFrame(cov_rows), badge_cols=["Mode"])
                st.caption(
                    f"Models used: `{', '.join(ai_bundle.get('models_used') or []) or 'gemini-4-hydrogen'}` | "
                    f"Generated: `{gen_str}` | Cache Hit: `{bool(ai_bundle.get('from_cache'))}`"
                )
                if ai_exec_summary:
                    st.markdown(f"**Macro Regime Thesis:** {ai_exec_summary.get('macro_regime_thesis', '')}")
                    st.markdown(f"**Cross-Asset Risk & LTV Synthesis:** {ai_exec_summary.get('cross_asset_risk_synthesis', '')}")
                    for item in ai_exec_summary.get("key_actionable_priorities", []):
                        st.markdown(f"- {item}")

        render_section_header(
            "Internal Architecture of the 360° Master Report (.PDF)",
            "Single high-density PDF file structured across 7 chapters without losing any metric, methodology, or vector graph",
        )

        df_sections = pd.DataFrame([
            {
                "PDF Section": "Section 1",
                "Chapter Title in Master Report": "Global Macroeconomics, Cycles, Tech Disruptions & Geopolitics",
                "Analytical Content & Included Charts": "Lagging Indicators (GDP, CPI, Fed Funds, Debt/GDP, U3), Sahm's Rule paired with Payroll & ICSA, SOS Indicator, Services vs Mfg PMI, 10Y-2Y Yield Curve, M2 vs DXY, Geopolitical Impact Matrix (10-K), Industry Tech Disruptions & Macro Sensitivity Matrix by Hard-Asset.",
            },
            {
                "PDF Section": "Section 2",
                "Chapter Title in Master Report": "Portfolio Analytics, Faithful Look-Through, Forensics & Forward Valuation",
                "Analytical Content & Included Charts": "Portfolio Positions, Strict Look-Through of owned equities + ETF Residual Basket, Forensic Accounting without Altman Z (Part A & Part B 5-column split), 12-KPI CAGR Matrix (Part A & B), All 8 Forward (NTM) Valuation Methods (NTM DCF, Reverse DCF, Owner Earnings, Forward Multiples, EVA, Forward PEGY, Magic Formula & SOTP), Portfolio Banks (JPM & NU).",
            },
            {
                "PDF Section": "Section 3",
                "Chapter Title in Master Report": "Crypto On-Chain Analytics & DeFi State of the Union",
                "Analytical Content & Included Charts": "On-Chain Cycle (MVRV Z, NUPL, aSOPR, Pi Cycle, 200W SMA), Mining Health (Hash Ribbon & MMC), Exchange Flows (Inflow, CDD, Stablecoins, HODL Waves), Tokenomics (NVM, NVT GC, P/F, TVL, Protocol Real Earnings, Real Yield), Cycle Rotation Compass (BTC -> ETH -> DeFi) & Tech Narrative Shifts (On-Chain Fundamental Synthesis).",
            },
            {
                "PDF Section": "Section 4",
                "Chapter Title in Master Report": "In-Depth Corporate Forensic Dossier (SEC 10-K/10-Q/20-F, Porter, Calls Q&A & M&As)",
                "Analytical Content & Included Charts": "Big Four Audit & SOX 404(b), MD&A Breakdown (Volume, Price, FX, Backlog, CAPEX), Item 1A Risks, Forensic Footnotes (Litigation, SBC, ASC 606, Debt), Moats (4 Pillars), Porter's 5 Forces, Common Size vs Peers, Signal vs Noise Filter in Earnings Calls (CEO/CFO statements and Q&A clashes), Full M&A Dossier, Dilution, Goodwill & Antitrust + Form 8-K/Form 4 Insider Trading.",
            },
            {
                "PDF Section": "Section 5",
                "Chapter Title in Master Report": "Crypto Protocols Technical Dossier (Whitepapers, Core Devs & Unlocks 30/60/90d)",
                "Analytical Content & Included Charts": "Technical Synthesis of White Papers, Consensus Architecture and Value Accrual, GitHub Engineering (4w Commits & Active Devs), DeepDAO Governance, Token Sniffer & Audit Reports, Insider Core Dev/Founder Signals, Network Upgrades (EIPs/PIPs) & Forensic Unlock Schedule (30/60/90 days) with Theoretical Post-Dilution Price.",
            },
            {
                "PDF Section": "Section 6",
                "Chapter Title in Master Report": "Executive Opportunity Radar — Quantitative & Forensic Screener",
                "Analytical Content & Included Charts": "Global Stocks Funnel (5 Strict Filters: Sloan, CFO/EBITDA, ROIC vs WACC, Solvency CR & Interest Coverage, Reverse DCF & Forward PEGY) and Crypto Funnel (Supply >= 65%, Unlocks <= 2.5%/mo, Sniffer >= 85, Active Devs >= 40 & Real Earnings > 0, MVRV Z <= 2.0).",
            },
            {
                "PDF Section": "Section 7",
                "Chapter Title in Master Report": "Risk Governance, Convex LTV Leverage, ADTV Liquidity & Advisory Timing",
                "Analytical Content & Included Charts": "Sharpe, Sortino, Calmar Ratio, VIX, ADTV Liquidity (<1%), Convex LTV Panel (IBKR Box Spreads + Aave V3 Stress-Test), The 7 Advisory Timing Rules by Asset Class, Advisory Positioning of Portfolio Holdings, Shannon Inflow Rebalancing Qualification & Tax-Drag Hurdle Rate.",
            },
        ])
        render_clean_table(df_sections)

        render_section_header(
            "Interactive Visual Intelligence Dashboard (Live Charts & Real Backtest)",
            "All 15 Plotly analytical charts wired directly to live macro, equity, banking, on-chain, and 3-year historical portfolio engines",
        )
        viz_tabs = st.tabs([
            "🌍 Macro & Yield Curve",
            "🏛️ Equities Valuation & Banks",
            "₿ Crypto On-Chain Cycle",
            "📈 Real Historical Backtest",
        ])
        with viz_tabs[0]:
            st.plotly_chart(build_macro_comprehensive_chart(macro), use_container_width=True)
            st.plotly_chart(build_yield_curve_and_icsa_chart(macro), use_container_width=True)
        with viz_tabs[1]:
            st.plotly_chart(build_multi_method_valuation_chart(equities), use_container_width=True)
            st.plotly_chart(build_banks_ptbv_vs_roe_scatter(equities), use_container_width=True)
        with viz_tabs[2]:
            btc_or_first = cryptos.get("BTC-USD") or (next(iter(cryptos.values())) if cryptos else None)
            if btc_or_first is not None:
                cr_c1, cr_c2 = st.columns(2)
                with cr_c1:
                    st.plotly_chart(build_btc_asopr_chart(btc_or_first), use_container_width=True)
                    st.plotly_chart(build_crypto_mvrv_nupl_chart(btc_or_first), use_container_width=True)
                with cr_c2:
                    st.plotly_chart(build_btc_picycle_200w_hashribbon_mmc_chart(btc_or_first), use_container_width=True)
                    st.plotly_chart(build_crypto_nvm_and_cdd_chart(btc_or_first), use_container_width=True)
            else:
                st.info("No portfolio cryptoassets active for on-chain cycle charting.")
        with viz_tabs[3]:
            b_k1, b_k2, b_k3, b_k4, b_k5 = st.columns(5)
            with b_k1:
                render_kpi_card("Portfolio 3Y CAGR", f"{backtest_res.get('portfolio_cagr_pct', 0.0):+.2f}%", f"Vol: {backtest_res.get('annualized_vol_pct', 0.0):.1f}% p.a.", tone="emerald")
            with b_k2:
                render_kpi_card("Sharpe Ratio", f"{backtest_res.get('sharpe_ratio', 0.0):.2f}", f"vs Rf {bundle.get('fed_funds_rate_pct', 4.25):.2f}%", tone="blue")
            with b_k3:
                render_kpi_card("Sortino Ratio", f"{backtest_res.get('sortino_ratio', 0.0):.2f}", "Downside Deviation Adjusted", tone="purple")
            with b_k4:
                render_kpi_card("Max Drawdown", f"-{backtest_res.get('max_drawdown_pct', 0.0):.2f}%", f"Calmar: {backtest_res.get('calmar_ratio', 0.0):.2f}x", tone="amber")
            with b_k5:
                render_kpi_card("Benchmarks (CAGR)", f"SPY {backtest_res.get('spy_cagr_pct', 0.0):+.1f}%", f"BTC {backtest_res.get('btc_cagr_pct', 0.0):+.1f}% | {backtest_res.get('period_days', 0)}d", tone="blue")
            st.plotly_chart(build_portfolio_equity_curve_chart(backtest_res), use_container_width=True)

    # ==========================================================================
    # TAB 2: DYNAMIC PORTFOLIO MANAGER (SQLITE CRUD)
    # ==========================================================================
    with tabs[1]:
        render_section_header(
            "Dynamic Portfolio Manager (Persistent SQLite CRUD)",
            "Add, edit, or remove portfolio assets; every change automatically recalculates the 360° Master Report (.PDF)",
        )

        total_w = portfolio.target_weight_sum_pct
        is_100 = getattr(portfolio, 'is_weight_valid_100', getattr(portfolio, 'weight_sum_is_valid_100', True))
        bar_col = "#10B981" if is_100 else "#F59E0B"
        st.markdown(
            f"""
            <div class="insight-callout" style="border-left-color:{bar_col};">
                <strong>Current SQLite Target Weight Sum: {total_w:.2f}%</strong> — {html.escape(portfolio.weight_validation_message)}
                <div style="width:100%; background:#1E293B; height:10px; border-radius:5px; margin-top:6px; overflow:hidden;">
                    <div style="width:{min(100.0, total_w):.1f}%; background:{bar_col}; height:100%;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_crud1, col_crud2 = st.columns([2, 1])
        with col_crud1:
            with st.form("form_upsert_asset", clear_on_submit=False):
                st.markdown("##### ➕ Add New Asset or Edit Existing Asset")
                f1, f2, f3 = st.columns(3)
                with f1:
                    in_ticker = st.text_input("Official Ticker (e.g., NVDA, COST, BTC-USD)", value="NVDA")
                    in_name = st.text_input("Company / Protocol / ETF Name", value="NVIDIA Corporation")
                with f2:
                    in_class = st.selectbox("Asset Class", ["Stock", "ETF", "Crypto", "Altcoin"])
                    in_sector = st.selectbox(
                        "Framework Sector Vertical",
                        [
                            "High-Growth Tech & AI Infra",
                            "Big Tech Cash Cow / Monopoly",
                            "Global Bank / Financial Institution",
                            "Defensive Retail (SSS)",
                            "Cyclical / Defense / Industrial",
                            "Index ETF (S&P 500 / Nasdaq / Sector)",
                            "2x Leveraged ETF (QLD)",
                            "Bitcoin Sovereign PoW Reserve",
                            "Smart Contract Layer-1 (ETH/SOL)",
                            "DeFi Blue-Chip / Real Yield (PENDLE/MKR/UNI)",
                            "Oracle / Interoperability (LINK)",
                        ],
                    )
                with f3:
                    in_weight = st.number_input("Target Portfolio Weight (%)", min_value=0.10, max_value=50.0, value=5.0, step=0.25)
                    in_avg_px = st.number_input("Average Purchase Price (USD)", min_value=0.0, max_value=500_000.0, value=88.0, step=1.0)
                    in_ltv = st.checkbox("Eligible as LTV Turbo Collateral?", value=True)

                in_role = st.text_input(
                    "Structural Portfolio Role",
                    value="AI GPU computing monopoly and CUDA accelerated computing infrastructure.",
                )
                if st.form_submit_button("💾 Save / Update Asset in SQLite", use_container_width=True, type="primary"):
                    port_eng_live.upsert_asset(
                        ticker=in_ticker,
                        name=in_name,
                        asset_class_ui=in_class,
                        sector_ui=in_sector,
                        target_weight_pct=in_weight,
                        avg_buy_price=in_avg_px,
                        ltv_turbo_eligible=in_ltv,
                        role_description=in_role,
                    )
                    st.cache_data.clear()
                    st.session_state["refresh_token"] += 1
                    st.success(f"Asset {in_ticker.upper()} successfully saved in SQLite!")
                    st.rerun()

        with col_crud2:
            st.markdown("##### 🗑️ Remove Asset or Normalize to 100%")
            all_tks = [p.ticker for p in portfolio.positions]
            del_tk = st.selectbox("Select Asset to Remove", options=all_tks)
            if st.button("🗑️ Remove Selected Asset", use_container_width=True):
                port_eng_live.delete_asset(del_tk)
                st.cache_data.clear()
                st.session_state["refresh_token"] += 1
                st.warning(f"Asset {del_tk} removed from portfolio.")
                st.rerun()

            st.markdown("<hr style='border-color:#334155;'>", unsafe_allow_html=True)
            st.caption("If the sum of target weights differs from 100.00%, click below to rescale proportionally:")
            if st.button("⚖️ Normalize Weights Automatically to 100.00%", use_container_width=True):
                port_eng_live.normalize_weights_to_100()
                st.cache_data.clear()
                st.session_state["refresh_token"] += 1
                st.success("Weights normalized exactly to 100.00%!")
                st.rerun()

        render_section_header(
            f"Active Portfolio Holdings Ledger ({len(portfolio.positions)} Assets in SQLite — {display_ccy})",
            "Concise 7-column table for monitoring Weights, Cost Basis, Spot Quotes, P&L, and LTV Collateral",
        )
        df_ledger = pd.DataFrame([
            {
                "Ticker": p.ticker,
                "Asset": p.name,
                "Category": p.category,
                "Target vs. Current Weight": f"{p.target_weight_pct:.2f}% (Current {p.current_weight_pct:.2f}% | Drift {p.weight_drift_pp:+.2f}pp)",
                f"Avg Buy -> Spot ({display_ccy.split()[0]})": f"{ccy_prefix}{p.avg_buy_price_usd * ccy_mult:,.2f} -> {ccy_prefix}{p.current_price_usd * ccy_mult:,.2f} ({ccy_prefix}{p.allocated_usd * ccy_mult:,.0f})",
                "Unrealized P&L": f"{p.pnl_pct:+.1f}% ({ccy_prefix}{p.pnl_usd * ccy_mult:+,.0f})",
                "LTV Collateral": "YES" if p.ltv_turbo_eligible else "NO",
            }
            for p in portfolio.positions
        ])
        render_clean_table(df_ledger, badge_cols=["LTV Collateral"])

        st.plotly_chart(build_portfolio_weight_gauge_chart(total_w), use_container_width=True)

        tx_list_all = port_eng_live.get_transactions()
        excel_bytes = build_institutional_excel_bytes(
            portfolio=portfolio,
            equities=equities,
            cryptos=cryptos,
            risk_timing=risk_timing,
            transactions=tx_list_all,
            backtest=backtest_res,
        )
        st.download_button(
            label="📊 Export Auditable Multi-Sheet Institutional Workbook (.XLSX)",
            data=excel_bytes,
            file_name="Institutional_Portfolio_Workbook.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="btn_export_xlsx",
        )

        with st.expander("📒 Real Custody Transactions Ledger (`transactions_ledger`) & CSV Broker Import", expanded=False):
            led_summary = port_eng_live.compute_ledger_summary({p.ticker: p.current_price_usd for p in portfolio.positions})
            lk1, lk2, lk3, lk4 = st.columns(4)
            with lk1:
                render_kpi_card("Custody Market Value", f"{ccy_prefix}{led_summary['total_market_value_usd'] * ccy_mult:,.2f}", f"{led_summary['total_transactions']} Logged Events", tone="blue")
            with lk2:
                render_kpi_card("Unrealized Custody P&L", f"{ccy_prefix}{led_summary['total_unrealized_pnl_usd'] * ccy_mult:+,.2f}", f"Cost Basis: {ccy_prefix}{led_summary['total_cost_basis_usd'] * ccy_mult:,.0f}", tone="emerald")
            with lk3:
                render_kpi_card("Realized P&L (Sells)", f"{ccy_prefix}{led_summary['total_realized_pnl_usd'] * ccy_mult:+,.2f}", "Weighted Avg Cost Method", tone="purple")
            with lk4:
                render_kpi_card("Dividends & Staking Income", f"{ccy_prefix}{led_summary['total_income_usd'] * ccy_mult:+,.2f}", "Cumulative Cash Yield", tone="amber")

            tx_c1, tx_c2 = st.columns([2, 1])
            with tx_c1:
                with st.form("form_add_tx", clear_on_submit=True):
                    st.markdown("##### ➕ Record Transaction (`BUY` / `SELL` / `DIVIDEND` / `STAKING`)")
                    tc1, tc2, tc3 = st.columns(3)
                    with tc1:
                        tx_dt = st.text_input("Date (YYYY-MM-DD)", value=datetime.date.today().isoformat())
                        tx_tk = st.text_input("Ticker", value=all_tks[0] if all_tks else "NVDA")
                    with tc2:
                        tx_tp = st.selectbox("Type", ["BUY", "SELL", "DIVIDEND", "STAKING"])
                        tx_qt = st.number_input("Quantity (or 1 for Cash Div)", min_value=0.0001, value=1.0, step=1.0, format="%.4f")
                    with tc3:
                        tx_px = st.number_input("Unit Price / Cash (USD)", min_value=0.0, value=100.0, step=1.0)
                        tx_fee = st.number_input("Fee (USD)", min_value=0.0, value=0.0, step=0.5)
                    tx_notes = st.text_input("Notes (Optional)", value="")
                    if st.form_submit_button("💾 Record Transaction in SQLite", use_container_width=True, type="primary"):
                        port_eng_live.add_transaction(tx_dt, tx_tk, tx_tp, tx_qt, tx_px, tx_fee, tx_notes)
                        st.cache_data.clear()
                        st.session_state["refresh_token"] += 1
                        st.success(f"Recorded {tx_tp} for {tx_tk.upper()}.")
                        st.rerun()
            with tx_c2:
                st.markdown("##### 📥 CSV Broker Import")
                csv_mode = st.radio("CSV Target", ["Holdings (`portfolio_assets`)", "Transactions (`transactions_ledger`)"], key="csv_imp_mode")
                csv_file = st.file_uploader("Upload CSV file", type=["csv"], key="csv_imp_uploader")
                if csv_file is not None and st.button("⬆️ Import CSV into SQLite", use_container_width=True, key="btn_imp_csv"):
                    raw_csv = csv_file.read()
                    if csv_mode.startswith("Holdings"):
                        n_ok, errs = port_eng_live.import_assets_from_csv(raw_csv)
                    else:
                        n_ok, errs = port_eng_live.import_transactions_from_csv(raw_csv)
                    st.cache_data.clear()
                    st.session_state["refresh_token"] += 1
                    st.success(f"Imported {n_ok} row(s)." + (f" Warnings: {len(errs)}" if errs else ""))
                    st.rerun()

            if tx_list_all:
                render_clean_table(pd.DataFrame(tx_list_all))
                del_tx_id = st.selectbox("Select Transaction ID to Remove", options=[t["id"] for t in tx_list_all], key="del_tx_sel")
                if st.button("🗑️ Delete Transaction", key="btn_del_tx"):
                    port_eng_live.delete_transaction(int(del_tx_id))
                    st.cache_data.clear()
                    st.session_state["refresh_token"] += 1
                    st.rerun()

    # ==========================================================================
    # TAB 3: SINGLE-ASSET DEEP DIVE (ON-DEMAND STOCK & CRYPTO PICKER)
    # ==========================================================================
    with tabs[2]:
        render_section_header(
            "Single-Asset Deep Dive Analyzer (Stock, ETF & Crypto Picker)",
            "Search any market asset or portfolio holding to generate an instant institutional audit + 1-Click Individual PDF Dossier",
        )

        col_s1, col_s2, col_s3 = st.columns([2, 2, 1])
        with col_s1:
            typed_tk = st.text_input(
                "Enter any Ticker (e.g., NVDA, ASML, TSM, MELI, COST, LLY, JPM, NU, BTC, ETH, PENDLE, LINK, SOL)",
                value=st.session_state["deep_dive_ticker"],
            )
        with col_s2:
            quick_pick = st.selectbox(
                "Or quickly pick a Portfolio / Watchlist Asset:",
                options=[
                    "NVDA", "AAPL", "MSFT", "ASML", "TSM", "JPM", "MELI", "AVGO", "MA", "NU",
                    "BTC-USD", "ETH-USD", "PENDLE-USD", "LINK-USD", "MKR-USD", "UNI-USD",
                    "SPY", "QQQ", "QLD", "ITA", "COST", "LLY", "SOL-USD", "AAVE-USD",
                ],
                index=0,
            )
        with col_s3:
            st.markdown("<div style='height:1.72rem;'></div>", unsafe_allow_html=True)
            if st.button("🔎 Run Deep Dive", use_container_width=True, type="primary"):
                st.session_state["deep_dive_ticker"] = typed_tk.strip().upper() or quick_pick

        active_dd_tk = typed_tk.strip().upper() if typed_tk.strip() else quick_pick
        dd_eng = DeepDiveEngine(risk_free_rate_pct=macro.yield_curve.get("us10y_pct", 4.42))
        dd_res: DeepDiveResultBundle = dd_eng.analyze_single_ticker(
            user_ticker=active_dd_tk,
            portfolio=portfolio,
        )
        pdf_exp_dd = InstitutionalPDFExporter()
        dd_pdf_bytes = pdf_exp_dd.generate_deep_dive_pdf_bytes(dd_res)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            render_kpi_card(
                f"Analyzed Asset ({dd_res.asset_class})",
                dd_res.normalized_ticker,
                dd_res.framework_category_label,
                tone="blue",
            )
        with d2:
            render_kpi_card(
                "Forward Sovereign Multiple",
                dd_res.sovereign_multiple_value,
                dd_res.sovereign_multiple_status,
                tone="emerald",
            )
        with d3:
            render_kpi_card(
                "5-Filter Funnel Score",
                f"{dd_res.screener_score_0_100} / 100 pts",
                dd_res.regime_classification.split("—")[0].strip(),
                tone="purple",
            )
        with d4:
            port_status_str = "IN CURRENT PORTFOLIO" if dd_res.in_current_portfolio else "WATCHLIST (EXTERNAL)"
            render_kpi_card(
                "Portfolio Status",
                port_status_str,
                "Individual PDF Dossier Ready",
                tone="amber",
            )

        st.markdown(
            f'<div class="insight-callout"><strong>Automated Advisory Verdict ({html.escape(dd_res.normalized_ticker)}):</strong> '
            f'{html.escape(dd_res.automated_consultative_verdict)}</div>',
            unsafe_allow_html=True,
        )

        st.download_button(
            label=f"📥 DOWNLOAD INDIVIDUAL DEEP DIVE DOSSIER FOR {dd_res.normalized_ticker} (.PDF)",
            data=dd_pdf_bytes,
            file_name=f"Deep_Dive_Dossier_{dd_res.normalized_ticker}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
            key=f"dl_dd_{dd_res.normalized_ticker}",
        )

        render_section_header(
            f"Strict 5-Filter Funnel — {dd_res.normalized_ticker} (Score {dd_res.screener_score_0_100}/100)",
            "Step-by-step rigorous evaluation without text truncation and without Altman Z-Score",
        )
        df_funnel = pd.DataFrame([
            {
                "Step": f"Filter {s.step_number}",
                "Evaluated Metric": s.filter_name,
                "Calculated Value": s.calculated_value,
                "Strict Framework Rule": s.strict_criterion,
                "Status": "APPROVED" if s.passed else "REJECTED",
                "Diagnostic": f"{s.score_points}/{s.max_points} pts — {s.diagnostic_note}",
            }
            for s in dd_res.screener_filters_breakdown
        ])
        render_clean_table(df_funnel, badge_cols=["Status"])

        if dd_res.asset_class != "CRYPTO" and dd_res.equity_analysis:
            eq_i = dd_res.equity_analysis
            fh_i = eq_i.forensic_health
            vm_i = eq_i.valuation_methods
            render_section_header(
                f"Forward (NTM) Multi-Method Valuation & Forensic Health Summary — {dd_res.normalized_ticker}",
                "Spacious 5-column table for immediate executive reading",
            )
            df_dd_val = pd.DataFrame([
                {
                    "Spot Price & WACC": f"${eq_i.current_price:,.2f} (WACC {vm_i['wacc_capm_pct']:.2f}%)",
                    "Forward DCF (10% MoS)": f"${vm_i['dcf_fair_mos10_usd']:,.2f} ({vm_i['dcf_upside_pct']:+.1f}%)",
                    "Reverse DCF (g_impl vs g_fund)": f"g_impl {vm_i['reverse_dcf_g_impl_pct']:.1f}% vs g_fund {vm_i['g_fund_projected_pct']:.1f}%",
                    "Forward PEGY (NTM)": f"{vm_i['primary_pegy_label']} ({vm_i['primary_pegy_status']})",
                    "SOTP & ROIC vs WACC": f"SOTP ${vm_i['sotp_fair_price_usd']:,.2f} ({vm_i['sotp_upside_pct']:+.1f}%) | ROIC {fh_i['roic_goodwill_pct']:.1f}%",
                }
            ])
            render_clean_table(df_dd_val)

            ed_i = dd_res.equity_dossier
            qs_i = eq_i.qualitative_strategy
            sm_i = dd_res.corporate_signal_ma
            if ed_i or sm_i:
                render_section_header(
                    f"SEC Filings, Competitive Moat & M&A Dossier — {dd_res.normalized_ticker}",
                    "Full parity with 360° Master Report (10-K/10-Q/8-K, Footnotes, Porter's 5 Forces, Earnings Call Q&A & M&A)",
                )
                ma_deals_disp = (
                    (getattr(ed_i, "ma_and_strategic_deals", "") if ed_i else "")
                    or (sm_i.ma_and_strategic_deals if sm_i else "N/A")
                )
                ma_pay_disp = (
                    (getattr(ed_i, "ma_payment_and_goodwill", "") if ed_i else "")
                    or (f"{sm_i.payment_structure_and_dilution} | {sm_i.goodwill_and_impairment_risk}" if sm_i else "N/A")
                )
                rows_eq_doc = []
                if ed_i:
                    rows_eq_doc.extend([
                        {"Pillar": "SEC Filings & SOX 404(b)", "Details": f"{ed_i.filing_form_annual} | {ed_i.filing_form_quarterly} | {ed_i.auditor_firm} — {ed_i.auditor_opinion}"},
                        {"Pillar": "MD&A & Segment Margins", "Details": f"{ed_i.mda_growth_decomposition} | {ed_i.mda_segment_profitability} | CapEx: {ed_i.mda_capex_plan}"},
                        {"Pillar": "Forensic Footnotes (Lit / SBC / Debt)", "Details": f"SBC: {ed_i.footnote_sbc_impact} | Debt: {ed_i.footnote_debt_maturity_schedule} | ASC 606: {ed_i.footnote_revenue_recognition}"},
                    ])
                rows_eq_doc.extend([
                    {"Pillar": "Competitive Moat & Porter's 5 Forces", "Details": f"{qs_i['moat_classification']} | {qs_i['porter_5_forces']}"},
                    {"Pillar": "M&A, Strategic Deals & Goodwill", "Details": f"{ma_deals_disp} — Payment & Goodwill: {ma_pay_disp}"},
                    {"Pillar": "Earnings Call Guidance & Analyst Q&A", "Details": f"{sm_i.guidance_delta_summary if sm_i else 'N/A'} | Q&A: {sm_i.qa_analyst_clashes if sm_i else 'N/A'}" + (f" | Target: ${ed_i.analyst_target_mean_usd:,.2f} ({ed_i.analyst_recommendations_dist})" if ed_i else "")},
                ])
                render_clean_table(pd.DataFrame(rows_eq_doc))

            render_section_header(
                f"Interactive 5-Year Forensic, DuPont & Valuation Cockpit Charts — {dd_res.normalized_ticker}",
                "Live interactive Plotly visualization of historical quality, capital efficiency, and multi-method fair values",
            )
            st.plotly_chart(build_deep_dive_forensic_5y_chart(dd_res), use_container_width=True)
            dc1, dc2 = st.columns(2)
            with dc1:
                st.plotly_chart(build_deep_dive_dupont_and_margins_chart(dd_res), use_container_width=True)
            with dc2:
                st.plotly_chart(
                    build_deep_dive_valuation_cockpit_chart(dd_res, macro.yield_curve.get("us10y_pct", 4.42)),
                    use_container_width=True,
                )

        elif dd_res.asset_class == "CRYPTO" and dd_res.crypto_profile:
            cp_i = dd_res.crypto_profile
            cd_i = dd_res.crypto_dossier
            dv_i = dd_res.crypto_internal_dev
            tv_i = cp_i.tokenomics_valuation
            ss_i = cp_i.supply_structure
            om_i = cp_i.onchain_metrics
            render_section_header(
                f"On-Chain Cycle, Protocol Economics, Security & Governance — {dd_res.normalized_ticker}",
                "Full parity with 360° Master Report (Whitepaper, GitHub, Snapshot/DeepDAO, Audits, Hacks & 30/60/90d Unlocks)",
            )
            df_cr_full = pd.DataFrame([
                {"Pillar": "On-Chain Timing & Valuation", "Details": f"MVRV Z: {om_i['mvrv_z_score']:.2f} | NUPL: {om_i['nupl']:.2f} | aSOPR: {om_i['asopr']:.3f} | 200W SMA: {om_i['price_to_200w_sma_x']:.2f}x | NVT GC: {tv_i['nvt_golden_cross']:+.2f} | NVM: {tv_i['nvm_ratio']:.2f}"},
                {"Pillar": "Real Economy & Token Unlocks", "Details": f"Real Earnings: USD {tv_i['protocol_real_earnings_m']:+,.1f}M/yr | Real Yield: {tv_i['real_yield_pct']:+.2f}% | 30d Unlocks: {ss_i['unlock_pct_of_circ']:.2f}% Circ (Post-Dilution Px: ${ss_i['theoretical_post_unlock_price_usd']:,.2f})"},
                {"Pillar": "Whitepaper & Value Accrual", "Details": f"{cd_i.wp_title_author if cd_i else 'N/A'} — {cd_i.wp_value_accrual_mechanism if cd_i else ''}"},
                {"Pillar": "GitHub & Security Audits", "Details": f"Repos: {cd_i.github_core_repos if cd_i else 'N/A'} ({cd_i.github_commits_4w if cd_i else 0} commits/4w, {cd_i.github_active_devs_monthly if cd_i else 0} Devs) | Sniffer: {cd_i.token_sniffer_score if cd_i else 0}/100 | Audits: {cd_i.audit_firms if cd_i else 'N/A'} | Exploits: {cd_i.exploit_history if cd_i else 'N/A'}"},
                {"Pillar": "DAO Governance & Upgrades / Unlocks", "Details": f"{cd_i.deepdao_status if cd_i else ''} | Proposals: {cd_i.recent_governance_proposals if cd_i else ''} | Upgrades: {dv_i.upcoming_protocol_upgrades if dv_i else ''}"},
            ])
            render_clean_table(df_cr_full)

            render_section_header(
                f"Interactive On-Chain Gauges, GitHub Activity & Real Economics — {dd_res.normalized_ticker}",
                "Live cycle gauges combined with real GitHub commit velocity and protocol Real Earnings breakdown",
            )
            st.plotly_chart(build_crypto_onchain_gauges_chart(dd_res), use_container_width=True)
            st.plotly_chart(build_crypto_github_and_earnings_chart(dd_res), use_container_width=True)

        with st.expander("📄 Dynamic Filing Dossier Extractor (Ad-Hoc Assets / Custom PDFs)", expanded=False):
            st.caption(
                "💡 Note: All active holdings in your SQLite portfolio are already auto-hydrated in **Tab 1** "
                "and share `data_cache/custom_filings_cache.json`. Use this tool below to inspect non-portfolio candidates "
                "or upload custom local PDFs/earnings transcripts."
            )
            if not gemini_ready:
                st.info(
                    "ℹ️ `GEMINI_API_KEY` is not set in `.env`. Static verified filings remain active; "
                    "add your API key to `.env` to auto-fetch and structure full equity/crypto document suites."
                )
            default_kind_idx = 1 if dd_res.asset_class == "CRYPTO" else 0
            ex_c1, ex_c2 = st.columns([1.4, 1])
            with ex_c1:
                ex_kind = st.selectbox(
                    "Document Suite Type",
                    [
                        "Equity Full Suite (10-K/20-F + 10-Q + 8-K + Form 4/DEF 14A + Analysts)",
                        "Crypto Full Suite (Whitepaper + GitHub + Snapshot DAO + DeFiLlama Audits/Hacks)",
                    ],
                    index=default_kind_idx,
                    key="ex_doc_kind",
                )
            with ex_c2:
                ex_ticker = st.text_input("Target Ticker / Symbol", value=dd_res.normalized_ticker, key="ex_doc_ticker")

            if st.button(
                "🌐 Auto-Fetch ALL Official Docs & Extract Complete Dossier (No Download Needed)",
                key="btn_auto_fetch_dossier",
                type="primary",
                use_container_width=True,
                disabled=not gemini_ready,
            ):
                fil_eng = FilingsEngine()
                with st.spinner(f"Fetching complete multi-document suite for {ex_ticker.strip().upper()} and structuring via Gemini..."):
                    if ex_kind.startswith("Equity"):
                        auto_dossier, auto_msg, auto_meta = fil_eng.auto_fetch_and_extract_equity_dossier(
                            ticker=ex_ticker,
                            persist=True,
                        )
                    else:
                        auto_dossier, auto_msg, auto_meta = fil_eng.auto_fetch_and_extract_crypto_dossier(
                            symbol=ex_ticker,
                            persist=True,
                        )
                if auto_dossier is not None:
                    st.success(auto_msg)
                    if auto_meta.get("sources_fetched"):
                        st.caption("Sources Aggregated: " + " | ".join(auto_meta["sources_fetched"]))
                    if auto_meta.get("source_url"):
                        st.caption(f"Primary URL: {auto_meta['source_url']}")
                    st.cache_data.clear()
                    from dataclasses import asdict
                    d_map = asdict(auto_dossier)
                    df_ex = pd.DataFrame([{"Dossier Field": k, "Extracted Value": str(v)} for k, v in d_map.items()])
                    render_clean_table(df_ex)
                else:
                    st.warning(auto_msg)

            st.markdown("---")
            st.caption("Optional manual mode: upload a local PDF/TXT or paste custom filing/transcript text below.")
            ex_name = st.text_input("Company / Protocol Name (Optional for manual mode)", value="", key="ex_doc_name")
            uploaded_doc = st.file_uploader(
                "Upload PDF or TXT filing/whitepaper (optional)",
                type=["pdf", "txt"],
                key="ex_doc_uploader",
            )
            pasted_text = st.text_area(
                "Or paste filing / MD&A / Risk Factors / Whitepaper excerpt text",
                height=120,
                placeholder="Paste Item 1A, Item 7 MD&A, SOX 404(b), earnings release, or protocol tokenomics whitepaper text...",
                key="ex_doc_textarea",
            )
            if st.button("✨ Extract from Uploaded / Pasted Document", key="btn_extract_dossier"):
                pdf_payload = None
                txt_payload = pasted_text.strip() or None
                if uploaded_doc is not None:
                    raw_bytes = uploaded_doc.read()
                    if uploaded_doc.name.lower().endswith(".pdf"):
                        pdf_payload = raw_bytes
                    else:
                        txt_payload = raw_bytes.decode("utf-8", errors="replace")

                fil_eng = FilingsEngine()
                with st.spinner(f"Extracting structured dossier for {ex_ticker.strip().upper()}..."):
                    if ex_kind.startswith("Equity"):
                        dossier_out, status_msg = fil_eng.extract_equity_dossier_from_document(
                            ticker=ex_ticker,
                            company_name=ex_name,
                            raw_text=txt_payload,
                            pdf_bytes=pdf_payload,
                            persist=True,
                        )
                    else:
                        dossier_out, status_msg = fil_eng.extract_crypto_dossier_from_document(
                            symbol=ex_ticker,
                            name=ex_name,
                            raw_text=txt_payload,
                            pdf_bytes=pdf_payload,
                            persist=True,
                        )

                if dossier_out is not None:
                    st.success(status_msg)
                    st.cache_data.clear()
                    from dataclasses import asdict
                    d_map = asdict(dossier_out)
                    df_ex = pd.DataFrame([{"Dossier Field": k, "Extracted Value": str(v)} for k, v in d_map.items()])
                    render_clean_table(df_ex)
                else:
                    st.warning(status_msg)

    # ==========================================================================
    # TAB 4: INTERACTIVE SIMULATORS (SHANNON INFLOW & LTV STRESS-TEST) & NOTIFIER
    # ==========================================================================
    with tabs[3]:
        render_section_header(
            "1. Interactive Cash Inflow Simulator (Shannon's Demon Inflow Rebalancing)",
            "Calculate how to allocate fresh capital exclusively across accumulation-range assets below target weight (without selling winners)",
        )
        col_inf1, col_inf2 = st.columns([1, 2])
        with col_inf1:
            inflow_usd = st.number_input(
                "Fresh Cash Inflow Amount (USD)",
                min_value=500.0,
                max_value=5_000_000.0,
                value=10_000.0,
                step=1_000.0,
            )
        eligible_rows = [r for r in risk_timing.consultative_asset_timing_table if r.shannon_inflow_eligible]
        if not eligible_rows:
            eligible_rows = risk_timing.consultative_asset_timing_table[:5]
        total_w_elig = sum(r.target_weight_pct for r in eligible_rows) or 1.0

        with col_inf2:
            st.markdown(
                f'<div class="insight-callout"><strong>{len(eligible_rows)} Qualified Assets to Receive Fresh Inflow of USD {inflow_usd:,.0f}:</strong> '
                f'Proportional allocation by target weight across assets simultaneously satisfying fundamental/on-chain discount criteria.</div>',
                unsafe_allow_html=True,
            )

        df_inflow = pd.DataFrame([
            {
                "Ticker": r.asset_ticker,
                "Asset": r.asset_name,
                "Vertical": r.framework_category,
                "Current Metric": r.primary_indicator_current,
                "Advisory Status": "INFLOW ELIGIBLE" if r.shannon_inflow_eligible else "MONITOR",
                "Suggested Inflow (USD)": f"USD {(inflow_usd * (r.target_weight_pct / total_w_elig)):,.2f} ({(r.target_weight_pct / total_w_elig)*100:.1f}% of Inflow)",
            }
            for r in eligible_rows
        ])
        render_clean_table(df_inflow, badge_cols=["Advisory Status"])

        render_section_header(
            "2. Interactive Convex Leverage Stress-Test Simulator (LTV & Aave V3 Health Factor)",
            "Simulate severe market drawdowns on your Stocks/ETFs and Bitcoin to audit your safety cushion against the 50% LTV Hard-Cap",
        )
        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            shock_eq_pct = st.slider("Simulated Shock on Stocks/ETFs (%)", min_value=-60, max_value=20, value=-25, step=5)
        with s_col2:
            shock_btc_pct = st.slider("Simulated Shock on Bitcoin (%)", min_value=-75, max_value=30, value=-40, step=5)
        with s_col3:
            sim_debt_pct = st.slider("Initial LTV Prior to Shock (%)", min_value=0, max_value=35, value=20, step=2)

        collat_stocks_usd = capital_usd * (portfolio.ltv_eligible_stocks_weight_pct / 100.0)
        collat_btc_usd = capital_usd * (portfolio.ltv_eligible_btc_weight_pct / 100.0)
        base_collat_usd = collat_stocks_usd + collat_btc_usd
        sim_debt_usd = capital_usd * (sim_debt_pct / 100.0)
        stressed_collat_usd = (
            collat_stocks_usd * (1.0 + shock_eq_pct / 100.0)
            + collat_btc_usd * (1.0 + shock_btc_pct / 100.0)
        )
        stressed_portfolio_usd = (
            stressed_collat_usd
            + capital_usd * ((100.0 - portfolio.ltv_eligible_stocks_weight_pct - portfolio.ltv_eligible_btc_weight_pct) / 100.0) * (1.0 + shock_btc_pct / 100.0)
        )
        resulting_ltv_pct = (sim_debt_usd / max(1.0, stressed_portfolio_usd)) * 100.0 if sim_debt_usd > 0 else 0.0
        resulting_hf = (0.78 / max(0.01, (resulting_ltv_pct / 100.0))) if resulting_ltv_pct > 0 else 9.99

        l1, l2, l3, l4 = st.columns(4)
        with l1:
            render_kpi_card("Simulated Debt", f"USD {sim_debt_usd:,.0f}", f"Initial LTV: {sim_debt_pct}%", tone="blue")
        with l2:
            render_kpi_card("Post-Shock Portfolio", f"USD {stressed_portfolio_usd:,.0f}", f"Eq {shock_eq_pct}% | BTC {shock_btc_pct}%", tone="amber")
        with l3:
            tone_ltv = "emerald" if resulting_ltv_pct <= 35.0 else "amber"
            render_kpi_card("Post-Shock Resulting LTV", f"{resulting_ltv_pct:.1f}%", "Safety Hard-Cap: 50.0%", tone=tone_ltv)
        with l4:
            render_kpi_card("Estimated Health Factor", f"{min(9.99, resulting_hf):.2f}", "Liquidation only at HF = 1.00", tone="purple")

        # ----------------------------------------------------------------------
        # 3. BACKGROUND MORNING NOTIFIER MASTER SWITCH (ON / OFF)
        # ----------------------------------------------------------------------
        render_section_header(
            "3. Background Morning Notifier (Master Switch — ON / OFF)",
            "Keep OFF while not actively investing; toggle ON when you want daily automated morning alerts",
        )
        notifier_eng = BackgroundNotifierEngine()
        notif_cfg = notifier_eng.load_config()

        n_col1, n_col2 = st.columns([1, 2])
        with n_col1:
            enabled_now = st.toggle(
                "🔔 Enable Morning Background Notifier (ON / OFF)",
                value=bool(notif_cfg.enabled),
                help="When turned OFF, no external alerts are dispatched.",
            )
            sched_time = st.text_input("Daily Scan Time (HH:MM)", value=notif_cfg.schedule_time_hhmm)
            tg_token = st.text_input("Telegram Bot Token (Optional — fill when ready)", value=notif_cfg.telegram_bot_token, type="password")
            tg_chat = st.text_input("Telegram Chat ID (Optional)", value=notif_cfg.telegram_chat_id)
            dc_hook = st.text_input("Discord Webhook URL (Optional)", value=notif_cfg.discord_webhook_url, type="password")
            enable_ai_briefing_now = st.toggle(
                "✨ Enable AI Executive Interpretation on Morning Briefing",
                value=bool(notif_cfg.enable_ai_briefing),
                disabled=not gemini_ready,
                help=(
                    "Interprets already-computed alert numbers concisely via Gemini before dispatching."
                    if gemini_ready
                    else "Configure GEMINI_API_KEY in .env to enable AI briefing interpretation."
                ),
            )

            if st.button("💾 Save Notifier Settings (ON/OFF)", use_container_width=True, type="primary"):
                notif_cfg.enabled = enabled_now
                notif_cfg.schedule_time_hhmm = sched_time
                notif_cfg.telegram_bot_token = tg_token
                notif_cfg.telegram_chat_id = tg_chat
                notif_cfg.discord_webhook_url = dc_hook
                notif_cfg.enable_ai_briefing = bool(enable_ai_briefing_now)
                notifier_eng.save_config(notif_cfg)
                st.success(f"Notifier state saved: {'ENABLED (ON)' if enabled_now else 'DISABLED (OFF — Silent Mode)'}!")
                st.rerun()

            if st.button("👁️ Preview Morning Briefing Payload", use_container_width=True, key="btn_preview_briefing"):
                with st.spinner("Building morning briefing payload..."):
                    preview_res = notifier_eng.build_morning_briefing_payload(
                        macro=macro,
                        portfolio=portfolio,
                        equities=equities,
                        cryptos=cryptos,
                        micro_events=bundle["micro_events"],
                        risk_timing=risk_timing,
                        use_ai=bool(enable_ai_briefing_now and gemini_ready),
                    )
                st.session_state["notifier_preview"] = preview_res

        with n_col2:
            status_badge = "ENABLED (ON — Active Monitoring)" if notif_cfg.enabled else "DISABLED (OFF — Silent Mode / Pre-Investment)"
            st.markdown(
                f"""
                <div class="insight-callout">
                    <strong>Current Master Switch Status:</strong> <code>{status_badge}</code><br>
                    • <strong>Why do Telegram/Discord fields exist?</strong> The terminal <strong>does not know or access</strong> your Telegram automatically — these fields remain blank and disabled by default until you optionally paste a Discord Webhook or Telegram Bot credentials.<br>
                    • As long as this switch is <strong>OFF</strong>, the engine remains 100% silent and you consume reports on-demand via the <strong>360° Master Report (.PDF)</strong> button in Tab 1.
                </div>
                """,
                unsafe_allow_html=True,
            )
            if "notifier_preview" in st.session_state and st.session_state["notifier_preview"]:
                prev = st.session_state["notifier_preview"]
                with st.expander(
                    f"📨 Briefing Preview ({prev.get('alerts_count', 0)} signals | AI Enhanced: {'YES' if prev.get('ai_enhanced') else 'NO'})",
                    expanded=True,
                ):
                    st.markdown(prev.get("formatted_message", ""))

    # ==========================================================================
    # TAB 5: AI PORTFOLIO ANALYST (READ-ONLY GOOGLE ANTIGRAVITY SDK AGENT)
    # ==========================================================================
    with tabs[4]:
        render_section_header(
            "AI Portfolio Analyst — Read-Only Google Antigravity Agent",
            "Conversational quantitative & forensic analyst wired exclusively to deterministic core/ Python tools (zero shell/file/SQLite write access)",
        )

        analyst = InstitutionalAIAnalyst()
        agent_ok, agent_status_msg = analyst.is_available()

        top_a1, top_a2 = st.columns([3, 1])
        with top_a1:
            if agent_ok:
                st.markdown(
                    f'<div class="insight-callout" style="border-left-color:#10B981;">'
                    f'<strong>Agent Status:</strong> <code>{html.escape(agent_status_msg)}</code><br>'
                    f'• Built-in file/shell/web/subagent tools: <strong>DISABLED</strong> (<code>BuiltinTools.none()</code> + <code>policy.deny_all()</code>).<br>'
                    f'• Active deterministic tools: <code>get_portfolio_snapshot</code>, <code>audit_single_asset</code>, '
                    f'<code>get_macro_and_geopolitics</code>, <code>simulate_shannon_inflow</code>, <code>simulate_ltv_stress_test</code>, <code>run_opportunity_screener</code>.'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="insight-callout" style="border-left-color:#F59E0B;">'
                    f'<strong>AI Analyst Standby Mode:</strong> {html.escape(agent_status_msg)}<br>'
                    f'Add <code>GEMINI_API_KEY=...</code> to your root <code>.env</code> file to activate live conversational reasoning. '
                    f'All deterministic quantitative modules (Tabs 1–4 and 360° Master PDF export) remain 100% operational.'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        with top_a2:
            model_options = {
                "Auto (Smart Fallback)": "auto",
                "gemini-3.5-flash-lite (Fast / Free-Tier)": "gemini-3.5-flash-lite",
                "gemini-3.1-flash-lite (Ultra-Fast)": "gemini-3.1-flash-lite",
                "gemini-3.8-flash (Antigravity Default)": "gemini-3.8-flash",
                "gemini-4-hydrogen": "gemini-4-hydrogen",
            }
            chosen_label = st.selectbox(
                "Agent Model",
                options=list(model_options.keys()),
                index=0,
                key="ai_agent_model_select",
            )
            selected_agent_model = model_options[chosen_label]
            if st.button("🗑️ New Chat Session", use_container_width=True, key="btn_reset_ai_chat"):
                st.session_state["ai_chat_history"] = []
                st.session_state["ai_conversation_id"] = None
                st.session_state["ai_pending_prompt"] = None
                st.rerun()

        st.markdown("##### ⚡ Quick Institutional Prompts")
        qp1, qp2, qp3, qp4, qp5 = st.columns(5)
        with qp1:
            if st.button("📊 Audit Portfolio Look-Through & Risks", use_container_width=True, disabled=not agent_ok, key="qp_port"):
                st.session_state["ai_pending_prompt"] = (
                    "Audit our current portfolio allocation, top ETF look-through overlap exposures, "
                    "macro cycle regime, and highlight the key geopolitical/valuation risks."
                )
        with qp2:
            if st.button("💧 Simulate $15k Shannon Inflow", use_container_width=True, disabled=not agent_ok, key="qp_shannon"):
                st.session_state["ai_pending_prompt"] = (
                    "Simulate deploying a fresh $15,000 USD cash inflow using Shannon's Demon (zero tax-drag). "
                    "Show exact suggested USD allocations and current Sovereign Multiple metrics for qualified holdings."
                )
        with qp3:
            if st.button("🛡️ Stress-Test -35% Eq / -50% BTC LTV", use_container_width=True, disabled=not agent_ok, key="qp_ltv"):
                st.session_state["ai_pending_prompt"] = (
                    "Run a convex LTV stress test with a -35% shock on equities/ETFs and a -50% shock on Bitcoin "
                    "from a 20% initial LTV. Does it breach the 50% Hard-Cap and what is the estimated Aave V3 Health Factor?"
                )
        with qp4:
            if st.button("🔎 Screen Best 5-Filter Candidates", use_container_width=True, disabled=not agent_ok, key="qp_screen"):
                st.session_state["ai_pending_prompt"] = (
                    "Run the 5-filter quantitative opportunity screener for both stocks and cryptoassets, "
                    "and rank candidates by framework discipline (Sloan, CFO/EBITDA, ROIC vs WACC, g_impl vs g_fund, Real Earnings, MVRV Z)."
                )
        with qp5:
            active_tab3_tk = st.session_state.get("deep_dive_ticker", "NVDA")
            if st.button(f"🔬 Deep-Audit {active_tab3_tk}", use_container_width=True, disabled=not agent_ok, key="qp_dd_active"):
                st.session_state["ai_pending_prompt"] = (
                    f"Run a full forensic, valuation, M&A/protocol audit on {active_tab3_tk}, "
                    f"contrasting Reverse DCF / Sovereign Multiple against framework thresholds and macro context."
                )

        for msg in st.session_state["ai_chat_history"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                meta_parts = []
                if msg.get("model"):
                    meta_parts.append(f"Model: `{msg['model']}`")
                if msg.get("tools"):
                    meta_parts.append("Deterministic tools consulted: " + ", ".join(f"`{t}`" for t in msg["tools"]))
                if meta_parts:
                    st.caption(" | ".join(meta_parts))

        typed_chat = st.chat_input(
            "Ask the AI Portfolio Analyst (e.g., Audit NVDA forensic health, compare JPM vs NU, or stress-test LTV)...",
            disabled=not agent_ok,
        )
        active_prompt = st.session_state.pop("ai_pending_prompt", None) or typed_chat

        if active_prompt and agent_ok:
            st.session_state["ai_chat_history"].append({"role": "user", "content": active_prompt})
            with st.chat_message("user"):
                st.markdown(active_prompt)

            with st.chat_message("assistant"):
                with st.status("Consulting deterministic core/ engines via Google Antigravity SDK...", expanded=True) as ag_status:
                    st.write("Executing read-only Python tools over SQLite & valuation models...")
                    turn_res = analyst.ask(
                        question=active_prompt,
                        conversation_id=st.session_state.get("ai_conversation_id"),
                        capital_usd=capital_usd,
                        preferred_model=selected_agent_model,
                    )
                    if turn_res.error:
                        ag_status.update(label="⚠️ Agent Notice / Fallback Triggered", state="error", expanded=False)
                    else:
                        tools_str = ", ".join(turn_res.tools_invoked) if turn_res.tools_invoked else "direct synthesis"
                        ag_status.write(f"Model: `{turn_res.model_used}` | Tools: `{tools_str}`")
                        ag_status.update(label=f"✅ Completed via `{turn_res.model_used}` ({len(turn_res.tools_invoked)} tool calls)", state="complete", expanded=False)
                if turn_res.error:
                    err_text = f"⚠️ **AI Analyst Notice:** {turn_res.error}"
                    st.warning(err_text)
                    st.session_state["ai_chat_history"].append({"role": "assistant", "content": err_text, "tools": turn_res.tools_invoked})
                else:
                    if turn_res.conversation_id:
                        st.session_state["ai_conversation_id"] = turn_res.conversation_id
                    st.markdown(turn_res.answer_text)
                    meta_parts = []
                    if turn_res.model_used:
                        meta_parts.append(f"Model: `{turn_res.model_used}`")
                    if turn_res.tools_invoked:
                        meta_parts.append("Deterministic tools consulted: " + ", ".join(f"`{t}`" for t in turn_res.tools_invoked))
                    if meta_parts:
                        st.caption(" | ".join(meta_parts))
                    st.session_state["ai_chat_history"].append(
                        {
                            "role": "assistant",
                            "content": turn_res.answer_text,
                            "tools": turn_res.tools_invoked,
                            "model": turn_res.model_used,
                        }
                    )


if __name__ == "__main__":
    main()

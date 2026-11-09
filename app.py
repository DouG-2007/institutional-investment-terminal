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


st.set_page_config(
    page_title="Hub de Relatório Master 360° & Intervenção Ativa — Value Investing Framework",
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
    if any(k in s for k in ["ótimo", "ouro", "aprovado", "positivo", "boa", "segura", "sim", "sweet spot", "baixo", "100%", "blindada"]):
        return "green"
    if any(k in s for k in ["ruim", "reprovado", "alerta", "crise", "recessão", "negativo", "cuidado", "veto", "alto risco"]):
        return "red"
    if any(k in s for k in ["neutro", "ok", "misto", "moderado", "aguardar"]):
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
    geo_matrix = geo_eng.get_geopolitical_matrix()
    micro_events = geo_eng.get_micro_events()

    scr_eng = ScreenerEngine()
    stk_screener = scr_eng.run_stock_screener()
    cr_screener = scr_eng.run_crypto_screener()

    rt_eng = RiskTimingEngine()
    rt_bundle = rt_eng.build_risk_and_consultative_timing(
        portfolio=port_bundle,
        equities=eq_list,
        cryptos=cr_dict,
    )

    pdf_exp = InstitutionalPDFExporter()
    master_pdf_bytes = pdf_exp.generate_pdf_bytes(
        macro=macro_bundle,
        portfolio=port_bundle,
        equities=eq_list,
        cryptos=cr_dict,
        eq_filings=eq_filings,
        cr_filings=cr_filings,
        geo_matrix=geo_matrix,
        micro_events=micro_events,
        stock_screener=stk_screener,
        crypto_screener=cr_screener,
        risk_timing=rt_bundle,
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
        "master_pdf_bytes": master_pdf_bytes,
    }


def main() -> None:
    inject_clean_css()

    if "refresh_token" not in st.session_state:
        st.session_state["refresh_token"] = 0
    if "deep_dive_ticker" not in st.session_state:
        st.session_state["deep_dive_ticker"] = "NVDA"

    port_eng_live = PortfolioEngine()
    db_assets_live = port_eng_live.get_all_assets()
    db_sig = "|".join(
        f"{a['ticker']}:{a['target_weight_pct']:.2f}:{a['avg_buy_price']:.2f}:{int(a['ltv_turbo_eligible'])}"
        for a in db_assets_live
    )

    # Sidebar enxuta: Patrimônio Base, Refresh Ao Vivo e Download Rápido do Relatório Único
    with st.sidebar:
        st.markdown("### 🏛️ Controle do Relatório Master")
        capital_usd = st.number_input(
            "Patrimônio Base para Cálculo (USD)",
            min_value=10_000.0,
            max_value=100_000_000.0,
            value=100_000.0,
            step=10_000.0,
            format="%.0f",
        )
        if st.button("🔄 Atualizar Cotações Ao Vivo & Recalcular PDF", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.session_state["refresh_token"] += 1
            st.rerun()

    with st.spinner("Compilando Relatório Master Multi-Completo 360° (7 Seções + Gráficos Vetoriais)..."):
        bundle = load_full_intelligence_bundle(
            capital_usd=capital_usd,
            db_sig=db_sig,
            refresh_token=st.session_state["refresh_token"],
        )

    macro: MacroDataBundle = bundle["macro"]
    portfolio: PortfolioOverviewBundle = bundle["portfolio"]
    equities: List[EquityFullAnalysis] = bundle["equities"]
    cryptos: Dict[str, CryptoFullProfile] = bundle["cryptos"]
    risk_timing: RiskLeverageTimingBundle = bundle["risk_timing"]
    master_pdf_bytes: bytes = bundle["master_pdf_bytes"]

    with st.sidebar:
        st.download_button(
            label="📥 BAIXAR RELATÓRIO MASTER 360° (.PDF)",
            data=master_pdf_bytes,
            file_name="Relatorio_Master_Multi_Completo_360.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
        st.caption(
            f"Última sincronização: **{macro.timestamp}** | "
            f"**{len(portfolio.positions)} Ativos** na Carteira SQLite."
        )

    st.markdown(
        f"""
        <div class="inst-banner">
            <h1>🏛️ CENTRAL DO RELATÓRIO MASTER 360° &amp; MÓDULOS DE INTERVENÇÃO ATIVA</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "📄 1. Relatório Master Multi-Completo (.PDF)",
        "⚙️ 2. Gestor da Carteira (CRUD SQLite)",
        "🔎 3. Deep Dive Individual (Stock & Crypto Picker)",
        "🎛️ 4. Simuladores (Inflow & LTV) & Notificador (ON/OFF)",
    ])

    # ==========================================================================
    # ABA 1: CENTRAL DE EMISSÃO DO RELATÓRIO ÚNICO MULTI-COMPLETO (.PDF)
    # ==========================================================================
    with tabs[0]:
        render_kpi_card(
            "Alocação Estrutural da Carteira",
            f"{portfolio.total_crypto_pct:.0f}% Cripto  |  {portfolio.total_hard_assets_pct:.0f}% Hard-Assets",
            f"Monitoramento Ativo de {len(portfolio.positions)} Posições da Carteira",
            tone="blue",
        )

        st.markdown("<div style='height:0.65rem;'></div>", unsafe_allow_html=True)

        c_dl1, c_dl2 = st.columns([2, 1])
        with c_dl1:
            st.download_button(
                label="📥 BAIXAR RELATÓRIO MASTER MULTI-COMPLETO 360° (.PDF — TODAS AS 7 SEÇÕES)",
                data=master_pdf_bytes,
                file_name="Relatorio_Master_Multi_Completo_360.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
                key="btn_main_master_pdf",
            )
        with c_dl2:
            if st.button("🔄 Recalcular com Cotações Ao Vivo Agora", use_container_width=True, key="btn_main_refresh"):
                st.cache_data.clear()
                st.session_state["refresh_token"] += 1
                st.rerun()

        render_section_header(
            "Estrutura Interna do Relatório Master Multi-Completo 360° (.PDF)",
            "Um único arquivo PDF dividido em 7 capítulos de alta densidade, sem perda de nenhum indicador ou método",
        )

        df_sections = pd.DataFrame([
            {
                "Seção do PDF": "Seção 1",
                "Título do Capítulo no Relatório Único": "Macroeconomia Global, Ciclos, Disrupções Tecnológicas & Geopolítica",
                "Conteúdo Analítico & Gráficos Incluídos": "Indicadores Lagging (GDP, CPI, Fed Funds, Dívida/PIB, U3), Regra de Sahm pareada c/ Payroll & ICSA, SOS Indicator, PMI Services vs Mfg, Curva 10Y-2Y, M2 vs DXY, Matriz Geopolítica (10-K), Disrupções Tecnológicas nas Indústrias e Matriz de Sensibilidade Macro por Hard-Asset.",
            },
            {
                "Seção do PDF": "Seção 2",
                "Título do Capítulo no Relatório Único": "Dados Analíticos da Carteira, Look-Through Fiel, Forense & Valuation Forward",
                "Conteúdo Analítico & Gráficos Incluídos": "Posições da Carteira, Look-Through estrito das ações que você possui + Cesta Residual dos ETFs, Contabilidade Forense sem Altman Z (dividida em Parte A e Parte B de 5 colunas), Matriz CAGR 12 KPIs (dividida em Parte A e Parte B), Todos os 8 Métodos de Valuation Forward NTM (DCF NTM, Reverse DCF, Owner Earnings, Múltiplos Forward, EVA, PEGY Forward, Magic Formula e SOTP), Bancos da Carteira (JPM e NU).",
            },
            {
                "Seção do PDF": "Seção 3",
                "Título do Capítulo no Relatório Único": "Inteligência Analítica Cripto On-Chain & DeFi State of the Union",
                "Conteúdo Analítico & Gráficos Incluídos": "Ciclo On-Chain (MVRV Z, NUPL, aSOPR, Pi Cycle, 200W SMA), Mineração (Hash Ribbon & MMC), Fluxos (Inflow, CDD, Stablecoins, HODL Waves), Tokenomics (NVM, NVT GC, P/F, TVL, Protocol Real Earnings, Real Yield), Bússola de Rotação de Ciclo (BTC -> ETH -> DeFi) e Radar de Novas Tecnologias & Mudanças Estruturais em Cripto (Síntese Fundamentalista On-Chain).",
            },
            {
                "Seção do PDF": "Seção 4",
                "Título do Capítulo no Relatório Único": "Dossiê Forense Corporativo (SEC 10-K/10-Q/20-F, Porter, Calls Q&A & M&As)",
                "Conteúdo Analítico & Gráficos Incluídos": "Auditoria Big Four & SOX 404(b), Decomposição MD&A (Volume, Preço, FX, Backlog, CAPEX), Riscos Item 1A, Footnotes Forenses (Litígios, SBC, ASC 606, Dívida), Moats (4 Pilares), 5 Forças de Porter, Common Size vs Pares, Filtro de Sinal vs Ruído em Earnings Calls (Falas de CEO/CFO e Confrontos no Q&A), Dossiê Completo de M&As, Diluição, Goodwill e Antitruste + Fatos Relevantes 8-K/Form 4.",
            },
            {
                "Seção do PDF": "Seção 5",
                "Título do Capítulo no Relatório Único": "Dossiê Técnico de Protocolos Cripto (Whitepapers, Core Devs & Unlocks 30/60/90d)",
                "Conteúdo Analítico & Gráficos Incluídos": "Síntese Técnica de White Papers, Consenso e Value Accrual, Engenharia GitHub (Commits 4w e Active Devs), Governança DeepDAO, Token Sniffer e Auditorias, Sinais Internos de Core Devs/Founders, Upgrades de Rede (EIPs/PIPs) e Cronograma Forense de Unlocks (30/60/90 dias) com Preço Teórico Pós-Diluição e Concentração de Baleias/VCs.",
            },
            {
                "Seção do PDF": "Seção 6",
                "Título do Capítulo no Relatório Único": "Radar Executivo de Oportunidades — Screener Quantitativo e Forense",
                "Conteúdo Analítico & Gráficos Incluídos": "Funil 1 de Ações Globais (5 Filtros Estritos: Sloan, FCO/EBITDA, ROIC vs WACC, Solvência CR & Cobertura de Juros, Reverse DCF & PEGY Forward) e Funil 2 de Criptoativos (Supply >= 65%, Unlocks <= 2.5%/mês, Sniffer >= 85, Active Devs >= 40 & Real Earnings > 0, MVRV Z <= 2.0).",
            },
            {
                "Seção do PDF": "Seção 7",
                "Título do Capítulo no Relatório Único": "Governança de Risco, Alavancagem Convexa LTV, Liquidez ADTV & Timing Consultivo",
                "Conteúdo Analítico & Gráficos Incluídos": "Sharpe, Sortino, Calmar Ratio, VIX, Liquidez ADTV (<1%), Painel LTV Convexo (IBKR Box Spreads + Stress-Test Aave V3), As 7 Regras Consultivas de Timing por Classe de Ativo, Posicionamento Consultivo dos 20 Ativos da Carteira, Qualificação Shannon Inflow e Tax-Drag Hurdle Rate.",
            },
        ])
        render_clean_table(df_sections)

    # ==========================================================================
    # ABA 2: GESTOR DINÂMICO DE PORTFÓLIO (CRUD SQLITE)
    # ==========================================================================
    with tabs[1]:
        render_section_header(
            "Gestor Dinâmico de Portfólio (CRUD Persistente em SQLite)",
            "Adicione, edite ou remova ativos da carteira; toda alteração recalcula automaticamente o Relatório Master 360° (.PDF)",
        )

        total_w = portfolio.target_weight_sum_pct
        is_100 = getattr(portfolio, 'is_weight_valid_100', getattr(portfolio, 'weight_sum_is_valid_100', True))
        bar_col = "#10B981" if is_100 else "#F59E0B"
        st.markdown(
            f"""
            <div class="insight-callout" style="border-left-color:{bar_col};">
                <strong>Soma Atual dos Pesos-Alvo no SQLite: {total_w:.2f}%</strong> — {html.escape(portfolio.weight_validation_message)}
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
                st.markdown("##### ➕ Adicionar Novo Ativo ou Editar Ativo Existente")
                f1, f2, f3 = st.columns(3)
                with f1:
                    in_ticker = st.text_input("Ticker Oficial (ex: NVDA, COST, BTC-USD)", value="NVDA")
                    in_name = st.text_input("Nome da Empresa / Protocolo / ETF", value="NVIDIA Corporation")
                with f2:
                    in_class = st.selectbox("Classe do Ativo", ["Ação", "ETF", "Cripto", "Altcoin"])
                    in_sector = st.selectbox(
                        "Vertical Setorial do Framework",
                        [
                            "High-Growth Tech & Infra IA",
                            "Big Tech Cash Cow / Monopólio",
                            "Banco Global / Instituição Financeira",
                            "Varejo Defensivo (SSS)",
                            "Cíclica / Defesa / Indústria",
                            "ETF Índice Base (S&P 500 / Nasdaq / Setorial)",
                            "ETF Alavancado 2x (QLD)",
                            "Bitcoin Reserva Soberana PoW",
                            "Smart Contract Layer-1 (ETH/SOL)",
                            "DeFi Blue-Chip / Real Yield (PENDLE/MKR/UNI)",
                            "Oráculo / Interoperabilidade (LINK)",
                        ],
                    )
                with f3:
                    in_weight = st.number_input("Peso-Alvo na Carteira (%)", min_value=0.10, max_value=50.0, value=5.0, step=0.25)
                    in_avg_px = st.number_input("Preço Médio de Compra (USD)", min_value=0.0, max_value=500_000.0, value=88.0, step=1.0)
                    in_ltv = st.checkbox("Elegível como Colateral LTV Turbo?", value=True)

                in_role = st.text_input(
                    "Papel Estrutural na Carteira",
                    value="Monopólio de GPUs de IA e infraestrutura de computação acelerada CUDA.",
                )
                if st.form_submit_button("💾 Salvar / Atualizar Ativo no SQLite", use_container_width=True, type="primary"):
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
                    st.success(f"Ativo {in_ticker.upper()} salvo com sucesso no SQLite!")
                    st.rerun()

        with col_crud2:
            st.markdown("##### 🗑️ Remover Ativo ou Normalizar 100%")
            all_tks = [p.ticker for p in portfolio.positions]
            del_tk = st.selectbox("Selecionar Ativo para Remover", options=all_tks)
            if st.button("🗑️ Remover Ativo Selecionado", use_container_width=True):
                port_eng_live.delete_asset(del_tk)
                st.cache_data.clear()
                st.session_state["refresh_token"] += 1
                st.warning(f"Ativo {del_tk} removido da carteira.")
                st.rerun()

            st.markdown("<hr style='border-color:#334155;'>", unsafe_allow_html=True)
            st.caption("Caso a soma dos pesos-alvo esteja diferente de 100.00%, clique abaixo para reescalonar proporcionalmente:")
            if st.button("⚖️ Normalizar Pesos Automaticamente para 100.00%", use_container_width=True):
                port_eng_live.normalize_weights_to_100()
                st.cache_data.clear()
                st.session_state["refresh_token"] += 1
                st.success("Pesos normalizados exatamente para 100.00%!")
                st.rerun()

        render_section_header(
            f" Quadro de Posições Ativas na Carteira ({len(portfolio.positions)} Ativos no SQLite)",
            "Tabela enxuta de 7 colunas para conferência rápida de Pesos, Preço Médio, Spot, P&L e Colateral LTV",
        )
        df_ledger = pd.DataFrame([
            {
                "Ticker": p.ticker,
                "Ativo": p.name,
                "Categoria": p.category,
                "Peso Alvo vs. Atual": f"{p.target_weight_pct:.2f}% (Atual {p.current_weight_pct:.2f}% | Drift {p.weight_drift_pp:+.2f}pp)",
                "PM -> Preço Spot (USD)": f"${p.avg_buy_price_usd:,.2f} -> ${p.current_price_usd:,.2f} (${p.allocated_usd:,.0f})",
                "P&L Latente": f"{p.pnl_pct:+.1f}% (USD {p.pnl_usd:+,.0f})",
                "Colateral LTV": "SIM" if p.ltv_turbo_eligible else "NÃO",
            }
            for p in portfolio.positions
        ])
        render_clean_table(df_ledger, badge_cols=["Colateral LTV"])

    # ==========================================================================
    # ABA 3: DEEP DIVE INDIVIDUAL (STOCK & CRYPTO PICKER SOB DEMANDA)
    # ==========================================================================
    with tabs[2]:
        render_section_header(
            "Deep Dive Analyzer Individual (Stock, ETF & Crypto Picker)",
            "Pesquise qualquer ativo do mercado ou da sua carteira para gerar um diagnóstico completo + PDF Individual em 1 clique",
        )

        col_s1, col_s2, col_s3 = st.columns([2, 2, 1])
        with col_s1:
            typed_tk = st.text_input(
                "Digite qualquer Ticker (Ex: NVDA, ASML, TSM, MELI, COST, LLY, JPM, NU, BTC, ETH, PENDLE, LINK, SOL)",
                value=st.session_state["deep_dive_ticker"],
            )
        with col_s2:
            quick_pick = st.selectbox(
                "Ou selecione rapidamente um Ativo da Carteira / Radar:",
                options=[
                    "NVDA", "AAPL", "MSFT", "ASML", "TSM", "JPM", "MELI", "AVGO", "MA", "NU",
                    "BTC-USD", "ETH-USD", "PENDLE-USD", "LINK-USD", "MKR-USD", "UNI-USD",
                    "SPY", "QQQ", "QLD", "ITA", "COST", "LLY", "SOL-USD", "AAVE-USD",
                ],
                index=0,
            )
        with col_s3:
            st.markdown("<div style='height:1.72rem;'></div>", unsafe_allow_html=True)
            if st.button("🔎 Executar Deep Dive", use_container_width=True, type="primary"):
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
                f"Ativo Analisado ({dd_res.asset_class})",
                dd_res.normalized_ticker,
                dd_res.framework_category_label,
                tone="blue",
            )
        with d2:
            render_kpi_card(
                "Múltiplo Soberano Forward",
                dd_res.sovereign_multiple_value,
                dd_res.sovereign_multiple_status,
                tone="emerald",
            )
        with d3:
            render_kpi_card(
                "Score no Funil de 5 Filtros",
                f"{dd_res.screener_score_0_100} / 100 pts",
                dd_res.regime_classification.split("—")[0].strip(),
                tone="purple",
            )
        with d4:
            port_status_str = "NA CARTEIRA ATUAL" if dd_res.in_current_portfolio else "ATIVO EXTERNO (RADAR)"
            render_kpi_card(
                "Status no Portfólio",
                port_status_str,
                "Dossiê Individual PDF Pronto",
                tone="amber",
            )

        st.markdown(
            f'<div class="insight-callout"><strong>Veredito Consultivo Automatizado ({html.escape(dd_res.normalized_ticker)}):</strong> '
            f'{html.escape(dd_res.automated_consultative_verdict)}</div>',
            unsafe_allow_html=True,
        )

        st.download_button(
            label=f"📥 BAIXAR DOSSIÊ DEEP DIVE INDIVIDUAL DE {dd_res.normalized_ticker} (.PDF)",
            data=dd_pdf_bytes,
            file_name=f"Dossie_Deep_Dive_{dd_res.normalized_ticker}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
            key=f"dl_dd_{dd_res.normalized_ticker}",
        )

        render_section_header(
            f"Funil Estrito de 5 Filtros — {dd_res.normalized_ticker} (Score {dd_res.screener_score_0_100}/100)",
            "Avaliação passo a passo sem texto espremido e sem Altman Z-Score",
        )
        df_funnel = pd.DataFrame([
            {
                "Etapa": f"Filtro {s.step_number}",
                "Critério Avaliado": s.filter_name,
                "Valor Calculado": s.calculated_value,
                "Regra Estrita do Framework": s.strict_criterion,
                "Status": "APROVADO" if s.passed else "REPROVADO",
                " Diagnóstico": f"{s.score_points}/{s.max_points} pts — {s.diagnostic_note}",
            }
            for s in dd_res.screener_filters_breakdown
        ])
        render_clean_table(df_funnel, badge_cols=["Status"])

        if dd_res.asset_class != "CRYPTO" and dd_res.equity_analysis:
            eq_i = dd_res.equity_analysis
            fh_i = eq_i.forensic_health
            vm_i = eq_i.valuation_methods
            render_section_header(
                f"Resumo de Valuation Multi-Métodos Forward (NTM) & Saúde Forense — {dd_res.normalized_ticker}",
                "Tabelas amplas de 5 colunas para leitura imediata",
            )
            df_dd_val = pd.DataFrame([
                {
                    "Preço Spot & WACC": f"${eq_i.current_price:,.2f} (WACC {vm_i['wacc_capm_pct']:.2f}%)",
                    "DCF Forward (10% MoS)": f"${vm_i['dcf_fair_mos10_usd']:,.2f} ({vm_i['dcf_upside_pct']:+.1f}%)",
                    "Reverse DCF (g_impl vs g_fund)": f"g_impl {vm_i['reverse_dcf_g_impl_pct']:.1f}% vs g_fund {vm_i['g_fund_projected_pct']:.1f}%",
                    "PEGY Forward (NTM)": f"{vm_i['primary_pegy_label']} ({vm_i['primary_pegy_status']})",
                    "SOTP & ROIC vs WACC": f"SOTP ${vm_i['sotp_fair_price_usd']:,.2f} ({vm_i['sotp_upside_pct']:+.1f}%) | ROIC {fh_i['roic_goodwill_pct']:.1f}%",
                }
            ])
            render_clean_table(df_dd_val)

    # ==========================================================================
    # ABA 4: SIMULADORES INTERATIVOS (SHANNON INFLOW & STRESS-TEST LTV) & NOTIFICADOR (ON/OFF)
    # ==========================================================================
    with tabs[3]:
        render_section_header(
            "1. Simulador Interativo de Novo Aporte (Shannon's Demon Inflow Rebalancing)",
            "Calcule como distribuir dinheiro novo exclusivamente nos ativos em faixa de acumulação e abaixo do peso-alvo (sem vender vencedores)",
        )
        col_inf1, col_inf2 = st.columns([1, 2])
        with col_inf1:
            inflow_usd = st.number_input(
                "Valor do Novo Aporte em Caixa (USD)",
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
                f'<div class="insight-callout"><strong>{len(eligible_rows)} Ativos Qualificados para Receber o Novo Aporte de USD {inflow_usd:,.0f}:</strong> '
                f'Alocação proporcional ao peso-alvo nos ativos que cumprem simultaneamente os critérios de desconto fundamentalista/on-chain.</div>',
                unsafe_allow_html=True,
            )

        df_inflow = pd.DataFrame([
            {
                "Ticker": r.asset_ticker,
                "Ativo": r.asset_name,
                "Vertical": r.framework_category,
                "Indicador Atual": r.primary_indicator_current,
                "Status Consultivo": "ELEGÍVEL INFLOW" if r.shannon_inflow_eligible else "MONITORAR",
                "Aporte Sugerido (USD)": f"USD {(inflow_usd * (r.target_weight_pct / total_w_elig)):,.2f} ({(r.target_weight_pct / total_w_elig)*100:.1f}% do Aporte)",
            }
            for r in eligible_rows
        ])
        render_clean_table(df_inflow, badge_cols=["Status Consultivo"])

        render_section_header(
            "2. Simulador Interativo de Stress-Test de Alavancagem Convexa (LTV & Health Factor Aave V3)",
            "Teste choques severos de mercado nas suas Ações/ETFs e no seu BTC para auditar a folga contra o Hard-Cap de 50% LTV",
        )
        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            shock_eq_pct = st.slider("Choque Simulado nas Ações/ETFs (%)", min_value=-60, max_value=20, value=-25, step=5)
        with s_col2:
            shock_btc_pct = st.slider("Choque Simulado no Bitcoin (%)", min_value=-75, max_value=30, value=-40, step=5)
        with s_col3:
            sim_debt_pct = st.slider("LTV Inicial antes do Choque (%)", min_value=0, max_value=35, value=20, step=2)

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
            render_kpi_card("Dívida Simulada", f"USD {sim_debt_usd:,.0f}", f"LTV Inicial: {sim_debt_pct}%", tone="blue")
        with l2:
            render_kpi_card("Patrimônio Pós-Choque", f"USD {stressed_portfolio_usd:,.0f}", f"Eq {shock_eq_pct}% | BTC {shock_btc_pct}%", tone="amber")
        with l3:
            tone_ltv = "emerald" if resulting_ltv_pct <= 35.0 else "amber"
            render_kpi_card("LTV Resultante Pós-Choque", f"{resulting_ltv_pct:.1f}%", "Hard-Cap de Segurança: 50.0%", tone=tone_ltv)
        with l4:
            render_kpi_card("Health Factor Estimado", f"{min(9.99, resulting_hf):.2f}", "Liquidação apenas em HF = 1.00", tone="purple")

        # ----------------------------------------------------------------------
        # 3. CHAVE LIGA / DESLIGA (ON/OFF) DO NOTIFICADOR PASSIVO MATINAL
        # ----------------------------------------------------------------------
        render_section_header(
            "3. Notificador Passivo Matinal em Background (Chave Mestra Liga / Desliga — ON/OFF)",
            "Mantenha DESLIGADO (OFF) enquanto não estiver investindo ativamente; ligue (ON) quando desejar receber alertas matinais",
        )
        notifier_eng = BackgroundNotifierEngine()
        notif_cfg = notifier_eng.load_config()

        n_col1, n_col2 = st.columns([1, 2])
        with n_col1:
            enabled_now = st.toggle(
                "🔔 Ativar Notificador Passivo Matinal (ON / OFF)",
                value=bool(notif_cfg.enabled),
                help="Quando desligado (OFF), nenhum alerta externo é disparado.",
            )
            sched_time = st.text_input("Horário Diário de Varredura", value=notif_cfg.schedule_time_hhmm)
            tg_token = st.text_input("Telegram Bot Token (Opcional — você preenche se quiser)", value=notif_cfg.telegram_bot_token, type="password")
            tg_chat = st.text_input("Telegram Chat ID (Opcional)", value=notif_cfg.telegram_chat_id)
            dc_hook = st.text_input("Discord Webhook URL (Opcional)", value=notif_cfg.discord_webhook_url, type="password")

            if st.button("💾 Salvar Estado do Notificador (ON/OFF)", use_container_width=True, type="primary"):
                notif_cfg.enabled = enabled_now
                notif_cfg.schedule_time_hhmm = sched_time
                notif_cfg.telegram_bot_token = tg_token
                notif_cfg.telegram_chat_id = tg_chat
                notif_cfg.discord_webhook_url = dc_hook
                notifier_eng.save_config(notif_cfg)
                st.success(f"Estado do Notificador salvo: {'LIGADO (ON)' if enabled_now else 'DESLIGADO (OFF — Modo Silencioso)'}!")
                st.rerun()

        with n_col2:
            status_badge = "LIGADO (ON — Monitoramento Ativo)" if notif_cfg.enabled else "DESLIGADO (OFF — Modo Silencioso / Pré-Investimento)"
            st.markdown(
                f"""
                <div class="insight-callout">
                    <strong>Status Atual da Chave Mestra:</strong> <code>{status_badge}</code><br>
                    • <strong>Por que os campos de Telegram/Discord existem?</strong> O aplicativo <strong>não conhece nem acessa</strong> seu Telegram automaticamente — esses campos ficam em branco e desligados por padrão caso no futuro você mesmo queira colar um Webhook do Discord ou Bot do Telegram.<br>
                    • Enquanto a chave estiver em <strong>OFF</strong>, o sistema permanece 100% silencioso e você consome tudo apenas quando quiser clicando no botão do <strong>Relatório Master Multi-Completo (.PDF)</strong> na Aba 1.
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()

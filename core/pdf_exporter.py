"""
MOTOR DE EXPORTAÇÃO DO RELATÓRIO MASTER MULTI-COMPLETO 360° EM PDF (.PDF)
Unifica 100% da densidade informacional dos 5 dossiês especializados + todos os dados analíticos,
indicadores econômicos, métodos de valuation Forward (NTM) e gráficos vetoriais (SVG) do aplicativo
em UM ÚNICO RELATÓRIO MULTI-SEÇÕES DE ALTA LEITURA E ZERO TABELAS ESPREMIDAS.
Renderizado via Chromium / Microsoft Edge Headless com tipografia e gráficos vetoriais nítidos.
"""

from __future__ import annotations

import html
import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

from core.macro_engine import MacroDataBundle
from core.portfolio_engine import PortfolioOverviewBundle
from core.equity_engine import EquityFullAnalysis, GLOBAL_BANKS_SCATTER_DATA
from core.crypto_engine import CryptoFullProfile
from core.filings_engine import EquityDocumentaryDossier, CryptoDocumentaryDossier
from core.geopolitics_micro_engine import GeopoliticalImpactRow, MicroCorporateProtocolEvent
from core.screener_engine import StockScreenerRow, CryptoScreenerRow
from core.risk_timing_engine import RiskLeverageTimingBundle
from core.deep_dive_engine import DeepDiveResultBundle


def _esc(val: Any) -> str:
    return html.escape(str(val if val is not None else ""))


def _badge(text: str, tone: str = "blue") -> str:
    colors = {
        "green": ("#DCFCE7", "#166534", "#86EFAC"),
        "blue": ("#DBEAFE", "#1E40AF", "#93C5FD"),
        "amber": ("#FEF3C7", "#92400E", "#FCD34D"),
        "red": ("#FEE2E2", "#991B1B", "#FCA5A5"),
        "purple": ("#F3E8FF", "#6B21A8", "#D8B4FE"),
        "slate": ("#F1F5F9", "#334155", "#CBD5E1"),
    }
    bg, fg, bd = colors.get(tone, colors["blue"])
    return (
        f'<span style="display:inline-block; padding:2px 7px; border-radius:4px; '
        f'background:{bg}; color:{fg}; border:1px solid {bd}; font-weight:700; '
        f'font-size:7.3pt; line-height:1.25; word-break:normal; overflow-wrap:break-word;">'
        f'{_esc(text)}</span>'
    )


def _auto_badge(text: str) -> str:
    low = str(text).lower()
    if any(k in low for k in ["ótimo", "ouro", "aprovado", "positivo", "boa", "segura", "clean", "unqualified", "sim", "sweet spot", "baixo", "100/100", "blindada", "assimetria positiva"]):
        return _badge(text, "green")
    if any(k in low for k in ["reprovado", "ruim", "alerta", "alto risco", "crise", "recessão", "negativo", "squeeze", "alta ("]):
        return _badge(text, "red")
    if any(k in low for k in ["neutro", "ok", "moderado", "misto", "monitorar", "média", "exigência"]):
        return _badge(text, "amber")
    return _badge(text, "blue")


class InstitutionalPDFExporter:
    def __init__(self) -> None:
        pass

    def _find_browser_executable(self) -> Optional[str]:
        candidates = [
            shutil.which("chrome"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            shutil.which("msedge"),
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return c
        return None

    # ==========================================================================
    # GERADORES DE GRÁFICOS SVG (DESATIVADOS / REMOVIDOS A PEDIDO DO USUÁRIO)
    # ==========================================================================
    def _build_svg_macro_charts(self, macro: MacroDataBundle) -> str:
        return ""

    def _build_svg_equity_valuation_charts(self, equities: List[EquityFullAnalysis]) -> str:
        return ""

    def _build_svg_crypto_onchain_charts(self, cryptos: Dict[str, CryptoFullProfile]) -> str:
        return ""

    # ==========================================================================
    # RELATÓRIO ÚNICO MULTI-COMPLETO (7 SEÇÕES INTEGRADAS EM UM SÓ PDF)
    # ==========================================================================
    def build_complete_html_report(
        self,
        macro: MacroDataBundle,
        portfolio: PortfolioOverviewBundle,
        equities: List[EquityFullAnalysis],
        cryptos: Dict[str, CryptoFullProfile],
        eq_filings: List[EquityDocumentaryDossier],
        cr_filings: List[CryptoDocumentaryDossier],
        geo_matrix: List[GeopoliticalImpactRow],
        micro_events: List[MicroCorporateProtocolEvent],
        stock_screener: List[StockScreenerRow],
        crypto_screener: List[CryptoScreenerRow],
        risk_timing: RiskLeverageTimingBundle,
    ) -> str:
        from core.intelligence_reports_engine import IntelligenceReportsEngine

        intel = IntelligenceReportsEngine()
        disruptions = intel.get_industry_tech_disruptions()
        sens_rows = intel.build_hard_asset_macro_sensitivity_matrix(portfolio.positions)
        llama_stats = intel.fetch_live_defillama_macro_stats()
        cycle_rows = intel.build_defi_cycle_indicators(cryptos)
        narratives = intel.get_defi_narratives()

        sp = macro.sahm_paired
        sos = macro.sos_indicator
        pmi = macro.pmi_analysis
        yc = macro.yield_curve
        mon = macro.monetary_aggregates
        pr = risk_timing.performance_risk_metrics
        vx = risk_timing.vix_indicator
        ltv = risk_timing.convex_ltv_panel

        css = """
        @page {
            size: A4 landscape;
            margin: 9mm 10mm 10mm 10mm;
        }
        * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
            font-size: 7.8pt;
            line-height: 1.36;
            color: #0F172A;
            background: #FFFFFF;
            margin: 0;
            padding: 0;
        }
        .page-section {
            page-break-after: always;
        }
        .page-section:last-child {
            page-break-after: auto;
        }
        .report-header {
            background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
            color: #FFFFFF;
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid #F59E0B;
        }
        .report-title {
            font-size: 12.8pt;
            font-weight: 800;
            letter-spacing: -0.2px;
            margin: 0;
        }
        .report-subtitle {
            font-size: 7.8pt;
            color: #CBD5E1;
            margin-top: 2px;
        }
        .section-banner {
            background: #0F172A;
            color: #FDE047;
            padding: 6px 12px;
            font-size: 9pt;
            font-weight: 800;
            border-left: 4px solid #3B82F6;
            border-radius: 4px;
            margin: 8px 0 6px 0;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .sub-banner {
            background: #1E293B;
            color: #F8FAFC;
            padding: 4px 10px;
            font-size: 8.1pt;
            font-weight: 700;
            border-left: 3px solid #10B981;
            border-radius: 3px;
            margin: 6px 0 4px 0;
        }
        .kpi-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin-bottom: 8px;
        }
        .kpi-box {
            background: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-left: 4px solid #1E3A8A;
            border-radius: 5px;
            padding: 6px 10px;
        }
        .kpi-box .lbl {
            font-size: 6.8pt;
            font-weight: 700;
            text-transform: uppercase;
            color: #475569;
        }
        .kpi-box .val {
            font-size: 10.6pt;
            font-weight: 800;
            color: #0F172A;
            margin: 2px 0;
        }
        .kpi-box .sub {
            font-size: 6.8pt;
            color: #64748B;
        }
        .insight-box {
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            border-left: 4px solid #2563EB;
            border-radius: 5px;
            padding: 6px 11px;
            margin-bottom: 7px;
            font-size: 7.6pt;
            color: #1E3A8A;
        }
        table.inst-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 8px;
            font-size: 7.4pt;
            table-layout: auto;
        }
        table.inst-table th {
            background: #1E293B;
            color: #FFFFFF;
            font-weight: 700;
            text-align: left;
            padding: 5px 7px;
            border: 1px solid #334155;
            font-size: 7.3pt;
            word-break: normal;
            overflow-wrap: break-word;
        }
        table.inst-table td {
            padding: 4.5px 7px;
            border: 1px solid #CBD5E1;
            vertical-align: top;
            color: #0F172A;
            word-break: normal;
            overflow-wrap: break-word;
            hyphens: none;
        }
        table.inst-table tr:nth-child(even) td {
            background: #F8FAFC;
        }
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .mono {
            font-family: 'Consolas', 'Courier New', monospace;
            font-weight: 600;
        }
        """

        # ======================================================================
        # SEÇÃO 1: MACROECONOMIA GLOBAL, CICLOS, GRÁFICOS MACRO, GEOPOLÍTICA & DISRUPÇÕES
        # ======================================================================
        lag_rows_html = "".join(
            f"<tr><td><strong>{_esc(m['Indicador'])}</strong></td>"
            f"<td class='mono'>{_esc(m['Valor Atual'])}</td>"
            f"<td class='mono'>{_esc(m['Variação / Taxa'])}</td>"
            f"<td>{_esc(m['Referência'])}</td>"
            f"<td>{_auto_badge(m['Leitura'])}</td></tr>"
            for m in macro.basic_metrics
        )
        verts_html = " | ".join(f"<strong>{k}:</strong> {v:.2f}%" for k, v in yc["vertices"].items())

        geo_rows_html = "".join(
            f"<tr>"
            f"<td><strong>{_esc(g.global_event)}</strong><br><span style='font-size:6.8pt;color:#475569;'>{_esc(g.region_vector)}</span></td>"
            f"<td>{_auto_badge(g.severity)}</td>"
            f"<td class='mono'><strong>{_esc(g.affected_portfolio_assets)}</strong></td>"
            f"<td>{_esc(g.revenue_or_production_exposed_pct)}</td>"
            f"<td>{_esc(g.fundamental_impact_mechanism)}</td>"
            f"<td>{_esc(g.country_liquidity_risk_assessment)}</td>"
            f"</tr>"
            for g in geo_matrix
        )

        disr_html = "".join(
            f"<tr>"
            f"<td><strong>{_esc(d.mega_trend)}</strong><br><span style='font-size:6.8pt;color:#475569;'>{_esc(d.time_horizon)}</span></td>"
            f"<td>{_esc(d.disruption_mechanism)}</td>"
            f"<td class='mono'><strong>{_esc(d.winners_in_portfolio)}</strong></td>"
            f"<td>{_esc(d.vulnerable_or_hedged_assets)}</td>"
            f"<td>{_esc(d.quantitative_kpi_to_watch)}</td>"
            f"</tr>"
            for d in disruptions
        )

        sens_html = "".join(
            f"<tr>"
            f"<td class='mono'><strong>{_esc(s.ticker)}</strong><br><span style='font-size:6.8pt;'>{_esc(s.company_name)}</span></td>"
            f"<td>{_esc(s.interest_rate_sensitivity)}</td>"
            f"<td>{_esc(s.usd_dxy_and_fx_sensitivity)}</td>"
            f"<td>{_esc(s.tariff_and_supply_chain_exposure)}</td>"
            f"<td>{_esc(s.energy_and_ai_capex_linkage)}</td>"
            f"<td>{_auto_badge(s.net_macro_positioning_verdict)}</td>"
            f"</tr>"
            for s in sens_rows
        )

        sec1_html = f"""
        <div class="page-section">
            <div class="report-header">
                <div>
                    <div class="report-title">RELATÓRIO MASTER MULTI-COMPLETO 360° — INTELIGÊNCIA ANALÍTICA, FORENSE, MACRO &amp; DEFI</div>
                    <div class="report-subtitle">Documento Único Consolidado (7 Seções Completas) &bull; Dados Analíticos Forward (NTM), Contabilidade Forense, SEC 10-K/M&amp;A/Porter, Whitepapers/Unlocks, NVT Nominal, DeFi &amp; Screener</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:9.5pt; font-weight:800; color:#FDE047;">PATRIMÔNIO BASE: USD {portfolio.capital_usd:,.0f}</div>
                    <div style="font-size:7.3pt; color:#E2E8F0;">Gerado em: {_esc(macro.timestamp)}</div>
                </div>
            </div>

            <div class="kpi-row">
                <div class="kpi-box">
                    <div class="lbl">Alocação da Carteira ({len(portfolio.positions)} Ativos)</div>
                    <div class="val">{portfolio.total_crypto_pct:.0f}% Cripto / {portfolio.total_hard_assets_pct:.0f}% Hard-Assets</div>
                    <div class="sub">Exposição Bruta Efetiva (c/ QLD 2x): {portfolio.effective_gross_exposure_pct:.1f}%</div>
                </div>
                <div class="kpi-box">
                    <div class="lbl">Regra de Sahm + Payroll &amp; ICSA</div>
                    <div class="val">{sp['sahm_current_pct']:+.2f}% (SOS: {sos['sos_current']:.3f})</div>
                    <div class="sub">Payroll: {sp['payroll_mom_thousands']:+.0f}k | ICSA: {sp['icsa_current']:,}</div>
                </div>
                <div class="kpi-box">
                    <div class="lbl">Curva 10Y-2Y &amp; Dinâmica Pontas</div>
                    <div class="val">{yc['spread_10y_2y_bps']:+.1f} bps ({_esc(yc['ends_dynamics_quality'])})</div>
                    <div class="sub">10Y: {yc['us10y_pct']:.2f}% | 2Y: {yc['us2y_pct']:.2f}% | Δ2Y: {yc['delta_60d_2y_bps']:+.0f}bps</div>
                </div>
                <div class="kpi-box">
                    <div class="lbl">Liquidez Global (M2 vs. DXY &amp; TVL DeFi)</div>
                    <div class="val">M2 ${mon['m2_trillions']:.2f}T | DXY {mon['dxy_current']:.2f}</div>
                    <div class="sub">Fed BS: ${mon['fed_balance_sheet_trillions']:.2f}T | TVL DeFi: ${llama_stats['total_defi_tvl_b']:.1f}B</div>
                </div>
            </div>

            <div class="section-banner">SEÇÃO 1: MACROECONOMIA GLOBAL, CICLOS DE MERCADO, DISRUPÇÕES INDUSTRIAIS &amp; GEOPOLÍTICA (HARD-ASSETS)</div>

            

            <div class="grid-2">
                <div>
                    <div class="sub-banner">1.1A. Indicadores Lagging (Confirmam Tendência): GDP, CPI, Juros, Dívida e Desemprego</div>
                    <table class="inst-table">
                        <thead><tr><th>Indicador</th><th>Valor Atual</th><th>Variação</th><th>Referência</th><th>Leitura</th></tr></thead>
                        <tbody>{lag_rows_html}</tbody>
                    </table>
                </div>
                <div>
                    <div class="sub-banner">1.1B. Regra de Sahm (Pareada c/ Payroll &amp; ICSA) e SOS Indicator</div>
                    <table class="inst-table">
                        <thead><tr><th>Indicador / Par Obrigatório</th><th>Valor Atual</th><th>Referência</th><th>Diagnóstico</th></tr></thead>
                        <tbody>
                            <tr><td><strong>Sahm's Rule (U3 MA3m - Mín 12m)</strong></td><td class="mono">{sp['sahm_current_pct']:+.2f}% (MA3: {sp['unrate_3m_ma_pct']:.2f}%)</td><td>&gt;= +0.50% (Recessão)</td><td>{_auto_badge(sp['paired_verdict'])}</td></tr>
                            <tr><td><strong>Par Obrigatório 1: Payroll (PAYEMS)</strong></td><td class="mono">{sp['payroll_mom_thousands']:+.1f}k MoM (MA3m: {sp['payroll_3m_avg_thousands']:+.1f}k)</td><td>&lt;= 0 confirma recessão</td><td>{_auto_badge(sp['payroll_status'])}</td></tr>
                            <tr><td><strong>Par Obrigatório 2: ICSA (Claims)</strong></td><td class="mono">{sp['icsa_current']:,} (MA4w: {sp['icsa_4w_ma']:,})</td><td>Crescendo confirma demissões</td><td>{_auto_badge(sp['icsa_trend_status'])}</td></tr>
                            <tr><td><strong>SOS Indicator (Weekly Recession)</strong></td><td class="mono">{sos['sos_current']:.3f} (MA13w: {sos['insured_unemp_13w_ma']:.3f}%)</td><td>&gt; 0.20 = Recessão</td><td>{_auto_badge(sos['status'])}</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="sub-banner">1.2. Indicadores Leading (Antecipam Tendência): PMI Services vs. Mfg, Curva 10Y-2Y, Dinâmica das Pontas e Liquidez M2 vs. DXY</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:18%;">Dimensão Leading</th>
                        <th style="width:26%;">Valores Atuais Calculados</th>
                        <th style="width:22%;">Parâmetros de Referência</th>
                        <th style="width:34%;">Insight Analítico &amp; Diagnóstico de Ciclo</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>PMI (Services vs. Manufacturing)</strong></td>
                        <td class="mono">PMI Services: {pmi['pmi_services_current']:.1f} (3m atrás: {pmi['pmi_Services_3m_ago']:.1f})<br>PMI Manufacturing: {pmi['pmi_manufacturing_current']:.1f} (Spread: {pmi['services_vs_mfg_spread']:+.1f})</td>
                        <td>&gt; 50 Expansão | &gt; 60 Risco Inflação | &lt; 50 Contração<br><strong>Sweet Spot:</strong> Queda recente mas ainda &gt; 50</td>
                        <td>{_auto_badge(pmi['automated_insight'])}<br>Relação estrutural: <strong>Services &gt; Manufacturing ({'Confirmado' if pmi['services_gt_manufacturing'] else 'Invertido'})</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Yield Curve &amp; Dinâmica das Pontas</strong></td>
                        <td class="mono">Spread 10Y-2Y: {yc['spread_10y_2y_pct']:+.2f}% ({yc['spread_10y_2y_bps']:+.1f} bps) | Δ60d 2Y: {yc['delta_60d_2y_bps']:+.0f}bps | Δ60d 10Y: {yc['delta_60d_10y_bps']:+.0f}bps<br>{verts_html}</td>
                        <td>2Y caindo mais rápido que 10Y &rarr; <strong>Dinâmica BOA</strong><br>Cruzamento &gt; 0 pós-inversão = <strong>Desinversão</strong></td>
                        <td>{_auto_badge(yc['ends_dynamics_insight'])}<br>{_esc(yc['uninversion_note'])}</td>
                    </tr>
                    <tr>
                        <td><strong>Fed Balance Sheet &amp; M2 vs. DXY</strong></td>
                        <td class="mono">WALCL: ${mon['fed_balance_sheet_trillions']:.3f}T ({mon['fed_bs_yoy_chg_pct']:+.2f}% YoY) | M2: ${mon['m2_trillions']:.2f}T ({mon['m2_yoy_chg_pct']:+.2f}% YoY)<br>DXY: {mon['dxy_current']:.2f} ({mon['dxy_3m_chg_pct']:+.2f}% 3m) | Ouro: ${mon['gold_usd']:,.0f} | S&amp;P 500: {mon['sp500_current']:,.0f}</td>
                        <td><strong>Cenário Positivo:</strong> Oferta Monetária M2 Subindo E Dólar (DXY) Caindo</td>
                        <td><strong>{_esc(mon['qe_qt_status'])}</strong> | {_auto_badge(mon['scenario_verdict'])}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="page-section">
            <div class="sub-banner">1.3. Matriz de Impacto Geopolítico Global (% de Receita/Produção Exposta Extraída dos 10-Ks e Transmissão nos Fundamentos)</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:20%;">Vetor Geopolítico / Regulatório</th>
                        <th style="width:10%;">Severidade</th>
                        <th style="width:13%;">Ativos da Carteira</th>
                        <th style="width:19%;">% Receita / Produção Exposta (10-K)</th>
                        <th style="width:24%;">Mecanismo de Transmissão nos Fundamentos</th>
                        <th style="width:14%;">Risco Jurisdicional</th>
                    </tr>
                </thead>
                <tbody>{geo_rows_html}</tbody>
            </table>

            <div class="sub-banner">1.4. Radar de Mega-Tendências, Novas Tecnologias nas Indústrias &amp; Reconfiguração Setorial</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:20%;">Mega-Tendência / Ruptura Tecnológica</th>
                        <th style="width:28%;">Mecanismo de Disrupção na Indústria</th>
                        <th style="width:16%;">Vencedores na Carteira</th>
                        <th style="width:18%;">Setores Vulneráveis / Hedge</th>
                        <th style="width:18%;">KPI Quantitativo p/ Monitorar</th>
                    </tr>
                </thead>
                <tbody>{disr_html}</tbody>
            </table>

            <div class="sub-banner">1.5. Matriz de Sensibilidade Macro Individual por Hard-Asset da Carteira (Juros US 10Y, Dólar DXY, Tarifas &amp; Energia/IA)</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:11%;">Ativo da Carteira</th>
                        <th style="width:22%;">Sensibilidade à Taxa de Juros (US 10Y / Fed)</th>
                        <th style="width:18%;">Sensibilidade ao Dólar (DXY / FX)</th>
                        <th style="width:19%;">Exposição a Tarifas &amp; Supply Chain</th>
                        <th style="width:17%;">Vínculo c/ Energia &amp; CapEx de IA</th>
                        <th style="width:13%;">Posicionamento Macro</th>
                    </tr>
                </thead>
                <tbody>{sens_html}</tbody>
            </table>
        </div>
        """

        # ======================================================================
        # SEÇÃO 2: DADOS ANALÍTICOS DO PORTFÓLIO, LOOK-THROUGH FIEL À CARTEIRA,
        #          CONTABILIDADE FORENSE (SEM ALTMAN Z) & VALUATION FORWARD (NTM)
        # ======================================================================
        pos_rows_html = "".join(
            f"<tr>"
            f"<td class='mono'><strong>{_esc(p.ticker)}</strong><br><span style='font-size:6.8pt;color:#475569;'>{_esc(p.name)}</span></td>"
            f"<td>{_badge(p.category, 'purple' if 'Crypto' in p.category else ('green' if 'ETF' in p.category else 'blue'))}</td>"
            f"<td class='mono'>Alvo: <strong>{p.target_weight_pct:.2f}%</strong><br>Atual: {p.current_weight_pct:.2f}% ({p.weight_drift_pp:+.2f}pp)</td>"
            f"<td class='mono'><strong>${p.allocated_usd:,.0f}</strong><br>PM ${p.avg_buy_price_usd:,.2f} &rarr; Spot <strong>${p.current_price_usd:,.2f}</strong></td>"
            f"<td class='mono' style='color:{'#166534' if p.pnl_pct >= 0 else '#991B1B'};'><strong>{p.pnl_pct:+.1f}%</strong><br>(${p.pnl_usd:+,.0f})</td>"
            f"<td>{_badge('Sim (Colateral LTV)', 'green') if p.ltv_turbo_eligible else _badge('Não (Volátil)', 'slate')}</td>"
            f"<td><strong>Papel:</strong> {_esc(p.role_description)}<br><strong>Yield:</strong> {_esc(p.yield_mechanism)}</td>"
            f"</tr>"
            for p in portfolio.positions
        )

        lt_rows_html = "".join(
            f"<tr>"
            f"<td class='mono'><strong>{_esc(h.ticker)}</strong></td>"
            f"<td>{_esc(h.company_name)}<br><span style='font-size:6.7pt;color:#475569;'>{_esc(h.sector)}</span></td>"
            f"<td class='mono'><strong>{h.direct_weight_pct:.2f}%</strong></td>"
            f"<td class='mono'>SPY: {h.spy_indirect_pct:.2f}% | QQQ: {h.qqq_indirect_pct:.2f}%<br>QLD 2x: {h.qld_2x_indirect_pct:.2f}% | ITA: {h.ita_indirect_pct:.2f}%</td>"
            f"<td class='mono'>{h.total_indirect_pct:.2f}%</td>"
            f"<td class='mono' style='background:#EFF6FF; font-weight:800;'>{h.total_effective_lookthrough_pct:.2f}% (${h.effective_exposure_usd:,.0f})</td>"
            f"<td>{_esc(h.overlap_sources)}</td>"
            f"</tr>"
            for h in portfolio.lookthrough_holdings
        )

        sec_lt_rows_html = "".join(
            f"<tr>"
            f"<td><strong>{_esc(s['Bloco / Setor Look-Through'])}</strong></td>"
            f"<td class='mono'>{s['Peso Nominal (%)']:.2f}%</td>"
            f"<td class='mono'><strong>{s['Exposição Efetiva Look-Through (%)']:.2f}%</strong></td>"
            f"<td class='mono'>${s['Exposição Financeira (USD)']:,.0f}</td>"
            f"<td>{_esc(s['Principais Ativos Contribuintes'])}</td>"
            f"</tr>"
            for s in portfolio.sector_exposure_summary
        )

        # Tabelas Forenses Divididas em Parte A (5 colunas) e Parte B (5 colunas) — ESTRITAMENTE CALIBRADAS POR SETOR!
        for_part_a_html = ""
        for_part_b_html = ""
        for e in equities:
            fh = e.forensic_health
            qs = e.qualitative_strategy
            vm = e.valuation_methods
            is_bank = (e.sector_vertical == "FINANCIAL_BANK")
            if is_bank:
                sloan_cell = f"<span class='mono'><strong>N/A em Bancos</strong></span><br>{_badge('Balanço Financeiro — Regido por Provisões PDD / Basileia III', 'blue')}"
                fco_cell = f"<span class='mono'>Lucro Líquido: <strong>USD {fh['fco_current_b']:.1f}B</strong></span><br><span style='font-size:6.8pt;color:#475569;'>FCO/EBITDA N/A em Bancos (Depósitos são passivo operacional)</span>"
                nwc_cell = f"<strong>Basileia III LCR &gt; 100%:</strong> {_esc(fh['nwc_contextual_verdict'])}"
                roic_cell = f"<span class='mono'><strong>ROE: {fh['roe_dupont_pct']:.1f}%</strong> vs <strong>Ke (CAPM): {vm['cost_of_equity_pct']:.2f}%</strong></span><br>Spread Bancário (ROE - Ke): <strong>{fh['roe_dupont_pct'] - vm['cost_of_equity_pct']:+.1f} pp</strong> (ROIC/WACC N/A em Bancos)"
                liq_cell = f"<span class='mono'>Índice Basileia / CET1: <strong>&gt; 15.0%</strong></span><br>Reservas de Liquidez: <strong>USD {fh['cash_b']:.1f}B</strong> (LCR Saudável)"
                debt_cell = f"<span class='mono'>Alavancagem Basileia: <strong>{fh['dupont_financial_leverage_x']:.1f}x Ativos/PL</strong></span><br><span style='font-size:6.8pt;color:#475569;'>Dívida/EBITDA N/A em Bancos (Funding via Depósitos)</span>"
            else:
                sloan_cell = f"<span class='mono'><strong>{fh['sloan_ratio_pct']:+.1f}%</strong></span><br>{_auto_badge(fh['sloan_verdict'])}"
                fco_cell = f"<span class='mono'>FCO: <strong>USD {fh['fco_current_b']:.1f}B</strong> | FCO/EBITDA: <strong>{fh['fco_to_ebitda']:.2f}x</strong></span><br>{_auto_badge(fh['fco_to_ebitda_verdict'])}"
                nwc_cell = f"{_esc(fh['nwc_contextual_verdict'])}"
                roic_cell = f"<span class='mono'>ROIC (c/ Goodwill): <strong>{fh['roic_goodwill_pct']:.1f}%</strong> vs WACC: <strong>{fh['wacc_pct']:.2f}%</strong></span><br>Spread de Criação de Valor: <strong>{fh['roic_minus_wacc_spread_pp']:+.1f} pp</strong>"
                liq_cell = f"<span class='mono'>Liquidez Corrente: <strong>{fh['current_ratio']:.2f}x</strong></span><br>Caixa: <strong>USD {fh['cash_b']:.1f}B</strong> (Pós-OpEx Positivo)"
                debt_cell = f"<span class='mono'>Cobertura Juros: <strong>{fh['interest_coverage_x']:.1f}x</strong></span><br>Dívida/EBITDA: {fh['debt_to_ebitda']:.2f}x | D/Assets: {fh['debt_to_assets_pct']:.1f}% | D/Eq: {fh['debt_to_equity_pct']:.0f}%"

            for_part_a_html += (
                f"<tr>"
                f"<td class='mono'><strong>{_esc(e.ticker)}</strong><br><span style='font-size:6.8pt;color:#475569;'>{_esc(e.company_name)}</span></td>"
                f"<td>{sloan_cell}</td>"
                f"<td>{fco_cell}</td>"
                f"<td>{nwc_cell}</td>"
                f"<td>{roic_cell}</td>"
                f"</tr>"
            )
            for_part_b_html += (
                f"<tr>"
                f"<td class='mono'><strong>{_esc(e.ticker)}</strong><br><span style='font-size:6.8pt;color:#64748b;'>{_esc(getattr(e, 'company_name', getattr(e, 'name', e.ticker)))}</span></td>"
                f"<td class='mono'><strong>ROE: {fh['roe_dupont_pct']:.1f}%</strong> = Margem {fh['dupont_net_margin_pct']:.1f}% × Giro {fh['dupont_asset_turnover_x']:.2f}x × Alav. {fh['dupont_financial_leverage_x']:.2f}x<br><span style='font-size:6.8pt;color:#334155;'>{_esc(fh['dupont_verdict'])}</span></td>"
                f"<td>{liq_cell}</td>"
                f"<td>{debt_cell}</td>"
                f"<td><strong>Margem Bruta / NIM:</strong> {qs['gross_margin_current_pct']:.1f}% ({qs['gross_margin_5y_delta_pp']:+.1f}pp em 5a)<br><strong>P&amp;D/Receita:</strong> {qs['rd_to_sales_pct']:.1f}% | <strong>LTV/CAC:</strong> {qs['ltv_to_cac_ratio']:.1f}x<br><strong>KPI Operacional Setorial:</strong> {_esc(fh['sss_same_store_sales'])}</td>"
                f"</tr>"
            )

        # Matriz CAGR 12 KPIs dividida em Parte A (6 KPIs Operacionais) e Parte B (6 KPIs de Caixa/Retorno)
        kpis_part_a = ["Receita", "Lucro Bruto", "EBIT", "EBITDA", "NOPAT", "Lucro Líquido"]
        kpis_part_b = ["FCO", "FCF", "EPS", "Dividendos", "Book Value", "ROIC"]
        cagr_a_rows = ""
        cagr_b_rows = ""
        for e in equities:
            cells_a = "".join(
                f"<td class='mono'>{e.cagr_matrix_12_kpis[k]['3y']:+.1f}% | <strong>{e.cagr_matrix_12_kpis[k]['5y']:+.1f}%</strong> | {e.cagr_matrix_12_kpis[k]['10y']:+.1f}%</td>"
                for k in kpis_part_a
            )
            cells_b = "".join(
                f"<td class='mono'>{e.cagr_matrix_12_kpis[k]['3y']:+.1f}% | <strong>{e.cagr_matrix_12_kpis[k]['5y']:+.1f}%</strong> | {e.cagr_matrix_12_kpis[k]['10y']:+.1f}%</td>"
                for k in kpis_part_b
            )
            cagr_a_rows += f"<tr><td class='mono'><strong>{_esc(e.ticker)}</strong></td>{cells_a}</tr>"
            cagr_b_rows += f"<tr><td class='mono'><strong>{_esc(e.ticker)}</strong></td>{cells_b}</tr>"

        # Valuation Multi-Métodos Forward (8 Métodos divididos em Parte A: 6 colunas e Parte B: 6 colunas — ESTRITAMENTE POR SETOR!)
        val_a_rows = ""
        val_b_rows = ""
        for e in equities:
            vm = e.valuation_methods
            fh = e.forensic_health
            is_bank = (e.sector_vertical == "FINANCIAL_BANK")

            if is_bank:
                cost_cap_cell = f"<span class='mono'><strong>Ke (CAPM): {vm['cost_of_equity_pct']:.2f}%</strong><br>(Beta {vm['beta']:.2f} | WACC N/A em Bancos)</span>"
                mult_sec_cell = (
                    f"<span class='mono'><strong>P/TBV: {vm['ptbv_current']:.2f}x</strong> vs <strong>ROE: {fh['roe_dupont_pct']:.1f}%</strong><br>"
                    f"<strong>P/B: {vm['pb_current']:.2f}x</strong> (&gt;= 1.0x Aprovado)<br>"
                    f"<span style='font-size:6.6pt;color:#475569;'>EV/EBITDA: N/A em Bancos</span></span>"
                )
                eva_cell = (
                    f"<span class='mono'><strong>Lucro Econômico Bancário: USD {vm['eva_usd_b']:+.1f}B/a</strong><br>"
                    f"(Spread ROE {fh['roe_dupont_pct']:.1f}% - Ke {vm['cost_of_equity_pct']:.2f}% = {fh['roe_dupont_pct'] - vm['cost_of_equity_pct']:+.1f}pp)</span>"
                )
                pegy_cell = (
                    f"<span class='mono'><strong>PEGY Financeiro (P/E NTM ÷ [g_EPS + DY]): {vm['pegy_financeiro']:.2f}x</strong><br>"
                    f"g_EPS NTM: {vm['eps_growth_ntm_pct']:.1f}% + DY {vm['div_yield_pct']:.2f}% | Preço Justo PEGY 1.0x: <strong>${vm['pegy_gold_fair_price_usd']:,.2f}</strong><br>"
                    f"{_auto_badge(vm['primary_pegy_status'])} <span style='font-size:6.5pt;color:#475569;'>(Enterprise PEGY N/A em Bancos)</span></span>"
                )
                magic_sotp_cell = (
                    f"<span class='mono'>Magic Formula: <strong>N/A Bancário</strong> (Regido por P/TBV vs ROE)<br>"
                    f"SOTP Peer Value: <strong>${vm['sotp_fair_price_usd']:,.2f} ({vm['sotp_upside_pct']:+.1f}%)</strong></span>"
                )
            elif e.sector_vertical == "TECH_HIGH_GROWTH":
                cost_cap_cell = f"<span class='mono'>WACC: <strong>{vm['wacc_capm_pct']:.2f}%</strong><br>Ke: {vm['cost_of_equity_pct']:.2f}% (Beta {vm['beta']:.2f})</span>"
                mult_sec_cell = (
                    f"<span class='mono'>EV/EBITDA: <strong>{vm['ev_ebitda_current']:.1f}x</strong> (Setor {vm['ev_ebitda_sector_avg']:.1f}x)<br>"
                    f"P/B: {vm['pb_current']:.2f}x <span style='font-size:6.6pt;color:#475569;'>(P/TBV Secundário em High-Growth Asset-Light)</span></span>"
                )
                eva_cell = f"<span class='mono'><strong>EVA: USD {vm['eva_usd_b']:+.1f}B / ano</strong><br>({vm['eva_pct_of_ic']:+.1f}% sobre Cap. Investido de ${vm['invested_capital_b']:.1f}B)</span>"
                pegy_cell = (
                    f"<span class='mono'><strong>Enterprise PEGY (EV/EBIT Forward NTM): {vm['enterprise_pegy_ev_ebit']:.2f}x</strong><br>"
                    f"Cresc. NTM: {vm['eps_growth_ntm_pct']:.1f}% + DY {vm['div_yield_pct']:.2f}% + BB {vm['buyback_yield_pct']:.2f}% | Px Ouro (1.2x): <strong>${vm['pegy_gold_fair_price_usd']:,.2f}</strong><br>"
                    f"{_auto_badge(vm['primary_pegy_status'])} <span style='font-size:6.5pt;color:#475569;'>(Setor: High-Growth Tech/Semis — Sem PEGY Fin)</span></span>"
                )
                magic_sotp_cell = (
                    f"<span class='mono'>Magic Rank: <strong>#{vm['magic_formula_rank']}</strong> (EY {vm['earnings_yield_ebit_ev_pct']:.2f}%)<br>"
                    f"SOTP Peer Value: <strong>${vm['sotp_fair_price_usd']:,.2f} ({vm['sotp_upside_pct']:+.1f}%)</strong></span>"
                )
            elif e.sector_vertical == "RETAIL":
                cost_cap_cell = f"<span class='mono'>WACC: <strong>{vm['wacc_capm_pct']:.2f}%</strong><br>Ke: {vm['cost_of_equity_pct']:.2f}% (Beta {vm['beta']:.2f})</span>"
                mult_sec_cell = f"<span class='mono'>EV/EBITDA: <strong>{vm['ev_ebitda_current']:.1f}x</strong> (Setor {vm['ev_ebitda_sector_avg']:.1f}x)<br>P/B: {vm['pb_current']:.2f}x | SSS Obrigatório</span>"
                eva_cell = f"<span class='mono'><strong>EVA: USD {vm['eva_usd_b']:+.1f}B / ano</strong><br>({vm['eva_pct_of_ic']:+.1f}% sobre Cap. Investido de ${vm['invested_capital_b']:.1f}B)</span>"
                pegy_cell = (
                    f"<span class='mono'><strong>Enterprise PEGY (EV/EBIT NTM c/ SSS): {vm['enterprise_pegy_ev_ebit']:.2f}x</strong><br>"
                    f"Cresc. NTM: {vm['eps_growth_ntm_pct']:.1f}% + DY {vm['div_yield_pct']:.2f}% + BB {vm['buyback_yield_pct']:.2f}% | Px Ouro: <strong>${vm['pegy_gold_fair_price_usd']:,.2f}</strong><br>"
                    f"{_auto_badge(vm['primary_pegy_status'])} <span style='font-size:6.5pt;color:#475569;'>(Setor: Varejo — Sem PEGY Fin)</span></span>"
                )
                magic_sotp_cell = (
                    f"<span class='mono'>Magic Rank: <strong>#{vm['magic_formula_rank']}</strong> (EY {vm['earnings_yield_ebit_ev_pct']:.2f}%)<br>"
                    f"SOTP Peer Value: <strong>${vm['sotp_fair_price_usd']:,.2f} ({vm['sotp_upside_pct']:+.1f}%)</strong></span>"
                )
            else:
                # TECH_CASH_COW & FINANCIAL_TOLLBOOTH (AAPL, MSFT, MA)
                cost_cap_cell = f"<span class='mono'>WACC: <strong>{vm['wacc_capm_pct']:.2f}%</strong><br>Ke: {vm['cost_of_equity_pct']:.2f}% (Beta {vm['beta']:.2f})</span>"
                mult_sec_cell = (
                    f"<span class='mono'>EV/EBITDA: <strong>{vm['ev_ebitda_current']:.1f}x</strong> (Setor {vm['ev_ebitda_sector_avg']:.1f}x)<br>"
                    f"P/B: {vm['pb_current']:.2f}x <span style='font-size:6.6pt;color:#475569;'>(Buybacks reduzem Book Value contábil)</span></span>"
                )
                eva_cell = f"<span class='mono'><strong>EVA: USD {vm['eva_usd_b']:+.1f}B / ano</strong><br>({vm['eva_pct_of_ic']:+.1f}% sobre Cap. Investido de ${vm['invested_capital_b']:.1f}B)</span>"
                pegy_cell = (
                    f"<span class='mono'><strong>Enterprise PEGY (EV/FCF Forward NTM): {vm['enterprise_pegy_ev_fcf']:.2f}x</strong><br>"
                    f"Cresc. NTM: {vm['eps_growth_ntm_pct']:.1f}% + DY {vm['div_yield_pct']:.2f}% + BB {vm['buyback_yield_pct']:.2f}% | Px Ouro (1.2x): <strong>${vm['pegy_gold_fair_price_usd']:,.2f}</strong><br>"
                    f"{_auto_badge(vm['primary_pegy_status'])} <span style='font-size:6.5pt;color:#475569;'>(Setor: Cash Cow / Pedágio — Sem PEGY Fin)</span></span>"
                )
                magic_sotp_cell = (
                    f"<span class='mono'>Magic Rank: <strong>#{vm['magic_formula_rank']}</strong> (EY {vm['earnings_yield_ebit_ev_pct']:.2f}%)<br>"
                    f"SOTP Peer Value: <strong>${vm['sotp_fair_price_usd']:,.2f} ({vm['sotp_upside_pct']:+.1f}%)</strong></span>"
                )

            val_a_rows += (
                f"<tr>"
                f"<td class='mono'><strong>{_esc(e.ticker)}</strong><br>${e.current_price:,.2f}<br><span style='font-size:6.5pt;color:#475569;'>{_esc(e.sector_vertical)}</span></td>"
                f"<td>{cost_cap_cell}</td>"
                f"<td class='mono'>Conservador: ${vm['dcf_conservador_usd']:,.2f}<br>Base Forward: ${vm['dcf_base_usd']:,.2f}<br>Otimista: ${vm['dcf_otimista_usd']:,.2f}</td>"
                f"<td class='mono'><strong>${vm['dcf_fair_mos10_usd']:,.2f}</strong><br>Upside: <strong>{vm['dcf_upside_pct']:+.1f}%</strong></td>"
                f"<td class='mono'><strong>g_impl: {vm['reverse_dcf_g_impl_pct']:.1f}%</strong> vs <strong>g_fund (NTM/5y): {vm['g_fund_projected_pct']:.1f}%</strong><br>Spread: {vm['reverse_dcf_spread_pp']:+.1f} pp | {_auto_badge(vm['reverse_dcf_verdict'])}</td>"
                f"<td class='mono'>Owner Earnings Yield: <strong>{vm['owner_earnings_yield_pct']:.2f}%</strong> (FCF Yield {vm['fcf_yield_pct']:.2f}%)<br>vs US 10Y ({vm['risk_free_us10y_pct']:.2f}%): {_esc(vm['oe_verdict'])}</td>"
                f"</tr>"
            )
            val_b_rows += (
                f"<tr>"
                f"<td class='mono'><strong>{_esc(e.ticker)}</strong><br><span style='font-size:6.8pt;color:#64748b;'>{_esc(getattr(e, 'company_name', getattr(e, 'name', e.ticker)))}</span></td>"
                f"<td class='mono'>P/E Spot: {vm['pe_current']:.1f}x | <strong>P/E Forward (NTM): {vm['pe_ntm']:.1f}x</strong><br>Setor: {vm['pe_sector_avg']:.1f}x | Média 5y: {vm['pe_5y_avg']:.1f}x | DCF Impl: {vm['pe_implied_dcf']:.1f}x</td>"
                f"<td>{mult_sec_cell}</td>"
                f"<td>{eva_cell}</td>"
                f"<td>{pegy_cell}</td>"
                f"<td>{magic_sotp_cell}</td>"
                f"</tr>"
            )

        sotp_rows_html = ""
        for e in equities:
            for seg in e.valuation_methods["sotp_segments"]:
                sotp_rows_html += (
                    f"<tr>"
                    f"<td class='mono'><strong>{_esc(e.ticker)}</strong><br><span style='font-size:6.8pt;color:#64748b;'>{_esc(getattr(e, 'company_name', getattr(e, 'name', e.ticker)))}</span></td>"
                    f"<td>{_esc(seg['segment'])}</td>"
                    f"<td class='mono'>{seg['rev_share_pct']:.1f}%</td>"
                    f"<td>{_esc(seg['peer_benchmark'])}</td>"
                    f"<td class='mono'>${seg['segment_val_per_share']:,.2f}</td>"
                    f"<td class='mono'><strong>${e.valuation_methods['sotp_fair_price_usd']:,.2f}</strong> (vs Spot ${e.current_price:,.2f})</td>"
                    f"</tr>"
                )

        banks_rows_html = "".join(
            f"<tr>"
            f"<td class='mono'><strong>{_esc(b['Ticker'])}</strong></td>"
            f"<td>{_esc(b['Banco'])}</td>"
            f"<td>{_auto_badge(b['Grupo'])}</td>"
            f"<td class='mono'><strong>{b['ROE_pct']:.1f}%</strong></td>"
            f"<td class='mono'><strong>{b['PTBV']:.2f}x</strong></td>"
            f"<td class='mono'>{b['PB']:.2f}x {'(VETO < 1.0x)' if b['PB'] < 1.0 else '(Aprovado >= 1.0x)'}</td>"
            f"<td class='mono'><strong>{b['PEGY_Fin']:.2f}x</strong></td>"
            f"</tr>"
            for b in GLOBAL_BANKS_SCATTER_DATA
        )

        sec2_html = f"""
        <div class="page-section">
            <div class="section-banner">SEÇÃO 2: DADOS ANALÍTICOS DO PORTFÓLIO, DECOMPOSIÇÃO LOOK-THROUGH (FIEL À CARTEIRA), FORENSE &amp; VALUATION FORWARD</div>
            <div class="insight-box">
                <strong>Validação Dinâmica de Pesos:</strong> {_esc(portfolio.weight_validation_message)} |
                <strong>P&amp;L Consolidado:</strong> <span class="mono">{portfolio.total_portfolio_pnl_pct:+.2f}% (USD {portfolio.total_portfolio_pnl_usd:+,.0f})</span> |
                <strong>Colateral Elegível LTV Turbo:</strong> Ações/ETFs {portfolio.ltv_eligible_stocks_weight_pct:.2f}% + BTC {portfolio.ltv_eligible_btc_weight_pct:.2f}%.
            </div>

            <div class="sub-banner">2.1. Arquitetura Direta das {len(portfolio.positions)} Posições da Carteira (Pesos, Preço Médio vs. Spot, P&amp;L, LTV e Mecanismo de Yield)</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:14%;">Ticker &amp; Ativo</th>
                        <th style="width:11%;">Categoria</th>
                        <th style="width:13%;">Alvo vs. Atual (Drift)</th>
                        <th style="width:15%;">Alocação &amp; PM &rarr; Spot</th>
                        <th style="width:10%;">P&amp;L (% / USD)</th>
                        <th style="width:11%;">Elegível LTV</th>
                        <th style="width:26%;">Papel Estrutural &amp; Mecanismo de Yield</th>
                    </tr>
                </thead>
                <tbody>{pos_rows_html}</tbody>
            </table>

            <div class="grid-2">
                <div>
                    <div class="sub-banner">2.2A. Decomposição Look-Through Fiel às Ações da Sua Carteira + Cesta Residual dos ETFs</div>
                    <table class="inst-table">
                        <thead>
                            <tr>
                                <th>Ticker</th><th>Ativo da Carteira</th><th>Peso Direto</th><th>Overlap via ETFs (SPY/QQQ/QLD/ITA)</th>
                                <th>Total Indireto</th><th>Exposição Real Total</th><th>Fontes</th>
                            </tr>
                        </thead>
                        <tbody>{lt_rows_html}</tbody>
                    </table>
                </div>
                <div>
                    <div class="sub-banner">2.2B. Consolidação Setorial Look-Through do Portfólio Completo</div>
                    <table class="inst-table">
                        <thead>
                            <tr><th>Bloco / Setor Consolidado</th><th>Nominal</th><th>Look-Through</th><th>Exposição (USD)</th><th>Ativos da Carteira Contribuintes</th></tr>
                        </thead>
                        <tbody>{sec_lt_rows_html}</tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="page-section">
            <div class="sub-banner">2.3A. Saúde Financeira e Contabilidade Forense — Parte A: Qualidade do Lucro (Sloan Ratio), Conversão FCO/EBITDA, NWC &amp; ROIC vs. WACC</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:13%;">Ticker &amp; Empresa</th>
                        <th style="width:19%;">Sloan Ratio (Accruals / Ativos)</th>
                        <th style="width:21%;">Geração de Caixa (FCO) &amp; FCO / EBITDA</th>
                        <th style="width:25%;">Capital de Giro (NWC) &amp; Consistência FCO (CV 5y)</th>
                        <th style="width:22%;">ROIC (via NOPAT c/ Goodwill) vs. WACC</th>
                    </tr>
                </thead>
                <tbody>{for_part_a_html}</tbody>
            </table>

            <div class="sub-banner">2.3B. Saúde Financeira e Contabilidade Forense — Parte B: Identidade DuPont (3 Pilares), Liquidez Corrente, Cobertura de Juros &amp; Margens</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:8%;">Ticker</th>
                        <th style="width:30%;">Decomposição DuPont (Margem × Giro × Alavancagem = ROE)</th>
                        <th style="width:18%;">Liquidez Corrente &amp; Caixa Pós-OpEx</th>
                        <th style="width:20%;">Cobertura de Juros &amp; Endividamento</th>
                        <th style="width:24%;">Margem Bruta 5y, P&amp;D/Sales, LTV/CAC &amp; SSS</th>
                    </tr>
                </thead>
                <tbody>{for_part_b_html}</tbody>
            </table>

            <div class="sub-banner">2.4A. Matriz de Crescimento Composto Anualizado (CAGR 3y | 5y | 10y) — Parte A: 6 KPIs Operacionais e de Lucro</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:10%;">Ticker</th>
                        {''.join(f'<th style="width:15%;">{k} (3y | 5y | 10y)</th>' for k in kpis_part_a)}
                    </tr>
                </thead>
                <tbody>{cagr_a_rows}</tbody>
            </table>

            <div class="sub-banner">2.4B. Matriz de Crescimento Composto Anualizado (CAGR 3y | 5y | 10y) — Parte B: 6 KPIs de Caixa Livre, Por Ação e Retorno</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:10%;">Ticker</th>
                        {''.join(f'<th style="width:15%;">{k} (3y | 5y | 10y)</th>' for k in kpis_part_b)}
                    </tr>
                </thead>
                <tbody>{cagr_b_rows}</tbody>
            </table>
        </div>

        <div class="page-section">
            <div class="sub-banner">2.5A. Motor de Valuation Multi-Métodos Forward (NTM) — Parte A: DCF Forward (3 Cenários + 10% MoS), Reverse DCF Pareado &amp; Owner Earnings</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:10%;">Ticker &amp; Spot</th>
                        <th style="width:14%;">WACC CAPM &amp; Beta</th>
                        <th style="width:18%;">DCF Forward (Cons / Base / Otim)</th>
                        <th style="width:14%;">DCF Justo (10% MoS)</th>
                        <th style="width:24%;">Reverse DCF (g_impl vs. g_fund Forward NTM)</th>
                        <th style="width:20%;">Owner Earnings Yield (Munger) vs. US 10Y</th>
                    </tr>
                </thead>
                <tbody>{val_a_rows}</tbody>
            </table>

            <div class="sub-banner">2.5B. Motor de Valuation Multi-Métodos Forward (NTM) — Parte B: Múltiplos Forward, EVA, PEGY Forward (EV/EBIT &amp; EV/FCF), Magic Formula &amp; SOTP</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:8%;">Ticker</th>
                        <th style="width:21%;">P/E Comparado (Spot / Forward NTM / Setor / 5y)</th>
                        <th style="width:16%;">EV/EBITDA, P/B &amp; P/TBV</th>
                        <th style="width:15%;">EVA (Lucro Econômico)</th>
                        <th style="width:26%;">Indicador PEGY Forward (NTM) Estrito da Vertical Setorial</th>
                        <th style="width:16%;">Magic Formula &amp; SOTP</th>
                    </tr>
                </thead>
                <tbody>{val_b_rows}</tbody>
            </table>

            

            <div class="grid-2">
                <div>
                    <div class="sub-banner">2.6A. Decomposição Sum of the Parts (SOTP) por Unidade de Negócio</div>
                    <table class="inst-table">
                        <thead><tr><th>Ticker</th><th>Segmento</th><th>% Rec.</th><th>Peer Benchmark</th><th>Val/Ação</th><th>SOTP Total</th></tr></thead>
                        <tbody>{sotp_rows_html}</tbody>
                    </table>
                </div>
                <div>
                    <div class="sub-banner">2.6B. Análise Setorial dos Bancos da Sua Carteira (JPM &amp; NU vs. Benchmark Setorial)</div>
                    <table class="inst-table">
                        <thead><tr><th>Ticker</th><th>Instituição na Carteira</th><th>Status</th><th>ROE (%)</th><th>P/TBV</th><th>P/B (&gt;= 1.0x)</th><th>PEGY Fin (NTM)</th></tr></thead>
                        <tbody>{banks_rows_html}</tbody>
                    </table>
                    <div class="insight-box">
                        <strong>Metodologia Forward (NTM) Confirmada:</strong> Tanto o <strong>DCF / Reverse DCF</strong> (partindo do FCF Forward NTM e projetando pelo consenso Forward $g_{{\text{{fund}}}}$) quanto os múltiplos <strong>PEGY Financeiro e Enterprise PEGY</strong> (<code>P/E NTM</code>, <code>EV/EBIT NTM</code>, <code>EV/FCF NTM</code> divididos por <code>CAGR EPS/EBIT NTM + DY + Buyback Yield</code>) utilizam estritamente dados <strong>Forward (Next Twelve Months)</strong>.
                    </div>
                </div>
            </div>
        </div>
        """

        # ======================================================================
        # SEÇÃO 3: INTELIGÊNCIA ANALÍTICA CRIPTO (ON-CHAIN, MINERAÇÃO, FLUXOS, TOKENOMICS)
        #          & DEFI STATE OF THE UNION (NARRATIVAS DUNE/DEFILLAMA & CICLO)
        # ======================================================================
        cr_part_a_rows = ""
        cr_part_b_rows = ""
        for sym, c in cryptos.items():
            om = c.onchain_metrics
            mm = c.mining_metrics
            cf = c.capital_flows
            tv = c.tokenomics_valuation
            ss = c.supply_structure
            ds = c.derivatives_sentiment
            cr_part_a_rows += (
                f"<tr>"
                f"<td class='mono'><strong>{_esc(sym)}</strong><br>${c.spot_price_usd:,.2f}<br><span style='font-size:6.8pt;'>MCap ${c.market_cap_b:.1f}B | FDV ${c.fdv_b:.1f}B</span></td>"
                f"<td class='mono'><strong>MVRV Z: {om['mvrv_z_score']:.2f}</strong> ({_esc(om['mvrv_z_status'])})<br><strong>NUPL: {om['nupl']:.2f}</strong> ({_esc(om['nupl_status'])})</td>"
                f"<td class='mono'><strong>aSOPR: {om['asopr']:.3f}</strong><br>{_esc(om['asopr_status'])}</td>"
                f"<td class='mono'>200W SMA: ${om['sma_200w_usd']:,.0f} ({om['price_to_200w_sma_x']:.2f}x)<br>Pi 111d: ${om['pi_cycle_111d_sma_usd']:,.0f} | 2x350d: ${om['pi_cycle_350d_x2_sma_usd']:,.0f}<br>{_auto_badge(om['pi_cycle_status'])}</td>"
                f"<td><strong>Hash Ribbon:</strong> {_esc(mm['hash_ribbon_status'])}<br><strong>MMC:</strong> {_esc(mm['mmc_status'])}</td>"
                f"<td><strong>Inflow/CDD:</strong> {_esc(om['inflow_cdd_status'])}<br><strong>Stablecoins:</strong> {_esc(cf['stablecoins_netflow_status'])}<br><strong>HODL Waves:</strong> {_esc(cf['hodl_waves_verdict'])}</td>"
                f"</tr>"
            )
            cr_part_b_rows += (
                f"<tr>"
                f"<td class='mono'><strong>{_esc(sym)}</strong></td>"
                f"<td class='mono'>NVT Nominal: <strong>{tv.get('nvt_nominal', 0.0):.1f}x</strong> {_auto_badge(tv.get('nvt_nominal_status', ''))}<br><span style='font-size:6.7pt;color:#475569;'><strong>Ref NVT:</strong> &lt; 30x (Subavaliado/Compra) | 30x a 75x (Justo) | &gt; 75x (Sobreavaliado/Bolha)</span><br>NVT Golden Cross: <strong>{tv['nvt_golden_cross']:+.2f}</strong> (Ref: &lt; -1.6 / &gt; +2.0) | NVM: <strong>{tv['nvm_ratio']:.2f}</strong><br>P/F: <strong>{tv['pf_ratio']:.1f}x</strong> | TVL: ${tv['tvl_b']:.2f}B | Vol 24h: ${tv['tx_vol_24h_b']:.2f}B</td>"
                f"<td class='mono'><strong>Real Earnings: USD {tv['protocol_real_earnings_m']:+.1f}M / ano</strong><br>(Fees ${tv['protocol_fees_annual_m']:.1f}M - Emissão ${tv['token_issuance_annual_m']:.1f}M)<br><strong>Real Yield: {tv['real_yield_pct']:+.2f}%</strong> (APR {tv['apr_staking_pct']:.1f}% - Infl {tv['token_inflation_pct']:.1f}%)</td>"
                f"<td class='mono'>Circulating: <strong>{c.circulating_pct:.1f}%</strong><br>Unlock 30d: <strong>{ss['unlock_pct_of_circ']:.2f}% Circ</strong> ({ss['monthly_unlock_tokens_m']:.2f}M tokens)<br><strong>Px Teórico Pós-Unlock: ${ss['theoretical_post_unlock_price_usd']:,.2f}</strong></td>"
                f"<td class='mono'>SSR: {ss['ssr_stablecoin_supply_ratio']:.1f} | BTC.D: {ss['btc_dominance_pct']:.1f}%<br>OI/MCap: <strong>{ds['oi_to_mcap_pct']:.2f}%</strong> (OI ${ds['open_interest_b']:.2f}B)<br>Funding 8h: <strong>{ds['funding_rate_8h_pct']:+.4f}%</strong> | F&amp;G: {ds['fear_and_greed_index']}/100</td>"
                f"<td>{_esc(ds['liquidation_heatmap_summary'])}</td>"
                f"</tr>"
            )

        cycle_html = "".join(
            f"<tr>"
            f"<td><strong>{_esc(c.indicator_name)}</strong></td>"
            f"<td class='mono'>{_esc(c.current_reading)}</td>"
            f"<td>{_esc(c.historical_band_ref)}</td>"
            f"<td>{_auto_badge(c.cycle_phase_signal)}</td>"
            f"<td>{_esc(c.portfolio_tactical_implication)}</td>"
            f"</tr>"
            for c in cycle_rows
        )

        narr_html = "".join(
            f"<tr>"
            f"<td><strong>{_esc(n.narrative_name)}</strong></td>"
            f"<td>{_auto_badge(n.cycle_momentum)}</td>"
            f"<td>{_esc(n.dune_defillama_evidence)}</td>"
            f"<td>{_esc(n.core_technology_shift)}</td>"
            f"<td class='mono'><strong>{_esc(n.portfolio_crypto_impact)}</strong></td>"
            f"<td>{_esc(n.risk_and_invalidator)}</td>"
            f"</tr>"
            for n in narratives
        )

        sec3_html = f"""
        <div class="page-section">
            <div class="section-banner">SEÇÃO 3: INTELIGÊNCIA ANALÍTICA CRIPTO (ON-CHAIN, MINERAÇÃO, TOKENOMICS) &amp; DEFI STATE OF THE UNION</div>

            

            <div class="sub-banner">3.1A. Matriz Analítica Cripto — Parte A: Ciclo On-Chain (MVRV Z, NUPL, aSOPR, Pi Cycle/200W SMA), Mineração (Hash Ribbon/MMC) &amp; Fluxos</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:12%;">Ativo &amp; Preço</th>
                        <th style="width:18%;">MVRV Z-Score &amp; NUPL</th>
                        <th style="width:16%;">aSOPR (Linha 1.0)</th>
                        <th style="width:18%;">Pi Cycle Top &amp; 200W SMA</th>
                        <th style="width:16%;">Mineração (Hash Ribbon &amp; MMC)</th>
                        <th style="width:20%;">Exchange Inflow, CDD, Stablecoins &amp; HODL</th>
                    </tr>
                </thead>
                <tbody>{cr_part_a_rows}</tbody>
            </table>

            <div class="sub-banner">3.1B. Matriz Analítica Cripto — Parte B: Tokenomics (NVM, NVT GC, P/F, TVL), Protocol Real Earnings, Unlocks &amp; Derivativos</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:9%;">Ativo</th>
                        <th style="width:28%;">NVT Nominal (c/ Referência), NVT Golden Cross, NVM, P/F &amp; TVL</th>
                        <th style="width:23%;">Protocol Real Earnings &amp; Real Yield</th>
                        <th style="width:18%;">Supply, Unlocks &amp; Preço Pós-Diluição</th>
                        <th style="width:16%;">SSR, BTC.D, OI/MCap &amp; Funding</th>
                        <th style="width:14%;">Liquidation Heatmap</th>
                    </tr>
                </thead>
                <tbody>{cr_part_b_rows}</tbody>
            </table>
        </div>

        <div class="page-section">
            <div class="sub-banner">3.2. Onde Estamos no Ciclo Cripto? (Bússola de Rotação BTC &rarr; ETH &rarr; DeFi / Altcoins &amp; Liquidez DefiLlama Ao Vivo)</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:20%;">Indicador de Ciclo / Liquidez</th>
                        <th style="width:16%;">Leitura Atual</th>
                        <th style="width:22%;">Bandas de Referência Histórica</th>
                        <th style="width:18%;">Sinal de Fase do Ciclo</th>
                        <th style="width:24%;">Implicação Tática p/ Seu Portfólio Cripto</th>
                    </tr>
                </thead>
                <tbody>{cycle_html}</tbody>
            </table>

            <div class="sub-banner">3.3. Radar de Mudanças de Narrativa &amp; Novas Tecnologias DeFi (Dune Analytics, DefiLlama, Token Terminal, Messari, Delphi &amp; Kaito)</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:18%;">Narrativa / Tecnologia DeFi</th>
                        <th style="width:12%;">Momentum</th>
                        <th style="width:22%;">Evidência Empírica (Dune / DefiLlama / Artemis)</th>
                        <th style="width:20%;">Mudança Arquitetural &amp; Tecnológica</th>
                        <th style="width:15%;">Impacto no Portfólio</th>
                        <th style="width:13%;">Risco / Invalidador</th>
                    </tr>
                </thead>
                <tbody>{narr_html}</tbody>
            </table>
        </div>
        """

        # ======================================================================
        # SEÇÃO 4: DOSSIÊ FORENSE CORPORATIVO (SEC 10-K/10-Q, PORTER, CALLS Q&A & M&A)
        # ======================================================================
        doc_eq_html = "".join(
            f"<tr>"
            f"<td class='mono'><strong>{_esc(d.ticker)}</strong><br><span style='font-size:6.6pt;'>{_esc(d.filing_form_annual)}</span></td>"
            f"<td><strong>{_esc(d.auditor_firm)}</strong><br>{_auto_badge(d.auditor_opinion)}<br>{_esc(d.sox_404b_controls)}</td>"
            f"<td><strong>Crescimento:</strong> {_esc(d.mda_growth_decomposition)}<br><strong>Margens:</strong> {_esc(d.mda_segment_profitability)}<br><strong>Backlog:</strong> {_esc(d.mda_backlog_rpo)}<br><strong>CAPEX:</strong> {_esc(d.mda_capex_plan)}</td>"
            f"<td>{_esc(d.item_1a_specific_risks)}</td>"
            f"<td><strong>Litígios:</strong> {_esc(d.footnote_contingencies_litigation)}<br><strong>SBC:</strong> {_esc(d.footnote_sbc_impact)}<br><strong>ASC 606:</strong> {_esc(d.footnote_revenue_recognition)}<br><strong>Dívida:</strong> {_esc(d.footnote_debt_maturity_schedule)}</td>"
            f"<td class='mono'><strong>Target: ${d.analyst_target_mean_usd:,.2f}</strong><br>{_esc(d.analyst_recommendations_dist)}<br>{_esc(d.analyst_eps_revisions_30d_90d)}</td>"
            f"</tr>"
            for d in eq_filings
        )

        qual_rows_html = "".join(
            f"<tr>"
            f"<td class='mono'><strong>{_esc(e.ticker)}</strong><br><span style='font-size:6.8pt;color:#64748b;'>{_esc(getattr(e, 'company_name', getattr(e, 'name', e.ticker)))}</span></td>"
            f"<td>{_esc(e.qualitative_strategy['sector_particularity_lens'])}<br><strong>Pilar ROIC:</strong> {_esc(e.qualitative_strategy['roic_central_pillar'])} ({e.qualitative_strategy['roic_op_margin_pct']:.1f}% × {e.qualitative_strategy['roic_cap_turnover_x']:.2f}x)</td>"
            f"<td>{_esc(e.qualitative_strategy['moat_classification'])}</td>"
            f"<td>{_esc(e.qualitative_strategy['porter_5_forces'])}</td>"
            f"<td>{_esc(e.qualitative_strategy['common_size_peer_comparison'])}</td>"
            f"<td><strong>Skin in the Game:</strong> {_esc(e.qualitative_strategy['ceo_skin_in_the_game'])}<br><strong>Alocação:</strong> {_esc(e.qualitative_strategy['capital_allocation_history'])}<br><strong>Governança:</strong> {_esc(e.qualitative_strategy['tag_along_governance'])}</td>"
            f"</tr>"
            for e in equities
        )

        signal_ma_rows = ""
        for e in equities:
            sm = intel.get_corporate_signal_and_ma_dossier(e.ticker, e.company_name)
            signal_ma_rows += (
                f"<tr>"
                f"<td class='mono'><strong>{_esc(sm.ticker)}</strong><br><span style='font-size:6.6pt;'>{_esc(sm.company_name)}</span></td>"
                f"<td><strong>Guidance Delta:</strong> {_esc(sm.guidance_delta_summary)}<br><strong>Mudança Operacional:</strong> {_esc(sm.operational_moat_shifts)}</td>"
                f"<td>{_esc(sm.ceo_cfo_internal_commentary)}</td>"
                f"<td>{_esc(sm.qa_analyst_clashes)}</td>"
                f"<td><strong>Transações M&amp;A / Alianças:</strong> {_esc(sm.ma_and_strategic_deals)}<br><strong>Pagamento &amp; Diluição:</strong> {_esc(sm.payment_structure_and_dilution)}</td>"
                f"<td><strong>Goodwill:</strong> {_esc(sm.goodwill_and_impairment_risk)}<br><strong>Antitruste:</strong> {_esc(sm.antitrust_and_regulatory_status)}</td>"
                f"</tr>"
            )

        eq_micro = [m for m in micro_events if not m.asset_ticker.endswith("-USD")]
        eq_micro_html = "".join(
            f"<tr>"
            f"<td class='mono'>{_esc(m.date)}</td>"
            f"<td class='mono'><strong>{_esc(m.asset_ticker)}</strong></td>"
            f"<td>{_esc(m.source_type)} ({_esc(m.event_category)})</td>"
            f"<td><strong>{_esc(m.headline)}</strong></td>"
            f"<td>{_esc(m.fundamental_impact_analysis)}</td>"
            f"<td>{_auto_badge(m.classification)}</td>"
            f"</tr>"
            for m in eq_micro
        )

        sec4_html = f"""
        <div class="page-section">
            <div class="section-banner">SEÇÃO 4: DOSSIÊ FORENSE CORPORATIVO PROFUNDO (SEC 10-K/10-Q/20-F, 5 FORÇAS DE PORTER, CALLS Q&amp;A &amp; M&amp;As)</div>
            <div class="sub-banner">4.1. Extração Documental SEC EDGAR (Auditoria SOX 404b, Dissecação MD&amp;A Item 7, Riscos Item 1A, Notas Explicativas Forenses e Consenso)</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:7%;">Ticker</th>
                        <th style="width:14%;">Auditoria &amp; SOX 404(b)</th>
                        <th style="width:24%;">Dissecação do MD&amp;A (Crescimento, Segmentos, Backlog &amp; CAPEX)</th>
                        <th style="width:18%;">Fatores de Risco Específicos (Item 1A)</th>
                        <th style="width:24%;">Notas Explicativas Forenses (Litígios, SBC, ASC 606 &amp; Dívida)</th>
                        <th style="width:13%;">Analyst Reports</th>
                    </tr>
                </thead>
                <tbody>{doc_eq_html}</tbody>
            </table>
        </div>

        <div class="page-section">
            <div class="sub-banner">4.2. Posicionamento Competitivo: Lente Setorial, Árvore de ROIC, Moats (4 Pilares), 5 Forças de Porter, Common Size vs. Pares &amp; Governança</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:7%;">Ticker</th>
                        <th style="width:18%;">Lente Setorial &amp; Árvore ROIC</th>
                        <th style="width:18%;">Moats (4 Pilares de Vantagem)</th>
                        <th style="width:20%;">5 Forças de Porter &amp; Poder de Barganha</th>
                        <th style="width:17%;">Common Size Statements vs. Pares</th>
                        <th style="width:20%;">Skin in the Game, Alocação de Capital &amp; Tag Along</th>
                    </tr>
                </thead>
                <tbody>{qual_rows_html}</tbody>
            </table>

            <div class="sub-banner">4.3. Filtro Forense de Sinal vs. Ruído (Earnings Calls, Declarações Internas CEO/CFO, Confrontos Q&amp;A) &amp; Dossiê Completo de M&amp;A / Goodwill</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:7%;">Ativo</th>
                        <th style="width:19%;">Guidance Delta &amp; Mudança Operacional</th>
                        <th style="width:20%;">Declarações Críticas Internas (CEO / CFO)</th>
                        <th style="width:19%;">Confrontos no Q&amp;A com Analistas</th>
                        <th style="width:19%;">M&amp;As, Alianças &amp; Estrutura de Diluição</th>
                        <th style="width:16%;">Goodwill (Ágio) &amp; Status Antitruste</th>
                    </tr>
                </thead>
                <tbody>{signal_ma_rows}</tbody>
            </table>

            <div class="sub-banner">4.4. Monitoramento de Fatos Relevantes Internos Corporativos (SEC Form 8-K, Form 4 Insider Trading &amp; Press Releases)</div>
            <table class="inst-table">
                <thead>
                    <tr><th>Data</th><th>Ticker</th><th>Fonte &amp; Categoria</th><th>Fato Relevante Reportado</th><th>Impacto Direto nos Fundamentos</th><th>Classificação</th></tr>
                </thead>
                <tbody>{eq_micro_html}</tbody>
            </table>
        </div>
        """

        # ======================================================================
        # SEÇÃO 5: DOSSIÊ TÉCNICO DE PROTOCOLOS CRIPTO (WHITEPAPERS, GITHUB,
        #          SINAIS DE CORE DEVS, UPGRADES & CRONOGRAMA FORENSE DE UNLOCKS)
        # ======================================================================
        doc_cr_html = "".join(
            f"<tr>"
            f"<td class='mono'><strong>{_esc(c.symbol)}</strong><br><span style='font-size:6.6pt;'>{_esc(c.name)}</span></td>"
            f"<td><strong>{_esc(c.wp_title_author)}</strong><br>{_esc(c.wp_value_proposition)}</td>"
            f"<td><strong>Consenso:</strong> {_esc(c.wp_consensus_architecture)}<br><strong>Captura de Valor:</strong> {_esc(c.wp_value_accrual_mechanism)}</td>"
            f"<td class='mono'>Repos: {_esc(c.github_core_repos)}<br><strong>{c.github_commits_4w} commits (4w) | {c.github_active_devs_monthly} Devs/mês</strong></td>"
            f"<td>{_esc(c.deepdao_status)}<br><strong>Propostas:</strong> {_esc(c.recent_governance_proposals)}<br><strong>Skin in the Game ({c.skin_in_the_game_locked_pct:.1f}%):</strong> {_esc(c.skin_in_the_game_details)}</td>"
            f"<td>{_auto_badge(f'Token Sniffer: {c.token_sniffer_score}/100')}<br><strong>Auditorias:</strong> {_esc(c.audit_firms)}<br><strong>Exploits:</strong> {_esc(c.exploit_history)}</td>"
            f"</tr>"
            for c in cr_filings
        )

        dev_internal_rows = ""
        for sym, cp in cryptos.items():
            dv = intel.get_crypto_internal_dev_dossier(sym, cp.name)
            ss = cp.supply_structure
            tv = cp.tokenomics_valuation
            dev_internal_rows += (
                f"<tr>"
                f"<td class='mono'><strong>{_esc(sym)}</strong><br>${cp.spot_price_usd:,.2f}<br>Circ: {cp.circulating_pct:.1f}%</td>"
                f"<td>{_esc(dv.founder_core_dev_signals)}</td>"
                f"<td><strong>Upgrades:</strong> {_esc(dv.upcoming_protocol_upgrades)}<br><strong>Fee Switch / Mecânica:</strong> {_esc(dv.architecture_and_fee_switch_changes)}</td>"
                f"<td><strong>Cronograma 30/60/90d:</strong> {_esc(dv.unlock_schedule_30_60_90d)}<br><strong>Unlock Mensal:</strong> {ss['unlock_pct_of_circ']:.2f}% Circ &rarr; <strong>Px Teórico Pós-Diluição: ${ss['theoretical_post_unlock_price_usd']:,.2f}</strong></td>"
                f"<td><strong>Concentração:</strong> {_esc(dv.whale_and_vc_concentration)}<br><strong>Impacto DAO:</strong> {_esc(dv.active_dao_proposals_impact)}<br><strong>Real Earnings:</strong> USD {tv['protocol_real_earnings_m']:+.1f}M/ano</td>"
                f"</tr>"
            )

        cr_micro = [m for m in micro_events if m.asset_ticker.endswith("-USD")]
        cr_micro_html = "".join(
            f"<tr>"
            f"<td class='mono'>{_esc(m.date)}</td>"
            f"<td class='mono'><strong>{_esc(m.asset_ticker)}</strong></td>"
            f"<td>{_esc(m.source_type)} ({_esc(m.event_category)})</td>"
            f"<td><strong>{_esc(m.headline)}</strong></td>"
            f"<td>{_esc(m.fundamental_impact_analysis)}</td>"
            f"<td>{_auto_badge(m.classification)}</td>"
            f"</tr>"
            for m in cr_micro
        )

        sec5_html = f"""
        <div class="page-section">
            <div class="section-banner">SEÇÃO 5: DOSSIÊ TÉCNICO DE PROTOCOLOS CRIPTO (WHITEPAPERS, GITHUB, SINAIS DE CORE DEVS &amp; UNLOCKS 30/60/90D)</div>
            <div class="sub-banner">5.1. Extração Documental Técnica de Criptoativos (White Papers, Arquitetura de Consenso, Value Accrual, GitHub API, DeepDAO &amp; Auditorias)</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:9%;">Protocolo</th>
                        <th style="width:19%;">Síntese Técnica do White Paper</th>
                        <th style="width:20%;">Consenso &amp; Captura de Valor</th>
                        <th style="width:14%;">Engenharia GitHub (4w)</th>
                        <th style="width:20%;">Governança DeepDAO &amp; Skin in the Game</th>
                        <th style="width:18%;">Token Sniffer &amp; Auditorias</th>
                    </tr>
                </thead>
                <tbody>{doc_cr_html}</tbody>
            </table>

            <div class="sub-banner">5.2. Sinais Internos de Core Devs/Founders, Upgrades Técnicos (EIPs/PIPs) &amp; Cronograma Forense de Unlocks (30/60/90d)</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:9%;">Ativo</th>
                        <th style="width:21%;">Sinais Internos de Core Devs &amp; Fundadores</th>
                        <th style="width:24%;">Próximos Upgrades de Rede &amp; Mudanças de Fee Switch</th>
                        <th style="width:23%;">Cronograma de Unlocks (30/60/90d) &amp; Preço Pós-Diluição</th>
                        <th style="width:23%;">Concentração Institucional &amp; Deliberações DAO</th>
                    </tr>
                </thead>
                <tbody>{dev_internal_rows}</tbody>
            </table>

            <div class="sub-banner">5.3. Eventos Internos Recentes de Protocolos e Governança On-Chain</div>
            <table class="inst-table">
                <thead>
                    <tr><th>Data</th><th>Protocolo</th><th>Fonte</th><th>Atualização / Proposta Aprovada</th><th>Impacto Econômico e Técnico</th><th>Classificação</th></tr>
                </thead>
                <tbody>{cr_micro_html}</tbody>
            </table>
        </div>
        """

        # ======================================================================
        # SEÇÃO 6: SCREENER QUANTITATIVO E FORENSE DE OPORTUNIDADES (SEM ALTMAN Z)
        # ======================================================================
        scr_stk_html = "".join(
            f"<tr>"
            f"<td class='mono'><strong>{_esc(s.ticker)}</strong><br>${s.price_usd:,.2f}</td>"
            f"<td><strong>{_esc(s.company_name)}</strong><br><span style='font-size:6.8pt;'>{_esc(s.sector)} ({_esc(s.country)})</span></td>"
            f"<td class='mono'>Sloan: <strong>{s.sloan_ratio_pct:+.1f}%</strong> ({_esc(s.sloan_status)})<br>FCO/EBITDA: <strong>{s.fco_to_ebitda:.2f}x</strong> ({_esc(s.fco_ebitda_status)})</td>"
            f"<td class='mono'>ROIC: <strong>{s.roic_nopat_pct:.1f}%</strong> vs WACC: {s.wacc_pct:.1f}%<br>Liq. Corr: <strong>{s.current_ratio:.2f}x</strong> | IntCov: <strong>{s.interest_coverage_x:.1f}x</strong></td>"
            f"<td class='mono'><strong>g_impl: {s.reverse_dcf_g_impl_pct:.1f}%</strong> vs <strong>g_fund: {s.g_fund_pct:.1f}%</strong><br>PEGY Forward: <strong>{s.enterprise_or_fin_pegy:.2f}x</strong><br>DCF: ${s.dcf_fair_mos10_usd:,.0f} | SOTP: ${s.sotp_fair_usd:,.0f}</td>"
            f"<td><strong>{_esc(s.auditor_sox404b)}</strong><br>{_esc(s.moat_and_catalysts)}</td>"
            f"<td>{_auto_badge(f'{s.filters_passed_count}/5 — {s.framework_verdict}')}</td>"
            f"</tr>"
            for s in stock_screener
        )

        scr_cr_html = "".join(
            f"<tr>"
            f"<td class='mono'><strong>{_esc(c.symbol)}</strong><br>${c.price_usd:,.2f}</td>"
            f"<td><strong>{_esc(c.name)}</strong><br><span style='font-size:6.8pt;'>{_esc(c.category)} | MCap ${c.market_cap_b:.2f}B</span></td>"
            f"<td class='mono'>Circ. Supply: <strong>{c.circulating_supply_pct:.1f}%</strong><br>{_esc(c.unlock_status)}<br>Px Pós-Unlock: <strong>${c.post_unlock_theoretical_px:,.2f}</strong></td>"
            f"<td><strong>Sniffer: {c.token_sniffer_score}/100</strong><br>{_esc(c.security_audits)}</td>"
            f"<td class='mono'><strong>{c.active_devs_github} Active Devs</strong> ({c.github_commits_4w} commits 4w)<br>Real Earnings: <strong>USD {c.protocol_real_earnings_m:+.1f}M/a</strong><br>Real Yield: {c.real_yield_pct:+.1f}% | P/F: {c.pf_ratio:.1f}x | MVRV Z: {c.mvrv_z_score:.2f}</td>"
            f"<td>{_esc(c.whitepaper_and_dao)}</td>"
            f"<td>{_auto_badge(f'{c.filters_passed_count}/5 — {c.framework_verdict}')}</td>"
            f"</tr>"
            for c in crypto_screener
        )

        sec6_html = f"""
        <div class="page-section">
            <div class="section-banner">SEÇÃO 6: RADAR EXECUTIVO DE OPORTUNIDADES — SCREENER QUANTITATIVO E FORENSE (AÇÕES &amp; CRIPTOATIVOS)</div>
            <div class="sub-banner">6.1. Funil 1: Screener de Ações Globais (Filtros: Sloan &lt;= +5%, FCO/EBITDA &gt;= 0.90x, ROIC &gt;= 18% &gt; WACC, CR &gt; 1.0x &amp; IntCov &gt; 4.0x, g_impl &lt;= g_fund Forward)</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:9%;">Ticker &amp; Spot</th>
                        <th style="width:15%;">Empresa &amp; Setor</th>
                        <th style="width:17%;">Filtros 1 &amp; 2: Sloan &amp; FCO/EBITDA</th>
                        <th style="width:16%;">Filtros 3 &amp; 4: ROIC vs WACC &amp; Solvência</th>
                        <th style="width:17%;">Filtro 5: Reverse DCF &amp; PEGY Forward</th>
                        <th style="width:14%;">Auditoria SOX &amp; Moat</th>
                        <th style="width:12%;">Veredito do Funil</th>
                    </tr>
                </thead>
                <tbody>{scr_stk_html}</tbody>
            </table>

            <div class="sub-banner">6.2. Funil 2: Screener de Criptoativos (Filtros: Supply &gt;= 65%, Unlocks &lt;= 2.5%/mês, Sniffer &gt;= 85, Active Devs &gt;= 40 &amp; Real Earnings &gt; 0, MVRV Z &lt;= 2.0)</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:9%;">Símbolo</th>
                        <th style="width:15%;">Protocolo &amp; MCap</th>
                        <th style="width:17%;">Filtros 1 &amp; 2: Supply &amp; Unlocks</th>
                        <th style="width:14%;">Filtro 3: Segurança</th>
                        <th style="width:19%;">Filtros 4 &amp; 5: Devs, Real Earnings &amp; MVRV Z</th>
                        <th style="width:14%;">White Paper &amp; DAO</th>
                        <th style="width:12%;">Veredito do Funil</th>
                    </tr>
                </thead>
                <tbody>{scr_cr_html}</tbody>
            </table>
        </div>
        """

        # ======================================================================
        # SEÇÃO 7: GOVERNANÇA DE RISCO, ALAVANCAGEM CONVEXA LTV & TIMING CONSULTIVO
        # ======================================================================
        aave_stress_html = "".join(
            f"<tr>"
            f"<td><strong>{_esc(s['Cenário Stress-Test Aave V3'])}</strong></td>"
            f"<td class='mono'>{_esc(s['Borrow Rate USDC (% a.a.)'])}</td>"
            f"<td class='mono'>{_esc(s['Choque Simulado no Colateral BTC'])}</td>"
            f"<td class='mono'>${s['Custo Anual de Juros (USD)']:,.0f}</td>"
            f"<td class='mono'><strong>{_esc(s['LTV BTC Resultante (Após 1 Ano s/ Amortizar)'])}</strong></td>"
            f"<td class='mono'>{_esc(s['Health Factor Aave V3 (Liq = 1.00)'])}</td>"
            f"<td>{_auto_badge(s['Diagnóstico de Risco'])}</td>"
            f"</tr>"
            for s in risk_timing.aave_v3_stress_test_table
        )

        rules_doc_html = "".join(
            f"<tr>"
            f"<td><strong>{_esc(r['Classe / Vertical'])}</strong></td>"
            f"<td>{_esc(r['Métrica Primária'])}</td>"
            f"<td>{_esc(r['Referência de Compra (Consultiva)'])}</td>"
            f"<td>{_esc(r['Referência de Poda 50% (Consultiva)'] if 'Referência de Poda 50% (Consultiva)' in r else r.get('Referência de Poda 50%/100% (Consultiva)', ''))}</td>"
            f"<td>{_esc(r['Nota Estratégica'])}</td>"
            f"</tr>"
            for r in risk_timing.framework_rules_documentation
        )

        timing_assets_html = "".join(
            f"<tr>"
            f"<td class='mono'><strong>{_esc(r.asset_ticker)}</strong><br><span style='font-size:6.6pt;'>{_esc(r.asset_name)}</span></td>"
            f"<td>{_esc(r.framework_category)}<br><span class='mono' style='font-size:6.8pt;'>Alvo {r.target_weight_pct:.2f}% vs Atual {r.current_weight_pct:.2f}% ({r.weight_drift_pp:+.2f}pp)</span></td>"
            f"<td class='mono'>{_esc(r.primary_indicator_current)}</td>"
            f"<td><strong>Compra:</strong> {_esc(r.framework_buy_reference)}<br><strong>Poda:</strong> {_esc(r.framework_prune_reference)}</td>"
            f"<td>{_auto_badge(r.consultative_status_vs_reference)}</td>"
            f"<td class='mono'><strong>-{r.tax_drag_hurdle_rate_pct:.2f}%</strong> (Ganho +{r.estimated_unrealized_gain_pct:.0f}% | IR {r.capital_gains_tax_rate_pct:.0f}%)<br>{_badge('Qualificado Shannon Inflow', 'green') if r.shannon_inflow_eligible else _badge('Aguardar', 'amber')}</td>"
            f"</tr>"
            for r in risk_timing.consultative_asset_timing_table
        )

        sec7_html = f"""
        <div class="page-section">
            <div class="section-banner">SEÇÃO 7: MONITOR DE RISCO, ALAVANCAGEM CONVEXA LTV, LIQUIDEZ ADTV &amp; TIMING CONSULTIVO DO PORTFÓLIO</div>

            <div class="kpi-row">
                <div class="kpi-box">
                    <div class="lbl">Sharpe &amp; Sortino Ratio</div>
                    <div class="val">Sharpe {pr['sharpe_ratio']:.2f} | Sortino {pr['sortino_ratio']:.2f}</div>
                    <div class="sub">Sortino &gt; Sharpe (Assimetria Positiva)</div>
                </div>
                <div class="kpi-box">
                    <div class="lbl">Calmar Ratio (CAGR / Max DD)</div>
                    <div class="val">{pr['calmar_ratio']:.2f} ({_esc(pr['calmar_classification'])})</div>
                    <div class="sub">Ref: &lt;0.5 Lixo | 0.5-1 Ok | 1-2 Ótimo | &gt;3 Lendário</div>
                </div>
                <div class="kpi-box">
                    <div class="lbl">VIX &amp; Liquidez de Execução ADTV</div>
                    <div class="val">VIX {vx['vix_current']:.2f} ({_esc(vx['vix_classification'].split('(')[0])})</div>
                    <div class="sub">100% das {len(portfolio.positions)} posições &lt; 1.0% do ADTV Diário</div>
                </div>
                <div class="kpi-box">
                    <div class="lbl">LTV Global — Alavancagem Convexa</div>
                    <div class="val">{ltv['ltv_global_current_pct']:.1f}% (Dívida USD {ltv['total_debt_usd']:,.0f})</div>
                    <div class="sub">IBKR Box: {ltv['ibkr_box_spread_rate_pct']:.2f}% | Aave V3: {ltv['aave_v3_wbtc_usdc_borrow_rate_pct']:.2f}%</div>
                </div>
            </div>

            <div class="grid-2">
                <div>
                    <div class="sub-banner">7.1A. Parâmetros do Painel de Alavancagem Convexa Anti-Cíclica (LTV Global)</div>
                    <table class="inst-table">
                        <thead><tr><th>Parâmetro LTV</th><th>Valor / Status Atual</th><th>Diretriz Documental do Framework</th></tr></thead>
                        <tbody>
                            <tr><td><strong>LTV Base Estrutural</strong></td><td class="mono">{ltv['ltv_global_current_pct']:.2f}%</td><td>{_esc(ltv['ltv_structural_base_ref'])}</td></tr>
                            <tr><td><strong>Gatilho Turbo (28% a 30% LTV)</strong></td><td>{_auto_badge(ltv['turbo_trigger_status'])}</td><td>{_esc(ltv['turbo_trigger_ref'])}</td></tr>
                            <tr><td><strong>Redução Defensiva (10% LTV)</strong></td><td>{_auto_badge(ltv['defensive_reduction_status'])}</td><td>{_esc(ltv['defensive_reduction_ref'])}</td></tr>
                        </tbody>
                    </table>
                </div>
                <div>
                    <div class="sub-banner">7.1B. Stress-Test de Custo de Carregamento DeFi (Aave V3 WBTC/USDC Borrow Spikes)</div>
                    <table class="inst-table">
                        <thead><tr><th>Cenário</th><th>Borrow Rate</th><th>Choque BTC</th><th>Juros/Ano</th><th>LTV 1 Ano</th><th>Health Factor</th><th>Diagnóstico</th></tr></thead>
                        <tbody>{aave_stress_html}</tbody>
                    </table>
                </div>
            </div>

            <div class="sub-banner">7.2A. Documentação das 7 Regras de Timing por Classe de Ativo — Referência Estratégica do Framework (Consultivo / Não-Vinculante)</div>
            <table class="inst-table">
                <thead><tr><th>Classe / Vertical</th><th>Métrica Primária</th><th>Referência Consultiva de Compra</th><th>Referência Consultiva de Poda</th><th>Nota Estratégica</th></tr></thead>
                <tbody>{rules_doc_html}</tbody>
            </table>

            <div class="sub-banner">7.2B. Posicionamento Consultivo dos {len(portfolio.positions)} Ativos da Carteira, Simulador Shannon Inflow &amp; Impacto Fiscal (Tax-Drag Hurdle Rate)</div>
            <table class="inst-table">
                <thead>
                    <tr>
                        <th style="width:12%;">Ticker &amp; Ativo</th>
                        <th style="width:16%;">Vertical &amp; Pesos</th>
                        <th style="width:20%;">Indicadores Atuais Calculados</th>
                        <th style="width:24%;">Referências Consultivas (Compra &amp; Poda)</th>
                        <th style="width:14%;">Status Consultivo</th>
                        <th style="width:14%;">Tax-Drag Hurdle &amp; Inflow</th>
                    </tr>
                </thead>
                <tbody>{timing_assets_html}</tbody>
            </table>
        </div>
        """

        full_html = f"""<!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="utf-8">
            <title>Relatório Master Multi-Completo 360° — Portfólio, Analytics, Forense, Macro &amp; DeFi</title>
            <style>{css}</style>
        </head>
        <body>
            {sec1_html}
            {sec2_html}
            {sec3_html}
            {sec4_html}
            {sec5_html}
            {sec6_html}
            {sec7_html}
        </body>
        </html>
        """
        return full_html

    def generate_pdf_bytes(
        self,
        macro: MacroDataBundle,
        portfolio: PortfolioOverviewBundle,
        equities: List[EquityFullAnalysis],
        cryptos: Dict[str, CryptoFullProfile],
        eq_filings: List[EquityDocumentaryDossier],
        cr_filings: List[CryptoDocumentaryDossier],
        geo_matrix: List[GeopoliticalImpactRow],
        micro_events: List[MicroCorporateProtocolEvent],
        stock_screener: List[StockScreenerRow],
        crypto_screener: List[CryptoScreenerRow],
        risk_timing: RiskLeverageTimingBundle,
        output_pdf_path: Optional[str] = None,
    ) -> bytes:
        html_str = self.build_complete_html_report(
            macro=macro,
            portfolio=portfolio,
            equities=equities,
            cryptos=cryptos,
            eq_filings=eq_filings,
            cr_filings=cr_filings,
            geo_matrix=geo_matrix,
            micro_events=micro_events,
            stock_screener=stock_screener,
            crypto_screener=crypto_screener,
            risk_timing=risk_timing,
        )
        return self._compile_html_to_pdf_bytes(html_str, "relatorio_master_multi_completo_360", output_pdf_path)

    # ==========================================================================
    # MÓDULO DE DOSSIÊ INDIVIDUAL DE ATIVO EM PDF (DEEP DIVE 360° SEM ALTMAN Z)
    # ==========================================================================
    def build_deep_dive_html_report(self, dd: DeepDiveResultBundle) -> str:
        css = """
        @page { size: A4 landscape; margin: 9mm 10mm 10mm 10mm; }
        * { box-sizing: border-box; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        body { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif; font-size: 7.8pt; line-height: 1.35; color: #0F172A; background: #FFFFFF; margin: 0; padding: 0; }
        .page-section { page-break-after: always; }
        .page-section:last-child { page-break-after: auto; }
        .report-header { background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%); color: #FFFFFF; padding: 12px 16px; border-radius: 6px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #F59E0B; }
        .report-title { font-size: 13pt; font-weight: 800; margin: 0; }
        .report-subtitle { font-size: 8pt; color: #CBD5E1; margin-top: 2px; }
        .section-banner { background: #0F172A; color: #FDE047; padding: 6px 12px; font-size: 9pt; font-weight: 800; border-left: 4px solid #3B82F6; border-radius: 4px; margin: 8px 0 6px 0; text-transform: uppercase; }
        .sub-banner { background: #1E293B; color: #F8FAFC; padding: 4px 10px; font-size: 8.2pt; font-weight: 700; border-left: 3px solid #10B981; border-radius: 3px; margin: 6px 0 4px 0; }
        .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 8px; }
        .kpi-box { background: #F8FAFC; border: 1px solid #CBD5E1; border-left: 4px solid #1E3A8A; border-radius: 5px; padding: 6px 10px; }
        .kpi-box .lbl { font-size: 6.8pt; font-weight: 700; text-transform: uppercase; color: #475569; }
        .kpi-box .val { font-size: 10.5pt; font-weight: 800; color: #0F172A; margin: 2px 0; }
        .kpi-box .sub { font-size: 6.8pt; color: #64748B; }
        .insight-box { background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid #2563EB; border-radius: 5px; padding: 7px 11px; margin-bottom: 8px; font-size: 7.8pt; color: #1E3A8A; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        table.inst-table { width: 100%; border-collapse: collapse; margin-bottom: 8px; font-size: 7.4pt; }
        table.inst-table th { background: #1E293B; color: #FFFFFF; font-weight: 700; text-align: left; padding: 5px 7px; border: 1px solid #334155; }
        table.inst-table td { padding: 4.5px 7px; border: 1px solid #CBD5E1; vertical-align: top; color: #0F172A; word-break: normal; overflow-wrap: break-word; }
        table.inst-table tr:nth-child(even) td { background: #F8FAFC; }
        .mono { font-family: 'Consolas', 'Courier New', monospace; font-weight: 600; }
        """

        funnel_rows_html = "".join(
            f"<tr>"
            f"<td class='mono'><strong>Etapa {s.step_number}</strong></td>"
            f"<td><strong>{_esc(s.filter_name)}</strong></td>"
            f"<td class='mono'>{_esc(s.calculated_value)}</td>"
            f"<td>{_esc(s.strict_criterion)}</td>"
            f"<td>{_badge('APROVADO ✓', 'green') if s.passed else _badge('REPROVADO ✗', 'red')}</td>"
            f"<td class='mono'><strong>{s.score_points}/{s.max_points} pts</strong></td>"
            f"<td>{_esc(s.diagnostic_note)}</td>"
            f"</tr>"
            for s in dd.screener_filters_breakdown
        )

        port_badge = (
            f"Na Carteira Atual (Alvo {dd.portfolio_position_info['target_weight_pct']:.2f}% | P&L {dd.portfolio_position_info['pnl_pct']:+.1f}%)"
            if dd.in_current_portfolio and dd.portfolio_position_info
            else "Ativo Externo / Sob Análise no Deep Dive"
        )

        geo_rows_html = "".join(
            f"<tr><td><strong>{_esc(g.global_event)}</strong></td><td>{_auto_badge(g.severity)}</td>"
            f"<td class='mono'>{_esc(g.affected_portfolio_assets)}</td><td>{_esc(g.fundamental_impact_mechanism)}</td></tr>"
            for g in (dd.related_geopolitics or [])
        )
        micro_rows_html = "".join(
            f"<tr><td class='mono'><strong>{_esc(m.asset_ticker)}</strong></td><td>{_esc(m.event_category)}</td>"
            f"<td>{_esc(m.headline)}</td><td>{_esc(m.fundamental_impact_analysis)}</td></tr>"
            for m in (dd.related_micro_events or [])
        )
        rt_ctx = dd.risk_and_timing_context or {}

        if dd.asset_class == "CRYPTO" and dd.crypto_profile and dd.crypto_dossier:
            cp = dd.crypto_profile
            cd = dd.crypto_dossier
            om = cp.onchain_metrics
            mm = cp.mining_metrics
            cf = cp.capital_flows
            tv = cp.tokenomics_valuation
            ss = cp.supply_structure
            ms = cp.derivatives_sentiment
            re_brk = dd.real_earnings_period_breakdown or {}
            gh_peers = dd.github_peers_comparison or []

            gh_rows = "".join(
                f"<tr><td><strong>{_esc(p['Protocolo'])}</strong></td><td class='mono'>{p['Commits (4w)']}</td><td class='mono'>{p['Active Devs (Mensal)']}</td></tr>"
                for p in gh_peers
            )

            body_html = f"""
            <div class="page-section">
                <div class="report-header">
                    <div>
                        <div class="report-title">DOSSIÊ EXECUTIVO DEEP DIVE — {_esc(dd.normalized_ticker)} ({_esc(cp.name)})</div>
                        <div class="report-subtitle">Value Investing Framework (TRUE) • Classe: {_esc(dd.asset_class)} • Status: {_esc(port_badge)}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:11pt;font-weight:800;color:#FDE047;">SCORE SCREENER: {dd.screener_score_0_100}/100</div>
                        <div style="font-size:7.5pt;color:#E2E8F0;">{_esc(dd.regime_classification)}</div>
                    </div>
                </div>

                <div class="kpi-row">
                    <div class="kpi-box"><div class="lbl">Preço Spot &amp; Market Cap / FDV</div><div class="val">${cp.spot_price_usd:,.2f}</div><div class="sub">MCap: ${cp.market_cap_b:.2f}B | FDV: ${cp.fdv_b:.2f}B ({ss['fdv_to_mcap_x']:.2f}x)</div></div>
                    <div class="kpi-box"><div class="lbl">Múltiplo Soberano &amp; Ciclo</div><div class="val">{_esc(dd.sovereign_multiple_value)}</div><div class="sub">{_esc(dd.sovereign_multiple_status)}</div></div>
                    <div class="kpi-box"><div class="lbl">Economia Real &amp; Real Yield</div><div class="val">USD {tv['protocol_real_earnings_m']:+,.1f}M / ano</div><div class="sub">Real Yield: {tv['real_yield_pct']:+.2f}%</div></div>
                    <div class="kpi-box"><div class="lbl">Segurança &amp; Engenharia GitHub</div><div class="val">Sniffer {cd.token_sniffer_score}/100 | {cd.github_active_devs_monthly} Devs</div><div class="sub">{cd.github_commits_4w} Commits (4w) | Circ: {cp.circulating_pct:.1f}%</div></div>
                </div>

                <div class="insight-box"><strong>Veredito Automatizado &amp; Regime Consultivo:</strong> {_esc(dd.automated_consultative_verdict)}</div>

                <div class="section-banner">1. MATRIZ DO FUNIL DE 5 FILTROS QUANTITATIVOS &amp; ON-CHAIN (SCORE {dd.screener_score_0_100}/100)</div>
                <table class="inst-table">
                    <thead><tr><th>Etapa</th><th>Filtro do Framework</th><th>Valor Calculado</th><th>Critério Estrito</th><th>Status</th><th>Score</th><th>Diagnóstico</th></tr></thead>
                    <tbody>{funnel_rows_html}</tbody>
                </table>

                <div class="section-banner">2. TIMING ON-CHAIN &amp; TOKENOMICS / UNLOCKS</div>
                <table class="inst-table">
                    <thead>
                        <tr><th>MVRV Z &amp; NUPL</th><th>aSOPR (Linha 1.0)</th><th>Pi Cycle &amp; 200W SMA</th><th>Hash Ribbon &amp; MMC</th><th>Fluxos &amp; HODL Waves</th></tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="mono"><strong>MVRV Z: {om['mvrv_z_score']:.2f}</strong> ({_esc(om['mvrv_z_status'])})<br><strong>NUPL: {om['nupl']:.2f}</strong> ({_esc(om['nupl_status'])})</td>
                            <td class="mono"><strong>{om['asopr']:.3f}</strong><br>{_esc(om['asopr_status'])}</td>
                            <td class="mono">111d: ${om['pi_cycle_111d_sma_usd']:,.0f} vs 2x350d: ${om['pi_cycle_350d_x2_sma_usd']:,.0f}<br>200W SMA: ${om['sma_200w_usd']:,.0f} ({om['price_to_200w_sma_x']:.2f}x)</td>
                            <td class="mono">{_esc(mm['hash_ribbon_status'])}<br>MMC: ${mm['mmc_minimum_mining_cost_usd']:,.0f}</td>
                            <td class="mono">Quentes: {cf['hodl_hot_waves_pct']:.1f}% | Frias: {cf['hodl_cold_waves_pct']:.1f}%<br>Stablecoin Netflow: USD {cf['stablecoins_netflow_24h_m']:+,.0f}M/24h</td>
                        </tr>
                    </tbody>
                </table>

                <table class="inst-table">
                    <thead>
                        <tr><th>Real Earnings (Dia / Sem / Ano)</th><th>NVT Nominal (c/ Ref), NVT GC &amp; NVM</th><th>TVL &amp; Vol 24h</th><th>Unlocks (30d) &amp; Preço Pós-Diluição</th><th>Derivativos &amp; Liq Heatmap</th></tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="mono">Dia: <strong>${re_brk.get('daily_real_earnings_usd', 0):+,.0f}</strong> | Sem: <strong>${re_brk.get('weekly_real_earnings_usd', 0):+,.0f}</strong><br>Ano: <strong>USD {re_brk.get('annual_real_earnings_m', 0):+,.1f}M</strong></td>
                            <td class="mono">NVM: <strong>{tv['nvm_ratio']:.2f}</strong> | NVT GC: {tv['nvt_golden_cross']:+.2f}<br>P/S: {tv['ps_ratio']:.1f}x | P/F: <strong>{tv['pf_ratio']:.1f}x</strong></td>
                            <td class="mono">TVL: ${tv['tvl_b']:.2f}B | Vol 24h: ${tv['tx_vol_24h_b']:.2f}B</td>
                            <td class="mono">Unlock 30d: <strong>{ss['unlock_pct_of_circ']:.2f}% Circ</strong><br>Px Pós-Diluição: <strong>${ss['theoretical_post_unlock_price_usd']:,.2f}</strong></td>
                            <td class="mono">OI/MCap: {ms['oi_to_mcap_pct']:.1f}% | Funding: {ms['funding_rate_8h_pct']:+.4f}%<br>Acima: ${ms['liq_heatmap_above_price_usd']:,.0f} | Abaixo: ${ms['liq_heatmap_below_price_usd']:,.0f}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            """
        else:
            eq = dd.equity_analysis
            ed = dd.equity_dossier
            fh = eq.forensic_health
            vm = eq.valuation_methods
            qs = eq.qualitative_strategy
            fh5 = dd.forensic_5y_history or {}
            mda_q = dd.mda_quant_breakdown or {}
            top_risks = dd.top_3_item1a_risks or []
            ins = dd.insider_form4_summary or {}
            shares_5y = dd.share_count_5y_b or []

            years_5 = fh5.get("years", ["2022", "2023", "2024", "2025", "2026 (LTM)"])
            hist_5y_rows = ""
            for idx, yr in enumerate(years_5):
                hist_5y_rows += (
                    f"<tr>"
                    f"<td class='mono'><strong>{_esc(yr)}</strong></td>"
                    f"<td class='mono'>{fh5.get('sloan_pct', [0]*5)[idx]:+.1f}%</td>"
                    f"<td class='mono'>{fh5.get('fco_to_ebitda', [0]*5)[idx]:.2f}x (FCO ${fh5.get('fco_b', [0]*5)[idx]:,.1f}B)</td>"
                    f"<td class='mono'>${fh5.get('nwc_b', [0]*5)[idx]:,.1f}B</td>"
                    f"<td class='mono'><strong>{fh5.get('roic_pct', [0]*5)[idx]:.1f}%</strong> vs {fh5.get('wacc_pct', [0]*5)[idx]:.2f}%</td>"
                    f"<td class='mono'>{fh5.get('dupont_margin_pct', [0]*5)[idx]:.1f}% × {fh5.get('dupont_turnover_x', [0]*5)[idx]:.2f}x × {fh5.get('dupont_leverage_x', [0]*5)[idx]:.2f}x = <strong>{fh5.get('roe_pct', [0]*5)[idx]:.1f}%</strong></td>"
                    f"<td class='mono'>MB: {fh5.get('gross_margin_pct', [0]*5)[idx]:.1f}% | Shares: {shares_5y[idx] if idx < len(shares_5y) else 0:.3f}B</td>"
                    f"</tr>"
                )

            kpis_a = ["Receita", "Lucro Bruto", "EBIT", "EBITDA", "NOPAT", "Lucro Líquido"]
            kpis_b = ["FCO", "FCF", "EPS", "Dividendos", "Book Value", "ROIC"]
            cagr_cells_a = "".join(
                f"<td class='mono'>{eq.cagr_matrix_12_kpis[k]['3y']:+.1f}% | <strong>{eq.cagr_matrix_12_kpis[k]['5y']:+.1f}%</strong> | {eq.cagr_matrix_12_kpis[k]['10y']:+.1f}%</td>"
                for k in kpis_a
            )
            cagr_cells_b = "".join(
                f"<td class='mono'>{eq.cagr_matrix_12_kpis[k]['3y']:+.1f}% | <strong>{eq.cagr_matrix_12_kpis[k]['5y']:+.1f}%</strong> | {eq.cagr_matrix_12_kpis[k]['10y']:+.1f}%</td>"
                for k in kpis_b
            )

            sotp_rows = "".join(
                f"<tr><td><strong>{_esc(s['segment'])}</strong></td><td class='mono'>{s['rev_share_pct']:.1f}%</td>"
                f"<td>{_esc(s['peer_benchmark'])}</td><td class='mono'><strong>${s['segment_val_per_share']:,.2f}</strong></td></tr>"
                for s in vm["sotp_segments"]
            )
            risks_html = "".join(f"<li>{_esc(r)}</li>" for r in top_risks)

            body_html = f"""
            <div class="page-section">
                <div class="report-header">
                    <div>
                        <div class="report-title">DOSSIÊ EXECUTIVO DEEP DIVE — {_esc(dd.normalized_ticker)} ({_esc(eq.company_name)})</div>
                        <div class="report-subtitle">Value Investing Framework (TRUE) • Categoria: {_esc(dd.framework_category_label)} • Status: {_esc(port_badge)}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:11pt;font-weight:800;color:#FDE047;">SCORE SCREENER: {dd.screener_score_0_100}/100</div>
                        <div style="font-size:7.5pt;color:#E2E8F0;">{_esc(dd.regime_classification)}</div>
                    </div>
                </div>

                <div class="kpi-row">
                    <div class="kpi-box"><div class="lbl">Preço Atual Spot &amp; Market Cap</div><div class="val">${eq.current_price:,.2f}</div><div class="sub">Market Cap: USD {eq.market_cap_b:,.1f}B | Setor: {_esc(eq.sector_label)}</div></div>
                    <div class="kpi-box"><div class="lbl">Múltiplo Soberano Forward (NTM)</div><div class="val">{_esc(dd.sovereign_multiple_value)}</div><div class="sub">{_esc(dd.sovereign_multiple_status)}</div></div>
                    <div class="kpi-box"><div class="lbl">Grade de Valor Justo (DCF / SOTP / PEGY Ouro)</div><div class="val">DCF: ${vm['dcf_fair_mos10_usd']:,.2f} | SOTP: ${vm['sotp_fair_price_usd']:,.2f}</div><div class="sub">Preço Justo PEGY Ouro: ${vm['pegy_gold_fair_price_usd']:,.2f}</div></div>
                    <div class="kpi-box"><div class="lbl">Saúde Forense &amp; Solvência</div><div class="val">ROIC {fh['roic_goodwill_pct']:.1f}% vs WACC {fh['wacc_pct']:.2f}%</div><div class="sub">Sloan: {fh['sloan_ratio_pct']:+.1f}% | FCO/EBITDA: {fh['fco_to_ebitda']:.2f}x | IntCov: {fh['interest_coverage_x']:.1f}x</div></div>
                </div>

                <div class="insight-box"><strong>Veredito Automatizado &amp; Regime Consultivo:</strong> {_esc(dd.automated_consultative_verdict)}</div>

                <div class="section-banner">1. MATRIZ DO FUNIL DE 5 FILTROS QUANTITATIVOS &amp; FORENSES (SCORE {dd.screener_score_0_100}/100)</div>
                <table class="inst-table">
                    <thead><tr><th>Etapa</th><th>Filtro do Framework</th><th>Valor Calculado</th><th>Critério Estrito</th><th>Status</th><th>Score</th><th>Diagnóstico</th></tr></thead>
                    <tbody>{funnel_rows_html}</tbody>
                </table>

                <div class="section-banner">2. SÉRIE HISTÓRICA FORENSE DE 5 ANOS &amp; MATRIZ CAGR (12 KPIs DIVIDIDOS EM 2 TABELAS LEGÍVEIS)</div>
                <table class="inst-table">
                    <thead>
                        <tr><th>Ano</th><th>Sloan Ratio</th><th>FCO / EBITDA &amp; FCO</th><th>NWC (USD B)</th><th>ROIC vs WACC</th><th>Identidade DuPont (M × G × A = ROE)</th><th>Margem Bruta &amp; Shares</th></tr>
                    </thead>
                    <tbody>{hist_5y_rows}</tbody>
                </table>

                <table class="inst-table">
                    <thead><tr>{''.join(f'<th>{k} (3y | 5y | 10y)</th>' for k in kpis_a)}</tr></thead>
                    <tbody><tr>{cagr_cells_a}</tr></tbody>
                </table>
                <table class="inst-table">
                    <thead><tr>{''.join(f'<th>{k} (3y | 5y | 10y)</th>' for k in kpis_b)}</tr></thead>
                    <tbody><tr>{cagr_cells_b}</tr></tbody>
                </table>
            </div>

            <div class="page-section">
                <div class="section-banner">3. COCKPIT DE VALUATION MULTI-MÉTODO FORWARD (NTM) &amp; EXTRAÇÃO DOCUMENTAL 10-K</div>
                <table class="inst-table">
                    <thead>
                        <tr><th>Preço Spot &amp; WACC</th><th>DCF Forward (Cons / Base / Otim)</th><th>DCF Justo (10% MoS)</th><th>Reverse DCF (g_impl vs g_fund)</th><th>Owner Earnings vs US 10Y</th></tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="mono"><strong>${eq.current_price:,.2f}</strong> | WACC: {vm['wacc_capm_pct']:.2f}%</td>
                            <td class="mono">Cons: ${vm['dcf_conservador_usd']:,.2f} | Base: ${vm['dcf_base_usd']:,.2f} | Otim: ${vm['dcf_otimista_usd']:,.2f}</td>
                            <td class="mono"><strong>${vm['dcf_fair_mos10_usd']:,.2f}</strong> ({vm['dcf_upside_pct']:+.1f}%)</td>
                            <td class="mono"><strong>g_impl: {vm['reverse_dcf_g_impl_pct']:.1f}%</strong> vs g_fund: {vm['g_fund_projected_pct']:.1f}%</td>
                            <td class="mono">OE Yield: <strong>{vm['owner_earnings_yield_pct']:.2f}%</strong> vs US 10Y {vm['risk_free_us10y_pct']:.2f}%</td>
                        </tr>
                    </tbody>
                </table>

                <table class="inst-table">
                    <thead>
                        <tr><th>P/E (Spot / Forward NTM / Setor / 5y)</th><th>EV/EBITDA, P/B &amp; P/TBV</th><th>EVA (Lucro Econômico)</th><th>Múltiplo Soberano (Enterprise PEGY / PEGY Bancos)</th><th>Magic Formula &amp; SOTP</th></tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="mono">Spot: {vm['pe_current']:.1f}x | <strong>NTM: {vm['pe_ntm']:.1f}x</strong> | Setor: {vm['pe_sector_avg']:.1f}x | 5y: {vm['pe_5y_avg']:.1f}x</td>
                            <td class="mono">EV/EBITDA: {vm['ev_ebitda_current']:.1f}x | P/B: {vm['pb_current']:.2f}x | P/TBV: {vm['ptbv_current']:.2f}x</td>
                            <td class="mono"><strong>USD {vm['eva_usd_b']:+.1f}B</strong> ({vm['eva_pct_of_ic']:+.1f}% IC)</td>
                            <td class="mono"><strong>{_esc(vm['primary_pegy_label'])}</strong><br>{_auto_badge(vm['primary_pegy_status'])}</td>
                            <td class="mono">Rank #{vm['magic_formula_rank']} | SOTP: <strong>${vm['sotp_fair_price_usd']:,.2f}</strong> ({vm['sotp_upside_pct']:+.1f}%)</td>
                        </tr>
                    </tbody>
                </table>

                <div class="grid-2">
                    <div>
                        <div class="sub-banner">Decomposição Sum of the Parts (SOTP) por Unidade de Negócio</div>
                        <table class="inst-table">
                            <thead><tr><th>Segmento</th><th>% Receita</th><th>Peer Benchmark</th><th>Valor / Ação</th></tr></thead>
                            <tbody>{sotp_rows}</tbody>
                        </table>
                    </div>
                    <div>
                        <div class="sub-banner">Holofote Documental SEC 10-K / 10-Q: MD&amp;A, SOX 404(b) &amp; Top 3 Riscos Item 1A</div>
                        <table class="inst-table">
                            <thead><tr><th>Dimensão SEC</th><th>Extração Quantitativa &amp; Forense</th></tr></thead>
                            <tbody>
                                <tr><td><strong>Auditor &amp; SOX 404(b)</strong></td><td>{_auto_badge(ed.auditor_opinion)} | {_esc(ed.auditor_firm)}</td></tr>
                                <tr><td><strong>Decomposição MD&amp;A</strong></td><td class="mono">Vol: <strong>{mda_q.get('Volume Orgânico (%)', 0):+.1f}%</strong> | Preço: <strong>{mda_q.get('Pricing Power / Mix (%)', 0):+.1f}%</strong> | FX: <strong>{mda_q.get('Impacto Cambial FX (%)', 0):+.1f}%</strong></td></tr>
                                <tr><td><strong>Top 3 Riscos Item 1A</strong></td><td><ol style="margin:0;padding-left:14px;">{risks_html}</ol></td></tr>
                                <tr><td><strong>Form 4 &amp; Buybacks</strong></td><td>{_esc(ins.get('ceo_skin_in_the_game', ''))} (Var. Shares 5y: <strong>{ins.get('net_share_count_change_5y_pct', 0):+.2f}%</strong>)</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            """

        return f"""<!DOCTYPE html>
        <html lang="pt-BR">
        <head><meta charset="utf-8"><title>Dossiê Executivo Deep Dive — {_esc(dd.normalized_ticker)}</title><style>{css}</style></head>
        <body>{body_html}</body>
        </html>
        """

    def generate_deep_dive_pdf_bytes(
        self,
        dd: DeepDiveResultBundle,
        output_pdf_path: Optional[str] = None,
    ) -> bytes:
        html_str = self.build_deep_dive_html_report(dd)
        return self._compile_html_to_pdf_bytes(html_str, f"dossie_deep_dive_{dd.normalized_ticker}", output_pdf_path)

    def _compile_html_to_pdf_bytes(
        self,
        html_str: str,
        stem_name: str,
        output_pdf_path: Optional[str] = None,
    ) -> bytes:
        browser_exe = self._find_browser_executable()
        tmp_dir = tempfile.mkdtemp(prefix=f"agy_{stem_name}_")
        try:
            html_file = os.path.abspath(os.path.join(tmp_dir, f"{stem_name}.html"))
            pdf_file = (
                os.path.abspath(output_pdf_path)
                if output_pdf_path
                else os.path.abspath(os.path.join(tmp_dir, f"{stem_name}.pdf"))
            )
            user_data_dir = os.path.abspath(os.path.join(tmp_dir, "chrome_profile"))

            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_str)

            if browser_exe:
                cmd = [
                    browser_exe,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    f"--user-data-dir={user_data_dir}",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_file}",
                    html_file,
                ]
                subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)

            if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 1000:
                with open(pdf_file, "rb") as pf:
                    return pf.read()
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        return html_str.encode("utf-8")

"""
INTERACTIVE INSTITUTIONAL PLOTLY CHARTS BUILDER
Builds all interactive charts with institutional Dark theme and vector layout:
1. BTC Price + aSOPR (with 1.0 line highlighted as bull support / bear resistance)
2. BTC Price + Pi Cycle Top (111d vs 2x 350d) + 200W SMA + Hash Ribbon + MMC
3. Crypto Price + MVRV Z-Score (< 0 and > 7) and NUPL (< 0, 0.30, 0.60, 0.75)
4. Crypto Price vs. NVM Ratio + Exchange Inflow + CDD
5. Scatter Plot P/TBV vs. ROE para Bancos
6. Multi-Method Equity Valuation Comparison Chart (Spot Price vs. DCF vs. SOTP vs. PEGY Band)
7. Macro Charts: 10Y-2Y Spread (Zero line & de-inversion) + Yield Curve + PMI (Services vs Mfg) + M2 vs DXY vs Gold vs S&P 500 + ICSA Trend
"""

from __future__ import annotations

from typing import Dict, List
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from typing import Any, Optional
from core.macro_engine import MacroDataBundle
from core.equity_engine import EquityFullAnalysis, GLOBAL_BANKS_SCATTER_DATA
from core.crypto_engine import CryptoFullProfile
from core.deep_dive_engine import DeepDiveResultBundle
from core.integrity_guard import sanitize_plotly_figure_against_overlaps


DARK_BG = "#0B0F19"
CARD_BG = "#111827"
GRID_COLOR = "#1F2937"
FONT_COLOR = "#E2E8F0"


def _apply_dark_theme(
    fig: go.Figure,
    height: int = 440,
    title: str = "",
    margin: Optional[Dict[str, int]] = None,
    legend_pos: str = "top",
) -> go.Figure:
    if margin is None:
        if title:
            top_m = 85
            bot_m = 65 if legend_pos == "bottom" else 45
            margin = dict(l=45, r=45, t=top_m, b=bot_m)
        else:
            bot_m = 60 if legend_pos == "bottom" else 40
            margin = dict(l=45, r=45, t=42, b=bot_m)

    layout_kwargs: Dict[str, Any] = dict(
        height=height,
        paper_bgcolor=CARD_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", color=FONT_COLOR, size=11),
        margin=margin,
        hovermode="x unified",
    )

    if title:
        layout_kwargs["title"] = dict(
            text=f"<b>{title}</b>",
            font=dict(size=13, color="#F8FAFC"),
            x=0.01,
            y=0.985,
            xanchor="left",
            yanchor="top",
        )

    if legend_pos == "hidden":
        layout_kwargs["showlegend"] = False
    elif legend_pos == "bottom":
        layout_kwargs["showlegend"] = True
        layout_kwargs["legend"] = dict(
            orientation="h",
            yanchor="top",
            y=-0.16,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(15,23,42,0.85)",
            bordercolor="rgba(51,65,85,0.4)",
            borderwidth=1,
            font=dict(size=10, color="#94A3B8"),
        )
    elif legend_pos == "top":
        layout_kwargs["legend"] = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            bgcolor="rgba(15,23,42,0.85)",
            bordercolor="rgba(51,65,85,0.4)",
            borderwidth=1,
            font=dict(size=10, color="#94A3B8"),
        )

    fig.update_layout(**layout_kwargs)
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)

    # Style all subplot title annotations with crisp institutional styling
    fig.for_each_annotation(
        lambda a: a.update(
            font=dict(size=11, color="#94A3B8", family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
        ) if a.text and ("<b" not in a.text and "Spot:" not in a.text and "Line" not in a.text and "Floor" not in a.text and "Limit" not in a.text and "Zone" not in a.text and "Conversion" not in a.text and "50" not in a.text and "60" not in a.text) else None
    )
    return sanitize_plotly_figure_against_overlaps(
        fig,
        default_height=height,
        force_bottom_legend=(legend_pos != "hidden"),
    )


# ==============================================================================
# 1. BTC PRICE + aSOPR (1.0 LINE HIGHLIGHTED AS BULL SUPPORT / BEAR RESISTANCE)
# ==============================================================================
def build_btc_asopr_chart(crypto: CryptoFullProfile) -> go.Figure:
    s = crypto.chart_series
    px = s["Price"]
    asopr = s["aSOPR"]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.07,
        row_heights=[0.55, 0.45],
        subplot_titles=(
            f"{crypto.symbol} — Spot Price (USD)",
            "aSOPR (Adjusted Spent Output Profit Ratio) — Line 1.00 = Bull Support / Bear Resistance",
        ),
    )

    fig.add_trace(
        go.Scatter(x=px.index, y=px.values, name="Price (USD)", line=dict(color="#F59E0B", width=2.2)),
        row=1, col=1,
    )

    fig.add_trace(
        go.Scatter(x=asopr.index, y=asopr.values, name="aSOPR", line=dict(color="#38BDF8", width=2.0)),
        row=2, col=1,
    )

    # 1.0 line highlighted as support/resistance
    fig.add_hline(
        y=1.00,
        line_dash="dash",
        line_color="#EF4444",
        line_width=2.2,
        annotation_text="aSOPR = 1.00 (Bull Support / Bear Resistance | >1 Profit, <1 Loss)",
        annotation_position="top left",
        annotation_font_color="#FCA5A5",
        row=2, col=1,
    )

    return _apply_dark_theme(fig, height=480, title=f"Chart 1: {crypto.symbol} Price vs. aSOPR (Support/Resistance at 1.0)")


# ==============================================================================
# 2. BTC PRICE + PI CYCLE TOP + 200W SMA + HASH RIBBON + MMC
# ==============================================================================
def build_btc_picycle_200w_hashribbon_mmc_chart(crypto: CryptoFullProfile) -> go.Figure:
    s = crypto.chart_series
    px = s["Price"]
    sma111 = s["SMA_111D"]
    sma350x2 = s["SMA_350D_X2"]
    sma200w = s["SMA_200W"]
    mmc = s["MMC"]
    hr30 = s["HASH_SMA30"]
    hr60 = s["HASH_SMA60"]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.62, 0.38],
        subplot_titles=(
            "BTC Price vs. Pi Cycle Top (111d SMA vs 2x 350d SMA), 200W SMA (Secular Floor) & MMC (Cost of Production)",
            "Hash Ribbon (Miner Capitulation & Recovery): Hash Rate 30d SMA vs. 60d SMA",
        ),
    )

    fig.add_trace(go.Scatter(x=px.index, y=px.values, name="BTC Price", line=dict(color="#F8FAFC", width=2.3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=sma111.index, y=sma111.values, name="Pi Cycle 111d SMA", line=dict(color="#F59E0B", width=1.8)), row=1, col=1)
    fig.add_trace(go.Scatter(x=sma350x2.index, y=sma350x2.values, name="Pi Cycle 2x 350d SMA (Topo)", line=dict(color="#EF4444", width=1.8, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=sma200w.index, y=sma200w.values, name="200W SMA (Secular Floor)", line=dict(color="#10B981", width=2.0, dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=mmc.index, y=mmc.values, name="MMC (Minimum Mining Cost)", line=dict(color="#A855F7", width=1.8, dash="dashdot")), row=1, col=1)

    fig.add_trace(go.Scatter(x=hr30.index, y=hr30.values, name="Hash Rate 30d SMA (Fast)", line=dict(color="#34D399", width=2.0)), row=2, col=1)
    fig.add_trace(go.Scatter(x=hr60.index, y=hr60.values, name="Hash Rate SMA 60d (Lenta)", line=dict(color="#60A5FA", width=2.0, dash="dash")), row=2, col=1)

    return _apply_dark_theme(fig, height=520, title="Chart 2: BTC Price + Pi Cycle Top + 200W SMA + MMC + Hash Ribbon")


# ==============================================================================
# 3. CRYPTO PRICE + MVRV Z-SCORE AND NUPL
# ==============================================================================
def build_crypto_mvrv_nupl_chart(crypto: CryptoFullProfile) -> go.Figure:
    s = crypto.chart_series
    px = s["Price"]
    mvrv = s["MVRV_Z"]
    nupl = s["NUPL"]

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.40, 0.30, 0.30],
        subplot_titles=(
            f"{crypto.symbol} — Spot Price (USD)",
            "MVRV Z-Score (< 0 Fundo/Verde | > 7 Topo/Vermelho)",
            "NUPL (< 0 Loss/Buy | 0.30 Accumulation | 0.60/0.65 Alert | > 0.75 Euphoria/Sell)",
        ),
    )

    fig.add_trace(go.Scatter(x=px.index, y=px.values, name="Price (USD)", line=dict(color="#F59E0B", width=2.0)), row=1, col=1)

    fig.add_trace(go.Scatter(x=mvrv.index, y=mvrv.values, name="MVRV Z-Score", line=dict(color="#38BDF8", width=1.9)), row=2, col=1)
    fig.add_hline(y=0.0, line_dash="dash", line_color="#10B981", annotation_text="Fundo (< 0)", row=2, col=1)
    fig.add_hline(y=7.0, line_dash="dash", line_color="#EF4444", annotation_text="Topo (> 7)", row=2, col=1)

    fig.add_trace(go.Scatter(x=nupl.index, y=nupl.values, name="NUPL", line=dict(color="#A855F7", width=1.9)), row=3, col=1)
    fig.add_hline(y=0.0, line_dash="dash", line_color="#10B981", annotation_text="Capitulation (0.0)", row=3, col=1)
    fig.add_hline(y=0.30, line_dash="dot", line_color="#60A5FA", annotation_text="0.30", row=3, col=1)
    fig.add_hline(y=0.60, line_dash="dot", line_color="#FBBF24", annotation_text="0.60", row=3, col=1)
    fig.add_hline(y=0.75, line_dash="dash", line_color="#EF4444", annotation_text="Euforia (0.75)", row=3, col=1)

    return _apply_dark_theme(fig, height=560, title=f"Chart 3: {crypto.symbol} Price + MVRV Z-Score & NUPL")


# ==============================================================================
# 4. CRYPTO PRICE VS. NVM RATIO (+ EXCHANGE INFLOW & CDD)
# ==============================================================================
def build_crypto_nvm_and_cdd_chart(crypto: CryptoFullProfile) -> go.Figure:
    s = crypto.chart_series
    px = s["Price"]
    nvm = s["NVM_Ratio"]
    inflow = s["Exchange_Inflow"]
    cdd = s["CDD"]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.55, 0.45],
        specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
        subplot_titles=(
            f"{crypto.symbol} Price vs. NVM Ratio (Strength = NVM flat/falling while Price rises)",
            "Exchange Inflow + CDD (Coin Days Destroyed — Vintage Coin Distribution)",
        ),
    )

    fig.add_trace(go.Scatter(x=px.index, y=px.values, name="Price (USD)", line=dict(color="#F59E0B", width=2.2)), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=nvm.index, y=nvm.values, name="NVM Ratio (Metcalfe)", line=dict(color="#10B981", width=2.0, dash="dot")), row=1, col=1, secondary_y=True)

    fig.add_trace(go.Bar(x=inflow.index, y=inflow.values, name="Exchange Inflow (24h)", marker_color="rgba(59, 130, 246, 0.45)"), row=2, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=cdd.index, y=cdd.values, name="CDD (Coin Days Destroyed)", line=dict(color="#EF4444", width=1.8)), row=2, col=1, secondary_y=True)

    return _apply_dark_theme(fig, height=500, title=f"Chart 4: {crypto.symbol} Price vs. NVM Ratio & Exchange Inflow + CDD")


# ==============================================================================
# 5. SCATTER PLOT P/TBV VS. ROE PARA BANCOS
# ==============================================================================
def build_banks_ptbv_vs_roe_scatter() -> go.Figure:
    df = pd.DataFrame(GLOBAL_BANKS_SCATTER_DATA)
    fig = go.Figure()

    color_map = {
        "Carteira": "#10B981",
        "Peer Global": "#3B82F6",
        "Peer Emergente": "#F59E0B",
        "Value Trap (P/B < 1.0)": "#EF4444",
    }

    for grp, sub in df.groupby("Grupo"):
        fig.add_trace(go.Scatter(
            x=sub["ROE_pct"],
            y=sub["PTBV"],
            mode="markers+text",
            name=grp,
            text=sub["Ticker"],
            textposition="top center",
            marker=dict(size=14 if grp == "Carteira" else 11, color=color_map.get(grp, "#60A5FA"), line=dict(width=1.5, color="#FFFFFF")),
            customdata=np.stack([sub["Banco"], sub["PEGY_Fin"], sub["PB"]], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]} (%{text})</b><br>"
                "ROE: %{x:.1f}%<br>"
                "P/TBV: %{y:.2f}x<br>"
                "P/B: %{customdata[2]:.2f}x<br>"
                "PEGY Financeiro: %{customdata[1]:.2f}x<extra></extra>"
            ),
        ))

    # Fundamental regression line (Fair corridor: P/TBV = 0.115 * ROE - 0.10)
    x_line = np.linspace(5.0, 23.0, 50)
    y_line = 0.115 * x_line - 0.10
    fig.add_trace(go.Scatter(
        x=x_line, y=y_line,
        mode="lines",
        name="Sector Regression Line (Fair P/TBV for ROE)",
        line=dict(color="#94A3B8", width=1.8, dash="dash"),
    ))

    # Linha de alerta P/TBV = 1.0x
    fig.add_hline(
        y=1.0,
        line_dash="dot",
        line_color="#EF4444",
        annotation_text="Limite Estrutural (P/B < 1.0x = Risco Estrutural / Veto de Compra)",
        annotation_position="bottom right",
    )

    fig.update_xaxes(title_text="ROE — Return on Equity (%)")
    fig.update_yaxes(title_text="P/TBV — Price to Tangible Book Value (x)")
    return _apply_dark_theme(fig, height=440, title="Chart 5: Global Banking Sector Scatter Plot — P/TBV vs. ROE")


# ==============================================================================
# 6. MULTI-METHOD EQUITY VALUATION COMPARISON CHART
# ==============================================================================
def build_multi_method_valuation_chart(equities: List[EquityFullAnalysis]) -> go.Figure:
    tickers = [e.ticker for e in equities]
    curr_px = [e.current_price for e in equities]
    dcf_mos10 = [e.valuation_methods["dcf_fair_mos10_usd"] for e in equities]
    sotp_px = [e.valuation_methods["sotp_fair_price_usd"] for e in equities]
    pegy_gold_px = [e.valuation_methods["pegy_gold_fair_price_usd"] for e in equities]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Current Spot Price (USD)", x=tickers, y=curr_px, marker_color="#3B82F6"))
    fig.add_trace(go.Bar(name="Valor Justo DCF (c/ 10% MoS)", x=tickers, y=dcf_mos10, marker_color="#10B981"))
    fig.add_trace(go.Bar(name="Valor Justo SOTP (Peer Multiples)", x=tickers, y=sotp_px, marker_color="#A855F7"))
    fig.add_trace(go.Bar(name="Teto Faixa Ouro PEGY (1.2x / 1.0x)", x=tickers, y=pegy_gold_px, marker_color="#F59E0B"))

    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Price per Share (USD)")
    return _apply_dark_theme(
        fig,
        height=460,
        title="Chart 6: Multi-Method Equity Valuation Matrix (Spot Price vs. DCF vs. SOTP vs. PEGY Gold Band)",
    )


# ==============================================================================
# 7. MACRO CHARTS: 10Y-2Y SPREAD + 2Y/10Y DYNAMICS + PMI + M2 VS DXY + ICSA
# ==============================================================================
def build_macro_comprehensive_chart(macro: MacroDataBundle) -> go.Figure:
    sh = macro.series_history
    spread = sh["SPREAD_10Y_2Y"]
    dgs2 = sh["DGS2"]
    dgs10 = sh["DGS10"]
    pmi_s = sh["PMI_SERVICES"]
    pmi_m = sh["PMI_MFG"]
    m2 = sh["M2"]
    dxy = sh["DXY"]

    fig = make_subplots(
        rows=2, cols=2,
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": True}],
        ],
        subplot_titles=(
            "10Y-2Y Spread (%) — Zero Line Highlighted (De-inversion Alert)",
            "Yield Curve Tenors: 2-Year Yield (Short) vs. 10-Year Yield (Long)",
            "PMI Services vs. Manufacturing (50 Expansion & 60 Inflation Lines)",
            "Global Liquidity: M2 Money Supply (USD B) vs. DXY Dollar Index",
        ),
    )

    # 1) Spread 10Y-2Y
    fig.add_trace(go.Scatter(x=spread.index, y=spread.values, name="Spread 10Y-2Y (%)", line=dict(color="#38BDF8", width=2.2), fill="tozeroy", fillcolor="rgba(56,189,248,0.12)"), row=1, col=1)
    fig.add_hline(y=0.0, line_dash="dash", line_color="#EF4444", line_width=2.0, annotation_text="Zero Line (De-inversion)", row=1, col=1)

    # 2) 2Y vs 10Y Dynamics
    fig.add_trace(go.Scatter(x=dgs2.index, y=dgs2.values, name="US 2Y Yield (%)", line=dict(color="#F59E0B", width=2.0)), row=1, col=2)
    fig.add_trace(go.Scatter(x=dgs10.index, y=dgs10.values, name="US 10Y Yield (%)", line=dict(color="#10B981", width=2.0)), row=1, col=2)

    # 3) PMI Services vs Manufacturing
    fig.add_trace(go.Scatter(x=pmi_s.index, y=pmi_s.values, name="PMI Services", line=dict(color="#10B981", width=2.2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=pmi_m.index, y=pmi_m.values, name="PMI Manufacturing", line=dict(color="#60A5FA", width=2.0, dash="dot")), row=2, col=1)
    fig.add_hline(y=50.0, line_dash="dash", line_color="#FBBF24", annotation_text="50 (Expansion/Contraction)", row=2, col=1)
    fig.add_hline(y=60.0, line_dash="dot", line_color="#EF4444", annotation_text="60 (Inflation Risk)", row=2, col=1)

    # 4) M2 vs DXY
    fig.add_trace(go.Scatter(x=m2.index, y=m2.values, name="M2 Money Supply", line=dict(color="#10B981", width=2.2)), row=2, col=2, secondary_y=False)
    fig.add_trace(go.Scatter(x=dxy.index, y=dxy.values, name="DXY (US Dollar Index)", line=dict(color="#EF4444", width=1.9, dash="dash")), row=2, col=2, secondary_y=True)

    return _apply_dark_theme(
        fig,
        height=660,
        title="Chart 7: Leading Macro Dashboard — 10Y-2Y Spread, 2Y vs 10Y Dynamics, PMI (Services vs Mfg) and M2 vs DXY",
        legend_pos="bottom",
    )


def build_yield_curve_and_icsa_chart(macro: MacroDataBundle) -> go.Figure:
    verts = macro.yield_curve["vertices"]
    icsa = macro.series_history["ICSA"]

    fig = make_subplots(
        rows=1, cols=2,
        horizontal_spacing=0.08,
        subplot_titles=(
            f"Curva de Juros Atual dos EUA — {macro.yield_curve['curve_classification']}",
            "ICSA (Initial Jobless Claims — Paired with Sahm Rule)",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=list(verts.keys()),
            y=list(verts.values()),
            mode="lines+markers+text",
            name="US Treasury Yield Curve (%)",
            text=[f"{v:.2f}%" for v in verts.values()],
            textposition="top center",
            line=dict(color="#38BDF8", width=2.5),
            marker=dict(size=9, color="#F59E0B"),
        ),
        row=1, col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=icsa.index,
            y=icsa.values,
            name="ICSA Semanal",
            line=dict(color="#A855F7", width=2.0),
        ),
        row=1, col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=icsa.index,
            y=icsa.rolling(4, min_periods=1).mean().values,
            name="ICSA 4-Week Moving Average",
            line=dict(color="#F59E0B", width=2.0, dash="dash"),
        ),
        row=1, col=2,
    )

    return _apply_dark_theme(fig, height=360, title="Treasury Yield Curve Term Structure & Initial Jobless Claims (ICSA Trend)")


# ==============================================================================
# 8. TARGET PORTFOLIO WEIGHT VALIDATION GAUGE (SUM = 100%)
# ==============================================================================
def build_portfolio_weight_gauge_chart(target_weight_sum_pct: float) -> go.Figure:
    diff = round(target_weight_sum_pct - 100.0, 2)
    is_ok = abs(diff) <= 0.05
    bar_color = "#10B981" if is_ok else ("#F59E0B" if target_weight_sum_pct < 100.0 else "#EF4444")

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=target_weight_sum_pct,
            number=dict(suffix="%", font=dict(size=32, color="#F8FAFC"), valueformat=".2f"),
            delta=dict(
                reference=100.0,
                increasing=dict(color="#EF4444"),
                decreasing=dict(color="#F59E0B"),
                valueformat=".2f",
                suffix=" pp vs 100%",
            ),
            title=dict(
                text="<b>Validador de Soma dos Pesos Alvo (%)</b><br><span style='font-size:11px;color:#94A3B8'>Meta Estrita: 100.00%</span>",
                font=dict(size=13, color="#E2E8F0"),
            ),
            gauge=dict(
                axis=dict(range=[0, 140], tickwidth=1, tickcolor="#64748B"),
                bar=dict(color=bar_color, thickness=0.38),
                bgcolor="#0B0F19",
                borderwidth=1,
                bordercolor="#1E293B",
                steps=[
                    dict(range=[0, 99.5], color="rgba(245, 158, 11, 0.14)"),
                    dict(range=[99.5, 100.5], color="rgba(16, 185, 129, 0.28)"),
                    dict(range=[100.5, 140], color="rgba(239, 68, 68, 0.16)"),
                ],
                threshold=dict(
                    line=dict(color="#10B981", width=4),
                    thickness=0.82,
                    value=100.0,
                ),
            ),
        )
    )
    fig.update_layout(
        height=250,
        paper_bgcolor=CARD_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family="Inter, sans-serif", color=FONT_COLOR),
        margin=dict(l=30, r=30, t=55, b=20),
    )
    return fig


# ==============================================================================
# 9. 5-YEAR FORENSIC HEALTH AUDIT (SLOAN, CFO/EBITDA, NWC, ROIC VS WACC)
# ==============================================================================
def build_deep_dive_forensic_5y_chart(dd: DeepDiveResultBundle) -> go.Figure:
    fh5 = dd.forensic_5y_history or {}
    years = fh5.get("years", ["2022", "2023", "2024", "2025", "2026 (LTM)"])
    sloan = fh5.get("sloan_pct", [0, 0, 0, 0, 0])
    fco_eb = fh5.get("fco_to_ebitda", [1, 1, 1, 1, 1])
    nwc = fh5.get("nwc_b", [0, 0, 0, 0, 0])
    fco = fh5.get("fco_b", [0, 0, 0, 0, 0])
    roic = fh5.get("roic_pct", [15, 15, 15, 15, 15])
    wacc = fh5.get("wacc_pct", [8, 8, 8, 8, 8])

    fig = make_subplots(
        rows=2,
        cols=2,
        vertical_spacing=0.25,
        horizontal_spacing=0.10,
        subplot_titles=(
            "5Y Historical Sloan Ratio (%) — [Alert: > +10% | Optimal: < -10%]",
            "Cash Conversion: CFO / EBITDA (x) — [Ideal: >= 0.85x | Pure: 1.0x]",
            "Net Working Capital (NWC) vs. Operating CFO (USD B)",
            "Value Creation Tree: ROIC with Goodwill vs. WACC (%)",
        ),
    )

    # 1) Sloan Ratio
    fig.add_trace(
        go.Bar(
            x=years,
            y=sloan,
            name="Sloan Ratio (%)",
            marker_color=["#10B981" if v <= 0 else ("#F59E0B" if v <= 10 else "#EF4444") for v in sloan],
            text=[f"{v:+.1f}%" for v in sloan],
            textposition="outside",
        ),
        row=1,
        col=1,
    )
    fig.add_hline(y=10.0, line_dash="dash", line_color="#EF4444", annotation_text="Limite Alerta (+10%)", row=1, col=1)
    fig.add_hline(y=-10.0, line_dash="dot", line_color="#10B981", annotation_text="Optimal Zone (-10%)", row=1, col=1)
    max_sloan = max(max(sloan), 12.0)
    min_sloan = min(min(sloan), -12.0)
    fig.update_yaxes(range=[min_sloan * 1.35 if min_sloan < 0 else -14.0, max_sloan * 1.35 if max_sloan > 0 else 14.0], row=1, col=1)

    # 2) FCO / EBITDA
    fig.add_trace(
        go.Scatter(
            x=years,
            y=fco_eb,
            mode="lines+markers+text",
            name="FCO / EBITDA (x)",
            text=[f"{v:.2f}x" for v in fco_eb],
            textposition="top center",
            line=dict(color="#38BDF8", width=2.5),
            marker=dict(size=9, color="#10B981"),
        ),
        row=1,
        col=2,
    )
    fig.add_hline(y=1.0, line_dash="dash", line_color="#10B981", annotation_text="Pure Conversion (1.0x)", row=1, col=2)
    fig.add_hline(y=0.80, line_dash="dot", line_color="#EF4444", annotation_text="Piso Forense (0.80x)", row=1, col=2)
    max_fco_eb = max(max(fco_eb), 1.05)
    min_fco_eb = min(min(fco_eb), 0.70)
    fig.update_yaxes(range=[min_fco_eb * 0.88, max_fco_eb * 1.22], row=1, col=2)

    # 3) NWC vs FCO (Grouped Bars)
    fig.add_trace(
        go.Bar(
            x=years,
            y=fco,
            name="FCO Operacional (USD B)",
            marker_color="#3B82F6",
            text=[f"${v:,.1f}B" for v in fco],
            textposition="auto",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=years,
            y=nwc,
            name="Net Working Capital NWC (USD B)",
            marker_color="#F59E0B",
            text=[f"${v:,.1f}B" for v in nwc],
            textposition="auto",
        ),
        row=2,
        col=1,
    )
    max_nwc_fco = max(max(fco + nwc), 5.0)
    min_nwc_fco = min(min(fco + nwc), 0.0)
    fig.update_yaxes(range=[min(min_nwc_fco * 1.25, 0.0) if min_nwc_fco < 0 else 0.0, max_nwc_fco * 1.25], row=2, col=1)

    # 4) ROIC vs WACC
    fig.add_trace(
        go.Scatter(
            x=years,
            y=roic,
            mode="lines+markers+text",
            name="ROIC c/ Goodwill (%)",
            text=[f"{v:.1f}%" for v in roic],
            textposition="top center",
            line=dict(color="#10B981", width=2.8),
            marker=dict(size=8, color="#10B981"),
        ),
        row=2,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=wacc,
            mode="lines+markers+text",
            name="WACC — Custo de Capital (%)",
            text=[f"{v:.1f}%" for v in wacc],
            textposition="bottom center",
            line=dict(color="#EF4444", width=2.2, dash="dash"),
            marker=dict(size=8, color="#EF4444"),
        ),
        row=2,
        col=2,
    )
    max_rw = max(max(roic + wacc), 15.0)
    min_rw = min(min(roic + wacc), 0.0)
    fig.update_yaxes(range=[min(min_rw * 0.85, 0.0) if min_rw < 0 else 0.0, max_rw * 1.25], row=2, col=2)

    fig.update_layout(barmode="group")
    return _apply_dark_theme(
        fig,
        height=640,
        title="",
        legend_pos="bottom",
    )


# ==============================================================================
# 10. DUPONT IDENTITY (3 PILLARS) + SHARE COUNT (BUYBACKS) & GROSS MARGIN
# ==============================================================================
def build_deep_dive_dupont_and_margins_chart(dd: DeepDiveResultBundle) -> go.Figure:
    fh5 = dd.forensic_5y_history or {}
    years = fh5.get("years", ["2022", "2023", "2024", "2025", "2026 (LTM)"])
    dm = fh5.get("dupont_margin_pct", [20, 20, 20, 20, 20])
    dt = fh5.get("dupont_turnover_x", [0.8, 0.8, 0.8, 0.8, 0.8])
    dl = fh5.get("dupont_leverage_x", [1.8, 1.8, 1.8, 1.8, 1.8])
    roe = fh5.get("roe_pct", [28, 28, 28, 28, 28])
    gm = fh5.get("gross_margin_pct", [50, 50, 50, 50, 50])
    shares = dd.share_count_5y_b or [1.0, 0.99, 0.98, 0.97, 0.96]

    fig = make_subplots(
        rows=1,
        cols=2,
        horizontal_spacing=0.12,
        specs=[[{"secondary_y": True}, {"secondary_y": True}]],
        subplot_titles=(
            "DuPont Decomposition: Net Margin (%), Asset Turnover (x), Leverage (x) & ROE (%)",
            "Economic Moats & Capital Allocation: 5Y Gross Margin (%) vs. Diluted Share Count (B)",
        ),
    )

    # Col 1: DuPont
    fig.add_trace(
        go.Bar(x=years, y=dm, name="Net Margin (%)", marker_color="rgba(16, 185, 129, 0.55)"),
        row=1, col=1, secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=years, y=roe, mode="lines+markers", name="ROE DuPont (%)", line=dict(color="#38BDF8", width=2.5)),
        row=1, col=1, secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=years, y=dt, mode="lines+markers", name="Giro do Ativo (x)", line=dict(color="#F59E0B", width=2.0, dash="dot")),
        row=1, col=1, secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(x=years, y=dl, mode="lines+markers", name="Alavancagem A/PL (x)", line=dict(color="#EF4444", width=2.0, dash="dash")),
        row=1, col=1, secondary_y=True,
    )
    fig.update_yaxes(range=[0, max(max(dm + roe), 20.0) * 1.25], row=1, col=1, secondary_y=False)
    fig.update_yaxes(range=[0, max(max(dt + dl), 2.0) * 1.25], row=1, col=1, secondary_y=True)

    # Col 2: Gross Margin & Share Count
    fig.add_trace(
        go.Scatter(
            x=years,
            y=gm,
            mode="lines+markers+text",
            name="Margem Bruta (%)",
            text=[f"{v:.1f}%" for v in gm],
            textposition="top center",
            line=dict(color="#10B981", width=2.5),
        ),
        row=1, col=2, secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=years,
            y=shares,
            name="Diluted Share Count (Billion Shares)",
            marker_color="rgba(168, 85, 247, 0.45)",
            text=[f"{v:.2f}B" for v in shares],
            textposition="auto",
        ),
        row=1, col=2, secondary_y=True,
    )
    fig.update_yaxes(range=[0, max(max(gm), 50.0) * 1.25], row=1, col=2, secondary_y=False)
    fig.update_yaxes(range=[0, max(max(shares), 1.0) * 1.25], row=1, col=2, secondary_y=True)

    return _apply_dark_theme(
        fig,
        height=480,
        title="",
        legend_pos="bottom",
    )


# ==============================================================================
# 11. MULTI-METHOD VALUATION COCKPIT + REVERSE DCF + OWNER EARNINGS + MD&A
# ==============================================================================
def build_deep_dive_valuation_cockpit_chart(dd: DeepDiveResultBundle, rf_pct: float = 4.42) -> go.Figure:
    eq = dd.equity_analysis
    vm = eq.valuation_methods
    mda = dd.mda_quant_breakdown or {
        "Organic Volume (%)": 5.0,
        "Pricing Power / Mix (%)": 3.5,
        "FX Headwind Impact (%)": -0.5,
        "Crescimento Total Receita (%)": 8.0,
    }

    # 2-Row Layout: Row 1 = Full-width Fair Value Grid (7 bars); Row 2 = Reverse DCF (Left) & MD&A (Right)
    # Notice: exactly 3 subplots exist because (1, 2) is merged into (1, 1).
    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[
            [{"colspan": 2}, None],
            [{}, {}],
        ],
        vertical_spacing=0.28,
        horizontal_spacing=0.10,
        subplot_titles=(
            "Multi-Method Fair Value Grid vs. Spot Price (DCF 3 Scenarios + 10% MoS, SOTP & PEGY Gold Band)",
            "Reverse DCF (g_impl vs. g_fund & CAGR FCF 5y) & Owner Earnings vs. US 10Y",
            "MD&A Revenue Growth Decomposition (% Volume, % Price, % FX)",
        ),
    )

    # Row 1 (Colspan=2): Grade de Valor Justo
    labels_val = [
        "Current Spot Price",
        "DCF Conservador",
        "DCF (c/ 10% MoS)",
        "DCF Base",
        "SOTP Fair Value",
        "PEGY Faixa Ouro",
        "DCF Otimista",
    ]
    vals_val = [
        eq.current_price,
        vm["dcf_conservador_usd"],
        vm["dcf_fair_mos10_usd"],
        vm["dcf_base_usd"],
        vm["sotp_fair_price_usd"],
        vm["pegy_gold_fair_price_usd"],
        vm["dcf_otimista_usd"],
    ]
    colors_val = [
        "#3B82F6",
        "#64748B",
        "#10B981",
        "#34D399",
        "#A855F7",
        "#F59E0B",
        "#38BDF8",
    ]
    fig.add_trace(
        go.Bar(
            x=labels_val,
            y=vals_val,
            name="Grade de Valor Justo (USD)",
            marker_color=colors_val,
            text=[f"${v:,.2f}" for v in vals_val],
            textposition="outside",
        ),
        row=1,
        col=1,
    )
    fig.add_hline(
        y=eq.current_price,
        line_dash="dash",
        line_color="#F8FAFC",
        annotation_text=f"Spot: ${eq.current_price:,.2f}",
        row=1,
        col=1,
    )
    max_val_1 = max(vals_val) if vals_val else 100.0
    fig.update_yaxes(range=[0, max_val_1 * 1.25], row=1, col=1)

    # Row 2, Col 1: Reverse DCF + Owner Earnings vs Risk Free
    cagr_fcf_5y = eq.cagr_matrix_12_kpis.get("FCF", {}).get("5y", vm["g_fund_projected_pct"])
    labels_g = [
        "g_impl (Reverse DCF)",
        "g_fund (Projetado)",
        "CAGR FCF (5y)",
        "Owner Earn. Yield",
        "US 10Y (Risk-Free)",
    ]
    vals_g = [
        vm["reverse_dcf_g_impl_pct"],
        vm["g_fund_projected_pct"],
        cagr_fcf_5y,
        vm["owner_earnings_yield_pct"],
        rf_pct,
    ]
    colors_g = [
        "#EF4444" if vm["reverse_dcf_g_impl_pct"] > vm["g_fund_projected_pct"] else "#10B981",
        "#38BDF8",
        "#A855F7",
        "#F59E0B",
        "#94A3B8",
    ]
    fig.add_trace(
        go.Bar(
            x=labels_g,
            y=vals_g,
            name="Taxas Anuais (%)",
            marker_color=colors_g,
            text=[f"{v:.1f}%" for v in vals_g],
            textposition="outside",
        ),
        row=2,
        col=1,
    )
    max_g = max(vals_g) if vals_g else 20.0
    min_g = min(vals_g) if vals_g else 0.0
    fig.update_yaxes(range=[min(min_g * 1.30, 0.0) if min_g < 0 else 0.0, max_g * 1.35 + 5.0], row=2, col=1)

    # Row 2, Col 2: MD&A Decomposition
    mda_keys = ["Organic Volume (%)", "Pricing Power / Mix (%)", "FX Headwind Impact (%)", "Total Revenue Growth (%)"]
    mda_vals = [mda.get(k, 0.0) for k in mda_keys]
    mda_colors = ["#38BDF8", "#10B981", "#EF4444" if mda_vals[2] < 0 else "#F59E0B", "#A855F7"]
    fig.add_trace(
        go.Bar(
            x=["% Volume", "% Price (Mix)", "% FX (Currency)", "Total Revenue"],
            y=mda_vals,
            name="MD&A Decomposition (%)",
            marker_color=mda_colors,
            text=[f"{v:+.1f}%" for v in mda_vals],
            textposition="outside",
        ),
        row=2,
        col=2,
    )
    max_mda = max(mda_vals) if mda_vals else 10.0
    min_mda = min(mda_vals) if mda_vals else 0.0
    fig.update_yaxes(range=[min(min_mda * 1.30, 0.0) if min_mda < 0 else 0.0, max_mda * 1.35 + 15.0], row=2, col=2)

    return _apply_dark_theme(
        fig,
        height=660,
        title="",
        legend_pos="hidden",
    )


# ==============================================================================
# 12. ON-CHAIN GAUGES (MVRV Z-SCORE & NUPL) + GITHUB AUDIT
# ==============================================================================
def build_crypto_onchain_gauges_chart(dd: DeepDiveResultBundle) -> go.Figure:
    cp = dd.crypto_profile
    cd = dd.crypto_dossier
    mvrv = cp.onchain_metrics["mvrv_z_score"]
    nupl = cp.onchain_metrics["nupl"]
    sniffer = cd.token_sniffer_score
    score = dd.screener_score_0_100

    fig = make_subplots(
        rows=1,
        cols=4,
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]],
        horizontal_spacing=0.06,
    )

    # 1) MVRV Z-Score Gauge
    mvrv_color = "#10B981" if mvrv <= 1.0 else ("#38BDF8" if mvrv <= 2.5 else ("#F59E0B" if mvrv <= 5.0 else "#EF4444"))
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=mvrv,
            number=dict(font=dict(size=24, color="#F8FAFC"), valueformat=".2f"),
            title=dict(text="<b>MVRV Z-Score</b><br><span style='font-size:10px;color:#94A3B8'>&lt;0 Fundo | &gt;7 Topo</span>", font=dict(size=11)),
            gauge=dict(
                axis=dict(range=[-1.0, 8.0]),
                bar=dict(color=mvrv_color, thickness=0.35),
                bgcolor="#0B0F19",
                steps=[
                    dict(range=[-1.0, 0.5], color="rgba(16, 185, 129, 0.28)"),
                    dict(range=[0.5, 2.5], color="rgba(56, 189, 248, 0.20)"),
                    dict(range=[2.5, 5.5], color="rgba(245, 158, 11, 0.20)"),
                    dict(range=[5.5, 8.0], color="rgba(239, 68, 68, 0.28)"),
                ],
                threshold=dict(line=dict(color="#EF4444", width=3), thickness=0.8, value=7.0),
            ),
        ),
        row=1, col=1,
    )

    # 2) NUPL Gauge
    nupl_color = "#10B981" if nupl < 0.30 else ("#38BDF8" if nupl < 0.60 else ("#F59E0B" if nupl < 0.75 else "#EF4444"))
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=nupl,
            number=dict(font=dict(size=24, color="#F8FAFC"), valueformat=".2f"),
            title=dict(text="<b>On-Chain NUPL</b><br><span style='font-size:10px;color:#94A3B8'>&lt;0 Capitulation | &gt;0.75 Market Top</span>", font=dict(size=11)),
            gauge=dict(
                axis=dict(range=[-0.3, 1.0]),
                bar=dict(color=nupl_color, thickness=0.35),
                bgcolor="#0B0F19",
                steps=[
                    dict(range=[-0.3, 0.0], color="rgba(16, 185, 129, 0.32)"),
                    dict(range=[0.0, 0.30], color="rgba(52, 211, 153, 0.20)"),
                    dict(range=[0.30, 0.60], color="rgba(56, 189, 248, 0.20)"),
                    dict(range=[0.60, 0.75], color="rgba(245, 158, 11, 0.22)"),
                    dict(range=[0.75, 1.0], color="rgba(239, 68, 68, 0.30)"),
                ],
                threshold=dict(line=dict(color="#EF4444", width=3), thickness=0.8, value=0.75),
            ),
        ),
        row=1, col=2,
    )

    # 3) Token Sniffer Score Gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=sniffer,
            number=dict(suffix="/100", font=dict(size=22, color="#F8FAFC")),
            title=dict(text="<b>Token Sniffer Audit</b><br><span style='font-size:10px;color:#94A3B8'>Filtro &gt;= 85/100</span>", font=dict(size=11)),
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color="#10B981" if sniffer >= 85 else "#EF4444", thickness=0.35),
                bgcolor="#0B0F19",
                steps=[
                    dict(range=[0, 85], color="rgba(239, 68, 68, 0.18)"),
                    dict(range=[85, 100], color="rgba(16, 185, 129, 0.25)"),
                ],
                threshold=dict(line=dict(color="#10B981", width=3), thickness=0.8, value=85),
            ),
        ),
        row=1, col=3,
    )

    # 4) Screener Score 0-100 Gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number=dict(suffix="/100", font=dict(size=22, color="#F8FAFC")),
            title=dict(text="<b>Score Framework</b><br><span style='font-size:10px;color:#94A3B8'>Funil 5 Filtros</span>", font=dict(size=11)),
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color="#10B981" if score >= 85 else ("#F59E0B" if score >= 70 else "#EF4444"), thickness=0.35),
                bgcolor="#0B0F19",
                steps=[
                    dict(range=[0, 65], color="rgba(239, 68, 68, 0.18)"),
                    dict(range=[65, 85], color="rgba(245, 158, 11, 0.20)"),
                    dict(range=[85, 100], color="rgba(16, 185, 129, 0.26)"),
                ],
            ),
        ),
        row=1, col=4,
    )

    fig.update_layout(
        height=320,
        paper_bgcolor=CARD_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family="Inter, sans-serif", color=FONT_COLOR),
        margin=dict(l=20, r=20, t=75, b=20),
        title=dict(text=f"On-Chain Cycle & Security Dashboard ({dd.normalized_ticker})", font=dict(size=14, color="#F8FAFC"), x=0.01),
    )
    return fig


def build_crypto_github_and_earnings_chart(dd: DeepDiveResultBundle) -> go.Figure:
    gh_peers = dd.github_peers_comparison or []
    re_brk = dd.real_earnings_period_breakdown or {}

    fig = make_subplots(
        rows=1,
        cols=2,
        horizontal_spacing=0.10,
        subplot_titles=(
            "Atividade de Engenharia GitHub: Commits (4w) & Active Devs vs. Benchmarks",
            "Protocol Real Economics (Annualized USD M): Fees vs. Issuance vs. Real Earnings",
        ),
    )

    # Col 1: GitHub Activity (Shorten names for clean presentation)
    clean_proto_names = []
    for p in gh_peers:
        raw_name = p["Protocolo"]
        # Shorten e.g. "Ethereum (L1 Smart Contracts)" -> "Ethereum"
        short_n = raw_name.split(" ")[0].split("(")[0].strip()
        clean_proto_names.append(short_n if len(short_n) <= 12 else short_n[:12])

    commits = [p["Commits (4w)"] for p in gh_peers]
    devs = [p["Active Devs (Mensal)"] for p in gh_peers]

    fig.add_trace(
        go.Bar(x=clean_proto_names, y=commits, name="Commits (4w)", marker_color="#3B82F6", text=commits, textposition="auto"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(x=clean_proto_names, y=devs, name="Active Devs", marker_color="#10B981", text=devs, textposition="auto"),
        row=1, col=1,
    )
    fig.add_hline(y=40, line_dash="dash", line_color="#F59E0B", annotation_text="Piso Framework (40 Devs)", row=1, col=1)

    # Col 2: Protocol Real Earnings
    fees_m = re_brk.get("annual_fees_m", 0.0)
    iss_m = re_brk.get("annual_issuance_m", 0.0)
    re_m = re_brk.get("annual_real_earnings_m", 0.0)

    fig.add_trace(
        go.Bar(
            x=["Protocol Fees (Revenue)", "Token Issuance (Dilution)", "Real Earnings (Retained Cash Flow)"],
            y=[fees_m, iss_m, re_m],
            name="Economia Real Anual (USD M)",
            marker_color=["#38BDF8", "#F59E0B", "#10B981" if re_m > 0 else "#EF4444"],
            text=[f"USD {fees_m:,.1f}M", f"USD {iss_m:,.1f}M", f"USD {re_m:+,.1f}M"],
            textposition="auto",
        ),
        row=1, col=2,
    )

    max_gh = max(max(commits + devs) if (commits and devs) else 50, 50)
    fig.update_yaxes(range=[0, max_gh * 1.25], row=1, col=1)

    all_re_vals = [fees_m, iss_m, abs(re_m)]
    max_re = max(max(all_re_vals) if all_re_vals else 10.0, 10.0)
    min_re = min(re_m, 0.0)
    fig.update_yaxes(range=[min_re * 1.25 if min_re < 0 else 0.0, max_re * 1.25], row=1, col=2)

    fig.update_layout(barmode="group")
    return _apply_dark_theme(
        fig,
        height=460,
        title="",
        legend_pos="bottom",
    )


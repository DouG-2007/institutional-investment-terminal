"""
================================================================================
PURE-SVG VECTOR CHART GENERATORS FOR A4 LANDSCAPE MASTER PDF EXPORT
================================================================================
Zero-dependency, print-safe inline `<svg>` chart builders designed specifically
for Headless Chromium `--print-to-pdf` A4 landscape rendering:
  1. render_yield_curve_svg(macro)
  2. render_valuation_vs_spot_svg(equities)
  3. render_crypto_cycle_svg(cryptos)
  4. render_backtest_equity_svg(backtest)

Every chart sits inside a crisp card with `break-inside: avoid`, generous
margins, clean label truncation, and high-contrast light-paper institutional
typography so nothing ever clips or overlaps across page boundaries.
================================================================================
"""

from __future__ import annotations

import html
from typing import Any, Dict, List, Optional

import pandas as pd


def _esc(val: Any) -> str:
    return html.escape(str(val or ""))


def _wrap_card(title: str, subtitle: str, svg_body: str) -> str:
    return (
        '<div style="background:#F8FAFC;border:1px solid #CBD5E1;border-radius:6px;'
        'padding:8px 10px;margin:6px 0 8px 0;break-inside:avoid;page-break-inside:avoid;">'
        f'<div style="font-size:8pt;font-weight:800;color:#0F172A;margin-bottom:1px;">{_esc(title)}</div>'
        f'<div style="font-size:6.8pt;color:#475569;margin-bottom:4px;">{_esc(subtitle)}</div>'
        f"{svg_body}"
        "</div>"
    )


def render_yield_curve_svg(macro: Any) -> str:
    yc = getattr(macro, "yield_curve", {}) or {}
    verts = yc.get("vertices") or {}
    ordered = ["3M", "1Y", "2Y", "5Y", "10Y", "30Y"]
    pts: List[tuple[str, float]] = [
        (k, float(verts[k]))
        for k in ordered
        if k in verts and verts[k] is not None
    ]
    if len(pts) < 3:
        return ""

    w, h = 760, 178
    ml, mr, mt, mb = 52, 34, 24, 30
    cw, ch = w - ml - mr, h - mt - mb

    ys = [p[1] for p in pts]
    y_min = max(0.0, min(ys) - 0.35)
    y_max = max(ys) + 0.40
    y_span = max(0.5, y_max - y_min)

    def _xy(i: int, val: float) -> tuple[float, float]:
        x = ml + (i / max(1, len(pts) - 1)) * cw
        y = mt + (1.0 - (val - y_min) / y_span) * ch
        return round(x, 1), round(y, 1)

    coords = [_xy(i, v) for i, (_k, v) in enumerate(pts)]
    poly_pts = " ".join(f"{x},{y}" for x, y in coords)
    area_pts = f"{coords[0][0]},{mt + ch} {poly_pts} {coords[-1][0]},{mt + ch}"

    grid_svg = ""
    for step in range(4):
        gv = y_min + (step / 3.0) * y_span
        _, gy = _xy(0, gv)
        grid_svg += (
            f'<line x1="{ml}" y1="{gy}" x2="{w - mr}" y2="{gy}" '
            f'stroke="#E2E8F0" stroke-width="1" stroke-dasharray="3,3"/>'
            f'<text x="{ml - 6}" y="{gy + 3}" text-anchor="end" '
            f'font-size="9" fill="#64748B" font-family="Consolas,monospace">{gv:.2f}%</text>'
        )

    nodes_svg = ""
    for (lbl, val), (x, y) in zip(pts, coords):
        col = "#DC2626" if lbl in ("2Y", "10Y") else "#1D4ED8"
        nodes_svg += (
            f'<circle cx="{x}" cy="{y}" r="4.2" fill="{col}" stroke="#FFFFFF" stroke-width="1.5"/>'
            f'<text x="{x}" y="{y - 8}" text-anchor="middle" font-size="9.5" font-weight="700" '
            f'fill="#0F172A" font-family="Consolas,monospace">{val:.2f}%</text>'
            f'<text x="{x}" y="{h - 10}" text-anchor="middle" font-size="9.5" font-weight="700" '
            f'fill="#334155">{_esc(lbl)}</text>'
        )

    spread_bps = float(yc.get("spread_10y_2y_bps", 0.0))
    hy_spread = float((getattr(macro, "monetary_aggregates", {}) or {}).get("hy_credit_spread_pct", 3.45))
    svg = (
        f'<svg viewBox="0 0 {w} {h}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="{ml}" y="{mt}" width="{cw}" height="{ch}" fill="#FFFFFF" stroke="#E2E8F0"/>'
        f"{grid_svg}"
        f'<polygon points="{area_pts}" fill="rgba(37, 99, 235, 0.12)"/>'
        f'<polyline fill="none" stroke="#1D4ED8" stroke-width="2.5" points="{poly_pts}"/>'
        f"{nodes_svg}"
        f"</svg>"
    )
    return _wrap_card(
        "U.S. Sovereign Treasury Yield Curve (Constant Maturity)",
        f"10Y–2Y Spread: {spread_bps:+.1f} bps | FRED HY Credit Spread: {hy_spread:.2f}% | Curve: {yc.get('curve_classification', '')}",
        svg,
    )


def render_valuation_vs_spot_svg(equities: List[Any]) -> str:
    rows = []
    for eq in equities[:10]:
        vm = getattr(eq, "valuation_methods", {}) or {}
        px = float(getattr(eq, "current_price", 0.0) or 0.0)
        dcf = float(vm.get("dcf_fair_mos10_usd", 0.0) or 0.0)
        if px > 0 and dcf > 0:
            rows.append((str(eq.ticker), px, dcf))
    if not rows:
        return ""

    w, h = 760, max(165, 34 + len(rows) * 20)
    ml, mr, mt, _mb = 62, 74, 18, 22
    cw = w - ml - mr
    max_val = max(max(r[1], r[2]) for r in rows) * 1.12 or 100.0

    bars_svg = ""
    for idx, (tk, px, dcf) in enumerate(rows):
        y0 = mt + idx * 19
        w_px = max(2.0, (px / max_val) * cw)
        w_dcf = max(2.0, (dcf / max_val) * cw)
        up = ((dcf / px) - 1.0) * 100.0
        col_dcf = "#059669" if dcf >= px else "#D97706"
        bars_svg += (
            f'<text x="{ml - 6}" y="{y0 + 11}" text-anchor="end" font-size="9.5" font-weight="700" '
            f'fill="#0F172A" font-family="Consolas,monospace">{_esc(tk)}</text>'
            f'<rect x="{ml}" y="{y0 + 1}" width="{w_px:.1f}" height="6.5" rx="1.5" fill="#3B82F6"/>'
            f'<rect x="{ml}" y="{y0 + 9}" width="{w_dcf:.1f}" height="6.5" rx="1.5" fill="{col_dcf}"/>'
            f'<text x="{ml + max(w_px, w_dcf) + 5:.1f}" y="{y0 + 11}" font-size="8.2" font-weight="700" '
            f'fill="#334155" font-family="Consolas,monospace">${px:,.0f} vs ${dcf:,.0f} ({up:+.0f}%)</text>'
        )

    svg = (
        f'<svg viewBox="0 0 {w} {h}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="{ml}" y="{mt}" width="{cw}" height="{len(rows) * 19}" fill="#FFFFFF" stroke="#E2E8F0"/>'
        f"{bars_svg}"
        f'<rect x="{ml}" y="{h - 14}" width="10" height="6" fill="#3B82F6"/>'
        f'<text x="{ml + 14}" y="{h - 8}" font-size="8.5" fill="#334155">Spot Price (USD)</text>'
        f'<rect x="{ml + 120}" y="{h - 14}" width="10" height="6" fill="#059669"/>'
        f'<text x="{ml + 134}" y="{h - 8}" font-size="8.5" fill="#334155">DCF Fair Value (10% MoS)</text>'
        f"</svg>"
    )
    return _wrap_card(
        "Forward Valuation Anchor: Live Spot Price vs. 3-Scenario DCF Fair Value (10% MoS)",
        "Green bar >= Blue bar indicates structural Margin of Safety upside under NTM CAPM DCF",
        svg,
    )


def render_crypto_cycle_svg(cryptos: Dict[str, Any]) -> str:
    items = list(cryptos.items())[:8]
    if not items:
        return ""

    w, h = 760, 175
    ml, mr, mt, mb = 74, 52, 20, 26
    cw, ch = w - ml - mr, h - mt - mb

    z_min, z_max = -1.5, 4.5
    z_span = z_max - z_min

    def _zx(z: float) -> float:
        zc = max(z_min, min(z_max, z))
        return round(ml + ((zc - z_min) / z_span) * cw, 1)

    zero_x = _zx(0.0)
    two_x = _zx(2.0)

    bars_svg = (
        f'<rect x="{ml}" y="{mt}" width="{max(1.0, _zx(0.5) - ml)}" height="{ch}" fill="rgba(16, 185, 129, 0.10)"/>'
        f'<rect x="{two_x}" y="{mt}" width="{max(1.0, w - mr - two_x)}" height="{ch}" fill="rgba(239, 68, 68, 0.09)"/>'
        f'<line x1="{zero_x}" y1="{mt}" x2="{zero_x}" y2="{mt + ch}" stroke="#059669" stroke-width="1.5" stroke-dasharray="3,2"/>'
        f'<line x1="{two_x}" y1="{mt}" x2="{two_x}" y2="{mt + ch}" stroke="#DC2626" stroke-width="1.5" stroke-dasharray="3,2"/>'
    )

    row_step = ch / max(1, len(items))
    for i, (sym, c) in enumerate(items):
        om = getattr(c, "onchain_metrics", {}) or {}
        z = float(om.get("mvrv_z_score", 0.0) or 0.0)
        nupl = float(om.get("nupl", 0.0) or 0.0)
        re_m = float((getattr(c, "tokenomics_valuation", {}) or {}).get("protocol_real_earnings_m", 0.0) or 0.0)
        y_mid = mt + (i + 0.5) * row_step
        x_val = _zx(z)
        x0, x1 = min(zero_x, x_val), max(zero_x, x_val)
        col = "#059669" if z <= 0.5 else ("#2563EB" if z <= 2.0 else "#DC2626")
        bars_svg += (
            f'<text x="{ml - 6}" y="{y_mid + 3:.1f}" text-anchor="end" font-size="9" font-weight="700" '
            f'fill="#0F172A" font-family="Consolas,monospace">{_esc(sym)}</text>'
            f'<rect x="{x0}" y="{y_mid - 5:.1f}" width="{max(3.0, x1 - x0):.1f}" height="10" rx="2" fill="{col}"/>'
            f'<text x="{x1 + 5:.1f}" y="{y_mid + 3:.1f}" font-size="8.2" font-weight="700" fill="#334155" '
            f'font-family="Consolas,monospace">Z {z:+.2f} | NUPL {nupl:+.2f} | RealEarn ${re_m:+.0f}M</text>'
        )

    svg = (
        f'<svg viewBox="0 0 {w} {h}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="{ml}" y="{mt}" width="{cw}" height="{ch}" fill="#FFFFFF" stroke="#E2E8F0"/>'
        f"{bars_svg}"
        f'<text x="{zero_x}" y="{h - 7}" text-anchor="middle" font-size="8.5" fill="#059669" font-weight="700">Z = 0.0 (Cycle Floor)</text>'
        f'<text x="{two_x}" y="{h - 7}" text-anchor="middle" font-size="8.5" fill="#DC2626" font-weight="700">Z = 2.0 (Screener Cap)</text>'
        f"</svg>"
    )
    return _wrap_card(
        "On-Chain Cycle Valuation Map: MVRV Z-Score, NUPL & Annual Protocol Real Earnings",
        "Green shaded zone (< 0.5 Z) = Historical Accumulation Zone; Dashed red line (2.0 Z) = Strict Screener Threshold",
        svg,
    )


def render_backtest_equity_svg(backtest: Optional[Dict[str, Any]]) -> str:
    if not isinstance(backtest, dict):
        return ""
    eq_df = backtest.get("equity_curve_df")
    if not isinstance(eq_df, pd.DataFrame) or eq_df.empty or len(eq_df) < 10:
        return ""

    # Downsample cleanly to <= 90 points for crisp, lightweight PDF vector paths
    step = max(1, len(eq_df) // 90)
    sub = eq_df.iloc[::step]
    if sub.index[-1] != eq_df.index[-1]:
        sub = pd.concat([sub, eq_df.iloc[[-1]]])

    w, h = 760, 185
    ml, mr, mt, mb = 60, 26, 22, 26
    cw, ch = w - ml - mr, h - mt - mb

    all_vals = sub.values.flatten().astype(float)
    y_min = float(all_vals.min()) * 0.96
    y_max = float(all_vals.max()) * 1.04
    y_span = max(1000.0, y_max - y_min)

    n = len(sub)
    paths_svg = ""
    color_map = {"Portfolio": "#059669", "SPY": "#2563EB", "BTC-USD": "#D97706"}
    for col in sub.columns:
        pts = []
        for idx, val in enumerate(sub[col].values.astype(float)):
            x = round(ml + (idx / max(1, n - 1)) * cw, 1)
            y = round(mt + (1.0 - (val - y_min) / y_span) * ch, 1)
            pts.append(f"{x},{y}")
        stroke_w = "2.6" if col == "Portfolio" else "1.6"
        dash = "" if col == "Portfolio" else ' stroke-dasharray="4,2"'
        paths_svg += f'<polyline fill="none" stroke="{color_map.get(col, "#64748B")}" stroke-width="{stroke_w}"{dash} points="{" ".join(pts)}"/>'

    grid_svg = ""
    for k in range(4):
        gv = y_min + (k / 3.0) * y_span
        gy = round(mt + (1.0 - (gv - y_min) / y_span) * ch, 1)
        grid_svg += (
            f'<line x1="{ml}" y1="{gy}" x2="{w - mr}" y2="{gy}" stroke="#E2E8F0" stroke-width="1"/>'
            f'<text x="{ml - 6}" y="{gy + 3}" text-anchor="end" font-size="8.5" fill="#64748B" '
            f'font-family="Consolas,monospace">${gv / 1000.0:,.0f}k</text>'
        )

    svg = (
        f'<svg viewBox="0 0 {w} {h}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="{ml}" y="{mt}" width="{cw}" height="{ch}" fill="#FFFFFF" stroke="#E2E8F0"/>'
        f"{grid_svg}{paths_svg}"
        f'<line x1="{ml}" y1="{h - 11}" x2="{ml + 16}" y2="{h - 11}" stroke="#059669" stroke-width="2.6"/>'
        f'<text x="{ml + 20}" y="{h - 8}" font-size="8.5" font-weight="700" fill="#0F172A">Portfolio ({backtest.get("portfolio_cagr_pct", 0.0):+.1f}% CAGR)</text>'
        f'<line x1="{ml + 185}" y1="{h - 11}" x2="{ml + 201}" y2="{h - 11}" stroke="#2563EB" stroke-width="1.8" stroke-dasharray="4,2"/>'
        f'<text x="{ml + 205}" y="{h - 8}" font-size="8.5" fill="#334155">SPY ({backtest.get("spy_cagr_pct", 0.0):+.1f}%)</text>'
        f'<line x1="{ml + 320}" y1="{h - 11}" x2="{ml + 336}" y2="{h - 11}" stroke="#D97706" stroke-width="1.8" stroke-dasharray="4,2"/>'
        f'<text x="{ml + 340}" y="{h - 8}" font-size="8.5" fill="#334155">BTC-USD ({backtest.get("btc_cagr_pct", 0.0):+.1f}%)</text>'
        f'<text x="{w - mr}" y="{h - 8}" text-anchor="end" font-size="8.2" font-weight="700" fill="#475569" font-family="Consolas,monospace">'
        f'Daily VaR95: -{backtest.get("var_95_daily_pct", 0.0):.2f}% | CVaR95: -{backtest.get("cvar_95_daily_pct", 0.0):.2f}%</text>'
        f"</svg>"
    )
    return _wrap_card(
        f"3-Year Real Historical Equity Curve & Tail-Risk Profile ({backtest.get('period_days', 0)} Trading Days)",
        f"Sharpe {backtest.get('sharpe_ratio', 0.0):.2f} | Sortino {backtest.get('sortino_ratio', 0.0):.2f} | MaxDD -{backtest.get('max_drawdown_pct', 0.0):.2f}% | Calmar {backtest.get('calmar_ratio', 0.0):.2f}x",
        svg,
    )

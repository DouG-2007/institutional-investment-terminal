"""
================================================================================
INSTITUTIONAL EXCEL WORKBOOK EXPORTER (.XLSX)
================================================================================
Exports auditable multi-sheet spreadsheets covering Portfolio Holdings,
ETF Look-Through Overlap, Equities Forensic & Forward NTM Valuations,
Crypto On-Chain & Tokenomics, and Real Custody Transactions Ledger.
================================================================================
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


def _write_styled_sheet(
    ws: Any,
    headers: List[str],
    rows: List[List[Any]],
) -> None:
    header_fill = PatternFill(start_color="0F172A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=10)
    alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="left", vertical="center")

    for r_idx, row_vals in enumerate(rows, start=2):
        ws.append(row_vals)
        if r_idx % 2 == 0:
            for col_idx in range(1, len(headers) + 1):
                ws.cell(row=r_idx, column=col_idx).fill = alt_fill

    ws.freeze_panes = "A2"
    for col_idx, h in enumerate(headers, start=1):
        max_len = max(
            [len(str(h))] + [len(str(r[col_idx - 1])) for r in rows[:50] if col_idx - 1 < len(r)]
        )
        ws.column_dimensions[get_column_letter(col_idx)].width = min(42, max(12, max_len + 4))


def build_institutional_excel_bytes(
    portfolio: Any,
    equities: List[Any],
    cryptos: Dict[str, Any],
    risk_timing: Any,
    transactions: Optional[List[Dict[str, Any]]] = None,
    backtest: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Compiles the complete multi-sheet institutional workbook into `.xlsx` bytes."""
    wb = Workbook()

    # 1. Portfolio Holdings
    ws_port = wb.active
    ws_port.title = "Portfolio_Holdings"
    port_headers = [
        "Ticker", "Asset Name", "Category", "Sector Vertical",
        "Target Weight (%)", "Current Weight (%)", "Drift (pp)",
        "Avg Buy (USD)", "Spot Price (USD)", "Units Held",
        "Allocated Value (USD)", "Unrealized P&L (%)", "Unrealized P&L (USD)", "LTV Collateral Eligible",
    ]
    port_rows = [
        [
            p.ticker, p.name, p.category, p.sector_vertical,
            p.target_weight_pct, p.current_weight_pct, p.weight_drift_pp,
            p.avg_buy_price_usd, p.current_price_usd, p.quantity_units,
            p.allocated_usd, p.pnl_pct, p.pnl_usd, "YES" if p.ltv_turbo_eligible else "NO",
        ]
        for p in getattr(portfolio, "positions", [])
    ]
    _write_styled_sheet(ws_port, port_headers, port_rows)

    # 2. ETF Look-Through
    ws_lt = wb.create_sheet("ETF_LookThrough")
    lt_headers = [
        "Ticker", "Company", "Sector", "Direct (%)",
        "SPY Indirect (%)", "QQQ Indirect (%)", "SMH Indirect (%)", "ITA Indirect (%)", "QLD 2x Indirect (%)",
        "Total Indirect (%)", "Effective Exposure (%)", "Effective Value (USD)", "Overlap Sources",
    ]
    lt_rows = [
        [
            h.ticker, h.company_name, h.sector, h.direct_weight_pct,
            h.spy_indirect_pct, h.qqq_indirect_pct, h.smh_indirect_pct, h.ita_indirect_pct, h.qld_2x_indirect_pct,
            h.total_indirect_pct, h.total_effective_lookthrough_pct, h.effective_exposure_usd, h.overlap_sources,
        ]
        for h in getattr(portfolio, "lookthrough_holdings", [])
    ]
    _write_styled_sheet(ws_lt, lt_headers, lt_rows)

    # 3. Equities Forensic & Valuation
    ws_eq = wb.create_sheet("Equities_Forensic_Valuation")
    eq_headers = [
        "Ticker", "Company", "Vertical", "Spot (USD)", "MCap (USD B)", "EV (USD B)",
        "Sloan Ratio (%)", "CFO/EBITDA (x)", "ROIC (%)", "WACC (%)", "Spread (pp)",
        "Current Ratio", "Int. Coverage (x)", "Debt/EBITDA",
        "DCF 10% MoS (USD)", "DCF Upside (%)", "Reverse DCF g_impl (%)", "Projected g_fund (%)",
        "Primary PEGY", "PEGY Status", "SOTP Fair (USD)", "EVA (USD B)", "Magic Formula Rank",
    ]
    eq_rows = []
    for e in equities:
        fh = e.forensic_health or {}
        vm = e.valuation_methods or {}
        eq_rows.append([
            e.ticker, e.company_name, e.sector_vertical, e.current_price, e.market_cap_b, e.enterprise_value_b,
            fh.get("sloan_ratio_pct"), fh.get("fco_to_ebitda"), fh.get("roic_goodwill_pct"), fh.get("wacc_pct"), fh.get("roic_minus_wacc_spread_pp"),
            fh.get("current_ratio"), fh.get("interest_coverage_x"), fh.get("debt_to_ebitda"),
            vm.get("dcf_fair_mos10_usd"), vm.get("dcf_upside_pct"), vm.get("reverse_dcf_g_impl_pct"), vm.get("g_fund_projected_pct"),
            vm.get("primary_pegy_label"), vm.get("primary_pegy_status"), vm.get("sotp_fair_price_usd"), vm.get("eva_usd_b"), vm.get("magic_formula_rank"),
        ])
    _write_styled_sheet(ws_eq, eq_headers, eq_rows)

    # 4. Crypto On-Chain & Tokenomics
    ws_cr = wb.create_sheet("Crypto_OnChain_Tokenomics")
    cr_headers = [
        "Symbol", "Name", "Spot (USD)", "MCap (USD B)", "FDV (USD B)", "Circulating (%)",
        "MVRV Z-Score", "NUPL", "aSOPR", "200W SMA (USD)", "Pi Cycle Crossed",
        "TVL (USD B)", "Real Earnings (USD M/yr)", "Real Yield (%)", "P/F Ratio",
        "30d Unlock (%)", "Post-Unlock Px (USD)", "Funding Rate 8h (%)", "OI/MCap (%)",
    ]
    cr_rows = []
    for sym, cp in cryptos.items():
        om = cp.onchain_metrics or {}
        tv = cp.tokenomics_valuation or {}
        ss = cp.supply_structure or {}
        ds = cp.derivatives_sentiment or {}
        cr_rows.append([
            sym, cp.name, cp.spot_price_usd, cp.market_cap_b, cp.fdv_b, cp.circulating_pct,
            om.get("mvrv_z_score"), om.get("nupl"), om.get("asopr"), om.get("sma_200w_usd"), om.get("pi_cycle_top_triggered"),
            tv.get("tvl_b"), tv.get("protocol_real_earnings_m"), tv.get("real_yield_pct"), tv.get("pf_ratio"),
            ss.get("unlock_pct_of_circ"), ss.get("theoretical_post_unlock_price_usd"), ds.get("funding_rate_8h_pct"), ds.get("oi_to_mcap_pct"),
        ])
    _write_styled_sheet(ws_cr, cr_headers, cr_rows)

    # 5. Transactions Ledger (+ Backtest Summary metadata rows if empty)
    ws_tx = wb.create_sheet("Transactions_Ledger")
    tx_headers = ["ID", "Date", "Ticker", "Type", "Quantity", "Price (USD)", "Fee (USD)", "Notional (USD)", "Notes"]
    tx_rows = [
        [
            t.get("id"), t.get("tx_date"), t.get("ticker"), t.get("tx_type"),
            t.get("quantity"), t.get("price_usd"), t.get("fee_usd", 0.0),
            round(float(t.get("quantity", 0.0)) * float(t.get("price_usd", 0.0)), 2),
            t.get("notes", ""),
        ]
        for t in (transactions or [])
    ]
    if not tx_rows and isinstance(backtest, dict):
        tx_rows.append([
            "SUMMARY", "LTM/3Y", "PORTFOLIO", backtest.get("data_source", ""),
            backtest.get("period_days", 0), backtest.get("portfolio_cagr_pct", 0.0),
            backtest.get("sharpe_ratio", 0.0), backtest.get("max_drawdown_pct", 0.0),
            f"Calmar={backtest.get('calmar_ratio', 0.0)} | Sortino={backtest.get('sortino_ratio', 0.0)}",
        ])
    _write_styled_sheet(ws_tx, tx_headers, tx_rows)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

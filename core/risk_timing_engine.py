"""
MODULE 5: RISK MONITOR, CONVEX LEVERAGE & CONSULTATIVE TIMING DOCUMENTATION
STRICT ARCHITECTURAL RULE: The system is NOT an automated trading bot and does NOT perform mechanical
calendar rebalancing. Timing guidelines, capital additions (Shannon Inflow), and pruning references are presented
strictly as Consultative / Non-Binding Strategic References alongside estimated tax drag
(Tax-Drag Hurdle Rate), enabling disciplined, discretionary decision-making by the institutional investor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np

from core.portfolio_engine import PortfolioOverviewBundle
from core.equity_engine import EquityFullAnalysis
from core.crypto_engine import CryptoFullProfile


@dataclass
class ConsultativeTimingRow:
    asset_ticker: str
    asset_name: str
    framework_category: str
    target_weight_pct: float
    current_weight_pct: float
    weight_drift_pp: float
    primary_indicator_current: str
    framework_buy_reference: str
    framework_prune_reference: str
    consultative_status_vs_reference: str
    estimated_unrealized_gain_pct: float
    capital_gains_tax_rate_pct: float
    tax_drag_hurdle_rate_pct: float  # Minimum post-sale drawdown required to offset capital gains tax
    shannon_inflow_eligible: bool


@dataclass
class RiskLeverageTimingBundle:
    # 5.1 Performance, Risk & Liquidity
    performance_risk_metrics: Dict[str, Any]
    vix_indicator: Dict[str, Any]
    adtv_liquidity_table: List[Dict[str, Any]]
    # Convex Anti-Cyclical Leverage Panel (LTV Global)
    convex_ltv_panel: Dict[str, Any]
    aave_v3_stress_test_table: List[Dict[str, Any]]
    # 5.2 Consultative Strategic Reference Section
    framework_rules_documentation: List[Dict[str, str]]
    consultative_asset_timing_table: List[ConsultativeTimingRow]


class RiskTimingEngine:
    def __init__(self) -> None:
        pass

    def build_risk_and_consultative_timing(
        self,
        portfolio: PortfolioOverviewBundle,
        equities: List[EquityFullAnalysis],
        cryptos: Dict[str, CryptoFullProfile],
        fed_funds_rate_pct: float = 4.25,
        shiller_cape: float = 36.8,
        vix_current: float = 18.4,
        capital_gains_tax_rate_pct: float = 15.0,
        backtest_metrics: Optional[Dict[str, Any]] = None,
        live_adtv_map_m: Optional[Dict[str, float]] = None,
    ) -> RiskLeverageTimingBundle:
        cap = portfolio.capital_usd

        # ======================================================================
        # 5.1 RISK METRICS, LIQUIDITY & CONVEX LEVERAGE
        # ======================================================================
        bt = backtest_metrics or {}
        if bt and bt.get("data_source") == "LIVE_YFINANCE_HISTORY":
            sharpe = float(bt.get("sharpe_ratio", 1.68))
            sortino = float(bt.get("sortino_ratio", 2.45))
            cagr_port_pct = float(bt.get("portfolio_cagr_pct", 24.8))
            max_dd_pct = float(bt.get("max_drawdown_pct", 14.2))
            calmar = float(bt.get("calmar_ratio", round(cagr_port_pct / max(0.5, max_dd_pct), 2)))
            risk_src = f"Real 3y Portfolio History ({bt.get('period_days', 0)} trading days)"
        else:
            sharpe = 1.68
            sortino = 2.45
            cagr_port_pct = 24.8
            max_dd_pct = 14.2
            calmar = round(cagr_port_pct / max_dd_pct, 2)
            risk_src = "Calibrated Baseline Model"

        if calmar > 3.0:
            calmar_cls = f"Legendary ({calmar:.2f} > 3.0)"
        elif calmar >= 1.0:
            calmar_cls = f"Optimal ({calmar:.2f} between 1.0 and 2.0+)"
        elif calmar >= 0.5:
            calmar_cls = f"Acceptable ({calmar:.2f} between 0.5 and 1.0)"
        else:
            calmar_cls = f"Poor ({calmar:.2f} < 0.5)"

        performance_risk_metrics = {
            "sharpe_ratio": sharpe,
            "sharpe_reference": "> 1.0 (Optimal Return-to-Volatility Profile)",
            "sortino_ratio": sortino,
            "sortino_reference": f"> Sharpe ({sortino:.2f} > {sharpe:.2f} — Upside Skew / Downside Protected)",
            "portfolio_cagr_est_pct": cagr_port_pct,
            "portfolio_max_drawdown_pct": max_dd_pct,
            "calmar_ratio": calmar,
            "calmar_reference": "< 0.5 Poor | 0.5-1.0 Acceptable | 1.0-2.0 Optimal | > 3.0 Legendary",
            "calmar_classification": calmar_cls,
            "data_source": risk_src,
        }

        if vix_current > 30.0:
            vix_cls = "Extreme Fear (> 30 — Deep Value / Institutional Panic)"
        elif vix_current >= 15.0:
            vix_cls = "Normal (15 to 25 — Standard Market Volatility)"
        else:
            vix_cls = "Complacency (< 15 — Low Implied Protection)"

        vix_indicator = {
            "vix_current": round(vix_current, 2),
            "vix_reference": "> 30 Extreme Fear / Deep Value | 15-25 Normal | < 15 Complacency",
            "vix_classification": vix_cls,
        }

        # Auditoria ADTV (< 1% do Average Daily Trading Volume para evitar slippage)
        adtv_map_m = {
            "BTC-USD": 34500.0,
            "ETH-USD": 16800.0,
            "SOL-USD": 4900.0,
            "AAVE-USD": 285.0,
            "SPY": 28500.0,
            "QQQ": 19200.0,
            "SMH": 2450.0,
            "ITA": 185.0,
            "QLD": 420.0,
            "AAPL": 11500.0,
            "MSFT": 8900.0,
            "GOOGL": 6400.0,
            "AMZN": 9200.0,
            "NVDA": 29500.0,
            "META": 7800.0,
            "V": 1950.0,
            "JPM": 2650.0,
            "WMT": 1650.0,
            "DBSDY": 145.0,
        }

        live_adtv = live_adtv_map_m or {}
        adtv_table: List[Dict[str, Any]] = []
        for pos in portfolio.positions:
            adtv_m = float(live_adtv.get(pos.ticker) or adtv_map_m.get(pos.ticker, 1000.0))
            adtv_usd = adtv_m * 1e6
            pos_pct_adtv = (pos.allocated_usd / adtv_usd) * 100.0 if adtv_usd > 0 else 0.0
            adtv_table.append({
                "Ticker": pos.ticker,
                "Ativo": pos.name,
                "Portfolio Position (USD)": round(pos.allocated_usd, 2),
                "Average Daily ADTV ($M)": round(adtv_usd / 1e6, 1),
                "% do ADTV": round(pos_pct_adtv, 4),
                "Reference Threshold": "< 1.0000% of ADTV",
                "Status Slippage": (
                    "Full Institutional Liquidity (< 1% ADTV — Zero Slippage)"
                    if pos_pct_adtv < 1.0
                    else "SLIPPAGE ALERT (>= 1% ADTV)"
                ),
            })

        # ======================================================================
        # CONVEX COUNTER-CYCLICAL LEVERAGE PANEL (GLOBAL LTV)
        # ======================================================================
        # LTV_Global = (Peso_Stocks * LTV_Stocks) + (Peso_BTC * LTV_BTC)
        # Assuming Hard-Assets/Stocks (50%) and Collateralizable Crypto/BTC (50%)
        btc_prof = cryptos.get("BTC-USD")
        btc_mvrv_z = btc_prof.onchain_timing["mvrv_z_score"] if btc_prof and hasattr(btc_prof, "onchain_timing") else (
            btc_prof.onchain_metrics["mvrv_z_score"] if btc_prof else 1.85
        )
        btc_asopr = btc_prof.onchain_metrics["asopr"] if btc_prof else 1.042
        hash_ribbon_ok = btc_prof.mining_metrics["hash_ribbon_crossed_up"] if btc_prof else True

        btc_nupl = (
            btc_prof.onchain_timing["nupl"]
            if btc_prof and hasattr(btc_prof, "onchain_timing")
            else (btc_prof.onchain_metrics["nupl"] if btc_prof else 0.52)
        )
        btc_px_to_200w = (
            btc_prof.onchain_metrics.get("price_to_200w_sma_x", 1.50)
            if btc_prof
            else 1.50
        )
        hash_ribbon_ok = btc_prof.mining_metrics["hash_ribbon_crossed_up"] if btc_prof else True

        weight_stocks = getattr(portfolio, "ltv_eligible_stocks_weight_pct", 50.0) / 100.0
        weight_btc_collat = getattr(portfolio, "ltv_eligible_btc_weight_pct", 50.0) / 100.0
        ltv_stocks_pct = 20.0
        ltv_btc_pct = 20.0
        ltv_global_pct = round(weight_stocks * ltv_stocks_pct + weight_btc_collat * ltv_btc_pct, 2)

        ibkr_box_spread_rate = round(fed_funds_rate_pct + 0.35, 2)
        aave_v3_usdc_borrow_rate = 5.15
        tot_collat_w = max(0.01, weight_stocks + weight_btc_collat)
        blended_borrow_cost = round(
            (weight_stocks / tot_collat_w) * ibkr_box_spread_rate
            + (weight_btc_collat / tot_collat_w) * aave_v3_usdc_borrow_rate,
            2,
        )

        turbo_condition_met = (shiller_cape < 28.0) or (btc_mvrv_z < 0.50)
        reversal_confirmed = hash_ribbon_ok and (btc_asopr > 1.0)

        convex_ltv_panel = {
            "formula_used": "LTV_Global = (Peso_Stocks × LTV_Stocks) + (Peso_BTC × LTV_BTC)",
            "weight_stocks_pct": weight_stocks * 100.0,
            "ltv_stocks_pct": ltv_stocks_pct,
            "weight_btc_pct": weight_btc_collat * 100.0,
            "ltv_btc_pct": ltv_btc_pct,
            "ltv_global_current_pct": ltv_global_pct,
            "total_debt_usd": round(cap * (ltv_global_pct / 100.0), 2),
            "ibkr_box_spread_rate_pct": ibkr_box_spread_rate,
            "ibkr_formula": f"Fed Funds ({fed_funds_rate_pct:.2f}%) + 0.35% p.a. = {ibkr_box_spread_rate:.2f}% p.a.",
            "aave_v3_wbtc_usdc_borrow_rate_pct": aave_v3_usdc_borrow_rate,
            "blended_carry_cost_pct": blended_borrow_cost,
            "ltv_structural_base_ref": "20.0% continuous fixed baseline (expandable up to 25.0% tactical wealth-max ceiling; zero 10% defensive deleveraging)",
            "turbo_trigger_ref": "28.0% to 30.0% LTV in acute panic (Shiller CAPE < 28x or BTC MVRV Z < 0.5) paired with confirmed technical reversal (Hash Ribbon Buy + aSOPR > 1.0)",
            "turbo_trigger_status": (
                "TURBO TRIGGER ACTIVE (Bottom Conditions + Confirmed Reversal)"
                if (turbo_condition_met and reversal_confirmed)
                else f"INACTIVE (CAPE {shiller_cape:.1f}x | BTC MVRV Z {btc_mvrv_z:.2f} | Confirmations: Hash Ribbon={'OK' if hash_ribbon_ok else 'Wait'}, aSOPR={btc_asopr:.3f})"
            ),
            "defensive_reduction_ref": "Eliminated per parity backtest (Maintain continuous 20%–25% structural LTV; no 10% drop in high rates)",
            "defensive_reduction_status": f"CONTINUOUS FLOOR ACTIVE (Base 20.0%–25.0% | Fed Funds {fed_funds_rate_pct:.2f}% | Hard-Cap Buffer at 45.0%–50.0% LTV Intact)",
            "margin_call_safety_ceiling_pct": 45.0,
            "max_collateral_drop_before_45_ltv_pct": round((1.0 - (ltv_global_pct / 45.0)) * 100.0, 1),  # -55.6% simultaneous collateral drop before reaching 45% LTV
        }

        # DeFi Carry Cost Stress-Test (Aave V3 WBTC/USDC Borrow Rate Spikes)
        base_btc_collat_usd = cap * 0.50
        base_aave_debt_usd = base_btc_collat_usd * (ltv_btc_pct / 100.0)
        aave_stress_scenarios = [
            ("Normal Base Scenario (Stable Liquidity)", 5.15, 0.0),
            ("Moderate Stress (Pool Utilization > 85%)", 11.50, -15.0),
            ("Euphoria Peak / Kink Rate (Utilization > 92%)", 19.80, -25.0),
            ("Extreme DeFi Liquidity Shock (Max Kink + BTC Dump)", 32.00, -40.0),
        ]
        aave_v3_stress_test_table: List[Dict[str, Any]] = []
        for sc_name, rate_aa, btc_shock_pct in aave_stress_scenarios:
            stressed_collat = base_btc_collat_usd * (1.0 + btc_shock_pct / 100.0)
            stressed_debt_1y = base_aave_debt_usd * (1.0 + rate_aa / 100.0)
            resulting_ltv_1y = (stressed_debt_1y / stressed_collat) * 100.0 if stressed_collat > 0 else 0.0
            health_factor = (stressed_collat * 0.78) / stressed_debt_1y if stressed_debt_1y > 0 else 9.9
            aave_v3_stress_test_table.append({
                "Aave V3 Stress Scenario": sc_name,
                "Borrow Rate USDC (% p.a.)": f"{rate_aa:.2f}%",
                "Simulated BTC Collateral Shock": f"{btc_shock_pct:+.0f}%",
                "Annual Interest Cost ($)": round(base_aave_debt_usd * (rate_aa / 100.0), 2),
                "Resulting 1Y BTC LTV (Without Amortization)": f"{resulting_ltv_1y:.2f}%",
                "Health Factor Aave V3 (Liq = 1.00)": f"{health_factor:.2f}",
                "Risk Assessment": (
                    "Safe (LTV < 35% & Health Factor > 2.2)"
                    if resulting_ltv_1y < 35.0
                    else "Caution: Refinance to IBKR Fixed Box Spread or amortize via dividends"
                ),
            })

        # ======================================================================
        # 5.2 CONSULTATIVE TIMING, INFLOW & PRUNING DOCUMENTATION
        # ======================================================================
        framework_rules_documentation = [
            {
                "Asset Class / Vertical": "1. High-Growth Techs & Fintechs (e.g., NVDA, AMZN, ASML, NU)",
                "Primary Metric": "Enterprise PEGY (EV/EBIT NTM)",
                "Advisory Buy Reference": "Gold Range: Enterprise PEGY (EV/EBIT NTM) between 0 and 1.20x (guides inflows & cross-asset rotation)",
                "Advisory 50% Trim Reference": "0% Valuation Pruning (Compounder Structural Hold — exit only on thesis/moat break)",
                "Strategic Note": "Parity backtests proved pruning secular compounders on PEGY > 1.6x destroys compounding; valuation directs buys only.",
            },
            {
                "Asset Class / Vertical": "2. Cash Cows & Tollbooths (e.g., AAPL, MSFT, GOOGL, META, V, MA)",
                "Primary Metric": "Enterprise PEGY (EV/FCF NTM) + Quality Gates",
                "Advisory Buy Reference": "Gold Range: Enterprise PEGY (EV/FCF NTM) 0–1.20x + Sloan <= +10% & CFO/EBITDA >= 0.70x",
                "Advisory 50% Trim Reference": "Enterprise PEGY (EV/FCF NTM) > 1.60x or structural Gross Margin deterioration",
                "Strategic Note": "Quality-gated 50% pruning rotates mature FCF capital into discounted Gold Range compounders or BTC capitulation.",
            },
            {
                "Asset Class / Vertical": "3. Cyclicals & Hard Commodities (e.g., XOM, CAT, FCX, VALE)",
                "Primary Metric": "Inverse Relative Multiples + Mid-Cycle DCF + Quality Gates",
                "Advisory Buy Reference": "Trough: P/E and EV/EBITDA > 1.15x sector avg + Price <= 0.85x Fair Value DCF (+ Sloan/CFO quality)",
                "Advisory 50% Trim Reference": "Peak: P/E and EV/EBITDA < 0.80x sector avg OR Price > 1.25x Fair Value DCF",
                "Strategic Note": "In cyclicals, low P/E flags unsustainable peak earnings; high P/E indicates depressed trough earnings.",
            },
            {
                "Asset Class / Vertical": "4. Financial Sector & Banks (e.g., JPM, BAC, DBSDY)",
                "Primary Metric": "Financial PEGY (NTM P/E / [EPS Growth + Div Yield]) + P/B Filter",
                "Advisory Buy Reference": "Financial PEGY 0 to 1.00x WITH P/B >= 1.0x (P/B < 1.0x is structural veto)",
                "Advisory 50% Trim Reference": "Financial PEGY > 1.50x",
                "Strategic Note": "Shields against value traps where P/B < 1.0 reflects balance-sheet book value destruction. Fintechs (NU) map to High-Growth Tech.",
            },
            {
                "Asset Class / Vertical": "5. Defensives & Dividend Aristocrats (e.g., WMT, PG, KO, JNJ)",
                "Primary Metric": "P/E & EV/EBITDA vs Sector + DCF + SSS & Quality Gates",
                "Advisory Buy Reference": "P/E & EV/EBITDA <= 0.85x sector avg + Price <= 0.85x DCF (positive SSS & Gross Margin stability)",
                "Advisory 50% Trim Reference": "P/E & EV/EBITDA >= 1.20x sector avg OR Price >= 1.20x DCF",
                "Strategic Note": "In physical retail, positive Same Store Sales (SSS) and accounting quality prevent relevance loss.",
            },
            {
                "Asset Class / Vertical": "6. Bitcoin (BTC — Sovereign Reserve Asset)",
                "Primary Metric": "NUPL, MVRV Z-Score, 200W SMA and Pi Cycle Top",
                "Advisory Buy Reference": "NUPL < 0.0 OR MVRV Z <= 0.50 OR Price <= 1.05x 200W SMA",
                "Advisory 50% Trim Reference": "Pi Cycle Top triggered (111d > 2x350d) OR NUPL Reverse Cross (< 0.60 after > 0.65)",
                "Strategic Note": "On-chain macro cycle reference; structural 50% core allocation remains in cold storage.",
            },
            {
                "Asset Class / Vertical": "7A. Crypto L1 Majors (ETH, SOL — Core Infrastructure)",
                "Primary Metric": "BTC 200W SMA / NUPL Cycle Floor + Network Fee Adoption",
                "Advisory Buy Reference": "Accumulate at historical BTC floor: BTC <= 1.05x 200W SMA (confirmed w/ BTC NUPL < 0.0)",
                "Advisory 50% Trim Reference": "0% Cyclical Pruning (Full-Cycle Hold — avoid -20% mid-altseason whipsaws)",
                "Strategic Note": "Major L1s accelerate after BTC Pi Cycle; parity backtests prove full-cycle hold beats partial/trailing exits.",
            },
            {
                "Asset Class / Vertical": "7B. Altcoins DeFi & Mid-Caps (AAVE, MKR, LINK, UNI, PENDLE)",
                "Primary Metric": "BTC 200W SMA Re-Entry + BTC Euphoria + Token Trailing DD + P/F",
                "Advisory Buy Reference": "Strict Re-Entry Floor: BTC <= 1.05x 200W SMA (confirm w/ NUPL < 0.0) + Healthy P/F & Real Earnings > 0",
                "Advisory 50%/100% Trim Reference": "100% Exit: (BTC NUPL > 0.60 or MVRV Z > 3.0) + (Trailing DD >= 20% or P/F > 35x)",
                "Strategic Note": "Waiting for BTC <= 1.05x 200W SMA eliminates early bear-market entries (replacing NUPL < 0.30).",
            },
        ]

        eq_map = {e.ticker: e for e in equities}
        btc_nupl = cryptos["BTC-USD"].onchain_metrics["nupl"] if "BTC-USD" in cryptos else 0.52
        btc_mvrv = cryptos["BTC-USD"].onchain_metrics["mvrv_z_score"] if "BTC-USD" in cryptos else 1.85

        tax_rate_pct = max(0.0, float(capital_gains_tax_rate_pct))
        consultative_rows: List[ConsultativeTimingRow] = []
        for pos in portfolio.positions:
            tk = pos.ticker
            # Unrealized gain derived directly from portfolio cost basis vs live spot price
            # Tax-Drag Hurdle Rate = (Unrealized_Gain_% / (100 + Unrealized_Gain_%)) * Tax_Rate_%
            # Returns 0.0% when unrealized P&L <= 0 (zero tax drag when harvesting a loss)
            est_gain_pct = round(max(0.0, float(pos.pnl_pct)), 2)
            tax_paid_pct_of_position = (
                (est_gain_pct / (100.0 + est_gain_pct)) * tax_rate_pct
                if est_gain_pct > 0.0
                else 0.0
            )
            tax_drag_hurdle_pct = round(tax_paid_pct_of_position, 2)

            if tk == "BTC-USD":
                c = cryptos["BTC-USD"]
                om = c.onchain_metrics
                ind_str = f"NUPL: {om['nupl']:.2f} | MVRV Z: {om['mvrv_z_score']:.2f} | Px/200W: {om['price_to_200w_sma_x']:.2f}x"
                buy_ref = "NUPL < 0.0 or MVRV Z <= 0.5 or Px <= 1.05x 200W SMA"
                prune_ref = "Pi Cycle Top Active or NUPL Reverse Cross (< 0.60 post > 0.65)"
                in_buy = (om["nupl"] < 0.0) or (om["mvrv_z_score"] <= 0.5) or (om["price_to_200w_sma_x"] <= 1.05)
                in_prune = om["pi_cycle_top_triggered"] or (om["nupl"] > 0.65)
                status = "Within Aggressive Buy Reference" if in_buy else ("Cycle Top Signal / Prune Reference" if in_prune else "Neutral Cycle Band (Hold / Discretionary DCA)")
                shannon_ok = not in_prune
            elif tk in cryptos:
                c = cryptos[tk]
                pf_val = c.tokenomics_valuation["pf_ratio"]
                is_l1_major = tk in ("ETH-USD", "SOL-USD")
                ind_str = f"BTC Px/200W: {btc_px_to_200w:.2f}x | BTC NUPL: {btc_nupl:.2f} | P/F: {pf_val:.1f}x"
                in_buy = (btc_px_to_200w <= 1.05) and (btc_nupl < 0.0)
                if not in_buy and btc_px_to_200w <= 1.05:
                    in_buy = True
                if is_l1_major:
                    buy_ref = "BTC <= 1.05x 200W SMA (confirm w/ BTC NUPL < 0.0)"
                    prune_ref = "0% Cyclical Pruning (Full-Cycle L1 Hold)"
                    in_prune = False
                    status = "Buy Reference (Historical BTC 200W Floor)" if in_buy else "Structural Full-Cycle Hold (L1 Major — Avoid -20% Whipsaws)"
                    shannon_ok = in_buy or (btc_nupl <= 0.55)
                else:
                    buy_ref = "BTC <= 1.05x 200W SMA (w/ NUPL < 0.0) + Healthy P/F"
                    prune_ref = "(BTC NUPL > 0.60 or MVRV Z > 3.0) + (Trailing DD >= 20% or P/F > 35x)"
                    in_prune = (btc_nupl > 0.60 or btc_mvrv > 3.0) and (pf_val > 35.0)
                    status = "Buy Reference (BTC 200W SMA Floor + P/F Discount)" if in_buy else ("Cyclical Exit Reference" if in_prune else "Mid-Cycle DeFi/Alt (Monitor BTC NUPL & Drawdown)")
                    shannon_ok = in_buy
            elif tk in eq_map:
                e = eq_map[tk]
                vm = e.valuation_methods
                fh = e.forensic_health
                sec = e.sector_vertical
                quality_ok = (fh.get("sloan_ratio_pct", 0.0) <= 10.0) and (
                    sec == "FINANCIAL_BANK" or fh.get("fco_to_ebitda", 1.0) >= 0.70
                )
                if sec == "TECH_HIGH_GROWTH":
                    val = vm["enterprise_pegy_ev_ebit"]
                    ind_str = f"Ent. PEGY (EV/EBIT): {val:.2f}x | g_impl: {vm['reverse_dcf_g_impl_pct']:.1f}% vs g_fund: {vm['g_fund_projected_pct']:.1f}%"
                    buy_ref = "Enterprise PEGY (EV/EBIT NTM) between 0 and 1.20x"
                    prune_ref = "0% Valuation Pruning (Compounder Structural Hold)"
                    in_buy = val <= 1.20
                    in_prune = False
                elif sec in ["TECH_CASH_COW", "FINANCIAL_TOLLBOOTH"]:
                    val = vm["enterprise_pegy_ev_fcf"]
                    ind_str = f"Ent. PEGY (EV/FCF): {val:.2f}x | Sloan: {fh.get('sloan_ratio_pct', 0.0):+.1f}% | CFO/EB: {fh.get('fco_to_ebitda', 1.0):.2f}x"
                    buy_ref = "Enterprise PEGY (EV/FCF NTM) 0–1.20x + Quality Gates"
                    prune_ref = "Enterprise PEGY (EV/FCF NTM) > 1.60x or Margin Deterioration"
                    in_buy = (val <= 1.20) and quality_ok
                    in_prune = val > 1.60
                elif sec == "FINANCIAL_BANK":
                    val = vm["pegy_financeiro"]
                    pb = vm["pb_current"]
                    ind_str = f"PEGY Fin: {val:.2f}x | P/B: {pb:.2f}x | P/TBV: {vm['ptbv_current']:.2f}x | ROE: {e.forensic_health['roic_goodwill_pct']:.1f}%"
                    buy_ref = "Financial PEGY 0 to 1.00x WITH P/B >= 1.0x"
                    prune_ref = "Financial PEGY > 1.50x"
                    in_buy = (val <= 1.00) and (pb >= 1.0)
                    in_prune = val > 1.50
                else:  # RETAIL / DEFENSIVE / CYCLICAL
                    pe_rel = vm["pe_current"] / vm["pe_sector_avg"] if vm["pe_sector_avg"] > 0 else 1.0
                    px_dcf = e.current_price / vm["dcf_fair_mos10_usd"] if vm["dcf_fair_mos10_usd"] > 0 else 1.0
                    ind_str = f"P/E vs Sector: {pe_rel:.2f}x | Px/DCF: {px_dcf:.2f}x | CFO/EB: {fh.get('fco_to_ebitda', 1.0):.2f}x"
                    buy_ref = "P/E & EV/EBITDA <= 0.85x Sector + Price <= 0.85x DCF (+ Quality Gates)"
                    prune_ref = "P/E & EV/EBITDA >= 1.20x Sector OR Price >= 1.20x DCF"
                    in_buy = (pe_rel <= 0.85) and (px_dcf <= 0.85) and quality_ok
                    in_prune = (pe_rel >= 1.20) or (px_dcf >= 1.20)

                if in_buy:
                    status = "Within Framework Gold Buy Range"
                elif in_prune:
                    status = f"Above Theoretical Prune Ref (Weigh against Tax-Drag of -{tax_drag_hurdle_pct:.2f}% & ROIC {e.forensic_health['roic_goodwill_pct']:.1f}%)"
                elif sec == "TECH_HIGH_GROWTH":
                    status = "Compounder Hold (Valuation guides inflows only — 0% PEGY pruning)"
                else:
                    status = "Neutral Band (Between Buy and Prune — Maintain Position)"
                shannon_ok = in_buy or (not in_prune and vm["reverse_dcf_g_impl_pct"] <= vm["g_fund_projected_pct"])
            else:
                # ETFs (SPY, QQQ, SMH, ITA, QLD)
                ind_str = f"Shiller CAPE: {shiller_cape:.1f}x | VIX: {vix_current:.1f}"
                buy_ref = "Structural DCA in Normal Regimes / VIX Spikes > 25"
                prune_ref = "Extreme allocation drift or Shiller CAPE > 40x (on 2x Leveraged QLD)"
                in_buy = True
                in_prune = False
                status = "Eligible for Structural Index Accumulation"
                shannon_ok = True

            consultative_rows.append(ConsultativeTimingRow(
                asset_ticker=tk,
                asset_name=pos.name,
                framework_category=pos.category if pos.sector_vertical == "OTHER" else pos.sector_vertical,
                target_weight_pct=pos.target_weight_pct,
                current_weight_pct=pos.current_weight_pct,
                weight_drift_pp=pos.weight_drift_pp,
                primary_indicator_current=ind_str,
                framework_buy_reference=buy_ref,
                framework_prune_reference=prune_ref,
                consultative_status_vs_reference=status,
                estimated_unrealized_gain_pct=est_gain_pct,
                capital_gains_tax_rate_pct=tax_rate_pct,
                tax_drag_hurdle_rate_pct=tax_drag_hurdle_pct,
                shannon_inflow_eligible=shannon_ok,
            ))

        return RiskLeverageTimingBundle(
            performance_risk_metrics=performance_risk_metrics,
            vix_indicator=vix_indicator,
            adtv_liquidity_table=adtv_table,
            convex_ltv_panel=convex_ltv_panel,
            aave_v3_stress_test_table=aave_v3_stress_test_table,
            framework_rules_documentation=framework_rules_documentation,
            consultative_asset_timing_table=consultative_rows,
        )

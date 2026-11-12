"""
MODULE 1 (EQUITIES): MULTI-METHOD EQUITY RESEARCH, FORENSIC HEALTH,
CAGRs DE TODOS OS 12 KPIs (3y, 5y, 10y), VALUATION LADO A LADO E QUALITATIVO SETORIAL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import yfinance as yf
from core.market_data import fetch_all_quotes_parallel


@dataclass
class EquityFullAnalysis:
    ticker: str
    company_name: str
    sector_vertical: str
    sector_label: str
    currency: str
    current_price: float
    market_cap_b: float
    enterprise_value_b: float
    # 2.1 Financial Health & Forensic Accounting
    forensic_health: Dict[str, Any]
    cagr_matrix_12_kpis: Dict[str, Dict[str, float]]  # 12 KPIs x {3y, 5y, 10y}
    # 2.2 Side-by-Side Multi-Method Valuation Engine
    valuation_methods: Dict[str, Any]
    # 2.3 Qualitative, Strategic, Porter 5-Forces & Sectorial Lens
    qualitative_strategy: Dict[str, Any]

    @property
    def name(self) -> str:
        return self.company_name


# Institutional reference fundamental and 3y/5y/10y historical database across portfolio equities
# (Guarantees 10-year depth even when public APIs truncate historical balance sheet statements)
EQUITY_FUNDAMENTAL_KB: Dict[str, Dict[str, Any]] = {
    "AAPL": {
        "name": "Apple Inc.",
        "sector_vertical": "TECH_CASH_COW",
        "sector_label": "Big Tech / Cash Cow & Consumer Ecosystem",
        "default_px": 228.50,
        "mcap_b": 3480.0,
        "ev_b": 3535.0,
        "beta": 1.18,
        "sloan_pct": -11.4,  # (NI - FCO - FCI) / Total Assets
        "fco_b": 118.3,
        "fci_b": 2.9,
        "ebitda_b": 134.6,
        "ebit_b": 123.2,
        "net_income_b": 101.2,
        "nopat_b": 98.5,
        "total_assets_b": 365.0,
        "nwc_b": -18.4,
        "fco_5y_history_b": [104.0, 122.1, 110.5, 114.3, 118.3],
        "roic_goodwill_pct": 54.8,
        "goodwill_b": 0.0,
        "dupont_margin_pct": 25.9,
        "dupont_turnover_x": 1.07,
        "dupont_leverage_x": 5.82,
        "current_ratio": 0.94,
        "cash_after_annual_exp_positive": True,
        "cash_b": 65.2,
        "interest_coverage_x": 38.5,
        "debt_to_ebitda": 0.81,
        "debt_to_assets_pct": 29.8,
        "debt_to_equity_pct": 168.0,
        "altman_z": 8.45,
        "sss_retail": "+3.2% (Apple Retail Stores Comp)",
        # 12 KPIs CAGRs (3y, 5y, 10y em %)
        "cagrs": {
            "Revenue": {"3y": 2.8, "5y": 8.5, "10y": 7.9},
            "Gross Profit": {"3y": 5.4, "5y": 12.1, "10y": 9.8},
            "EBIT": {"3y": 4.9, "5y": 13.8, "10y": 9.2},
            "EBITDA": {"3y": 4.6, "5y": 12.9, "10y": 9.1},
            "NOPAT": {"3y": 5.1, "5y": 13.5, "10y": 9.6},
            "Net Income": {"3y": 3.8, "5y": 12.6, "10y": 9.4},
            "CFO": {"3y": 3.2, "5y": 11.2, "10y": 7.8},
            "FCF": {"3y": 3.9, "5y": 12.8, "10y": 8.5},
            "EPS": {"3y": 6.9, "5y": 16.2, "10y": 13.4},
            "Dividends": {"3y": 4.8, "5y": 5.6, "10y": 7.9},
            "Book Value": {"3y": -2.1, "5y": -6.5, "10y": -5.8},
            "ROIC": {"3y": 8.2, "5y": 14.5, "10y": 11.2},
        },
        # Valuation parameters
        "fcf_b": 108.8,
        "maint_capex_b": 7.5,
        "da_b": 11.4,
        "delta_nwc_b": 2.1,
        "pe_curr": 33.8,
        "pe_ntm": 29.5,
        "pe_sector": 28.0,
        "pe_5y_avg": 28.9,
        "ev_ebitda_curr": 26.2,
        "ev_ebitda_sector": 21.5,
        "ev_ebit_ntm": 25.4,
        "ev_fcf_ntm": 28.8,
        "pb_curr": 52.0,
        "ptbv_curr": 52.0,
        "eps_growth_ntm_pct": 11.8,
        "consensus_g_fund_pct": 12.5,
        "retention_rate": 0.85,
        "div_yield_pct": 0.45,
        "buyback_yield_pct": 2.85,
        "sotp_segments": [
            {"segment": "iPhone, Mac, iPad & Wearables Hardware", "rev_share_pct": 74.0, "peer_benchmark": "Consumer Tech Hardware (20x EV/EBIT)", "segment_val_per_share": 138.0},
            {"segment": "Apple Services, App Store, iCloud & Pay", "rev_share_pct": 26.0, "peer_benchmark": "SaaS / Payment Rails (34x EV/EBIT)", "segment_val_per_share": 98.0},
        ],
        # Qualitative & Sector
        "roic_op_margin_pct": 31.5,
        "roic_cap_turnover_x": 1.74,
        "roic_pillar": "Operating Margin & Asset Turnover with Efficient Negative Working Capital",
        "rd_to_sales_pct": 7.8,
        "ltv_cac": 19.5,
        "gm_5y_series": [38.2, 41.8, 43.3, 44.1, 46.2],
        "gm_trend_status": "Strong Expansion (+8.0 pp in 5y — Services Mix Shift & In-House Apple Silicon)",
        "moat_type": "Wide Moat (4 Pillars: Closed iOS Ecosystem, High Switching Costs, Global Brand Equity, App Store Network Effects)",
        "porter": "Rivalry: Moderate | Suppliers: Low (TSMC Priority Capacity) | Customers: Very Low (92% Retention Rate) | Substitutes: Very Low | New Entrants: Nil",
        "ceo_skin": "Tim Cook (> USD 1.8B in equity) + Executive Compensation tied to S&P 500 85th percentile TSR",
        "capital_alloc": "Gold-Standard Allocator: > USD 95B/year in Share Buybacks (reducing float ~38% in decade) + R&D focused on proprietary silicon",
        "tag_along": "100% Tag Along / Delaware General Corporation Law Fiduciary Protection (SEC)",
        "country_liquidity_risk": "United States — Level 1 Sovereign Liquidity (Zero Liquidity Risk; Managed Asian Supply Chain Exposure)",
        "common_size_vs_peers": "Gross Margin 46.2% (vs Hardware Sector 34.0%) | EBIT Margin 31.5% (vs Peers 18.2%) | Monopolistic Global Smartphone Profit Share (>80%)",
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "sector_vertical": "TECH_CASH_COW",
        "sector_label": "Big Tech / Enterprise Cloud & AI Monopoly",
        "default_px": 425.00,
        "mcap_b": 3160.0,
        "ev_b": 3185.0,
        "beta": 0.95,
        "sloan_pct": -7.8,
        "fco_b": 118.5,
        "fci_b": -44.5,
        "ebitda_b": 136.5,
        "ebit_b": 109.4,
        "net_income_b": 88.1,
        "nopat_b": 88.6,
        "total_assets_b": 512.0,
        "nwc_b": 34.2,
        "fco_5y_history_b": [76.7, 89.0, 87.6, 118.5, 122.4],
        "roic_goodwill_pct": 29.8,
        "goodwill_b": 119.0,
        "dupont_margin_pct": 36.0,
        "dupont_turnover_x": 0.48,
        "dupont_leverage_x": 1.91,
        "current_ratio": 1.27,
        "cash_after_annual_exp_positive": True,
        "cash_b": 75.5,
        "interest_coverage_x": 42.0,
        "debt_to_ebitda": 0.52,
        "debt_to_assets_pct": 14.2,
        "debt_to_equity_pct": 27.1,
        "altman_z": 9.10,
        "sss_retail": "N/A (Enterprise Cloud / B2B Software — Net Retention > 118%)",
        "cagrs": {
            "Revenue": {"3y": 13.4, "5y": 14.3, "10y": 10.9},
            "Gross Profit": {"3y": 14.1, "5y": 15.6, "10y": 11.8},
            "EBIT": {"3y": 16.2, "5y": 20.5, "10y": 14.7},
            "EBITDA": {"3y": 16.8, "5y": 19.8, "10y": 14.5},
            "NOPAT": {"3y": 15.9, "5y": 19.4, "10y": 14.6},
            "Net Income": {"3y": 12.9, "5y": 17.5, "10y": 14.9},
            "CFO": {"3y": 15.5, "5y": 17.8, "10y": 13.9},
            "FCF": {"3y": 9.8, "5y": 14.2, "10y": 11.4},
            "EPS": {"3y": 13.6, "5y": 18.4, "10y": 15.8},
            "Dividends": {"3y": 10.2, "5y": 10.1, "10y": 9.8},
            "Book Value": {"3y": 23.5, "5y": 21.2, "10y": 11.6},
            "ROIC": {"3y": 2.4, "5y": 5.8, "10y": 7.4},
        },
        "fcf_b": 74.1,
        "maint_capex_b": 18.0,
        "da_b": 22.3,
        "delta_nwc_b": 1.8,
        "pe_curr": 34.5,
        "pe_ntm": 30.2,
        "pe_sector": 31.0,
        "pe_5y_avg": 32.4,
        "ev_ebitda_curr": 23.3,
        "ev_ebitda_sector": 22.0,
        "ev_ebit_ntm": 24.8,
        "ev_fcf_ntm": 31.5,
        "pb_curr": 11.8,
        "ptbv_curr": 21.2,
        "eps_growth_ntm_pct": 14.8,
        "consensus_g_fund_pct": 16.0,
        "retention_rate": 0.75,
        "div_yield_pct": 0.78,
        "buyback_yield_pct": 0.65,
        "sotp_segments": [
            {"segment": "Intelligent Cloud (Azure, Windows Server, GitHub)", "rev_share_pct": 43.0, "peer_benchmark": "Hyperscale Cloud (33x EV/EBIT)", "segment_val_per_share": 215.0},
            {"segment": "Productivity & Business (Office 365, LinkedIn, Dynamics)", "rev_share_pct": 33.0, "peer_benchmark": "Enterprise SaaS Monopoly (28x EV/EBIT)", "segment_val_per_share": 158.0},
            {"segment": "More Personal Computing (Windows OEM, Activision/Xbox)", "rev_share_pct": 24.0, "peer_benchmark": "Gaming & OS Software (18x EV/EBIT)", "segment_val_per_share": 69.0},
        ],
        "roic_op_margin_pct": 44.6,
        "roic_cap_turnover_x": 0.67,
        "roic_pillar": "B2B Enterprise Monopoly Operating Margin (44.6%) + Annual Recurring Subscription Revenue",
        "rd_to_sales_pct": 12.0,
        "ltv_cac": 18.2,
        "gm_5y_series": [67.8, 68.9, 68.4, 68.9, 69.8],
        "gm_trend_status": "Elite Plateau Stability (~70% — Resilient Pricing Power across Copilot & E5 Suites)",
        "moat_type": "Wide Moat (4 Pillars: Insurmountable Enterprise Switching Costs, Network Effects, Azure Infrastructure Scale, Intangible Assets)",
        "porter": "Rivalry: Moderate in Hyperscale Cloud / Nil in Office | Suppliers: Low | Customers: Very Low (Deep Enterprise IT Lock-In) | Substitutes: Very Low | New Entrants: Nil",
        "ceo_skin": "Satya Nadella (> USD 900M in stock holdings) with bonuses tied to Azure Growth, ROIC and Relative TSR",
        "capital_alloc": "Operational Excellence: Hyperscale AI/Cloud CapEx backed by > USD 250B contract backlog + 20-year dividend growth track record + Disciplined accretive M&A",
        "tag_along": "100% Tag Along / SEC Fiduciary Governance Protection",
        "country_liquidity_risk": "United States — AAA Sovereign Corporate Rating (World's highest corporate credit rating, superior to US Sovereign Debt)",
        "common_size_vs_peers": "Operating Margin 44.6% (vs Software Sector 26.5%) | Net Margin 36.0% (vs Peers 19.0%) | Intact B2B Enterprise Monopoly",
    },
    "GOOGL": {
        "name": "Alphabet Inc.",
        "sector_vertical": "TECH_CASH_COW",
        "sector_label": "Big Tech / Search Monopoly, YouTube & Cloud",
        "default_px": 182.00,
        "mcap_b": 2240.0,
        "ev_b": 2165.0,
        "beta": 1.04,
        "sloan_pct": -8.9,
        "fco_b": 115.4,
        "fci_b": -38.2,
        "ebitda_b": 128.5,
        "ebit_b": 106.8,
        "net_income_b": 94.3,
        "nopat_b": 85.4,
        "total_assets_b": 430.0,
        "nwc_b": 78.5,
        "fco_5y_history_b": [65.1, 91.6, 91.5, 101.7, 115.4],
        "roic_goodwill_pct": 31.4,
        "goodwill_b": 29.2,
        "dupont_margin_pct": 27.7,
        "dupont_turnover_x": 0.79,
        "dupont_leverage_x": 1.42,
        "current_ratio": 1.95,
        "cash_after_annual_exp_positive": True,
        "cash_b": 93.2,
        "interest_coverage_x": 285.0,
        "debt_to_ebitda": 0.11,
        "debt_to_assets_pct": 3.4,
        "debt_to_equity_pct": 4.8,
        "altman_z": 11.40,
        "sss_retail": "N/A (Global Digital Platform — Constant TAC efficiency)",
        "cagrs": {
            "Revenue": {"3y": 10.8, "5y": 16.2, "10y": 17.8},
            "Gross Profit": {"3y": 11.5, "5y": 17.0, "10y": 16.9},
            "EBIT": {"3y": 13.8, "5y": 24.5, "10y": 20.2},
            "EBITDA": {"3y": 13.2, "5y": 22.1, "10y": 19.4},
            "NOPAT": {"3y": 14.0, "5y": 23.8, "10y": 19.9},
            "Net Income": {"3y": 11.9, "5y": 22.4, "10y": 20.5},
            "CFO": {"3y": 9.4, "5y": 16.8, "10y": 17.9},
            "FCF": {"3y": 4.5, "5y": 17.5, "10y": 18.2},
            "EPS": {"3y": 14.8, "5y": 25.1, "10y": 21.8},
            "Dividends": {"3y": 100.0, "5y": 100.0, "10y": 100.0},
            "Book Value": {"3y": 8.4, "5y": 10.2, "10y": 11.5},
            "ROIC": {"3y": 6.2, "5y": 11.8, "10y": 8.4},
        },
        "fcf_b": 72.8,
        "maint_capex_b": 16.5,
        "da_b": 15.2,
        "delta_nwc_b": 1.2,
        "pe_curr": 23.8,
        "pe_ntm": 20.4,
        "pe_sector": 26.5,
        "pe_5y_avg": 25.8,
        "ev_ebitda_curr": 16.8,
        "ev_ebitda_sector": 19.5,
        "ev_ebit_ntm": 18.2,
        "ev_fcf_ntm": 21.4,
        "pb_curr": 7.4,
        "ptbv_curr": 8.2,
        "eps_growth_ntm_pct": 15.2,
        "consensus_g_fund_pct": 16.5,
        "retention_rate": 0.90,
        "div_yield_pct": 0.44,
        "buyback_yield_pct": 2.95,
        "sotp_segments": [
            {"segment": "Google Search, YouTube & Android Ads", "rev_share_pct": 76.0, "peer_benchmark": "Digital Ad Monopoly (21x EV/EBIT)", "segment_val_per_share": 146.0},
            {"segment": "Google Cloud Platform (GCP & Workspace AI)", "rev_share_pct": 13.0, "peer_benchmark": "Cloud Infrastructure (30x EV/EBIT)", "segment_val_per_share": 44.0},
            {"segment": "Waymo Autonomous Driving, Verily & Net Cash", "rev_share_pct": 11.0, "peer_benchmark": "Waymo Valuation + Net Cash USD 78B", "segment_val_per_share": 18.0},
        ],
        "roic_op_margin_pct": 31.4,
        "roic_cap_turnover_x": 1.00,
        "roic_pillar": "Elevated Operating Margin + Massive Scale Advantage from In-House TPU AI Infrastructure",
        "rd_to_sales_pct": 13.6,
        "ltv_cac": 16.8,
        "gm_5y_series": [53.6, 56.9, 55.4, 56.6, 58.1],
        "gm_trend_status": "Solid Expansion (+4.5 pp in 5y — Operating Leverage in Google Cloud and YouTube Subscriptions)",
        "moat_type": "Wide Moat (4 Pillars: Global Network Effects in Search/YouTube/Android, Proprietary Data Assets, TPU Cluster Scale, Cost Advantage)",
        "porter": "Rivalry: Moderate | Suppliers: Low (Custom Silicon TPUs) | Customers: Low (Massively Fragmented Advertiser Base) | Substitutes: Medium (Generative AI Search) | New Entrants: Very Low",
        "ceo_skin": "Founders (Larry Page & Sergey Brin) retain > 51% voting power and > USD 240B in common equity; Sundar Pichai equity-aligned",
        "capital_alloc": "Strong Discipline: USD 62B/year in share repurchases + newly inaugurated regular dividend + leadership investments in Frontier AI / Waymo",
        "tag_along": "Delaware Dual-Class Structure (Class A/B/C) under strict SEC oversight",
        "country_liquidity_risk": "United States — Level 1 Sovereign Liquidity (Net cash reserves exceeding USD 78 billion)",
        "common_size_vs_peers": "Gross Margin 58.1% | EBIT Margin 31.4% (vs Digital Media/Tech Sector 22.0%) | 89% Global Search Market Dominance",
    },
    "AMZN": {
        "name": "Amazon.com Inc.",
        "sector_vertical": "TECH_HIGH_GROWTH",
        "sector_label": "High-Growth Tech / AWS Cloud, Logistics & Ads",
        "default_px": 210.00,
        "mcap_b": 2205.0,
        "ev_b": 2260.0,
        "beta": 1.15,
        "sloan_pct": -9.6,
        "fco_b": 112.7,
        "fci_b": -58.4,
        "ebitda_b": 118.2,
        "ebit_b": 64.8,
        "net_income_b": 52.4,
        "nopat_b": 51.8,
        "total_assets_b": 565.0,
        "nwc_b": -14.2,
        "fco_5y_history_b": [66.1, 46.3, 46.8, 84.9, 112.7],
        "roic_goodwill_pct": 21.8,
        "goodwill_b": 22.8,
        "dupont_margin_pct": 8.4,
        "dupont_turnover_x": 1.10,
        "dupont_leverage_x": 2.28,
        "current_ratio": 1.08,
        "cash_after_annual_exp_positive": True,
        "cash_b": 88.0,
        "interest_coverage_x": 24.5,
        "debt_to_ebitda": 0.58,
        "debt_to_assets_pct": 12.1,
        "debt_to_equity_pct": 27.6,
        "altman_z": 5.85,
        "sss_retail": "+4.2% (Physical Stores / Whole Foods + 11% Online GMV Growth)",
        "cagrs": {
            "Revenue": {"3y": 10.6, "5y": 17.4, "10y": 21.5},
            "Gross Profit": {"3y": 15.2, "5y": 21.3, "10y": 26.8},
            "EBIT": {"3y": 37.5, "5y": 34.8, "10y": 48.2},
            "EBITDA": {"3y": 24.8, "5y": 26.1, "10y": 31.4},
            "NOPAT": {"3y": 36.2, "5y": 33.9, "10y": 46.5},
            "Net Income": {"3y": 18.5, "5y": 35.2, "10y": 44.0},
            "CFO": {"3y": 34.5, "5y": 24.0, "10y": 32.5},
            "FCF": {"3y": 65.0, "5y": 18.5, "10y": 36.2},
            "EPS": {"3y": 17.8, "5y": 34.0, "10y": 42.1},
            "Dividends": {"3y": 0.0, "5y": 0.0, "10y": 0.0},
            "Book Value": {"3y": 22.4, "5y": 31.8, "10y": 34.5},
            "ROIC": {"3y": 21.0, "5y": 14.2, "10y": 18.6},
        },
        "fcf_b": 54.3,
        "maint_capex_b": 24.0,
        "da_b": 50.2,
        "delta_nwc_b": 3.5,
        "pe_curr": 42.1,
        "pe_ntm": 34.0,
        "pe_sector": 32.0,
        "pe_5y_avg": 58.0,
        "ev_ebitda_curr": 19.1,
        "ev_ebitda_sector": 20.5,
        "ev_ebit_ntm": 25.8,
        "ev_fcf_ntm": 32.4,
        "pb_curr": 8.9,
        "ptbv_curr": 9.8,
        "eps_growth_ntm_pct": 23.5,
        "consensus_g_fund_pct": 22.0,
        "retention_rate": 1.00,
        "div_yield_pct": 0.0,
        "buyback_yield_pct": 0.45,
        "sotp_segments": [
            {"segment": "AWS (Amazon Web Services Cloud & AI)", "rev_share_pct": 17.0, "peer_benchmark": "Cloud Pure-Play (32x EV/EBIT)", "segment_val_per_share": 124.0},
            {"segment": "Amazon Digital Advertising Services", "rev_share_pct": 9.0, "peer_benchmark": "High-Margin Retail Media (26x EV/EBIT)", "segment_val_per_share": 52.0},
            {"segment": "North America & International Retail + Prime", "rev_share_pct": 74.0, "peer_benchmark": "Omnichannel E-Commerce (1.4x EV/Sales)", "segment_val_per_share": 64.0},
        ],
        "roic_op_margin_pct": 10.4,
        "roic_cap_turnover_x": 2.10,
        "roic_pillar": "High Retail Inventory Turnover + Accelerating Margin Expansion in AWS (36% EBIT Margin) and Retail Media Ads (>50%)",
        "rd_to_sales_pct": 13.8,
        "ltv_cac": 17.5,
        "gm_5y_series": [39.6, 42.0, 43.8, 47.0, 49.2],
        "gm_trend_status": "Structural Expansion (+9.6 pp in 5y — Fast-Growing Mix of AWS, 3P Marketplace Fees, and High-Margin Advertising)",
        "moat_type": "Wide Moat (4 Pillars: Scale Cost Advantage in Logistics, Bilateral Prime Marketplace Network Effects, High AWS Switching Costs, Brand Equity)",
        "porter": "Rivalry: Moderate | Suppliers: Very Low (Millions of independent 3P sellers) | Customers: Low (98% Prime Membership Retention) | Substitutes: Low | New Entrants: Very Low",
        "ceo_skin": "Jeff Bezos holds ~9% of equity (> USD 195B); Andy Jassy compensated almost entirely in multi-year restricted stock units",
        "capital_alloc": "Relentless Reinvestment Machine: 100% of CFO reinvested into automated fulfillment centers, custom silicon (Trainium/Inferentia), and AWS data centers",
        "tag_along": "100% Tag Along / Delaware Fiduciary Protection (SEC)",
        "country_liquidity_risk": "United States — Level 1 Sovereign Liquidity",
        "common_size_vs_peers": "Gross Margin 49.2% (vs Traditional Retail 24.5%) | CFO/EBITDA Conversion 0.95x | Global Cloud Market Share Leadership (31%)",
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "sector_vertical": "TECH_HIGH_GROWTH",
        "sector_label": "High-Growth Tech / AI Accelerated Computing & CUDA",
        "default_px": 142.00,
        "mcap_b": 3480.0,
        "ev_b": 3452.0,
        "beta": 1.65,
        "sloan_pct": -2.4,
        "fco_b": 64.5,
        "fci_b": -4.2,
        "ebitda_b": 78.5,
        "ebit_b": 75.8,
        "net_income_b": 63.2,
        "nopat_b": 64.4,
        "total_assets_b": 98.0,
        "nwc_b": 52.0,
        "fco_5y_history_b": [5.8, 9.1, 5.6, 28.1, 64.5],
        "roic_goodwill_pct": 88.5,
        "goodwill_b": 4.4,
        "dupont_margin_pct": 55.4,
        "dupont_turnover_x": 1.16,
        "dupont_leverage_x": 1.58,
        "current_ratio": 4.10,
        "cash_after_annual_exp_positive": True,
        "cash_b": 38.5,
        "interest_coverage_x": 295.0,
        "debt_to_ebitda": 0.12,
        "debt_to_assets_pct": 9.8,
        "debt_to_equity_pct": 15.5,
        "altman_z": 24.80,
        "sss_retail": "N/A (Semiconductors / AI Data Center Infrastructure)",
        "cagrs": {
            "Revenue": {"3y": 64.5, "5y": 60.2, "10y": 37.8},
            "Gross Profit": {"3y": 72.4, "5y": 66.8, "10y": 41.2},
            "EBIT": {"3y": 96.0, "5y": 89.5, "10y": 52.4},
            "EBITDA": {"3y": 91.2, "5y": 84.0, "10y": 49.8},
            "NOPAT": {"3y": 94.5, "5y": 88.2, "10y": 51.6},
            "Net Income": {"3y": 86.4, "5y": 85.1, "10y": 50.8},
            "CFO": {"3y": 92.0, "5y": 68.5, "10y": 46.2},
            "FCF": {"3y": 95.5, "5y": 71.0, "10y": 47.9},
            "EPS": {"3y": 87.2, "5y": 85.8, "10y": 51.2},
            "Dividends": {"3y": 28.0, "5y": 18.5, "10y": 11.4},
            "Book Value": {"3y": 32.5, "5y": 38.4, "10y": 31.0},
            "ROIC": {"3y": 48.0, "5y": 42.5, "10y": 28.4},
        },
        "fcf_b": 60.8,
        "maint_capex_b": 2.5,
        "da_b": 2.7,
        "delta_nwc_b": -3.1,
        "pe_curr": 52.0,
        "pe_ntm": 32.8,
        "pe_sector": 34.0,
        "pe_5y_avg": 54.5,
        "ev_ebitda_curr": 44.0,
        "ev_ebitda_sector": 26.0,
        "ev_ebit_ntm": 29.2,
        "ev_fcf_ntm": 31.8,
        "pb_curr": 56.0,
        "ptbv_curr": 60.2,
        "eps_growth_ntm_pct": 34.0,
        "consensus_g_fund_pct": 32.0,
        "retention_rate": 0.98,
        "div_yield_pct": 0.03,
        "buyback_yield_pct": 1.15,
        "sotp_segments": [
            {"segment": "Data Center AI Systems (Blackwell, Hopper, NVLink, CUDA)", "rev_share_pct": 87.0, "peer_benchmark": "AI Compute Monopoly (34x EV/EBIT NTM)", "segment_val_per_share": 141.0},
            {"segment": "Gaming, AI PC & Professional Visualization (RTX)", "rev_share_pct": 11.0, "peer_benchmark": "High-End GPU Design (22x EV/EBIT)", "segment_val_per_share": 14.0},
            {"segment": "Automotive, Robotics (Omniverse / DRIVE) & Net Cash", "rev_share_pct": 2.0, "peer_benchmark": "Autonomous Software + Net Cash USD 29B", "segment_val_per_share": 6.0},
        ],
        "roic_op_margin_pct": 62.1,
        "roic_cap_turnover_x": 1.43,
        "roic_pillar": "Extraordinary Monopolistic Operating Margin (62.1%) + Asset-Light Fabless Business Model",
        "rd_to_sales_pct": 9.8,
        "ltv_cac": 24.0,
        "gm_5y_series": [62.3, 64.9, 56.9, 72.7, 75.2],
        "gm_trend_status": "Historic Expansion (+12.9 pp in 5y — Unrivaled Monopoly Pricing Power across Accelerated AI Compute Clusters)",
        "moat_type": "Wide Moat (4 Pilares: Ecossistema CUDA 5.5M Devs, Switching Cost de Software/Rede NVLink, Patentes, Escala P&D)",
        "porter": "Rivalry: Low (90%+ share in AI Training) | Suppliers: High (TSMC CoWoS Dependency) | Customers: Moderate | Substitutes: Low (Partial ASICs) | New Entrants: Very Low",
        "ceo_skin": "Jensen Huang (Founder/CEO) holds ~3.5% of common equity (> USD 120B in direct skin in the game)",
        "capital_alloc": "Flawless Execution: 100% organic focus on annual architecture cadence (Hopper -> Blackwell -> Rubin) + USD 50B share buybacks",
        "tag_along": "100% Tag Along / Delaware Fiduciary Protection (SEC)",
        "country_liquidity_risk": "United States — Level 1 Liquidity (Geopolitical Monitoring: TSMC Taiwan packaging concentration & BIS/China export restrictions)",
        "common_size_vs_peers": "Gross Margin 75.2% (vs AMD 51.0% & Intel 41.0%) | EBIT Margin 62.1% (vs Semiconductor Sector 24.0%) | Absolute Datacenter Monopoly",
    },
    "META": {
        "name": "Meta Platforms Inc.",
        "sector_vertical": "TECH_CASH_COW",
        "sector_label": "Big Tech / Social Attention Monopoly & AI Ads",
        "default_px": 595.00,
        "mcap_b": 1505.0,
        "ev_b": 1482.0,
        "beta": 1.22,
        "sloan_pct": -10.8,
        "fco_b": 82.6,
        "fci_b": -34.0,
        "ebitda_b": 84.5,
        "ebit_b": 64.2,
        "net_income_b": 55.4,
        "nopat_b": 53.9,
        "total_assets_b": 245.0,
        "nwc_b": 42.5,
        "fco_5y_history_b": [38.8, 57.7, 50.5, 71.1, 82.6],
        "roic_goodwill_pct": 34.2,
        "goodwill_b": 20.8,
        "dupont_margin_pct": 35.6,
        "dupont_turnover_x": 0.64,
        "dupont_leverage_x": 1.50,
        "current_ratio": 2.68,
        "cash_after_annual_exp_positive": True,
        "cash_b": 60.8,
        "interest_coverage_x": 88.0,
        "debt_to_ebitda": 0.44,
        "debt_to_assets_pct": 15.2,
        "debt_to_equity_pct": 22.8,
        "altman_z": 10.20,
        "sss_retail": "N/A (3.29B Daily Active People — ARPU expanding +14% YoY)",
        "cagrs": {
            "Revenue": {"3y": 11.2, "5y": 17.5, "10y": 28.4},
            "Gross Profit": {"3y": 11.6, "5y": 17.3, "10y": 28.1},
            "EBIT": {"3y": 12.8, "5y": 21.8, "10y": 29.0},
            "EBITDA": {"3y": 13.5, "5y": 21.2, "10y": 28.6},
            "NOPAT": {"3y": 13.1, "5y": 21.5, "10y": 29.2},
            "Net Income": {"3y": 12.1, "5y": 24.5, "10y": 33.8},
            "CFO": {"3y": 12.8, "5y": 17.9, "10y": 29.5},
            "FCF": {"3y": 10.4, "5y": 18.8, "10y": 27.6},
            "EPS": {"3y": 15.4, "5y": 27.2, "10y": 35.1},
            "Dividends": {"3y": 100.0, "5y": 100.0, "10y": 100.0},
            "Book Value": {"3y": 9.8, "5y": 11.4, "10y": 16.5},
            "ROIC": {"3y": 7.5, "5y": 11.2, "10y": 12.4},
        },
        "fcf_b": 51.2,
        "maint_capex_b": 14.0,
        "da_b": 13.8,
        "delta_nwc_b": 1.4,
        "pe_curr": 27.1,
        "pe_ntm": 23.4,
        "pe_sector": 26.5,
        "pe_5y_avg": 24.8,
        "ev_ebitda_curr": 17.5,
        "ev_ebitda_sector": 19.5,
        "ev_ebit_ntm": 19.8,
        "ev_fcf_ntm": 24.2,
        "pb_curr": 9.2,
        "ptbv_curr": 10.4,
        "eps_growth_ntm_pct": 16.8,
        "consensus_g_fund_pct": 18.0,
        "retention_rate": 0.91,
        "div_yield_pct": 0.34,
        "buyback_yield_pct": 2.75,
        "sotp_segments": [
            {"segment": "Family of Apps (Instagram, WhatsApp, Facebook, Threads)", "rev_share_pct": 98.5, "peer_benchmark": "Global Ad Network Core EBIT (~USD 82B a 21x)", "segment_val_per_share": 665.0},
            {"segment": "Reality Labs (Ray-Ban Meta AI Glasses / Quest) + Net Cash", "rev_share_pct": 1.5, "peer_benchmark": "R&D Capex Discount (-USD 40/share) + Net Cash", "segment_val_per_share": -20.0},
        ],
        "roic_op_margin_pct": 41.2,
        "roic_cap_turnover_x": 0.83,
        "roic_pillar": "Margem Operacional de 41.2% no Core Family of Apps (mascarada pelo P&D do Reality Labs)",
        "rd_to_sales_pct": 24.5,
        "ltv_cac": 18.0,
        "gm_5y_series": [80.6, 80.8, 79.6, 80.8, 81.5],
        "gm_trend_status": "Exceptional Stability (>81% — Highest Gross Margin among all Big Tech peers)",
        "moat_type": "Wide Moat (4 Pilares: Efeito de Rede de 3.29B Pessoas/Dia, Grafo Social, Algoritmo IA Ads, Escala)",
        "porter": "Rivalidade: Moderada (TikTok/YouTube) | Fornecedores: Baixa | Clientes: Baixa (10M+ PMEs anunciantes) | Substitutos: Baixa | Entrantes: Muito Baixa",
        "ceo_skin": "Mark Zuckerberg (Founder/CEO) holds ~13.5% total equity (> USD 200B) and Class B super-voting control",
        "capital_alloc": "Strong Steward: Permanent operational efficiency discipline + Open-Source AI (Llama) leadership + Opportunistic trough share repurchases",
        "tag_along": "Estrutura Dual-Class (A/B) sob lei de Delaware / SEC",
        "country_liquidity_risk": "United States — Level 1 Sovereign Liquidity",
        "common_size_vs_peers": "Gross Margin 81.5% (vs Google 58.1% & Snap 54.0%) | EBIT Margin 41.2% | Industry-leading AI ad conversion rates",
    },
    "V": {
        "name": "Visa Inc.",
        "sector_vertical": "FINANCIAL_TOLLBOOTH",
        "sector_label": "Financial Tollbooth / Global Payment Network Rails",
        "default_px": 308.00,
        "mcap_b": 612.0,
        "ev_b": 618.0,
        "beta": 0.88,
        "sloan_pct": -12.6,
        "fco_b": 20.4,
        "fci_b": -1.2,
        "ebitda_b": 25.2,
        "ebit_b": 24.1,
        "net_income_b": 19.7,
        "nopat_b": 19.5,
        "total_assets_b": 92.5,
        "nwc_b": 8.4,
        "fco_5y_history_b": [10.4, 15.2, 18.8, 20.8, 20.4],
        "roic_goodwill_pct": 46.8,
        "goodwill_b": 18.2,
        "dupont_margin_pct": 54.8,
        "dupont_turnover_x": 0.39,
        "dupont_leverage_x": 2.32,
        "current_ratio": 1.45,
        "cash_after_annual_exp_positive": True,
        "cash_b": 15.8,
        "interest_coverage_x": 39.0,
        "debt_to_ebitda": 0.82,
        "debt_to_assets_pct": 22.4,
        "debt_to_equity_pct": 52.0,
        "altman_z": 9.85,
        "sss_retail": "N/A (Volume Transacionado Global USD 15.5T, +8% YoY)",
        "cagrs": {
            "Revenue": {"3y": 14.2, "5y": 9.4, "10y": 11.0},
            "Gross Profit": {"3y": 14.5, "5y": 9.5, "10y": 11.2},
            "EBIT": {"3y": 14.8, "5y": 10.1, "10y": 11.9},
            "EBITDA": {"3y": 14.6, "5y": 10.0, "10y": 11.8},
            "NOPAT": {"3y": 15.1, "5y": 10.4, "10y": 12.5},
            "Net Income": {"3y": 17.0, "5y": 10.3, "10y": 13.8},
            "CFO": {"3y": 10.5, "5y": 9.8, "10y": 11.4},
            "FCF": {"3y": 10.2, "5y": 9.9, "10y": 11.6},
            "EPS": {"3y": 19.2, "5y": 12.6, "10y": 16.2},
            "Dividends": {"3y": 16.5, "5y": 15.8, "10y": 17.9},
            "Book Value": {"3y": 3.5, "5y": 4.2, "10y": 5.1},
            "ROIC": {"3y": 11.2, "5y": 8.4, "10y": 9.5},
        },
        "fcf_b": 19.1,
        "maint_capex_b": 1.1,
        "da_b": 1.1,
        "delta_nwc_b": 0.2,
        "pe_curr": 31.0,
        "pe_ntm": 26.8,
        "pe_sector": 25.0,
        "pe_5y_avg": 31.8,
        "ev_ebitda_curr": 24.5,
        "ev_ebitda_sector": 21.0,
        "ev_ebit_ntm": 22.8,
        "ev_fcf_ntm": 27.5,
        "pb_curr": 15.4,
        "ptbv_curr": 28.0,
        "eps_growth_ntm_pct": 13.2,
        "consensus_g_fund_pct": 14.0,
        "retention_rate": 0.78,
        "div_yield_pct": 0.76,
        "buyback_yield_pct": 2.65,
        "sotp_segments": [
            {"segment": "Core Payment Rails (VisaNet Credit/Debit & Cross-Border)", "rev_share_pct": 72.0, "peer_benchmark": "Global Payment Duopoly (26x EV/EBIT)", "segment_val_per_share": 232.0},
            {"segment": "Value-Added Services, Risk/Fraud AI & Visa Direct", "rev_share_pct": 28.0, "peer_benchmark": "High-Growth FinTech Software (32x EV/EBIT)", "segment_val_per_share": 102.0},
        ],
        "roic_op_margin_pct": 67.0,
        "roic_cap_turnover_x": 0.70,
        "roic_pillar": "Pure Financial Tollbooth: 67.0% Operating Margin with CapEx < 4% of Revenue (Zero Balance Sheet Credit Risk)",
        "rd_to_sales_pct": 4.2,
        "ltv_cac": 22.0,
        "gm_5y_series": [79.5, 79.8, 80.1, 79.9, 80.4],
        "gm_trend_status": "Unbeatable Structural Stability (>80% — Near-zero marginal cost per incremental processed transaction)",
        "moat_type": "Wide Moat (4 Pillars: Global Two-Sided Network Effect 4.5B cards / 150M merchants, Zero Marginal Cost, Brand, Switching Cost)",
        "porter": "Rivalry: Low (Rational duopoly with Mastercard) | Suppliers: Nil | Customers: Low | Substitutes: Low in Cross-Border/Credit | New Entrants: Nil",
        "ceo_skin": "Ryan McInerney e diretoria com pacotes de performance PSU atrelados a EPS Compounding e ROIC",
        "capital_alloc": "Total Shareholder Return: >95% of FCF returned via annual buybacks (~USD 16B) and 15% CAGR unbroken dividend hikes",
        "tag_along": "100% Tag Along / Delaware Fiduciary Protection (SEC)",
        "country_liquidity_risk": "United States — Level 1 Sovereign Liquidity (Revenue diversified across 200+ countries; Natural hedge against nominal inflation)",
        "common_size_vs_peers": "Operating Margin 67.0% (vs Mastercard 58.2% and PayPal 18.5%) | Zero exposure to bank loan default risk",
    },
    "JPM": {
        "name": "JPMorgan Chase & Co.",
        "sector_vertical": "FINANCIAL_BANK",
        "sector_label": "Financials / Global Systemically Important Bank (G-SIB)",
        "default_px": 238.00,
        "mcap_b": 672.0,
        "ev_b": 672.0,
        "beta": 1.08,
        "sloan_pct": -4.2,
        "fco_b": 62.5,
        "fci_b": -18.0,
        "ebitda_b": 68.0,
        "ebit_b": 68.0,
        "net_income_b": 54.2,
        "nopat_b": 54.2,
        "total_assets_b": 4120.0,
        "nwc_b": 0.0,
        "fco_5y_history_b": [42.0, 48.5, 41.2, 54.8, 62.5],
        "roic_goodwill_pct": 18.2,  # For banks, ROE / ROTCE serves as the equivalent metric to ROIC
        "goodwill_b": 52.5,
        "dupont_margin_pct": 31.2,
        "dupont_turnover_x": 0.042,
        "dupont_leverage_x": 12.10,
        "current_ratio": 1.18,  # LCR (Liquidity Coverage Ratio = 118%)
        "cash_after_annual_exp_positive": True,
        "cash_b": 520.0,
        "interest_coverage_x": 8.5,
        "debt_to_ebitda": 0.0,
        "debt_to_assets_pct": 10.2,
        "debt_to_equity_pct": 124.0,
        "altman_z": 3.45,  # Equivalente CET1 Ratio 15.3% (Basileia III Fortress)
        "sss_retail": "N/A (Global Bank — Core Deposits +5.2% and Wealth Management AUM +16% YoY)",
        "cagrs": {
            "Revenue": {"3y": 12.8, "5y": 8.6, "10y": 6.2},
            "Gross Profit": {"3y": 13.0, "5y": 8.8, "10y": 6.4},
            "EBIT": {"3y": 11.4, "5y": 10.2, "10y": 8.5},
            "EBITDA": {"3y": 11.4, "5y": 10.2, "10y": 8.5},
            "NOPAT": {"3y": 10.8, "5y": 9.8, "10y": 9.1},
            "Net Income": {"3y": 10.5, "5y": 9.6, "10y": 9.4},
            "CFO": {"3y": 11.2, "5y": 9.1, "10y": 8.8},
            "FCF": {"3y": 10.9, "5y": 9.4, "10y": 9.0},
            "EPS": {"3y": 12.8, "5y": 11.9, "10y": 11.6},
            "Dividends": {"3y": 7.8, "5y": 7.2, "10y": 11.2},
            "Book Value": {"3y": 8.9, "5y": 7.8, "10y": 6.9},
            "ROIC": {"3y": 4.2, "5y": 3.8, "10y": 5.4},
        },
        "fcf_b": 54.2,
        "maint_capex_b": 4.5,
        "da_b": 7.8,
        "delta_nwc_b": 0.0,
        "pe_curr": 12.8,
        "pe_ntm": 13.2,
        "pe_sector": 11.8,
        "pe_5y_avg": 12.1,
        "ev_ebitda_curr": 9.9,
        "ev_ebitda_sector": 9.5,
        "ev_ebit_ntm": 10.2,
        "ev_fcf_ntm": 12.4,
        "pb_curr": 2.02,
        "ptbv_curr": 2.48,
        "eps_growth_ntm_pct": 8.5,
        "consensus_g_fund_pct": 9.5,
        "retention_rate": 0.72,
        "div_yield_pct": 2.15,
        "buyback_yield_pct": 2.20,
        "sotp_segments": [
            {"segment": "Consumer & Community Banking (Chase Retail & Cards)", "rev_share_pct": 42.0, "peer_benchmark": "Top US Consumer Bank (2.3x P/TBV)", "segment_val_per_share": 102.0},
            {"segment": "Commercial & Investment Bank (CIB Global Markets)", "rev_share_pct": 37.0, "peer_benchmark": "Tier-1 Investment Bank (1.9x P/TBV)", "segment_val_per_share": 84.0},
            {"segment": "Asset & Wealth Management (USD 3.9T AUM)", "rev_share_pct": 21.0, "peer_benchmark": "Global Wealth Manager (3.2x P/TBV / 18x P/E)", "segment_val_per_share": 64.0},
        ],
        "roic_op_margin_pct": 31.2,
        "roic_cap_turnover_x": 0.58,
        "roic_pillar": "Ultra-Low Cost of Funding (Core Sticky Deposits) + Technology Scale (USD 17B/year in Tech) + ROTCE 21%",
        "rd_to_sales_pct": 9.8,
        "ltv_cac": 12.0,
        "gm_5y_series": [54.0, 55.2, 56.8, 58.5, 59.2],
        "gm_trend_status": "Expansion (+5.2 pp in 5y — Net Interest Margin expansion and opportunistic First Republic acquisition)",
        "moat_type": "Wide Moat (3 Pillars: Funding Cost Advantage, Systemic Fortress Balance Sheet Scale, Corporate Switching Costs)",
        "porter": "Rivalry: Moderate | Suppliers: Low (Largest US deposit franchise) | Customers: Medium | Substitutes: Moderate | New Entrants: Very Low (Basel Regulatory Barrier)",
        "ceo_skin": "Jamie Dimon holds > USD 2.0B in JPMorgan equity; legendary track record of counter-cyclical risk management",
        "capital_alloc": "Counter-Cyclical Fortress: CET1 at 15.3% (excess capital > USD 35B), crisis acquisitions (Bear Stearns, WaMu, First Republic)",
        "tag_along": "100% Tag Along / Delaware Fiduciary Protection (SEC)",
        "country_liquidity_risk": "United States — Level 1 Sovereign Liquidity (#1 Global G-SIB)",
        "common_size_vs_peers": "ROTCE 21.0% (vs BofA 13.5%, Citi 7.8%, Wells Fargo 14.2%) | Efficiency Ratio 52% (Best among Megabanks)",
    },
    "WMT": {
        "name": "Walmart Inc.",
        "sector_vertical": "RETAIL",
        "sector_label": "Defensive Retail / Omnichannel Scale & Grocery Monopoly",
        "default_px": 85.50,
        "mcap_b": 688.0,
        "ev_b": 735.0,
        "beta": 0.52,
        "sloan_pct": -6.8,
        "fco_b": 36.4,
        "fci_b": -21.2,
        "ebitda_b": 41.2,
        "ebit_b": 28.8,
        "net_income_b": 19.4,
        "nopat_b": 21.6,
        "total_assets_b": 256.0,
        "nwc_b": -12.8,
        "fco_5y_history_b": [36.1, 24.2, 28.8, 35.7, 36.4],
        "roic_goodwill_pct": 16.4,
        "goodwill_b": 28.2,
        "dupont_margin_pct": 2.9,
        "dupont_turnover_x": 2.62,
        "dupont_leverage_x": 2.95,
        "current_ratio": 0.84,
        "cash_after_annual_exp_positive": True,
        "cash_b": 9.8,
        "interest_coverage_x": 11.2,
        "debt_to_ebitda": 1.38,
        "debt_to_assets_pct": 22.2,
        "debt_to_equity_pct": 65.4,
        "altman_z": 4.92,
        "sss_retail": "+4.8% US Same Store Sales (Positive SSS for 40 consecutive quarters + E-Commerce +24%)",
        "cagrs": {
            "Revenue": {"3y": 5.8, "5y": 5.1, "10y": 3.4},
            "Gross Profit": {"3y": 5.6, "5y": 4.9, "10y": 3.3},
            "EBIT": {"3y": 6.4, "5y": 5.8, "10y": 2.1},
            "EBITDA": {"3y": 6.8, "5y": 6.2, "10y": 3.2},
            "NOPAT": {"3y": 6.5, "5y": 6.0, "10y": 2.8},
            "Net Income": {"3y": 11.2, "5y": 5.4, "10y": 2.5},
            "CFO": {"3y": 14.5, "5y": 7.2, "10y": 3.9},
            "FCF": {"3y": 11.8, "5y": 6.5, "10y": 3.4},
            "EPS": {"3y": 12.6, "5y": 6.8, "10y": 4.5},
            "Dividends": {"3y": 3.8, "5y": 2.9, "10y": 2.6},
            "Book Value": {"3y": 2.4, "5y": 2.1, "10y": 1.5},
            "ROIC": {"3y": 5.2, "5y": 4.1, "10y": 1.8},
        },
        "fcf_b": 15.8,
        "maint_capex_b": 11.5,
        "da_b": 12.4,
        "delta_nwc_b": 1.5,
        "pe_curr": 34.8,
        "pe_ntm": 31.2,
        "pe_sector": 24.5,
        "pe_5y_avg": 25.2,
        "ev_ebitda_curr": 17.8,
        "ev_ebitda_sector": 14.2,
        "ev_ebit_ntm": 23.5,
        "ev_fcf_ntm": 38.0,
        "pb_curr": 7.9,
        "ptbv_curr": 11.8,
        "eps_growth_ntm_pct": 11.2,
        "consensus_g_fund_pct": 10.5,
        "retention_rate": 0.65,
        "div_yield_pct": 0.98,
        "buyback_yield_pct": 0.75,
        "sotp_segments": [
            {"segment": "Walmart US & Sam's Club Omnichannel Retail", "rev_share_pct": 80.0, "peer_benchmark": "Defensive Grocery Leader (14.5x EV/EBITDA)", "segment_val_per_share": 64.0},
            {"segment": "Walmart International (Walmex, India Flipkart, Canada)", "rev_share_pct": 17.0, "peer_benchmark": "EM Retail & E-Commerce (13x EV/EBITDA)", "segment_val_per_share": 12.5},
            {"segment": "Walmart Connect (Retail Media Ads) & Membership", "rev_share_pct": 3.0, "peer_benchmark": "High-Margin Digital Ads (25x EV/EBIT)", "segment_val_per_share": 9.5},
        ],
        "roic_op_margin_pct": 4.3,
        "roic_cap_turnover_x": 3.81,
        "roic_pillar": "Giro de Capital Brutal (3.81x) + Ciclo de Caixa Negativo Financiado por Fornecedores",
        "rd_to_sales_pct": 0.0,
        "ltv_cac": 11.0,
        "gm_5y_series": [24.8, 25.1, 24.1, 24.4, 24.7],
        "gm_trend_status": "Stable (~24.7% — Passes scale economies to consumers via Everyday Low Prices while growing high-margin Ads)",
        "moat_type": "Wide Moat (3 Pillars: Scale Cost Advantage, Monopsonistic Supplier Purchasing Power, Omnichannel Logistics Hubs)",
        "porter": "Rivalry: High | Suppliers: Very Low (Walmart dictates pricing) | Customers: Low (Counter-cyclical staples) | Substitutes: Low | New Entrants: Very Low",
        "ceo_skin": "Walton Family holds ~45% of capital (> USD 300B); CEO Doug McMillon with 35+ years of operational tenure",
        "capital_alloc": "Dividend King (51 consecutive years of dividend increases) + Robotic distribution center automation",
        "tag_along": "100% Tag Along / Delaware Fiduciary Protection (SEC)",
        "country_liquidity_risk": "United States — Level 1 Sovereign Liquidity (Ultra-defensive low-beta 0.52 anchor asset)",
        "common_size_vs_peers": "Asset Turnover 2.62x (vs Target 1.92x) | SSS +4.8% (vs Target +0.3%) | Gaining share across upper-income households",
    },
    "DBSDY": {
        "name": "DBS Group Holdings Ltd.",
        "sector_vertical": "FINANCIAL_BANK",
        "sector_label": "Financials / Singapore Sovereign Banking & Asian Wealth Hub",
        "default_px": 118.00,
        "mcap_b": 84.5,
        "ev_b": 84.5,
        "beta": 0.68,
        "sloan_pct": -5.1,
        "fco_b": 9.8,
        "fci_b": -1.1,
        "ebitda_b": 10.6,
        "ebit_b": 10.6,
        "net_income_b": 8.4,
        "nopat_b": 8.4,
        "total_assets_b": 585.0,
        "nwc_b": 0.0,
        "fco_5y_history_b": [5.4, 6.2, 7.5, 8.9, 9.8],
        "roic_goodwill_pct": 18.4,  # ROE of 18.4% (Historic high across Asia-Pacific)
        "goodwill_b": 4.1,
        "dupont_margin_pct": 48.2,
        "dupont_turnover_x": 0.030,
        "dupont_leverage_x": 12.70,
        "current_ratio": 1.42,  # LCR 142% MAS Singapore
        "cash_after_annual_exp_positive": True,
        "cash_b": 82.0,
        "interest_coverage_x": 9.4,
        "debt_to_ebitda": 0.0,
        "debt_to_assets_pct": 8.5,
        "debt_to_equity_pct": 108.0,
        "altman_z": 3.85,  # CET1 Ratio 15.2% (Rating AA- / Aa1)
        "sss_retail": "N/A (Asian Bank — Wealth Management Fees +32% YoY, AUM SGD 390B)",
        "cagrs": {
            "Revenue": {"3y": 14.5, "5y": 9.8, "10y": 8.4},
            "Gross Profit": {"3y": 14.5, "5y": 9.8, "10y": 8.4},
            "EBIT": {"3y": 18.2, "5y": 12.6, "10y": 10.2},
            "EBITDA": {"3y": 18.2, "5y": 12.6, "10y": 10.2},
            "NOPAT": {"3y": 17.8, "5y": 12.4, "10y": 10.5},
            "Net Income": {"3y": 17.8, "5y": 12.4, "10y": 10.5},
            "CFO": {"3y": 16.5, "5y": 11.8, "10y": 9.8},
            "FCF": {"3y": 16.2, "5y": 11.5, "10y": 9.6},
            "EPS": {"3y": 17.5, "5y": 12.2, "10y": 10.1},
            "Dividends": {"3y": 21.0, "5y": 13.5, "10y": 12.8},
            "Book Value": {"3y": 6.4, "5y": 5.8, "10y": 5.9},
            "ROIC": {"3y": 11.2, "5y": 7.5, "10y": 5.8},
        },
        "fcf_b": 8.4,
        "maint_capex_b": 0.6,
        "da_b": 0.8,
        "delta_nwc_b": 0.0,
        "pe_curr": 10.2,
        "pe_ntm": 10.0,
        "pe_sector": 10.5,
        "pe_5y_avg": 10.8,
        "ev_ebitda_curr": 8.0,
        "ev_ebitda_sector": 8.5,
        "ev_ebit_ntm": 8.2,
        "ev_fcf_ntm": 10.0,
        "pb_curr": 1.72,
        "ptbv_curr": 1.88,
        "eps_growth_ntm_pct": 6.5,
        "consensus_g_fund_pct": 7.5,
        "retention_rate": 0.45,
        "div_yield_pct": 5.85,
        "buyback_yield_pct": 1.25,
        "sotp_segments": [
            {"segment": "Institutional Banking & Global Treasury (Singapore/Asia)", "rev_share_pct": 46.0, "peer_benchmark": "AAA Sovereign Asian Bank (1.75x P/TBV)", "segment_val_per_share": 54.0},
            {"segment": "Consumer Banking & Asian Private Wealth Hub", "rev_share_pct": 45.0, "peer_benchmark": "High-ROE Wealth Franchise (2.25x P/TBV)", "segment_val_per_share": 61.0},
            {"segment": "Digital Assets & Excess Capital Return Program", "rev_share_pct": 9.0, "peer_benchmark": "SGD 3B Buyback & Capital Return", "segment_val_per_share": 11.0},
        ],
        "roic_op_margin_pct": 58.5,
        "roic_cap_turnover_x": 0.31,
        "roic_pillar": "Cost-to-Income Ratio of 39% (Full Digitalization) + Strong Currency Deposits (SGD) + ROE 18.4%",
        "rd_to_sales_pct": 6.5,
        "ltv_cac": 14.0,
        "gm_5y_series": [56.0, 57.5, 59.2, 60.8, 61.4],
        "gm_trend_status": "Expansion (+5.4 pp in 5y — Massive inflow of global family offices and wealth into Singapore)",
        "moat_type": "Wide Moat (3 Pillars: CASA Deposit Monopoly in Singapore, Wealth Management Scale, Digital Cost Advantage)",
        "porter": "Rivalry: Low (Rational tripartite oligopoly in Singapore: DBS, OCBC, UOB) | Suppliers: Nil | Customers: Low | Substitutes: Low | New Entrants: Nil (MAS)",
        "ceo_skin": "Temasek Holdings (Singapore AAA Sovereign Wealth Fund) anchor shareholder with 29% stake; Management fully aligned",
        "capital_alloc": "Exemplary: ~5.85% annual dividend yield paid quarterly + SGD 3 billion share buyback program to return excess capital",
        "tag_along": "100% Minority Shareholder Protection under SGX / Monetary Authority of Singapore (MAS) regulation",
        "country_liquidity_risk": "Singapore — AAA Sovereign Rating (Asia's only triple-A sovereign across all rating agencies; Ultra-strong Singapore Dollar)",
        "common_size_vs_peers": "ROE 18.4% (vs OCBC 14.2%, UOB 13.8%, HSBC 14.5%) | Cost-to-Income 39.0% (Best banking efficiency in Asia)",
    },
    "ASML": {
        "name": "ASML Holding N.V.",
        "sector_vertical": "TECH_HIGH_GROWTH",
        "sector_label": "Semiconductor Equipment Monopoly (EUV Lithography)",
        "default_px": 745.00,
        "mcap_b": 295.0,
        "ev_b": 292.0,
        "beta": 1.18,
        "sloan_pct": -11.2,
        "fco_b": 11.2,
        "fci_b": -2.5,
        "ebitda_b": 10.6,
        "ebit_b": 9.8,
        "net_income_b": 8.4,
        "nopat_b": 8.2,
        "total_assets_b": 45.0,
        "nwc_b": 6.8,
        "fco_5y_history_b": [6.5, 8.9, 8.2, 9.4, 11.2],
        "roic_goodwill_pct": 44.5,
        "goodwill_b": 5.1,
        "dupont_margin_pct": 28.5,
        "dupont_turnover_x": 0.68,
        "dupont_leverage_x": 2.90,
        "current_ratio": 1.58,
        "cash_after_annual_exp_positive": True,
        "cash_b": 8.2,
        "interest_coverage_x": 34.0,
        "debt_to_ebitda": 0.50,
        "debt_to_assets_pct": 11.8,
        "debt_to_equity_pct": 34.2,
        "altman_z": 8.60,
        "sss_retail": "N/A (Backlog contratado EUR 36B em sistemas EUV/High-NA)",
        "cagrs": {
            "Revenue": {"3y": 14.2, "5y": 18.5, "10y": 16.8},
            "Gross Profit": {"3y": 15.1, "5y": 20.2, "10y": 18.1},
            "EBIT": {"3y": 16.5, "5y": 23.4, "10y": 20.5},
            "EBITDA": {"3y": 16.0, "5y": 22.8, "10y": 19.9},
            "NOPAT": {"3y": 16.2, "5y": 23.0, "10y": 20.1},
            "Net Income": {"3y": 15.8, "5y": 23.6, "10y": 20.8},
            "CFO": {"3y": 14.5, "5y": 21.0, "10y": 19.2},
            "FCF": {"3y": 14.9, "5y": 22.1, "10y": 19.8},
            "EPS": {"3y": 17.2, "5y": 25.1, "10y": 22.3},
            "Dividends": {"3y": 12.0, "5y": 18.5, "10y": 21.0},
            "Book Value": {"3y": 8.5, "5y": 6.2, "10y": 7.4},
            "ROIC": {"3y": 9.8, "5y": 14.2, "10y": 12.5},
        },
        "fcf_b": 8.8,
        "maint_capex_b": 1.2,
        "da_b": 0.95,
        "delta_nwc_b": 0.8,
        "pe_curr": 35.1,
        "pe_ntm": 27.2,
        "pe_sector": 32.0,
        "pe_5y_avg": 38.0,
        "ev_ebitda_curr": 27.5,
        "ev_ebitda_sector": 25.0,
        "ev_ebit_ntm": 24.5,
        "ev_fcf_ntm": 27.8,
        "pb_curr": 18.2,
        "ptbv_curr": 23.8,
        "eps_growth_ntm_pct": 21.5,
        "consensus_g_fund_pct": 19.5,
        "retention_rate": 0.72,
        "div_yield_pct": 0.95,
        "buyback_yield_pct": 1.35,
        "sotp_segments": [
            {"segment": "EUV & High-NA EUV Systems (100% Monopoly)", "rev_share_pct": 54.0, "peer_benchmark": "Unique Global Monopoly (32x EV/EBIT)", "segment_val_per_share": 475.0},
            {"segment": "DUV Immersion Systems (ArFi)", "rev_share_pct": 24.0, "peer_benchmark": "Semi CapEx Leaders (22x EV/EBIT)", "segment_val_per_share": 190.0},
            {"segment": "Installed Base Management & Services", "rev_share_pct": 22.0, "peer_benchmark": "Industrial Mission-Critical SaaS (28x EV/EBIT)", "segment_val_per_share": 170.0},
        ],
        "roic_op_margin_pct": 33.2,
        "roic_cap_turnover_x": 1.34,
        "roic_pillar": "Absolute Technological Monopoly in EUV Lithography (100% Global Market Share)",
        "rd_to_sales_pct": 14.5,
        "ltv_cac": 25.0,
        "gm_5y_series": [48.6, 52.7, 50.5, 51.3, 51.8],
        "gm_trend_status": "Expansion (+3.2 pp in 5y — High-NA EUV Transition)",
        "moat_type": "Wide Moat (30 Years R&D Lead, Exclusive Zeiss Optics, Infinite Switching Cost)",
        "porter": "Rivalry: Nil | Suppliers: Symbiotic Zeiss | Customers: Concentrated (TSMC, Samsung, Intel) | Substitutes: Non-Existent | New Entrants: Impossible",
        "ceo_skin": "Christophe Fouquet (CEO) compensated on ROIC and Gross Margin expansion",
        "capital_alloc": "Excellent: EUR 4B/year in R&D + unbroken growing dividends and disciplined share repurchases",
        "tag_along": "100% Protection Euronext Amsterdam / ADR SEC Form 20-F",
        "country_liquidity_risk": "Netherlands / EU (AAA) — Monitoring Western export controls on DUV tools to China",
        "common_size_vs_peers": "Gross Margin 51.8% (vs Applied Materials 47.5%) | ROIC 44.5% global sector leader",
    },
    "TSM": {
        "name": "Taiwan Semiconductor (TSMC)",
        "sector_vertical": "TECH_HIGH_GROWTH",
        "sector_label": "Semiconductor Foundry Monopoly (3nm/2nm & CoWoS Packaging)",
        "default_px": 192.00,
        "mcap_b": 995.0,
        "ev_b": 980.0,
        "beta": 1.25,
        "sloan_pct": -10.6,
        "fco_b": 42.5,
        "fci_b": -28.0,
        "ebitda_b": 51.2,
        "ebit_b": 38.6,
        "net_income_b": 33.5,
        "nopat_b": 32.0,
        "total_assets_b": 195.0,
        "nwc_b": 18.2,
        "fco_5y_history_b": [26.0, 31.5, 34.2, 38.0, 42.5],
        "roic_goodwill_pct": 31.8,
        "goodwill_b": 1.2,
        "dupont_margin_pct": 39.5,
        "dupont_turnover_x": 0.48,
        "dupont_leverage_x": 1.68,
        "current_ratio": 2.35,
        "cash_after_annual_exp_positive": True,
        "cash_b": 48.0,
        "interest_coverage_x": 42.0,
        "debt_to_ebitda": 0.48,
        "debt_to_assets_pct": 13.5,
        "debt_to_equity_pct": 22.8,
        "altman_z": 7.95,
        "sss_retail": "N/A (Leading-Edge Sub-5nm Fab Utilization >100%)",
        "cagrs": {
            "Revenue": {"3y": 18.5, "5y": 21.4, "10y": 17.5},
            "Gross Profit": {"3y": 20.2, "5y": 23.8, "10y": 19.2},
            "EBIT": {"3y": 19.8, "5y": 24.5, "10y": 19.8},
            "EBITDA": {"3y": 19.5, "5y": 24.0, "10y": 19.5},
            "NOPAT": {"3y": 19.4, "5y": 24.2, "10y": 19.6},
            "Net Income": {"3y": 18.9, "5y": 23.9, "10y": 19.4},
            "CFO": {"3y": 16.5, "5y": 22.0, "10y": 18.2},
            "FCF": {"3y": 15.2, "5y": 19.8, "10y": 16.5},
            "EPS": {"3y": 20.5, "5y": 25.2, "10y": 20.8},
            "Dividends": {"3y": 10.5, "5y": 12.8, "10y": 14.5},
            "Book Value": {"3y": 16.2, "5y": 18.4, "10y": 16.8},
            "ROIC": {"3y": 12.5, "5y": 15.8, "10y": 14.2},
        },
        "fcf_b": 14.5,
        "maint_capex_b": 8.0,
        "da_b": 12.6,
        "delta_nwc_b": 2.4,
        "pe_curr": 29.7,
        "pe_ntm": 22.4,
        "pe_sector": 28.0,
        "pe_5y_avg": 24.5,
        "ev_ebitda_curr": 19.1,
        "ev_ebitda_sector": 21.0,
        "ev_ebit_ntm": 18.2,
        "ev_fcf_ntm": 24.5,
        "pb_curr": 7.2,
        "ptbv_curr": 7.3,
        "eps_growth_ntm_pct": 25.5,
        "consensus_g_fund_pct": 21.0,
        "retention_rate": 0.70,
        "div_yield_pct": 1.25,
        "buyback_yield_pct": 0.50,
        "sotp_segments": [
            {"segment": "Advanced Nodes (3nm, 5nm & 2nm GAA N2)", "rev_share_pct": 69.0, "peer_benchmark": "Advanced Foundry Monopoly (24x EV/EBIT)", "segment_val_per_share": 158.0},
            {"segment": "Advanced Packaging (CoWoS, SoIC, InFO)", "rev_share_pct": 14.0, "peer_benchmark": "AI Hardware Bottleneck (28x EV/EBIT)", "segment_val_per_share": 42.0},
            {"segment": "Specialty & Mature Nodes (Automotive/IoT)", "rev_share_pct": 17.0, "peer_benchmark": "Legacy Foundry (14x EV/EBIT)", "segment_val_per_share": 28.0},
        ],
        "roic_op_margin_pct": 43.5,
        "roic_cap_turnover_x": 0.73,
        "roic_pillar": "Monopolistic Advanced Node AI Foundry (90%+ of all global AI chips manufactured)",
        "rd_to_sales_pct": 8.5,
        "ltv_cac": 22.0,
        "gm_5y_series": [51.3, 53.1, 54.4, 53.0, 57.8],
        "gm_trend_status": "Expansion (+6.5 pp in 5y — 3nm and N2 nodes with extreme monopolistic pricing power)",
        "moat_type": "Wide Moat (Unmatched Decades-Long Learning Curve, Open Innovation Platform OIP Ecosystem, 99%+ CoWoS Advanced Packaging Yields)",
        "porter": "Rivalry: Nil in leading-edge sub-3nm nodes | Suppliers: Symbiotic relationship with ASML | Customers: Low (Apple, Nvidia, AMD, Qualcomm competing for allocation) | Substitutes: Non-Existent | New Entrants: Impossible ($20B+ fab capex barrier)",
        "ceo_skin": "C.C. Wei (CEO/Chairman) with compensation closely aligned to global geographic expansion milestones and sustained >20% ROE",
        "capital_alloc": "Disciplined Sovereign-Scale Capex: ~$30B/year fully self-funded from operating cash flows, maintaining pristine net cash balance sheet",
        "tag_along": "100% Taiwan Stock Exchange Fiduciary Protection + New York Stock Exchange ADR SEC Form 20-F Compliance",
        "country_liquidity_risk": "Taiwan (Geopolitical Taiwan Strait risk; actively hedged via geographic diversification into Japan Fab Kumamoto, US Fab Arizona, and Germany Dresden)",
        "common_size_vs_peers": "Operating Margin 43.5% (vs Samsung Foundry 2.0%, Intel Foundry Operating Losses) | Global Advanced Node Foundry Market Share >90%",
    },
    "MELI": {
        "name": "MercadoLibre, Inc.",
        "sector_vertical": "TECH_HIGH_GROWTH",
        "sector_label": "E-Commerce, Fintech & Logistics Platform Monopoly in Latin America",
        "default_px": 1980.00,
        "mcap_b": 100.2,
        "ev_b": 102.5,
        "beta": 1.38,
        "sloan_pct": -12.4,
        "fco_b": 4.8,
        "fci_b": -1.1,
        "ebitda_b": 3.6,
        "ebit_b": 2.8,
        "net_income_b": 1.8,
        "nopat_b": 2.2,
        "total_assets_b": 19.5,
        "nwc_b": 1.5,
        "fco_5y_history_b": [1.2, 2.1, 2.9, 3.8, 4.8],
        "roic_goodwill_pct": 29.4,
        "goodwill_b": 0.8,
        "dupont_margin_pct": 10.5,
        "dupont_turnover_x": 0.88,
        "dupont_leverage_x": 3.18,
        "current_ratio": 1.36,
        "cash_after_annual_exp_positive": True,
        "cash_b": 4.2,
        "interest_coverage_x": 14.8,
        "debt_to_ebitda": 1.45,
        "debt_to_assets_pct": 26.5,
        "debt_to_equity_pct": 85.0,
        "altman_z": 4.45,
        "sss_retail": "+28.5% (E-Commerce Gross Merchandise Volume YoY in Constant Currency)",
        "cagrs": {
            "Revenue": {"3y": 32.5, "5y": 42.0, "10y": 36.5},
            "Gross Profit": {"3y": 35.0, "5y": 44.5, "10y": 38.2},
            "EBIT": {"3y": 48.0, "5y": 65.0, "10y": 45.0},
            "EBITDA": {"3y": 46.5, "5y": 62.0, "10y": 43.5},
            "NOPAT": {"3y": 47.0, "5y": 63.5, "10y": 44.0},
            "Net Income": {"3y": 52.0, "5y": 72.0, "10y": 48.0},
            "CFO": {"3y": 38.0, "5y": 55.0, "10y": 40.0},
            "FCF": {"3y": 42.0, "5y": 58.0, "10y": 42.0},
            "EPS": {"3y": 50.5, "5y": 70.0, "10y": 46.5},
            "Dividends": {"3y": 0.0, "5y": 0.0, "10y": 0.0},
            "Book Value": {"3y": 34.0, "5y": 45.0, "10y": 32.0},
            "ROIC": {"3y": 18.5, "5y": 24.0, "10y": 19.5},
        },
        "fcf_b": 3.7,
        "maint_capex_b": 0.45,
        "da_b": 0.80,
        "delta_nwc_b": 0.35,
        "pe_curr": 55.6,
        "pe_ntm": 38.5,
        "pe_sector": 35.0,
        "pe_5y_avg": 65.0,
        "ev_ebitda_curr": 28.5,
        "ev_ebitda_sector": 22.0,
        "ev_ebit_ntm": 26.2,
        "ev_fcf_ntm": 27.5,
        "pb_curr": 20.5,
        "ptbv_curr": 24.8,
        "eps_growth_ntm_pct": 34.0,
        "consensus_g_fund_pct": 26.5,
        "retention_rate": 0.95,
        "div_yield_pct": 0.00,
        "buyback_yield_pct": 0.80,
        "sotp_segments": [
            {"segment": "Mercado Livre Marketplace & Ads", "rev_share_pct": 58.0, "peer_benchmark": "High-Growth E-Commerce & Ads (30x EV/EBIT)", "segment_val_per_share": 1380.0},
            {"segment": "Mercado Pago Fintech (Credit, Cards & Payments)", "rev_share_pct": 42.0, "peer_benchmark": "LatAm Fintech Leader (25x EV/EBIT)", "segment_val_per_share": 860.0},
        ],
        "roic_op_margin_pct": 16.5,
        "roic_cap_turnover_x": 1.78,
        "roic_pillar": "Triple-Lock Cross-Network Effects: #1 E-Commerce Marketplace + #1 Latin American Fintech (Mercado Pago) + Proprietary Managed Logistics (Mercado Envíos)",
        "rd_to_sales_pct": 9.2,
        "ltv_cac": 16.5,
        "gm_5y_series": [46.8, 50.1, 52.4, 53.5, 54.2],
        "gm_trend_status": "Continuous Expansion (+7.4 pp in 5y — Rapidly Scaling High-Margin Advertising and Financial Credit Products)",
        "moat_type": "Wide Moat (Unassailable Regional Logistics Network in Brazil/Mexico/Argentina, Billion-Dollar Two-Sided Network Effect, Deep Fintech Sticky Moat)",
        "porter": "Rivalry: Low (Clear market share leader distancing regional competitors) | Suppliers: Low | Customers: Low (High switching costs into Mercado Pago ecosystem) | Substitutes: Low | New Entrants: Nil",
        "ceo_skin": "Marcos Galperin (Founder) holds substantial personal net worth concentrated in MELI equity, actively guiding long-term vision",
        "capital_alloc": "Exemplary Reinvestment Engine: Prudent proprietary credit book expansion with disciplined NPL controls + dense fulfillment warehouse rollout",
        "tag_along": "100% Delaware Fiduciary Protection / Nasdaq Global Select Market Oversight",
        "country_liquidity_risk": "Latin America (FX volatility in BRL/MXN/ARS effectively hedged through local market pricing power and triple-digit inflation pass-through)",
        "common_size_vs_peers": "Net Revenue Growth 35% YoY (vs Amazon 11%) | Rapidly expanding EBIT margin from negative to >15%",
    },
    "AVGO": {
        "name": "Broadcom Inc.",
        "sector_vertical": "TECH_HIGH_GROWTH",
        "sector_label": "Semiconductors, Custom AI Silicon & VMware Enterprise Software",
        "default_px": 176.00,
        "mcap_b": 825.0,
        "ev_b": 885.0,
        "beta": 1.22,
        "sloan_pct": -8.4,
        "fco_b": 22.5,
        "fci_b": -2.2,
        "ebitda_b": 28.5,
        "ebit_b": 21.6,
        "net_income_b": 16.8,
        "nopat_b": 19.5,
        "total_assets_b": 168.0,
        "nwc_b": 4.5,
        "fco_5y_history_b": [13.2, 16.5, 18.1, 19.8, 22.5],
        "roic_goodwill_pct": 24.8,
        "goodwill_b": 68.0,
        "dupont_margin_pct": 32.5,
        "dupont_turnover_x": 0.31,
        "dupont_leverage_x": 2.45,
        "current_ratio": 1.22,
        "cash_after_annual_exp_positive": True,
        "cash_b": 10.5,
        "interest_coverage_x": 7.8,
        "debt_to_ebitda": 2.45,
        "debt_to_assets_pct": 41.5,
        "debt_to_equity_pct": 102.0,
        "altman_z": 4.12,
        "sss_retail": "N/A (AI Datacenter Semiconductor Revenue Growing >300% YoY for Hyperscale Custom Silicon)",
        "cagrs": {
            "Revenue": {"3y": 21.5, "5y": 24.0, "10y": 28.5},
            "Gross Profit": {"3y": 23.0, "5y": 26.5, "10y": 30.0},
            "EBIT": {"3y": 25.5, "5y": 29.0, "10y": 32.0},
            "EBITDA": {"3y": 24.8, "5y": 28.5, "10y": 31.5},
            "NOPAT": {"3y": 25.0, "5y": 28.8, "10y": 31.8},
            "Net Income": {"3y": 26.2, "5y": 30.5, "10y": 33.2},
            "CFO": {"3y": 20.5, "5y": 25.0, "10y": 29.0},
            "FCF": {"3y": 21.8, "5y": 26.2, "10y": 30.5},
            "EPS": {"3y": 24.0, "5y": 28.0, "10y": 31.0},
            "Dividends": {"3y": 14.5, "5y": 18.2, "10y": 34.0},
            "Book Value": {"3y": 22.0, "5y": 25.5, "10y": 28.0},
            "ROIC": {"3y": 12.0, "5y": 15.5, "10y": 14.8},
        },
        "fcf_b": 20.3,
        "maint_capex_b": 1.8,
        "da_b": 6.9,
        "delta_nwc_b": 0.4,
        "pe_curr": 49.1,
        "pe_ntm": 28.2,
        "pe_sector": 28.0,
        "pe_5y_avg": 26.5,
        "ev_ebitda_curr": 31.0,
        "ev_ebitda_sector": 21.0,
        "ev_ebit_ntm": 24.8,
        "ev_fcf_ntm": 26.5,
        "pb_curr": 11.5,
        "ptbv_curr": 32.0,
        "eps_growth_ntm_pct": 24.0,
        "consensus_g_fund_pct": 18.5,
        "retention_rate": 0.55,
        "div_yield_pct": 1.25,
        "buyback_yield_pct": 1.85,
        "sotp_segments": [
            {"segment": "Semiconductor Solutions (Custom AI ASICs & Tomahawk)", "rev_share_pct": 58.0, "peer_benchmark": "AI Silicon & Switch Monopoly (30x EV/EBIT)", "segment_val_per_share": 118.0},
            {"segment": "Infrastructure Software (VMware Cloud Foundation)", "rev_share_pct": 42.0, "peer_benchmark": "Enterprise Mission-Critical SaaS (25x EV/EBIT)", "segment_val_per_share": 78.0},
        ],
        "roic_op_margin_pct": 60.5,
        "roic_cap_turnover_x": 0.41,
        "roic_pillar": "Monopoly in AI Datacenter Networking Silicon (Tomahawk 5 / Jericho 3-AI) + Proprietary Custom ASIC Accelerators for Cloud Hyperscalers (Google TPU, Meta MTIA)",
        "rd_to_sales_pct": 10.5,
        "ltv_cac": 20.0,
        "gm_5y_series": [73.5, 74.8, 75.2, 74.1, 76.8],
        "gm_trend_status": "Structural Margin Expansion (+3.3 pp in 5y — Rapid Transition of VMware Enterprise Software into High-Margin VCF Subscriptions)",
        "moat_type": "Wide Moat (Insurmountable Enterprise Switching Costs in VMware Infrastructure Software & Mission-Critical Datacenter Switches)",
        "porter": "Rivalry: Low | Suppliers: TSMC priority allocation | Customers: Cloud Hyperscalers (Google, Meta, Apple, Microsoft) | Substitutes: Nil | New Entrants: Nil",
        "ceo_skin": "Hock Tan (CEO) universally recognized as the semiconductor and enterprise software industry's premier M&A capital allocator",
        "capital_alloc": "Legendary Capital Track Record: Rapid post-VMware debt paydown + 13 consecutive years of double-digit dividend growth + High FCF conversion (>45%)",
        "tag_along": "100% Delaware Protection / Nasdaq Global Select Oversight",
        "country_liquidity_risk": "United States — Level 1 Sovereign Liquidity (Technology leader generating >$20B in annual Free Cash Flow)",
        "common_size_vs_peers": "EBITDA Margin 60.5% (Substantially superior to traditional semiconductor and enterprise software medians)",
    },
    "MA": {
        "name": "Mastercard Incorporated",
        "sector_vertical": "FINANCIAL_TOLLBOOTH",
        "sector_label": "Global Payment Rails Duopoly & Cyber Intelligence Services",
        "default_px": 512.00,
        "mcap_b": 472.0,
        "ev_b": 478.0,
        "beta": 1.02,
        "sloan_pct": -11.8,
        "fco_b": 13.8,
        "fci_b": -0.9,
        "ebitda_b": 15.6,
        "ebit_b": 14.8,
        "net_income_b": 12.2,
        "nopat_b": 12.0,
        "total_assets_b": 44.0,
        "nwc_b": 2.1,
        "fco_5y_history_b": [8.5, 10.2, 11.1, 12.4, 13.8],
        "roic_goodwill_pct": 58.2,
        "goodwill_b": 6.8,
        "dupont_margin_pct": 46.5,
        "dupont_turnover_x": 0.65,
        "dupont_leverage_x": 6.80,
        "current_ratio": 1.18,
        "cash_after_annual_exp_positive": True,
        "cash_b": 9.2,
        "interest_coverage_x": 36.5,
        "debt_to_ebitda": 0.98,
        "debt_to_assets_pct": 34.5,
        "debt_to_equity_pct": 235.0,
        "altman_z": 11.50,
        "sss_retail": "+11.0% (Gross Dollar Volume Growth YoY in Constant Currency)",
        "cagrs": {
            "Revenue": {"3y": 14.5, "5y": 16.0, "10y": 13.8},
            "Gross Profit": {"3y": 14.5, "5y": 16.0, "10y": 13.8},
            "EBIT": {"3y": 15.2, "5y": 16.8, "10y": 14.2},
            "EBITDA": {"3y": 15.0, "5y": 16.5, "10y": 14.0},
            "NOPAT": {"3y": 15.1, "5y": 16.6, "10y": 14.1},
            "Net Income": {"3y": 15.8, "5y": 17.2, "10y": 14.5},
            "CFO": {"3y": 14.8, "5y": 16.2, "10y": 14.0},
            "FCF": {"3y": 15.0, "5y": 16.5, "10y": 14.2},
            "EPS": {"3y": 17.5, "5y": 19.0, "10y": 16.8},
            "Dividends": {"3y": 16.2, "5y": 17.5, "10y": 19.5},
            "Book Value": {"3y": 12.0, "5y": 8.5, "10y": 9.2},
            "ROIC": {"3y": 14.0, "5y": 16.5, "10y": 15.0},
        },
        "fcf_b": 12.9,
        "maint_capex_b": 0.45,
        "da_b": 0.80,
        "delta_nwc_b": 0.45,
        "pe_curr": 38.6,
        "pe_ntm": 29.5,
        "pe_sector": 28.0,
        "pe_5y_avg": 34.0,
        "ev_ebitda_curr": 30.6,
        "ev_ebitda_sector": 21.0,
        "ev_ebit_ntm": 26.5,
        "ev_fcf_ntm": 28.2,
        "pb_curr": 68.0,
        "ptbv_curr": 85.0,
        "eps_growth_ntm_pct": 16.5,
        "consensus_g_fund_pct": 15.2,
        "retention_rate": 0.78,
        "div_yield_pct": 0.55,
        "buyback_yield_pct": 2.15,
        "sotp_segments": [
            {"segment": "Core Payment Network Rails (Switched Transactions)", "rev_share_pct": 65.0, "peer_benchmark": "Global Tollbooth Monopoly (32x EV/EBIT)", "segment_val_per_share": 365.0},
            {"segment": "Value-Added Services & Cyber Security Intelligence", "rev_share_pct": 35.0, "peer_benchmark": "CyberSecurity / Data Intelligence (34x EV/EBIT)", "segment_val_per_share": 195.0},
        ],
        "roic_op_margin_pct": 58.2,
        "roic_cap_turnover_x": 1.25,
        "roic_pillar": "Unshakable Global Financial Tollbooth: >3.4B active cards, 150M+ acceptance locations, Zero Credit Risk",
        "rd_to_sales_pct": 5.8,
        "ltv_cac": 28.0,
        "gm_5y_series": [78.2, 79.5, 80.1, 80.8, 81.2],
        "gm_trend_status": "Gold-Standard Margin Stability (~81% — Rational Global Duopoly with Visa with Zero Price Competition)",
        "moat_type": "Wide Moat (Bilateral Two-Sided Network Effects connecting global issuing banks, merchants, and sovereign cardholders)",
        "porter": "Rivalry: Low (Rational, disciplined duopoly with Visa) | Suppliers: Nil | Customers: Low | Substitutes: Very Low | New Entrants: Impossible",
        "ceo_skin": "Michael Miebach (CEO) and executive leadership compensated on long-term EPS CAGR and ROIC performance criteria",
        "capital_alloc": "Prudent Shareholder Payouts: Near 100% of Free Cash Flow returned to shareholders via regular share buybacks and unbroken dividend hikes",
        "tag_along": "100% Delaware Protection / NYSE Fiduciary Oversight",
        "country_liquidity_risk": "United States — Zero Sovereign Risk (Global payment clearing volume indexed to personal consumption across 200+ countries)",
        "common_size_vs_peers": "Operating Margin 58.2% (vs Visa 66.8%, PayPal 17.5%) | Peerless return on invested capital (>55%)",
    },
    "NU": {
        "name": "Nu Holdings Ltd. (Nubank)",
        "sector_vertical": "FINANCIAL_BANK",
        "sector_label": "Fintech / Digital Banking & Financial Platform Monopoly",
        "default_px": 14.20,
        "mcap_b": 68.5,
        "ev_b": 68.5,
        "beta": 1.15,
        "sloan_pct": -13.1,
        "fco_b": 4.2,
        "fci_b": -0.4,
        "ebitda_b": 2.8,
        "ebit_b": 2.6,
        "net_income_b": 2.1,
        "nopat_b": 2.1,
        "total_assets_b": 42.0,
        "nwc_b": 0.0,
        "fco_5y_history_b": [0.2, 0.8, 1.8, 3.1, 4.2],
        "roic_goodwill_pct": 31.2,
        "goodwill_b": 0.3,
        "dupont_margin_pct": 26.5,
        "dupont_turnover_x": 0.19,
        "dupont_leverage_x": 6.20,
        "current_ratio": 1.48,
        "cash_after_annual_exp_positive": True,
        "cash_b": 9.5,
        "interest_coverage_x": 28.0,
        "debt_to_ebitda": 0.40,
        "debt_to_assets_pct": 10.2,
        "debt_to_equity_pct": 65.0,
        "altman_z": 3.65,
        "sss_retail": "N/A (Average Revenue Per Active Customer ARPAC growing +25% YoY to $11.00/month)",
        "cagrs": {
            "Revenue": {"3y": 68.0, "5y": 85.0, "10y": 92.0},
            "Gross Profit": {"3y": 75.0, "5y": 92.0, "10y": 98.0},
            "EBIT": {"3y": 95.0, "5y": 120.0, "10y": 110.0},
            "EBITDA": {"3y": 92.0, "5y": 115.0, "10y": 105.0},
            "NOPAT": {"3y": 94.0, "5y": 118.0, "10y": 108.0},
            "Net Income": {"3y": 110.0, "5y": 135.0, "10y": 120.0},
            "CFO": {"3y": 80.0, "5y": 95.0, "10y": 90.0},
            "FCF": {"3y": 82.0, "5y": 98.0, "10y": 92.0},
            "EPS": {"3y": 105.0, "5y": 130.0, "10y": 118.0},
            "Dividends": {"3y": 0.0, "5y": 0.0, "10y": 0.0},
            "Book Value": {"3y": 42.0, "5y": 55.0, "10y": 48.0},
            "ROIC": {"3y": 25.0, "5y": 32.0, "10y": 28.0},
        },
        "fcf_b": 3.8,
        "maint_capex_b": 0.15,
        "da_b": 0.20,
        "delta_nwc_b": 0.25,
        "pe_curr": 32.5,
        "pe_ntm": 20.8,
        "pe_sector": 14.0,
        "pe_5y_avg": 38.0,
        "ev_ebitda_curr": 24.5,
        "ev_ebitda_sector": 12.0,
        "ev_ebit_ntm": 21.0,
        "ev_fcf_ntm": 18.0,
        "pb_curr": 8.5,
        "ptbv_curr": 9.1,
        "eps_growth_ntm_pct": 45.0,
        "consensus_g_fund_pct": 30.0,
        "retention_rate": 0.98,
        "div_yield_pct": 0.00,
        "buyback_yield_pct": 0.00,
        "sotp_segments": [
            {"segment": "Nubank Brazil (Mature Operation ROE > 28%)", "rev_share_pct": 82.0, "peer_benchmark": "High-ROE Digital Banking (18x P/E)", "segment_val_per_share": 12.50},
            {"segment": "Mexico & Colombia Expansion (Deposit Gathering)", "rev_share_pct": 18.0, "peer_benchmark": "Hypergrowth FinTech (25x P/E)", "segment_val_per_share": 4.50},
        ],
        "roic_op_margin_pct": 42.0,
        "roic_cap_turnover_x": 0.74,
        "roic_pillar": "Structural Disruptive Cost Advantage: Cost-to-Serve of USD 0.80/active customer/month vs Latin American Incumbent Banks at USD 12.00+",
        "rd_to_sales_pct": 8.0,
        "ltv_cac": 30.0,
        "gm_5y_series": [32.0, 38.5, 43.2, 45.8, 48.2],
        "gm_trend_status": "Accelerating Margin Expansion (+16.2 pp in 5y — Pure Operating Leverage as ARPAC expands and cost-to-serve remains flat)",
        "moat_type": "Wide Moat (Unbeatable Cost-to-Serve, >110M sticky retail clients, Cost of funding structurally below regional policy rates)",
        "porter": "Rivalry: Low against brick-and-mortar branch-heavy incumbents | Suppliers: Nil | Customers: Low churn | Substitutes: Low | New Entrants: Very Low",
        "ceo_skin": "David Vélez (Founder/CEO) controls >75% of voting rights, maintaining uncompromising long-term alignment with compounding intrinsic value",
        "capital_alloc": "Exemplary Retained Earnings: 100% of net earnings retained to self-fund balance sheet loan expansion with zero shareholder dilution",
        "tag_along": "100% NYSE Class A Governance / SEC Fiduciary Oversight",
        "country_liquidity_risk": "Latin America (Fortress capital adequacy with CET1 Ratio >17% and sticky, granular retail deposit funding)",
        "common_size_vs_peers": "Efficiency Ratio 31.4% (Best in Latin America, vs Incumbent Median 52.0%) | Consolidated ROE 28.5%",
    },
}


# Global bank peer data for mandatory scatter plot: P/TBV vs ROE for Banks
GLOBAL_BANKS_SCATTER_DATA: List[Dict[str, Any]] = [
    {"Ticker": "JPM", "Bank": "JPMorgan Chase & Co. (Portfolio — Money Center Leader)", "ROE_pct": 18.2, "PTBV": 2.48, "PEGY_Fin": 1.24, "PB": 2.02, "Group": "Portfolio"},
    {"Ticker": "NU", "Bank": "Nu Holdings / Nubank (Portfolio — High-ROTE Digital Bank)", "ROE_pct": 28.5, "PTBV": 6.80, "PEGY_Fin": 0.78, "PB": 6.45, "Group": "Portfolio"},
    {"Ticker": "SECTOR-AVG", "Bank": "Global Banking Peer Average (Sector Benchmark)", "ROE_pct": 11.8, "PTBV": 1.35, "PEGY_Fin": 1.32, "PB": 1.15, "Group": "Sector Benchmark"},
]


class EquityEngine:
    def __init__(self, risk_free_rate_pct: float = 4.42) -> None:
        self.rf_pct = risk_free_rate_pct
        self.rf = risk_free_rate_pct / 100.0
        self.erp = 0.0460  # Damodaran Mature Market Equity Risk Premium (4.60%)

    def analyze_portfolio_equities(self, tickers: Optional[List[str]] = None) -> List[EquityFullAnalysis]:
        if tickers is None:
            try:
                import sqlite3
                with sqlite3.connect("portfolio_store.db") as conn:
                    rows = conn.execute("SELECT ticker, category FROM portfolio_assets ORDER BY display_order ASC").fetchall()
                tickers = [
                    r[0] for r in rows
                    if "Crypto" not in r[1] and "ETF" not in r[1] and r[0] in EQUITY_FUNDAMENTAL_KB
                ]
            except Exception:
                tickers = ["NVDA", "AAPL", "MSFT", "JPM", "ASML", "TSM", "MELI", "AVGO", "MA", "NU"]
            if not tickers:
                tickers = ["NVDA", "AAPL", "MSFT", "JPM", "ASML", "TSM", "MELI", "AVGO", "MA", "NU"]

        live_px_map: Dict[str, float] = {}
        try:
            live_px_map = fetch_all_quotes_parallel(tickers)
        except Exception:
            pass

        results: List[EquityFullAnalysis] = []
        for tk in tickers:
            kb = EQUITY_FUNDAMENTAL_KB.get(tk)
            if not kb:
                continue
            px = live_px_map.get(tk, kb["default_px"])
            scale = px / kb["default_px"] if kb["default_px"] > 0 else 1.0
            mcap_b = round(kb["mcap_b"] * scale, 2)
            ev_b = round(kb["ev_b"] * scale, 2)

            # ==================================================================
            # 2.1 FINANCIAL HEALTH AND FORENSIC ACCOUNTING
            # ==================================================================
            # Sloan Ratio: (Net Income - CFO - CFI) / Total Assets
            sloan_pct = kb["sloan_pct"]
            if sloan_pct < -10.0:
                sloan_status = "Optimal (< -10% — Cash Generation exceeds Accrual Net Income)"
            elif sloan_pct <= 10.0:
                sloan_status = "Ok (-10% to +10% — Normal Accruals)"
            else:
                sloan_status = "Warning (> +10% — Elevated Accruals / Aggressive Accounting Alert)"

            fco_ebitda = round(kb["fco_b"] / kb["ebitda_b"], 2) if kb["ebitda_b"] > 0 else 1.0
            if fco_ebitda > 1.0:
                fco_ebitda_status = f"Optimal ({fco_ebitda:.2f}x > 1.0x)"
            elif fco_ebitda >= 0.70:
                fco_ebitda_status = f"Healthy ({fco_ebitda:.2f}x between 0.70x and 1.0x)"
            else:
                fco_ebitda_status = f"Cuidado ({fco_ebitda:.2f}x < 0.70x)"

            # NWC crossed with historical CFO standard deviation / CV
            fco_hist = kb["fco_5y_history_b"]
            fco_std_b = round(float(np.std(fco_hist)), 2)
            fco_cv = round(float(np.std(fco_hist) / np.mean(fco_hist)), 2) if np.mean(fco_hist) > 0 else 0.10
            nwc_b = kb["nwc_b"]
            if kb["sector_vertical"] == "FINANCIAL_BANK":
                nwc_context = "N/A Banking (Regulated by Basel III LCR > 100%)"
            elif nwc_b > 0:
                nwc_context = f"Positivo (USD {nwc_b:+.1f}B > 0) + FCO Consistente (DP: USD {fco_std_b:.1f}B | CV: {fco_cv:.2f})"
            else:
                nwc_context = f"NWC Negativo Eficiente (USD {nwc_b:+.1f}B financiado por fornecedores, validado por FCO ultra-consistente CV={fco_cv:.2f})"

            # CAPM Damodaran WACC para cruzar com ROIC
            beta = kb["beta"]
            crp = 0.0  # US and Singapore have CRP = 0.0% (AAA)
            ke = self.rf + beta * self.erp + crp
            kd_after_tax = (self.rf + 0.011) * (1.0 - 0.21)
            debt_w = min(0.35, (kb["debt_to_assets_pct"] / 100.0) * 0.5)
            eq_w = 1.0 - debt_w
            wacc_pct = round((eq_w * ke + debt_w * kd_after_tax) * 100.0, 2)
            roic_pct = kb["roic_goodwill_pct"]
            roic_wacc_spread = round(roic_pct - wacc_pct, 2)

            # DuPont 3 Pillars: ROE = Net Margin x Asset Turnover x Financial Leverage
            dp_m = kb["dupont_margin_pct"]
            dp_t = kb["dupont_turnover_x"]
            dp_l = kb["dupont_leverage_x"]
            roe_dupont_pct = round((dp_m / 100.0) * dp_t * dp_l * 100.0, 1)
            if kb["sector_vertical"] == "FINANCIAL_BANK":
                dupont_quality = f"Healthy Banking (ROE {roe_dupont_pct:.1f}% supported by Margin {dp_m:.1f}% and Basel Leverage {dp_l:.1f}x)"
            elif dp_l > 4.0 and dp_m > 20.0:
                dupont_quality = f"Operational Efficiency + Buybacks (Margin {dp_m:.1f}% and Turnover {dp_t:.2f}x; Leverage {dp_l:.2f}x due to Book Value reduction via Buybacks)"
            elif dp_l > 4.0:
                dupont_quality = f"WARNING: ROE inflated by excessive Financial Leverage ({dp_l:.2f}x)"
            else:
                dupont_quality = f"Pure Quality: ROE {roe_dupont_pct:.1f}% driven by Net Margin ({dp_m:.1f}%) and Asset Turnover ({dp_t:.2f}x) with conservative leverage ({dp_l:.2f}x)"

            forensic_health = {
                "sloan_ratio_pct": sloan_pct,
                "sloan_reference": "< -10% (Optimal) | -10% to +10% (Ok) | > +10% (Warning)",
                "sloan_verdict": sloan_status,
                "fco_current_b": kb["fco_b"],
                "fci_current_b": kb["fci_b"],
                "fco_5y_history_b": fco_hist,
                "fco_to_ebitda": fco_ebitda,
                "fco_to_ebitda_ref": "> 1.0x (Optimal) | < 0.70x (Caution)",
                "fco_to_ebitda_verdict": fco_ebitda_status,
                "nwc_b": nwc_b,
                "fco_std_b": fco_std_b,
                "fco_cv": fco_cv,
                "nwc_contextual_verdict": nwc_context,
                "roic_goodwill_pct": roic_pct,
                "goodwill_b": kb["goodwill_b"],
                "wacc_pct": wacc_pct,
                "roic_minus_wacc_spread_pp": roic_wacc_spread,
                "roic_gt_wacc": roic_pct > wacc_pct,
                "roe_dupont_pct": roe_dupont_pct,
                "dupont_net_margin_pct": dp_m,
                "dupont_asset_turnover_x": dp_t,
                "dupont_financial_leverage_x": dp_l,
                "dupont_verdict": dupont_quality,
                "current_ratio": kb["current_ratio"],
                "current_ratio_ref": "> 1.0x + Positive Cash Post-Expenses",
                "cash_b": kb["cash_b"],
                "cash_after_annual_exp_positive": kb["cash_after_annual_exp_positive"],
                "interest_coverage_x": kb["interest_coverage_x"],
                "interest_coverage_ref": "> 3.0x (Healthy)",
                "debt_to_ebitda": kb["debt_to_ebitda"],
                "debt_to_assets_pct": kb["debt_to_assets_pct"],
                "debt_to_equity_pct": kb["debt_to_equity_pct"],
                "sss_same_store_sales": kb["sss_retail"],
            }

            # ==================================================================
            # 2.2 MULTI-METHOD VALUATION ENGINE (ALL 8 METHODS SIDE-BY-SIDE)
            # ==================================================================
            # 1) Traditional DCF (Damodaran CAPM + Gordon Growth + Conservative/Base/Optimistic Scenarios + 10% MoS)
            wacc_dec = max(0.068, wacc_pct / 100.0)
            g_term = 0.030
            g_base = min(0.22, kb["consensus_g_fund_pct"] / 100.0)
            g_cons = max(0.05, g_base * 0.78)
            g_opt = min(0.26, g_base * 1.18)

            shares_b = mcap_b / px if px > 0 else 10.0
            # DCF ancorado em dados Forward: Ano 1 parte do FCF Forward NTM = FCF_0 * (1 + g_NTM)
            # projetando os anos subsequentes pelo consenso Forward (consensus_g_fund_pct)
            fcf_ntm_b = round(kb["fcf_b"] * (1.0 + g_base), 2)
            fcf_per_share = kb["fcf_b"] / shares_b if shares_b > 0 else (px * 0.04)

            def _calc_dcf_scenario(g_5y: float, w_adj: float, gt: float) -> float:
                pv = 0.0
                cf = fcf_per_share
                for yr in range(1, 6):
                    cf *= (1.0 + g_5y)
                    pv += cf / ((1.0 + w_adj) ** yr)
                # 5-year additional fade to terminal rate
                for yr in range(6, 11):
                    g_fade = g_5y - ((g_5y - gt) * ((yr - 5) / 5.0))
                    cf *= (1.0 + g_fade)
                    pv += cf / ((1.0 + w_adj) ** yr)
                tv = (cf * (1.0 + gt)) / max(0.025, (w_adj - gt))
                pv_tv = tv / ((1.0 + w_adj) ** 10)
                return round(max(1.0, pv + pv_tv), 2)

            dcf_conservador = _calc_dcf_scenario(g_cons, wacc_dec + 0.005, g_term - 0.005)
            dcf_base = _calc_dcf_scenario(g_base, wacc_dec, g_term)
            dcf_otimista = _calc_dcf_scenario(g_opt, max(0.06, wacc_dec - 0.005), g_term + 0.002)
            dcf_range_mean = round((dcf_conservador + dcf_base + dcf_otimista) / 3.0, 2)
            dcf_fair_mos10 = round(dcf_range_mean * 0.90, 2)  # 10% Margin of Safety

            dcf_note = (
                "METHODOLOGICAL WARNING: Avoid isolated traditional DCF for High-Growth Stocks (prioritize Enterprise PEGY EV/EBIT and SOTP)"
                if kb["sector_vertical"] == "TECH_HIGH_GROWTH"
                else (
                    "SECTORIAL WARNING: For Banks, DCF is only a proxy for DDM; prioritize P/TBV vs ROE and Financial PEGY"
                    if kb["sector_vertical"] == "FINANCIAL_BANK"
                    else "DCF Applicable with verified ROIC > WACC and 10% Margin of Safety on range mean"
                )
            )

            # 2) Reverse DCF (Paired Implied Growth)
            # Solves for g_impl such that DCF(g_impl) == Current Price
            low_g, high_g = -0.05, 0.45
            for _ in range(32):
                mid_g = (low_g + high_g) / 2.0
                val_mid = _calc_dcf_scenario(mid_g, wacc_dec, g_term)
                if val_mid < px:
                    low_g = mid_g
                else:
                    high_g = mid_g
            g_impl_pct = round(((low_g + high_g) / 2.0) * 100.0, 2)
            g_fund_sustainable = round(min(kb["consensus_g_fund_pct"], (roic_pct * kb["retention_rate"]) * 0.65 + kb["consensus_g_fund_pct"] * 0.35), 2)
            g_fund_pct = kb["consensus_g_fund_pct"]
            g_spread_pp = round(g_fund_pct - g_impl_pct, 2)
            g_ratio = round(g_impl_pct / g_fund_pct, 2) if g_fund_pct > 0 else 1.0

            # 3) FCF Yield / Owner Earnings Yield (Charlie Munger Method) vs Risk-Free Rate (US 10Y)
            # Owner Earnings = Net Income + D&A - Maintenance CapEx +/- Delta NWC
            owner_earnings_b = round(kb["net_income_b"] + kb["da_b"] - kb["maint_capex_b"] + kb["delta_nwc_b"], 2)
            owner_earnings_yield_pct = round((owner_earnings_b / mcap_b) * 100.0, 2) if mcap_b > 0 else 4.0
            fcf_yield_pct = round((kb["fcf_b"] / mcap_b) * 100.0, 2) if mcap_b > 0 else 3.8
            oe_gt_rf = owner_earnings_yield_pct > self.rf_pct
            oe_vs_rf_spread = round(owner_earnings_yield_pct - self.rf_pct, 2)

            # 4) Relative Multiples & Ratios (P/E, EV/EBITDA, P/B, P/TBV)
            pe_curr = round(kb["pe_curr"] * scale, 1)
            pe_ntm = round(kb["pe_ntm"] * scale, 1)
            eps_curr = px / pe_curr if pe_curr > 0 else 5.0
            pe_implied_dcf = round(dcf_fair_mos10 / eps_curr, 1) if eps_curr > 0 else 22.0
            ev_ebitda_curr = round(kb["ev_ebitda_curr"] * scale, 1)
            pb_curr = round(kb["pb_curr"] * scale, 2)
            ptbv_curr = round(kb["ptbv_curr"] * scale, 2)

            # 5) EVA (Economic Value Added) = NOPLAT - (Capital Investido * WACC)
            invested_cap_b = round(kb["nopat_b"] / (roic_pct / 100.0), 2) if roic_pct > 0 else (mcap_b * 0.35)
            capital_charge_b = round(invested_cap_b * (wacc_pct / 100.0), 2)
            eva_usd_b = round(kb["nopat_b"] - capital_charge_b, 2)
            eva_pct_ic = round((eva_usd_b / invested_cap_b) * 100.0, 2) if invested_cap_b > 0 else roic_wacc_spread

            # 6) PEG & PEGY Ratios (PEGY Financeiro + Enterprise PEGY EV/EBIT e EV/FCF)
            eps_g_ntm = kb["eps_growth_ntm_pct"]
            div_y = kb["div_yield_pct"]
            bb_y = kb["buyback_yield_pct"]
            total_growth_plus_yield = max(2.0, eps_g_ntm + div_y + bb_y)

            pegy_financeiro = round(pe_ntm / max(2.0, eps_g_ntm + div_y), 2)
            ent_pegy_ebit = round((kb["ev_ebit_ntm"] * scale) / total_growth_plus_yield, 2)
            ent_pegy_fcf = round((kb["ev_fcf_ntm"] * scale) / total_growth_plus_yield, 2)

            if kb["sector_vertical"] == "FINANCIAL_BANK":
                primary_pegy_val = pegy_financeiro
                primary_pegy_label = f"Financial PEGY (NTM P/E ÷ [g_EPS + DY]): {pegy_financeiro:.2f}x"
                primary_pegy_status = "Optimal (0 to 1.0x — Bank)" if pegy_financeiro <= 1.0 else ("Ok (1.0 to 1.5x — Bank)" if pegy_financeiro <= 1.5 else "Expensive (> 1.5x — Bank)")
            elif kb["sector_vertical"] == "TECH_HIGH_GROWTH":
                primary_pegy_val = ent_pegy_ebit
                primary_pegy_label = f"Enterprise PEGY (EV/EBIT NTM): {ent_pegy_ebit:.2f}x"
                primary_pegy_status = "Gold Band (0 to 1.2x — High-Growth)" if ent_pegy_ebit <= 1.2 else ("Neutral (1.2 to 1.6x)" if ent_pegy_ebit <= 1.6 else "Stretched (> 1.6x)")
            elif kb["sector_vertical"] == "RETAIL":
                primary_pegy_val = ent_pegy_ebit
                primary_pegy_label = f"Enterprise PEGY (EV/EBIT NTM c/ SSS): {ent_pegy_ebit:.2f}x"
                primary_pegy_status = "Gold Band (0 to 1.2x — Retail)" if ent_pegy_ebit <= 1.2 else ("Neutral (1.2 to 1.6x)" if ent_pegy_ebit <= 1.6 else "Stretched (> 1.6x)")
            else:
                primary_pegy_val = ent_pegy_fcf
                primary_pegy_label = f"Enterprise PEGY (EV/FCF NTM): {ent_pegy_fcf:.2f}x"
                primary_pegy_status = "Gold Band (0 to 1.2x — Cash Cow)" if ent_pegy_fcf <= 1.2 else ("Neutral (1.2 to 1.6x)" if ent_pegy_fcf <= 1.6 else "Stretched (> 1.6x)")

            # Implied Fair Price at Gold Band PEGY (1.20x for non-financials, 1.00x for banks)
            target_pegy_gold = 1.00 if kb["sector_vertical"] == "FINANCIAL_BANK" else 1.20
            pegy_gold_fair_price = round(px * (target_pegy_gold / max(0.3, primary_pegy_val)), 2)

            # 7) Greenblatt's Magic Formula (ROIC + Earnings Yield EBIT/EV)
            earnings_yield_ebit_ev_pct = round((kb["ebit_b"] / ev_b) * 100.0, 2) if ev_b > 0 else 5.0
            magic_combined_score = round(roic_pct * 0.55 + earnings_yield_ebit_ev_pct * 2.5, 1)
            altman_caution_flag = "Pristine Solvency (Interest Coverage & Liquidity)" if kb["interest_coverage_x"] >= 3.0 else "CAUTION: Check Structural Debt Risk"

            # 8) SOTP (Sum of the Parts) com Peer Analysis
            sotp_fair_price = round(sum(seg["segment_val_per_share"] for seg in kb["sotp_segments"]), 2)
            sotp_upside_pct = round(((sotp_fair_price / px) - 1.0) * 100.0, 1)

            valuation_methods = {
                # 1. DCF
                "wacc_capm_pct": wacc_pct,
                "cost_of_equity_pct": round(ke * 100.0, 2),
                "beta": beta,
                "dcf_conservador_usd": dcf_conservador,
                "dcf_base_usd": dcf_base,
                "dcf_otimista_usd": dcf_otimista,
                "dcf_range_mean_usd": dcf_range_mean,
                "dcf_fair_mos10_usd": dcf_fair_mos10,
                "dcf_upside_pct": round(((dcf_fair_mos10 / px) - 1.0) * 100.0, 1),
                "dcf_methodological_note": dcf_note,
                # 2. Reverse DCF Pareado
                "reverse_dcf_g_impl_pct": g_impl_pct,
                "hist_fcf_cagr_3y_pct": kb["cagrs"]["FCF"]["3y"],
                "hist_fcf_cagr_5y_pct": kb["cagrs"]["FCF"]["5y"],
                "hist_eps_cagr_3y_pct": kb["cagrs"]["EPS"]["3y"],
                "hist_eps_cagr_5y_pct": kb["cagrs"]["EPS"]["5y"],
                "g_fund_projected_pct": g_fund_pct,
                "g_fund_sustainable_roic_rr_pct": g_fund_sustainable,
                "reverse_dcf_spread_pp": g_spread_pp,
                "reverse_dcf_ratio_impl_to_fund": g_ratio,
                "reverse_dcf_verdict": (
                    f"ASSIMETRIA POSITIVA (g_impl {g_impl_pct:.1f}% <= g_fund {g_fund_pct:.1f}%)"
                    if g_impl_pct <= g_fund_pct
                    else f"ELEVATED HURDLE (g_impl {g_impl_pct:.1f}% > g_fund {g_fund_pct:.1f}%)"
                ),
                # 3. FCF Yield / Owner Earnings Yield (Munger)
                "owner_earnings_b": owner_earnings_b,
                "owner_earnings_yield_pct": owner_earnings_yield_pct,
                "fcf_yield_pct": fcf_yield_pct,
                "risk_free_us10y_pct": round(self.rf_pct, 2),
                "oe_vs_rf_spread_pp": oe_vs_rf_spread,
                "oe_gt_rf": oe_gt_rf,
                "oe_verdict": (
                    f"ACIMA DA RISK-FREE ({owner_earnings_yield_pct:.2f}% > US10Y {self.rf_pct:.2f}%)"
                    if oe_gt_rf
                    else f"BELOW RISK-FREE ({owner_earnings_yield_pct:.2f}% < US10Y {self.rf_pct:.2f}% — Return anchored in Growth)"
                ),
                "oe_vs_rf_verdict": (
                    f"ACIMA DA RISK-FREE ({owner_earnings_yield_pct:.2f}% > US10Y {self.rf_pct:.2f}%)"
                    if oe_gt_rf
                    else f"BELOW RISK-FREE ({owner_earnings_yield_pct:.2f}% < US10Y {self.rf_pct:.2f}% — Return anchored in Growth)"
                ),
                # 4. Múltiplos Comparados
                "pe_current": pe_curr,
                "pe_ntm": pe_ntm,
                "pe_sector_avg": kb["pe_sector"],
                "pe_5y_hist_avg": kb["pe_5y_avg"],
                "pe_5y_avg": kb["pe_5y_avg"],
                "pe_implied_dcf": pe_implied_dcf,
                "cyclical_pe_warning": "CYCLICAL SECTORS NOTE: In cyclicals and commodities, valuation multiples invert (low P/E and EV/EBITDA indicate cycle peak / expensive; high multiples indicate cycle trough / attractive).",
                "ev_ebitda_current": ev_ebitda_curr,
                "ev_ebitda_sector_avg": kb["ev_ebitda_sector"],
                "pb_current": pb_curr,
                "ptbv_current": ptbv_curr,
                "pb_structural_ref": "P/B < 1.0x generally signals structural impairment / value destruction (Veto in Banking)",
                # 5. EVA
                "invested_capital_b": invested_cap_b,
                "eva_usd_b": eva_usd_b,
                "eva_pct_of_ic": eva_pct_ic,
                # 6. PEG & PEGY Ratios
                "pegy_financeiro": pegy_financeiro,
                "pegy_financeiro_ref": "0 to 1.0 (Optimal) | 1.0 to 1.5 (Ok) | > 1.5 (Expensive)",
                "enterprise_pegy_ev_ebit": ent_pegy_ebit,
                "enterprise_pegy_ev_fcf": ent_pegy_fcf,
                "enterprise_pegy_ref": "0 a 1.2 (Ouro) | 1.2 a 1.6 (Neutro) | > 1.6 (Alto Risco)",
                "primary_pegy_label": primary_pegy_label,
                "primary_pegy_status": primary_pegy_status,
                "pegy_gold_fair_price_usd": pegy_gold_fair_price,
                "eps_growth_ntm_pct": eps_g_ntm,
                "div_yield_pct": div_y,
                "buyback_yield_pct": bb_y,
                # 7. Greenblatt Magic Formula
                "earnings_yield_ebit_ev_pct": earnings_yield_ebit_ev_pct,
                "magic_combined_score": magic_combined_score,
                "magic_formula_combined_score": magic_combined_score,
                "magic_formula_rank": 0,  # Preenchido após ordenar todos os ativos
                "magic_caution_flag": altman_caution_flag,
                # 8. SOTP
                "sotp_segments": kb["sotp_segments"],
                "sotp_fair_price_usd": sotp_fair_price,
                "sotp_upside_pct": sotp_upside_pct,
            }

            # ==================================================================
            # 2.3 QUALITATIVE, STRATEGIC ANALYSIS & SECTORIAL LENSES
            # ==================================================================
            if kb["sector_vertical"] == "FINANCIAL_BANK":
                sector_lens = (
                    "BANKING & INSURANCE LENS: Analytical priority on P/TBV vs ROE and Financial PEGY. "
                    "WARNING: EV/EBITDA and isolated traditional DCF are distorted by customer deposits and loan-loss provisions; P/B < 1.0x is a veto on structural risk."
                )
            elif kb["sector_vertical"] == "FINANCIAL_TOLLBOOTH":
                sector_lens = (
                    "FINTECH & PAYMENT PROCESSORS LENS: Evaluated as Big Tech / Cash Cow (Zero bank balance sheet credit risk). "
                    "Analytical priority on Enterprise PEGY (NTM EV/FCF), ROIC > 40%, and Operating Margin."
                )
            elif kb["sector_vertical"] == "TECH_HIGH_GROWTH":
                sector_lens = (
                    "HIGH-GROWTH TECH & AI INFRASTRUCTURE LENS: Analytical priority placed on Enterprise PEGY using NTM EV/EBIT (avoids penalizing high-growth expansion capex), "
                    "Paired Reverse DCF vs g_fund and SOTP by business unit."
                )
            elif kb["sector_vertical"] == "TECH_CASH_COW":
                sector_lens = (
                    "BIG TECH CASH COWS & MONOPOLIES LENS: Analytical priority on Enterprise PEGY with NTM EV/FCF (pure free cash flow generation + Buybacks), "
                    "Owner Earnings Yield vs. US 10Y e SOTP."
                )
            elif kb["sector_vertical"] == "RETAIL":
                sector_lens = (
                    "RETAIL & CONSUMER LENS: Analytical priority on Enterprise PEGY (EV/EBIT) strictly paired with SSS (Same Store Sales) "
                    "and organic foot-traffic growth. If SSS is negative, depressed multiples signal a Value Trap."
                )
            else:
                sector_lens = (
                    "INDUSTRIALS & CYCLICAL COMMODITIES LENS: Analytical priority on normalized inverse EV/EBITDA vs historical cycle average, commodity pricing resilience, and mid-cycle DCF."
                )

            qualitative_strategy = {
                "roic_op_margin_pct": kb["roic_op_margin_pct"],
                "roic_cap_turnover_x": kb["roic_cap_turnover_x"],
                "roic_central_pillar": kb["roic_pillar"],
                "rd_to_sales_pct": kb["rd_to_sales_pct"],
                "ltv_to_cac_ratio": kb["ltv_cac"],
                "gross_margin_5y_series": kb["gm_5y_series"],
                "gross_margin_current_pct": kb["gm_5y_series"][-1],
                "gross_margin_5y_delta_pp": round(kb["gm_5y_series"][-1] - kb["gm_5y_series"][0], 1),
                "gross_margin_trend_verdict": kb["gm_trend_status"],
                "gross_margin_5y_status": kb["gm_trend_status"],
                "moat_classification": kb["moat_type"],
                "porter_5_forces": kb["porter"],
                "ceo_skin_in_the_game": kb["ceo_skin"],
                "capital_allocation_history": kb["capital_alloc"],
                "tag_along_governance": kb["tag_along"],
                "country_geopolitical_liquidity_risk": kb["country_liquidity_risk"],
                "common_size_peer_comparison": kb["common_size_vs_peers"],
                "sector_particularity_lens": sector_lens,
            }

            results.append(EquityFullAnalysis(
                ticker=tk,
                company_name=kb["name"],
                sector_vertical=kb["sector_vertical"],
                sector_label=kb["sector_label"],
                currency="USD",
                current_price=round(px, 2),
                market_cap_b=mcap_b,
                enterprise_value_b=ev_b,
                forensic_health=forensic_health,
                cagr_matrix_12_kpis=(lambda c: {
                    **c,
                    "Revenue": c.get("Revenue", c.get("Receita", {"3y": 0.0, "5y": 0.0, "10y": 0.0})),
                    "Gross Profit": c.get("Gross Profit", c.get("Lucro Bruto", {"3y": 0.0, "5y": 0.0, "10y": 0.0})),
                    "Net Income": c.get("Net Income", c.get("Lucro Líquido", {"3y": 0.0, "5y": 0.0, "10y": 0.0})),
                    "CFO": c.get("CFO", c.get("FCO", {"3y": 0.0, "5y": 0.0, "10y": 0.0})),
                    "Dividends": c.get("Dividends", c.get("Dividendos", {"3y": 0.0, "5y": 0.0, "10y": 0.0})),
                    "Revenue": c.get("Receita", c.get("Revenue", {"3y": 0.0, "5y": 0.0, "10y": 0.0})),
                    "Gross Profit": c.get("Lucro Bruto", c.get("Gross Profit", {"3y": 0.0, "5y": 0.0, "10y": 0.0})),
                    "Net Income": c.get("Lucro Líquido", c.get("Net Income", {"3y": 0.0, "5y": 0.0, "10y": 0.0})),
                    "CFO": c.get("FCO", c.get("CFO", {"3y": 0.0, "5y": 0.0, "10y": 0.0})),
                    "Dividends": c.get("Dividendos", c.get("Dividends", {"3y": 0.0, "5y": 0.0, "10y": 0.0})),
                })(kb.get("cagrs", {})),
                valuation_methods=valuation_methods,
                qualitative_strategy=qualitative_strategy,
            ))

        # Calculates official Greenblatt Magic Formula ranking (ROIC Rank + Earnings Yield Rank)
        roic_sorted = sorted(results, key=lambda x: x.forensic_health["roic_goodwill_pct"], reverse=True)
        ey_sorted = sorted(results, key=lambda x: x.valuation_methods["earnings_yield_ebit_ev_pct"], reverse=True)
        rank_sums = {}
        for r in results:
            r_roic = roic_sorted.index(r) + 1
            r_ey = ey_sorted.index(r) + 1
            rank_sums[r.ticker] = r_roic + r_ey

        final_magic_order = sorted(results, key=lambda x: (rank_sums[x.ticker], -x.forensic_health["roic_goodwill_pct"]))
        for idx, item in enumerate(final_magic_order, 1):
            item.valuation_methods["magic_formula_rank"] = idx

        return results

"""
MÓDULO 1 (AÇÕES): ANALISADOR MULTI-MÉTODOS DE EQUITY RESEARCH, SAÚDE FORENSE,
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
    # 2.1 Saúde Financeira e Contabilidade Forense
    forensic_health: Dict[str, Any]
    cagr_matrix_12_kpis: Dict[str, Dict[str, float]]  # 12 KPIs x {3y, 5y, 10y}
    # 2.2 Motor de Valuation Multi-Métodos Lado a Lado
    valuation_methods: Dict[str, Any]
    # 2.3 Qualitativo, Estratégico, Concorrência e Lente Setorial
    qualitative_strategy: Dict[str, Any]

    @property
    def name(self) -> str:
        return self.company_name


# Banco de dados calibrado de referência fundamentalista e histórica 3y/5y/10y das 10 ações da carteira
# (Garante completude de 10 anos mesmo quando a API pública gratuita retorna apenas 4 anos de balanço)
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
        "sss_retail": " +3.2% (Apple Retail Stores Comp)",
        # 12 KPIs CAGRs (3y, 5y, 10y em %)
        "cagrs": {
            "Receita": {"3y": 2.8, "5y": 8.5, "10y": 7.9},
            "Lucro Bruto": {"3y": 5.4, "5y": 12.1, "10y": 9.8},
            "EBIT": {"3y": 4.9, "5y": 13.8, "10y": 9.2},
            "EBITDA": {"3y": 4.6, "5y": 12.9, "10y": 9.1},
            "NOPAT": {"3y": 5.1, "5y": 13.5, "10y": 9.6},
            "Lucro Líquido": {"3y": 3.8, "5y": 12.6, "10y": 9.4},
            "FCO": {"3y": 3.2, "5y": 11.2, "10y": 7.8},
            "FCF": {"3y": 3.9, "5y": 12.8, "10y": 8.5},
            "EPS": {"3y": 6.9, "5y": 16.2, "10y": 13.4},
            "Dividendos": {"3y": 4.8, "5y": 5.6, "10y": 7.9},
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
        "roic_pillar": "Margem Operacional & Giro com Capital de Giro Negativo Eficiente",
        "rd_to_sales_pct": 7.8,
        "ltv_cac": 19.5,
        "gm_5y_series": [38.2, 41.8, 43.3, 44.1, 46.2],
        "gm_trend_status": "Expansão Forte (+8.0 pp em 5a — Ganho de Mix de Services & Silicon Próprio)",
        "moat_type": "Wide Moat (4 Pilares: Ecossistema Fechado iOS, Switching Cost, Marca Global, Efeito de Rede App Store)",
        "porter": "Rivalidade: Moderada | Fornecedores: Baixa (Prioridade TSMC) | Clientes: Muito Baixa (Retenção 92%) | Substitutos: Muito Baixa | Entrantes: Nula",
        "ceo_skin": "Tim Cook (> USD 1.8B em equity) + Remuneração Executiva atrelada a TSR percentil 85 do S&P 500",
        "capital_alloc": "Alocador Padrão-Ouro: > USD 95B/ano em Buybacks reduzindo float em ~38% na década + P&D focado em silício proprietário",
        "tag_along": "100% Tag Along / Proteção Fiduciária Delaware General Corporation Law (SEC)",
        "country_liquidity_risk": "EUA — Liquidez Soberana Nível 1 (Risco de Liquidez Zero; Exposição de Cadeia na Ásia)",
        "common_size_vs_peers": "Margem Bruta 46.2% (vs Setor Hardware 34.0%) | Margem EBIT 31.5% (vs Pares 18.2%) | Ganho contínuo de lucro global de smartphones (>80% profit share)",
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
        "sss_retail": "N/A (Enterprise Cloud / Software B2B — Net Retention > 118%)",
        "cagrs": {
            "Receita": {"3y": 13.4, "5y": 14.3, "10y": 10.9},
            "Lucro Bruto": {"3y": 14.1, "5y": 15.6, "10y": 11.8},
            "EBIT": {"3y": 16.2, "5y": 20.5, "10y": 14.7},
            "EBITDA": {"3y": 16.8, "5y": 19.8, "10y": 14.5},
            "NOPAT": {"3y": 15.9, "5y": 19.4, "10y": 14.6},
            "Lucro Líquido": {"3y": 12.9, "5y": 17.5, "10y": 14.9},
            "FCO": {"3y": 15.5, "5y": 17.8, "10y": 13.9},
            "FCF": {"3y": 9.8, "5y": 14.2, "10y": 11.4},
            "EPS": {"3y": 13.6, "5y": 18.4, "10y": 15.8},
            "Dividendos": {"3y": 10.2, "5y": 10.1, "10y": 9.8},
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
        "roic_pillar": "Margem Operacional de Monopólio B2B (44.6%) + Receita Recorrente Anual",
        "rd_to_sales_pct": 12.0,
        "ltv_cac": 18.2,
        "gm_5y_series": [67.8, 68.9, 68.4, 68.9, 69.8],
        "gm_trend_status": "Estabilidade em Patamar de Elite (~70% — Forte Pricing Power em Copilot/E5)",
        "moat_type": "Wide Moat (4 Pilares: Switching Costs Corporativos Intransponíveis, Efeito de Rede, Escala Azure, Intangíveis)",
        "porter": "Rivalidade: Moderada em Cloud / Nula em Office | Fornecedores: Baixa | Clientes: Muito Baixa (Lock-in de TI) | Substitutos: Muito Baixa | Entrantes: Nula",
        "ceo_skin": "Satya Nadella (> USD 900M em ações) com bônus vinculado a Azure Growth, ROIC e TSR",
        "capital_alloc": "Excelência: Capex em IA/Cloud com backlog contratado > USD 250B + Dividendos crescentes há 20 anos + M&A cirúrgico",
        "tag_along": "100% Tag Along / Proteção Fiduciária SEC",
        "country_liquidity_risk": "EUA — Liquidez Soberana AAA (Maior rating de crédito corporativo do mundo, superior ao Tesouro EUA)",
        "common_size_vs_peers": "Margem Operacional 44.6% (vs Setor Software 26.5%) | Margem Líquida 36.0% (vs Pares 19.0%) | Monopólio B2B Intacto",
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
        "sss_retail": "N/A (Plataforma Digital Global — TAC constante)",
        "cagrs": {
            "Receita": {"3y": 10.8, "5y": 16.2, "10y": 17.8},
            "Lucro Bruto": {"3y": 11.5, "5y": 17.0, "10y": 16.9},
            "EBIT": {"3y": 13.8, "5y": 24.5, "10y": 20.2},
            "EBITDA": {"3y": 13.2, "5y": 22.1, "10y": 19.4},
            "NOPAT": {"3y": 14.0, "5y": 23.8, "10y": 19.9},
            "Lucro Líquido": {"3y": 11.9, "5y": 22.4, "10y": 20.5},
            "FCO": {"3y": 9.4, "5y": 16.8, "10y": 17.9},
            "FCF": {"3y": 4.5, "5y": 17.5, "10y": 18.2},
            "EPS": {"3y": 14.8, "5y": 25.1, "10y": 21.8},
            "Dividendos": {"3y": 100.0, "5y": 100.0, "10y": 100.0},
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
            {"segment": "Waymo Autonomous Driving, Verily & Net Cash", "rev_share_pct": 11.0, "peer_benchmark": "Waymo Valuation + Caixa Líquido USD 78B", "segment_val_per_share": 18.0},
        ],
        "roic_op_margin_pct": 31.4,
        "roic_cap_turnover_x": 1.00,
        "roic_pillar": "Margem Operacional Elevada + Escala de Infraestrutura TPU Própria",
        "rd_to_sales_pct": 13.6,
        "ltv_cac": 16.8,
        "gm_5y_series": [53.6, 56.9, 55.4, 56.6, 58.1],
        "gm_trend_status": "Expansão Sólida (+4.5 pp em 5a — Alavancagem Operacional em Google Cloud e YouTube)",
        "moat_type": "Wide Moat (4 Pilares: Efeito de Rede Search/YouTube/Android, Ativos Intangíveis/Dados, Escala TPU, Custo)",
        "porter": "Rivalidade: Moderada | Fornecedores: Baixa (TPUs próprias) | Clientes: Baixa (Anunciantes pulverizados) | Substitutos: Média (GenAI Search) | Entrantes: Muito Baixa",
        "ceo_skin": "Fundadores (Larry Page & Sergey Brin) detêm > 51% do poder votante e > USD 240B em ações; Sundar Pichai alinhado",
        "capital_alloc": "Forte: USD 62B/ano em recompras de ações + dividendo recém-iniciado + liderança em IA/Waymo",
        "tag_along": "Estrutura Dual-Class (A/B/C) sob jurisdição Delaware / SEC",
        "country_liquidity_risk": "EUA — Liquidez Soberana Nível 1 (Caixa líquido superior a USD 78 bilhões)",
        "common_size_vs_peers": "Margem Bruta 58.1% | Margem EBIT 31.4% (vs Setor Mídia/Tech 22.0%) | Dominância de 89% em Search Global",
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
            "Receita": {"3y": 10.6, "5y": 17.4, "10y": 21.5},
            "Lucro Bruto": {"3y": 15.2, "5y": 21.3, "10y": 26.8},
            "EBIT": {"3y": 37.5, "5y": 34.8, "10y": 48.2},
            "EBITDA": {"3y": 24.8, "5y": 26.1, "10y": 31.4},
            "NOPAT": {"3y": 36.2, "5y": 33.9, "10y": 46.5},
            "Lucro Líquido": {"3y": 18.5, "5y": 35.2, "10y": 44.0},
            "FCO": {"3y": 34.5, "5y": 24.0, "10y": 32.5},
            "FCF": {"3y": 65.0, "5y": 18.5, "10y": 36.2},
            "EPS": {"3y": 17.8, "5y": 34.0, "10y": 42.1},
            "Dividendos": {"3y": 0.0, "5y": 0.0, "10y": 0.0},
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
        "roic_pillar": "Giro Elevado no Varejo + Expansão Acelerada de Margem em AWS (36%) e Ads (>50%)",
        "rd_to_sales_pct": 13.8,
        "ltv_cac": 17.5,
        "gm_5y_series": [39.6, 42.0, 43.8, 47.0, 49.2],
        "gm_trend_status": "Expansão Estrutural (+9.6 pp em 5a — Crescimento de AWS, 3P Marketplace e Publicidade)",
        "moat_type": "Wide Moat (4 Pilares: Vantagem de Custo Logístico, Efeito de Rede Marketplace/Prime, Switching Cost AWS, Marca)",
        "porter": "Rivalidade: Moderada | Fornecedores: Muito Baixa (Milhões de sellers 3P) | Clientes: Baixa (Retenção Prime 98%) | Substitutos: Baixa | Entrantes: Muito Baixa",
        "ceo_skin": "Jeff Bezos detém ~9% da empresa (> USD 195B); Andy Jassy remunerado quase 100% em ações restritas plurianuais",
        "capital_alloc": "Máquina de Reinvestimento: 100% do FCO reinvestido em nós logísticos robotizados, chips Trainium/Inferentia e AWS",
        "tag_along": "100% Tag Along / Proteção Fiduciária Delaware / SEC",
        "country_liquidity_risk": "EUA — Liquidez Soberana Nível 1",
        "common_size_vs_peers": "Margem Bruta 49.2% (vs Varejo Tradicional 24.5%) | FCO/EBITDA 0.95x | Liderança global em Cloud (31% share)",
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
            "Receita": {"3y": 64.5, "5y": 60.2, "10y": 37.8},
            "Lucro Bruto": {"3y": 72.4, "5y": 66.8, "10y": 41.2},
            "EBIT": {"3y": 96.0, "5y": 89.5, "10y": 52.4},
            "EBITDA": {"3y": 91.2, "5y": 84.0, "10y": 49.8},
            "NOPAT": {"3y": 94.5, "5y": 88.2, "10y": 51.6},
            "Lucro Líquido": {"3y": 86.4, "5y": 85.1, "10y": 50.8},
            "FCO": {"3y": 92.0, "5y": 68.5, "10y": 46.2},
            "FCF": {"3y": 95.5, "5y": 71.0, "10y": 47.9},
            "EPS": {"3y": 87.2, "5y": 85.8, "10y": 51.2},
            "Dividendos": {"3y": 28.0, "5y": 18.5, "10y": 11.4},
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
        "roic_pillar": "Margem Operacional Extraordinária (62.1%) + Modelo Fabless Asset-Light",
        "rd_to_sales_pct": 9.8,
        "ltv_cac": 24.0,
        "gm_5y_series": [62.3, 64.9, 56.9, 72.7, 75.2],
        "gm_trend_status": "Expansão Histórica (+12.9 pp em 5a — Poder de Precificação Monopolístico em Clusters de IA)",
        "moat_type": "Wide Moat (4 Pilares: Ecossistema CUDA 5.5M Devs, Switching Cost de Software/Rede NVLink, Patentes, Escala P&D)",
        "porter": "Rivalidade: Baixa (90%+ share em AI Training) | Fornecedores: Alta (Dependência TSMC CoWoS) | Clientes: Moderada | Substitutos: Baixa (ASICs parciais) | Entrantes: Muito Baixa",
        "ceo_skin": "Jensen Huang (Fundador/CEO) detém ~3.5% da companhia (> USD 120B em Skin in the Game direto)",
        "capital_alloc": "Impecável: Foco 100% orgânico em cadência anual de arquiteturas (Hopper -> Blackwell -> Rubin) + USD 50B em recompras",
        "tag_along": "100% Tag Along / Proteção Fiduciária Delaware / SEC",
        "country_liquidity_risk": "EUA — Liquidez Nível 1 (Atenção Geopolítica: Fabricação concentrada em Taiwan/TSMC e restrições BIS/China)",
        "common_size_vs_peers": "Margem Bruta 75.2% (vs AMD 51.0% e Intel 41.0%) | Margem EBIT 62.1% (vs Setor Chips 24.0%) | Monopólio Absoluto",
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
        "sss_retail": "N/A (3.29B Daily Active People — ARPU crescendo +14% YoY)",
        "cagrs": {
            "Receita": {"3y": 11.2, "5y": 17.5, "10y": 28.4},
            "Lucro Bruto": {"3y": 11.6, "5y": 17.3, "10y": 28.1},
            "EBIT": {"3y": 12.8, "5y": 21.8, "10y": 29.0},
            "EBITDA": {"3y": 13.5, "5y": 21.2, "10y": 28.6},
            "NOPAT": {"3y": 13.1, "5y": 21.5, "10y": 29.2},
            "Lucro Líquido": {"3y": 12.1, "5y": 24.5, "10y": 33.8},
            "FCO": {"3y": 12.8, "5y": 17.9, "10y": 29.5},
            "FCF": {"3y": 10.4, "5y": 18.8, "10y": 27.6},
            "EPS": {"3y": 15.4, "5y": 27.2, "10y": 35.1},
            "Dividendos": {"3y": 100.0, "5y": 100.0, "10y": 100.0},
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
            {"segment": "Reality Labs (Ray-Ban Meta AI Glasses / Quest) + Net Cash", "rev_share_pct": 1.5, "peer_benchmark": "Desconto Capex R&D (-USD 40/ação) + Caixa Líquido", "segment_val_per_share": -20.0},
        ],
        "roic_op_margin_pct": 41.2,
        "roic_cap_turnover_x": 0.83,
        "roic_pillar": "Margem Operacional de 41.2% no Core Family of Apps (mascarada pelo P&D do Reality Labs)",
        "rd_to_sales_pct": 24.5,
        "ltv_cac": 18.0,
        "gm_5y_series": [80.6, 80.8, 79.6, 80.8, 81.5],
        "gm_trend_status": "Estabilidade Excepcional (>81% — Maior Margem Bruta entre todas as Big Techs)",
        "moat_type": "Wide Moat (4 Pilares: Efeito de Rede de 3.29B Pessoas/Dia, Grafo Social, Algoritmo IA Ads, Escala)",
        "porter": "Rivalidade: Moderada (TikTok/YouTube) | Fornecedores: Baixa | Clientes: Baixa (10M+ PMEs anunciantes) | Substitutos: Baixa | Entrantes: Muito Baixa",
        "ceo_skin": "Mark Zuckerberg (Fundador/CEO) detém ~13.5% do capital total (> USD 200B) e controle votante Classe B",
        "capital_alloc": "Forte: Disciplina operacional ('Eficiência Permanente') + Open-Source IA Llama + Recompras oportunas nos fundos",
        "tag_along": "Estrutura Dual-Class (A/B) sob lei de Delaware / SEC",
        "country_liquidity_risk": "EUA — Liquidez Soberana Nível 1",
        "common_size_vs_peers": "Margem Bruta 81.5% (vs Google 58.1% e Snap 54.0%) | Margem EBIT 41.2% | Conversão de Anúncios Líder via IA",
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
            "Receita": {"3y": 14.2, "5y": 9.4, "10y": 11.0},
            "Lucro Bruto": {"3y": 14.5, "5y": 9.5, "10y": 11.2},
            "EBIT": {"3y": 14.8, "5y": 10.1, "10y": 11.9},
            "EBITDA": {"3y": 14.6, "5y": 10.0, "10y": 11.8},
            "NOPAT": {"3y": 15.1, "5y": 10.4, "10y": 12.5},
            "Lucro Líquido": {"3y": 17.0, "5y": 10.3, "10y": 13.8},
            "FCO": {"3y": 10.5, "5y": 9.8, "10y": 11.4},
            "FCF": {"3y": 10.2, "5y": 9.9, "10y": 11.6},
            "EPS": {"3y": 19.2, "5y": 12.6, "10y": 16.2},
            "Dividendos": {"3y": 16.5, "5y": 15.8, "10y": 17.9},
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
        "roic_pillar": "Pedágio Puro: Margem Operacional de 67.0% com CAPEX < 4% da Receita (Zero Risco de Crédito)",
        "rd_to_sales_pct": 4.2,
        "ltv_cac": 22.0,
        "gm_5y_series": [79.5, 79.8, 80.1, 79.9, 80.4],
        "gm_trend_status": "Estabilidade Imbatível (>80% — Custo marginal de processar uma transação adicional é próximo de zero)",
        "moat_type": "Wide Moat (4 Pilares: Efeito de Rede Bilateral Global 4.5B cartões / 150M lojistas, Custo Marginal Zero, Marca, Switching Cost)",
        "porter": "Rivalidade: Baixa (Duopólio racional c/ Mastercard) | Fornecedores: Nula | Clientes: Baixa | Substitutos: Baixa em Cross-Border/Crédito | Entrantes: Nula",
        "ceo_skin": "Ryan McInerney e diretoria com pacotes de performance PSU atrelados a EPS Compounding e ROIC",
        "capital_alloc": "Devolução Total ao Acionista: >95% do FCF devolvido via Recompras Anuais (~USD 16B) e Dividendos crescentes 15% a.a.",
        "tag_along": "100% Tag Along / Proteção Fiduciária Delaware / SEC",
        "country_liquidity_risk": "EUA — Liquidez Soberana Nível 1 (Receita diversificada em mais de 200 países; Hedge natural contra inflação nominal)",
        "common_size_vs_peers": "Margem Operacional 67.0% (vs Mastercard 58.2% e PayPal 18.5%) | Zero exposição a inadimplência bancária",
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
        "roic_goodwill_pct": 18.2,  # Em bancos, ROE / ROTCE é a métrica equivalente ao ROIC
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
        "sss_retail": "N/A (Banco Global — Crescimento de Depósitos Core +5.2% e AUM +16% YoY)",
        "cagrs": {
            "Receita": {"3y": 12.8, "5y": 8.6, "10y": 6.2},
            "Lucro Bruto": {"3y": 13.0, "5y": 8.8, "10y": 6.4},
            "EBIT": {"3y": 11.4, "5y": 10.2, "10y": 8.5},
            "EBITDA": {"3y": 11.4, "5y": 10.2, "10y": 8.5},
            "NOPAT": {"3y": 10.8, "5y": 9.8, "10y": 9.1},
            "Lucro Líquido": {"3y": 10.5, "5y": 9.6, "10y": 9.4},
            "FCO": {"3y": 11.2, "5y": 9.1, "10y": 8.8},
            "FCF": {"3y": 10.9, "5y": 9.4, "10y": 9.0},
            "EPS": {"3y": 12.8, "5y": 11.9, "10y": 11.6},
            "Dividendos": {"3y": 7.8, "5y": 7.2, "10y": 11.2},
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
        "roic_pillar": "Custo de Captação Baixíssimo (Depósitos Core) + Escala de Tecnologia (USD 17B/ano em TI) + ROTCE 21%",
        "rd_to_sales_pct": 9.8,
        "ltv_cac": 12.0,
        "gm_5y_series": [54.0, 55.2, 56.8, 58.5, 59.2],
        "gm_trend_status": "Expansão (+5.2 pp em 5a — Ganho de Net Interest Margin e aquisição oportunista do First Republic)",
        "moat_type": "Wide Moat (3 Pilares: Vantagem de Custo de Funding, Escala Sistêmica Fortress Balance Sheet, Switching Cost Corporativo)",
        "porter": "Rivalidade: Moderada | Fornecedores: Baixa (Maior base de depositantes dos EUA) | Clientes: Média | Substitutos: Moderada | Entrantes: Muito Baixa (Regulação Basileia)",
        "ceo_skin": "Jamie Dimon detém > USD 2.0B em ações do JPMorgan; histórico lendário de gestão de risco contracíclica",
        "capital_alloc": "Fortaleza Contracíclica: CET1 em 15.3% (excesso de capital > USD 35B), aquisições em crises (Bear Stearns, WaMu, First Republic)",
        "tag_along": "100% Tag Along / Proteção Fiduciária Delaware / SEC",
        "country_liquidity_risk": "EUA — Liquidez Soberana Nível 1 (G-SIB #1 do Mundo)",
        "common_size_vs_peers": "ROTCE 21.0% (vs BofA 13.5%, Citi 7.8%, Wells Fargo 14.2%) | Índice de Eficiência 52% (Melhor entre Megabanks)",
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
        "sss_retail": "+4.8% US Same Store Sales (SSS Positivo há 40 trimestres consecutivos + E-Commerce +24%)",
        "cagrs": {
            "Receita": {"3y": 5.8, "5y": 5.1, "10y": 3.4},
            "Lucro Bruto": {"3y": 5.6, "5y": 4.9, "10y": 3.3},
            "EBIT": {"3y": 6.4, "5y": 5.8, "10y": 2.1},
            "EBITDA": {"3y": 6.8, "5y": 6.2, "10y": 3.2},
            "NOPAT": {"3y": 6.5, "5y": 6.0, "10y": 2.8},
            "Lucro Líquido": {"3y": 11.2, "5y": 5.4, "10y": 2.5},
            "FCO": {"3y": 14.5, "5y": 7.2, "10y": 3.9},
            "FCF": {"3y": 11.8, "5y": 6.5, "10y": 3.4},
            "EPS": {"3y": 12.6, "5y": 6.8, "10y": 4.5},
            "Dividendos": {"3y": 3.8, "5y": 2.9, "10y": 2.6},
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
            {"segment": "Walmart International (Walmex, Índia Flipkart, Canadá)", "rev_share_pct": 17.0, "peer_benchmark": "EM Retail & E-Commerce (13x EV/EBITDA)", "segment_val_per_share": 12.5},
            {"segment": "Walmart Connect (Retail Media Ads) & Membership", "rev_share_pct": 3.0, "peer_benchmark": "High-Margin Digital Ads (25x EV/EBIT)", "segment_val_per_share": 9.5},
        ],
        "roic_op_margin_pct": 4.3,
        "roic_cap_turnover_x": 3.81,
        "roic_pillar": "Giro de Capital Brutal (3.81x) + Ciclo de Caixa Negativo Financiado por Fornecedores",
        "rd_to_sales_pct": 0.0,
        "ltv_cac": 11.0,
        "gm_5y_series": [24.8, 25.1, 24.1, 24.4, 24.7],
        "gm_trend_status": "Estável (~24.7% — Repassa ganhos de escala ao consumidor via Everyday Low Price enquanto cresce em Ads)",
        "moat_type": "Wide Moat (3 Pilares: Vantagem de Custo de Escala, Poder Monopsonista sobre Fornecedores, Malha Física Omnichannel)",
        "porter": "Rivalidade: Alta | Fornecedores: Muito Baixa (Walmart dita preços) | Clientes: Baixa (Bens essenciais anticíclicos) | Substitutos: Baixa | Entrantes: Muito Baixa",
        "ceo_skin": "Família Walton detém ~45% do capital (> USD 300B); CEO Doug McMillon com 35+ anos de casa",
        "capital_alloc": "Dividend King (51 anos de aumentos consecutivos de dividendos) + Automação robótica de Centros de Distribuição",
        "tag_along": "100% Tag Along / Proteção Fiduciária Delaware / SEC",
        "country_liquidity_risk": "EUA — Liquidez Soberana Nível 1 (Ativo ultra-defensivo de Beta 0.52)",
        "common_size_vs_peers": "Giro de Ativos 2.62x (vs Target 1.92x) | SSS +4.8% (vs Target +0.3%) | Ganhando share de famílias de alta renda",
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
        "roic_goodwill_pct": 18.4,  # ROE de 18.4% (Recorde histórico na Ásia)
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
        "sss_retail": "N/A (Banco Asiático — Wealth Management Fees +32% YoY, AUM SGD 390B)",
        "cagrs": {
            "Receita": {"3y": 14.5, "5y": 9.8, "10y": 8.4},
            "Lucro Bruto": {"3y": 14.5, "5y": 9.8, "10y": 8.4},
            "EBIT": {"3y": 18.2, "5y": 12.6, "10y": 10.2},
            "EBITDA": {"3y": 18.2, "5y": 12.6, "10y": 10.2},
            "NOPAT": {"3y": 17.8, "5y": 12.4, "10y": 10.5},
            "Lucro Líquido": {"3y": 17.8, "5y": 12.4, "10y": 10.5},
            "FCO": {"3y": 16.5, "5y": 11.8, "10y": 9.8},
            "FCF": {"3y": 16.2, "5y": 11.5, "10y": 9.6},
            "EPS": {"3y": 17.5, "5y": 12.2, "10y": 10.1},
            "Dividendos": {"3y": 21.0, "5y": 13.5, "10y": 12.8},
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
            {"segment": "Institutional Banking & Global Treasury (Singapura/Ásia)", "rev_share_pct": 46.0, "peer_benchmark": "AAA Sovereign Asian Bank (1.75x P/TBV)", "segment_val_per_share": 54.0},
            {"segment": "Consumer Banking & Asian Private Wealth Hub", "rev_share_pct": 45.0, "peer_benchmark": "High-ROE Wealth Franchise (2.25x P/TBV)", "segment_val_per_share": 61.0},
            {"segment": "Digital Assets & Excess Capital Return Program", "rev_share_pct": 9.0, "peer_benchmark": "SGD 3B Buyback & Capital Return", "segment_val_per_share": 11.0},
        ],
        "roic_op_margin_pct": 58.5,
        "roic_cap_turnover_x": 0.31,
        "roic_pillar": "Índice Cost-to-Income de 39% (Digitalização Total) + Depósitos em Moeda Forte (SGD) + ROE 18.4%",
        "rd_to_sales_pct": 6.5,
        "ltv_cac": 14.0,
        "gm_5y_series": [56.0, 57.5, 59.2, 60.8, 61.4],
        "gm_trend_status": "Expansão (+5.4 pp em 5a — Influxo massivo de family offices e fortunas asiáticas para Singapura)",
        "moat_type": "Wide Moat (3 Pilares: Monopólio de Depósitos CASA em Singapura, Escala de Wealth Management, Vantagem de Custo Digital)",
        "porter": "Rivalidade: Baixa (Oligopólio racional de 3 bancos em Singapura: DBS, OCBC, UOB) | Fornecedores: Nula | Clientes: Baixa | Substitutos: Baixa | Entrantes: Nula (MAS)",
        "ceo_skin": "Temasek Holdings (Fundo Soberano de Singapura AAA) é acionista âncora com 29% de participação; Gestão Piyush Gupta / Tan Su Shan alinhada",
        "capital_alloc": "Exemplar: Dividend Yield de ~5.85% a.a. pago trimestralmente + Programa de recompra de SGD 3 bilhões para devolver capital excedente",
        "tag_along": "100% Proteção de Minoritários sob Regulação SGX / Monetary Authority of Singapore (MAS)",
        "country_liquidity_risk": "Singapura — Rating Soberano AAA (Único país da Ásia com triplo A em todas as agências; Dólar de Singapura ultra-forte)",
        "common_size_vs_peers": "ROE 18.4% (vs OCBC 14.2%, UOB 13.8%, HSBC 14.5%) | Cost-to-Income 39.0% (Melhor eficiência bancária da Ásia)",
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
            "Receita": {"3y": 14.2, "5y": 18.5, "10y": 16.8},
            "Lucro Bruto": {"3y": 15.1, "5y": 20.2, "10y": 18.1},
            "EBIT": {"3y": 16.5, "5y": 23.4, "10y": 20.5},
            "EBITDA": {"3y": 16.0, "5y": 22.8, "10y": 19.9},
            "NOPAT": {"3y": 16.2, "5y": 23.0, "10y": 20.1},
            "Lucro Líquido": {"3y": 15.8, "5y": 23.6, "10y": 20.8},
            "FCO": {"3y": 14.5, "5y": 21.0, "10y": 19.2},
            "FCF": {"3y": 14.9, "5y": 22.1, "10y": 19.8},
            "EPS": {"3y": 17.2, "5y": 25.1, "10y": 22.3},
            "Dividendos": {"3y": 12.0, "5y": 18.5, "10y": 21.0},
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
            {"segment": "EUV & High-NA EUV Systems (100% Monopólio)", "rev_share_pct": 54.0, "peer_benchmark": "Unique Global Monopoly (32x EV/EBIT)", "segment_val_per_share": 475.0},
            {"segment": "DUV Immersion Systems (ArFi)", "rev_share_pct": 24.0, "peer_benchmark": "Semi CapEx Leaders (22x EV/EBIT)", "segment_val_per_share": 190.0},
            {"segment": "Installed Base Management & Services", "rev_share_pct": 22.0, "peer_benchmark": "Industrial Mission-Critical SaaS (28x EV/EBIT)", "segment_val_per_share": 170.0},
        ],
        "roic_op_margin_pct": 33.2,
        "roic_cap_turnover_x": 1.34,
        "roic_pillar": "Monopólio Tecnológico Absoluto em Litografia EUV (100% Market Share Global)",
        "rd_to_sales_pct": 14.5,
        "ltv_cac": 25.0,
        "gm_5y_series": [48.6, 52.7, 50.5, 51.3, 51.8],
        "gm_trend_status": "Expansão (+3.2 pp em 5a — Transição para High-NA EUV)",
        "moat_type": "Wide Moat (30 anos de P&D, Óptica Zeiss exclusiva, Switching Cost Infinito)",
        "porter": "Rivalidade: Nula | Fornecedores: Simbiótica Zeiss | Clientes: Concentrada (TSMC, Samsung, Intel) | Substitutos: Inexistente | Entrantes: Impossível",
        "ceo_skin": "Christophe Fouquet (CEO) com remuneração atrelada a ROIC e margem bruta",
        "capital_alloc": "Excelente: P&D de EUR 4B/ano + dividendos crescentes e recompras disciplinadas",
        "tag_along": "100% Proteção Euronext Amsterdam / ADR SEC Form 20-F",
        "country_liquidity_risk": "Holanda / UE (AAA) — Atenção a controles de exportação de DUV para a China",
        "common_size_vs_peers": "Margem Bruta 51.8% (vs Applied Materials 47.5%) | ROIC 44.5% líder global",
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
        "sss_retail": "N/A (Utilização de nós avançados > 100%)",
        "cagrs": {
            "Receita": {"3y": 18.5, "5y": 21.4, "10y": 17.5},
            "Lucro Bruto": {"3y": 20.2, "5y": 23.8, "10y": 19.2},
            "EBIT": {"3y": 19.8, "5y": 24.5, "10y": 19.8},
            "EBITDA": {"3y": 19.5, "5y": 24.0, "10y": 19.5},
            "NOPAT": {"3y": 19.4, "5y": 24.2, "10y": 19.6},
            "Lucro Líquido": {"3y": 18.9, "5y": 23.9, "10y": 19.4},
            "FCO": {"3y": 16.5, "5y": 22.0, "10y": 18.2},
            "FCF": {"3y": 15.2, "5y": 19.8, "10y": 16.5},
            "EPS": {"3y": 20.5, "5y": 25.2, "10y": 20.8},
            "Dividendos": {"3y": 10.5, "5y": 12.8, "10y": 14.5},
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
        "roic_pillar": "Monopólio de Fabricação Avançada de Silício de IA (90%+ de chips IA do mundo)",
        "rd_to_sales_pct": 8.5,
        "ltv_cac": 22.0,
        "gm_5y_series": [51.3, 53.1, 54.4, 53.0, 57.8],
        "gm_trend_status": "Expansão (+6.5 pp em 5a — Nós 3nm e N2 com pricing power extremo)",
        "moat_type": "Wide Moat (Curva de Aprendizado Insuperável, Ecossistema OIP, Rendimento CoWoS 99%)",
        "porter": "Rivalidade: Nula em nós de ponta | Fornecedores: ASML simbiótica | Clientes: Apple, Nvidia, AMD | Substitutos: Inexistente | Entrantes: Impossível",
        "ceo_skin": "C.C. Wei (CEO/Chairman) com remuneração atrelada a expansão global e ROE",
        "capital_alloc": "CapEx disciplinado de USD 30B/ano financiado 100% pelo fluxo operacional",
        "tag_along": "100% Proteção Taiwan Stock Exchange / ADR SEC Form 20-F",
        "country_liquidity_risk": "Taiwan (Risco Geopolítico Estreito de Taiwan; mitigado por expansão Japão/EUA)",
        "common_size_vs_peers": "Margem Operacional 43.5% (vs Samsung Foundry 2.0%, Intel Foundry negativa)",
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
        "sss_retail": "+28.5% (GMV E-commerce YoY em Moeda Constante)",
        "cagrs": {
            "Receita": {"3y": 32.5, "5y": 42.0, "10y": 36.5},
            "Lucro Bruto": {"3y": 35.0, "5y": 44.5, "10y": 38.2},
            "EBIT": {"3y": 48.0, "5y": 65.0, "10y": 45.0},
            "EBITDA": {"3y": 46.5, "5y": 62.0, "10y": 43.5},
            "NOPAT": {"3y": 47.0, "5y": 63.5, "10y": 44.0},
            "Lucro Líquido": {"3y": 52.0, "5y": 72.0, "10y": 48.0},
            "FCO": {"3y": 38.0, "5y": 55.0, "10y": 40.0},
            "FCF": {"3y": 42.0, "5y": 58.0, "10y": 42.0},
            "EPS": {"3y": 50.5, "5y": 70.0, "10y": 46.5},
            "Dividendos": {"3y": 0.0, "5y": 0.0, "10y": 0.0},
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
            {"segment": "Mercado Pago Fintech (Crédito, Cartões)", "rev_share_pct": 42.0, "peer_benchmark": "LatAm Fintech Leader (25x EV/EBIT)", "segment_val_per_share": 860.0},
        ],
        "roic_op_margin_pct": 16.5,
        "roic_cap_turnover_x": 1.78,
        "roic_pillar": "Efeito de Rede Cruzado (Marketplace + Fintech + Rede Logística Mercado Envíos)",
        "rd_to_sales_pct": 9.2,
        "ltv_cac": 16.5,
        "gm_5y_series": [46.8, 50.1, 52.4, 53.5, 54.2],
        "gm_trend_status": "Expansão Contínua (+7.4 pp em 5a — Monetização de Ads e Serviços Financeiros)",
        "moat_type": "Wide Moat (Rede logística regional imbatível em BR/MX/AR, Efeito de rede bilionário)",
        "porter": "Rivalidade: Baixa | Fornecedores: Baixa | Clientes: Baixa (Switching cost Mercado Pago) | Substitutos: Baixa | Entrantes: Nula",
        "ceo_skin": "Marcos Galperin (Fundador) com grande fatia do patrimônio pessoal em ações MELI",
        "capital_alloc": "Reinvestimento exemplar: Expansão de crédito com NPL controlado + malha de CDs",
        "tag_along": "100% Proteção Delaware / Nasdaq Global Select Market",
        "country_liquidity_risk": "América Latina (Risco Cambial BRL/MXN/ARS compensado por liderança e repasse inflacionário)",
        "common_size_vs_peers": "Crescimento de Receita 35% YoY vs Amazon 11% | Margem Operacional em expansão rápida",
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
        "sss_retail": "N/A (Chips de IA crescendo +300% YoY para Google TPU e Meta MTIA)",
        "cagrs": {
            "Receita": {"3y": 21.5, "5y": 24.0, "10y": 28.5},
            "Lucro Bruto": {"3y": 23.0, "5y": 26.5, "10y": 30.0},
            "EBIT": {"3y": 25.5, "5y": 29.0, "10y": 32.0},
            "EBITDA": {"3y": 24.8, "5y": 28.5, "10y": 31.5},
            "NOPAT": {"3y": 25.0, "5y": 28.8, "10y": 31.8},
            "Lucro Líquido": {"3y": 26.2, "5y": 30.5, "10y": 33.2},
            "FCO": {"3y": 20.5, "5y": 25.0, "10y": 29.0},
            "FCF": {"3y": 21.8, "5y": 26.2, "10y": 30.5},
            "EPS": {"3y": 24.0, "5y": 28.0, "10y": 31.0},
            "Dividendos": {"3y": 14.5, "5y": 18.2, "10y": 34.0},
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
        "roic_pillar": "Monopólio de Redes de IA (Ethernet Tomahawk 5) + Custom ASICs para Hyperscalers",
        "rd_to_sales_pct": 10.5,
        "ltv_cac": 20.0,
        "gm_5y_series": [73.5, 74.8, 75.2, 74.1, 76.8],
        "gm_trend_status": "Expansão (+3.3 pp em 5a — Transição da VMware para assinaturas VCF)",
        "moat_type": "Wide Moat (Switching costs insuperáveis em software VMware e switches Tomahawk)",
        "porter": "Rivalidade: Baixa | Fornecedores: TSMC prioritária | Clientes: Hyperscalers (Google, Meta, Apple) | Substitutos: Nula | Entrantes: Nula",
        "ceo_skin": "Hock Tan (CEO) considerado o maior alocador de capital de fusões e aquisições do setor",
        "capital_alloc": "Histórico lendário: Desalavancagem rápida após VMware + dividendos crescentes há 13 anos",
        "tag_along": "100% Proteção Delaware / Nasdaq Global Select",
        "country_liquidity_risk": "EUA — Risco de Liquidez Zero (Líder tecnológico com geração de FCF de USD 20B+)",
        "common_size_vs_peers": "Margem EBITDA 60.5% (Muito superior ao setor de semicondutores e software)",
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
        "sss_retail": "+11.0% (Crescimento de Volume GDV Global em Moeda Constante)",
        "cagrs": {
            "Receita": {"3y": 14.5, "5y": 16.0, "10y": 13.8},
            "Lucro Bruto": {"3y": 14.5, "5y": 16.0, "10y": 13.8},
            "EBIT": {"3y": 15.2, "5y": 16.8, "10y": 14.2},
            "EBITDA": {"3y": 15.0, "5y": 16.5, "10y": 14.0},
            "NOPAT": {"3y": 15.1, "5y": 16.6, "10y": 14.1},
            "Lucro Líquido": {"3y": 15.8, "5y": 17.2, "10y": 14.5},
            "FCO": {"3y": 14.8, "5y": 16.2, "10y": 14.0},
            "FCF": {"3y": 15.0, "5y": 16.5, "10y": 14.2},
            "EPS": {"3y": 17.5, "5y": 19.0, "10y": 16.8},
            "Dividendos": {"3y": 16.2, "5y": 17.5, "10y": 19.5},
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
        "roic_pillar": "Pedágio Financeiro Global Inabalável (>3.4B cartões ativos e 150M de estabelecimentos)",
        "rd_to_sales_pct": 5.8,
        "ltv_cac": 28.0,
        "gm_5y_series": [78.2, 79.5, 80.1, 80.8, 81.2],
        "gm_trend_status": "Estabilidade Padrão-Ouro (~81% — Duopólio com a Visa sem pressão concorrencial)",
        "moat_type": "Wide Moat (Efeito de rede bilateral insubstituível entre consumidores e bancos)",
        "porter": "Rivalidade: Baixa (Duopólio racional Visa/Mastercard) | Fornecedores: Nula | Clientes: Baixa | Substitutos: Muito Baixa | Entrantes: Impossível",
        "ceo_skin": "Michael Miebach (CEO) e corpo executivo com remuneração atrelada a EPS CAGR e ROIC",
        "capital_alloc": "Conversão de caixa de 100% devolvida aos acionistas via recompras e dividendos",
        "tag_along": "100% Proteção Delaware / NYSE",
        "country_liquidity_risk": "EUA — Risco Soberano Zero (Fluxo monetário global lastreado no consumo global)",
        "common_size_vs_peers": "Margem Operacional 58.2% (vs Visa 66.8%, PayPal 17.5%) | Retorno sobre capital incomparável",
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
        "sss_retail": "N/A (ARPAC crescendo 25% YoY para $11.00/mês)",
        "cagrs": {
            "Receita": {"3y": 68.0, "5y": 85.0, "10y": 92.0},
            "Lucro Bruto": {"3y": 75.0, "5y": 92.0, "10y": 98.0},
            "EBIT": {"3y": 95.0, "5y": 120.0, "10y": 110.0},
            "EBITDA": {"3y": 92.0, "5y": 115.0, "10y": 105.0},
            "NOPAT": {"3y": 94.0, "5y": 118.0, "10y": 108.0},
            "Lucro Líquido": {"3y": 110.0, "5y": 135.0, "10y": 120.0},
            "FCO": {"3y": 80.0, "5y": 95.0, "10y": 90.0},
            "FCF": {"3y": 82.0, "5y": 98.0, "10y": 92.0},
            "EPS": {"3y": 105.0, "5y": 130.0, "10y": 118.0},
            "Dividendos": {"3y": 0.0, "5y": 0.0, "10y": 0.0},
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
            {"segment": "Nubank Brasil (Operação Madura ROE > 28%)", "rev_share_pct": 82.0, "peer_benchmark": "High-ROE Digital Banking (18x P/E)", "segment_val_per_share": 12.50},
            {"segment": "Expansão México & Colômbia (Captação de Depósitos)", "rev_share_pct": 18.0, "peer_benchmark": "Hypergrowth FinTech (25x P/E)", "segment_val_per_share": 4.50},
        ],
        "roic_op_margin_pct": 42.0,
        "roic_cap_turnover_x": 0.74,
        "roic_pillar": "Vantagem de Custo Estrutural: Cost-to-Serve de USD 0.80/cliente/mês vs Incumbentes USD 12.00+",
        "rd_to_sales_pct": 8.0,
        "ltv_cac": 30.0,
        "gm_5y_series": [32.0, 38.5, 43.2, 45.8, 48.2],
        "gm_trend_status": "Expansão Acelerada (+16.2 pp em 5a — Alavancagem operacional pura)",
        "moat_type": "Wide Moat (Custo de servir imbatível, 110M+ clientes, Custo de captação abaixo do CDI)",
        "porter": "Rivalidade: Baixa frente aos incumbentes com agências | Fornecedores: Nula | Clientes: Baixa churn | Substitutos: Baixa | Entrantes: Muito Baixa",
        "ceo_skin": "David Vélez (Fundador/CEO) com > 75% dos direitos de voto e foco exclusivo no longo prazo",
        "capital_alloc": "Excelente: Lucro retido integralmente para financiar expansão de balanço sem diluição",
        "tag_along": "100% Proteção NYSE Class A / SEC Regulação",
        "country_liquidity_risk": "América Latina (Sólida base de capital CET1 > 17% e depósitos inelásticos)",
        "common_size_vs_peers": "Efficiency Ratio 31.4% (Melhor da América Latina) | ROE consolidado 28.5%",
    },
}


# Dados de pares bancários globais para o Scatter Plot obrigatório: P/TBV vs. ROE para Bancos
GLOBAL_BANKS_SCATTER_DATA: List[Dict[str, Any]] = [
    {"Ticker": "JPM", "Banco": "JPMorgan Chase & Co. (Portfolio — Money Center Leader)", "ROE_pct": 18.2, "PTBV": 2.48, "PEGY_Fin": 1.24, "PB": 2.02, "Grupo": "Portfolio"},
    {"Ticker": "NU", "Banco": "Nu Holdings / Nubank (Portfolio — High-ROTE Digital Bank)", "ROE_pct": 28.5, "PTBV": 6.80, "PEGY_Fin": 0.78, "PB": 6.45, "Grupo": "Portfolio"},
    {"Ticker": "SECTOR-AVG", "Banco": "Global Banking Peer Average (Sector Benchmark)", "ROE_pct": 11.8, "PTBV": 1.35, "PEGY_Fin": 1.32, "PB": 1.15, "Grupo": "Sector Benchmark"},
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
            # 2.1 SAÚDE FINANCEIRA E CONTABILIDADE FORENSE
            # ==================================================================
            # Sloan Ratio: (Lucro Líquido - FCO - FCI) / Ativos Totais
            sloan_pct = kb["sloan_pct"]
            if sloan_pct < -10.0:
                sloan_status = "Ótimo (< -10% — Geração de Caixa excede Lucro Contábil)"
            elif sloan_pct <= 10.0:
                sloan_status = "Ok (-10% a +10% — Accruals Normais)"
            else:
                sloan_status = "Ruim (> +10% — Alerta de Accruals Elevados / Contabilidade Agressiva)"

            fco_ebitda = round(kb["fco_b"] / kb["ebitda_b"], 2) if kb["ebitda_b"] > 0 else 1.0
            if fco_ebitda > 1.0:
                fco_ebitda_status = f"Ótimo ({fco_ebitda:.2f}x > 1.0x)"
            elif fco_ebitda >= 0.70:
                fco_ebitda_status = f"Saudável ({fco_ebitda:.2f}x entre 0.70x e 1.0x)"
            else:
                fco_ebitda_status = f"Cuidado ({fco_ebitda:.2f}x < 0.70x)"

            # NWC cruzado com Desvio Padrão / CV histórico do FCO
            fco_hist = kb["fco_5y_history_b"]
            fco_std_b = round(float(np.std(fco_hist)), 2)
            fco_cv = round(float(np.std(fco_hist) / np.mean(fco_hist)), 2) if np.mean(fco_hist) > 0 else 0.10
            nwc_b = kb["nwc_b"]
            if kb["sector_vertical"] == "FINANCIAL_BANK":
                nwc_context = "N/A Bancário (Regido por Basileia III LCR > 100%)"
            elif nwc_b > 0:
                nwc_context = f"Positivo (USD {nwc_b:+.1f}B > 0) + FCO Consistente (DP: USD {fco_std_b:.1f}B | CV: {fco_cv:.2f})"
            else:
                nwc_context = f"NWC Negativo Eficiente (USD {nwc_b:+.1f}B financiado por fornecedores, validado por FCO ultra-consistente CV={fco_cv:.2f})"

            # CAPM Damodaran WACC para cruzar com ROIC
            beta = kb["beta"]
            crp = 0.0  # EUA e Singapura têm CRP = 0.0% (AAA)
            ke = self.rf + beta * self.erp + crp
            kd_after_tax = (self.rf + 0.011) * (1.0 - 0.21)
            debt_w = min(0.35, (kb["debt_to_assets_pct"] / 100.0) * 0.5)
            eq_w = 1.0 - debt_w
            wacc_pct = round((eq_w * ke + debt_w * kd_after_tax) * 100.0, 2)
            roic_pct = kb["roic_goodwill_pct"]
            roic_wacc_spread = round(roic_pct - wacc_pct, 2)

            # DuPont 3 Pilares: ROE = Margem Líquida x Giro de Ativos x Alavancagem Financeira
            dp_m = kb["dupont_margin_pct"]
            dp_t = kb["dupont_turnover_x"]
            dp_l = kb["dupont_leverage_x"]
            roe_dupont_pct = round((dp_m / 100.0) * dp_t * dp_l * 100.0, 1)
            if kb["sector_vertical"] == "FINANCIAL_BANK":
                dupont_quality = f"Bancário Saudável (ROE {roe_dupont_pct:.1f}% sustentado por Margem {dp_m:.1f}% e Alavancagem Basileia {dp_l:.1f}x)"
            elif dp_l > 4.0 and dp_m > 20.0:
                dupont_quality = f"Eficiência Operacional + Recompras (Margem {dp_m:.1f}% e Giro {dp_t:.2f}x; Alavancagem {dp_l:.2f}x por redução de Book Value via Buybacks)"
            elif dp_l > 4.0:
                dupont_quality = f"ALERTA: ROE inflado por Alavancagem Financeira excessiva ({dp_l:.2f}x)"
            else:
                dupont_quality = f"Qualidade Pura: ROE {roe_dupont_pct:.1f}% impulsionado por Margem ({dp_m:.1f}%) e Giro ({dp_t:.2f}x) com baixa alavancagem ({dp_l:.2f}x)"

            forensic_health = {
                "sloan_ratio_pct": sloan_pct,
                "sloan_reference": "< -10% (Ótimo) | -10% a +10% (Ok) | > +10% (Ruim)",
                "sloan_verdict": sloan_status,
                "fco_current_b": kb["fco_b"],
                "fci_current_b": kb["fci_b"],
                "fco_5y_history_b": fco_hist,
                "fco_to_ebitda": fco_ebitda,
                "fco_to_ebitda_ref": "> 1.0x (Ótimo) | < 0.70x (Cuidado)",
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
                "current_ratio_ref": "> 1.0x + Caixa Positivo Pós-Despesas",
                "cash_b": kb["cash_b"],
                "cash_after_annual_exp_positive": kb["cash_after_annual_exp_positive"],
                "interest_coverage_x": kb["interest_coverage_x"],
                "interest_coverage_ref": "> 3.0x (Saudável)",
                "debt_to_ebitda": kb["debt_to_ebitda"],
                "debt_to_assets_pct": kb["debt_to_assets_pct"],
                "debt_to_equity_pct": kb["debt_to_equity_pct"],
                "sss_same_store_sales": kb["sss_retail"],
            }

            # ==================================================================
            # 2.2 MOTOR DE VALUATION MULTI-MÉTODOS (TODOS OS 8 MÉTODOS LADO A LADO)
            # ==================================================================
            # 1) DCF Tradicional (CAPM Damodaran + Gordon Growth Model + Cenários Conservador/Base/Otimista + 10% MoS)
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
                # Fade de 5 anos adicionais até o terminal
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
            dcf_fair_mos10 = round(dcf_range_mean * 0.90, 2)  # 10% de desconto (Margem de Segurança)

            dcf_note = (
                "AVISO METODOLÓGICO: Evitar DCF tradicional isolado para High-Growth Stocks (priorizar Enterprise PEGY EV/EBIT e SOTP)"
                if kb["sector_vertical"] == "TECH_HIGH_GROWTH"
                else (
                    "AVISO SETORIAL: Em Bancos, DCF é apenas proxy de DDM; priorizar P/TBV vs. ROE e PEGY Financeiro"
                    if kb["sector_vertical"] == "FINANCIAL_BANK"
                    else "DCF Aplicável com ROIC > WACC verificado e Margem de Segurança de 10% sobre a média do range"
                )
            )

            # 2) Reverse DCF (Crescimento Implícito Pareado)
            # Encontra g_impl tal que DCF(g_impl) == Preço Atual
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

            # 3) FCF Yield / Owner Earnings Yield (Método Charlie Munger) vs Risk-Free Rate (US 10Y)
            # Owner Earnings = Lucro Líquido + D&A - CAPEX de Manutenção +/- Delta NWC
            owner_earnings_b = round(kb["net_income_b"] + kb["da_b"] - kb["maint_capex_b"] + kb["delta_nwc_b"], 2)
            owner_earnings_yield_pct = round((owner_earnings_b / mcap_b) * 100.0, 2) if mcap_b > 0 else 4.0
            fcf_yield_pct = round((kb["fcf_b"] / mcap_b) * 100.0, 2) if mcap_b > 0 else 3.8
            oe_gt_rf = owner_earnings_yield_pct > self.rf_pct
            oe_vs_rf_spread = round(owner_earnings_yield_pct - self.rf_pct, 2)

            # 4) Múltiplos e Ratios Comparados (P/E, EV/EBITDA, P/B, P/TBV)
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
                primary_pegy_label = f"PEGY Financeiro (P/E NTM ÷ [g_EPS + DY]): {pegy_financeiro:.2f}x"
                primary_pegy_status = "Ótimo (0 a 1.0x — Banco)" if pegy_financeiro <= 1.0 else ("Ok (1.0 a 1.5x — Banco)" if pegy_financeiro <= 1.5 else "Caro (> 1.5x — Banco)")
            elif kb["sector_vertical"] == "TECH_HIGH_GROWTH":
                primary_pegy_val = ent_pegy_ebit
                primary_pegy_label = f"Enterprise PEGY (EV/EBIT NTM): {ent_pegy_ebit:.2f}x"
                primary_pegy_status = "Faixa Ouro (0 a 1.2x — High-Growth)" if ent_pegy_ebit <= 1.2 else ("Neutro (1.2 a 1.6x)" if ent_pegy_ebit <= 1.6 else "Esticado (> 1.6x)")
            elif kb["sector_vertical"] == "RETAIL":
                primary_pegy_val = ent_pegy_ebit
                primary_pegy_label = f"Enterprise PEGY (EV/EBIT NTM c/ SSS): {ent_pegy_ebit:.2f}x"
                primary_pegy_status = "Faixa Ouro (0 a 1.2x — Varejo)" if ent_pegy_ebit <= 1.2 else ("Neutro (1.2 a 1.6x)" if ent_pegy_ebit <= 1.6 else "Esticado (> 1.6x)")
            else:
                primary_pegy_val = ent_pegy_fcf
                primary_pegy_label = f"Enterprise PEGY (EV/FCF NTM): {ent_pegy_fcf:.2f}x"
                primary_pegy_status = "Faixa Ouro (0 a 1.2x — Cash Cow)" if ent_pegy_fcf <= 1.2 else ("Neutro (1.2 a 1.6x)" if ent_pegy_fcf <= 1.6 else "Esticado (> 1.6x)")

            # Preço Justo implícito na Faixa Ouro PEGY (1.20x para não-financeiras, 1.00x para bancos)
            target_pegy_gold = 1.00 if kb["sector_vertical"] == "FINANCIAL_BANK" else 1.20
            pegy_gold_fair_price = round(px * (target_pegy_gold / max(0.3, primary_pegy_val)), 2)

            # 7) Greenblatt's Magic Formula (ROIC + Earnings Yield EBIT/EV)
            earnings_yield_ebit_ev_pct = round((kb["ebit_b"] / ev_b) * 100.0, 2) if ev_b > 0 else 5.0
            magic_combined_score = round(roic_pct * 0.55 + earnings_yield_ebit_ev_pct * 2.5, 1)
            altman_caution_flag = "Solvência Blindada (Cobertura Juros & Liquidez)" if kb["interest_coverage_x"] >= 3.0 else "CAUTELA: Checar Risco Estrutural"

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
                    else f"EXIGÊNCIA ELEVADA (g_impl {g_impl_pct:.1f}% > g_fund {g_fund_pct:.1f}%)"
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
                    else f"ABAIXO DA RISK-FREE ({owner_earnings_yield_pct:.2f}% < US10Y {self.rf_pct:.2f}% — Retorno ancorado em Crescimento)"
                ),
                "oe_vs_rf_verdict": (
                    f"ACIMA DA RISK-FREE ({owner_earnings_yield_pct:.2f}% > US10Y {self.rf_pct:.2f}%)"
                    if oe_gt_rf
                    else f"ABAIXO DA RISK-FREE ({owner_earnings_yield_pct:.2f}% < US10Y {self.rf_pct:.2f}% — Retorno ancorado em Crescimento)"
                ),
                # 4. Múltiplos Comparados
                "pe_current": pe_curr,
                "pe_ntm": pe_ntm,
                "pe_sector_avg": kb["pe_sector"],
                "pe_5y_hist_avg": kb["pe_5y_avg"],
                "pe_5y_avg": kb["pe_5y_avg"],
                "pe_implied_dcf": pe_implied_dcf,
                "cyclical_pe_warning": "NOTA SETORES CÍCLICOS: Em cíclicas/commodities a lógica é inversa (P/E e EV/EBITDA baixos = topo de ciclo / caro; múltiplos altos = fundo de ciclo).",
                "ev_ebitda_current": ev_ebitda_curr,
                "ev_ebitda_sector_avg": kb["ev_ebitda_sector"],
                "pb_current": pb_curr,
                "ptbv_current": ptbv_curr,
                "pb_structural_ref": "P/B < 1.0x geralmente indica risco estrutural / destruição de valor (Veto em Bancos)",
                # 5. EVA
                "invested_capital_b": invested_cap_b,
                "eva_usd_b": eva_usd_b,
                "eva_pct_of_ic": eva_pct_ic,
                # 6. PEG & PEGY Ratios
                "pegy_financeiro": pegy_financeiro,
                "pegy_financeiro_ref": "0 a 1.0 (Ótimo) | 1.0 a 1.5 (Ok) | > 1.5 (Ruim)",
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
            # 2.3 ANÁLISE QUALITATIVA, ESTRATÉGICA E LENTE DE PARTICULARIDADES SETORIAIS
            # ==================================================================
            if kb["sector_vertical"] == "FINANCIAL_BANK":
                sector_lens = (
                    "LENTE BANCOS & SEGUROS: Prioridade analítica em P/TBV vs. ROE e PEGY Financeiro. "
                    "AVISO: EV/EBITDA e DCF tradicional isolado são distorcidos por depósitos e provisões de crédito; P/B < 1.0x é veto por risco estrutural."
                )
            elif kb["sector_vertical"] == "FINANCIAL_TOLLBOOTH":
                sector_lens = (
                    "LENTE FINTECH / PROCESSADORAS DE PAGAMENTO: Tratar como Big Tech / Cash Cow (Não tem risco de balanço bancário). "
                    "Prioridade analítica em Enterprise PEGY (EV/FCF NTM), ROIC > 40% e Margem Operacional."
                )
            elif kb["sector_vertical"] == "TECH_HIGH_GROWTH":
                sector_lens = (
                    "LENTE HIGH-GROWTH TECH & INFRA IA: Prioridade analítica em Enterprise PEGY com EV/EBIT NTM (não penaliza Capex de expansão), "
                    "Reverse DCF pareado com g_fund e SOTP por unidade de negócio."
                )
            elif kb["sector_vertical"] == "TECH_CASH_COW":
                sector_lens = (
                    "LENTE BIG TECH CASH COWS & MONOPÓLIOS: Prioridade analítica em Enterprise PEGY com EV/FCF NTM (geração de caixa livre real + Buybacks), "
                    "Owner Earnings Yield vs. US 10Y e SOTP."
                )
            elif kb["sector_vertical"] == "RETAIL":
                sector_lens = (
                    "LENTE VAREJO (RETAIL): Prioridade analítica em Enterprise PEGY (EV/EBIT) obrigatoriamente pareado com SSS (Same Store Sales) "
                    "e crescimento orgânico. Se SSS for negativo, múltiplos baixos sinalizam Value Trap."
                )
            else:
                sector_lens = (
                    "LENTE INDÚSTRIA & COMMODITIES (CÍCLICOS): Prioridade em EV/EBITDA inverso vs. média histórica, estabilidade da commodity e DCF de meio de ciclo."
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
                cagr_matrix_12_kpis=kb["cagrs"],
                valuation_methods=valuation_methods,
                qualitative_strategy=qualitative_strategy,
            ))

        # Calcula o Ranking oficial da Greenblatt Magic Formula (ROIC Rank + Earnings Yield Rank)
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

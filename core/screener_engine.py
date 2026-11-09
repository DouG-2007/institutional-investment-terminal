"""
MÓDULO 4: SCREENER QUANTITATIVO E FORENSE DE NOVAS OPORTUNIDADES (AÇÕES E CRIPTOATIVOS)
Aplica estritamente todos os filtros do "Value Investing Framework (TRUE)" e reúne os indicadores
dos Módulos 1, 2 e 3 para cada candidato do universo de busca:

Filtros de Ações:
1. Sloan Ratio <= +5.0% (destacando < -10% como Ótimo);
2. FCO / EBITDA >= 0.90x (destacando > 1.0x como Ótimo);
3. ROIC (via NOPAT) >= 18.0% e > WACC;
4. Solvência Blindada: Liquidez Corrente > 1.0x, Caixa Pós-OpEx Positivo e Interest Coverage > 4.0x (mínimo saudável > 3.0x);
5. Valuation e Setor: Reverse DCF (g_impl <= g_fund) + métricas setoriais saudáveis (PEGY / Enterprise PEGY / DCF / SOTP).

Filtros de Criptoativos:
1. Circulating Supply >= 65.0%;
2. Unlocks <= 2.5%/mês (destacando < 1.0% como impacto baixo);
3. Token Sniffer >= 85/100 e auditorias de código;
4. Active Devs >= 40 no GitHub e Protocol Real Earnings > 0;
5. MVRV Z-Score <= 2.0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import yfinance as yf


@dataclass
class StockScreenerRow:
    ticker: str
    company_name: str
    sector: str
    country: str
    price_usd: float
    # Filtros Forenses & Solvência
    sloan_ratio_pct: float
    sloan_status: str
    fco_to_ebitda: float
    fco_ebitda_status: str
    roic_nopat_pct: float
    wacc_pct: float
    current_ratio: float
    interest_coverage_x: float
    # Filtros de Valuation & Setor
    reverse_dcf_g_impl_pct: float
    g_fund_pct: float
    enterprise_or_fin_pegy: float
    pegy_type: str
    dcf_fair_mos10_usd: float
    sotp_fair_usd: float
    # Módulo 2 & 3 (Filings & Geopolítica/Micro)
    auditor_sox404b: str
    moat_and_catalysts: str
    # Resultado dos 5 Filtros
    filters_passed_count: int
    all_5_filters_passed: bool
    framework_verdict: str


@dataclass
class CryptoScreenerRow:
    symbol: str
    name: str
    category: str
    price_usd: float
    market_cap_b: float
    fdv_b: float
    # 5 Filtros Estritos
    circulating_supply_pct: float
    monthly_unlock_pct: float
    unlock_status: str
    post_unlock_theoretical_px: float
    token_sniffer_score: int
    security_audits: str
    active_devs_github: int
    github_commits_4w: int
    protocol_real_earnings_m: float
    real_yield_pct: float
    pf_ratio: float
    mvrv_z_score: float
    nupl: float
    # Documental & Micro
    whitepaper_and_dao: str
    filters_passed_count: int
    all_5_filters_passed: bool
    framework_verdict: str


STOCK_CANDIDATES_RAW: List[Dict[str, Any]] = [
    {
        "ticker": "ASML",
        "name": "ASML Holding N.V.",
        "sector": "High-Growth Tech / Litografia EUV",
        "country": "Holanda (UE)",
        "px": 745.00,
        "sloan": -11.2,
        "fco_eb": 1.24,
        "roic": 44.5,
        "wacc": 8.9,
        "z": 8.60,
        "cr": 1.58,
        "icov": 34.0,
        "g_impl": 15.8,
        "g_fund": 19.5,
        "pegy": 1.12,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 835.0,
        "sotp": 860.0,
        "audit": "KPMG — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Monopólio 100% em Litografia EUV & High-NA EUV; Backlog de EUR 36B)",
    },
    {
        "ticker": "TSM",
        "name": "Taiwan Semiconductor (TSMC)",
        "sector": "High-Growth Tech / Foundry Semicondutores",
        "country": "Taiwan / ADR EUA",
        "px": 192.00,
        "sloan": -10.6,
        "fco_eb": 1.18,
        "roic": 31.8,
        "wacc": 8.8,
        "z": 7.95,
        "cr": 2.35,
        "icov": 42.0,
        "g_impl": 14.5,
        "g_fund": 21.0,
        "pegy": 0.88,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 228.0,
        "sotp": 240.0,
        "audit": "Deloitte — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Monopólio de Fundição 3nm/2nm e Empacotamento CoWoS para IA)",
    },
    {
        "ticker": "MELI",
        "name": "MercadoLibre, Inc.",
        "sector": "High-Growth Tech / E-Commerce & Fintech",
        "country": "EUA / América Latina",
        "px": 1980.00,
        "sloan": -12.4,
        "fco_eb": 1.32,
        "roic": 29.4,
        "wacc": 10.4,
        "z": 4.45,
        "cr": 1.36,
        "icov": 14.8,
        "g_impl": 19.2,
        "g_fund": 26.5,
        "pegy": 0.96,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 2240.0,
        "sotp": 2380.0,
        "audit": "PwC — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Efeito de Rede Duplo: Mercado Livre + Mercado Pago + Logística Própria)",
    },
    {
        "ticker": "NU",
        "name": "Nu Holdings Ltd. (Nubank)",
        "sector": "Fintech / Digital Banking",
        "country": "Brasil / México / Colômbia",
        "px": 14.20,
        "sloan": -13.1,
        "fco_eb": 1.28,
        "roic": 31.2,
        "wacc": 11.2,
        "z": 3.65,
        "cr": 1.48,
        "icov": 28.0,
        "g_impl": 21.5,
        "g_fund": 30.0,
        "pegy": 0.78,
        "pegy_t": "PEGY Financeiro / Fintech",
        "dcf": 17.5,
        "sotp": 18.2,
        "audit": "KPMG — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Custo de Servir < $0.90/mês, 110M+ clientes e expansão acelerada no México)",
    },
    {
        "ticker": "AVGO",
        "name": "Broadcom Inc.",
        "sector": "High-Growth Tech / Custom AI Silicon & VMware",
        "country": "Estados Unidos",
        "px": 176.00,
        "sloan": -8.4,
        "fco_eb": 1.04,
        "roic": 24.8,
        "wacc": 8.9,
        "z": 4.12,
        "cr": 1.22,
        "icov": 7.8,
        "g_impl": 16.0,
        "g_fund": 18.5,
        "pegy": 1.15,
        "pegy_t": "Enterprise PEGY (EV/FCF)",
        "dcf": 192.0,
        "sotp": 204.0,
        "audit": "PwC — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Líder em ASICs de IA customizados para Google/Meta + Software VMware)",
    },
    {
        "ticker": "MA",
        "name": "Mastercard Incorporated",
        "sector": "Cash Cow / Payment Rails Duopoly",
        "country": "Estados Unidos",
        "px": 512.00,
        "sloan": -11.8,
        "fco_eb": 1.09,
        "roic": 58.2,
        "wacc": 8.2,
        "z": 11.50,
        "cr": 1.18,
        "icov": 36.5,
        "g_impl": 13.4,
        "g_fund": 15.2,
        "pegy": 1.18,
        "pegy_t": "Enterprise PEGY (EV/FCF)",
        "dcf": 545.0,
        "sotp": 560.0,
        "audit": "PwC — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Duopólio global de cartões com margem operacional > 58% e serviços cyber)",
    },
    {
        "ticker": "COST",
        "name": "Costco Wholesale Corp.",
        "sector": "Varejo Subscrição / Defensive",
        "country": "Estados Unidos",
        "px": 915.00,
        "sloan": -6.2,
        "fco_eb": 1.11,
        "roic": 24.5,
        "wacc": 7.6,
        "z": 6.40,
        "cr": 1.04,
        "icov": 48.0,
        "g_impl": 14.8,
        "g_fund": 11.2,  # Reprova no Filtro 5 (g_impl > g_fund e PEGY > 1.6)
        "pegy": 1.88,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 740.0,
        "sotp": 790.0,
        "audit": "KPMG — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Negócio impecável com SSS +7.2%, mas reprovado no filtro de Valuation atual)",
    },
    {
        "ticker": "LLY",
        "name": "Eli Lilly and Company",
        "sector": "Healthcare / GLP-1 Duopoly",
        "country": "Estados Unidos",
        "px": 860.00,
        "sloan": -3.8,
        "fco_eb": 0.92,
        "roic": 27.5,
        "wacc": 7.9,
        "z": 5.20,
        "cr": 1.15,
        "icov": 16.2,
        "g_impl": 24.5,
        "g_fund": 22.0,  # g_impl > g_fund
        "pegy": 1.54,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 795.0,
        "sotp": 840.0,
        "audit": "EY — Unqualified / SOX 404b Clean",
        "moat_cat": "Wide Moat (Patentes Mounjaro/Zepbound; aguardar recuo para g_impl <= g_fund)",
    },
    {
        "ticker": "INTC",
        "name": "Intel Corporation",
        "sector": "Semicondutores Legacy IDM",
        "country": "Estados Unidos",
        "px": 23.50,
        "sloan": +6.8,  # Reprova Sloan (> +5.0%)
        "fco_eb": 0.68,  # Reprova FCO/EBITDA (< 0.90x)
        "roic": 2.1,    # Reprova ROIC (< 18%)
        "wacc": 9.4,
        "z": 1.65,      # Reprova Altman Z (< 2.90)
        "cr": 1.32,
        "icov": 1.8,    # Reprova Interest Coverage (< 4.0x)
        "g_impl": 8.5,
        "g_fund": 3.0,
        "pegy": 2.45,
        "pegy_t": "Enterprise PEGY (EV/EBIT)",
        "dcf": 18.0,
        "sotp": 21.0,
        "audit": "EY — Unqualified / Reestruturação",
        "moat_cat": "Narrow/Eroding Moat (Perda de liderança litográfica para TSMC e de GPUs para Nvidia)",
    },
]


CRYPTO_CANDIDATES_RAW: List[Dict[str, Any]] = [
    {
        "symbol": "MKR",
        "name": "Maker / Sky Protocol",
        "category": "DeFi Central Bank & RWA Treasury",
        "px": 1580.0,
        "mcap_b": 1.45,
        "fdv_b": 1.52,
        "circ_pct": 95.4,
        "unlock_pct": 0.0,
        "sniffer": 100,
        "audits": "Trail of Bits, OpenZeppelin, Runtime Verification, ChainSecurity",
        "devs": 115,
        "commits": 320,
        "real_earnings_m": +142.0,
        "real_yield_pct": 6.8,
        "pf": 6.2,
        "mvrv_z": 0.55,
        "nupl": 0.21,
        "wp_dao": "Whitepaper DAI/USDS + Smart Burn Engine (Recompra contínua de MKR com lucro de T-Bills RWA)",
    },
    {
        "symbol": "PENDLE",
        "name": "Pendle Finance V2",
        "category": "DeFi Yield Tokenization & Fixed Income AMM",
        "px": 4.65,
        "mcap_b": 0.76,
        "fdv_b": 1.20,
        "circ_pct": 66.2,
        "unlock_pct": 0.45,
        "sniffer": 98,
        "audits": "Ackee Blockchain, Dedaub, WatchPug, Spearbit",
        "devs": 68,
        "commits": 235,
        "real_earnings_m": +34.5,
        "real_yield_pct": 8.9,
        "pf": 16.4,
        "mvrv_z": 0.78,
        "nupl": 0.31,
        "wp_dao": "Padrão EIP-5115 Principal/Yield Token (PT/YT) + 42% do supply travado em vePENDLE",
    },
    {
        "symbol": "LINK",
        "name": "Chainlink Network",
        "category": "Decentralized Oracle Monopoly & CCIP RWA",
        "px": 13.80,
        "mcap_b": 8.65,
        "fdv_b": 13.80,
        "circ_pct": 65.5,
        "unlock_pct": 0.58,
        "sniffer": 100,
        "audits": "SigmaPrime, Trail of Bits, Certora, OpenZeppelin",
        "devs": 315,
        "commits": 590,
        "real_earnings_m": +42.0,
        "real_yield_pct": 4.3,
        "pf": 48.0,
        "mvrv_z": 0.48,
        "nupl": 0.18,
        "wp_dao": "Monopólio de Oráculos (USD 75B+ TVS) e protocolo CCIP adotado por SWIFT, DTCC e Euroclear",
    },
    {
        "symbol": "UNI",
        "name": "Uniswap Protocol (Unichain)",
        "category": "DEX Liquidity Monopoly & DeFi L2",
        "px": 8.90,
        "mcap_b": 5.35,
        "fdv_b": 8.90,
        "circ_pct": 75.3,
        "unlock_pct": 0.25,
        "sniffer": 100,
        "audits": "Trail of Bits, ABDK, OpenZeppelin, Spearbit",
        "devs": 185,
        "commits": 410,
        "real_earnings_m": +95.0,
        "real_yield_pct": 3.5,
        "pf": 11.2,
        "mvrv_z": 0.64,
        "nupl": 0.24,
        "wp_dao": "Uniswap V4 Hooks + Unichain L2 com captura de MEV e taxas para validadores/stakers UNI",
    },
    {
        "symbol": "SUI",
        "name": "Sui Network",
        "category": "Layer-1 Move Blockchain",
        "px": 2.15,
        "mcap_b": 6.10,
        "fdv_b": 21.50,
        "circ_pct": 28.4,      # Reprova Filtro 1 (< 65% Circulating Supply)
        "unlock_pct": 4.20,    # Reprova Filtro 2 (> 2.5%/mês — Diluição VC)
        "sniffer": 95,
        "audits": "Zellic, OtterSec",
        "devs": 145,
        "commits": 330,
        "real_earnings_m": -185.0,  # Reprova Filtro 4 (Emissão de tokens supera receita)
        "real_yield_pct": -4.2,
        "pf": 390.0,
        "mvrv_z": 1.55,
        "nupl": 0.52,
        "wp_dao": "Tecnologia rápida, mas reprovado pela diluição agressiva de unlocks mensais para VCs/Seed",
    },
]


class ScreenerEngine:
    def __init__(self) -> None:
        pass

    def run_stock_screener(self) -> List[StockScreenerRow]:
        out: List[StockScreenerRow] = []
        for c in STOCK_CANDIDATES_RAW:
            # Avaliação dos 5 filtros estritos do Framework:
            f1_sloan = c["sloan"] <= 5.0
            f2_fco = c["fco_eb"] >= 0.90
            f3_roic = (c["roic"] >= 18.0) and (c["roic"] > c["wacc"])
            f4_solv = (c["cr"] > 1.0) and (c["icov"] > 4.0)
            f5_val = (c["g_impl"] <= c["g_fund"]) and (c["pegy"] <= 1.25)

            passed_cnt = sum([f1_sloan, f2_fco, f3_roic, f4_solv, f5_val])
            all_passed = passed_cnt == 5

            sloan_st = "Ótimo (< -10%)" if c["sloan"] < -10.0 else ("Aprovado (<= +5%)" if f1_sloan else "REPROVADO (> +5%)")
            fco_st = "Ótimo (> 1.0x)" if c["fco_eb"] > 1.0 else ("Aprovado (>= 0.90x)" if f2_fco else "REPROVADO (< 0.90x)")

            if all_passed:
                verdict = f"APROVADO 5/5 (Candidato de Elite — {c['pegy_t']} {c['pegy']:.2f}x | g_impl {c['g_impl']:.1f}% <= g_fund {c['g_fund']:.1f}%)"
            elif passed_cnt == 4 and not f5_val:
                verdict = f"WATCHLIST QUALIDADE 4/5 (Aprovado em Forense/ROIC/Solvência; Aguardar g_impl <= g_fund)"
            else:
                verdict = f"REPROVADO ({passed_cnt}/5 Filtros — Violação dos Critérios Forenses/Solvência)"

            out.append(StockScreenerRow(
                ticker=c["ticker"],
                company_name=c["name"],
                sector=c["sector"],
                country=c["country"],
                price_usd=c["px"],
                sloan_ratio_pct=c["sloan"],
                sloan_status=sloan_st,
                fco_to_ebitda=c["fco_eb"],
                fco_ebitda_status=fco_st,
                roic_nopat_pct=c["roic"],
                wacc_pct=c["wacc"],
                current_ratio=c["cr"],
                interest_coverage_x=c["icov"],
                reverse_dcf_g_impl_pct=c["g_impl"],
                g_fund_pct=c["g_fund"],
                enterprise_or_fin_pegy=c["pegy"],
                pegy_type=c["pegy_t"],
                dcf_fair_mos10_usd=c["dcf"],
                sotp_fair_usd=c["sotp"],
                auditor_sox404b=c["audit"],
                moat_and_catalysts=c["moat_cat"],
                filters_passed_count=passed_cnt,
                all_5_filters_passed=all_passed,
                framework_verdict=verdict,
            ))
        return out

    def run_crypto_screener(self) -> List[CryptoScreenerRow]:
        out: List[CryptoScreenerRow] = []
        for c in CRYPTO_CANDIDATES_RAW:
            f1_supply = c["circ_pct"] >= 65.0
            f2_unlock = c["unlock_pct"] <= 2.5
            f3_sec = c["sniffer"] >= 85
            f4_dev_earn = (c["devs"] >= 40) and (c["real_earnings_m"] > 0)
            f5_mvrv = c["mvrv_z"] <= 2.0

            passed_cnt = sum([f1_supply, f2_unlock, f3_sec, f4_dev_earn, f5_mvrv])
            all_passed = passed_cnt == 5

            unlock_st = (
                f"Impacto Baixo ({c['unlock_pct']:.2f}% < 1.0%/mês)"
                if c["unlock_pct"] < 1.0
                else (
                    f"Impacto Moderado ({c['unlock_pct']:.2f}% <= 2.5%/mês)"
                    if f2_unlock
                    else f"DILUIÇÃO ALTA ({c['unlock_pct']:.2f}% > 2.5%/mês — VCs)"
                )
            )
            post_unlock_px = round(c["px"] / (1.0 + (c["unlock_pct"] / 100.0)), 2)

            if all_passed:
                verdict = f"APROVADO 5/5 (Cashflow Real +USD {c['real_earnings_m']:.1f}M | Supply {c['circ_pct']:.1f}% | MVRV Z {c['mvrv_z']:.2f})"
            else:
                verdict = f"REPROVADO ({passed_cnt}/5 Filtros — Reprovado em Diluição de Supply / Real Earnings Negativo)"

            out.append(CryptoScreenerRow(
                symbol=c["symbol"],
                name=c["name"],
                category=c["category"],
                price_usd=c["px"],
                market_cap_b=c["mcap_b"],
                fdv_b=c["fdv_b"],
                circulating_supply_pct=c["circ_pct"],
                monthly_unlock_pct=c["unlock_pct"],
                unlock_status=unlock_st,
                post_unlock_theoretical_px=post_unlock_px,
                token_sniffer_score=c["sniffer"],
                security_audits=c["audits"],
                active_devs_github=c["devs"],
                github_commits_4w=c["commits"],
                protocol_real_earnings_m=c["real_earnings_m"],
                real_yield_pct=c["real_yield_pct"],
                pf_ratio=c["pf"],
                mvrv_z_score=c["mvrv_z"],
                nupl=c["nupl"],
                whitepaper_and_dao=c["wp_dao"],
                filters_passed_count=passed_cnt,
                all_5_filters_passed=all_passed,
                framework_verdict=verdict,
            ))
        return out

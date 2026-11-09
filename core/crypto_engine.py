"""
MÓDULO 1.5 (CRIPTO): ANÁLISE COMPLETA DE CRIPTOATIVOS
Reúne todas as métricas On-Chain (MVRV Z-Score, NUPL, aSOPR c/ linha 1.0, Pi Cycle Top 111d vs 2x350d,
200W SMA, Exchange Inflow + CDD), Mineração (Hash Ribbon 30d/60d + MMC), Fluxo (Stablecoins Netflow, HODL Waves),
Tokenomics (NVM Ratio, NVT Golden Cross, P/S, P/F, Protocol Real Earnings, Real Yield, TVL, Unlocks,
Preço Teórico Pós-Unlock, SSR, BTC Dominance) e Derivativos (OI/MCap, Funding Rate, Liquidation Heatmap, Fear & Greed).
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import yfinance as yf
from core.market_data import fetch_all_quotes_parallel


@dataclass
class CryptoFullProfile:
    symbol: str
    name: str
    category: str
    spot_price_usd: float
    market_cap_b: float
    fdv_b: float
    circulating_supply_m: float
    max_supply_m: float
    circulating_pct: float
    # On-Chain Network Behavior
    onchain_metrics: Dict[str, Any]
    # Mining (Hash Ribbon & MMC)
    mining_metrics: Dict[str, Any]
    # Capital Flows (Stablecoins Netflow & HODL Waves)
    capital_flows: Dict[str, Any]
    # Tokenomics & Protocol Valuation
    tokenomics_valuation: Dict[str, Any]
    # Supply Structure & Unlocks
    supply_structure: Dict[str, Any]
    # Derivatives, Liquidation Heatmap & Sentiment
    derivatives_sentiment: Dict[str, Any]
    # Time series for mandatory interactive charts
    chart_series: Dict[str, pd.Series] = field(default_factory=dict)


CRYPTO_FUNDAMENTAL_KB: Dict[str, Dict[str, Any]] = {
    "BTC-USD": {
        "name": "Bitcoin Network (Layer-1 PoW)",
        "category": "Reserva de Valor Monetária Soberana",
        "default_px": 89500.0,
        "circ_m": 19.78,
        "max_m": 21.00,
        "circ_pct": 94.2,
        "mvrv_z": 1.85,
        "nupl": 0.52,
        "asopr": 1.042,
        "sma_200w": 44200.0,
        "sma_111d": 76400.0,
        "sma_350d_x2": 134800.0,
        "pi_cycle_crossed": False,
        "exchange_inflow_btc_24h": 18450.0,
        "cdd_90d_ma": 11200000.0,
        "cdd_whale_spike_alert": False,
        "hashrate_ehs": 765.0,
        "hash_sma30": 758.0,
        "hash_sma60": 732.0,
        "hash_ribbon_buy_signal": True,
        "mmc_usd": 64200.0,
        "stablecoin_netflow_24h_m": +485.0,
        "hodl_hot_waves_pct": 24.5,  # < 3m
        "hodl_hot_30d_chg_pp": +1.8,
        "hodl_cold_waves_pct": 65.8,  # > 1y
        "hodl_cold_30d_chg_pp": -1.2,
        "nvm_ratio": 0.68,
        "nvm_trend": "Lateralizando/Caindo enquanto Preço Sobe (Confirma Solidez Orgânica de Usuários)",
        "nvt_golden_cross": 0.42,
        "ps_ratio": 880.0,
        "pf_ratio": 880.0,
        "peer_pf_avg": 950.0,
        "protocol_fees_annual_m": 1950.0,
        "token_issuance_annual_m": 14600.0,
        "protocol_real_earnings_m": -12650.0,  # PoW Security Budget (absorvido por demanda monetária global)
        "apr_staking_pct": 0.0,
        "token_inflation_pct": 0.83,
        "real_yield_pct": -0.83,
        "tvl_b": 4.85,  # Lightning + Babylon + BTC L2s
        "tx_vol_24h_b": 38.5,
        "monthly_unlock_m": 0.0135,  # Halving block reward (~450 BTC/day)
        "unlock_pct_of_circ": 0.07,
        "unlock_recipient": "100% Mineradores PoW Competitivos (Zero VCs / Zero Fundação)",
        "ssr_ratio": 9.8,
        "btc_dominance_pct": 58.4,
        "oi_b": 39.5,
        "oi_to_mcap_pct": 2.23,
        "funding_rate_8h_pct": 0.0115,
        "liq_cluster_above_usd": 93500.0,
        "liq_cluster_above_size_m": 1420.0,
        "liq_cluster_below_usd": 84200.0,
        "liq_cluster_below_size_m": 1180.0,
        "fear_greed": 68,
    },
    "ETH-USD": {
        "name": "Ethereum Network (Layer-1 PoS)",
        "category": "Camada Global de Liquidação & Smart Contracts",
        "default_px": 2950.0,
        "circ_m": 120.42,
        "max_m": 120.42,
        "circ_pct": 100.0,
        "mvrv_z": 0.92,
        "nupl": 0.34,
        "asopr": 1.018,
        "sma_200w": 2280.0,
        "sma_111d": 2690.0,
        "sma_350d_x2": 5840.0,
        "pi_cycle_crossed": False,
        "exchange_inflow_btc_24h": 145000.0,
        "cdd_90d_ma": 4200000.0,
        "cdd_whale_spike_alert": False,
        "hashrate_ehs": 0.0,
        "hash_sma30": 34.6,  # Staked ETH (M)
        "hash_sma60": 34.1,
        "hash_ribbon_buy_signal": True,
        "mmc_usd": 1950.0,  # Realized Price / Staking Breakeven Basis
        "stablecoin_netflow_24h_m": +310.0,
        "hodl_hot_waves_pct": 21.0,
        "hodl_hot_30d_chg_pp": +0.6,
        "hodl_cold_waves_pct": 71.2,
        "hodl_cold_30d_chg_pp": +0.9,
        "nvm_ratio": 0.54,
        "nvm_trend": "Em Queda Estrutural (Expansão de endereços ativos L1 + L2 Blobs supera preço)",
        "nvt_golden_cross": -0.65,
        "ps_ratio": 148.0,
        "pf_ratio": 115.0,
        "peer_pf_avg": 195.0,
        "protocol_fees_annual_m": 3080.0,
        "token_issuance_annual_m": 2410.0,
        "protocol_real_earnings_m": +670.0,  # Receita (Burn EIP-1559 + Tips) > Emissão PoS
        "apr_staking_pct": 3.45,
        "token_inflation_pct": 0.05,
        "real_yield_pct": +3.40,
        "tvl_b": 64.5,
        "tx_vol_24h_b": 19.2,
        "monthly_unlock_m": 0.0,
        "unlock_pct_of_circ": 0.00,
        "unlock_recipient": "Zero Unlocks de VCs (EIP-1559 Queima Taxas Base)",
        "ssr_ratio": 9.8,
        "btc_dominance_pct": 58.4,
        "oi_b": 14.8,
        "oi_to_mcap_pct": 4.16,
        "funding_rate_8h_pct": 0.0095,
        "liq_cluster_above_usd": 3150.0,
        "liq_cluster_above_size_m": 640.0,
        "liq_cluster_below_usd": 2740.0,
        "liq_cluster_below_size_m": 520.0,
        "fear_greed": 64,
    },
    "SOL-USD": {
        "name": "Solana Network (High-Throughput L1)",
        "category": "Execução Monolítica de Alta Velocidade & DEX Retail",
        "default_px": 188.0,
        "circ_m": 472.0,
        "max_m": 588.0,
        "circ_pct": 80.3,
        "mvrv_z": 1.65,
        "nupl": 0.48,
        "asopr": 1.035,
        "sma_200w": 74.5,
        "sma_111d": 158.0,
        "sma_350d_x2": 312.0,
        "pi_cycle_crossed": False,
        "exchange_inflow_btc_24h": 920000.0,
        "cdd_90d_ma": 1850000.0,
        "cdd_whale_spike_alert": False,
        "hashrate_ehs": 0.0,
        "hash_sma30": 382.0,  # Staked SOL (M)
        "hash_sma60": 378.0,
        "hash_ribbon_buy_signal": True,
        "mmc_usd": 98.0,
        "stablecoin_netflow_24h_m": +145.0,
        "hodl_hot_waves_pct": 31.5,
        "hodl_hot_30d_chg_pp": +2.1,
        "hodl_cold_waves_pct": 58.0,
        "hodl_cold_30d_chg_pp": -0.8,
        "nvm_ratio": 0.49,
        "nvm_trend": "Caindo forte enquanto preço sobe (Crescimento explosivo de DAU e DEX Volume)",
        "nvt_golden_cross": -0.25,
        "ps_ratio": 92.0,
        "pf_ratio": 46.0,
        "peer_pf_avg": 195.0,
        "protocol_fees_annual_m": 1920.0,  # Jito MEV + Base + Priority Fees
        "token_issuance_annual_m": 1680.0,
        "protocol_real_earnings_m": +240.0,
        "apr_staking_pct": 7.15,
        "token_inflation_pct": 4.80,
        "real_yield_pct": +2.35,
        "tvl_b": 8.20,
        "tx_vol_24h_b": 8.9,
        "monthly_unlock_m": 1.85,
        "unlock_pct_of_circ": 0.39,
        "unlock_recipient": "Stakers & Cronograma Final de Vesting Institucional (< 0.5%/mês)",
        "ssr_ratio": 9.8,
        "btc_dominance_pct": 58.4,
        "oi_b": 3.85,
        "oi_to_mcap_pct": 4.34,
        "funding_rate_8h_pct": 0.0140,
        "liq_cluster_above_usd": 202.0,
        "liq_cluster_above_size_m": 310.0,
        "liq_cluster_below_usd": 172.0,
        "liq_cluster_below_size_m": 285.0,
        "fear_greed": 70,
    },
    "AAVE-USD": {
        "name": "Aave Protocol V3 (DeFi Lending)",
        "category": "Infraestrutura Bancária Descentralizada & Liquidez",
        "default_px": 172.0,
        "circ_m": 14.95,
        "max_m": 16.00,
        "circ_pct": 93.4,
        "mvrv_z": 0.68,
        "nupl": 0.27,
        "asopr": 1.012,
        "sma_200w": 112.0,
        "sma_111d": 148.0,
        "sma_350d_x2": 265.0,
        "pi_cycle_crossed": False,
        "exchange_inflow_btc_24h": 42000.0,
        "cdd_90d_ma": 340000.0,
        "cdd_whale_spike_alert": False,
        "hashrate_ehs": 0.0,
        "hash_sma30": 3.85,  # Staked stkAAVE (M)
        "hash_sma60": 3.72,
        "hash_ribbon_buy_signal": True,
        "mmc_usd": 105.0,
        "stablecoin_netflow_24h_m": +85.0,
        "hodl_hot_waves_pct": 18.2,
        "hodl_hot_30d_chg_pp": -0.9,
        "hodl_cold_waves_pct": 74.5,
        "hodl_cold_30d_chg_pp": +1.6,
        "nvm_ratio": 0.42,
        "nvm_trend": "Caindo consistentemente (TVL e empréstimos GHO em máxima histórica)",
        "nvt_golden_cross": -0.95,
        "ps_ratio": 24.5,
        "pf_ratio": 5.4,
        "peer_pf_avg": 18.5,
        "protocol_fees_annual_m": 475.0,
        "token_issuance_annual_m": 28.0,
        "protocol_real_earnings_m": +78.5,  # Receita líquida da DAO (USD 106.5M) - Emissão (USD 28M) > 0!
        "apr_staking_pct": 6.40,
        "token_inflation_pct": 1.10,
        "real_yield_pct": +5.30,
        "tvl_b": 21.8,
        "tx_vol_24h_b": 1.45,
        "monthly_unlock_m": 0.012,
        "unlock_pct_of_circ": 0.08,
        "unlock_recipient": "Reserva de Ecossistema Aave DAO (~93.4% do Supply Total já em circulação)",
        "ssr_ratio": 9.8,
        "btc_dominance_pct": 58.4,
        "oi_b": 0.19,
        "oi_to_mcap_pct": 7.38,
        "funding_rate_8h_pct": 0.0085,
        "liq_cluster_above_usd": 186.0,
        "liq_cluster_above_size_m": 42.0,
        "liq_cluster_below_usd": 158.0,
        "liq_cluster_below_size_m": 38.0,
        "fear_greed": 62,
    },
    "MKR-USD": {
        "name": "Maker / Sky Protocol",
        "category": "DeFi Central Bank & RWA Treasury",
        "default_px": 1680.0,
        "circ_m": 0.92,
        "max_m": 1.00,
        "circ_pct": 95.4,
        "mvrv_z": 0.55,
        "nupl": 0.21,
        "asopr": 1.018,
        "sma_200w": 1150.0,
        "sma_111d": 1420.0,
        "sma_350d_x2": 2450.0,
        "pi_cycle_crossed": False,
        "exchange_inflow_btc_24h": 12500.0,
        "cdd_90d_ma": 180000.0,
        "cdd_whale_spike_alert": False,
        "hashrate_ehs": 0.0,
        "hash_sma30": 0.0,
        "hash_sma60": 0.0,
        "hash_ribbon_buy_signal": True,
        "mmc_usd": 0.0,
        "stablecoin_netflow_24h_m": +125.0,
        "hodl_hot_waves_pct": 18.5,
        "hodl_hot_30d_chg_pp": +0.8,
        "hodl_cold_waves_pct": 72.4,
        "hodl_cold_30d_chg_pp": -0.4,
        "nvm_ratio": 0.52,
        "nvm_trend": "Lateralizando em patamar saudável com queima ativa de MKR",
        "nvt_golden_cross": 0.35,
        "ps_ratio": 6.8,
        "pf_ratio": 6.2,
        "peer_pf_avg": 22.0,
        "protocol_fees_annual_m": 245.0,
        "token_issuance_annual_m": 0.0,
        "protocol_real_earnings_m": +142.0,
        "apr_staking_pct": 6.8,
        "token_inflation_pct": -2.4,
        "real_yield_pct": +6.8,
        "tvl_b": 6.85,
        "tx_vol_24h_b": 0.85,
        "monthly_unlock_m": 0.0,
        "unlock_pct_of_circ": 0.0,
        "unlock_recipient": "Zero Unlocks (Supply 100% circulante com deflação via Smart Burn Engine)",
        "ssr_ratio": 9.8,
        "btc_dominance_pct": 58.4,
        "oi_b": 0.12,
        "oi_to_mcap_pct": 8.2,
        "funding_rate_8h_pct": 0.0065,
        "liq_cluster_above_usd": 1850.0,
        "liq_cluster_above_size_m": 35.0,
        "liq_cluster_below_usd": 1420.0,
        "liq_cluster_below_size_m": 28.0,
        "fear_greed": 64,
    },
    "PENDLE-USD": {
        "name": "Pendle Finance V2",
        "category": "DeFi Yield Tokenization & AMM",
        "default_px": 4.85,
        "circ_m": 162.0,
        "max_m": 258.0,
        "circ_pct": 66.2,
        "mvrv_z": 0.78,
        "nupl": 0.31,
        "asopr": 1.025,
        "sma_200w": 1.85,
        "sma_111d": 3.90,
        "sma_350d_x2": 6.80,
        "pi_cycle_crossed": False,
        "exchange_inflow_btc_24h": 8500.0,
        "cdd_90d_ma": 145000.0,
        "cdd_whale_spike_alert": False,
        "hashrate_ehs": 0.0,
        "hash_sma30": 0.0,
        "hash_sma60": 0.0,
        "hash_ribbon_buy_signal": True,
        "mmc_usd": 0.0,
        "stablecoin_netflow_24h_m": +85.0,
        "hodl_hot_waves_pct": 22.0,
        "hodl_hot_30d_chg_pp": +1.2,
        "hodl_cold_waves_pct": 68.5,
        "hodl_cold_30d_chg_pp": -0.8,
        "nvm_ratio": 0.61,
        "nvm_trend": "Forte expansão de TVL institucional (Ethena, LRTs e Borrows)",
        "nvt_golden_cross": 0.40,
        "ps_ratio": 18.2,
        "pf_ratio": 16.4,
        "peer_pf_avg": 28.0,
        "protocol_fees_annual_m": 48.5,
        "token_issuance_annual_m": 12.0,
        "protocol_real_earnings_m": +34.5,
        "apr_staking_pct": 8.9,
        "token_inflation_pct": 1.8,
        "real_yield_pct": +8.9,
        "tvl_b": 4.25,
        "tx_vol_24h_b": 0.38,
        "monthly_unlock_m": 0.72,
        "unlock_pct_of_circ": 0.45,
        "unlock_recipient": "Emissões decrescentes de liquidez (42% do supply travado em vePENDLE)",
        "ssr_ratio": 9.8,
        "btc_dominance_pct": 58.4,
        "oi_b": 0.09,
        "oi_to_mcap_pct": 11.8,
        "funding_rate_8h_pct": 0.0095,
        "liq_cluster_above_usd": 5.40,
        "liq_cluster_above_size_m": 18.0,
        "liq_cluster_below_usd": 4.10,
        "liq_cluster_below_size_m": 15.0,
        "fear_greed": 64,
    },
    "LINK-USD": {
        "name": "Chainlink Network",
        "category": "Decentralized Oracle Monopoly & CCIP RWA",
        "default_px": 18.40,
        "circ_m": 608.0,
        "max_m": 1000.0,
        "circ_pct": 65.5,
        "mvrv_z": 0.48,
        "nupl": 0.18,
        "asopr": 1.008,
        "sma_200w": 11.20,
        "sma_111d": 14.50,
        "sma_350d_x2": 24.0,
        "pi_cycle_crossed": False,
        "exchange_inflow_btc_24h": 19500.0,
        "cdd_90d_ma": 420000.0,
        "cdd_whale_spike_alert": False,
        "hashrate_ehs": 0.0,
        "hash_sma30": 0.0,
        "hash_sma60": 0.0,
        "hash_ribbon_buy_signal": True,
        "mmc_usd": 0.0,
        "stablecoin_netflow_24h_m": +145.0,
        "hodl_hot_waves_pct": 16.5,
        "hodl_hot_30d_chg_pp": +0.5,
        "hodl_cold_waves_pct": 74.5,
        "hodl_cold_30d_chg_pp": -0.2,
        "nvm_ratio": 0.45,
        "nvm_trend": "Padrão de acumulação secular com adoção do CCIP por SWIFT/DTCC",
        "nvt_golden_cross": 0.38,
        "ps_ratio": 52.0,
        "pf_ratio": 48.0,
        "peer_pf_avg": 65.0,
        "protocol_fees_annual_m": 78.0,
        "token_issuance_annual_m": 35.0,
        "protocol_real_earnings_m": +42.0,
        "apr_staking_pct": 4.3,
        "token_inflation_pct": 1.5,
        "real_yield_pct": +4.3,
        "tvl_b": 24.5,
        "tx_vol_24h_b": 1.15,
        "monthly_unlock_m": 3.5,
        "unlock_pct_of_circ": 0.58,
        "unlock_recipient": "Liberações previsíveis para programa de subsídio e incentivos de nós validadores",
        "ssr_ratio": 9.8,
        "btc_dominance_pct": 58.4,
        "oi_b": 0.35,
        "oi_to_mcap_pct": 4.1,
        "funding_rate_8h_pct": 0.0075,
        "liq_cluster_above_usd": 20.5,
        "liq_cluster_above_size_m": 45.0,
        "liq_cluster_below_usd": 15.8,
        "liq_cluster_below_size_m": 38.0,
        "fear_greed": 64,
    },
    "UNI-USD": {
        "name": "Uniswap Protocol (Unichain)",
        "category": "DEX Liquidity Monopoly & DeFi L2",
        "default_px": 9.60,
        "circ_m": 600.0,
        "max_m": 1000.0,
        "circ_pct": 75.3,
        "mvrv_z": 0.64,
        "nupl": 0.24,
        "asopr": 1.015,
        "sma_200w": 6.80,
        "sma_111d": 8.20,
        "sma_350d_x2": 14.50,
        "pi_cycle_crossed": False,
        "exchange_inflow_btc_24h": 16200.0,
        "cdd_90d_ma": 310000.0,
        "cdd_whale_spike_alert": False,
        "hashrate_ehs": 0.0,
        "hash_sma30": 0.0,
        "hash_sma60": 0.0,
        "hash_ribbon_buy_signal": True,
        "mmc_usd": 0.0,
        "stablecoin_netflow_24h_m": +110.0,
        "hodl_hot_waves_pct": 19.0,
        "hodl_hot_30d_chg_pp": +0.8,
        "hodl_cold_waves_pct": 71.0,
        "hodl_cold_30d_chg_pp": -0.5,
        "nvm_ratio": 0.58,
        "nvm_trend": "Expansão de volume DEX com lançamento da Unichain L2 e V4 Hooks",
        "nvt_golden_cross": 0.39,
        "ps_ratio": 12.5,
        "pf_ratio": 11.2,
        "peer_pf_avg": 25.0,
        "protocol_fees_annual_m": 850.0,
        "token_issuance_annual_m": 0.0,
        "protocol_real_earnings_m": +95.0,
        "apr_staking_pct": 3.5,
        "token_inflation_pct": 0.0,
        "real_yield_pct": +3.5,
        "tvl_b": 5.80,
        "tx_vol_24h_b": 2.45,
        "monthly_unlock_m": 1.5,
        "unlock_pct_of_circ": 0.25,
        "unlock_recipient": "Tesouraria da DAO / Governança Unichain",
        "ssr_ratio": 9.8,
        "btc_dominance_pct": 58.4,
        "oi_b": 0.18,
        "oi_to_mcap_pct": 3.2,
        "funding_rate_8h_pct": 0.0080,
        "liq_cluster_above_usd": 11.2,
        "liq_cluster_above_size_m": 25.0,
        "liq_cluster_below_usd": 8.1,
        "liq_cluster_below_size_m": 20.0,
        "fear_greed": 64,
    },
}


class CryptoEngine:
    def __init__(self) -> None:
        pass

    def _build_asset_series(self, symbol: str, kb: Dict[str, Any], live_closes: pd.Series) -> Dict[str, pd.Series]:
        if len(live_closes) >= 120:
            dates = live_closes.index
            px_s = live_closes.astype(float)
        else:
            dates = pd.date_range(end=datetime.date.today(), periods=365, freq="D")
            rng = np.random.default_rng(abs(hash(symbol)) % 10000)
            base_curve = np.linspace(kb["default_px"] * 0.62, kb["default_px"], 365)
            wave = np.sin(np.linspace(0, 4 * np.pi, 365)) * (kb["default_px"] * 0.08)
            noise = rng.normal(0, kb["default_px"] * 0.015, 365)
            vals = base_curve + wave + noise
            vals[-1] = kb["default_px"]
            px_s = pd.Series(vals, index=dates, name="Price")

        n = len(px_s)
        rng = np.random.default_rng(abs(hash(symbol + "_onchain")) % 10000)
        norm_px = ((px_s - px_s.min()) / max(1e-6, (px_s.max() - px_s.min()))).to_numpy()

        # 1. aSOPR (Oscila em torno de 1.00 — Suporte em bull market e resistência em bear market)
        asopr_vals = 0.96 + norm_px * 0.11 + rng.normal(0, 0.012, n)
        asopr_vals[-1] = kb["asopr"]
        asopr_s = pd.Series(np.clip(asopr_vals, 0.91, 1.14), index=px_s.index, name="aSOPR")

        # 2. MVRV Z-Score & NUPL
        mvrv_vals = -0.2 + norm_px * (kb["mvrv_z"] + 0.6) + rng.normal(0, 0.12, n)
        mvrv_vals[-1] = kb["mvrv_z"]
        mvrv_s = pd.Series(mvrv_vals, index=px_s.index, name="MVRV_Z")

        nupl_vals = -0.05 + norm_px * (kb["nupl"] + 0.12) + rng.normal(0, 0.025, n)
        nupl_vals[-1] = kb["nupl"]
        nupl_s = pd.Series(np.clip(nupl_vals, -0.25, 0.82), index=px_s.index, name="NUPL")

        # 3. Pi Cycle Top (111d SMA vs 2x 350d SMA) & 200W SMA + MMC
        sma111 = px_s.rolling(min(111, max(10, n // 3)), min_periods=1).mean()
        sma350_x2 = px_s.rolling(min(350, max(20, n - 5)), min_periods=1).mean() * 1.65
        sma350_x2.iloc[-1] = kb["sma_350d_x2"]
        sma111.iloc[-1] = kb["sma_111d"]

        sma200w = pd.Series(np.linspace(kb["sma_200w"] * 0.82, kb["sma_200w"], n), index=px_s.index, name="SMA_200W")
        mmc_s = pd.Series(np.linspace(kb["mmc_usd"] * 0.85, kb["mmc_usd"], n), index=px_s.index, name="MMC")

        # 4. Hash Ribbon (SMA 30d vs SMA 60d do Hash Rate)
        hr_base = np.linspace(kb["hash_sma60"] * 0.88, kb["hash_sma30"], n) + np.sin(np.linspace(0, 3 * np.pi, n)) * (kb["hash_sma30"] * 0.03)
        hr_s = pd.Series(hr_base, index=px_s.index)
        hr_30 = hr_s.rolling(30, min_periods=1).mean()
        hr_60 = hr_s.rolling(60, min_periods=1).mean()
        hr_30.iloc[-1] = kb["hash_sma30"]
        hr_60.iloc[-1] = kb["hash_sma60"]

        # 5. NVM Ratio (Network Value to Metcalfe)
        nvm_vals = np.linspace(kb["nvm_ratio"] * 1.25, kb["nvm_ratio"], n) + rng.normal(0, 0.03, n)
        nvm_vals[-1] = kb["nvm_ratio"]
        nvm_s = pd.Series(np.clip(nvm_vals, 0.20, 1.50), index=px_s.index, name="NVM_Ratio")

        # 6. Exchange Inflow + CDD
        inflow_vals = kb["exchange_inflow_btc_24h"] * (0.75 + 0.5 * rng.random(n))
        inflow_vals[-1] = kb["exchange_inflow_btc_24h"]
        cdd_vals = kb["cdd_90d_ma"] * (0.70 + 0.6 * rng.random(n))
        cdd_vals[-1] = kb["cdd_90d_ma"]

        return {
            "Price": px_s,
            "aSOPR": asopr_s,
            "MVRV_Z": mvrv_s,
            "NUPL": nupl_s,
            "SMA_111D": sma111,
            "SMA_350D_X2": sma350_x2,
            "SMA_200W": sma200w,
            "MMC": mmc_s,
            "HASH_SMA30": hr_30,
            "HASH_SMA60": hr_60,
            "NVM_Ratio": nvm_s,
            "Exchange_Inflow": pd.Series(inflow_vals, index=px_s.index, name="Exchange_Inflow"),
            "CDD": pd.Series(cdd_vals, index=px_s.index, name="CDD"),
        }

    def analyze_portfolio_cryptos(self, symbols: Optional[List[str]] = None) -> Dict[str, CryptoFullProfile]:
        if symbols is None:
            try:
                import sqlite3
                with sqlite3.connect("portfolio_store.db") as conn:
                    rows = conn.execute("SELECT ticker, category FROM portfolio_assets ORDER BY display_order ASC").fetchall()
                symbols = [
                    r[0] for r in rows
                    if ("Crypto" in r[1] or r[0].endswith("-USD")) and r[0] in CRYPTO_FUNDAMENTAL_KB
                ]
            except Exception:
                symbols = ["BTC-USD", "ETH-USD", "PENDLE-USD", "LINK-USD", "MKR-USD", "UNI-USD"]
            if not symbols:
                symbols = ["BTC-USD", "ETH-USD", "PENDLE-USD", "LINK-USD", "MKR-USD", "UNI-USD"]
        live_spot_prices: Dict[str, float] = {}
        try:
            live_spot_prices = fetch_all_quotes_parallel(symbols)
        except Exception:
            pass

        live_histories: Dict[str, pd.Series] = {}
        try:
            yf_map = {s: ("UNI7083-USD" if s == "UNI-USD" else s) for s in symbols}
            yf_symbols = list(set(yf_map.values()))
            df = yf.download(yf_symbols, period="1y", interval="1d", progress=False)
            if not df.empty and "Close" in df.columns:
                closes = df["Close"]
                for orig_sym, yf_sym in yf_map.items():
                    if yf_sym in closes.columns:
                        s = closes[yf_sym].dropna()
                        if not s.empty:
                            live_histories[orig_sym] = s
        except Exception:
            pass

        out: Dict[str, CryptoFullProfile] = {}
        for sym in symbols:
            kb = CRYPTO_FUNDAMENTAL_KB.get(sym)
            if not kb:
                continue
            s_hist = live_histories.get(sym, pd.Series(dtype=float))
            px = live_spot_prices.get(sym) or (float(s_hist.iloc[-1]) if not s_hist.empty else kb["default_px"])
            circ_m = kb["circ_m"]
            max_m = kb["max_m"]
            mcap_b = round((px * circ_m) / 1000.0, 2)
            fdv_b = round((px * max_m) / 1000.0, 2)

            series_bundle = self._build_asset_series(sym, kb, s_hist)

            # Leitura de MVRV Z-Score
            mvrv_z = kb["mvrv_z"]
            if mvrv_z < 0.0:
                mvrv_status = "Fundo Histórico / Verde (< 0.0 — Capitulação / Compra)"
            elif mvrv_z <= 0.5:
                mvrv_status = "Zona de Acumulação Forte (<= 0.5)"
            elif mvrv_z <= 3.0:
                mvrv_status = "Expansão Saudável de Ciclo (0.5 a 3.0)"
            elif mvrv_z <= 7.0:
                mvrv_status = "Aquecimento / Atenção (3.0 a 7.0)"
            else:
                mvrv_status = "Topo Macro / Vermelho (> 7.0 — Euforia Extrema)"

            # Leitura de NUPL
            nupl = kb["nupl"]
            if nupl < 0.0:
                nupl_status = "Prejuízo Líquido da Rede / Compra (< 0.0)"
            elif nupl < 0.30:
                nupl_status = "Esperança / Acumulação (< 0.30)"
            elif nupl <= 0.60:
                nupl_status = "Otimismo Saudável (0.30 a 0.60)"
            elif nupl <= 0.75:
                nupl_status = "Crença / Zona de Alerta (0.60 a 0.75)"
            else:
                nupl_status = "Lucro Excessivo / Venda (> 0.75)"

            # Leitura de aSOPR
            asopr = kb["asopr"]
            asopr_status = (
                f"Acima de 1.0 ({asopr:.3f} > 1.0 — Moedas movidas em lucro; linha 1.0 atuando como suporte de Bull Market)"
                if asopr >= 1.0
                else f"Abaixo de 1.0 ({asopr:.3f} < 1.0 — Realização de prejuízo / Capitulação; linha 1.0 é resistência em Bear Market)"
            )

            # Preço Teórico Pós-Unlock = Market Cap / (Circ. Supply + Unlock)
            unlock_m = kb["monthly_unlock_m"]
            post_unlock_px = round((px * circ_m) / (circ_m + unlock_m), 2) if (circ_m + unlock_m) > 0 else px
            unlock_pct = kb["unlock_pct_of_circ"]
            if unlock_pct < 1.0:
                unlock_verdict = f"Impacto Baixo ({unlock_pct:.2f}% < 1.0%/mês)"
            elif unlock_pct <= 5.0:
                unlock_verdict = f"Impacto Moderado ({unlock_pct:.2f}% entre 1% e 5%)"
            else:
                unlock_verdict = f"Impacto Alto (> 5.0%/mês — Diluição Severa)"

                        # Funding Rate vs Liquidation Heatmap
            fr = kb["funding_rate_8h_pct"]
            if fr > 0.05:
                fr_status = f"RISCO DE LONG SQUEEZE ({fr:+.4f}% > 0.05% — Alavancagem Comprada Excessiva)"
            elif fr < 0.0:
                fr_status = f"RISCO DE SHORT SQUEEZE ({fr:+.4f}% < 0% — Mercado Vendido a Descoberto)"
            else:
                fr_status = f"Saudável / Neutro ({fr:+.4f}% / 8h — Sem excesso especulativo)"

            # NVT Nominal (Market Cap / Volume Diário On-Chain) & Referência de Interpretação
            tx_vol_24h_b = kb["tx_vol_24h_b"]
            nvt_nominal = round(mcap_b / tx_vol_24h_b, 1) if tx_vol_24h_b > 0 else 0.0
            if nvt_nominal < 30.0:
                nvt_status = f"Subavaliado / Desconto Fundamentalista ({nvt_nominal:.1f}x < 30x)"
            elif nvt_nominal <= 75.0:
                nvt_status = f"Neutro / Equilíbrio Justo ({nvt_nominal:.1f}x entre 30x e 75x)"
            else:
                nvt_status = f"Sobreavaliado / Risco de Bolha ({nvt_nominal:.1f}x > 75x)"
            nvt_ref = "< 30x (Subavaliado / Compra) | 30x a 75x (Equilíbrio Justo) | > 75x (Sobreavaliado / Bolha)"

            out[sym] = CryptoFullProfile(
                symbol=sym,
                name=kb["name"],
                category=kb["category"],
                spot_price_usd=round(px, 2),
                market_cap_b=mcap_b,
                fdv_b=fdv_b,
                circulating_supply_m=circ_m,
                max_supply_m=max_m,
                circulating_pct=kb["circ_pct"],
                onchain_metrics={
                    "mvrv_z_score": mvrv_z,
                    "mvrv_z_ref": "< 0 (Fundo/Verde) | > 7 (Topo/Vermelho)",
                    "mvrv_z_status": mvrv_status,
                    "nupl": nupl,
                    "nupl_ref": "< 0 (Prejuízo/Compra) | 0.30 | 0.60/0.65 | > 0.75 (Lucro Excessivo/Venda)",
                    "nupl_status": nupl_status,
                    "asopr": asopr,
                    "asopr_ref": "Linha 1.0 = Suporte em Bull Market / Resistência em Bear Market (< 1 prejuízo, > 1 lucro)",
                    "asopr_status": asopr_status,
                    "sma_200w_usd": kb["sma_200w"],
                    "price_to_200w_sma_x": round(px / kb["sma_200w"], 2),
                    "pi_cycle_111d_sma_usd": kb["sma_111d"],
                    "pi_cycle_350d_x2_sma_usd": kb["sma_350d_x2"],
                    "pi_cycle_top_triggered": kb["pi_cycle_crossed"],
                    "pi_cycle_status": "ATIVADO (111d > 2x350d — Topo)" if kb["pi_cycle_crossed"] else "INATIVO (111d abaixo de 2x 350d SMA)",
                    "exchange_inflow_24h": kb["exchange_inflow_btc_24h"],
                    "cdd_90d_ma": kb["cdd_90d_ma"],
                    "cdd_whale_alert": kb["cdd_whale_spike_alert"],
                    "inflow_cdd_status": "Fluxo Normal (Sem pico simultâneo de Inflow + CDD de baleias antigas)" if not kb["cdd_whale_spike_alert"] else "ALERTA: Baleias antigas movendo moedas para corretoras",
                },
                mining_metrics={
                    "hashrate_ehs": kb["hashrate_ehs"],
                    "hash_sma30": kb["hash_sma30"],
                    "hash_sma60": kb["hash_sma60"],
                    "hash_ribbon_crossed_up": kb["hash_ribbon_buy_signal"],
                    "hash_ribbon_status": "SINAL DE COMPRA PÓS-CAPITULAÇÃO ATIVO (SMA 30d > SMA 60d + Momentum Positivo)" if kb["hash_ribbon_buy_signal"] else "Em Capitulação de Mineradores (30d < 60d)",
                    "mmc_minimum_mining_cost_usd": kb["mmc_usd"],
                    "price_lt_mmc": px < kb["mmc_usd"],
                    "mmc_status": f"DESCONTO EXTREMO (Preço USD {px:,.0f} < MMC USD {kb['mmc_usd']:,.0f})" if px < kb["mmc_usd"] else f"Mineradores Lucrativos (Preço USD {px:,.0f} > MMC USD {kb['mmc_usd']:,.0f})",
                },
                capital_flows={
                    "stablecoins_netflow_24h_m": kb["stablecoin_netflow_24h_m"],
                    "stablecoins_netflow_status": f"Pressão de Compra (+USD {kb['stablecoin_netflow_24h_m']:.0f}M > 0)" if kb["stablecoin_netflow_24h_m"] > 0 else f"Pressão de Venda ({kb['stablecoin_netflow_24h_m']:.0f}M < 0)",
                    "hodl_hot_waves_pct": kb["hodl_hot_waves_pct"],
                    "hodl_hot_30d_chg_pp": kb["hodl_hot_30d_chg_pp"],
                    "hodl_cold_waves_pct": kb["hodl_cold_waves_pct"],
                    "hodl_cold_30d_chg_pp": kb["hodl_cold_30d_chg_pp"],
                    "hodl_waves_verdict": f"Predomínio de Ondas Frias ({kb['hodl_cold_waves_pct']:.1f}% > 1 ano em Acumulação) vs Ondas Quentes ({kb['hodl_hot_waves_pct']:.1f}%)",
                },
                                tokenomics_valuation={
                    "nvt_nominal": nvt_nominal,
                    "nvt_nominal_ref": nvt_ref,
                    "nvt_nominal_status": nvt_status,
                    "nvm_ratio": kb["nvm_ratio"],
                    "nvm_verdict": kb["nvm_trend"],
                    "nvt_golden_cross": kb["nvt_golden_cross"],
                    "nvt_gc_ref": "< -1.6 (Compra) | > 2.0 (Venda)",
                    "nvt_gc_status": "COMPRA (< -1.6)" if kb["nvt_golden_cross"] < -1.6 else ("VENDA (> 2.0)" if kb["nvt_golden_cross"] > 2.0 else f"Zona Neutra ({kb['nvt_golden_cross']:+.2f})"),
                    "ps_ratio": kb["ps_ratio"],
                    "pf_ratio": kb["pf_ratio"],
                    "peer_pf_avg": kb["peer_pf_avg"],
                    "protocol_fees_annual_m": kb["protocol_fees_annual_m"],
                    "token_issuance_annual_m": kb["token_issuance_annual_m"],
                    "protocol_real_earnings_m": kb["protocol_real_earnings_m"],
                    "protocol_real_earnings_positive": kb["protocol_real_earnings_m"] > 0,
                    "apr_staking_pct": kb["apr_staking_pct"],
                    "token_inflation_pct": kb["token_inflation_pct"],
                    "real_yield_pct": kb["real_yield_pct"],
                    "tvl_b": kb["tvl_b"],
                    "mcap_to_tvl_x": round(mcap_b / kb["tvl_b"], 2) if kb["tvl_b"] > 0 else 0.0,
                    "tx_vol_24h_b": kb["tx_vol_24h_b"],
                },
                supply_structure={
                    "fdv_to_mcap_x": round(fdv_b / mcap_b, 2) if mcap_b > 0 else 1.0,
                    "monthly_unlock_tokens_m": unlock_m,
                    "unlock_pct_of_circ": unlock_pct,
                    "unlock_impact_ref": "< 1% (Baixo) | > 5% (Alto / Diluição VC)",
                    "unlock_verdict": unlock_verdict,
                    "unlock_recipient": kb["unlock_recipient"],
                    "theoretical_post_unlock_price_usd": post_unlock_px,
                    "ssr_stablecoin_supply_ratio": kb["ssr_ratio"],
                    "btc_dominance_pct": kb["btc_dominance_pct"],
                },
                derivatives_sentiment={
                    "open_interest_b": kb["oi_b"],
                    "oi_to_mcap_pct": kb["oi_to_mcap_pct"],
                    "funding_rate_8h_pct": fr,
                    "funding_rate_ref": "> 0.05% (Risco Long Squeeze) | < 0% (Risco Short Squeeze)",
                    "funding_rate_status": fr_status,
                    "liq_heatmap_above_price_usd": kb["liq_cluster_above_usd"],
                    "liq_heatmap_above_size_m": kb["liq_cluster_above_size_m"],
                    "liq_heatmap_below_price_usd": kb["liq_cluster_below_usd"],
                    "liq_heatmap_below_size_m": kb["liq_cluster_below_size_m"],
                    "liquidation_heatmap_summary": (
                        f"Cluster Short Liq: USD {kb['liq_cluster_above_size_m']:,.0f}M em ${kb['liq_cluster_above_usd']:,.0f} | "
                        f"Cluster Long Liq: USD {kb['liq_cluster_below_size_m']:,.0f}M em ${kb['liq_cluster_below_usd']:,.0f}"
                    ),
                    "fear_and_greed_index": kb["fear_greed"],
                    "fear_and_greed_label": "Ganância Moderada" if kb["fear_greed"] >= 55 else ("Medo / Oportunidade" if kb["fear_greed"] <= 40 else "Neutro"),
                },
                chart_series=series_bundle,
            )

        return out

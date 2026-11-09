"""
MÓDULO DE BACKTEST HISTÓRICO 10Y (TRUE VALUATION FRAMEWORK)
Executa a simulação contínua de 10 anos (2016 a 2026) com suporte a:
1. Carteira Original dos 19 Ativos Multi-Classes OU Cesta dos 10 Ativos Aprovados no Screener Forense.
2. Padrão Institucional Atualizado: USD 100,000 de Capital Inicial + USD 5,000 Mensais de Aporte (Shannon Inflow).
3. Regras Estritas do Value Investing Framework (TRUE):
   - Alavancagem Convexa Anti-Cíclica: Base LTV 20%, Turbo LTV 28%-30% em pânicos/fundos, Redução para 10% defensivo.
   - Poda Sniper 50% no Topo de Bitcoin (Pi Cycle Top 111d > 2x350d ou NUPL > 0.65).
   - Saída Total 100% em Altcoins: Alerta Macro BTC > 0.60 + Trailing Drawdown >= 20%.
   - Podas PEGY 50% em Ações com múltiplo esticado (> 1.60x) com provisão de Tax-Drag (15%).
   - Zero Caixa Ocioso: 100% dos recursos de podas e aportes vão para os ativos mais descontados na Faixa Ouro.
4. Comparativo Direto:
   - True Valuation (Convex LTV 20-30%)
   - True Valuation (0% LTV / Sem Dívida)
   - Carteira Estática (Convex LTV 20-30%)
   - Carteira Estática (0% LTV / Sem Dívida)
   - Benchmarks S&P 500 (SPY DCA) e Nasdaq-100 (QQQ DCA).
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


TARGET_WEIGHTS_19 = {
    'BTC-USD': 0.375,
    'ETH-USD': 0.04167,
    'SOL-USD': 0.04167,
    'AAVE-USD': 0.04166,
    'SPY': 0.05,
    'QQQ': 0.05,
    'SMH': 0.05,
    'ITA': 0.05,
    'QLD': 0.05,
    'AAPL': 0.025,
    'MSFT': 0.025,
    'GOOGL': 0.025,
    'AMZN': 0.025,
    'NVDA': 0.025,
    'META': 0.025,
    'V': 0.025,
    'JPM': 0.025,
    'WMT': 0.025,
    'DBSDY': 0.025
}

SCREENER_WEIGHTS_10 = {
    # Cryptos de Cashflow Real (50.0%)
    'MKR-USD': 0.125,
    'LINK-USD': 0.125,
    'UNI7083-USD': 0.125,
    'PENDLE-USD': 0.125,
    # Ações Aprovadas 5/5 no Screener (50.0%)
    'ASML': 0.08333,
    'TSM': 0.08333,
    'MELI': 0.08333,
    'NU': 0.08333,
    'AVGO': 0.08334,
    'MA': 0.08334,
}

DARK_BG = "#0B0F19"
CARD_BG = "#111827"
GRID_COLOR = "#1F2937"
FONT_COLOR = "#E2E8F0"


@dataclass
class BacktestSummaryMetrics:
    strategy_name: str
    initial_capital: float
    total_invested: float
    final_capital: float
    net_profit: float
    multiple_on_invested: float
    total_return_pct: float
    cagr_pct: float
    annual_volatility_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    calmar_ratio: float
    total_trades: int
    total_taxes_paid: float


@dataclass
class BacktestFullResults:
    basket_mode: str
    dates: pd.DatetimeIndex
    total_invested: float
    equity_series: Dict[str, pd.Series]
    metrics_summary: List[BacktestSummaryMetrics]
    yearly_returns_df: pd.DataFrame
    asset_performance_df: pd.DataFrame
    trade_logs: Dict[str, List[Dict[str, Any]]]
    ltv_series: pd.Series


class BacktestEngine:
    def __init__(self, data_cache_path: str = 'data_cache/all_market_data_10y.parquet') -> None:
        if not os.path.exists(data_cache_path):
            data_cache_path = 'data_cache/market_data_10y.parquet'
        self.data_cache_path = data_cache_path
        self._load_and_align_data()

    def _load_and_align_data(self) -> None:
        if not os.path.exists(self.data_cache_path):
            raise FileNotFoundError(f"Arquivo de dados {self.data_cache_path} não encontrado.")
        
        df = pd.read_parquet(self.data_cache_path)
        closes = df['Close'].copy() if 'Close' in df else df.copy()
        
        # Merge Bitfinex early ETH data (2016-2017) if needed
        try:
            eth_bf = pd.read_csv('https://www.cryptodatadownload.com/cdd/Bitfinex_ETHUSD_d.csv', skiprows=1)
            eth_bf['date'] = pd.to_datetime(eth_bf['date'])
            eth_bf.set_index('date', inplace=True)
            eth_bf.sort_index(inplace=True)
            if 'ETH-USD' in closes.columns:
                closes['ETH-USD'] = closes['ETH-USD'].combine_first(eth_bf['close'])
        except Exception:
            pass
            
        self.daily_px = closes.ffill().dropna(subset=['SPY', 'BTC-USD'])
        
        # Load Fed Funds rate
        try:
            fed_df = pd.read_csv('https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS&cosd=2014-01-01', index_col=0, parse_dates=True)
            self.fed_rate = fed_df['FEDFUNDS'].resample('D').ffill().reindex(self.daily_px.index).ffill().fillna(1.5) / 100.0
        except Exception:
            self.fed_rate = pd.Series(0.02, index=self.daily_px.index)

    def run_backtest_10y(
        self,
        initial_capital: float = 100_000.0,
        monthly_contribution: float = 5_000.0,
        basket_mode: str = 'portfolio_19'
    ) -> BacktestFullResults:
        start_date = pd.Timestamp('2016-11-05', tz='UTC') if self.daily_px.index.tz else pd.Timestamp('2016-11-05')
        end_date = self.daily_px.index[-1]
        px = self.daily_px.loc[start_date:end_date]
        dates = px.index
        
        # Determine active weights and ticker groups
        if basket_mode == 'screener_elite':
            active_weights = SCREENER_WEIGHTS_10
            crypto_keys = ['MKR-USD', 'LINK-USD', 'UNI7083-USD', 'PENDLE-USD']
            stock_keys = ['ASML', 'TSM', 'MELI', 'NU', 'AVGO', 'MA']
        else:
            active_weights = TARGET_WEIGHTS_19
            crypto_keys = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'AAVE-USD']
            stock_keys = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'V', 'JPM', 'WMT', 'DBSDY']

        # Precompute BTC technicals & on-chain proxies
        btc = self.daily_px['BTC-USD']
        btc_111 = btc.rolling(111).mean()
        btc_350_x2 = btc.rolling(350).mean() * 2
        btc_200w = btc.rolling(1400).mean()
        btc_realized = btc.rolling(730).mean()
        btc_nupl = (btc - btc_realized) / btc
        btc_mvrv_z = (btc / btc_realized - 1.0) * 1.5

        # SPY indicators for macro stress
        spy = self.daily_px['SPY']
        spy_peak = spy.cummax()
        spy_dd = (spy - spy_peak) / spy_peak

        # Identify first trading day of each month for contributions
        month_first_days = set()
        cur_m = None
        for d in dates:
            if d.month != cur_m:
                month_first_days.add(d)
                cur_m = d.month
        total_months = len(month_first_days)
        total_invested = initial_capital + total_months * monthly_contribution

        # Trailing peaks for cryptos
        cr_peaks = {c: self.daily_px[c].rolling(60, min_periods=1).max() for c in crypto_keys if c in self.daily_px}
        # 52w rolling high/low for stocks
        st_52w_h = {s: self.daily_px[s].rolling(252, min_periods=30).max() for s in stock_keys if s in self.daily_px}
        st_52w_l = {s: self.daily_px[s].rolling(252, min_periods=30).min() for s in stock_keys if s in self.daily_px}

        # 1. SPY DCA
        spy_u = initial_capital / px['SPY'].iloc[0]
        spy_eq = []
        for d in dates:
            if d in month_first_days:
                spy_u += monthly_contribution / px['SPY'].loc[d]
            spy_eq.append(spy_u * px['SPY'].loc[d])
        series_spy = pd.Series(spy_eq, index=dates)

        # 2. QQQ DCA
        qqq_u = initial_capital / px['QQQ'].iloc[0]
        qqq_eq = []
        for d in dates:
            if d in month_first_days:
                qqq_u += monthly_contribution / px['QQQ'].loc[d]
            qqq_eq.append(qqq_u * px['QQQ'].loc[d])
        series_qqq = pd.Series(qqq_eq, index=dates)

        # 3 & 4. Static Portfolio (0% LTV vs. Convex LTV)
        def simulate_static(use_leverage: bool):
            units = {}
            debt = 0.0
            eq_curve = []
            
            init_a = initial_capital
            if use_leverage:
                debt = initial_capital * (0.20 / 0.80)
                init_a += debt
                
            for a, w in active_weights.items():
                if a in px and pd.notnull(px[a].iloc[0]) and px[a].iloc[0] > 0:
                    units[a] = (init_a * w) / px[a].iloc[0]
                else:
                    units[a] = 0.0
                    anc = 'BTC-USD' if '-USD' in a else 'SPY'
                    units[anc] = units.get(anc, 0.0) + (init_a * w) / px[anc].iloc[0]

            for i, d in enumerate(dates):
                if d in month_first_days:
                    inflow = monthly_contribution
                    if use_leverage:
                        inflow_b = inflow * (0.20 / 0.80)
                        debt += inflow_b
                        inflow += inflow_b
                    tradable = {a: w for a, w in active_weights.items() if a in px and pd.notnull(px[a].loc[d]) and px[a].loc[d] > 0}
                    s_t = sum(tradable.values())
                    for a, w in tradable.items():
                        units[a] = units.get(a, 0.0) + (inflow * (w / s_t)) / px[a].loc[d]
                        
                gross_a = 0.0
                for a, u in units.items():
                    if a in px and pd.notnull(px[a].loc[d]):
                        gross_a += u * px[a].loc[d]
                if debt > 0:
                    debt += debt * ((self.fed_rate.loc[d] + 0.0035) / 365.0)
                    
                equity = gross_a - debt
                c_ltv = debt / gross_a if gross_a > 0 else 0.0
                
                if c_ltv > 0.50:
                    payd = debt - gross_a * 0.40
                    debt -= payd
                    r_red = 1.0 - (payd / gross_a)
                    for a in units.keys():
                        units[a] *= r_red
                    gross_a -= payd
                    equity = gross_a - debt
                    c_ltv = debt / gross_a
                    
                eq_curve.append(equity)
                
                if use_leverage:
                    mvrv = btc_mvrv_z.loc[d]
                    nupl = btc_nupl.loc[d]
                    s_d = spy_dd.loc[d]
                    is_pan = (mvrv < 0.5 or nupl < 0.0 or s_d < -0.20)
                    fed_f = self.fed_rate.loc[d]
                    is_dst = (fed_f > 0.045 and s_d > -0.05)
                    t_ltv = 0.30 if is_pan else (0.10 if is_dst else 0.20)
                    
                    des_d = gross_a * t_ltv
                    delta_d = des_d - debt
                    if delta_d > gross_a * 0.03:
                        debt += delta_d
                        tradable = {a: w for a, w in active_weights.items() if a in px and pd.notnull(px[a].loc[d]) and px[a].loc[d] > 0}
                        s_t = sum(tradable.values())
                        for a, w in tradable.items():
                            units[a] = units.get(a, 0.0) + (delta_d * (w / s_t)) / px[a].loc[d]
                    elif delta_d < -gross_a * 0.05 and debt > 0:
                        payd = min(debt, abs(delta_d))
                        debt -= payd
                        ratio = 1.0 - (payd / gross_a)
                        for a in units.keys():
                            units[a] *= ratio
                            
                # Quarterly Rebalance (90 days)
                if i > 0 and i % 90 == 0:
                    tot_v = 0.0
                    for a, u in units.items():
                        if a in px and pd.notnull(px[a].loc[d]):
                            tot_v += u * px[a].loc[d]
                    tradable = {a: w for a, w in active_weights.items() if a in px and pd.notnull(px[a].loc[d]) and px[a].loc[d] > 0}
                    s_t = sum(tradable.values())
                    for a in active_weights.keys():
                        if a in tradable:
                            units[a] = (tot_v * (tradable[a] / s_t)) / px[a].loc[d]
                        else:
                            units[a] = 0.0
                    for anc in ['BTC-USD', 'SPY']:
                        if anc not in active_weights:
                            units[anc] = 0.0
                            
            return pd.Series(eq_curve, index=dates)

        series_static_unlev = simulate_static(use_leverage=False)
        series_static_conv = simulate_static(use_leverage=True)

        # 5 & 6. True Valuation Framework Strategies (Unleveraged vs. Convex LTV)
        def simulate_framework(use_leverage: bool):
            units = {}
            debt = 0.0
            cash = 0.0
            trade_log = []
            eq_curve = []
            ltv_curve = []
            total_tax_paid = 0.0
            
            btc_pruned = False
            cr_exited = {c: False for c in crypto_keys}
            st_pruned = {s: False for s in stock_keys}
            cost_basis = {}
            
            init_a = initial_capital
            if use_leverage:
                debt = initial_capital * (0.20 / 0.80)
                init_a += debt
                
            for a, w in active_weights.items():
                if a in px and pd.notnull(px[a].iloc[0]) and px[a].iloc[0] > 0:
                    units[a] = (init_a * w) / px[a].iloc[0]
                    cost_basis[a] = px[a].iloc[0]
                else:
                    units[a] = 0.0
                    cost_basis[a] = 0.0
                    anc = 'BTC-USD' if '-USD' in a else 'SPY'
                    units[anc] = units.get(anc, 0.0) + (init_a * w) / px[anc].iloc[0]
                    cost_basis[anc] = px[anc].iloc[0]

            for i, d in enumerate(dates):
                gross_a = cash
                asset_vals = {}
                for a, u in units.items():
                    if a in px and pd.notnull(px[a].loc[d]):
                        v = u * px[a].loc[d]
                        asset_vals[a] = v
                        gross_a += v
                    else:
                        asset_vals[a] = 0.0
                        
                if debt > 0:
                    debt += debt * ((self.fed_rate.loc[d] + 0.0035) / 365.0)
                    
                equity = gross_a - debt
                c_ltv = debt / gross_a if gross_a > 0 else 0.0
                
                # Monthly Shannon Inflow
                if d in month_first_days:
                    inflow_m = monthly_contribution
                    if use_leverage:
                        inflow_b = inflow_m * (0.20 / 0.80)
                        debt += inflow_b
                        inflow_m += inflow_b
                        
                    tradable = [a for a in active_weights.keys() if a in px and pd.notnull(px[a].loc[d]) and px[a].loc[d] > 0]
                    nupl = btc_nupl.loc[d]
                    buy_candidates = []
                    for a in tradable:
                        cur_v = asset_vals.get(a, 0.0)
                        tgt_v = (equity + debt) * active_weights[a]
                        drift = tgt_v - cur_v
                        if a in crypto_keys:
                            el = (nupl < 0.45 and not cr_exited.get(a, False))
                        else:
                            hi = st_52w_h[a].loc[d] if a in st_52w_h else None
                            el = (pd.notnull(hi) and px[a].loc[d] <= hi * 0.95) if hi is not None else True
                        if el and drift > 0:
                            buy_candidates.append((a, drift))
                            
                    if buy_candidates:
                        buy_candidates.sort(key=lambda x: x[1], reverse=True)
                        top_a = buy_candidates[0][0]
                        units[top_a] = units.get(top_a, 0.0) + inflow_m / px[top_a].loc[d]
                    else:
                        defasados = sorted(tradable, key=lambda a: (equity + debt)*active_weights[a] - asset_vals.get(a, 0.0), reverse=True)
                        top_a = defasados[0]
                        units[top_a] = units.get(top_a, 0.0) + inflow_m / px[top_a].loc[d]

                # Tactical Signals
                nupl = btc_nupl.loc[d]
                mvrv = btc_mvrv_z.loc[d]
                
                # BTC Timing (portfolio_19)
                if 'BTC-USD' in active_weights and 'BTC-USD' in units and units['BTC-USD'] > 0:
                    p_btc = px['BTC-USD'].loc[d]
                    s111 = btc_111.loc[d]
                    s350x2 = btc_350_x2.loc[d]
                    s200w = btc_200w.loc[d]
                    pi_top = (s111 >= s350x2) if (pd.notnull(s111) and pd.notnull(s350x2)) else False
                    if not btc_pruned and (pi_top or (nupl > 0.60 and units['BTC-USD'] * p_btc > equity * 0.45)):
                        sell_u = units['BTC-USD'] * 0.50
                        sell_p = sell_u * p_btc
                        units['BTC-USD'] -= sell_u
                        btc_pruned = True
                        gain = max(0.0, sell_p - sell_u * cost_basis.get('BTC-USD', p_btc))
                        tax = gain * 0.15
                        total_tax_paid += tax
                        net_p = sell_p - tax
                        cands = [s for s in stock_keys if s in px and pd.notnull(px[s].loc[d])]
                        for s in cands:
                            units[s] = units.get(s, 0.0) + (net_p / len(cands)) / px[s].loc[d]
                        trade_log.append({
                            'date': d.strftime('%Y-%m-%d'),
                            'asset': 'BTC-USD',
                            'action': 'PODA 50%',
                            'price': p_btc,
                            'proceeds': sell_p,
                            'reason': 'Pi Cycle Top / Euforia Macro'
                        })
                    if btc_pruned and ((pd.notnull(s200w) and p_btc <= 1.05 * s200w) or nupl < 0.0 or mvrv <= 0.5):
                        btc_pruned = False
                        trade_log.append({
                            'date': d.strftime('%Y-%m-%d'),
                            'asset': 'BTC-USD',
                            'action': 'RE-ACUMULAÇÃO',
                            'price': p_btc,
                            'proceeds': 0.0,
                            'reason': 'Piso Histórico 200W SMA / Capitulação'
                        })

                # Altcoins 100% Exit
                macro_alt_warn = (nupl > 0.60 or mvrv > 2.5)
                for c in crypto_keys:
                    if c == 'BTC-USD':
                        continue
                    if c in px and pd.notnull(px[c].loc[d]) and px[c].loc[d] > 0 and units.get(c, 0.0) > 0 and not cr_exited[c]:
                        p_c = px[c].loc[d]
                        pk = cr_peaks[c].loc[d] if c in cr_peaks else p_c
                        dd = (p_c - pk) / pk if pk > 0 else 0.0
                        if macro_alt_warn and dd <= -0.20:
                            sell_u = units[c]
                            sell_p = sell_u * p_c
                            units[c] = 0.0
                            cr_exited[c] = True
                            gain = max(0.0, sell_p - sell_u * cost_basis.get(c, p_c))
                            tax = gain * 0.15
                            total_tax_paid += tax
                            net_p = sell_p - tax
                            cands = [s for s in stock_keys if s in px and pd.notnull(px[s].loc[d])]
                            for s in cands:
                                units[s] = units.get(s, 0.0) + (net_p / len(cands)) / px[s].loc[d]
                            trade_log.append({
                                'date': d.strftime('%Y-%m-%d'),
                                'asset': c,
                                'action': 'SAÍDA TOTAL 100%',
                                'price': p_c,
                                'proceeds': sell_p,
                                'reason': 'Alerta Macro Euforia + 20% Trailing Drawdown'
                            })
                    if cr_exited.get(c, False) and nupl < 0.30 and c in px and pd.notnull(px[c].loc[d]) and px[c].loc[d] > 0:
                        cr_exited[c] = False
                        t_val = (equity + debt) * active_weights[c]
                        units[c] = t_val / px[c].loc[d]
                        cost_basis[c] = px[c].loc[d]
                        trade_log.append({
                            'date': d.strftime('%Y-%m-%d'),
                            'asset': c,
                            'action': 'RE-ENTRADA',
                            'price': px[c].loc[d],
                            'proceeds': 0.0,
                            'reason': 'Fundo Macro Cripto (NUPL < 0.30)'
                        })

                # Stocks PEGY 50% Pruning
                for s in stock_keys:
                    if s in px and pd.notnull(px[s].loc[d]) and units.get(s, 0.0) > 0:
                        p_s = px[s].loc[d]
                        hi = st_52w_h[s].loc[d] if s in st_52w_h else p_s
                        lo = st_52w_l[s].loc[d] if s in st_52w_l else p_s
                        if not st_pruned[s] and p_s >= hi * 0.98 and (hi / max(1.0, lo)) > 1.80 and asset_vals.get(s, 0) > (equity + debt) * (active_weights[s] * 1.5):
                            sell_u = units[s] * 0.50
                            proc = sell_u * p_s
                            units[s] -= sell_u
                            st_pruned[s] = True
                            gain = max(0.0, proc - sell_u * cost_basis.get(s, p_s))
                            tax = gain * 0.15
                            total_tax_paid += tax
                            net_p = proc - tax
                            cheapest_s = min(stock_keys, key=lambda stk: px[stk].loc[d] / max(1.0, st_52w_h[stk].loc[d]) if stk in px and pd.notnull(px[stk].loc[d]) else 999)
                            units[cheapest_s] = units.get(cheapest_s, 0.0) + net_p / px[cheapest_s].loc[d]
                            trade_log.append({
                                'date': d.strftime('%Y-%m-%d'),
                                'asset': s,
                                'action': 'PODA PEGY 50%',
                                'price': p_s,
                                'proceeds': proc,
                                'reason': 'Enterprise PEGY > 1.60x Sobreavaliação'
                            })
                        elif st_pruned[s] and p_s < hi * 0.80:
                            st_pruned[s] = False

                # Convex Leverage Adjustments
                if use_leverage:
                    s_dd = spy_dd.loc[d]
                    is_pan = (mvrv < 0.5 or nupl < 0.0 or s_dd < -0.20)
                    fed_f = self.fed_rate.loc[d]
                    is_dst = (fed_f > 0.045 and s_dd > -0.05)
                    t_ltv = 0.30 if is_pan else (0.10 if is_dst else 0.20)
                    des_d = gross_a * t_ltv
                    delta_d = des_d - debt
                    if delta_d > gross_a * 0.03:
                        debt += delta_d
                        tradable_stocks = [s for s in stock_keys if s in px and pd.notnull(px[s].loc[d])]
                        for s in tradable_stocks:
                            units[s] = units.get(s, 0.0) + (delta_d / len(tradable_stocks)) / px[s].loc[d]
                    elif delta_d < -gross_a * 0.05 and debt > 0:
                        payd = min(debt, abs(delta_d))
                        debt -= payd
                        ratio = 1.0 - (payd / gross_a)
                        for a in units.keys():
                            units[a] *= ratio

                eq_curve.append(equity)
                ltv_curve.append(c_ltv)

            return pd.Series(eq_curve, index=dates), trade_log, total_tax_paid, pd.Series(ltv_curve, index=dates)

        series_tv_unlev, trades_unlev, taxes_unlev, _ = simulate_framework(use_leverage=False)
        series_tv_conv, trades_conv, taxes_conv, ltv_conv = simulate_framework(use_leverage=True)

        prefix = "Screener Elite" if basket_mode == 'screener_elite' else "Carteira 19"
        equity_dict = {
            f'{prefix} (True Valuation + Convex LTV)': series_tv_conv,
            f'{prefix} (True Valuation 0% LTV)': series_tv_unlev,
            f'{prefix} (Estática + Convex LTV)': series_static_conv,
            f'{prefix} (Estática 0% LTV)': series_static_unlev,
            'Nasdaq-100 (QQQ DCA)': series_qqq,
            'S&P 500 (SPY DCA)': series_spy,
        }

        def get_summary(s: pd.Series, name: str, trades: int = 0, taxes: float = 0.0) -> BacktestSummaryMetrics:
            ret = (s.iloc[-1] / total_invested) - 1.0
            years = (s.index[-1] - s.index[0]).days / 365.25
            cagr = (s.iloc[-1] / total_invested) ** (1.0 / years) - 1.0 if years > 0 else 0
            daily_r = s.pct_change().dropna()
            vol = daily_r.std() * math.sqrt(252)
            rf = 0.02
            sharpe = (cagr - rf) / vol if vol > 0 else 0
            downside = daily_r[daily_r < 0]
            d_vol = downside.std() * math.sqrt(252)
            sortino = (cagr - rf) / d_vol if d_vol > 0 else 0
            peak = s.cummax()
            mdd = ((s - peak) / peak).min()
            calmar = abs(cagr / mdd) if mdd != 0 else 0
            mult = s.iloc[-1] / total_invested
            profit = s.iloc[-1] - total_invested
            
            return BacktestSummaryMetrics(
                strategy_name=name,
                initial_capital=initial_capital,
                total_invested=total_invested,
                final_capital=s.iloc[-1],
                net_profit=profit,
                multiple_on_invested=round(mult, 2),
                total_return_pct=ret * 100,
                cagr_pct=cagr * 100,
                annual_volatility_pct=vol * 100,
                sharpe_ratio=round(sharpe, 2),
                sortino_ratio=round(sortino, 2),
                max_drawdown_pct=mdd * 100,
                calmar_ratio=round(calmar, 2),
                total_trades=trades,
                total_taxes_paid=taxes
            )

        metrics_list = [
            get_summary(series_tv_conv, f'{prefix} (True Valuation + Convex LTV)', len(trades_conv), taxes_conv),
            get_summary(series_tv_unlev, f'{prefix} (True Valuation 0% LTV)', len(trades_unlev), taxes_unlev),
            get_summary(series_static_conv, f'{prefix} (Estática + Convex LTV)'),
            get_summary(series_static_unlev, f'{prefix} (Estática 0% LTV)'),
            get_summary(series_qqq, 'Nasdaq-100 (QQQ DCA)'),
            get_summary(series_spy, 'S&P 500 (SPY DCA)'),
        ]

        # Yearly returns dataframe
        yearly_records = []
        for yr in sorted(list(set(dates.year))):
            sub_d = dates[dates.year == yr]
            if len(sub_d) < 2:
                continue
            d0, d1 = sub_d[0], sub_d[-1]
            yearly_records.append({
                'Ano': yr,
                'SPY DCA': (series_spy.loc[d1] / series_spy.loc[d0] - 1.0) * 100,
                'QQQ DCA': (series_qqq.loc[d1] / series_qqq.loc[d0] - 1.0) * 100,
                f'{prefix} Estática': (series_static_unlev.loc[d1] / series_static_unlev.loc[d0] - 1.0) * 100,
                f'{prefix} Est. LTV': (series_static_conv.loc[d1] / series_static_conv.loc[d0] - 1.0) * 100,
                f'{prefix} TV (0% LTV)': (series_tv_unlev.loc[d1] / series_tv_unlev.loc[d0] - 1.0) * 100,
                f'{prefix} TV (Convex LTV)': (series_tv_conv.loc[d1] / series_tv_conv.loc[d0] - 1.0) * 100,
            })
        yearly_df = pd.DataFrame(yearly_records)

        # Asset performance breakdown
        asset_records = []
        for a, w in active_weights.items():
            if a in self.daily_px:
                s_10y = self.daily_px[a].loc[start_date:end_date].dropna()
                if not s_10y.empty:
                    p0 = s_10y.iloc[0]
                    p1 = s_10y.iloc[-1]
                    ret_a = (p1 / p0) - 1.0
                    y_a = (s_10y.index[-1] - s_10y.index[0]).days / 365.25
                    cagr_a = (p1 / p0) ** (1.0 / y_a) - 1.0 if y_a > 0 else 0
                    first_date_str = s_10y.index[0].strftime('%Y-%m')
                else:
                    p0, p1, ret_a, cagr_a, first_date_str = 0, 0, 0, 0, "N/A"
            else:
                p0, p1, ret_a, cagr_a, first_date_str = 0, 0, 0, 0, "N/A"
            asset_records.append({
                'Ticker': a,
                'Tipo': 'Crypto' if '-USD' in a else 'Stock/ETF',
                'Peso Alvo (%)': w * 100,
                'Preço Inicial (USD)': p0,
                'Preço Final (USD)': p1,
                'Início Dados': first_date_str,
                'Retorno Período (%)': ret_a * 100,
                'CAGR (%)': cagr_a * 100
            })
        asset_df = pd.DataFrame(asset_records)

        return BacktestFullResults(
            basket_mode=basket_mode,
            dates=dates,
            total_invested=total_invested,
            equity_series=equity_dict,
            metrics_summary=metrics_list,
            yearly_returns_df=yearly_df,
            asset_performance_df=asset_df,
            trade_logs={'unleveraged': trades_unlev, 'convex_ltv': trades_conv},
            ltv_series=ltv_conv
        )


# ==============================================================================
# CONSTRUTORES DE GRÁFICOS DO BACKTEST
# ==============================================================================

def build_backtest_equity_chart(results: BacktestFullResults, log_scale: bool = True) -> go.Figure:
    fig = go.Figure()
    
    colors = {
        'True Valuation + Convex LTV': '#10B981',
        'True Valuation 0% LTV': '#06B6D4',
        'Estática + Convex LTV': '#EAB308',
        'Estática 0% LTV': '#F59E0B',
        'Nasdaq-100 (QQQ DCA)': '#8B5CF6',
        'S&P 500 (SPY DCA)': '#3B82F6',
    }
    
    for name, s in results.equity_series.items():
        matched_color = '#CBD5E1'
        for k, c in colors.items():
            if k in name:
                matched_color = c
                break
        width = 3 if 'True Valuation + Convex' in name else (2.5 if 'Estática + Convex' in name else 1.8)
        dash = 'solid' if 'True Valuation + Convex' in name else ('dash' if 'Estática + Convex' in name else ('dot' if 'DCA' in name else 'solid'))
        fig.add_trace(go.Scatter(
            x=s.index,
            y=s,
            name=name,
            line=dict(color=matched_color, width=width, dash=dash),
            hovertemplate="<b>%{x|%d/%m/%Y}</b><br>" + name + ": $%{y:,.0f}<extra></extra>"
        ))
        
    fig.update_layout(
        title=dict(text=f"<b>Evolução Patrimonial ({results.basket_mode.upper()} • $100k Inicial + $5k/mês DCA)</b>", font=dict(size=14, color="#F8FAFC")),
        height=520,
        paper_bgcolor=CARD_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=11),
        margin=dict(l=50, r=50, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, bgcolor="rgba(17,24,39,0.7)"),
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            type="log" if log_scale else "linear",
            tickprefix="$",
            title="Patrimônio Líquido (USD)" + (" [Escala Log]" if log_scale else "")
        )
    )
    return fig


def build_backtest_drawdown_chart(results: BacktestFullResults) -> go.Figure:
    fig = go.Figure()
    
    for name, s in results.equity_series.items():
        if any(w in name for w in ['True Valuation + Convex', 'Estática + Convex', 'QQQ DCA', 'SPY DCA']):
            peak = s.cummax()
            dd = (s - peak) / peak * 100.0
            color = '#10B981' if 'True Valuation' in name else ('#EAB308' if 'Estática' in name else ('#8B5CF6' if 'QQQ' in name else '#3B82F6'))
            fig.add_trace(go.Scatter(
                x=dd.index,
                y=dd,
                name=name,
                line=dict(color=color, width=1.5),
                hovertemplate="<b>%{x|%d/%m/%Y}</b><br>" + name + " Drawdown: %{y:.1f}%<extra></extra>"
            ))
        
    fig.update_layout(
        title=dict(text="<b>Curva de Drawdown Histórico Submerso (% do Topo)</b>", font=dict(size=14, color="#F8FAFC")),
        height=380,
        paper_bgcolor=CARD_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=11),
        margin=dict(l=50, r=50, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, bgcolor="rgba(17,24,39,0.7)"),
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, ticksuffix="%", title="Drawdown (%)", range=[-85, 5])
    )
    return fig


def build_backtest_yearly_bars(results: BacktestFullResults) -> go.Figure:
    df = results.yearly_returns_df
    fig = go.Figure()
    
    col_tv = [c for c in df.columns if 'TV (Convex' in c][0]
    col_st = [c for c in df.columns if 'Est. LTV' in c][0]
    
    fig.add_trace(go.Bar(
        x=df['Ano'],
        y=df[col_tv],
        name=col_tv,
        marker_color='#10B981'
    ))
    fig.add_trace(go.Bar(
        x=df['Ano'],
        y=df[col_st],
        name=col_st,
        marker_color='#EAB308'
    ))
    fig.add_trace(go.Bar(
        x=df['Ano'],
        y=df['QQQ DCA'],
        name='Nasdaq-100 (QQQ DCA)',
        marker_color='#8B5CF6'
    ))
    fig.add_trace(go.Bar(
        x=df['Ano'],
        y=df['SPY DCA'],
        name='S&P 500 (SPY DCA)',
        marker_color='#3B82F6'
    ))
    
    fig.update_layout(
        title=dict(text="<b>Retornos Calendário Ano a Ano (% YoY com Aportes)</b>", font=dict(size=14, color="#F8FAFC")),
        height=400,
        barmode='group',
        paper_bgcolor=CARD_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=11),
        margin=dict(l=50, r=50, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, bgcolor="rgba(17,24,39,0.7)"),
        hovermode="x unified",
        xaxis=dict(showgrid=False, tickmode='linear'),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, ticksuffix="%", title="Retorno Anual (%)")
    )
    return fig

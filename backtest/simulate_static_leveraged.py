import sys
import os
import math
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"c:\Users\ladou\Desktop\Agente de Investimentos"
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.backtest_engine import BacktestEngine, TARGET_WEIGHTS_19

engine = BacktestEngine()
daily_px = engine.daily_px
fed_rate = engine.fed_rate

start_date = pd.Timestamp('2016-11-05', tz='UTC') if daily_px.index.tz else pd.Timestamp('2016-11-05')
end_date = daily_px.index[-1]
px = daily_px.loc[start_date:end_date]
dates = px.index

# Indicators for leverage triggers
btc = daily_px['BTC-USD']
btc_realized = btc.rolling(730).mean()
btc_nupl = (btc - btc_realized) / btc
btc_mvrv_z = (btc / btc_realized - 1.0) * 1.5
spy = daily_px['SPY']
spy_peak = spy.cummax()
spy_dd = (spy - spy_peak) / spy_peak

INITIAL_CAPITAL = 10_000_000.0

# -------------------------------------------------------------
# STRATEGY: Static 19-Asset Portfolio WITH Convex LTV (20-30%)
# - Same 19 assets
# - Rebalanced Quarterly (every 90 days)
# - Leveraged with Base LTV 20%, Turbo LTV 30% in panics, Defensive LTV 10% in dual stress
# - NO Pi Cycle Top prune on BTC
# - NO 100% exit on Altcoins
# - NO PEGY prune on individual stocks
# -------------------------------------------------------------

def run_static_convex_ltv():
    units = {}
    debt = 0.0
    cash = 0.0
    equity_curve = []
    ltv_curve = []
    margin_call_events = []
    
    # Initial setup with Base LTV 20%
    base_ltv = 0.20
    debt = INITIAL_CAPITAL * (base_ltv / (1.0 - base_ltv))
    total_assets = INITIAL_CAPITAL + debt
    
    for a, w in TARGET_WEIGHTS_19.items():
        p = px[a].iloc[0]
        if pd.notnull(p) and p > 0:
            units[a] = (total_assets * w) / p
        else:
            units[a] = 0.0
            units['BTC-USD'] = units.get('BTC-USD', 0.0) + (total_assets * w) / px['BTC-USD'].iloc[0]
            
    for i, d in enumerate(dates):
        # Calculate asset values
        gross_assets = cash
        for a, u in units.items():
            p = px[a].loc[d]
            if pd.notnull(p):
                gross_assets += u * p
                
        # Daily interest accrual on debt (Fed Funds + 0.35%)
        if debt > 0:
            rate = fed_rate.loc[d] + 0.0035
            debt += debt * (rate / 365.0)
            
        equity = gross_assets - debt
        cur_ltv = debt / gross_assets if gross_assets > 0 else 0.0
        
        # Check margin stress (> 45% LTV)
        if cur_ltv >= 0.45:
            margin_call_events.append({
                'date': d.strftime('%Y-%m-%d'),
                'ltv': cur_ltv,
                'equity': equity,
                'assets': gross_assets,
                'debt': debt
            })
            # Emergency deleveraging if above 50% to prevent liquidation
            if cur_ltv > 0.50:
                needed_paydown = debt - gross_assets * 0.40
                debt -= needed_paydown
                # Sell pro-rata
                reduction_ratio = 1.0 - (needed_paydown / gross_assets)
                for a in units.keys():
                    units[a] *= reduction_ratio
                gross_assets -= needed_paydown
                equity = gross_assets - debt
                cur_ltv = debt / gross_assets
                
        equity_curve.append(equity)
        ltv_curve.append(cur_ltv)
        
        # Convex LTV Target adjustments (same macro triggers)
        mvrv = btc_mvrv_z.loc[d]
        nupl = btc_nupl.loc[d]
        s_dd = spy_dd.loc[d]
        is_panic = (mvrv < 0.5 or nupl < 0.0 or s_dd < -0.20)
        fed_f = fed_rate.loc[d]
        is_dual_stress = (fed_f > 0.045 and s_dd > -0.05)
        
        target_ltv = 0.20
        if is_panic:
            target_ltv = 0.30
        elif is_dual_stress:
            target_ltv = 0.10
            
        desired_debt = gross_assets * target_ltv
        delta_debt = desired_debt - debt
        
        if delta_debt > gross_assets * 0.03: # Expand leverage
            borrow_add = delta_debt
            debt += borrow_add
            # Buy according to target weights (static allocation)
            tradable = {a: w for a, w in TARGET_WEIGHTS_19.items() if pd.notnull(px[a].loc[d]) and px[a].loc[d] > 0}
            sum_t = sum(tradable.values())
            for a, w in tradable.items():
                units[a] += (borrow_add * (w / sum_t)) / px[a].loc[d]
        elif delta_debt < -gross_assets * 0.05 and debt > 0: # Deleveraging
            paydown = min(debt, abs(delta_debt))
            debt -= paydown
            # Sell pro-rata to pay down debt
            ratio = 1.0 - (paydown / gross_assets)
            for a in units.keys():
                units[a] *= ratio
                
        # Quarterly Rebalancing (every 90 days) back to target weights
        if i > 0 and i % 90 == 0:
            tot_val = 0.0
            for a, u in units.items():
                p = px[a].loc[d]
                if pd.notnull(p):
                    tot_val += u * p
            tradable = {a: w for a, w in TARGET_WEIGHTS_19.items() if pd.notnull(px[a].loc[d]) and px[a].loc[d] > 0}
            sum_t = sum(tradable.values())
            for a in TARGET_WEIGHTS_19.keys():
                if a in tradable:
                    units[a] = (tot_val * (tradable[a] / sum_t)) / px[a].loc[d]
                else:
                    units[a] = 0.0
                    
    return pd.Series(equity_curve, index=dates), pd.Series(ltv_curve, index=dates), margin_call_events

series_static_conv, ltv_static_conv, margin_events = run_static_convex_ltv()

# Run standard backtest to compare
results_std = engine.run_backtest_10y(initial_capital=INITIAL_CAPITAL)

def calc_m(s, name):
    ret = (s.iloc[-1] / s.iloc[0]) - 1.0
    y = (s.index[-1] - s.index[0]).days / 365.25
    cagr = (s.iloc[-1] / s.iloc[0]) ** (1.0 / y) - 1.0 if y > 0 else 0
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
    return {
        'Estratégia': name,
        'Capital Inicial': f"${s.iloc[0]:,.0f}",
        'Capital Final': f"${s.iloc[-1]:,.0f}",
        'Retorno Total (%)': f"{ret * 100:,.1f}%",
        'CAGR (%)': f"{cagr * 100:.2f}%",
        'Volatilidade (%)': f"{vol * 100:.2f}%",
        'Sharpe': f"{sharpe:.2f}",
        'Sortino': f"{sortino:.2f}",
        'Max Drawdown (%)': f"{mdd * 100:.2f}%",
        'Calmar': f"{calmar:.2f}"
    }

comp_list = []
# 1. Static Unleveraged
s_unlev = results_std.equity_series['Carteira Estática 19 Ativos']
comp_list.append(calc_m(s_unlev, '1. Carteira Estática (Rebal. Trimestral) [0% LTV / Sem Alavancagem]'))
# 2. Static Convex LTV
comp_list.append(calc_m(series_static_conv, '2. Carteira Estática (Rebal. Trimestral) + ALAVANCAGEM CONVEXA (LTV 20-30%)'))
# 3. True Valuation Framework (Unleveraged)
s_tv_unlev = results_std.equity_series['True Valuation (0% LTV)']
comp_list.append(calc_m(s_tv_unlev, '3. True Valuation Framework (Timing & Podas) [0% LTV / Sem Alavancagem]'))
# 4. True Valuation Framework (Convex LTV)
s_tv_conv = results_std.equity_series['True Valuation (Convex LTV 20-30%)']
comp_list.append(calc_m(s_tv_conv, '4. True Valuation Framework (Timing & Podas) + ALAVANCAGEM CONVEXA (LTV 20-30%)'))
# 5. Benchmarks
comp_list.append(calc_m(results_std.equity_series['QQQ (Nasdaq 100)'], '5. Nasdaq-100 (QQQ) Buy & Hold'))
comp_list.append(calc_m(results_std.equity_series['SPY (S&P 500)'], '6. S&P 500 (SPY) Buy & Hold'))

comp_df = pd.DataFrame(comp_list)
print("\n" + "="*95)
print("       COMPARATIVO DIRETO: CARTEIRA ESTÁTICA COM vs. SEM ALAVANCAGEM CONVEXA LTV")
print("="*95)
print(comp_df.to_string(index=False))
print("="*95)

# Year by Year Comparison for these key 4 portfolio variants
yr_records = []
for yr in sorted(list(set(dates.year))):
    mask = (dates.year == yr)
    sub_d = dates[mask]
    if len(sub_d) < 2:
        continue
    d0, d1 = sub_d[0], sub_d[-1]
    yr_records.append({
        'Ano': yr,
        'Estática (0% LTV)': f"{(s_unlev.loc[d1]/s_unlev.loc[d0]-1)*100:+.1f}%",
        'Estática (Convex LTV)': f"{(series_static_conv.loc[d1]/series_static_conv.loc[d0]-1)*100:+.1f}%",
        'True Valuation (0% LTV)': f"{(s_tv_unlev.loc[d1]/s_tv_unlev.loc[d0]-1)*100:+.1f}%",
        'True Valuation (Convex LTV)': f"{(s_tv_conv.loc[d1]/s_tv_conv.loc[d0]-1)*100:+.1f}%",
    })

print("\n=== RETORNOS ANO A ANO (ISOLANDO O EFEITO DA ALAVANCAGEM VS. TIMING) ===")
print(pd.DataFrame(yr_records).to_string(index=False))

print(f"\nAlertas de Estresse de Alavancagem na Carteira Estática (LTV >= 45%): {len(margin_events)} dias")
if margin_events:
    sample = margin_events[:3] + margin_events[-3:]
    for ev in sample:
        print(f"  Data: {ev['date']} | LTV atingido: {ev['ltv']*100:.1f}% | Patrimônio Líquido: ${ev['equity']:,.0f}")

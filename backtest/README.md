# Suite de Backtest 10 Anos (True Valuation Framework)

Esta pasta reúne todos os relatórios, códigos de simulação e dossiês analíticos do backtest histórico de 10 anos (2016 a 2026) da carteira dos 19 ativos.

## Arquivos Disponíveis:

1. **Relatorios Executivos em PDF e HTML**:
   - Relatorio_Backtest_10Y_True_Valuation.pdf: Dossiê analítico geral de 10 anos comparando True Valuation (Convex LTV), Carteira Estática, SPY, QQQ e 60/40.
   - Relatorio_Backtest_10Y_True_Valuation.html: Versão web responsiva do dossiê geral.
   - Relatorio_Comparativo_Estatica_vs_Convex_LTV.pdf: Dossiê comparativo específico isolando o efeito da **Alavancagem Convexa Pura (Carteira Estática LTV)** vs. **Alavancagem Pareada com as Regras de Timing e Poda do Framework**.
   - Relatorio_Comparativo_Estatica_vs_Convex_LTV.html: Versão web responsiva do dossiê comparativo.

2. **Motores e Scripts de Execução**:
   - acktest_engine.py: Motor central com a classe BacktestEngine e geradores de gráficos Plotly para Streamlit.
   - simulate_static_leveraged.py: Script isolado para simular e contrastar a Carteira Estática alavancada com a estratégia True Valuation.

## Resumo dos Resultados (Base ,000,000):
- **True Valuation (Convex LTV 20-30%)**: Final: **,755,953,252** | CAGR: **106.01%** | MaxDD: **-49.93%** | Sharpe: **2.93** | Sortino: **4.14** | Calmar: **2.12**
- **Carteira Estática + Convex LTV 20-30%**: Final: **,449,751,002** | CAGR: **73.36%** | MaxDD: **-73.00%** | Sharpe: **1.63** | Sortino: **2.11** | Calmar: **1.00**
- **Carteira Estática (0% LTV / Sem Dívida)**: Final: **,137,267,519** | CAGR: **60.55%** | MaxDD: **-60.18%** | Sharpe: **1.76** | Sortino: **2.30** | Calmar: **1.01**
- **Nasdaq-100 (QQQ)**: Final: **,151,682** | CAGR: **20.62%** | MaxDD: **-35.12%** | Sharpe: **0.99**
- **S&P 500 (SPY)**: Final: **,054,839** | CAGR: **15.72%** | MaxDD: **-33.72%** | Sharpe: **0.92**

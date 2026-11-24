# GEMINI.md — Institutional Multi-Asset Investment Terminal (360° Engine)

This file defines the architectural invariants, module responsibilities, persistence rules, financial methodology constraints, AI integration boundaries, and validation checklist for this repository. Every developer and AI agent working on this codebase must follow these rules without exception.

---

## 1. High-Level Architecture & Strict Deterministic/AI Separation

- **Front-End:** Streamlit (`app.py`) — 5-tab institutional workspace:
  1. `📄 1. Master Consolidated Report (.PDF)` — Portfolio allocation summary, Full Portfolio OR Single-Asset Master 360° (Portfolio Decision Mode) A4 vector PDF export, and **AI-Powered Master Report** toggle (ON by default when `GEMINI_API_KEY` is present) automatically orchestrating full-portfolio SEC/Crypto filing hydration plus ALL qualitative insights/matrices/events across Sections 1, 3, 4 & 5.
  2. `⚙️ 2. Portfolio Manager (SQLite CRUD)` — Read-only custody sync (IBKR Flex Web Service / XML + Binance Spot API), asset upsert/delete, target weight 100% normalization, and configured target holdings table.
  3. `🔎 3. Single-Asset Deep Dive (Stock & Crypto Picker)` — New-candidate Opportunity Screener (5-filter forensic/valuation audit), individual 2-page PDF dossier, and ad-hoc Gemini Structured Filing Dossier Extractor (shares `data_cache/custom_filings_cache.json` with Tab 1).
  4. `🎛️ 4. Simulators (Inflow & LTV) & Notifier (ON/OFF)` — Shannon's Demon cash inflow simulator, Convex LTV / Aave V3 Health Factor stress-tester, and passive morning notifier (Telegram / Discord) with optional AI executive briefing toggle.
  5. `🤖 5. AI Portfolio Analyst` — Conversational AI analyst powered by Google Antigravity SDK in **strictly read-only mode**.

- **Ironclad Separation Rule (Deterministic Math vs. AI Layer):**
  - All financial, accounting, valuation, on-chain, macro, risk, and look-through calculations live strictly inside deterministic Python modules in `core/`.
  - **AI never computes, interpolates, extrapolates, or invents financial figures.** AI components either:
    - (**Front A — `core/gemini_client.py` + `core/ai_report_orchestrator.py`**, direct `google-genai` Interactions API): Automatically hydrate SEC/Crypto filings (`custom_filings_cache.json`, 7-day TTL) across the entire portfolio and synthesize ALL qualitative matrices, moats, Porter 5 Forces, Calls Q&A, M&A, DeFi narratives/cycle commentary, micro events, and executive thesis (`ai_master_insights_cache.json`, 24-hour TTL) strictly from pre-computed deterministic JSON payloads, plus morning notifier briefing interpretation.
    - (**Front B — `core/ai_analyst.py`**, `google-antigravity` SDK): Orchestrate **read-only Python Custom Tools** wired directly to the deterministic `core/` engines and reason strictly over tool outputs.

---

## 2. Core Module Map (`core/`)

| Module | Primary Responsibility |
| :--- | :--- |
| `core/market_data.py` | Parallel sub-second quote streaming (`Binance Spot` -> `CoinCap` for crypto; `Yahoo Finance v8 direct chart` -> `yfinance.fast_info` for equities/ETFs). |
| `core/live_quant_fetcher.py` | Cached real-time quantitative overlays (`^VIX`, `USDBRL=X`, global multi-currency FX via `fetch_live_currency_rate`, `yfinance` statements w/ FX conversion + SEC EDGAR XBRL facts, live ETF `top_holdings`, Binance Futures funding/OI/24h Vol, DeFiLlama TVL/Fees/Stablecoins, CoinGecko dominance, CoinMetrics MVRV/Supply, and live ADTV). |
| `core/backtest_engine.py` | Real 3-year daily-return historical portfolio backtest (`SPY` equity trading-day calendar alignment, 12h Parquet cache) producing cumulative equity curves vs. `SPY`/`BTC-USD`, drawdowns, CAGR, Volatility, Sharpe, Sortino, MaxDD, Calmar, historical VaR/CVaR (95%/99%), Top-12 correlation matrix, crisis stress-tests, and Shannon Inflow vs. Passive DCA simulation. |
| `core/valuation_backtest.py` | Composable 10-year sector-stratified point-in-time valuation & on-chain parity backtest simulator driven by SEC EDGAR XBRL (`US-GAAP` + `IFRS`), FRED macro series, split-adjusted market/valuation prices, asymmetrical equity pruning (`TECH_HIGH_GROWTH` hold + quality-gated `Cash Cow`/Traditional trims), `L1 Major` hold vs. `DeFi` trailing exit + `BTC <= 1.05x 200W SMA` re-entry, continuous LTV, and 15% tax/loss-carryforward ledger. |
| `core/macro_engine.py` | FRED CSV + Yahoo Finance macro aggregation: lagging indicators (GDP, CPI, Fed Funds, Debt/GDP, U3), Sahm's Rule paired with Payroll & ICSA, SOS Indicator, Services vs. Mfg PMI (+ FRED `IPMAN`), 10Y-2Y Yield Curve dynamics, M2 vs. DXY, live `^VIX`, and `USDBRL=X`. |
| `core/portfolio_engine.py` | ACID SQLite CRUD (`portfolio_store.db` <-> `portfolio_config.json`), target weight 100% validation/normalization, live P&L / mark-to-market drift, and generic dynamic ETF Look-Through overlap decomposition across all SQLite ETFs (`SPY`, `QQQ`, `SMH`, `ITA`, `QLD 2x`, plus any custom ETF via `fetch_live_etf_constituents`). |
| `core/custody_sync_engine.py` | Strictly read-only broker/exchange custody sync (Interactive Brokers Flex Web Service / Activity XML + Binance Spot `account` & `myTrades` cost-basis API), auto-syncing on startup/refresh when `.env` keys are present (preserving zeroed-out positions), producing side-by-side custody vs. SQLite target reconciliation (`build_custody_reconciliation`), and writing exclusively via `PortfolioEngine`. |
| `core/equity_engine.py` | Forensic health & 8-method Forward (NTM) valuation engine over shallow copies of `EQUITY_FUNDAMENTAL_KB` + live XBRL/`yfinance` statement overlays + `GLOBAL_BANK_PEERS_DB`. |
| `core/crypto_engine.py` | On-chain cycle metrics (`MVRV Z-Score`, `NUPL`, `aSOPR 1.0`, `Pi Cycle Top`, `200W SMA`), mining (`Hash Ribbon`, `MMC`), flows, tokenomics (`NVM`, `NVT GC`, `P/F`, `Protocol Real Earnings`, `Real Yield`, unlocks, theoretical post-dilution price), and live Binance/DeFiLlama/CoinMetrics derivatives & TVL overlays. |
| `core/filings_engine.py` | Documentary dossiers (`EquityDocumentaryDossier`, `CryptoDocumentaryDossier`) merging static `EQUITY_FILINGS_DB` / `CRYPTO_FILINGS_DB`, dynamic Gemini Structured Output extraction (`data_cache/custom_filings_cache.json`), 1-click auto-fetch, and deterministic public-telemetry fallback dossiers for any non-KB equity/crypto. |
| `core/filing_fetcher.py` | Zero-download multi-document fetcher capturing SEC EDGAR (`10-K`/`20-F`, `10-Q`/`6-K`, `8-K`, `Form 4`/`DEF 14A`) + `yfinance` Analyst Consensus for equities, and Whitepaper + GitHub live 28d commits/devs + Snapshot DAO + DeFiLlama Audits/Hacks for crypto. |
| `core/geopolitics_micro_engine.py` | Macro-geopolitical impact matrix (10-K revenue/supply-chain exposure) and corporate/protocol micro events (`8-K`, `Form 4`, DAO governance). |
| `core/intelligence_reports_engine.py` | Synthesizes industry tech disruptions, hard-asset macro sensitivity matrix, DeFiLlama macro TVL stats, DeFi cycle indicators, M&A/Earnings Call Q&A dossiers, and core dev upgrades. |
| `core/screener_engine.py` | Strict 5-filter quantitative & forensic screener for Stocks (`extra_tickers`) and Cryptoassets (`extra_symbols`). |
| `core/risk_timing_engine.py` | Performance risk metrics (`Sharpe`, `Sortino`, `Calmar` backed by real 3y backtest), live `^VIX`, live ADTV liquidity (`< 1%`), Convex LTV panel + Aave V3 stress-test table, consultative-only timing rules, Shannon Inflow eligibility, and Tax-Drag Hurdle Rate (`0.0%` at loss). |
| `core/deep_dive_engine.py` | On-demand single-asset analyzer for any Stock, ETF, or Crypto (KB lookup or dynamic `yfinance` + SEC XBRL `live_quant_fetcher` synthesis) + 5-filter funnel scoring (`0–100`) and Regime 1–4 classification. |
| `core/charts.py` | Library of 16 dark-theme Plotly builders (tested standalone; not rendered in `app.py` UI). |
| `core/pdf_charts.py` | Legacy standalone SVG helpers (not embedded in Master PDF; decision reports are table-driven). |
| `core/pdf_exporter.py` | Headless Chromium / Microsoft Edge `--print-to-pdf` vector PDF compiler (`A4 landscape`) for the graph-free 7-section 360° Master Report (all decision tables including 3Y Backtest, VaR/CVaR, Shannon vs Passive DCA, and Crisis Stress-Tests) and Individual Deep Dive dossier (including M&A/Goodwill, Moats, and Crypto protocol dossiers). |
| `core/background_notifier.py` | Windows Task Scheduler (`Antigravity_Quant_Morning_Notifier`) ON/OFF passive alerting daemon (Telegram / Discord) with optional Gemini executive interpretation. |
| `core/integrity_guard.py` | Plotly anti-overlap sanitizer (`sanitize_plotly_figure_against_overlaps`) and 33-criterion ecosystem data preservation auditor (`run_complete_ecosystem_integrity_audit`). |
| `core/gemini_client.py` | Direct `google-genai` Interactions API wrapper (`store=False`), `.env` loader, Structured Outputs (Pydantic), PDF executive synthesis, and graceful fallback when `GEMINI_API_KEY` is absent. |
| `core/ai_report_orchestrator.py` | Parallel (`max_workers=3`) AI Master Report orchestrator supporting `Full Deep Hydration` and `Economic / Fast Batch` profiles across dual disk caches (`custom_filings_cache.json` 7d + `ai_master_insights_cache.json` 24h) plus deterministic post-synthesis numeric & ticker grounding verification (`verify_and_sanitize_ai_bundle`). |
| `core/ai_analyst.py` | Read-only `google-antigravity` SDK agent with 7 custom tools linked to deterministic `core/` engines, explicit session persistence, and strict tool-grounding prompt constraints. |

---

## 3. SQLite & Config Persistence Rules (`portfolio_store.db`)

- **Database file:** `portfolio_store.db` in project root, synchronized with `portfolio_config.json` via `PortfolioEngine._sync_sqlite_to_json()`.
- **Table `portfolio_assets` Schema:**
  ```sql
  CREATE TABLE IF NOT EXISTS portfolio_assets (
      ticker TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      category TEXT NOT NULL,
      sector_vertical TEXT NOT NULL,
      target_weight_pct REAL NOT NULL,
      avg_buy_price REAL NOT NULL,
      ltv_turbo_eligible INTEGER NOT NULL,
      fair_price REAL NOT NULL,
      role_description TEXT,
      accumulate_rule TEXT,
      sell_rule TEXT,
      yield_mechanism TEXT,
      display_order INTEGER DEFAULT 999
  )
  ```
- **Governance Rules:**
  - All mutations (writes, updates, deletes, weight normalizations) MUST go exclusively through `PortfolioEngine` (`upsert_asset`, `delete_asset`, `normalize_weights_to_100`).
  - Target portfolio weights must sum to **100.00%** (`is_weight_valid_100`). Leverage is reflected separately in `effective_gross_exposure_pct` (accounting for 2x `QLD`).
  - **AI agents and direct LLM calls are strictly READ-ONLY against `portfolio_store.db`** (`portfolio_assets`) and must never alter holdings, weights, cost basis, or `portfolio_config.json`.

---

## 4. Financial Methodology Invariants (Must Not Regress)

1. **English-Only Institutional Output:** All UI copy, chart titles, engine verdicts, PDF sections, CAGR keys (`Revenue`, `Gross Profit`, `EBIT`, `EBITDA`, `NOPAT`, `Net Income`, `CFO`, `FCF`, `EPS`, `Dividends`, `Book Value`, `ROIC`), and AI outputs must stay in clean institutional English (legacy PT key fallbacks may remain internally for backward compatibility).
2. **NO Altman Z-Score:** Altman Z-Score is intentionally excluded from equity forensic auditing and PDF reporting. Solvency evaluation relies strictly on **Current Ratio (`> 1.0x`)**, **Positive Cash After Annual Expenses**, **Interest Coverage (`> 3.0x` healthy / `> 4.0x` screener)**, and **Debt/EBITDA**.
3. **Forensic Accounting + 12-KPI CAGR Matrix:** Equity forensic health computes **Sloan Ratio** (`<= +5%` pass, `< -10%` optimal), **CFO/EBITDA** (`>= 0.90x` pass, `> 1.0x` optimal), **NWC vs. historical CFO CV**, **ROIC (NOPAT w/ Goodwill) vs. WACC**, and **DuPont 3 Pillars** (`Net Margin × Asset Turnover × Financial Leverage`), plus 3y/5y/10y CAGRs across all 12 KPIs.
4. **Banking Sector Calibration (`FINANCIAL_BANK`) & Asymmetric Sector Rules:** Banks (`JPM`, `BAC`, `WFC`, `C`, `DBSDY`) are never judged by `CFO/EBITDA`, `Sloan Ratio`, or `EV/EBITDA` (deposits are operating liabilities). Banking uses **P/TBV vs. ROE**, **Financial PEGY (`NTM P/E ÷ [g_EPS + DY]`)**, `Ke` (CAPM), Basel CET1/LCR, and enforces a structural **P/B `< 1.0x` veto**. Disruptive Fintechs (`NU`) and high-CapEx AI infrastructure leaders (`GOOGL`) map to `TECH_HIGH_GROWTH` (EV/EBIT PEGY), and mature Cash Cows/processors (`AAPL`, `MSFT`, `META`, `MA`, `V`) map to `TECH_CASH_COW` (EV/FCF PEGY). Parity-validated asymmetric pruning: `TECH_HIGH_GROWTH` applies valuation strictly for purchases/rotations (`0%` valuation pruning), whereas `TECH_CASH_COW` trims `50%` at `Enterprise PEGY > 1.4x` and `FINANCIAL_BANK` / `CYCLICAL` / `DEFENSIVE_RETAIL` trim `50%` at `1.5x` / `0.80x` / `1.20x` paired with accounting Quality Gates (`Sloan Ratio <= +10%`, `CFO/EBITDA >= 0.70x`, Gross Margin stability).
5. **8 Forward (NTM) Valuation Methods:** (1) NTM 3-scenario DCF w/ 10% Margin of Safety, (2) Paired Reverse DCF (`g_impl` vs. `g_fund`), (3) Owner Earnings Yield vs. US 10Y Risk-Free Rate, (4) Current/NTM Multiples vs. Sector/5Y avg (inverted interpretation for cyclicals), (5) EVA, (6) Sector-Strict PEGY (`Gold Band`: `0–1.2x` Tech/Retail/Cash Cow using EV/EBIT or EV/FCF; `0–1.0x` Financial PEGY for Banks), (7) Greenblatt Magic Formula rank, (8) Sum of the Parts (`SOTP`).
6. **Crypto On-Chain, Asymmetric Exit & Protocol Real Economics:** Evaluates `MVRV Z-Score`, `NUPL`, `aSOPR` (`1.0` bull support / bear resistance), `Pi Cycle Top`, `200W SMA`, `MMC`, `NVM Ratio`, `NVT Golden Cross`, **Protocol Real Earnings** (`Annualized Fees - Token Issuance`), **Real Yield** (`APR - Inflation`), 30d unlocks (`<= 2.5%/mo`), **Theoretical Post-Unlock Price**, and GitHub/Token Sniffer thresholds. Parity-validated crypto timing: `BTC` performs `50%` trims exclusively on **`Pi Cycle Top`** (`111d >= 2x 350d SMA`, removing premature `NUPL Reverse Cross 0.65 -> 0.60` trims, acting automatically as `0%` Hold in non-parabolic cycles); `L1 Majors` (`ETH`, `SOL`) follow full-cycle `0%` pruning Hold; `DeFi / Mid-Caps` trigger `100%` exits on `BTC NUPL > 0.60` or `MVRV > 3.0` + trailing drawdown `>= 20%`, re-entering strictly at historical floor **`BTC <= 1.05x 200W SMA`** (confirmable with `NUPL < 0.0`, replacing legacy `NUPL < 0.30`).
7. **Consultative-Only Governance, Shannon's Demon & Continuous LTV Policy:**
   - The terminal NEVER executes automated trades or calendar rebalancing. All timing signals are strictly **Consultative / Non-Binding** paired with **Tax-Drag Hurdle Rate**.
   - Rebalancing uses **Shannon's Demon Inflow** (directing fresh capital exclusively to discounted underweight holdings — zero tax-drag).
   - **Continuous LTV Framework:** Structural continuous baseline **`20%`** (expandable tactically up to **`25%`** for wealth maximization; zero `10%` defensive reduction in high-rate regimes), Anti-cyclical Turbo Trigger `28%–30%` (CAPE `< 28x` / BTC `MVRV Z < 0.5`), Hard-Cap safety ceiling `45%–50%` (IBKR Box Spreads & Aave V3 stress-tests). Altcoins are strictly prohibited as debt collateral.

---

## 5. PDF Export & Layout Rules (`core/pdf_exporter.py`)

- Compiles HTML -> A4 Landscape PDF (`@page { size: A4 landscape; margin: 9mm 10mm 10mm 10mm; }`) via headless Chrome or Edge (`--headless=new --print-to-pdf`).
- Reports are 100% graph-free and table-driven: ALL decision-making telemetry (macro cycles, look-through overlap, forensic accounting, 8-method valuation, crypto on-chain & tokenomics, SEC/whitepaper dossiers, 5-filter screener, 3-Year Historical Backtest, Daily VaR/CVaR, Shannon vs. Passive DCA, Crisis Stress-Tests, and Convex LTV governance) resides inside the Master PDF and Individual Deep Dive PDF, while `app.py` serves strictly as the emission/configuration/simulator/chat control plane.
- Dense tables MUST stay split into Part A / Part B (max 5–6 columns per table) with `word-break: normal` to prevent clipping or squeezed typography.
- When `GEMINI_API_KEY` is configured and Tab 1's **AI-Powered Master Report** toggle is ON (default), ALL qualitative insights, matrices, events, and portfolio SEC/Crypto dossiers across Sections 1, 3, 4, and 5 are automatically generated by Gemini (dual disk cache: `data_cache/custom_filings_cache.json` 7d TTL + `data_cache/ai_master_insights_cache.json` 24h TTL) and cleanly embedded into the A4 landscape PDF while leaving mechanical numbers (e.g., DeFi cycle `current_reading`, `roic_op_margin_pct`, `roic_cap_turnover_x`, spot prices, unlocks, Real Earnings) 100% deterministic. When `GEMINI_API_KEY` is missing or the toggle is OFF, the exporter degrades gracefully to deterministic/static baselines.
- The optional **Executive AI Thesis & Cross-Asset Risk Synthesis** block (`ai_executive_summary`) and provenance banner render cleanly in Section 1 right below `.kpi-row` using `break-inside: avoid` and HTML-escaped strings (`_esc`), and are 100% omitted when `None` or disabled.

---

## 6. AI Layer Rules & Security

- **API Keys & Secrets:** Store `GEMINI_API_KEY` (plus optional `GEMINI_MODEL`, `GEMINI_FAST_MODEL`, `ANTIGRAVITY_MODEL`) in root `.env`. `.env` and `.env.*` (except `!.env.example`) MUST stay in `.gitignore`. Never log, print, commit, or embed API keys in Streamlit HTML/PDF outputs or artifacts.
- **Models & SDKs (No Deprecated Surfaces):**
  - Use **`google-genai >= 3.2.0`** via **`client.interactions.create(...)`** (`store=False`) and default model **`gemini-4-hydrogen`** (`gemini-3.5-flash-lite` for fast tasks like morning briefing interpretation). **NEVER** import deprecated `google.generativeai` or use retired `gemini-2.5-*`, `gemini-2.0-*`, or `gemini-1.5-*` models.
  - Use **`google-antigravity >= 0.1.23`** via `Agent` and `LocalAgentConfig` with `model=None` by default (uses SDK default `gemini-3.8-flash` unless `ANTIGRAVITY_MODEL` is explicitly set).
- **Read-Only Agent Lockdown (`core/ai_analyst.py`):**
  - Built-in tools disabled: `CapabilitiesConfig(enable_subagents=False, enabled_tools=types.BuiltinTools.none())`.
  - Policy belt-and-suspenders: `policies=[policy.deny_all(), *(policy.allow(fn.__name__) for fn in custom_tools)]`.
  - No shell (`run_command`), no file writes (`create_file`, `edit_file`), no web browsing or subagents.
  - Strictly bounded via `BudgetConfig(max_model_calls=8, max_tool_calls=12)`.
- **Graceful Degradation & Resilient Model Fallback:** Missing `GEMINI_API_KEY`, rate limits (HTTP 429), high-demand spikes (HTTP 503), or timeouts automatically trigger a 5-minute in-process cooldown and automatic fallback across current Gemini models (`gemini-3.5-flash-lite` -> `gemini-3.1-flash-lite`), and degrade cleanly to deterministic behavior across all 4 core tabs, PDF generation, and background notifier.
- **Protobuf / Streamlit Runtime Note:** `google-antigravity 0.1.23` requires `protobuf>=7` (tested on `protobuf 7.36.2` alongside `streamlit 1.51.0`). Do NOT downgrade `protobuf<7` even though `pip check` reports Streamlit's upper bound warning; always verify Streamlit UI boot after dependency updates.

---

## 7. Validation Checklist (Run Before Committing)

1. **Syntax Check:**
   ```bash
   python -m py_compile app.py core/*.py tests/*.py
   ```
2. **Automated Unit Test Suite & CI Workflow Template (`docs/github_ci_workflow.yml`):**
   ```bash
   python -m unittest discover -s tests -v
   ```
   Verifies financial invariants (no Altman Z, bank calibration, Tax-Drag loss=0/gain formula), isolated SQLite CRUD + Multi-Currency FX resolver, all 16 Plotly figures, backtest VaR/CVaR + stress-tests + correlation matrix, Antigravity read-only lockdown, zero-key graceful degradation, and the **33/33 (100%) Ecosystem Integrity Audit**.
3. **Ecosystem Integrity Audit (Standalone One-Liner, 33 Criteria, Must Pass 33/33 = 100%, Without Altman Z):**
   ```bash
   python -c "from core.macro_engine import MacroEngine; from core.portfolio_engine import PortfolioEngine; from core.equity_engine import EquityEngine; from core.crypto_engine import CryptoEngine; from core.filings_engine import FilingsEngine; from core.geopolitics_micro_engine import GeopoliticsMicroEngine; from core.screener_engine import ScreenerEngine; from core.risk_timing_engine import RiskTimingEngine; from core.integrity_guard import run_complete_ecosystem_integrity_audit; m=MacroEngine().run_macro_aggregation(); p=PortfolioEngine().build_overview_and_lookthrough(100000.0); e=EquityEngine(m.yield_curve.get('us10y_pct',4.42)).analyze_portfolio_equities(); c=CryptoEngine().analyze_portfolio_cryptos(); f=FilingsEngine(); g=GeopoliticsMicroEngine(); s=ScreenerEngine(); rt=RiskTimingEngine().build_risk_and_consultative_timing(p,e,c); a=run_complete_ecosystem_integrity_audit(m,p,e,c,f.get_equity_dossiers(),f.get_crypto_dossiers(),g.get_geopolitical_matrix(),g.get_micro_events(),s.run_stock_screener(),s.run_crypto_screener(),rt); print(a.total_criteria_passed, '/', a.total_criteria_checked, f'({a.preservation_rate_pct}%)')"
   ```
4. **Graceful Degradation Check (Zero Key):** Verify `GEMINI_API_KEY=""` leaves PDF generation, `FilingsEngine` fallback, `BackgroundNotifierEngine`, and `InstitutionalAIAnalyst.is_available()` clean without exceptions.
5. **Antigravity Read-Only Lockdown Check:** Verify `LocalAgentConfig` has `capabilities.enable_subagents is False` and `capabilities.enabled_tools == []`.
6. **Streamlit Boot / UI Smoke Test:** Verify `AppTest.from_file("app.py")` / `streamlit run app.py --server.headless true` runs cleanly under `protobuf>=7` across all 5 tabs.
7. **Git Hygiene:** Run `git status` and `git check-ignore` to confirm `.env`, `notifier_config.json`, `data_cache/ai_sessions/`, `data_cache/custom_filings_cache.json`, `data_cache/ai_master_insights_cache.json`, `data_cache/live_quant_cache.json`, and `data_cache/*.parquet` are untracked/ignored.

---

## 8. Documentation & Git Sync Policy

- **Default Git & Documentation Synchronization Rule:** Whenever any feature, module, tab, dependency, or financial invariant is added or modified in `app.py` or `core/`, ALWAYS keep [README.md](README.md), [GEMINI.md](GEMINI.md), and [.env.example](.env.example) synchronized and commit + push the verified changes cleanly to `origin` after passing Section 7 checks.
- **Secret Protection:** Double-check `git status --short` and `git check-ignore` before every commit so `.env`, `notifier_config.json`, `data_cache/sec_tickers.json`, `data_cache/custom_filings_cache.json`, `data_cache/ai_master_insights_cache.json`, `data_cache/live_quant_cache.json`, `data_cache/*.parquet`, and `data_cache/ai_sessions/` never enter Git history.

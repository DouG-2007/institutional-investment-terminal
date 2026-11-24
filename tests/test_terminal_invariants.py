"""
Institutional Multi-Asset Investment Terminal — Automated Test Suite
Verifies core financial invariants, SQLite custody ledger CRUD, Plotly charts,
Excel exports, Read-Only Antigravity agent lockdown, zero-key graceful
degradation, and the 33-criterion ecosystem integrity audit.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from unittest import mock

import openpyxl
import pandas as pd

from core.ai_analyst import InstitutionalAIAnalyst, build_readonly_agent_config
from core.background_notifier import BackgroundNotifierEngine
from core.charts import (
    build_banks_ptbv_vs_roe_scatter,
    build_btc_asopr_chart,
    build_btc_picycle_200w_hashribbon_mmc_chart,
    build_crypto_github_and_earnings_chart,
    build_crypto_mvrv_nupl_chart,
    build_crypto_nvm_and_cdd_chart,
    build_crypto_onchain_gauges_chart,
    build_deep_dive_dupont_and_margins_chart,
    build_deep_dive_forensic_5y_chart,
    build_deep_dive_valuation_cockpit_chart,
    build_macro_comprehensive_chart,
    build_multi_method_valuation_chart,
    build_portfolio_correlation_heatmap_chart,
    build_portfolio_equity_curve_chart,
    build_portfolio_weight_gauge_chart,
    build_yield_curve_and_icsa_chart,
)
from core.backtest_engine import run_portfolio_backtest
from core.crypto_engine import CryptoEngine
from core.deep_dive_engine import DeepDiveEngine
from core.equity_engine import EquityEngine
from core.excel_exporter import build_institutional_excel_bytes
from core.filings_engine import FilingsEngine
from core.geopolitics_micro_engine import GeopoliticsMicroEngine
from core.integrity_guard import run_complete_ecosystem_integrity_audit
from core.live_quant_fetcher import GLOBAL_CURRENCY_OPTIONS, fetch_live_currency_rate
from core.macro_engine import MacroEngine
from core.pdf_exporter import InstitutionalPDFExporter
from core.portfolio_engine import PortfolioEngine
from core.risk_timing_engine import RiskTimingEngine
from core.screener_engine import ScreenerEngine


class TestTerminalInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.macro = MacroEngine().run_macro_aggregation()
        cls.rf_pct = cls.macro.yield_curve.get("us10y_pct", 4.42)
        cls.portfolio = PortfolioEngine().build_overview_and_lookthrough(100_000.0)
        cls.equities = EquityEngine(risk_free_rate_pct=cls.rf_pct).analyze_portfolio_equities()
        cls.cryptos = CryptoEngine().analyze_portfolio_cryptos()
        cls.filings = FilingsEngine()
        cls.geo = GeopoliticsMicroEngine()
        cls.screener = ScreenerEngine()
        cls.risk_timing = RiskTimingEngine().build_risk_and_consultative_timing(
            portfolio=cls.portfolio,
            equities=cls.equities,
            cryptos=cls.cryptos,
            fed_funds_rate_pct=float(cls.macro.monetary_aggregates.get("fed_funds_rate_pct", 4.25)),
            vix_current=float(cls.macro.monetary_aggregates.get("vix_current", 18.4)),
            capital_gains_tax_rate_pct=15.0,
        )

    def test_1_financial_invariants_no_altman_and_tax_drag(self) -> None:
        pdf_exp = InstitutionalPDFExporter()
        dd_eq = DeepDiveEngine(self.rf_pct).analyze_single_ticker("NVDA", portfolio=self.portfolio)
        dd_html = pdf_exp.build_deep_dive_html_report(dd_eq)
        bt_sample = run_portfolio_backtest(self.portfolio.positions, 100_000.0, self.rf_pct)
        master_html = pdf_exp.build_complete_html_report(
            macro=self.macro,
            portfolio=self.portfolio,
            equities=self.equities,
            cryptos=self.cryptos,
            eq_filings=self.filings.get_equity_dossiers(),
            cr_filings=self.filings.get_crypto_dossiers(),
            geo_matrix=self.geo.get_geopolitical_matrix(prefer_ai_cache=False),
            micro_events=self.geo.get_micro_events(prefer_ai_cache=False),
            stock_screener=self.screener.run_stock_screener(),
            crypto_screener=self.screener.run_crypto_screener(),
            risk_timing=self.risk_timing,
            backtest=bt_sample,
        )
        # Altman Z-Score and embedded graphs are intentionally excluded across reporting
        self.assertNotIn("altman", dd_html.lower())
        self.assertNotIn("altman", master_html.lower())
        self.assertNotIn("<svg", master_html)
        # 3Y Backtest, VaR/CVaR, Shannon DCA vs Passive, and Stress-Test tables are in Section 7
        self.assertIn("7.3A.", master_html)
        self.assertIn("7.3B.", master_html)
        self.assertIn("table-header-group", master_html)
        self.assertIn("break-inside: avoid !important", master_html)

        # Single-Asset Master 360° (Portfolio Decision Mode) scoped to one equity holding
        single_master_html = pdf_exp.build_complete_html_report(
            macro=self.macro,
            portfolio=self.portfolio,
            equities=self.equities,
            cryptos=self.cryptos,
            eq_filings=self.filings.get_equity_dossiers(),
            cr_filings=self.filings.get_crypto_dossiers(),
            geo_matrix=self.geo.get_geopolitical_matrix(prefer_ai_cache=False),
            micro_events=self.geo.get_micro_events(prefer_ai_cache=False),
            stock_screener=self.screener.run_stock_screener(),
            crypto_screener=self.screener.run_crypto_screener(),
            risk_timing=self.risk_timing,
            backtest=bt_sample,
            focus_ticker="NVDA",
        )
        self.assertIn("SINGLE-ASSET MASTER 360° DECISION REPORT", single_master_html)
        self.assertIn("NVDA", single_master_html)
        self.assertNotIn("SECTION 3: CRYPTO ANALYTICAL INTELLIGENCE", single_master_html)

        # Tax-Drag Hurdle Rate: 0.0% at loss, exact formula at +100% gain with 15% tax = 7.50%
        loss_pos = self.portfolio.positions[0]
        orig_pnl = loss_pos.pnl_pct
        try:
            loss_pos.pnl_pct = -15.0
            rt_loss = RiskTimingEngine().build_risk_and_consultative_timing(
                self.portfolio, self.equities, self.cryptos, capital_gains_tax_rate_pct=15.0
            )
            self.assertEqual(rt_loss.consultative_asset_timing_table[0].tax_drag_hurdle_rate_pct, 0.0)

            loss_pos.pnl_pct = 100.0
            rt_gain = RiskTimingEngine().build_risk_and_consultative_timing(
                self.portfolio, self.equities, self.cryptos, capital_gains_tax_rate_pct=15.0
            )
            self.assertEqual(rt_gain.consultative_asset_timing_table[0].tax_drag_hurdle_rate_pct, 7.5)
        finally:
            loss_pos.pnl_pct = orig_pnl

        # Banking calibration: FINANCIAL_BANK must use Financial PEGY and enforce P/B >= 1.0 filter
        # Disruptive Fintechs (NU) map to TECH_HIGH_GROWTH (EV/EBIT PEGY)
        banks = [e for e in self.equities if e.sector_vertical == "FINANCIAL_BANK"]
        self.assertGreater(len(banks), 0)
        for b in banks:
            self.assertIn("Financial PEGY", b.valuation_methods["primary_pegy_label"])
            self.assertGreater(b.valuation_methods["pb_current"], 0.0)

        # Valuation invariants across all equities: monotonic DCF scenarios & positive fair values
        for eq in self.equities:
            vm = eq.valuation_methods
            self.assertLessEqual(vm["dcf_conservador_usd"], vm["dcf_base_usd"])
            self.assertLessEqual(vm["dcf_base_usd"], vm["dcf_otimista_usd"])
            self.assertGreater(vm["pegy_gold_fair_price_usd"], 0.0)
            self.assertGreater(vm["sotp_fair_price_usd"], 0.0)

    def test_2_sqlite_crud_transactions_ledger_and_csv_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = os.path.join(tmp, "portfolio_config.json")
            seed = {
                "assets": [
                    {
                        "ticker": "NVDA",
                        "name": "NVIDIA Corporation",
                        "category": "Hard-Asset Stock",
                        "sector_vertical": "TECH_HIGH_GROWTH",
                        "target_weight_pct": 60.0,
                        "avg_buy_price": 100.0,
                        "ltv_turbo_eligible": True,
                        "fair_price": 150.0,
                    },
                    {
                        "ticker": "BTC-USD",
                        "name": "Bitcoin",
                        "category": "Crypto BTC",
                        "sector_vertical": "CRYPTO_SOV",
                        "target_weight_pct": 40.0,
                        "avg_buy_price": 50000.0,
                        "ltv_turbo_eligible": True,
                        "fair_price": 100000.0,
                    },
                ]
            }
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(seed, f)

            pe = PortfolioEngine(config_path=cfg_path)
            pe.upsert_asset("MSFT", "Microsoft", "Stock", "Big Tech Cash Cow", 20.0, 400.0, True)
            pe.normalize_weights_to_100()
            assets = pe.get_all_assets()
            self.assertAlmostEqual(sum(a["target_weight_pct"] for a in assets), 100.0, places=2)
            ov = pe.build_overview_and_lookthrough(100_000.0)
            self.assertEqual(len(ov.positions), 3)
            self.assertTrue(ov.is_weight_valid_100)
            pe.delete_asset("MSFT")
            pe.normalize_weights_to_100()
            self.assertEqual(len(pe.get_all_assets()), 2)

            # Global FX resolver invariants
            self.assertIn("USD ($)", GLOBAL_CURRENCY_OPTIONS)
            self.assertIn("EUR (€)", GLOBAL_CURRENCY_OPTIONS)
            self.assertEqual(fetch_live_currency_rate("USD"), 1.0)
            with mock.patch("core.live_quant_fetcher._fetch_yahoo_chart_last", return_value=0.95):
                with mock.patch("core.live_quant_fetcher._load_cache_bucket", return_value=None):
                    with mock.patch("core.live_quant_fetcher._save_cache_bucket"):
                        self.assertAlmostEqual(fetch_live_currency_rate("EUR"), 0.95, places=4)

    def test_3_all_16_plotly_charts_and_backtest_risk_metrics(self) -> None:
        dd_eq = DeepDiveEngine(self.rf_pct).analyze_single_ticker("NVDA", portfolio=self.portfolio)
        dd_cr = DeepDiveEngine(self.rf_pct).analyze_single_ticker("BTC-USD", portfolio=self.portfolio)
        corr_sample = pd.DataFrame({
            "BTC-USD": dd_cr.crypto_profile.chart_series["Price"],
            "MVRV_Z": dd_cr.crypto_profile.chart_series["MVRV_Z"],
        }).pct_change().corr()
        mock_bt = {
            "equity_curve_df": dd_cr.crypto_profile.chart_series["Price"].to_frame(name="Portfolio"),
            "drawdown_series": dd_cr.crypto_profile.chart_series["MVRV_Z"] * 0.0 - 5.0,
            "corr_matrix_df": corr_sample,
        }
        btc_prof = self.cryptos.get("BTC-USD") or next(iter(self.cryptos.values()))

        figs = [
            build_macro_comprehensive_chart(self.macro),
            build_yield_curve_and_icsa_chart(self.macro),
            build_banks_ptbv_vs_roe_scatter(self.equities),
            build_multi_method_valuation_chart(self.equities),
            build_portfolio_weight_gauge_chart(self.portfolio.target_weight_sum_pct),
            build_btc_asopr_chart(btc_prof),
            build_btc_picycle_200w_hashribbon_mmc_chart(btc_prof),
            build_crypto_mvrv_nupl_chart(btc_prof),
            build_crypto_nvm_and_cdd_chart(btc_prof),
            build_deep_dive_forensic_5y_chart(dd_eq),
            build_deep_dive_dupont_and_margins_chart(dd_eq),
            build_deep_dive_valuation_cockpit_chart(dd_eq, self.rf_pct),
            build_crypto_onchain_gauges_chart(dd_cr),
            build_crypto_github_and_earnings_chart(dd_cr),
            build_portfolio_equity_curve_chart(mock_bt),
            build_portfolio_correlation_heatmap_chart(mock_bt),
        ]
        self.assertEqual(len(figs), 16)
        for fig in figs:
            self.assertGreater(len(fig.data), 0)

        bt = run_portfolio_backtest(self.portfolio.positions, capital_usd=100_000.0, risk_free_rate_pct=self.rf_pct)
        self.assertGreaterEqual(bt["var_95_daily_pct"], 0.0)
        self.assertGreaterEqual(bt["cvar_95_daily_pct"], bt["var_95_daily_pct"])
        self.assertGreaterEqual(bt["cvar_99_daily_pct"], bt["var_99_daily_pct"])
        if bt["data_source"] == "LIVE_YFINANCE_HISTORY":
            self.assertGreaterEqual(len(bt["stress_tests"]), 3)
            self.assertFalse(bt["corr_matrix_df"].empty)

    def test_4_excel_exporter_valid_workbook(self) -> None:
        xlsx_bytes = build_institutional_excel_bytes(
            portfolio=self.portfolio,
            equities=self.equities,
            cryptos=self.cryptos,
            risk_timing=self.risk_timing,
            backtest={"portfolio_cagr_pct": 18.0, "sharpe_ratio": 1.2, "max_drawdown_pct": 12.0},
        )
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
        expected_sheets = {
            "Portfolio_Holdings",
            "ETF_LookThrough",
            "Equities_Forensic_Valuation",
            "Crypto_OnChain_Tokenomics",
        }
        self.assertEqual(set(wb.sheetnames), expected_sheets)
        self.assertGreater(wb["Portfolio_Holdings"].max_row, 1)

    def test_5_antigravity_readonly_lockdown(self) -> None:
        cfg = build_readonly_agent_config(api_key="dummy-test-key")
        self.assertFalse(cfg.capabilities.enable_subagents)
        self.assertEqual(cfg.capabilities.enabled_tools, [])
        self.assertEqual(cfg.policies[0].name, "deny_all")
        allowed_tools = {p.tool for p in cfg.policies[1:]}
        self.assertEqual(
            allowed_tools,
            {
                "get_portfolio_snapshot",
                "audit_single_asset",
                "get_macro_and_geopolitics",
                "simulate_shannon_inflow",
                "simulate_ltv_stress_test",
                "run_opportunity_screener",
                "get_backtest_and_risk_metrics",
            },
        )
        for forbidden in ("run_command", "edit_file", "create_file", "view_file"):
            self.assertNotIn(forbidden, allowed_tools)

    def test_6_zero_key_graceful_degradation(self) -> None:
        with (
            mock.patch("core.gemini_client.get_gemini_api_key", return_value=None),
            mock.patch("core.ai_analyst.get_gemini_api_key", return_value=None),
        ):
            from core.gemini_client import is_gemini_configured

            self.assertFalse(is_gemini_configured())
            ok_agent, _msg = InstitutionalAIAnalyst().is_available()
            self.assertFalse(ok_agent)

            dos, msg_fil = self.filings.extract_equity_dossier_from_document(
                "NVDA", raw_text="Sample test excerpt", persist=False
            )
            self.assertIsNotNone(dos)
            self.assertIn("static", msg_fil.lower())

            from core.background_notifier import NotifierSettings
            cfg_custom = NotifierSettings(vix_alert_threshold=20.0, drift_alert_threshold_pp=1.0, btc_nupl_buy_threshold=0.5, dcf_upside_alert_pct=5.0)
            notif_payload = BackgroundNotifierEngine().build_morning_briefing_payload(
                macro=self.macro,
                portfolio=self.portfolio,
                equities=self.equities,
                cryptos=self.cryptos,
                micro_events=self.geo.get_micro_events(prefer_ai_cache=False),
                risk_timing=self.risk_timing,
                use_ai=True,
                settings_override=cfg_custom,
            )
            self.assertFalse(notif_payload["ai_enhanced"])
            self.assertGreater(notif_payload["alerts_count"], 0)

        # AI Numeric & Ticker Grounding Verifier (independent of API key)
        from core.ai_report_orchestrator import verify_and_sanitize_ai_bundle

        sample_eq = self.equities[0]
        mock_cache = {
            "macro_sensitivity": [
                {"ticker": sample_eq.ticker, "company_name": "Valid"},
                {"ticker": "FAKE999", "company_name": "Hallucinated"},
            ],
            "executive_summary": {
                "macro_regime_thesis": "With VIX at 99.90 and US 10Y at 19.50%, positioning remains cautious.",
                "cross_asset_risk_synthesis": "Monitor portfolio drift.",
                "key_actionable_priorities": ["Maintain discipline."],
            },
            "equity_qualitative_overrides": {
                sample_eq.ticker: {"roic_central_pillar": "Driven by ROIC of 999.0% across core units."},
                "FAKE999": {"roic_central_pillar": "Should be stripped."},
            },
            "corporate_signal_ma": {},
            "crypto_dev_dossiers": {},
        }
        ver_meta = verify_and_sanitize_ai_bundle(
            out_cache=mock_cache,
            macro=self.macro,
            portfolio=self.portfolio,
            equities=self.equities,
            cryptos=self.cryptos,
            risk_timing=self.risk_timing,
        )
        self.assertTrue(ver_meta["verified_clean"])
        self.assertGreaterEqual(ver_meta["auto_corrected_claims"], 3)
        self.assertEqual([r["ticker"] for r in mock_cache["macro_sensitivity"]], [sample_eq.ticker])
        self.assertNotIn("FAKE999", mock_cache["equity_qualitative_overrides"])
        self.assertNotIn("99.90", mock_cache["executive_summary"]["macro_regime_thesis"])
        self.assertNotIn("999.0%", mock_cache["equity_qualitative_overrides"][sample_eq.ticker]["roic_central_pillar"])

    def test_7_ecosystem_integrity_audit_33_criteria(self) -> None:
        audit = run_complete_ecosystem_integrity_audit(
            macro=self.macro,
            portfolio=self.portfolio,
            equities=self.equities,
            cryptos=self.cryptos,
            eq_filings=self.filings.get_equity_dossiers(),
            cr_filings=self.filings.get_crypto_dossiers(),
            geo_matrix=self.geo.get_geopolitical_matrix(prefer_ai_cache=False),
            micro_events=self.geo.get_micro_events(prefer_ai_cache=False),
            stock_screener=self.screener.run_stock_screener(),
            crypto_screener=self.screener.run_crypto_screener(),
            risk_timing=self.risk_timing,
        )
        self.assertEqual(audit.total_criteria_checked, 33)
        self.assertEqual(audit.total_criteria_passed, 33)
        self.assertEqual(audit.preservation_rate_pct, 100.0)

    def test_8_custody_sync_ibkr_xml_and_sqlite_isolation(self) -> None:
        from core.custody_sync_engine import (
            CustodySyncResult,
            SyncedPosition,
            apply_synced_positions_to_sqlite,
            combine_custody_results,
            parse_ibkr_flex_xml,
        )

        sample_xml = """
        <FlexQueryResponse queryName="Positions" type="AF">
          <FlexStatements count="1">
            <FlexStatement accountId="U1234567">
              <OpenPositions>
                <OpenPosition symbol="NVDA" description="NVIDIA CORP" assetCategory="STK" position="50" markPrice="130.0" positionValue="6500.0" positionValueInBase="6500.0" costBasisPrice="90.0" currency="USD" fxRateToBase="1.0" />
                <OpenPosition symbol="SPY" description="SPDR S&amp;P 500 ETF" assetCategory="ETF" position="10" markPrice="580.0" positionValue="5800.0" positionValueInBase="5800.0" costBasisPrice="450.0" currency="USD" fxRateToBase="1.0" />
              </OpenPositions>
              <CashReport>
                <CashReportCurrency currency="BASE_SUMMARY" endingCash="1200.0" />
              </CashReport>
            </FlexStatement>
          </FlexStatements>
        </FlexQueryResponse>
        """
        ibkr_res = parse_ibkr_flex_xml(sample_xml)
        self.assertTrue(ibkr_res.ok)
        self.assertEqual(len(ibkr_res.positions), 2)
        self.assertAlmostEqual(ibkr_res.total_nav_usd, 12300.0, places=2)
        self.assertAlmostEqual(ibkr_res.stablecoin_cash_usd, 1200.0, places=2)

        bn_mock = CustodySyncResult(
            ok=True,
            source_summary="Binance Spot (1 positions)",
            positions=[
                SyncedPosition(
                    ticker="BTC-USD",
                    name="BTC (Binance Spot)",
                    source="Binance",
                    quantity=0.1,
                    market_price_usd=90000.0,
                    market_value_usd=9000.0,
                    avg_buy_price_usd=62000.0,
                    actual_weight_pct=100.0,
                    asset_class_ui="Crypto",
                    sector_ui="Bitcoin Sovereign PoW Reserve",
                    ltv_turbo_eligible=True,
                    role_description="Synced from Binance Spot custody.",
                )
            ],
            total_nav_usd=9000.0,
            stablecoin_cash_usd=500.0,
        )
        combined = combine_custody_results([ibkr_res, bn_mock])
        self.assertTrue(combined.ok)
        self.assertEqual(len(combined.positions), 3)
        self.assertAlmostEqual(sum(p.actual_weight_pct for p in combined.positions), 100.0, delta=0.1)

        with tempfile.TemporaryDirectory() as tmpd:
            cfg_path = os.path.join(tmpd, "test_sync_cfg.json")
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump({"assets": [{"ticker": "OLD1", "name": "Old Asset", "category": "Hard-Asset Stock", "sector_vertical": "OTHER", "target_weight_pct": 100.0, "avg_buy_price": 10.0, "ltv_turbo_eligible": True}]}, f)
            pe = PortfolioEngine(config_path=cfg_path)
            # First test merge_preserve_targets: OLD1 (zeroed out in custody) MUST remain in SQLite
            up_m, rm_m = apply_synced_positions_to_sqlite(
                pe,
                combined.positions,
                sync_mode="merge_preserve_targets",
                normalize_to_100=True,
            )
            self.assertEqual(up_m, 3)
            self.assertEqual(rm_m, 0)
            merged_tickers = {a["ticker"] for a in pe.get_all_assets_from_db()}
            self.assertIn("OLD1", merged_tickers)
            self.assertEqual(len(merged_tickers), 4)

            # Next test replace_with_actual_weights: removes unheld OLD1
            up_cnt, rm_cnt = apply_synced_positions_to_sqlite(
                pe,
                combined.positions,
                sync_mode="replace_with_actual_weights",
                normalize_to_100=True,
            )
            self.assertEqual(up_cnt, 3)
            self.assertGreater(rm_cnt, 0)
            synced_db = pe.get_all_assets_from_db()
            self.assertEqual(len(synced_db), 3)
            self.assertAlmostEqual(sum(a["target_weight_pct"] for a in synced_db), 100.0, delta=0.05)

            # Verify zero-env auto_sync returns None without network calls
            from core.custody_sync_engine import (
                _load_custody_sync_cache,
                _save_custody_sync_cache,
                auto_sync_configured_brokers,
            )
            with mock.patch.dict(os.environ, {"IBKR_FLEX_TOKEN": "", "IBKR_FLEX_QUERY_ID": "", "BINANCE_API_KEY": "", "BINANCE_API_SECRET": ""}, clear=False):
                self.assertIsNone(auto_sync_configured_brokers(pe))

            # Verify local custody sync cache round-trip using temp path
            with mock.patch("core.custody_sync_engine.CUSTODY_CACHE_PATH", os.path.join(tmpd, "custody_cache.json")):
                _save_custody_sync_cache(combined)
                loaded_c = _load_custody_sync_cache(ttl_sec=600.0)
                self.assertIsNotNone(loaded_c)
                self.assertEqual(len(loaded_c.positions), 3)


if __name__ == "__main__":
    unittest.main()

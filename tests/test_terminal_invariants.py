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
        )
        # Altman Z-Score is intentionally excluded across reporting
        self.assertNotIn("altman", dd_html.lower())
        self.assertNotIn("altman", master_html.lower())

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
        banks = [e for e in self.equities if e.sector_vertical == "FINANCIAL_BANK"]
        self.assertGreater(len(banks), 0)
        for b in banks:
            self.assertIn("Financial PEGY", b.valuation_methods["primary_pegy_label"])
            self.assertGreater(b.valuation_methods["pb_current"], 0.0)

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

            # Real custody ledger arithmetic
            pe.add_transaction("2026-01-10", "NVDA", "BUY", 10.0, 100.0, 5.0)
            pe.add_transaction("2026-02-15", "NVDA", "BUY", 10.0, 120.0, 5.0)
            pe.add_transaction("2026-03-01", "NVDA", "SELL", 5.0, 150.0, 5.0)
            pe.add_transaction("2026-04-01", "NVDA", "DIVIDEND", 1.0, 25.0, 0.0)

            summary = pe.compute_ledger_summary(live_prices={"NVDA": 140.0})
            nvda_led = summary["by_ticker"]["NVDA"]
            self.assertAlmostEqual(nvda_led["net_quantity"], 15.0, places=4)
            self.assertAlmostEqual(nvda_led["avg_buy_price_usd"], 110.5, places=2)
            self.assertAlmostEqual(nvda_led["realized_pnl_usd"], 192.5, places=2)
            self.assertAlmostEqual(nvda_led["income_usd"], 25.0, places=2)

            # Sync ledger cost basis back to portfolio_assets
            synced_n = pe.sync_ledger_cost_basis_to_assets()
            self.assertEqual(synced_n, 1)
            nvda_row = next(a for a in pe.get_all_assets() if a["ticker"] == "NVDA")
            self.assertAlmostEqual(nvda_row["avg_buy_price"], 110.5, places=2)

            # CSV import
            csv_payload = b"ticker,name,asset_class,sector,target_weight_pct,avg_buy_price\nCOST,Costco,Stock,Defensive Retail,10.0,850.0\n"
            imported_cnt, errs = pe.import_assets_from_csv(csv_payload)
            self.assertEqual(imported_cnt, 1)
            self.assertEqual(errs, [])
            pe.delete_asset("COST")

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
            transactions=[],
            backtest={"portfolio_cagr_pct": 18.0, "sharpe_ratio": 1.2, "max_drawdown_pct": 12.0},
        )
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
        expected_sheets = {
            "Portfolio_Holdings",
            "ETF_LookThrough",
            "Equities_Forensic_Valuation",
            "Crypto_OnChain_Tokenomics",
            "Transactions_Ledger",
        }
        self.assertTrue(expected_sheets.issubset(set(wb.sheetnames)))
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

            notif_payload = BackgroundNotifierEngine().build_morning_briefing_payload(
                macro=self.macro,
                portfolio=self.portfolio,
                equities=self.equities,
                cryptos=self.cryptos,
                micro_events=self.geo.get_micro_events(prefer_ai_cache=False),
                risk_timing=self.risk_timing,
                use_ai=True,
            )
            self.assertFalse(notif_payload["ai_enhanced"])

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


if __name__ == "__main__":
    unittest.main()

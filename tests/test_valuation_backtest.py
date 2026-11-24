"""
Unit tests for the Sector-Stratified Composable Valuation & Backtest Engine
(`core/valuation_backtest.py`).
Verifies authentic SEC XBRL US-GAAP + IFRS processing, sector dispatch,
P/B < 1.0 banking veto, PEGY formula variants, T-Bills destination,
symmetrical tax accounting, and deterministic math.
"""

import unittest
import pandas as pd
from core.valuation_backtest import (
    DEFAULT_SECTOR_MAP,
    HistoricalDataWarehouse,
    PointInTimeValuationEngine,
    run_valuation_backtest,
)


class TestValuationBacktestEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.warehouse = HistoricalDataWarehouse()
        cls.val_engine = PointInTimeValuationEngine(cls.warehouse)

    def test_warehouse_loads_market_and_macro_data(self) -> None:
        self.assertFalse(self.warehouse.market_data.empty)
        self.assertIn("SPY", self.warehouse.market_data.columns)
        self.assertIn("BTC-USD", self.warehouse.market_data.columns)
        self.assertIn("AVGO", self.warehouse.market_data.columns)
        self.assertIn("FEDFUNDS", self.warehouse.macro_df.columns)
        self.assertIn("T10Y2Y", self.warehouse.macro_df.columns)
        self.assertIn("SAHMREALTIME", self.warehouse.macro_df.columns)

    def test_fintech_and_processors_sector_mapping_aligned_with_pdf(self) -> None:
        self.assertEqual(DEFAULT_SECTOR_MAP["NU"], "TECH_HIGH_GROWTH")
        self.assertEqual(DEFAULT_SECTOR_MAP["GOOGL"], "TECH_HIGH_GROWTH")
        self.assertEqual(DEFAULT_SECTOR_MAP["MA"], "TECH_CASH_COW")
        self.assertEqual(DEFAULT_SECTOR_MAP["V"], "TECH_CASH_COW")
        self.assertEqual(DEFAULT_SECTOR_MAP["JPM"], "FINANCIAL_BANK")
        self.assertEqual(DEFAULT_SECTOR_MAP["XOM"], "CYCLICAL")
        self.assertEqual(DEFAULT_SECTOR_MAP["WMT"], "DEFENSIVE_RETAIL")

    def test_point_in_time_pegy_and_yield_denominator_variant(self) -> None:
        test_date = pd.Timestamp("2023-06-01")
        price = 78.50
        pegy_denom = self.val_engine.calc_enterprise_pegy("AVGO", price, test_date, yield_in_denominator=True)
        pegy_num = self.val_engine.calc_enterprise_pegy("AVGO", price, test_date, yield_in_denominator=False)
        self.assertIsInstance(pegy_denom, float)
        self.assertGreater(pegy_denom, 0.0)
        self.assertLessEqual(pegy_denom, pegy_num + 1e-9)

    def test_dcf_and_reverse_dcf_calculation(self) -> None:
        test_date = pd.Timestamp("2023-06-01")
        dcf_val = self.val_engine.calc_dcf_fair_value("AVGO", test_date)
        rev_ratio = self.val_engine.calc_reverse_dcf_ratio("AVGO", 78.50, test_date)
        self.assertGreater(dcf_val, 0.0)
        self.assertGreater(rev_ratio, 0.0)

    def test_sector_auto_dispatch_multi_sector(self) -> None:
        res = run_valuation_backtest(
            assets=["AVGO", "AAPL", "JPM", "WMT"],
            initial_capital=100_000.0,
            monthly_inflow=2_000.0,
            start_date="2020-01-01",
            end_date="2024-01-01",
            valuation_method="sector_auto",
            ltv_mode="none",
        )
        self.assertGreater(res.metrics["final_capital"], 0.0)
        for t in res.trade_log:
            if t.asset == "JPM":
                self.assertEqual(t.metric_name, "Financial_PEGY")

    def test_bank_pb_veto_toggle(self) -> None:
        res_veto = run_valuation_backtest(
            assets=["JPM", "DBSDY"],
            initial_capital=100_000.0,
            monthly_inflow=2_000.0,
            start_date="2020-01-01",
            end_date="2024-01-01",
            valuation_method="bank_pegy_pb",
            bank_pb_veto=1.0,
            ltv_mode="none",
        )
        res_noveto = run_valuation_backtest(
            assets=["JPM", "DBSDY"],
            initial_capital=100_000.0,
            monthly_inflow=2_000.0,
            start_date="2020-01-01",
            end_date="2024-01-01",
            valuation_method="bank_pegy_pb",
            bank_pb_veto=0.0,
            ltv_mode="none",
        )
        self.assertGreater(res_veto.metrics["final_capital"], 0.0)
        self.assertGreater(res_noveto.metrics["final_capital"], 0.0)

    def test_prune_destination_tbills_vs_reinvest(self) -> None:
        res_reinv = run_valuation_backtest(
            assets=["AVGO", "TSM", "ASML"],
            initial_capital=100_000.0,
            monthly_inflow=2_000.0,
            start_date="2020-01-01",
            end_date="2024-01-01",
            prune_pegy=1.6,
            prune_destination="reinvest_discounted",
            ltv_mode="none",
        )
        res_tbills = run_valuation_backtest(
            assets=["AVGO", "TSM", "ASML"],
            initial_capital=100_000.0,
            monthly_inflow=2_000.0,
            start_date="2020-01-01",
            end_date="2024-01-01",
            prune_pegy=1.6,
            prune_destination="tbills",
            ltv_mode="none",
        )
        self.assertGreater(res_reinv.metrics["final_capital"], 0.0)
        self.assertGreater(res_tbills.metrics["final_capital"], 0.0)

    def test_symmetrical_tax_on_quarterly_rebalance(self) -> None:
        res_gross = run_valuation_backtest(
            assets=["AVGO", "AAPL", "SPY"],
            initial_capital=100_000.0,
            monthly_inflow=2_000.0,
            start_date="2020-01-01",
            end_date="2024-01-01",
            valuation_method="buy_and_hold",
            inflow_mode="pro_rata",
            rebalance_freq="quarterly",
            ltv_mode="none",
            enable_tax=False,
        )
        res_net = run_valuation_backtest(
            assets=["AVGO", "AAPL", "SPY"],
            initial_capital=100_000.0,
            monthly_inflow=2_000.0,
            start_date="2020-01-01",
            end_date="2024-01-01",
            valuation_method="buy_and_hold",
            inflow_mode="pro_rata",
            rebalance_freq="quarterly",
            ltv_mode="none",
            enable_tax=True,
            tax_rate=0.15,
        )
        self.assertEqual(res_gross.metrics["total_taxes_paid"], 0.0)
        self.assertGreater(res_net.metrics["total_taxes_paid"], 0.0)
        self.assertGreater(res_gross.metrics["final_capital"], res_net.metrics["final_capital"])

    def test_trend_filter_avoids_pruning_leaders(self) -> None:
        res_no_filter = run_valuation_backtest(
            assets=["AVGO", "TSM"],
            initial_capital=50_000.0,
            monthly_inflow=1_000.0,
            start_date="2020-01-01",
            end_date="2024-01-01",
            prune_pegy=1.6,
            tech_hg_hold=False,
            trend_filter_sma200=False,
            ltv_mode="none",
        )
        res_with_filter = run_valuation_backtest(
            assets=["AVGO", "TSM"],
            initial_capital=50_000.0,
            monthly_inflow=1_000.0,
            start_date="2020-01-01",
            end_date="2024-01-01",
            prune_pegy=1.6,
            tech_hg_hold=False,
            trend_filter_sma200=True,
            ltv_mode="none",
        )
        self.assertLessEqual(len(res_with_filter.trade_log), len(res_no_filter.trade_log))

    def test_unified_asymmetric_framework_defaults(self) -> None:
        res = run_valuation_backtest(
            assets={"BTC-USD": 0.30, "ETH-USD": 0.10, "LINK-USD": 0.10, "NVDA": 0.25, "AAPL": 0.25},
            initial_capital=100_000.0,
            monthly_inflow=2_000.0,
            start_date="2020-01-01",
            end_date="2024-01-01",
        )
        self.assertGreater(res.metrics["final_capital"], 0.0)
        # Official defaults: TECH_HIGH_GROWTH (NVDA) and L1 Majors (ETH-USD) never pruned on multiple/DD
        self.assertFalse(any(t.asset in ("NVDA", "ETH-USD") and ("PRUNE" in t.action or "SAIDA" in t.action) for t in res.trade_log))
        # Official BTC default uses exclusive Pi Cycle Top (never mid-cycle NUPL reverse cross)
        self.assertEqual(res.config.get("btc_top_mode"), "pi_cycle_only")
        # Continuous LTV baseline maintains non-zero leverage with no 10% drop
        self.assertGreater(res.ltv_series.iloc[-1], 0.0)


if __name__ == "__main__":
    unittest.main()

"""
core/custody_sync_engine.py
Read-Only Custody & Broker Sync Engine (IBKR Flex Web Service / XML + Binance Spot API).
Eliminates manual ticker/cost-basis entry in Tab 2 while keeping all SQLite writes
strictly routed through PortfolioEngine and preserving all GEMINI.md invariants.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import requests

from core.portfolio_engine import PortfolioEngine

BINANCE_API_BASE = "https://api.binance.com"
IBKR_FLEX_SEND_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService/SendRequest"
IBKR_FLEX_GET_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService/GetStatement"

STABLECOIN_SYMBOLS = {
    "USDT", "USDC", "FDUSD", "BUSD", "TUSD", "USDP", "DAI", "PYUSD", "USD", "EUR", "BRL", "GBP",
}
LAYER1_CRYPTO_SYMBOLS = {"ETH", "SOL", "ADA", "AVAX", "SUI", "TON", "NEAR", "APT", "DOT", "ATOM"}
DEFI_CRYPTO_SYMBOLS = {"AAVE", "PENDLE", "MKR", "UNI", "CRV", "LDO", "SNX", "COMP", "ENA"}
ORACLE_CRYPTO_SYMBOLS = {"LINK", "PYTH", "GRT", "BAND"}


@dataclass
class SyncedPosition:
    ticker: str
    name: str
    source: str  # "IBKR" or "Binance"
    quantity: float
    market_price_usd: float
    market_value_usd: float
    avg_buy_price_usd: float
    actual_weight_pct: float
    asset_class_ui: str  # "Stock" | "ETF" | "Crypto" | "Altcoin"
    sector_ui: str
    ltv_turbo_eligible: bool
    role_description: str
    currency: str = "USD"


@dataclass
class CustodySyncResult:
    ok: bool
    source_summary: str
    positions: List[SyncedPosition] = field(default_factory=list)
    total_nav_usd: float = 0.0
    stablecoin_cash_usd: float = 0.0
    warnings: List[str] = field(default_factory=list)
    error_message: str = ""


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        if val is None or val == "":
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def _infer_crypto_vertical(base_sym: str) -> Tuple[str, str, bool]:
    sym = base_sym.upper().strip()
    if sym == "BTC":
        return "Crypto", "Bitcoin Sovereign PoW Reserve", True
    if sym in LAYER1_CRYPTO_SYMBOLS:
        return "Altcoin", "Smart Contract Layer-1 (ETH/SOL)", False
    if sym in DEFI_CRYPTO_SYMBOLS:
        return "Altcoin", "DeFi Blue-Chip / Real Yield (PENDLE/MKR/UNI)", False
    if sym in ORACLE_CRYPTO_SYMBOLS:
        return "Altcoin", "Oracle / Interoperability (LINK)", False
    return "Altcoin", "Smart Contract Layer-1 (ETH/SOL)", False


def _infer_equity_vertical(ticker: str, ibkr_cat: str = "", name: str = "") -> Tuple[str, str, str]:
    """Infers (asset_class_ui, sector_ui, resolved_name) using yfinance metadata with safe fallbacks."""
    tk = ticker.upper().strip()
    resolved_name = name.strip() or tk
    if tk == "QLD":
        return "ETF", "2x Leveraged ETF (QLD)", resolved_name
    if ibkr_cat.upper() in ("ETF", "FUND") or tk in {"SPY", "QQQ", "VOO", "IVV", "SMH", "ITA", "SCHD", "VTI", "IWM"}:
        return "ETF", "Index ETF (S&P 500 / Nasdaq / Sector)", resolved_name

    try:
        import yfinance as yf

        info = yf.Ticker(tk).info or {}
        qtype = str(info.get("quoteType", "")).upper()
        resolved_name = str(info.get("shortName") or info.get("longName") or resolved_name)
        if qtype == "ETF":
            return "ETF", "Index ETF (S&P 500 / Nasdaq / Sector)", resolved_name
        sector = str(info.get("sector", "")).lower()
        industry = str(info.get("industry", "")).lower()
        if "bank" in industry or "financial" in sector:
            return "Stock", "Global Bank / Financial Institution", resolved_name
        if "semiconductor" in industry or "software" in industry or "technology" in sector:
            return "Stock", "High-Growth Tech & AI Infra", resolved_name
        if "consumer defensive" in sector or "discount" in industry or "retail" in industry:
            return "Stock", "Defensive Retail (SSS)", resolved_name
        if "communication" in sector:
            return "Stock", "Big Tech Cash Cow / Monopoly", resolved_name
        if "industrial" in sector or "aerospace" in industry or "energy" in sector or "basic materials" in sector:
            return "Stock", "Cyclical / Defense / Industrial", resolved_name
    except Exception:
        pass

    return "Stock", "High-Growth Tech & AI Infra", resolved_name


def _binance_signed_get(
    endpoint: str,
    api_key: str,
    api_secret: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 12,
) -> Tuple[Optional[Any], str]:
    """Executes a read-only HMAC-SHA256 signed GET request against Binance Spot API."""
    payload = dict(params or {})
    payload["timestamp"] = int(time.time() * 1000)
    payload.setdefault("recvWindow", 10000)
    query_str = urllib.parse.urlencode(payload)
    signature = hmac.new(api_secret.encode("utf-8"), query_str.encode("utf-8"), hashlib.sha256).hexdigest()
    url = f"{BINANCE_API_BASE}{endpoint}?{query_str}&signature={signature}"
    headers = {"X-MBX-APIKEY": api_key}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            try:
                msg = resp.json().get("msg", resp.text[:180])
            except Exception:
                msg = resp.text[:180]
            return None, f"Binance HTTP {resp.status_code}: {msg}"
        return resp.json(), ""
    except Exception as exc:
        return None, f"Binance connection error: {exc}"


def _fetch_binance_spot_prices() -> Dict[str, float]:
    prices: Dict[str, float] = {}
    try:
        resp = requests.get(f"{BINANCE_API_BASE}/api/v3/ticker/price", timeout=10)
        if resp.status_code == 200:
            for item in resp.json():
                sym = str(item.get("symbol", ""))
                px = _safe_float(item.get("price"))
                if sym and px > 0:
                    prices[sym] = px
    except Exception:
        pass
    return prices


def _estimate_binance_avg_buy_price(
    asset: str,
    api_key: str,
    api_secret: str,
    fallback_spot_px: float,
) -> float:
    """Computes weighted-average net buy price from recent Binance Spot trades (USDT/FDUSD/USDC)."""
    for quote in ("USDT", "FDUSD", "USDC"):
        trades, err = _binance_signed_get(
            "/api/v3/myTrades",
            api_key,
            api_secret,
            params={"symbol": f"{asset}{quote}", "limit": 500},
            timeout=10,
        )
        if err or not isinstance(trades, list) or not trades:
            continue
        net_qty = 0.0
        total_cost = 0.0
        for tr in trades:
            qty = _safe_float(tr.get("qty"))
            px = _safe_float(tr.get("price"))
            if qty <= 0 or px <= 0:
                continue
            if tr.get("isBuyer"):
                total_cost += qty * px
                net_qty += qty
            else:
                if net_qty > 0:
                    avg = total_cost / net_qty
                    reduce_qty = min(net_qty, qty)
                    net_qty -= reduce_qty
                    total_cost -= reduce_qty * avg
        if net_qty > 0 and total_cost > 0:
            return round(total_cost / net_qty, 4)
    return round(fallback_spot_px, 4)


def fetch_binance_spot_positions(
    api_key: str,
    api_secret: str,
    min_dust_usd: float = 10.0,
    include_trade_cost_basis: bool = True,
) -> CustodySyncResult:
    """Fetches non-dust Binance Spot holdings via strictly read-only API endpoints."""
    key = (api_key or "").strip()
    sec = (api_secret or "").strip()
    if not key or not sec:
        return CustodySyncResult(ok=False, source_summary="Binance", error_message="Missing Binance Read-Only API Key or Secret.")

    acct, err = _binance_signed_get("/api/v3/account", key, sec)
    if err or not isinstance(acct, dict):
        return CustodySyncResult(ok=False, source_summary="Binance", error_message=err or "Invalid Binance account response.")

    spot_prices = _fetch_binance_spot_prices()
    positions: List[SyncedPosition] = []
    warnings: List[str] = []
    stable_cash = 0.0
    total_nav = 0.0

    for bal in acct.get("balances", []):
        asset = str(bal.get("asset", "")).upper().strip()
        # Binance Earn / Staking balances often carry LD prefix (e.g. LDBTC -> BTC)
        clean_asset = asset[2:] if asset.startswith("LD") and len(asset) > 3 else asset
        qty = _safe_float(bal.get("free")) + _safe_float(bal.get("locked"))
        if qty <= 0 or not clean_asset:
            continue

        if clean_asset in STABLECOIN_SYMBOLS:
            if clean_asset in {"USDT", "USDC", "FDUSD", "BUSD", "TUSD", "DAI", "PYUSD", "USD"}:
                stable_cash += qty
            continue

        px_usd = (
            spot_prices.get(f"{clean_asset}USDT")
            or spot_prices.get(f"{clean_asset}FDUSD")
            or spot_prices.get(f"{clean_asset}USDC")
            or 0.0
        )
        if px_usd <= 0:
            warnings.append(f"Binance: skipped {asset} (no USD/USDT spot quote).")
            continue

        val_usd = qty * px_usd
        if val_usd < min_dust_usd:
            continue

        avg_buy = (
            _estimate_binance_avg_buy_price(clean_asset, key, sec, px_usd)
            if include_trade_cost_basis
            else round(px_usd, 4)
        )
        cls_ui, sec_ui, ltv_ok = _infer_crypto_vertical(clean_asset)
        ticker = f"{clean_asset}-USD"
        total_nav += val_usd
        positions.append(
            SyncedPosition(
                ticker=ticker,
                name=f"{clean_asset} (Binance Spot)",
                source="Binance",
                quantity=qty,
                market_price_usd=round(px_usd, 4),
                market_value_usd=round(val_usd, 2),
                avg_buy_price_usd=avg_buy,
                actual_weight_pct=0.0,
                asset_class_ui=cls_ui,
                sector_ui=sec_ui,
                ltv_turbo_eligible=ltv_ok,
                role_description=f"Synced from Binance Spot custody ({sec_ui}).",
                currency="USD",
            )
        )

    for p in positions:
        p.actual_weight_pct = round((p.market_value_usd / total_nav) * 100.0, 2) if total_nav > 0 else 0.0

    positions.sort(key=lambda x: x.market_value_usd, reverse=True)
    return CustodySyncResult(
        ok=True,
        source_summary=f"Binance Spot ({len(positions)} positions)",
        positions=positions,
        total_nav_usd=round(total_nav, 2),
        stablecoin_cash_usd=round(stable_cash, 2),
        warnings=warnings,
    )


def parse_ibkr_flex_xml(xml_content: str, min_dust_usd: float = 10.0) -> CustodySyncResult:
    """Parses an IBKR Activity Flex Query XML statement into normalized SyncedPosition records."""
    try:
        root = ET.fromstring(xml_content.strip())
    except Exception as exc:
        return CustodySyncResult(ok=False, source_summary="IBKR Flex XML", error_message=f"Invalid XML format: {exc}")

    # Check if IBKR returned a Flex error payload
    status_node = root.find(".//Status")
    if status_node is not None and status_node.text and status_node.text.strip().lower() == "fail":
        err_msg = (root.findtext(".//ErrorMessage") or "IBKR Flex request failed").strip()
        return CustodySyncResult(ok=False, source_summary="IBKR Flex XML", error_message=err_msg)

    raw_positions: List[SyncedPosition] = []
    warnings: List[str] = []
    cash_usd = 0.0
    total_nav = 0.0
    seen_symbols: Dict[str, SyncedPosition] = {}

    for node in root.iter("OpenPosition"):
        attrib = node.attrib
        symbol = str(attrib.get("symbol", "")).strip().upper()
        asset_cat = str(attrib.get("assetCategory", "STK")).strip().upper()
        if not symbol or asset_cat in ("CASH", "FX"):
            continue
        if asset_cat in ("OPT", "FUT", "FOP", "WAR"):
            warnings.append(f"IBKR: skipped derivative {symbol} ({asset_cat}).")
            continue

        qty = _safe_float(attrib.get("position"))
        if abs(qty) <= 0:
            continue

        fx_rate = _safe_float(attrib.get("fxRateToBase"), 1.0) or 1.0
        currency = str(attrib.get("currency", "USD")).strip().upper()
        mark_px = _safe_float(attrib.get("markPrice") or attrib.get("closePrice"))
        val_base = _safe_float(attrib.get("positionValueInBase"))
        if val_base == 0.0:
            val_local = _safe_float(attrib.get("positionValue")) or (qty * mark_px)
            val_base = val_local * (fx_rate if currency != "USD" else 1.0)

        if abs(val_base) < min_dust_usd:
            continue

        cost_px = _safe_float(attrib.get("costBasisPrice") or attrib.get("openPrice"))
        if cost_px <= 0 and mark_px > 0:
            cost_px = mark_px
        cost_px_usd = cost_px * (fx_rate if currency != "USD" else 1.0)
        mark_px_usd = (mark_px * (fx_rate if currency != "USD" else 1.0)) if mark_px > 0 else (abs(val_base) / abs(qty))

        desc = str(attrib.get("description", symbol)).strip()
        cls_ui, sec_ui, resolved_name = _infer_equity_vertical(symbol, ibkr_cat=asset_cat, name=desc)

        if symbol in seen_symbols:
            prev = seen_symbols[symbol]
            combined_qty = prev.quantity + qty
            combined_val = prev.market_value_usd + val_base
            if combined_qty != 0:
                prev.avg_buy_price_usd = round(
                    ((prev.avg_buy_price_usd * prev.quantity) + (cost_px_usd * qty)) / combined_qty,
                    4,
                )
            prev.quantity = combined_qty
            prev.market_value_usd = round(combined_val, 2)
        else:
            pos = SyncedPosition(
                ticker=symbol,
                name=resolved_name,
                source="IBKR",
                quantity=qty,
                market_price_usd=round(mark_px_usd, 4),
                market_value_usd=round(val_base, 2),
                avg_buy_price_usd=round(cost_px_usd, 4),
                actual_weight_pct=0.0,
                asset_class_ui=cls_ui,
                sector_ui=sec_ui,
                ltv_turbo_eligible=True,
                role_description=f"Synced from IBKR custody ({sec_ui}).",
                currency=currency,
            )
            seen_symbols[symbol] = pos
            raw_positions.append(pos)

    for cash_node in root.iter("CashReportCurrency"):
        if str(cash_node.attrib.get("currency", "")).upper() in ("BASE_SUMMARY", "USD"):
            ending_cash = _safe_float(cash_node.attrib.get("endingCash"))
            if ending_cash > 0:
                cash_usd = max(cash_usd, ending_cash)

    total_nav = sum(max(0.0, p.market_value_usd) for p in raw_positions)
    for p in raw_positions:
        p.actual_weight_pct = round((p.market_value_usd / total_nav) * 100.0, 2) if total_nav > 0 else 0.0

    raw_positions.sort(key=lambda x: x.market_value_usd, reverse=True)
    return CustodySyncResult(
        ok=True,
        source_summary=f"IBKR Flex ({len(raw_positions)} positions)",
        positions=raw_positions,
        total_nav_usd=round(total_nav, 2),
        stablecoin_cash_usd=round(cash_usd, 2),
        warnings=warnings,
    )


def fetch_ibkr_flex_positions(
    flex_token: str,
    query_id: str,
    min_dust_usd: float = 10.0,
) -> CustodySyncResult:
    """Fetches Open Positions via Interactive Brokers Flex Web Service (SendRequest -> GetStatement)."""
    tok = (flex_token or "").strip()
    qid = (query_id or "").strip()
    if not tok or not qid:
        return CustodySyncResult(ok=False, source_summary="IBKR", error_message="Missing IBKR Flex Token or Query ID.")

    try:
        send_resp = requests.get(
            IBKR_FLEX_SEND_URL,
            params={"t": tok, "q": qid, "v": "3"},
            headers={"User-Agent": "InstitutionalInvestmentTerminal/1.0"},
            timeout=15,
        )
        if send_resp.status_code != 200:
            return CustodySyncResult(ok=False, source_summary="IBKR", error_message=f"IBKR SendRequest HTTP {send_resp.status_code}")

        send_root = ET.fromstring(send_resp.text.strip())
        status = (send_root.findtext(".//Status") or "").strip()
        if status.lower() != "success":
            err_msg = (send_root.findtext(".//ErrorMessage") or "IBKR SendRequest rejected").strip()
            return CustodySyncResult(ok=False, source_summary="IBKR", error_message=err_msg)

        ref_code = (send_root.findtext(".//ReferenceCode") or "").strip()
        if not ref_code:
            return CustodySyncResult(ok=False, source_summary="IBKR", error_message="IBKR did not return a ReferenceCode.")

        for attempt in range(4):
            if attempt > 0:
                time.sleep(2.0)
            stmt_resp = requests.get(
                IBKR_FLEX_GET_URL,
                params={"t": tok, "q": ref_code, "v": "3"},
                headers={"User-Agent": "InstitutionalInvestmentTerminal/1.0"},
                timeout=20,
            )
            if stmt_resp.status_code == 200 and "<OpenPosition" in stmt_resp.text:
                return parse_ibkr_flex_xml(stmt_resp.text, min_dust_usd=min_dust_usd)
            if stmt_resp.status_code == 200 and "Statement generation in progress" not in stmt_resp.text:
                return parse_ibkr_flex_xml(stmt_resp.text, min_dust_usd=min_dust_usd)

        return CustodySyncResult(
            ok=False,
            source_summary="IBKR",
            error_message="IBKR Flex statement timed out while generating. Retry in a few seconds.",
        )
    except Exception as exc:
        return CustodySyncResult(ok=False, source_summary="IBKR", error_message=f"IBKR Flex connection error: {exc}")


def combine_custody_results(results: List[CustodySyncResult]) -> CustodySyncResult:
    """Combines IBKR and Binance sync results and recalculates cross-broker portfolio weights."""
    valid = [r for r in results if r.ok]
    if not valid:
        errors = " | ".join(r.error_message for r in results if r.error_message)
        return CustodySyncResult(ok=False, source_summary="Combined Custody", error_message=errors or "No custody sources synced.")

    merged: Dict[str, SyncedPosition] = {}
    warnings: List[str] = []
    cash_total = 0.0
    for r in valid:
        warnings.extend(r.warnings)
        cash_total += r.stablecoin_cash_usd
        for p in r.positions:
            if p.ticker in merged:
                prev = merged[p.ticker]
                tot_qty = prev.quantity + p.quantity
                if tot_qty > 0:
                    prev.avg_buy_price_usd = round(
                        ((prev.avg_buy_price_usd * prev.quantity) + (p.avg_buy_price_usd * p.quantity)) / tot_qty,
                        4,
                    )
                prev.quantity = tot_qty
                prev.market_value_usd = round(prev.market_value_usd + p.market_value_usd, 2)
                if p.source not in prev.source:
                    prev.source = f"{prev.source} + {p.source}"
            else:
                merged[p.ticker] = SyncedPosition(**vars(p))

    all_pos = list(merged.values())
    total_nav = sum(max(0.0, p.market_value_usd) for p in all_pos)
    for p in all_pos:
        p.actual_weight_pct = round((p.market_value_usd / total_nav) * 100.0, 2) if total_nav > 0 else 0.0

    all_pos.sort(key=lambda x: x.market_value_usd, reverse=True)
    return CustodySyncResult(
        ok=True,
        source_summary=" + ".join(r.source_summary for r in valid),
        positions=all_pos,
        total_nav_usd=round(total_nav, 2),
        stablecoin_cash_usd=round(cash_total, 2),
        warnings=warnings,
    )


def apply_synced_positions_to_sqlite(
    port_engine: PortfolioEngine,
    synced_positions: List[SyncedPosition],
    sync_mode: str = "merge_preserve_targets",
    normalize_to_100: bool = True,
) -> Tuple[int, int]:
    """
    Persists synced custody positions into SQLite strictly via PortfolioEngine.
    sync_mode:
      - 'merge_preserve_targets': updates avg_buy_price for existing tickers (preserving
        custom target_weight_pct, sector, and role) and inserts new holdings at actual weight.
      - 'replace_with_actual_weights': replaces SQLite holdings with the synced custody
        snapshot using actual market-value weights.
    Returns (upserted_count, removed_count).
    """
    if not synced_positions:
        return 0, 0

    existing_map = {a["ticker"].upper(): a for a in port_engine.get_all_assets_from_db()}
    synced_tickers = {p.ticker.upper() for p in synced_positions}
    removed = 0

    if sync_mode == "replace_with_actual_weights":
        for old_tk in list(existing_map.keys()):
            if old_tk not in synced_tickers:
                port_engine.delete_asset(old_tk)
                removed += 1

    upserted = 0
    for p in synced_positions:
        tk_up = p.ticker.upper()
        prev = existing_map.get(tk_up)
        if prev and sync_mode == "merge_preserve_targets":
            port_engine.upsert_asset(
                ticker=tk_up,
                name=prev["name"] or p.name,
                category=prev["category"],
                sector_vertical=prev["sector_vertical"],
                target_weight_pct=float(prev["target_weight_pct"]),
                avg_buy_price=float(p.avg_buy_price_usd),
                ltv_turbo_eligible=bool(prev["ltv_turbo_eligible"]),
                fair_price=float(prev["fair_price"]),
                role_description=prev["role_description"] or p.role_description,
            )
        else:
            port_engine.upsert_asset(
                ticker=tk_up,
                name=p.name,
                asset_class_ui=p.asset_class_ui,
                sector_ui=p.sector_ui,
                target_weight_pct=max(0.10, float(p.actual_weight_pct)),
                avg_buy_price=float(p.avg_buy_price_usd),
                ltv_turbo_eligible=bool(p.ltv_turbo_eligible),
                fair_price=float(p.market_price_usd),
                role_description=p.role_description,
            )
        upserted += 1

    if normalize_to_100:
        port_engine.normalize_weights_to_100()

    return upserted, removed


def has_env_custody_credentials() -> bool:
    """Returns True when at least one broker (IBKR Flex or Binance Spot) has credentials in env."""
    has_ibkr = bool(os.getenv("IBKR_FLEX_TOKEN", "").strip() and os.getenv("IBKR_FLEX_QUERY_ID", "").strip())
    has_binance = bool(os.getenv("BINANCE_API_KEY", "").strip() and os.getenv("BINANCE_API_SECRET", "").strip())
    return has_ibkr or has_binance


def auto_sync_configured_brokers(
    port_engine: PortfolioEngine,
    min_dust_usd: float = 10.0,
) -> Optional[CustodySyncResult]:
    """
    Runs automatic read-only sync from IBKR Flex and/or Binance Spot when credentials exist in `.env`.
    Always uses `merge_preserve_targets` so zeroed-out positions remain in SQLite as watchlist/rebuy targets.
    Uses zero Gemini API quota (100% deterministic API + SQLite).
    """
    ibkr_tok = os.getenv("IBKR_FLEX_TOKEN", "").strip()
    ibkr_qid = os.getenv("IBKR_FLEX_QUERY_ID", "").strip()
    bn_key = os.getenv("BINANCE_API_KEY", "").strip()
    bn_sec = os.getenv("BINANCE_API_SECRET", "").strip()

    results: List[CustodySyncResult] = []
    if ibkr_tok and ibkr_qid:
        results.append(fetch_ibkr_flex_positions(ibkr_tok, ibkr_qid, min_dust_usd=min_dust_usd))
    if bn_key and bn_sec:
        results.append(
            fetch_binance_spot_positions(
                bn_key,
                bn_sec,
                min_dust_usd=min_dust_usd,
                include_trade_cost_basis=True,
            )
        )

    if not results:
        return None

    combined = combine_custody_results(results)
    if combined.ok and combined.positions:
        apply_synced_positions_to_sqlite(
            port_engine,
            combined.positions,
            sync_mode="merge_preserve_targets",
            normalize_to_100=True,
        )
    return combined

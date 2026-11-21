"""
READ-ONLY AUTOMATIC CUSTODY SYNCHRONIZATION CONNECTORS
- 100% read-only brokerage & on-chain ingestion (zero trade execution, zero private keys).
- Connectors:
  1. Interactive Brokers (IBKR) Flex Query XML parser + Flex Web Service client.
  2. Binance Read-Only Spot API (HMAC-SHA256 signed account balances & myTrades).
  3. Public On-Chain Wallet Balances:
     - Bitcoin public addresses via Blockstream / Mempool REST APIs.
     - EVM public addresses (`0x...`) via public JSON-RPC (`eth_getBalance` + ERC-20 `balanceOf`).
- Dynamic Asset Handling: Never restricts or hardcodes a fixed crypto allowlist; any held asset
  discovered in IBKR, Binance, or custom ERC-20 tokens is mapped dynamically.
- Security Hygiene: API keys/secrets live strictly in `.env` or transient UI inputs and are NEVER
  written to SQLite, `custody_sync_config.json`, logs, or exceptions.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import os
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

import requests

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CUSTODY_CONFIG_PATH = os.path.join(ROOT_DIR, "custody_sync_config.json")

_USD_STABLECOINS = {"USD", "USDT", "USDC", "FDUSD", "BUSD", "TUSD", "USDP", "DAI"}
_REF_PATTERN = re.compile(r"\[ref:([^\]]+)\]")
_EVM_ADDR_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")
_BTC_ENDPOINTS = (
    "https://blockstream.info/api/address/{address}",
    "https://mempool.space/api/address/{address}",
)
_EVM_RPC_ENDPOINTS = (
    "https://eth.llamarpc.com",
    "https://cloudflare-eth.com",
    "https://ethereum-rpc.publicnode.com",
)
_IBKR_FLEX_SEND_URL = "https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest"
_IBKR_FLEX_GET_URL = "https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement"


def load_custody_sync_config(path: str = DEFAULT_CUSTODY_CONFIG_PATH) -> Dict[str, Any]:
    """Loads non-secret public wallet sync configuration from local gitignored JSON."""
    default_cfg: Dict[str, Any] = {
        "btc_address": "",
        "evm_address": "",
        "erc20_tokens": [],
        "last_sync_utc": "",
    }
    if not os.path.exists(path):
        return default_cfg
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            return default_cfg
        return {
            "btc_address": str(raw.get("btc_address") or "").strip(),
            "evm_address": str(raw.get("evm_address") or "").strip(),
            "erc20_tokens": [
                {
                    "symbol": str(t.get("symbol") or "").strip().upper(),
                    "contract": str(t.get("contract") or "").strip(),
                    "decimals": int(t.get("decimals", 18)),
                }
                for t in (raw.get("erc20_tokens") or [])
                if isinstance(t, dict) and t.get("symbol") and t.get("contract")
            ],
            "last_sync_utc": str(raw.get("last_sync_utc") or "").strip(),
        }
    except Exception:
        return default_cfg


def save_custody_sync_config(cfg: Dict[str, Any], path: str = DEFAULT_CUSTODY_CONFIG_PATH) -> None:
    """Persists ONLY non-secret public addresses and token contract metadata."""
    clean_payload = {
        "btc_address": str(cfg.get("btc_address") or "").strip(),
        "evm_address": str(cfg.get("evm_address") or "").strip(),
        "erc20_tokens": [
            {
                "symbol": str(t.get("symbol") or "").strip().upper(),
                "contract": str(t.get("contract") or "").strip(),
                "decimals": int(t.get("decimals", 18)),
            }
            for t in (cfg.get("erc20_tokens") or [])
            if isinstance(t, dict) and t.get("symbol") and t.get("contract")
        ],
        "last_sync_utc": str(cfg.get("last_sync_utc") or "").strip(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean_payload, f, indent=2, ensure_ascii=False)


def get_custody_env_credentials() -> Dict[str, str]:
    """Reads optional read-only brokerage credentials from `.env` / environment."""
    try:
        from core.gemini_client import _load_env_safely

        _load_env_safely()
    except Exception:
        pass

    return {
        "ibkr_flex_token": (os.getenv("IBKR_FLEX_TOKEN") or "").strip(),
        "ibkr_flex_query_id": (os.getenv("IBKR_FLEX_QUERY_ID") or "").strip(),
        "binance_api_key": (os.getenv("BINANCE_API_KEY") or "").strip(),
        "binance_api_secret": (os.getenv("BINANCE_API_SECRET") or "").strip(),
    }


def parse_erc20_spec_lines(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses multi-line custom ERC-20 definitions of the form `SYMBOL:0xCONTRACT:DECIMALS`
    (decimals optional, default 18). Enables any dynamic token without static hardcoding.
    """
    tokens: List[Dict[str, Any]] = []
    for raw_line in (raw_text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.replace(",", ":").split(":") if p.strip()]
        if len(parts) < 2:
            continue
        symbol = parts[0].upper()
        contract = parts[1]
        if not _EVM_ADDR_PATTERN.match(contract):
            continue
        decimals = 18
        if len(parts) >= 3:
            try:
                decimals = max(0, min(36, int(parts[2])))
            except ValueError:
                decimals = 18
        tokens.append({"symbol": symbol, "contract": contract, "decimals": decimals})
    return tokens


def _normalize_flex_date(raw_dt: str) -> str:
    txt = (raw_dt or "").strip()
    if not txt:
        return datetime.date.today().isoformat()
    date_part = txt.split(";")[0].split("T")[0].split(" ")[0].strip()
    if re.match(r"^\d{8}$", date_part):
        return f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]}"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_part):
        return date_part
    digits = re.sub(r"[^0-9]", "", date_part)
    if len(digits) >= 8:
        return f"{digits[0:4]}-{digits[4:6]}-{digits[6:8]}"
    return datetime.date.today().isoformat()


def _normalize_ibkr_ticker(symbol: str, asset_category: str = "") -> str:
    tk = re.sub(r"\s+", "-", (symbol or "").strip().upper())
    if not tk:
        return ""
    if asset_category.upper() == "CRYPTO" and "-USD" not in tk:
        return f"{tk}-USD"
    return tk


def parse_ibkr_flex_xml(xml_bytes: bytes) -> Dict[str, Any]:
    """
    Parses an Interactive Brokers Flex Query XML payload (Trades, TradeConfirms,
    CashTransactions Dividends, and OpenPositions) into normalized read-only records.
    """
    if not xml_bytes or not xml_bytes.strip():
        raise ValueError("Empty IBKR Flex XML payload.")

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"Malformed IBKR Flex XML: {exc}") from exc

    events: List[Dict[str, Any]] = []
    positions: List[Dict[str, Any]] = []
    trades_count = 0
    div_count = 0

    trade_nodes = list(root.findall(".//Trade")) + list(root.findall(".//TradeConfirm"))
    seen_trade_sigs = set()
    for node in trade_nodes:
        attr = node.attrib
        asset_cat = str(attr.get("assetCategory") or "").upper()
        if asset_cat == "CASH":
            continue
        raw_sym = attr.get("symbol") or attr.get("underlyingSymbol") or ""
        ticker = _normalize_ibkr_ticker(raw_sym, asset_cat)
        if not ticker:
            continue

        buy_sell = str(attr.get("buySell") or "").strip().upper()
        if buy_sell in ("BUY", "BOT"):
            tx_type = "BUY"
        elif buy_sell in ("SELL", "SLD"):
            tx_type = "SELL"
        else:
            continue

        try:
            qty = abs(float(attr.get("quantity") or 0.0))
            raw_px = float(attr.get("tradePrice") or attr.get("price") or 0.0)
            raw_comm = abs(float(attr.get("ibCommission") or attr.get("commission") or 0.0))
            fx = float(attr.get("fxRateToBase") or 1.0)
        except (TypeError, ValueError):
            continue

        if qty <= 0 or raw_px < 0:
            continue
        ccy = str(attr.get("currency") or "USD").strip().upper()
        fx_mult = fx if (ccy != "USD" and fx > 0) else 1.0
        price_usd = round(raw_px * fx_mult, 6)
        fee_usd = round(raw_comm * fx_mult, 4)

        tx_date = _normalize_flex_date(str(attr.get("tradeDate") or attr.get("dateTime") or attr.get("reportDate") or ""))
        ext_id = str(attr.get("transactionID") or attr.get("tradeID") or attr.get("ibExecID") or "").strip()
        if not ext_id:
            ext_id = f"{tx_date}:{ticker}:{tx_type}:{qty:.6f}:{price_usd:.4f}"
        if ext_id in seen_trade_sigs:
            continue
        seen_trade_sigs.add(ext_id)

        trades_count += 1
        events.append(
            {
                "tx_date": tx_date,
                "ticker": ticker,
                "tx_type": tx_type,
                "quantity": qty,
                "price_usd": price_usd,
                "fee_usd": fee_usd,
                "notes": f"IBKR Flex {tx_type}",
                "external_ref": f"ibkr:{ext_id}",
            }
        )

    for node in root.findall(".//CashTransaction"):
        attr = node.attrib
        ctype = str(attr.get("type") or "").strip()
        if "dividend" not in ctype.lower():
            continue
        ticker = _normalize_ibkr_ticker(attr.get("symbol") or attr.get("underlyingSymbol") or "")
        if not ticker:
            continue
        try:
            amount = float(attr.get("amount") or 0.0)
            fx = float(attr.get("fxRateToBase") or 1.0)
        except (TypeError, ValueError):
            continue
        if amount <= 0:
            continue
        ccy = str(attr.get("currency") or "USD").strip().upper()
        fx_mult = fx if (ccy != "USD" and fx > 0) else 1.0
        amount_usd = round(amount * fx_mult, 4)
        tx_date = _normalize_flex_date(str(attr.get("dateTime") or attr.get("settleDate") or attr.get("reportDate") or ""))
        ext_id = str(attr.get("transactionID") or attr.get("actionID") or f"div:{tx_date}:{ticker}:{amount_usd:.4f}").strip()
        div_count += 1
        events.append(
            {
                "tx_date": tx_date,
                "ticker": ticker,
                "tx_type": "DIVIDEND",
                "quantity": 1.0,
                "price_usd": amount_usd,
                "fee_usd": 0.0,
                "notes": f"IBKR Flex {ctype}",
                "external_ref": f"ibkr:{ext_id}",
            }
        )

    for node in root.findall(".//OpenPosition"):
        attr = node.attrib
        asset_cat = str(attr.get("assetCategory") or "").upper()
        ticker = _normalize_ibkr_ticker(attr.get("symbol") or "", asset_cat)
        if not ticker:
            continue
        try:
            qty = float(attr.get("position") or 0.0)
            mark_px = float(attr.get("markPrice") or 0.0)
            cost_px = float(attr.get("costBasisPrice") or attr.get("openPrice") or 0.0)
            pos_val = float(attr.get("positionValue") or (qty * mark_px))
        except (TypeError, ValueError):
            continue
        positions.append(
            {
                "ticker": ticker,
                "description": str(attr.get("description") or ticker).strip(),
                "asset_category": asset_cat or "STK",
                "quantity": qty,
                "mark_price": mark_px,
                "cost_basis_price": cost_px,
                "position_value": pos_val,
                "currency": str(attr.get("currency") or "USD").strip().upper(),
            }
        )

    return {
        "events": events,
        "positions": positions,
        "summary": {
            "trades": trades_count,
            "dividends": div_count,
            "open_positions": len(positions),
        },
    }


def fetch_ibkr_flex_query(token: str, query_id: str, timeout: int = 15) -> bytes:
    """
    Executes Interactive Brokers' official 2-step read-only Flex Web Service workflow:
    1. SendRequest -> obtains temporary ReferenceCode
    2. GetStatement -> polls XML Flex report
    """
    tok = (token or "").strip()
    qid = (query_id or "").strip()
    if not tok or not qid:
        raise ValueError("IBKR Flex Token and Flex Query ID are required.")

    headers = {"User-Agent": "InstitutionalTerminal/3.0"}
    resp = requests.get(
        _IBKR_FLEX_SEND_URL,
        params={"t": tok, "q": qid, "v": "3"},
        headers=headers,
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise ValueError(f"IBKR Flex SendRequest failed with HTTP {resp.status_code}.")

    try:
        send_root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML returned by IBKR SendRequest: {exc}") from exc

    status = (send_root.findtext("Status") or "").strip()
    if status != "Success":
        err_msg = (send_root.findtext("ErrorMessage") or "Request rejected").strip()
        raise ValueError(f"IBKR Flex SendRequest error: {err_msg}")

    ref_code = (send_root.findtext("ReferenceCode") or "").strip()
    if not ref_code:
        raise ValueError("IBKR Flex SendRequest succeeded without returning a ReferenceCode.")

    base_url = (send_root.findtext("Url") or _IBKR_FLEX_GET_URL).strip()
    last_err = "Statement still generating."
    for attempt in range(4):
        if attempt > 0:
            time.sleep(min(4.0, 1.5 * attempt))
        get_resp = requests.get(
            base_url,
            params={"q": ref_code, "t": tok, "v": "3"},
            headers=headers,
            timeout=timeout,
        )
        if get_resp.status_code != 200:
            last_err = f"HTTP {get_resp.status_code}"
            continue
        content = get_resp.content
        if b"<FlexQueryResponse" in content:
            return content
        try:
            err_root = ET.fromstring(content)
            err_code = (err_root.findtext("ErrorCode") or "").strip()
            last_err = (err_root.findtext("ErrorMessage") or "Pending").strip()
            # 1019 = Statement generation in progress; retry
            if err_code not in ("1019", "1018", ""):
                raise ValueError(f"IBKR Flex GetStatement error ({err_code}): {last_err}")
        except ET.ParseError:
            if content.strip():
                return content

    raise ValueError(f"IBKR Flex Statement timeout after polling: {last_err}")


def _to_binance_pair(symbol: str) -> str:
    tk = (symbol or "").strip().upper()
    if tk.endswith("-USD"):
        base = tk[:-4]
        return f"{base}USDT"
    if "/" in tk:
        return tk.replace("/", "")
    if tk.endswith(("USDT", "USDC", "FDUSD", "BUSD", "BTC")):
        return tk
    return f"{tk}USDT"


def _binance_base_from_pair(pair: str) -> str:
    for quote in ("USDT", "USDC", "FDUSD", "BUSD", "TUSD", "USD"):
        if pair.endswith(quote) and len(pair) > len(quote):
            return pair[: -len(quote)]
    return pair


def fetch_binance_readonly_snapshot(
    api_key: str,
    api_secret: str,
    symbols: Optional[List[str]] = None,
    include_stablecoins: bool = False,
    timeout: int = 12,
) -> Dict[str, Any]:
    """
    Fetches read-only Spot account balances (`GET /api/v3/account`) and optional recent
    trade executions (`GET /api/v3/myTrades`) using HMAC-SHA256 authentication.
    Dynamically discovers ALL held non-zero assets without hardcoded coin filters.
    """
    key = (api_key or "").strip()
    secret = (api_secret or "").strip()
    if not key or not secret:
        return {
            "balances": [],
            "events": [],
            "error": "Binance read-only API Key and Secret are required.",
        }

    headers = {"X-MBX-APIKEY": key}

    def _signed_get(endpoint: str, extra_params: Optional[Dict[str, Any]] = None) -> requests.Response:
        ts_ms = int(time.time() * 1000)
        try:
            t_resp = requests.get("https://api.binance.com/api/v3/time", timeout=4)
            if t_resp.status_code == 200:
                ts_ms = int(t_resp.json().get("serverTime", ts_ms))
        except Exception:
            pass
        params: Dict[str, Any] = dict(extra_params or {})
        params["recvWindow"] = 10000
        params["timestamp"] = ts_ms
        query = urllib.parse.urlencode(params)
        sig = hmac.new(secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
        url = f"https://api.binance.com{endpoint}?{query}&signature={sig}"
        return requests.get(url, headers=headers, timeout=timeout)

    try:
        acc_resp = _signed_get("/api/v3/account")
    except Exception as exc:
        return {"balances": [], "events": [], "error": f"Network error reaching Binance API: {type(exc).__name__}"}

    if acc_resp.status_code != 200:
        try:
            err_json = acc_resp.json()
            err_msg = str(err_json.get("msg") or f"HTTP {acc_resp.status_code}")
        except Exception:
            err_msg = f"HTTP {acc_resp.status_code}"
        return {"balances": [], "events": [], "error": f"Binance API error: {err_msg}"}

    acc_data = acc_resp.json()
    balances: List[Dict[str, Any]] = []
    discovered_pairs: List[str] = []

    for row in acc_data.get("balances", []):
        asset = str(row.get("asset") or "").strip().upper()
        if not asset:
            continue
        free_amt = float(row.get("free") or 0.0)
        locked_amt = float(row.get("locked") or 0.0)
        total_amt = free_amt + locked_amt
        if total_amt <= 1e-10:
            continue
        is_stable = asset in _USD_STABLECOINS
        if is_stable and not include_stablecoins:
            continue
        ticker = f"{asset}-USD"
        balances.append(
            {
                "asset": asset,
                "ticker": ticker,
                "free": free_amt,
                "locked": locked_amt,
                "total": total_amt,
                "is_stablecoin": is_stable,
            }
        )
        if not is_stable and len(discovered_pairs) < 12:
            discovered_pairs.append(f"{asset}USDT")

    target_pairs: List[str] = []
    if symbols:
        for s in symbols:
            if s and s.strip():
                p = _to_binance_pair(s)
                if p not in target_pairs:
                    target_pairs.append(p)
    else:
        target_pairs = discovered_pairs

    events: List[Dict[str, Any]] = []
    for pair in target_pairs:
        try:
            tr_resp = _signed_get("/api/v3/myTrades", {"symbol": pair, "limit": 50})
            if tr_resp.status_code != 200:
                continue
            base_asset = _binance_base_from_pair(pair)
            ticker = f"{base_asset}-USD"
            for tr in tr_resp.json():
                qty = float(tr.get("qty") or 0.0)
                px = float(tr.get("price") or 0.0)
                if qty <= 0 or px < 0:
                    continue
                comm = float(tr.get("commission") or 0.0)
                comm_asset = str(tr.get("commissionAsset") or "").upper()
                if comm_asset in _USD_STABLECOINS:
                    fee_usd = comm
                elif comm_asset == base_asset:
                    fee_usd = comm * px
                else:
                    fee_usd = 0.0
                dt_ms = int(tr.get("time") or 0)
                tx_date = (
                    datetime.datetime.fromtimestamp(dt_ms / 1000.0, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
                    if dt_ms > 0
                    else datetime.date.today().isoformat()
                )
                tx_type = "BUY" if bool(tr.get("isBuyer")) else "SELL"
                tr_id = str(tr.get("id") or f"{dt_ms}:{qty}:{px}")
                events.append(
                    {
                        "tx_date": tx_date,
                        "ticker": ticker,
                        "tx_type": tx_type,
                        "quantity": qty,
                        "price_usd": px,
                        "fee_usd": round(fee_usd, 6),
                        "notes": f"Binance Spot {pair}",
                        "external_ref": f"binance:{pair}:{tr_id}",
                    }
                )
        except Exception:
            continue

    return {"balances": balances, "events": events, "error": None}


def parse_btc_address_payload(address: str, payload: Dict[str, Any], source: str = "blockstream") -> Dict[str, Any]:
    """Parses Blockstream/Mempool Esplora address JSON into BTC balance."""
    chain = payload.get("chain_stats") or {}
    mempool = payload.get("mempool_stats") or {}
    confirmed_sat = int(chain.get("funded_txo_sum", 0)) - int(chain.get("spent_txo_sum", 0))
    mempool_sat = int(mempool.get("funded_txo_sum", 0)) - int(mempool.get("spent_txo_sum", 0))
    confirmed_btc = round(confirmed_sat / 1e8, 8)
    unconfirmed_btc = round(mempool_sat / 1e8, 8)
    total_btc = round((confirmed_sat + mempool_sat) / 1e8, 8)
    return {
        "chain": "Bitcoin",
        "asset": "BTC",
        "ticker": "BTC-USD",
        "address": address,
        "confirmed_balance": confirmed_btc,
        "unconfirmed_balance": unconfirmed_btc,
        "balance": total_btc,
        "source": source,
    }


def fetch_public_btc_balance(btc_address: str, timeout: int = 10) -> Dict[str, Any]:
    """Read-only public BTC address balance via Blockstream / Mempool API."""
    addr = (btc_address or "").strip()
    if not addr:
        return {"error": "Empty Bitcoin address."}
    last_err = "All BTC explorers unreachable"
    for template in _BTC_ENDPOINTS:
        url = template.format(address=urllib.parse.quote(addr))
        src = "blockstream.info" if "blockstream" in url else "mempool.space"
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                return parse_btc_address_payload(addr, resp.json(), source=src)
            last_err = f"{src} HTTP {resp.status_code}"
        except Exception as exc:
            last_err = f"{src} {type(exc).__name__}"
    return {"chain": "Bitcoin", "asset": "BTC", "ticker": "BTC-USD", "address": addr, "balance": None, "error": last_err}


def _eth_json_rpc(method: str, params: List[Any], timeout: int = 10) -> Tuple[Optional[str], Optional[str]]:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    last_err = "All EVM RPC endpoints failed"
    for rpc_url in _EVM_RPC_ENDPOINTS:
        try:
            resp = requests.post(rpc_url, json=payload, timeout=timeout)
            if resp.status_code != 200:
                last_err = f"{rpc_url} HTTP {resp.status_code}"
                continue
            body = resp.json()
            if isinstance(body, dict) and body.get("result") is not None:
                return str(body["result"]), rpc_url
            if isinstance(body, dict) and body.get("error"):
                last_err = str(body["error"])
        except Exception as exc:
            last_err = f"{rpc_url} {type(exc).__name__}"
    return None, last_err


def fetch_public_evm_balances(
    evm_address: str,
    erc20_tokens: Optional[List[Dict[str, Any]]] = None,
    timeout: int = 10,
) -> Dict[str, Any]:
    """
    Read-only public EVM address query (`eth_getBalance` for native ETH + dynamic
    `balanceOf` calls for any user-specified ERC-20 token contracts). Zero private keys.
    """
    addr = (evm_address or "").strip()
    if not _EVM_ADDR_PATTERN.match(addr):
        return {"balances": [], "error": "Invalid EVM address (expected 0x followed by 40 hex chars)."}

    balances: List[Dict[str, Any]] = []
    eth_hex, src_or_err = _eth_json_rpc("eth_getBalance", [addr, "latest"], timeout=timeout)
    if eth_hex is None:
        return {"balances": [], "error": f"EVM RPC error: {src_or_err}"}

    eth_bal = round(int(eth_hex, 16) / 1e18, 8)
    balances.append(
        {
            "chain": "Ethereum",
            "asset": "ETH",
            "ticker": "ETH-USD",
            "address": addr,
            "balance": eth_bal,
            "contract": "NATIVE",
            "source": src_or_err,
        }
    )

    padded_owner = addr[2:].lower().rjust(64, "0")
    call_data = f"0x70a08231{padded_owner}"

    for tok in erc20_tokens or []:
        sym = str(tok.get("symbol") or "").strip().upper()
        contract = str(tok.get("contract") or "").strip()
        decimals = int(tok.get("decimals", 18))
        if not sym or not _EVM_ADDR_PATTERN.match(contract):
            continue
        raw_hex, tok_src = _eth_json_rpc(
            "eth_call",
            [{"to": contract, "data": call_data}, "latest"],
            timeout=timeout,
        )
        if raw_hex is None or not raw_hex.startswith("0x"):
            continue
        try:
            raw_int = int(raw_hex, 16) if len(raw_hex) > 2 else 0
            tok_bal = round(raw_int / (10 ** decimals), 8)
            balances.append(
                {
                    "chain": "Ethereum ERC-20",
                    "asset": sym,
                    "ticker": f"{sym}-USD",
                    "address": addr,
                    "balance": tok_bal,
                    "contract": contract,
                    "source": tok_src,
                }
            )
        except ValueError:
            continue

    return {"balances": balances, "error": None}


def fetch_public_wallet_balances(
    btc_address: str = "",
    evm_address: str = "",
    erc20_tokens: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Queries configured public BTC and/or EVM addresses cleanly with zero private keys."""
    balances: List[Dict[str, Any]] = []
    errors: List[str] = []

    if btc_address and btc_address.strip():
        btc_res = fetch_public_btc_balance(btc_address.strip())
        if btc_res.get("error"):
            errors.append(f"BTC: {btc_res['error']}")
        else:
            balances.append(btc_res)

    if evm_address and evm_address.strip():
        evm_res = fetch_public_evm_balances(evm_address.strip(), erc20_tokens=erc20_tokens)
        if evm_res.get("error"):
            errors.append(f"EVM: {evm_res['error']}")
        balances.extend(evm_res.get("balances") or [])

    return {"balances": balances, "errors": errors}


def import_custody_events_to_ledger(
    portfolio_engine: Any,
    events: List[Dict[str, Any]],
    source_tag: str = "SYNC",
) -> Tuple[int, int]:
    """
    Idempotently inserts normalized custody events (`BUY`/`SELL`/`DIVIDEND`/`STAKING`) into
    `transactions_ledger`. Deduplicates using `[ref:<external_ref>]` tags plus exact tuple
    signatures so re-running custody sync never creates duplicate rows.
    """
    existing = portfolio_engine.get_transactions()
    seen_refs = set()
    seen_sigs = set()
    for tx in existing:
        notes_str = str(tx.get("notes") or "")
        for m in _REF_PATTERN.findall(notes_str):
            seen_refs.add(m.strip())
        seen_sigs.add(
            (
                str(tx.get("tx_date") or "")[:10],
                str(tx.get("ticker") or "").upper(),
                str(tx.get("tx_type") or "").upper(),
                round(float(tx.get("quantity") or 0.0), 6),
                round(float(tx.get("price_usd") or 0.0), 4),
            )
        )

    inserted = 0
    skipped = 0
    for ev in events:
        ext_ref = str(ev.get("external_ref") or "").strip()
        tx_date = _normalize_flex_date(str(ev.get("tx_date") or ""))
        ticker = str(ev.get("ticker") or "").strip().upper()
        tx_type = str(ev.get("tx_type") or "BUY").strip().upper()
        try:
            qty = float(ev.get("quantity") or 0.0)
            px = float(ev.get("price_usd") or 0.0)
            fee = max(0.0, float(ev.get("fee_usd") or 0.0))
        except (TypeError, ValueError):
            skipped += 1
            continue

        if not ticker or qty <= 0 or px < 0:
            skipped += 1
            continue

        sig = (tx_date, ticker, tx_type, round(qty, 6), round(px, 4))
        if (ext_ref and ext_ref in seen_refs) or sig in seen_sigs:
            skipped += 1
            continue

        base_notes = str(ev.get("notes") or source_tag).strip()
        if ext_ref:
            full_notes = f"{base_notes} [ref:{ext_ref}]"
            seen_refs.add(ext_ref)
        else:
            full_notes = base_notes
        seen_sigs.add(sig)

        portfolio_engine.add_transaction(
            tx_date=tx_date,
            ticker=ticker,
            tx_type=tx_type,
            quantity=qty,
            price_usd=px,
            fee_usd=fee,
            notes=full_notes,
        )
        inserted += 1

    return inserted, skipped

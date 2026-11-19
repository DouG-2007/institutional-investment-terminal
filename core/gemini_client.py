"""
================================================================================
DIRECT GEMINI API CLIENT (GOOGLE-GENAI INTERACTIONS API + STRUCTURED OUTPUTS)
================================================================================
Provides centralized, fault-tolerant access to Google's `google-genai` SDK using
the Interactions API (`client.interactions.create`) for non-agentic tasks:
  1. Dynamic SEC 10-K/10-Q & Crypto Whitepaper Structured Output Extraction
  2. Optional Master PDF "Executive AI Thesis & Cross-Asset Risk Synthesis"
  3. Optional Morning Notifier Briefing Interpretation

All functions degrade gracefully (returning None / safe fallback) if
GEMINI_API_KEY is absent or if the API is unreachable. Never logs secrets.
================================================================================
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(ROOT_DIR, ".env")

DEFAULT_GEMINI_MODEL = "gemini-4-hydrogen"
DEFAULT_GEMINI_FAST_MODEL = "gemini-3.5-flash-lite"
_GENAI_FALLBACK_MODELS: Tuple[str, ...] = ("gemini-3.5-flash-lite", "gemini-3.1-flash-lite")
_GENAI_COOLDOWN_SEC = 300.0
_GENAI_LOCK = threading.Lock()
_UNHEALTHY_GENAI_UNTIL: Dict[str, float] = {}

T = TypeVar("T", bound=BaseModel)


def _is_genai_in_cooldown(model_name: str) -> bool:
    now = time.monotonic()
    with _GENAI_LOCK:
        until = _UNHEALTHY_GENAI_UNTIL.get(model_name)
        if until is None:
            return False
        if now >= until:
            _UNHEALTHY_GENAI_UNTIL.pop(model_name, None)
            return False
        return True


def _mark_genai_unhealthy(model_name: str) -> None:
    with _GENAI_LOCK:
        _UNHEALTHY_GENAI_UNTIL[model_name] = time.monotonic() + _GENAI_COOLDOWN_SEC


def _resolve_candidate_models(model: Optional[str] = None, fast: bool = False) -> List[str]:
    primary = model or get_default_model(fast=fast)
    raw = [primary, *(_GENAI_FALLBACK_MODELS if not fast else ("gemini-3.1-flash-lite",))]
    deduped: List[str] = []
    for m in raw:
        if m and m not in deduped:
            deduped.append(m)
    healthy = [m for m in deduped if not _is_genai_in_cooldown(m)]
    return healthy if healthy else deduped


def _is_transient_genai_error(exc: BaseException) -> bool:
    err_str = f"{type(exc).__name__}: {exc}".upper()
    return any(
        tok in err_str
        for tok in ("503", "500", "INTERNAL", "UNAVAILABLE", "429", "RATELIMIT", "RESOURCE_EXHAUSTED", "TIMEOUT", "TIMED OUT")
    )


def _load_env_safely() -> None:
    """Loads root .env without overriding already-set environment variables."""
    try:
        from dotenv import load_dotenv

        if os.path.exists(ENV_FILE_PATH):
            load_dotenv(dotenv_path=ENV_FILE_PATH, override=False)
        else:
            load_dotenv(override=False)
    except Exception:
        pass


_load_env_safely()


def get_gemini_api_key() -> Optional[str]:
    """Returns GEMINI_API_KEY from environment/.env, or None if not configured."""
    _load_env_safely()
    val = os.environ.get("GEMINI_API_KEY", "").strip()
    if not val or val.lower() in ("your_api_key_here", "none", "null", "changeme"):
        return None
    return val


def is_gemini_configured() -> bool:
    """Checks whether GEMINI_API_KEY is present and google-genai SDK is available."""
    if not get_gemini_api_key():
        return False
    try:
        from google import genai  # noqa: F401

        return True
    except Exception:
        return False


def get_default_model(fast: bool = False) -> str:
    """Resolves current model ID from env overrides or compliant defaults."""
    _load_env_safely()
    if fast:
        return os.environ.get("GEMINI_FAST_MODEL", "").strip() or DEFAULT_GEMINI_FAST_MODEL
    return os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_GEMINI_MODEL


def get_genai_client() -> Optional[Any]:
    """Instantiates `google.genai.Client` with fast-fail HTTP options so fallback triggers promptly."""
    api_key = get_gemini_api_key()
    if not api_key:
        return None
    try:
        from google import genai
        from google.genai import types as genai_types

        return genai.Client(
            api_key=api_key,
            http_options=genai_types.HttpOptions(
                timeout=18_000,
                retry_options=genai_types.HttpRetryOptions(attempts=1),
            ),
        )
    except Exception as exc:
        logger.warning("Failed to initialize google-genai Client: %s", type(exc).__name__)
        return None


def generate_text_interaction(
    prompt: str,
    system_instruction: str,
    model: Optional[str] = None,
    fast: bool = False,
    temperature: float = 0.2,
    max_output_tokens: int = 1200,
) -> Optional[str]:
    """Executes a stateless Interactions API text generation call (`store=False`) with cooldown fallback."""
    client = get_genai_client()
    if client is None:
        return None

    for chosen_model in _resolve_candidate_models(model=model, fast=fast):
        try:
            interaction = client.interactions.create(
                model=chosen_model,
                input=prompt,
                system_instruction=system_instruction,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
                store=False,
                timeout=18.0,
            )
            text = (getattr(interaction, "output_text", None) or "").strip()
            if text:
                return text
        except Exception as exc:
            logger.warning("Gemini text interaction failed (%s): %s", chosen_model, type(exc).__name__)
            if _is_transient_genai_error(exc):
                _mark_genai_unhealthy(chosen_model)
                continue
            break
    return None


def _generate_structured_with_model(
    input_payload: Any,
    schema_cls: Type[T],
    system_instruction: str,
    model: Optional[str] = None,
    fast: bool = False,
    temperature: float = 0.1,
    max_output_tokens: int = 3000,
) -> Tuple[Optional[T], Optional[str]]:
    """Internal helper returning `(parsed_model, winning_model_name)` with automatic fallback."""
    client = get_genai_client()
    if client is None:
        return None, None

    for chosen_model in _resolve_candidate_models(model=model, fast=fast):
        try:
            interaction = client.interactions.create(
                model=chosen_model,
                input=input_payload,
                system_instruction=system_instruction,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": schema_cls.model_json_schema(),
                },
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
                store=False,
                timeout=18.0,
            )
            raw_json = (getattr(interaction, "output_text", None) or "").strip()
            if raw_json:
                return schema_cls.model_validate_json(raw_json), chosen_model
        except Exception as exc:
            logger.warning(
                "Gemini structured interaction failed (%s, schema=%s): %s",
                chosen_model,
                schema_cls.__name__,
                type(exc).__name__,
            )
            if _is_transient_genai_error(exc):
                _mark_genai_unhealthy(chosen_model)
                continue
            break
    return None, None


def generate_structured_interaction(
    input_payload: Any,
    schema_cls: Type[T],
    system_instruction: str,
    model: Optional[str] = None,
    fast: bool = False,
    temperature: float = 0.1,
    max_output_tokens: int = 3000,
) -> Optional[T]:
    """
    Executes a stateless Interactions API call enforcing a Pydantic JSON schema
    via the current unified `response_format` contract.
    """
    parsed, _ = _generate_structured_with_model(
        input_payload=input_payload,
        schema_cls=schema_cls,
        system_instruction=system_instruction,
        model=model,
        fast=fast,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    return parsed


class ExecutiveAISynthesisSchema(BaseModel):
    """Structured schema for optional Master PDF executive cross-asset synthesis."""

    macro_regime_thesis: str = Field(
        description=(
            "2 to 3 crisp sentences interpreting the current macro regime, Sahm Rule/SOS, "
            "10Y-2Y spread, and global liquidity M2/DXY using ONLY figures from the input payload."
        )
    )
    cross_asset_risk_synthesis: str = Field(
        description=(
            "2 to 3 crisp sentences linking hard-asset equity valuations/forensics, crypto "
            "on-chain/Real Earnings signals, geopolitical tail risks, and Convex LTV headroom."
        )
    )
    key_actionable_priorities: List[str] = Field(
        min_length=3,
        max_length=4,
        description=(
            "3 to 4 concise consultative (non-binding) priority takeaways grounded strictly "
            "in Shannon Inflow eligibility, Reverse DCF g_impl vs g_fund, or LTV/unlock thresholds."
        ),
    )


def generate_pdf_executive_synthesis(
    macro: Any,
    portfolio: Any,
    equities: List[Any],
    cryptos: Dict[str, Any],
    geo_matrix: List[Any],
    risk_timing: Any,
    model: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Synthesizes an optional executive AI summary for Section 1 of the Master PDF.
    Strictly fed with pre-computed deterministic numbers; returns None if unavailable.
    """
    if not is_gemini_configured():
        return None

    try:
        sp = getattr(macro, "sahm_paired", {}) or {}
        sos = getattr(macro, "sos_indicator", {}) or {}
        yc = getattr(macro, "yield_curve", {}) or {}
        mon = getattr(macro, "monetary_aggregates", {}) or {}
        pmi = getattr(macro, "pmi_analysis", {}) or {}
        ltv = getattr(risk_timing, "convex_ltv_panel", {}) or {}

        eq_highlights = []
        for e in equities[:10]:
            vm = e.valuation_methods
            fh = e.forensic_health
            eq_highlights.append(
                {
                    "ticker": e.ticker,
                    "spot_usd": round(float(e.current_price), 2),
                    "sloan_pct": fh.get("sloan_ratio_pct"),
                    "roic_pct": fh.get("roic_goodwill_pct"),
                    "wacc_pct": fh.get("wacc_pct"),
                    "g_impl_pct": vm.get("reverse_dcf_g_impl_pct"),
                    "g_fund_pct": vm.get("g_fund_projected_pct"),
                    "pegy": vm.get("primary_pegy_label"),
                    "pegy_status": vm.get("primary_pegy_status"),
                    "sotp_usd": vm.get("sotp_fair_price_usd"),
                }
            )

        cr_highlights = []
        for sym, c in list(cryptos.items())[:8]:
            om = c.onchain_metrics
            tv = c.tokenomics_valuation
            ss = c.supply_structure
            cr_highlights.append(
                {
                    "symbol": sym,
                    "spot_usd": round(float(c.spot_price_usd), 2),
                    "mvrv_z": om.get("mvrv_z_score"),
                    "nupl": om.get("nupl"),
                    "asopr": om.get("asopr"),
                    "real_earnings_m": tv.get("protocol_real_earnings_m"),
                    "real_yield_pct": tv.get("real_yield_pct"),
                    "unlock_30d_pct": ss.get("unlock_pct_of_circ"),
                }
            )

        inflow_eligible = [
            r.asset_ticker
            for r in getattr(risk_timing, "consultative_asset_timing_table", [])
            if getattr(r, "shannon_inflow_eligible", False)
        ]

        geo_top = [
            {
                "event": g.global_event,
                "severity": g.severity,
                "assets": g.affected_portfolio_assets,
            }
            for g in geo_matrix[:4]
        ]

        snapshot = {
            "capital_usd": round(float(portfolio.capital_usd), 2),
            "crypto_pct": round(float(portfolio.total_crypto_pct), 2),
            "hard_assets_pct": round(float(portfolio.total_hard_assets_pct), 2),
            "effective_gross_exposure_pct": round(float(portfolio.effective_gross_exposure_pct), 2),
            "portfolio_pnl_pct": round(float(portfolio.total_portfolio_pnl_pct), 2),
            "macro": {
                "cycle_phase": getattr(macro, "cycle_phase", ""),
                "sahm_pct": sp.get("sahm_current_pct"),
                "sahm_verdict": sp.get("paired_verdict"),
                "sos_current": sos.get("sos_current"),
                "pmi_services": pmi.get("pmi_services_current"),
                "pmi_mfg": pmi.get("pmi_manufacturing_current"),
                "spread_10y_2y_bps": yc.get("spread_10y_2y_bps"),
                "us10y_pct": yc.get("us10y_pct"),
                "m2_trillions": mon.get("m2_trillions"),
                "dxy": mon.get("dxy_current"),
            },
            "ltv_global_pct": ltv.get("ltv_global_current_pct"),
            "ltv_turbo_status": ltv.get("turbo_trigger_status"),
            "shannon_inflow_eligible_tickers": inflow_eligible,
            "equities": eq_highlights,
            "cryptos": cr_highlights,
            "top_geopolitical_risks": geo_top,
        }

        import json

        chosen_model = model or get_default_model(fast=False)
        system_instruction = (
            "You are the Chief Investment Strategist for an Institutional Multi-Asset Value Investing "
            "Terminal. Synthesize ONLY the deterministic JSON metrics provided. "
            "IRONCLAD RULES: (1) Cite ONLY numbers explicitly present in the payload — NEVER invent, "
            "recompute, or estimate missing numbers. (2) Never reference Altman Z-Score. "
            "(3) All recommendations must be strictly consultative/non-binding (no automated trading). "
            "(4) Write in crisp, concise institutional English suitable for an A4 landscape executive box."
        )
        prompt = (
            "Produce an executive cross-asset synthesis from this verified deterministic portfolio snapshot:\n\n"
            + json.dumps(snapshot, ensure_ascii=False)
        )
        res, winning_model = _generate_structured_with_model(
            input_payload=prompt,
            schema_cls=ExecutiveAISynthesisSchema,
            system_instruction=system_instruction,
            model=model,
            temperature=0.15,
            max_output_tokens=1100,
        )
        if res is None:
            return None
        return {
            "macro_regime_thesis": res.macro_regime_thesis,
            "cross_asset_risk_synthesis": res.cross_asset_risk_synthesis,
            "key_actionable_priorities": res.key_actionable_priorities,
            "model_used": winning_model or get_default_model(fast=False),
        }
    except Exception as exc:
        logger.warning("Executive AI PDF synthesis skipped: %s", type(exc).__name__)
        return None

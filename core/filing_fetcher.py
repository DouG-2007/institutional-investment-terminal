"""
================================================================================
COMPREHENSIVE MULTI-DOCUMENT AUTO-FETCHER (EQUITIES & CRYPTOASSETS)
================================================================================
Eliminates manual PDF downloading and captures ALL document classes modeled in
`EquityDocumentaryDossier` and `CryptoDocumentaryDossier`:

1. Equities (Full SEC + Wall Street Consensus Bundle):
   - SEC EDGAR Annual (`10-K` / `20-F`): Auditor, SOX 404(b), Item 1A, Item 7 MD&A,
     Forensic Footnotes (ASC 606, SBC, Debt Maturities, Litigation).
   - SEC EDGAR Latest Quarterly (`10-Q` / `6-K`): Sequential margin/MD&A updates.
   - SEC EDGAR Material Events (`8-K`, latest up to 3 filings): Earnings releases,
     M&A, guidance updates, material agreements.
   - SEC EDGAR Governance & Insider Telemetry (`Form 4` 90d activity + `DEF 14A`).
   - External Wall Street Analysts' Consensus (`yfinance`): Mean/High/Low price
     targets, Buy/Hold/Sell distribution, and 7d/30d EPS upward/downward revisions.

2. Cryptoassets (Full Protocol + Dev + Governance + Security Bundle):
   - CoinGecko Protocol Metadata + Official Whitepaper / Docs (PDF or HTML) +
     GitHub `README.md` fallback.
   - Live GitHub Engineering Telemetry: Direct commit count over the last 28 days
     (`/commits?since=...`) and unique monthly active committers across core repos.
   - Snapshot GraphQL DAO Governance: Live space matching + recent proposals,
     voting counts, and governance activity status.
   - DeFiLlama Protocol Audits, Staking TVL & Exploits DB (`api.llama.fi/protocols`,
     `api.llama.fi/protocol/{slug}`, `api.llama.fi/hacks`).

100% free public endpoints, zero paid API keys required.
================================================================================
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import datetime
import html as html_lib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC_TICKERS_CACHE_PATH = os.path.join(ROOT_DIR, "data_cache", "sec_tickers.json")
SEC_USER_AGENT = "InstitutionalInvestmentTerminal/1.0 (research@institutional-terminal.local)"
_SEC_CACHE_TTL_SEC = 7 * 24 * 3600


def _http_get_bytes(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 16) -> bytes:
    req_headers = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "identity"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _http_post_json(url: str, payload: Dict[str, Any], timeout: int = 12) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": SEC_USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _strip_html_to_text(raw_html: str) -> str:
    """Converts SEC/Docs HTML into clean readable plain text."""
    cleaned = re.sub(r"(?is)<(script|style|ix:header|ix:hidden)[^>]*>.*?</\1>", " ", raw_html)
    cleaned = re.sub(r"(?i)</?(div|p|tr|li|h[1-6]|br|table)[^>]*>", "\n", cleaned)
    cleaned = re.sub(r"(?s)<[^>]+>", " ", cleaned)
    cleaned = html_lib.unescape(cleaned)
    cleaned = re.sub(r"[ \t\xa0]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
    return cleaned.strip()


def _extract_forensic_sections(full_text: str, max_total_chars: int = 68_000) -> str:
    """
    Slices a full 10-K/20-F/10-Q into high-signal forensic excerpts so Gemini
    receives Item 1A, Item 7 MD&A, Auditor/SOX 404(b), and Footnotes without
    wasting context on boilerplate or Table of Contents.
    """
    if len(full_text) <= max_total_chars:
        return full_text

    chunks: List[str] = ["=== FILING COVER & HEADER ===\n" + full_text[:3_500]]
    body_offset = min(10_000, len(full_text) // 10)
    body = full_text[body_offset:]

    section_specs = [
        ("ITEM 1A — RISK FACTORS", r"(?im)^\s*item\s+1a[\.\:\s\-]+risk\s+factors", 16_000),
        ("ITEM 7 / MD&A", r"(?im)^\s*(item\s+7|item\s+2)[\.\:\s\-]+management.{0,24}discussion", 22_000),
        (
            "AUDITOR REPORT & SOX 404(b)",
            r"(?im)(report\s+of\s+independent\s+registered\s+public\s+accounting\s+firm|item\s+9a[\.\:\s\-]+controls\s+and\s+procedures)",
            12_000,
        ),
        (
            "FORENSIC FOOTNOTES (REVENUE / SBC / DEBT / CONTINGENCIES)",
            r"(?im)(note\s+\d+\s*[\.\:\-—]\s*(revenue|stock[- ]based\s+compensation|debt|commitments\s+and\s+contingencies|legal))",
            12_500,
        ),
        (
            "BUSINESS COMBINATIONS, M&A, GOODWILL & STRATEGIC DEALS",
            r"(?im)(note\s+\d+\s*[\.\:\-—]\s*(business\s+combinations|acquisitions|divestitures|goodwill\s+and\s+intangible)|item\s+(1\.01|2\.01)\b)",
            11_000,
        ),
    ]

    used_ranges: List[Tuple[int, int]] = []
    for label, pattern, window in section_specs:
        matches = list(re.finditer(pattern, body))
        if not matches:
            continue
        chosen_pos = matches[0].start()
        for m in matches:
            snippet_after = body[m.start():m.start() + 600]
            if len(snippet_after.splitlines()) >= 4 and len(snippet_after) > 320:
                chosen_pos = m.start()
                break
        start = chosen_pos
        end = min(len(body), start + window)
        if any(abs(start - u0) < 3500 for u0, _ in used_ranges):
            continue
        used_ranges.append((start, end))
        chunks.append(f"\n\n=== {label} ===\n" + body[start:end])

    combined = "\n".join(chunks)
    if len(combined) < 18_000:
        mid = len(full_text) // 2
        combined = (
            full_text[:22_000]
            + "\n\n=== MID-FILING EXCERPT ===\n"
            + full_text[mid:mid + 24_000]
            + "\n\n=== NOTES & CONTROLS EXCERPT ===\n"
            + full_text[-22_000:]
        )

    return combined[:max_total_chars]


def _get_sec_ticker_map() -> Dict[str, Dict[str, Any]]:
    """Loads ticker -> {cik, title} from SEC EDGAR with 7-day local cache."""
    if os.path.exists(SEC_TICKERS_CACHE_PATH):
        try:
            age = time.time() - os.path.getmtime(SEC_TICKERS_CACHE_PATH)
            if age < _SEC_CACHE_TTL_SEC:
                with open(SEC_TICKERS_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

    raw = _http_get_bytes("https://www.sec.gov/files/company_tickers.json", timeout=15)
    parsed = json.loads(raw.decode("utf-8"))
    by_ticker: Dict[str, Dict[str, Any]] = {}
    for entry in parsed.values():
        tk = str(entry.get("ticker", "")).strip().upper()
        if tk:
            by_ticker[tk] = {
                "cik": int(entry["cik_str"]),
                "title": str(entry.get("title", tk)),
            }

    try:
        os.makedirs(os.path.dirname(SEC_TICKERS_CACHE_PATH), exist_ok=True)
        with open(SEC_TICKERS_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(by_ticker, f)
    except Exception:
        pass

    return by_ticker


def _download_sec_filing_text(
    cik_int: int,
    accession: str,
    primary_doc: str,
    max_raw_bytes: int = 7_500_000,
    max_text_chars: int = 68_000,
    slice_forensic: bool = True,
) -> str:
    acc_nodash = accession.replace("-", "")
    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{primary_doc}"
    raw_bytes = _http_get_bytes(doc_url, timeout=22)
    raw_html = raw_bytes[:max_raw_bytes].decode("utf-8", errors="replace")
    plain = _strip_html_to_text(raw_html)
    if slice_forensic:
        return _extract_forensic_sections(plain, max_total_chars=max_text_chars)
    return plain[:max_text_chars]


def _fetch_yfinance_analyst_report(ticker: str) -> Tuple[str, Dict[str, Any]]:
    """Extracts external analyst targets, recommendations distribution & EPS revisions."""
    lines: List[str] = []
    meta: Dict[str, Any] = {"has_analyst_data": False}
    try:
        import yfinance as yf

        t = yf.Ticker(ticker)
        info = t.info or {}
        mean_pt = info.get("targetMeanPrice")
        high_pt = info.get("targetHighPrice")
        low_pt = info.get("targetLowPrice")
        n_op = info.get("numberOfAnalystOpinions")
        rec_key = info.get("recommendationKey")

        if mean_pt is not None:
            meta["analyst_target_mean_usd"] = float(mean_pt)
            meta["has_analyst_data"] = True
            lines.append(
                f"- Consensus Price Target: ${float(mean_pt):,.2f} USD "
                f"(Low: ${float(low_pt or 0):,.2f}, High: ${float(high_pt or 0):,.2f}, "
                f"Opinions: {n_op or 'N/A'}, Consensus Rating: {rec_key or 'N/A'})"
            )

        rec_sum = getattr(t, "recommendations_summary", None)
        if rec_sum is not None and not rec_sum.empty:
            row0 = rec_sum.iloc[0].to_dict()
            sb = int(row0.get("strongBuy", 0) or 0)
            b = int(row0.get("buy", 0) or 0)
            h = int(row0.get("hold", 0) or 0)
            s = int(row0.get("sell", 0) or 0)
            ss = int(row0.get("strongSell", 0) or 0)
            tot = sb + b + h + s + ss
            if tot > 0:
                meta["has_analyst_data"] = True
                buy_pct = round(((sb + b) / tot) * 100)
                hold_pct = round((h / tot) * 100)
                sell_pct = max(0, 100 - buy_pct - hold_pct)
                lines.append(
                    f"- Analyst Recommendations Distribution ({tot} Analysts): "
                    f"{buy_pct}% Buy/Strong Buy ({sb + b}) | {hold_pct}% Hold ({h}) | {sell_pct}% Sell/Strong Sell ({s + ss})"
                )

        eps_rev = getattr(t, "eps_revisions", None)
        if eps_rev is not None and not eps_rev.empty:
            rev_dict = eps_rev.to_dict()
            up30 = rev_dict.get("upLast30days", {})
            dn30 = rev_dict.get("downLast30days", {})
            up7 = rev_dict.get("upLast7days", {})
            dn7 = rev_dict.get("downLast7Days", {})
            meta["has_eps_revisions"] = True
            lines.append(
                f"- EPS Revisions (Current Qtr `0q` / Current Yr `0y`): "
                f"7d Up/Down (0q={up7.get('0q', 0)}/{dn7.get('0q', 0)}, 0y={up7.get('0y', 0)}/{dn7.get('0y', 0)}) | "
                f"30d Up/Down (0q={up30.get('0q', 0)}/{dn30.get('0q', 0)}, 0y={up30.get('0y', 0)}/{dn30.get('0y', 0)}, +1y={up30.get('+1y', 0)}/{dn30.get('+1y', 0)})"
            )
    except Exception:
        pass

    text = (
        "=== EXTERNAL ANALYSTS' CONSENSUS REPORT (YFINANCE) ===\n" + "\n".join(lines)
        if lines
        else ""
    )
    return text, meta


def fetch_complete_equity_document_bundle(
    ticker: str,
    preferred_forms: Tuple[str, ...] = ("10-K", "20-F", "10-Q"),
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Fetches ALL documentary pillars for an equity:
      1. Latest Annual SEC Filing (`10-K` or `20-F`)
      2. Latest Quarterly SEC Filing (`10-Q` or `6-K`)
      3. Latest Material Current Reports (`8-K`, up to 3 recent filings)
      4. `Form 4` insider & `DEF 14A` proxy submission metadata
      5. External Wall Street Analysts' Consensus (`yfinance`)
    Returns `(combined_document_bundle_text, metadata_dict)`.
    """
    tk = (ticker or "").strip().upper().replace(".", "-")
    if not tk:
        return None, {"error": "Empty ticker."}

    analyst_future_text = ""
    analyst_meta: Dict[str, Any] = {}
    tmap: Optional[Dict[str, Dict[str, Any]]] = None
    sec_err: Optional[str] = None

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_analyst = pool.submit(_fetch_yfinance_analyst_report, tk)
        f_tmap = pool.submit(_get_sec_ticker_map)
        try:
            analyst_future_text, analyst_meta = f_analyst.result(timeout=15)
        except Exception:
            analyst_future_text, analyst_meta = "", {}
        try:
            tmap = f_tmap.result(timeout=18)
        except Exception as exc:
            sec_err = f"SEC EDGAR ticker index unreachable: {exc}"

    info = (tmap or {}).get(tk) or (tmap or {}).get(tk.replace("-", ""))
    if not info:
        if analyst_future_text:
            return (
                analyst_future_text,
                {
                    "ticker": tk,
                    "sec_found": False,
                    "sources_fetched": ["External Analyst Consensus (yfinance)"],
                    "needs_search_enrichment": True,
                    **analyst_meta,
                    "error": sec_err or f"Ticker '{tk}' not indexed in SEC EDGAR (non-US/OTC).",
                },
            )
        return None, {"error": sec_err or f"Ticker '{tk}' not found in SEC EDGAR."}

    cik_int = int(info["cik"])
    cik_padded = str(cik_int).zfill(10)
    company_title = info["title"]

    try:
        sub_raw = _http_get_bytes(f"https://data.sec.gov/submissions/CIK{cik_padded}.json", timeout=15)
        sub = json.loads(sub_raw.decode("utf-8"))
        company_title = str(sub.get("name") or company_title)
        recent = sub.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
    except Exception as exc:
        return (
            analyst_future_text or None,
            {
                "ticker": tk,
                "sec_found": False,
                "needs_search_enrichment": True,
                "error": f"Failed SEC submissions for CIK {cik_padded}: {exc}",
            },
        )

    # Locate Annual (10-K / 20-F), Quarterly (10-Q / 6-K), up to 3 recent 8-Ks, Form 4 count, DEF 14A
    annual_idx: Optional[int] = None
    for target in ("10-K", "20-F") if "10-Q" not in preferred_forms[:1] else ("10-K", "20-F"):
        for i, f_type in enumerate(forms):
            if str(f_type).strip().upper() == target:
                annual_idx = i
                break
        if annual_idx is not None:
            break

    quarterly_idx: Optional[int] = None
    for target_q in ("10-Q", "6-K"):
        for i, f_type in enumerate(forms):
            if str(f_type).strip().upper() == target_q:
                quarterly_idx = i
                break
        if quarterly_idx is not None:
            break

    eightk_indices: List[int] = [
        i for i, f_type in enumerate(forms) if str(f_type).strip().upper() in ("8-K", "8-K/A")
    ][:3]

    cutoff_90d = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
    form4_recent = [dates[i] for i, ft in enumerate(forms) if str(ft).strip().upper() == "4" and dates[i] >= cutoff_90d]
    def14a_dates = [dates[i] for i, ft in enumerate(forms) if "DEF 14A" in str(ft).strip().upper()][:2]

    # Parallel download of Annual (10-K/20-F), Quarterly (10-Q/6-K), and 8-Ks
    sections_out: List[str] = []
    sources_fetched: List[str] = []
    source_urls: List[str] = []

    def _fetch_idx(idx: Optional[int], max_chars: int, slice_forensic: bool) -> Tuple[Optional[str], str, str]:
        if idx is None:
            return None, "", ""
        ft = str(forms[idx])
        dt = str(dates[idx])
        rd = str(report_dates[idx]) if idx < len(report_dates) else dt
        acc = str(accessions[idx])
        pdoc = str(primary_docs[idx])
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc.replace('-', '')}/{pdoc}"
        txt = _download_sec_filing_text(
            cik_int, acc, pdoc, max_text_chars=max_chars, slice_forensic=slice_forensic
        )
        return txt, f"SEC Form {ft} (Filed {dt}, Period {rd})", url

    with ThreadPoolExecutor(max_workers=5) as pool:
        f_ann = pool.submit(_fetch_idx, annual_idx, 62_000, True)
        f_qrt = pool.submit(_fetch_idx, quarterly_idx, 20_000, True)
        f_8ks = [pool.submit(_fetch_idx, i8, 4_500, False) for i8 in eightk_indices]

        ann_txt, ann_lbl, ann_url = f_ann.result() if annual_idx is not None else (None, "", "")
        qrt_txt, qrt_lbl, qrt_url = f_qrt.result() if quarterly_idx is not None else (None, "", "")
        eightk_results = []
        for f8 in f_8ks:
            try:
                eightk_results.append(f8.result())
            except Exception:
                pass

    header = (
        f"OFFICIAL MULTI-DOCUMENT SEC EDGAR + ANALYST BUNDLE FOR {tk}:\n"
        f"- Legal Company Name: {company_title}\n"
        f"- SEC CIK: {cik_padded}\n"
        f"- Annual Filing On Record: {ann_lbl or 'Not available'}\n"
        f"- Quarterly Filing On Record: {qrt_lbl or 'Not available'}\n"
        f"- Recent Material 8-K Filings Fetched: {len([r for r in eightk_results if r[0]])}\n"
        f"- Insider Form 4 Filings (Last 90d): {len(form4_recent)} filings"
        + (f" (latest: {form4_recent[0]})" if form4_recent else "")
        + "\n"
        + f"- Proxy Statement (DEF 14A): {', '.join(def14a_dates) if def14a_dates else 'None in recent submissions'}\n"
    )
    sections_out.append(header)

    if analyst_future_text:
        sections_out.append(analyst_future_text)
        sources_fetched.append("Wall Street Consensus & EPS Revisions (yfinance)")
    if ann_txt:
        sections_out.append(f"=== ANNUAL FILING: {ann_lbl} ===\n{ann_txt}")
        sources_fetched.append(ann_lbl)
        source_urls.append(ann_url)
    if qrt_txt:
        sections_out.append(f"=== LATEST QUARTERLY FILING: {qrt_lbl} ===\n{qrt_txt}")
        sources_fetched.append(qrt_lbl)
        source_urls.append(qrt_url)
    for k_txt, k_lbl, k_url in eightk_results:
        if k_txt:
            sections_out.append(f"=== MATERIAL EVENT ({k_lbl}) ===\n{k_txt}")
            sources_fetched.append(k_lbl)
            source_urls.append(k_url)

    combined_text = "\n\n".join(sections_out)
    if not (ann_txt or qrt_txt or analyst_future_text):
        return None, {"error": f"No recent SEC filings downloaded for {tk}."}

    meta = {
        "ticker": tk,
        "company_name": company_title,
        "cik": cik_padded,
        "sec_found": True,
        "form": ann_lbl or qrt_lbl or "SEC Bundle",
        "filing_date": str(dates[annual_idx]) if annual_idx is not None else (str(dates[quarterly_idx]) if quarterly_idx is not None else ""),
        "annual_filing": ann_lbl,
        "latest_quarterly": qrt_lbl,
        "sources_fetched": sources_fetched,
        "source_url": source_urls[0] if source_urls else "",
        "source_urls": source_urls,
        "chars_extracted": len(combined_text),
        "needs_search_enrichment": not bool(analyst_meta.get("has_analyst_data") and analyst_meta.get("has_eps_revisions")),
        **analyst_meta,
    }
    return combined_text, meta


def fetch_latest_sec_filing_text(
    ticker: str,
    preferred_forms: Tuple[str, ...] = ("10-K", "20-F", "10-Q"),
) -> Tuple[Optional[str], Dict[str, Any]]:
    """Backward-compatible wrapper now returning the complete multi-document equity bundle."""
    return fetch_complete_equity_document_bundle(ticker=ticker, preferred_forms=preferred_forms)


def _fetch_github_engineering_metrics(repo_urls: List[str]) -> Tuple[str, int, int, List[str]]:
    """
    Queries GitHub REST API across up to 3 core repos to measure true 28-day
    commits, unique active monthly committers, repo stats, and README overview.
    """
    since_iso = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=28)).strftime("%Y-%m-%dT%H:%M:%SZ")
    slugs: List[str] = []
    for r_url in repo_urls:
        m = re.search(r"github\.com/([^/]+/[^/]+)", str(r_url))
        if m:
            slug = m.group(1).rstrip("/").removesuffix(".git")
            if slug not in slugs:
                slugs.append(slug)

    if not slugs:
        return "", 0, 0, []

    total_commits_4w = 0
    unique_authors: set[str] = set()
    lines: List[str] = []
    readme_excerpt = ""

    def _inspect_repo(slug: str) -> Tuple[str, int, set[str], str]:
        repo_line = f"- Repo {slug}"
        c4w = 0
        authors: set[str] = set()
        rm = ""
        try:
            meta_raw = _http_get_bytes(f"https://api.github.com/repos/{slug}", timeout=8)
            gh = json.loads(meta_raw.decode("utf-8"))
            repo_line = (
                f"- Repo {slug}: stars={gh.get('stargazers_count')}, forks={gh.get('forks_count')}, "
                f"pushed_at={gh.get('pushed_at')}, description={gh.get('description')}"
            )
            default_branch = gh.get("default_branch") or "main"
        except Exception:
            default_branch = "main"

        try:
            cm_raw = _http_get_bytes(
                f"https://api.github.com/repos/{slug}/commits?since={since_iso}&per_page=100",
                timeout=8,
            )
            cmts = json.loads(cm_raw.decode("utf-8"))
            if isinstance(cmts, list):
                c4w = len(cmts)
                for c in cmts:
                    login = ((c.get("author") or {}).get("login") or "").strip().lower()
                    email = (((c.get("commit") or {}).get("author") or {}).get("email") or "").strip().lower()
                    ident = login or email
                    if ident and "bot" not in ident:
                        authors.add(ident)
        except Exception:
            pass

        try:
            rm_raw = _http_get_bytes(
                f"https://raw.githubusercontent.com/{slug}/{default_branch}/README.md",
                timeout=7,
            )
            rm = rm_raw[:12_000].decode("utf-8", errors="replace")
        except Exception:
            pass

        return repo_line, c4w, authors, rm

    with ThreadPoolExecutor(max_workers=3) as pool:
        for repo_line, c4w, authors, rm in pool.map(_inspect_repo, slugs[:3]):
            lines.append(f"{repo_line} | commits_28d={c4w} | unique_committers_28d={len(authors)}")
            total_commits_4w += c4w
            unique_authors.update(authors)
            if rm and not readme_excerpt:
                readme_excerpt = rm

    # If CoinGecko listed an older/archived repo (0 recent commits), inspect top recently-pushed repos in the GitHub org
    if total_commits_4w == 0 and slugs:
        org = slugs[0].split("/")[0]
        try:
            org_raw = _http_get_bytes(f"https://api.github.com/orgs/{org}/repos?sort=pushed&per_page=5", timeout=8)
            org_repos = json.loads(org_raw.decode("utf-8"))
            extra_slugs = [
                str(r.get("full_name"))
                for r in org_repos
                if isinstance(r, dict) and r.get("full_name") and r.get("full_name") not in slugs
            ][:3]
            if extra_slugs:
                with ThreadPoolExecutor(max_workers=3) as pool:
                    for repo_line, c4w, authors, _rm in pool.map(_inspect_repo, extra_slugs):
                        lines.append(f"{repo_line} | commits_28d={c4w} | unique_committers_28d={len(authors)}")
                        total_commits_4w += c4w
                        unique_authors.update(authors)
                for es in extra_slugs:
                    if es not in slugs:
                        slugs.append(es)
        except Exception:
            pass

    summary = "\n".join(lines)
    if readme_excerpt:
        summary += f"\n\n=== CORE REPOSITORY README EXCERPT ===\n{readme_excerpt[:8_000]}"
    return summary, total_commits_4w, len(unique_authors), slugs[:4]


def _fetch_snapshot_governance(space_hints: List[str], name_hint: str) -> Tuple[str, List[str]]:
    """Queries Snapshot GraphQL API for DAO governance status and recent proposals."""
    candidate_spaces: List[str] = []
    for h in space_hints:
        s = (h or "").strip().lower().removeprefix("snapshot:")
        if s and s not in candidate_spaces:
            candidate_spaces.append(s)

    base = re.sub(r"[^a-z0-9]", "", (name_hint or "").lower())
    if base:
        for suffix in (f"{base}.eth", f"{base}dao.eth", f"{base}-dao.eth", f"{base}.xyz"):
            if suffix not in candidate_spaces:
                candidate_spaces.append(suffix)

    proposals_found: List[Dict[str, Any]] = []
    matched_space_id = ""
    space_followers = 0

    try:
        # 1. Try explicit candidate space IDs
        res = _http_post_json(
            "https://hub.snapshot.org/graphql",
            {
                "query": (
                    "query($spaces:[String]){"
                    "proposals(first:8, where:{space_in:$spaces}, orderBy:\"created\", orderDirection:desc){"
                    "id title state votes scores_total created space{id name followersCount}"
                    "}}"
                ),
                "variables": {"spaces": candidate_spaces[:8]},
            },
            timeout=10,
        )
        proposals_found = (res.get("data") or {}).get("proposals") or []

        # 2. If no direct hit, search Snapshot spaces by name/symbol substring
        if not proposals_found and name_hint:
            sp_res = _http_post_json(
                "https://hub.snapshot.org/graphql",
                {
                    "query": (
                        "query($s:String){spaces(first:5, where:{name_contains:$s}){id name followersCount}}"
                    ),
                    "variables": {"s": name_hint},
                },
                timeout=10,
            )
            spaces = (sp_res.get("data") or {}).get("spaces") or []
            if spaces:
                spaces_sorted = sorted(spaces, key=lambda x: int(x.get("followersCount") or 0), reverse=True)
                top_id = spaces_sorted[0]["id"]
                space_followers = int(spaces_sorted[0].get("followersCount") or 0)
                p_res = _http_post_json(
                    "https://hub.snapshot.org/graphql",
                    {
                        "query": (
                            "query($sp:String){proposals(first:6, where:{space:$sp}, orderBy:\"created\", orderDirection:desc){"
                            "title state votes scores_total created space{id name followersCount}}}"
                        ),
                        "variables": {"sp": top_id},
                    },
                    timeout=10,
                )
                proposals_found = (p_res.get("data") or {}).get("proposals") or []
    except Exception:
        pass

    if not proposals_found:
        return "", []

    sp_info = proposals_found[0].get("space") or {}
    matched_space_id = str(sp_info.get("id") or "")
    space_followers = int(sp_info.get("followersCount") or space_followers or 0)
    lines = [
        f"Snapshot DAO Space: {sp_info.get('name', matched_space_id)} (`{matched_space_id}`) | Followers: {space_followers:,}",
        "Recent Governance Proposals:",
    ]
    titles = []
    for p in proposals_found[:5]:
        dt = datetime.datetime.fromtimestamp(int(p.get("created") or 0), tz=datetime.timezone.utc).strftime("%Y-%m-%d")
        t_str = f"[{dt} | {p.get('state')} | {p.get('votes')} votes] {p.get('title')}"
        lines.append(f"- {t_str}")
        titles.append(str(p.get("title") or ""))

    return "\n".join(lines), ([matched_space_id] if matched_space_id else [])


def _fetch_defillama_security_and_tvl(coin_id: str, name: str, base_sym: str) -> Tuple[str, List[str]]:
    """
    Fetches protocol audit links, audit count, staking TVL, governance space hint,
    and verified exploit history from DeFiLlama (`protocols`, `protocol/{slug}`, `hacks`).
    """
    lines: List[str] = []
    gov_hints: List[str] = []
    name_low = (name or "").lower()
    sym_low = (base_sym or "").lower()
    gecko_low = (coin_id or "").lower()

    def _get_protocols():
        return json.loads(_http_get_bytes("https://api.llama.fi/protocols", timeout=12).decode("utf-8"))

    def _get_hacks():
        return json.loads(_http_get_bytes("https://api.llama.fi/hacks", timeout=12).decode("utf-8"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_p = pool.submit(_get_protocols)
        f_h = pool.submit(_get_hacks)
        try:
            prots = f_p.result(timeout=14)
        except Exception:
            prots = []
        try:
            hacks = f_h.result(timeout=14)
        except Exception:
            hacks = []

    matched = [
        p for p in prots
        if (gecko_low and str(p.get("gecko_id") or "").lower() == gecko_low)
        or (str(p.get("symbol") or "").lower() == sym_low and sym_low)
        or (name_low and str(p.get("name") or "").lower() == name_low)
    ]

    if matched:
        matched.sort(key=lambda x: float(x.get("tvl") or 0.0), reverse=True)
        top = matched[0]
        slug = str(top.get("slug") or "")
        tvl_usd = float(top.get("tvl") or 0.0)
        audits_cnt = top.get("audits")
        audit_links = top.get("audit_links") or []
        audit_note = top.get("audit_note") or ""
        gov_ids = top.get("governanceID") or []
        if isinstance(gov_ids, list):
            gov_hints.extend([str(g) for g in gov_ids if g])

        lines.append(
            f"- DeFiLlama Protocol Match (`{slug}`): TVL=${tvl_usd:,.0f} USD | "
            f"Audited Tier/Count={audits_cnt or 'N/A'} | Audit Links={', '.join(audit_links[:4]) or 'None listed'}"
        )
        if audit_note:
            lines.append(f"- DeFiLlama Audit Note: {audit_note}")

        try:
            pdet = json.loads(_http_get_bytes(f"https://api.llama.fi/protocol/{slug}", timeout=10).decode("utf-8"))
            chain_tvls = pdet.get("currentChainTvls") or {}
            staking_tvl = float(chain_tvls.get("staking") or 0.0)
            if staking_tvl > 0:
                lines.append(f"- On-Chain Native Token Staking Value Locked (DeFiLlama): ${staking_tvl:,.0f} USD")
        except Exception:
            pass

    # Cross-reference DeFiLlama Hacks DB
    matched_hacks = [
        h for h in hacks
        if (name_low and name_low in str(h.get("name") or "").lower())
        or (gecko_low and gecko_low == str(h.get("defillamaId") or "").lower())
    ]
    if matched_hacks:
        for h in matched_hacks[:4]:
            ts = h.get("date")
            dt_str = (
                datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc).strftime("%Y-%m-%d")
                if isinstance(ts, (int, float))
                else str(ts)
            )
            lines.append(
                f"- Historical Exploit Incident: {h.get('name')} ({dt_str}) | "
                f"Amount=${float(h.get('amount') or 0):,.0f} | Technique={h.get('technique')} | Classification={h.get('classification')}"
            )
    else:
        lines.append("- DeFiLlama Hacks Database Cross-Check: 0 historical protocol exploits recorded.")

    return ("=== SECURITY AUDITS, STAKING & EXPLOIT DB (DEFILLAMA) ===\n" + "\n".join(lines)) if lines else "", gov_hints


def fetch_complete_crypto_document_bundle(
    symbol: str,
) -> Tuple[Optional[str], Optional[bytes], Dict[str, Any]]:
    """
    Fetches ALL documentary pillars for a cryptoasset:
      1. CoinGecko Protocol Metadata + Official Whitepaper / Docs (PDF bytes or HTML text)
      2. Live GitHub Engineering Telemetry (28d commits, unique active devs, README.md)
      3. DeFiLlama Protocol Audits, Staking TVL & Exploit DB
      4. Snapshot GraphQL DAO Governance Proposals
    Returns `(text_context, optional_whitepaper_pdf_bytes, metadata_dict)`.
    """
    raw_sym = (symbol or "").strip().upper()
    base_sym = raw_sym.replace("-USD", "") if raw_sym.endswith("-USD") else raw_sym
    norm_sym = raw_sym if "-" in raw_sym else f"{base_sym}-USD"

    try:
        q = urllib.parse.quote(base_sym)
        search_raw = _http_get_bytes(f"https://api.coingecko.com/api/v3/search?query={q}", timeout=12)
        coins = json.loads(search_raw.decode("utf-8")).get("coins", [])
        if not coins:
            return None, None, {"error": f"Token '{base_sym}' not found on CoinGecko."}
        exact = [c for c in coins if str(c.get("symbol", "")).upper() == base_sym]
        chosen = exact[0] if exact else coins[0]
        coin_id = chosen["id"]

        detail_raw = _http_get_bytes(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false",
            timeout=15,
        )
        detail = json.loads(detail_raw.decode("utf-8"))
    except Exception as exc:
        return None, None, {"error": f"Failed CoinGecko metadata for {base_sym}: {exc}"}

    name = str(detail.get("name") or base_sym)
    desc = re.sub(r"<[^>]+>", " ", str((detail.get("description") or {}).get("en", "")))
    links = detail.get("links", {}) or {}
    wp_url = str(links.get("whitepaper") or "").strip()
    homepage_list = [u for u in (links.get("homepage") or []) if u]
    repos = [r for r in ((links.get("repos_url") or {}).get("github") or []) if r]
    dev_data = detail.get("developer_data", {}) or {}
    mkt_data = detail.get("market_data", {}) or {}

    # Detect any snapshot links embedded inside CoinGecko announcement/chat/blockchain links
    cg_snapshot_hints: List[str] = []
    for url_group in (
        links.get("chat_url") or [],
        links.get("announcement_url") or [],
        links.get("official_forum_url") or [],
        homepage_list,
    ):
        for u in url_group:
            m_snap = re.search(r"snapshot\.org/(?:#/)?([a-zA-Z0-9\-\.]+)", str(u))
            if m_snap:
                cg_snapshot_hints.append(m_snap.group(1))

    # Parallel fetch: GitHub commits/devs/README, DeFiLlama security/hacks/TVL, Whitepaper PDF/HTML
    def _fetch_wp() -> Tuple[Optional[bytes], str]:
        target_url = wp_url or (homepage_list[0] if homepage_list else "")
        if not target_url:
            return None, ""
        # Convert GitHub UI `/blob/` URLs into raw downloadable URLs so PDFs aren't HTML wrappers
        m_gh_blob = re.match(r"https?://github\.com/([^/]+/[^/]+)/blob/(.+)", target_url)
        if m_gh_blob:
            target_url = f"https://raw.githubusercontent.com/{m_gh_blob.group(1)}/{m_gh_blob.group(2)}"
        try:
            doc_bytes = _http_get_bytes(target_url, timeout=15)
            # Validate genuine PDF magic header (never trust filename extension alone)
            if doc_bytes.lstrip()[:4] == b"%PDF":
                if len(doc_bytes) <= 8_000_000:
                    return doc_bytes, ""
                return None, ""
            return None, _strip_html_to_text(doc_bytes[:1_500_000].decode("utf-8", errors="replace"))[:40_000]
        except Exception:
            return None, ""

    with ThreadPoolExecutor(max_workers=3) as pool:
        f_gh = pool.submit(_fetch_github_engineering_metrics, repos)
        f_llama = pool.submit(_fetch_defillama_security_and_tvl, coin_id, name, base_sym)
        f_wp = pool.submit(_fetch_wp)

        gh_summary, gh_commits_4w, gh_active_devs, repo_slugs = f_gh.result()
        llama_text, llama_gov_hints = f_llama.result()
        wp_pdf_bytes, wp_text_excerpt = f_wp.result()

    # Now query Snapshot DAO governance using combined hints
    snap_text, snap_spaces = _fetch_snapshot_governance(llama_gov_hints + cg_snapshot_hints, name)

    # Prefer direct GitHub 28d measurement, fall back to CoinGecko developer_data if GitHub empty
    commits_4w_val = gh_commits_4w if gh_commits_4w > 0 else (dev_data.get("commit_count_4_weeks") or 0)
    devs_monthly_val = gh_active_devs if gh_active_devs > 0 else (dev_data.get("pull_request_contributors") or 0)

    circ_sup = mkt_data.get("circulating_supply")
    tot_sup = mkt_data.get("total_supply") or mkt_data.get("max_supply")
    mcap_usd = (mkt_data.get("market_cap") or {}).get("usd")

    sources_fetched: List[str] = ["CoinGecko Protocol & Tokenomics Metadata"]
    if wp_pdf_bytes is not None or wp_text_excerpt:
        sources_fetched.append("Official Whitepaper / Protocol Docs")
    if repo_slugs:
        sources_fetched.append(f"GitHub Live Engineering ({', '.join(repo_slugs)})")
    if snap_text:
        sources_fetched.append(f"Snapshot DAO Governance ({', '.join(snap_spaces)})")
    if llama_text:
        sources_fetched.append("DeFiLlama Audits, Staking TVL & Hacks DB")

    context_sections: List[str] = [
        f"OFFICIAL MULTI-SOURCE CRYPTO PROTOCOL DOSSIER FOR {norm_sym} ({name}):\n"
        f"- Categories: {', '.join(detail.get('categories') or [])}\n"
        f"- Homepage: {', '.join(homepage_list[:2])}\n"
        f"- Whitepaper URL: {wp_url or 'N/A'}\n"
        f"- Market Cap (USD): {f'${float(mcap_usd):,.0f}' if mcap_usd else 'N/A'} | "
        f"Circulating Supply: {circ_sup or 'N/A'} | Total/Max Supply: {tot_sup or 'N/A'}\n"
        f"- Measured 28d Core Commits (GitHub / CG): {commits_4w_val} | Measured Monthly Active Devs: {devs_monthly_val}\n"
        f"- Core GitHub Repos: {', '.join(repo_slugs) or 'N/A'}\n",
        f"=== PROTOCOL OVERVIEW ===\n{desc[:10_000]}",
    ]
    if gh_summary:
        context_sections.append(f"=== GITHUB LIVE ENGINEERING TELEMETRY ===\n{gh_summary}")
    if snap_text:
        context_sections.append(f"=== DAO GOVERNANCE (SNAPSHOT) ===\n{snap_text}")
    if llama_text:
        context_sections.append(llama_text)
    if wp_text_excerpt:
        context_sections.append(f"=== WHITEPAPER / DOCS EXCERPT ===\n{wp_text_excerpt}")

    candidate_doc_url = wp_url or (homepage_list[0] if homepage_list else f"https://www.coingecko.com/en/coins/{coin_id}")
    meta = {
        "symbol": norm_sym,
        "name": name,
        "source_url": candidate_doc_url,
        "whitepaper_pdf_attached": wp_pdf_bytes is not None,
        "github_repos": ", ".join(repo_slugs),
        "commits_4w": commits_4w_val,
        "active_devs_monthly": devs_monthly_val,
        "snapshot_spaces": snap_spaces,
        "sources_fetched": sources_fetched,
        # Supplement with Google Search grounding if key whitepaper/audit/lockup/governance info is thin
        "needs_search_enrichment": not (snap_text and (wp_pdf_bytes is not None or len(wp_text_excerpt) > 1500)),
    }
    return "\n\n".join(context_sections), wp_pdf_bytes, meta


def fetch_crypto_whitepaper_and_github(symbol: str) -> Tuple[Optional[str], Optional[bytes], Dict[str, Any]]:
    """Backward-compatible wrapper returning the complete multi-source crypto bundle."""
    return fetch_complete_crypto_document_bundle(symbol=symbol)

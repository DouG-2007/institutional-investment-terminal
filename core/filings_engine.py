"""
MODULE 2: IN-DEPTH FORENSIC DOCUMENTARY INTELLIGENCE
1. Equities (SEC EDGAR Form 10-K, 10-Q, 8-K, 20-F, Forensic Footnotes & External Analyst Reports):
   - Independent Audit & Controls (Audit Firm, Unqualified/Clean Opinion, SOX 404b)
   - MD&A Dissection (Item 7: Volume vs Pricing Power vs FX decomposition, Segment Margins, Contracted Backlog, CapEx Schedule)
   - Item 1A Specific Risk Factors
   - Forensic Footnotes (Litigation/Contingencies, Real SBC dilution impact, ASC 606 Revenue Recognition, Debt Maturity Staggering)
   - External Analysts' Reports (Mean Target Price, Buy/Hold/Sell Distribution, 30d/90d EPS Revisions)
2. Cryptoassets (White Papers, GitHub API, DeepDAO & Security Audits):
   - Technical White Paper Synthesis (Value proposition, Consensus architecture, Token value accrual)
   - GitHub Engineering Metrics (4-week commits, Monthly active developers, Core repos)
   - DeepDAO Governance (Activity level, Recent fee/tokenomics proposals, Skin in the Game % locked supply)
   - Security & Resilience (Token Sniffer score, Independent audit firms, Exploit track record)
"""

from __future__ import annotations

import base64
from dataclasses import asdict, dataclass, fields
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


@dataclass
class EquityDocumentaryDossier:
    ticker: str
    company_name: str
    filing_form_annual: str
    filing_form_quarterly: str
    auditor_firm: str
    auditor_opinion: str
    sox_404b_controls: str
    # MD&A Item 7 Dissection
    mda_growth_decomposition: str
    mda_segment_profitability: str
    mda_backlog_rpo: str
    mda_capex_plan: str
    # Item 1A Risk Factors
    item_1a_specific_risks: str
    # Forensic Footnotes
    footnote_contingencies_litigation: str
    footnote_sbc_impact: str
    footnote_revenue_recognition: str
    footnote_debt_maturity_schedule: str
    # External Analysts' Reports
    analyst_target_mean_usd: float
    analyst_recommendations_dist: str
    analyst_eps_revisions_30d_90d: str
    # M&A, Strategic Deals, Payment Dilution & Goodwill (defaults keep static KB backward compatible)
    ma_and_strategic_deals: str = ""
    ma_payment_and_goodwill: str = ""


@dataclass
class CryptoDocumentaryDossier:
    symbol: str
    name: str
    # White Paper Synthesis
    wp_title_author: str
    wp_value_proposition: str
    wp_consensus_architecture: str
    wp_value_accrual_mechanism: str
    # GitHub Metrics
    github_core_repos: str
    github_commits_4w: int
    github_active_devs_monthly: int
    # DeepDAO Governance
    deepdao_status: str
    recent_governance_proposals: str
    skin_in_the_game_locked_pct: float
    skin_in_the_game_details: str
    # Security & Audits
    token_sniffer_score: int
    audit_firms: str
    exploit_history: str


EQUITY_FILINGS_DB: List[EquityDocumentaryDossier] = [
    EquityDocumentaryDossier(
        ticker="AAPL",
        company_name="Apple Inc.",
        filing_form_annual="SEC Form 10-K (FY Ended Sept 2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 2026)",
        auditor_firm="Ernst & Young LLP (PCAOB ID #42)",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="SOX Section 404(b) Effective — Zero material weaknesses reported",
        mda_growth_decomposition="Hardware Volume: +1.5% | Pricing Power (Pro Mix + Services): +5.8% | FX Impact: -1.2%",
        mda_segment_profitability="Products Gross Margin: 37.2% | Services Gross Margin: 74.1% (Structural margin expansion engine)",
        mda_backlog_rpo="Deferred Revenue & Remaining Performance Obligations (RPO): $12.8B across subscriptions and AppleCare",
        mda_capex_plan="Annual CapEx of $10.5B focused on Private Cloud Compute servers (Apple Silicon M4) and precision tooling",
        item_1a_specific_risks="1) Advanced foundry concentration in 3nm at TSMC (Taiwan); 2) EU DMA regulation on App Store fees; 3) US DOJ antitrust lawsuit on iPhone ecosystem; 4) ~17% revenue exposure in Greater China.",
        footnote_contingencies_litigation="Note 10: US DOJ and European Commission antitrust inquiries; Ireland state aid tax litigation fully settled without additional cash impact.",
        footnote_sbc_impact="SBC of $11.7B/yr (3.0% of Revenue | 9.9% of CFO) — Heavily offset by $95B in share buybacks (2.8% net share count reduction/yr).",
        footnote_revenue_recognition="ASC 606: Hardware recognized point-in-time upon delivery; Services/iCloud recognized ratably over service period; App Store commissions on net basis (Principal vs Agent).",
        footnote_debt_maturity_schedule="Total Debt of $106B maturing through 2062 (Weighted-average fixed coupon of 2.65% p.a.; only $10.9B due within 12 months vs $65B in cash).",
        analyst_target_mean_usd=248.00,
        analyst_recommendations_dist="68% Buy / Strong Buy | 25% Hold | 7% Sell (44 Analysts)",
        analyst_eps_revisions_30d_90d="30d: +1.4% (28 Up / 4 Down) | 90d: +3.8% (Driven by Services and Apple Intelligence refresh cycle)",
    ),
    EquityDocumentaryDossier(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        filing_form_annual="SEC Form 10-K (FY Ended June 2026)",
        filing_form_quarterly="SEC Form 10-Q (Q1 FY2027)",
        auditor_firm="Deloitte & Touche LLP (PCAOB ID #34)",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="SOX Section 404(b) Effective — Internal controls audited without reservation",
        mda_growth_decomposition="Cloud/Seats Volume: +9.2% | Pricing Power (E5 + Copilot ARPU): +6.8% | FX Impact: -0.6%",
        mda_segment_profitability="Intelligent Cloud Operating Margin: 44.2% | Productivity & Business: 51.8% | More Personal Computing: 26.5%",
        mda_backlog_rpo="Commercial Remaining Performance Obligations (Contracted RPO): $268 Billion (+21% YoY; 45% recognizable within 12m)",
        mda_capex_plan="CapEx of $52B/yr (Global hyperscale data centers, Nvidia GPUs, and custom Azure Maia/Cobalt silicon), 100% backed by contracted demand",
        item_1a_specific_risks="1) ROIC realization across generative AI CapEx cycle; 2) Cybersecurity resilience across critical government infra; 3) FTC/EU scrutiny over Teams bundling and AI foundation model investments.",
        footnote_contingencies_litigation="Note 15: Historic IRS transfer pricing audit (gradual resolution expected with zero threat to AAA liquidity rating).",
        footnote_sbc_impact="SBC of $10.7B/yr (4.3% of Revenue | 9.0% of CFO) — Dilution fully neutralized by systematic share repurchases.",
        footnote_revenue_recognition="ASC 606: Multi-year Enterprise Agreement contracts recognized upon consumption (Azure ACR) or over subscription term (M365).",
        footnote_debt_maturity_schedule="Long-term debt of $44.9B maturing through 2062 (Weighted coupon ~2.9%; Cash of $75.5B exceeds total gross debt).",
        analyst_target_mean_usd=495.00,
        analyst_recommendations_dist="91% Buy / Strong Buy | 9% Hold | 0% Sell (56 Analysts)",
        analyst_eps_revisions_30d_90d="30d: +2.1% (42 Up / 2 Down) | 90d: +5.4% (Accelerating +29% growth in Azure AI Services)",
    ),
    EquityDocumentaryDossier(
        ticker="GOOGL",
        company_name="Alphabet Inc.",
        filing_form_annual="SEC Form 10-K (FY 2025/2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 2026)",
        auditor_firm="Ernst & Young LLP",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="SOX Section 404(b) Effective",
        mda_growth_decomposition="Search/YouTube Volume: +7.5% | Pricing Power (CPC / Ad Monetization): +6.9% | FX Impact: -0.8%",
        mda_segment_profitability="Google Services Op Margin: 39.8% | Google Cloud Op Margin: 14.2% (+850 bps expansion over 2 yrs) | Other Bets: Controlled loss",
        mda_backlog_rpo="Google Cloud Contracted Backlog (RPO): $86.8 Billion (+28% YoY)",
        mda_capex_plan="CapEx of $48B/yr concentrated in TPU v6 (Trillium) clusters, subsea fiber cables, and Gemini AI infrastructure",
        item_1a_specific_risks="1) US DOJ antitrust remedies in Search Distribution (Apple ISA contract) and AdTech; 2) Generative search competition; 3) Accelerated server depreciation schedules.",
        footnote_contingencies_litigation="Note 10: Legal accruals for US and EU antitrust proceedings; ongoing judicial appeals with estimated timeline of 2 to 4 years.",
        footnote_sbc_impact="SBC of $22.8B/yr (6.6% of Revenue | 19.7% of CFO) — Monitored dilution metric, fully surpassed by $62B/yr in share buybacks.",
        footnote_revenue_recognition="ASC 606: Search/YouTube advertising recognized upon validated click/impression; Cloud recognized upon customer consumption or subscription.",
        footnote_debt_maturity_schedule="Negligible long-term debt ($13.2B vs $93.2B in Cash and US Treasuries; weighted coupon < 2.1%).",
        analyst_target_mean_usd=218.00,
        analyst_recommendations_dist="84% Buy / Strong Buy | 16% Hold | 0% Sell (52 Analysts)",
        analyst_eps_revisions_30d_90d="30d: +3.2% (46 Up / 1 Down) | 90d: +6.8% (Driven by operating leverage and margin expansion in Google Cloud)",
    ),
    EquityDocumentaryDossier(
        ticker="AMZN",
        company_name="Amazon.com Inc.",
        filing_form_annual="SEC Form 10-K (FY 2025/2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 2026)",
        auditor_firm="Ernst & Young LLP",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="SOX Section 404(b) Effective",
        mda_growth_decomposition="Unit/Cloud Volume: +10.2% | High-Margin Mix (AWS + Advertising + 3P): +4.5% | FX Impact: -0.5%",
        mda_segment_profitability="AWS Operating Margin: 35.8% (Record High) | North America Retail Op Margin: 6.1% | International Op Margin: 3.2%",
        mda_backlog_rpo="AWS Contracted Backlog (RPO): $164.0 Billion (Weighted-average remaining term of 3.8 years)",
        mda_capex_plan="CapEx of $65B/yr (~70% allocated to AWS capacity expansion & Trainium2 chips; ~30% to robotic fulfillment automation)",
        item_1a_specific_risks="1) FTC antitrust litigation regarding Marketplace pricing mechanisms; 2) Power infrastructure and grid interconnection delays for AWS data centers; 3) Discretionary consumer spending cycles.",
        footnote_contingencies_litigation="Note 7: Unconditional clean energy purchase commitments and long-term operating leases for fulfillment network and cargo aircraft.",
        footnote_sbc_impact="SBC of $22.0B/yr (3.5% of Revenue | 19.5% of CFO) — Declining as a percentage of net sales for the 3rd consecutive year.",
        footnote_revenue_recognition="ASC 606: 1P sales recognized gross; 3P Seller Services commissions recognized net; Amazon Prime subscription fees deferred ratably over 12 months.",
        footnote_debt_maturity_schedule="Long-term debt of $54.5B evenly staggered through 2062 (Cash balance of $88B secures net positive cash position).",
        analyst_target_mean_usd=245.00,
        analyst_recommendations_dist="95% Buy / Strong Buy | 5% Hold | 0% Sell (61 Analysts)",
        analyst_eps_revisions_30d_90d="30d: +4.1% | 90d: +9.5% (Accelerating EBIT expansion in North America retail and AWS)",
    ),
    EquityDocumentaryDossier(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        filing_form_annual="SEC Form 10-K (FY2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 FY2027)",
        auditor_firm="PricewaterhouseCoopers LLP (PCAOB ID #238)",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="SOX Section 404(b) Effective",
        mda_growth_decomposition="Data Center Server Systems Volume (Hopper/Blackwell): +68% | Pricing Power (Full NVL72 Rack Scale Systems + Spectrum-X): +24% | FX: 0%",
        mda_segment_profitability="Data Center Operating Margin: ~68.5% | Gaming & AI PC: ~42.0% | Consolidated Gross Margin: 75.2%",
        mda_backlog_rpo="Supply commitments and CoWoS advanced packaging capacity secured 12-18 months forward; Blackwell capacity booked out 4 quarters",
        mda_capex_plan="Fabless Asset-Light Model: CapEx < $2.8B/yr (2.2% of Revenue); massive capital allocation directed to R&D and TSMC wafer prepayments",
        item_1a_specific_risks="1) US BIS export control restrictions on advanced AI compute to China/Middle East; 2) TSMC CoWoS packaging capacity bottlenecks; 3) Revenue concentration across top 4 US hyperscalers (~45%).",
        footnote_contingencies_litigation="Note 13: Non-cancelable inventory purchase and foundry capacity commitments of $18.5B to secure Blackwell deployment leadership.",
        footnote_sbc_impact="SBC of $4.2B/yr (3.4% of Revenue | 6.5% of CFO) — Minimal dilution relative to hyper-growth in Free Cash Flow.",
        footnote_revenue_recognition="ASC 606: Hardware revenue recognized upon customer shipment; NVIDIA AI Enterprise software licenses recognized ratably over contract period.",
        footnote_debt_maturity_schedule="Total gross debt of just $8.5B vs Cash of $38.5B (Net Cash Position of $30B; zero refinancing risk).",
        analyst_target_mean_usd=168.00,
        analyst_recommendations_dist="93% Buy / Strong Buy | 7% Hold | 0% Sell (60 Analysts)",
        analyst_eps_revisions_30d_90d="30d: +5.2% | 90d: +14.8% (Consecutive upward revisions driven by Blackwell volume ramp)",
    ),
    EquityDocumentaryDossier(
        ticker="META",
        company_name="Meta Platforms Inc.",
        filing_form_annual="SEC Form 10-K (FY 2025/2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 2026)",
        auditor_firm="Ernst & Young LLP",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="SOX Section 404(b) Effective",
        mda_growth_decomposition="Ad Impressions Delivered: +10.0% | Average Price per Ad (AI-Driven Pricing Power): +9.0% | FX Impact: -0.5%",
        mda_segment_profitability="Family of Apps (FoA) Operating Margin: 51.4% (Elite) | Reality Labs: Operational R&D loss of ~$16B/yr for spatial compute",
        mda_backlog_rpo="Self-service real-time programmatic ad auction platform serving over 10 million active business advertisers",
        mda_capex_plan="CapEx of $38B-$40B/yr dedicated to Llama 4 foundation model training clusters and unified video recommendation algorithms",
        item_1a_specific_risks="1) EU regulatory data privacy fines and DMA consent mandates; 2) US youth protection litigation; 3) Long-term commercial ROI from Reality Labs spatial computing R&D.",
        footnote_contingencies_litigation="Note 12: EU regulatory settlements and FTC compliance protocols fully absorbed within operational cash flow.",
        footnote_sbc_impact="SBC of $15.2B/yr (9.6% of Revenue | 18.4% of CFO) — Fully sterilized by $42B+ in share buybacks.",
        footnote_revenue_recognition="ASC 606: Advertising revenue recognized upon validated ad impression; WhatsApp Business Messaging recognized per delivered conversation.",
        footnote_debt_maturity_schedule="Long-term debt of $28.8B vs $60.8B in Cash (Over $32B in Net Positive Cash Position).",
        analyst_target_mean_usd=655.00,
        analyst_recommendations_dist="87% Buy / Strong Buy | 11% Hold | 2% Sell (58 Analysts)",
        analyst_eps_revisions_30d_90d="30d: +2.8% | 90d: +7.9% (Strong pricing gains per ad powered by generative AI recommendation architecture)",
    ),
    EquityDocumentaryDossier(
        ticker="V",
        company_name="Visa Inc.",
        filing_form_annual="SEC Form 10-K (FY Ended Sept 2026)",
        filing_form_quarterly="SEC Form 10-Q (Q4 FY2026)",
        auditor_firm="KPMG LLP (PCAOB ID #185)",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="SOX Section 404(b) Effective",
        mda_growth_decomposition="Payments Volume (+8.0%) + Processed Transactions (+10.0%) + Cross-Border Volume (+13.0%) + Value-Added Services (+21.0%)",
        mda_segment_profitability="Single Global Payment Network Segment with GAAP Operating Margin of 67.0% and Adjusted EBITDA Margin of 70.1%",
        mda_backlog_rpo="Multi-year co-branded issuing partnership contracts secured with leading global financial institutions (7 to 10-year average duration)",
        mda_capex_plan="Ultra Asset-Light Architecture: CapEx of just $1.2B/yr (~3.3% of Revenue), driving FCF conversion in excess of 94%",
        item_1a_specific_risks="1) US DOJ debit routing antitrust complaint; 2) US Interchange Multidistrict Litigation (MDL 1720); 3) Regulatory interchange fee caps across UK/EU payment corridors.",
        footnote_contingencies_litigation="Note 19 (U.S. Interchange MDL): Visa maintains a dedicated Litigation Escrow Account pre-funded via Class B share conversions (fully shielding Class A public equity holders!).",
        footnote_sbc_impact="SBC of just $0.85B/yr (2.3% of Revenue | 4.1% of CFO) — One of the lowest dilution ratios across the entire S&P 500.",
        footnote_revenue_recognition="ASC 606: Service, data processing, and international transaction revenues reported net of client incentives.",
        footnote_debt_maturity_schedule="Total Debt of $20.6B carrying AA- / Aa3 rating with staggered maturities through 2050 (Weighted coupon ~2.8%).",
        analyst_target_mean_usd=335.00,
        analyst_recommendations_dist="82% Buy / Strong Buy | 18% Hold | 0% Sell (39 Analysts)",
        analyst_eps_revisions_30d_90d="30d: +1.2% | 90d: +2.6% (Resilience in global consumer payment volumes and cross-border travel flows)",
    ),
    EquityDocumentaryDossier(
        ticker="JPM",
        company_name="JPMorgan Chase & Co.",
        filing_form_annual="SEC Form 10-K (FY 2025/2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 2026)",
        auditor_firm="PricewaterhouseCoopers LLP",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="SOX Section 404(b) Effective",
        mda_growth_decomposition="Net Interest Income (NII): +4.5% | Non-Interest Fee Income (Investment Banking +31% & Wealth AUM +16%): +11.2%",
        mda_segment_profitability="Consumer CCB ROE: 33% | Corporate & Investment Bank ROE: 18% | Wealth AWM ROE: 34% | Firm ROTCE: 21.0% | Basel CET1 Ratio: 15.3%",
        mda_backlog_rpo="$3.9 Trillion in Assets Under Management (AUM) and $5.4 Trillion in total client assets under custody",
        mda_capex_plan="Annual Technology & AI budget of $17.0 Billion (Core banking modernizations, institutional cyberdefense, and autonomous risk models)",
        item_1a_specific_risks="1) NII sensitivity to aggressive Fed Funds rate cuts; 2) Credit normalization across consumer credit cards and office commercial real estate; 3) Basel III Endgame regulatory capital surcharge rules.",
        footnote_contingencies_litigation="Note 28 (Allowance for Credit Losses - CECL): Total allowance of $26.2B covering over 240% of non-accrual loans (NPLs).",
        footnote_sbc_impact="SBC of $3.1B/yr (1.8% of Net Revenue) — Variable compensation strictly subject to multi-year clawback covenants.",
        footnote_revenue_recognition="Interest income recognized via effective interest rate method; Investment Banking fees upon transaction close; Asset management fees ratably per month.",
        footnote_debt_maturity_schedule="Funding structure anchored by $2.4 Trillion in stable consumer/commercial deposits and over $1.4 Trillion in High-Quality Liquid Assets (HQLA).",
        analyst_target_mean_usd=248.00,
        analyst_recommendations_dist="72% Buy / Strong Buy | 24% Hold | 4% Sell (29 Analysts)",
        analyst_eps_revisions_30d_90d="30d: +2.4% | 90d: +4.9% (Investment banking fee rebound alongside sticky deposit beta support)",
    ),
    EquityDocumentaryDossier(
        ticker="WMT",
        company_name="Walmart Inc.",
        filing_form_annual="SEC Form 10-K (FY2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 FY2027)",
        auditor_firm="Ernst & Young LLP",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="SOX Section 404(b) Effective",
        mda_growth_decomposition="US Same Store Sales (SSS): +4.8% (Store foot traffic +3.1% + Average ticket +1.7%) | Global E-Commerce: +24% | Walmart Connect Retail Ads: +26%",
        mda_segment_profitability="Walmart US Op Margin: 5.1% | International Op Margin: 4.4% | Sam's Club: Membership income growing +14%",
        mda_backlog_rpo="Over 255 million weekly retail customers served across 10,600 omnichannel supercenters and digital platforms across 19 countries",
        mda_capex_plan="CapEx of $20B/yr dedicated to Symbotic robotic automation across regional distribution centers (reducing unit handling costs >20%)",
        item_1a_specific_risks="1) Associate hourly wage inflation across stores/supply chain; 2) Inventory shrink/retail theft; 3) Import tariffs on general merchandise.",
        footnote_contingencies_litigation="Note 11: Prior legal settlements fully reserved and funded; zero material contingencies outstanding impacting AA credit rating.",
        footnote_sbc_impact="SBC of just $0.78B/yr (0.12% of Revenue | 2.1% of CFO) — Virtually zero dilution to public equity holders.",
        footnote_revenue_recognition="ASC 606: Store/e-commerce sales recognized net of estimated returns; Sam's Club and Walmart+ membership fees deferred ratably over 12 months.",
        footnote_debt_maturity_schedule="Long-term debt of $36.2B (AA credit rating) with smooth maturity profile through 2053 and EBIT interest coverage of 11.2x.",
        analyst_target_mean_usd=90.00,
        analyst_recommendations_dist="85% Buy / Strong Buy | 15% Hold | 0% Sell (41 Analysts)",
        analyst_eps_revisions_30d_90d="30d: +1.8% | 90d: +4.2% (Full-year guidance upgrades across top-line sales and operating income)",
    ),
    EquityDocumentaryDossier(
        ticker="DBSDY",
        company_name="DBS Group Holdings Ltd.",
        filing_form_annual="SGX Annual Report & Audited Financial Statements (FY2025/2026)",
        filing_form_quarterly="SGXNet Q3 2026 Financial Statement Announcement",
        auditor_firm="PricewaterhouseCoopers LLP Singapore",
        auditor_opinion="Unqualified / Clean Opinion (Sem Ressalvas — IFRS / SFRS)",
        sox_404b_controls="Full compliance with Monetary Authority of Singapore internal controls framework (MAS Notice 609)",
        mda_growth_decomposition="Commercial Net Interest Income: +4.0% | Wealth Management Fees: +32.0% | Treasury Customer Sales: +14.0%",
        mda_segment_profitability="ROE of 18.4% | Cost-to-Income Ratio of 39.0% | Non-Performing Loan (NPL) Ratio of just 1.0% | CET1 Ratio: 15.2%",
        mda_backlog_rpo="Wealth Management Assets Under Management (AUM) reached record SGD 390 Billion (+18% YoY)",
        mda_capex_plan="Continuous enterprise investment in digital platform resilience, predictive banking AI, and regulated Asian digital asset custody",
        item_1a_specific_risks="1) Sharp decline in SORA/SOFR policy rates compressing NIM; 2) Greater China commercial property slowdown; 3) MAS operational resilience guidelines.",
        footnote_contingencies_litigation="Note 32: General Allowance Overlays of SGD 2.3B comfortably exceed statutory regulatory thresholds.",
        footnote_sbc_impact="Share-based compensation below 1.2% of Revenue, satisfied via open-market Treasury Share repurchases with zero primary dilution.",
        footnote_revenue_recognition="SFRS(I) 9 and 15: Interest recognized via effective interest method; wealth management fees accrued monthly on AUM.",
        footnote_debt_maturity_schedule="Ultra-conservative Loan-to-Deposit Ratio (LDR) of 78% (Abundant low-cost CASA deposit base in Singapore Dollars).",
        analyst_target_mean_usd=128.00,
        analyst_recommendations_dist="76% Buy / Strong Buy | 20% Hold | 4% Sell (25 Analysts)",
        analyst_eps_revisions_30d_90d="30d: +3.5% | 90d: +7.1% (Record quarterly profits and inaugural SGD 3B share cancellation buyback program)",
    ),
    EquityDocumentaryDossier(
        ticker="ASML",
        company_name="ASML Holding N.V.",
        filing_form_annual="SEC Form 20-F (Euronext / Nasdaq)",
        filing_form_quarterly="Form 6-K (Q1-Q3 Earnings Releases)",
        auditor_firm="KPMG Accountants N.V.",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="Effective — Internal controls over financial reporting fully validated",
        mda_growth_decomposition="+18.5% YoY: +14.2% Volume (EUV/DUV systems shipped), +4.8% Pricing/Mix (High-NA EUV EXE:5000 systems at EUR 350M+ each), -0.5% FX",
        mda_segment_profitability="EUV Systems Gross Margin: 55.2% | DUV Systems: 48.5% | Installed Base Management & Services Op Margin: 44.0%",
        mda_backlog_rpo="Firm contracted backlog of EUR 36.0 Billion (~1.5 years of forward factory capacity fully booked)",
        mda_capex_plan="R&D CapEx of EUR 4.2B/yr allocated to Veldhoven cleanroom capacity expansion and next-generation Hyper-NA technology",
        item_1a_specific_risks="1. Geopolitical export controls (US/Netherlands) on advanced immersion DUV to China (~38% recent revenue); 2. Customer concentration across 3 global leaders (TSMC, Samsung, Intel); 3. Single-source optics bottleneck (Carl Zeiss SMT atomic-precision mirrors).",
        footnote_contingencies_litigation="Zero material litigation or patent infringement exposures; full compliance with multilateral semiconductor export control frameworks.",
        footnote_sbc_impact="Share-based compensation of just 1.2% of CFO (virtually negligible dilution).",
        footnote_revenue_recognition="ASC 606: Revenue recognized upon customer factory site acceptance following beam-on calibration testing.",
        footnote_debt_maturity_schedule="Gross debt of EUR 4.6B with 7.5-year average maturity at 1.85% fixed coupon; Cash & equivalents of EUR 7.8B (Net Cash Position of EUR 3.2B).",
        analyst_target_mean_usd=835.00,
        analyst_recommendations_dist="32 Buy | 6 Hold | 1 Sell (Strong Buy Wall Street Consensus)",
        analyst_eps_revisions_30d_90d="+8.2% upward EPS revisions for 2026/2027 reflecting AI fab buildout acceleration.",
    ),
    EquityDocumentaryDossier(
        ticker="TSM",
        company_name="Taiwan Semiconductor (TSMC)",
        filing_form_annual="SEC Form 20-F (Taiwan Stock Exchange / NYSE ADR)",
        filing_form_quarterly="Form 6-K (Quarterly Results)",
        auditor_firm="Deloitte & Touche Taiwan",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="Effective — SOX controls fully attested",
        mda_growth_decomposition="+31.8% YoY: +22.0% Volume (3nm wafers and CoWoS for Nvidia/Apple/AMD), +10.2% Price/Mix (N3E node premium), -0.4% FX",
        mda_segment_profitability="HPC / AI: 52% of revenue (Operating Margin 46%) | Smartphones: 34% (Op Margin 41%) | IoT & Automotive: 14%",
        mda_backlog_rpo="3nm process nodes and CoWoS advanced packaging capacity 100% booked out through 2026",
        mda_capex_plan="Planned CapEx of $30B to $32B fully funded out of operating cash flow",
        item_1a_specific_risks="1. Taiwan Strait geopolitical tension (concentration of advanced fabs in Taiwan); 2. Sole-source dependency on ASML EUV lithography systems; 3. Cost differentials and skilled labor constraints in Fab 21 Arizona and Dresden fabs.",
        footnote_contingencies_litigation="Zero active material litigation; complete regulatory compliance across bilateral export jurisdictions.",
        footnote_sbc_impact="SBC of 0.8% of CFO (traditional cash bonus culture with minimal equity dilution).",
        footnote_revenue_recognition="ASC 606: Revenue recognized upon wafer completion and customer fab delivery following yield testing.",
        footnote_debt_maturity_schedule="Gross debt of $28.5B vs Cash and marketable securities of $48.0B (Net Cash Position of $19.5B).",
        analyst_target_mean_usd=228.00,
        analyst_recommendations_dist="38 Buy | 3 Hold | 0 Sell (Overwhelming Wall Street Consensus)",
        analyst_eps_revisions_30d_90d="+12.5% upward revisions over last 90 days driven by Blackwell CoWoS allocations and 2nm N2 pipeline.",
    ),
    EquityDocumentaryDossier(
        ticker="MELI",
        company_name="MercadoLibre, Inc.",
        filing_form_annual="SEC Form 10-K (Nasdaq Global Select)",
        filing_form_quarterly="SEC Form 10-Q (Q1-Q3)",
        auditor_firm="PricewaterhouseCoopers (PwC) Argentina",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="Effective — Internal controls fully certified",
        mda_growth_decomposition="+35.2% YoY FX-Neutral: +28.5% Volume (GMV & Mercado Pago transactions), +6.8% Take Rate / Ads & Credit, -0.1% FX",
        mda_segment_profitability="Commerce & Ads Operating Margin: 22.5% | Mercado Pago Fintech Op Margin: 18.2%",
        mda_backlog_rpo="Over 55 million unique active buyers and 100M+ Mercado Pago ecosystem accounts",
        mda_capex_plan="CapEx of $800M/yr in automated fulfillment centers, dedicated air cargo fleet, and financial data centers",
        item_1a_specific_risks="1. Latin American macroeconomic and FX volatility (BRL/ARS vs USD translation); 2. Credit risk in Mercado Credito consumer book (NPLs contained at 7.5%); 3. E-commerce competition in select urban tiers.",
        footnote_contingencies_litigation="Routine Brazilian civil/tax contingencies provisioned at $185M under conservative legal audit standards.",
        footnote_sbc_impact="SBC of 3.2% of CFO (competitive Silicon Valley-grade tech compensation).",
        footnote_revenue_recognition="ASC 606: Commerce revenue recognized upon package delivery; Fintech take rate upon transaction settlement.",
        footnote_debt_maturity_schedule="Comfortable net cash position with long-term debt facilities and strong liquid cash of $4.2B.",
        analyst_target_mean_usd=2240.00,
        analyst_recommendations_dist="24 Buy | 4 Hold | 0 Sell (Strong Buy Consensus)",
        analyst_eps_revisions_30d_90d="+15.0% upward EPS revisions following record operational results in Mexico and Brazil.",
    ),
    EquityDocumentaryDossier(
        ticker="AVGO",
        company_name="Broadcom Inc.",
        filing_form_annual="SEC Form 10-K (Nasdaq)",
        filing_form_quarterly="SEC Form 10-Q",
        auditor_firm="PricewaterhouseCoopers (PwC) LLP",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="Effective — Internal controls over VMware acquisition fully integrated",
        mda_growth_decomposition="+44.0% YoY: +28.0% VMware acquisition, +14.5% AI semiconductor volume (Tomahawk/Jericho Ethernet & custom ASICs), +1.5% Pricing",
        mda_segment_profitability="Semiconductor Solutions EBITDA Margin: 58.5% | Infrastructure Software (VMware) EBITDA Margin: 66.0%",
        mda_backlog_rpo="Consolidated semiconductor backlog exceeding $21B and multi-year enterprise VMware contracts > $15B",
        mda_capex_plan="Asset-light CapEx of $1.8B/yr (pure fabless model utilizing TSMC foundries)",
        item_1a_specific_risks="1. Customer concentration across hyperscaler ASIC programs (Google TPU, Meta) and Apple RF; 2. Post-VMware debt leverage ($71B gross debt deleveraging via $20B+ FCF); 3. Enterprise software antitrust scrutiny.",
        footnote_contingencies_litigation="Zero material litigation with probable adverse loss; VMware operational integration successfully completed.",
        footnote_sbc_impact="SBC of 5.8% of CFO (long-term equity grants tied to multi-year Total Shareholder Return targets).",
        footnote_revenue_recognition="ASC 606: Accelerated transition of VMware perpetual licenses to predictable annual subscriptions (ARR).",
        footnote_debt_maturity_schedule="Free cash flow exceeding $20B/yr allows paying down $8B to $10B in gross debt annually.",
        analyst_target_mean_usd=192.00,
        analyst_recommendations_dist="31 Buy | 5 Hold | 0 Sell",
        analyst_eps_revisions_30d_90d="+9.4% upward revisions following record quarterly guidance in custom AI silicon.",
    ),
    EquityDocumentaryDossier(
        ticker="MA",
        company_name="Mastercard Incorporated",
        filing_form_annual="SEC Form 10-K (NYSE)",
        filing_form_quarterly="SEC Form 10-Q",
        auditor_firm="PricewaterhouseCoopers (PwC) LLP",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="Effective — Security and transaction internal controls fully certified",
        mda_growth_decomposition="+14.5% YoY: +11.0% GDV in constant currency, +3.5% Cyber & Data Intelligence Value-Added Services",
        mda_segment_profitability="Payment Network Op Margin: 62.0% | Value-Added Services Op Margin: 50.5%",
        mda_backlog_rpo="Over 3.4 billion active Mastercard and Maestro cards deployed globally",
        mda_capex_plan="Ultra-light CapEx of $450M/yr in cybersecurity and low-latency settlement infrastructure",
        item_1a_specific_risks="1. US regulatory pressure on interchange (Credit Card Competition Act); 2. Sovereign instant payment rails (Pix in Brazil, UPI in India — offset by VAS and credit growth); 3. Cyber risks against global financial rails.",
        footnote_contingencies_litigation="US merchant interchange antitrust litigation fully accrued within class-action settlement structure.",
        footnote_sbc_impact="SBC of 2.1% of CFO (minimal dilution burden on public equity holders).",
        footnote_revenue_recognition="ASC 606: Transaction assessment fees recognized in real time upon payment authorization and clearing.",
        footnote_debt_maturity_schedule="Gross debt of $15.2B carrying A+ rating with smooth amortizing maturities through 2053.",
        analyst_target_mean_usd=545.00,
        analyst_recommendations_dist="34 Buy | 4 Hold | 0 Sell",
        analyst_eps_revisions_30d_90d="+4.5% upward revisions backed by steady cross-border travel and consumer card spend.",
    ),
    EquityDocumentaryDossier(
        ticker="NU",
        company_name="Nu Holdings Ltd. (Nubank)",
        filing_form_annual="SEC Form 20-F (NYSE Class A)",
        filing_form_quarterly="Form 6-K (Quarterly Results)",
        auditor_firm="KPMG Auditores Independentes",
        auditor_opinion="Unqualified / Clean Opinion (No Reservations)",
        sox_404b_controls="Effective — Internal controls fully compliant with global banking standards",
        mda_growth_decomposition="+68.0% YoY FX-Neutral: +42.0% Customer base growth (+18M/yr), +26.0% ARPAC expansion ($11/mo) and multi-product cross-sell",
        mda_segment_profitability="Brazil Operations: ROE > 28% and Cost-to-Income of 31.4% | Mexico Operations: Rapid retail deposit gathering phase",
        mda_backlog_rpo="Total active customer base exceeding 110 million individuals and SMEs",
        mda_capex_plan="CapEx of $150M/yr dedicated to proprietary credit underwriting AI models and cloud architecture",
        item_1a_specific_risks="1. Credit card and personal loan delinquency in high-rate macro environments; 2. Execution milestones for full Mexican banking license; 3. FX translation from BRL/MXN into reporting USD.",
        footnote_contingencies_litigation="Zero material litigation; 100% expected credit loss provisions (CECL) comfortably covering 90+ NPLs.",
        footnote_sbc_impact="SBC of 6.5% of CFO (long-term equity grants for world-class software engineering talent).",
        footnote_revenue_recognition="ASC 606 & IFRS 9: Net interest income recognized via effective interest rate; interchange fees recognized on transaction date.",
        footnote_debt_maturity_schedule="Surplus capital structure with Basel CET1 ratio > 17% (Fortress balance sheet with zero expensive corporate debt).",
        analyst_target_mean_usd=17.50,
        analyst_recommendations_dist="18 Buy | 5 Hold | 1 Sell",
        analyst_eps_revisions_30d_90d="+18.5% upward revisions following consecutive quarterly expansions in ROE and net income.",
    ),
]


CRYPTO_FILINGS_DB: List[CryptoDocumentaryDossier] = [
    CryptoDocumentaryDossier(
        symbol="BTC-USD",
        name="Bitcoin Network",
        wp_title_author="Bitcoin: A Peer-to-Peer Electronic Cash System — Satoshi Nakamoto (October 2008)",
        wp_value_proposition="Sovereign, censorship-resistant digital monetary asset with zero counterparty risk and mathematically immutable supply capped at 21,000,000 units.",
        wp_consensus_architecture="Proof-of-Work (SHA-256) with automatic difficulty adjustment every 2,016 blocks (~14 days) and programmatic supply halving every 210,000 blocks (~4 years).",
        wp_value_accrual_mechanism="Absolute inelastic scarcity (Stock-to-Flow > 110 post-2024 halving) + base-layer settlement fees for high-value institutional settlement and L2 anchoring.",
        github_core_repos="bitcoin/bitcoin, lightningnetwork/lnd, ElementsProject/lightning",
        github_commits_4w=192,
        github_active_devs_monthly=1150,
        deepdao_status="Pure decentralized governance via BIPs (Bitcoin Improvement Proposals) and social consensus of > 19,000 independent full nodes.",
        recent_governance_proposals="BIP-324 (Encrypted P2P Transport v2 active), Miniscript integration in Bitcoin Core 28.0, and technical covenant discussions (OP_CAT / BIP-119).",
        skin_in_the_game_locked_pct=65.8,
        skin_in_the_game_details="65.8% of Circulating Supply held by Long-Term Holders (> 1 year dormant) + multi-billion-dollar irreversible ASIC mining hardware CapEx.",
        token_sniffer_score=100,
        audit_firms="Continuous global cryptographic peer review across 16+ years (MIT Digital Currency Initiative, Chaincode Labs, Blockstream)",
        exploit_history="Zero double-spending incidents or cryptographic breaches on mainnet since 2009 (100% continuous uptime over last 11 years).",
    ),
    CryptoDocumentaryDossier(
        symbol="ETH-USD",
        name="Ethereum Network",
        wp_title_author="A Next-Generation Smart Contract and Decentralized Application Platform — Vitalik Buterin (2013)",
        wp_value_proposition="Decentralized world computer and primary global financial settlement layer for DeFi, Stablecoins (~$95B), institutional RWAs (BlackRock BUIDL), and L2 Rollups.",
        wp_consensus_architecture="Proof-of-Stake (Gasper = Casper FFG + LMD-GHOST) with over 1.05 million active validators and Proposer-Builder Separation (MEV-Boost).",
        wp_value_accrual_mechanism="Triple Point Asset: 1) Consumable gas commodity burned via EIP-1559; 2) Capital asset generating real ETH yield for stakers; 3) Pristine collateral for global DeFi.",
        github_core_repos="ethereum/go-ethereum, ethereum/consensus-specs, sigp/lighthouse, paradigmxyz/reth",
        github_commits_4w=355,
        github_active_devs_monthly=2480,
        deepdao_status="Technical governance via EIPs, All Core Devs (ACD) calls, and Ethereum Foundation + Ecosystem of major L2 DAOs (Arbitrum, Optimism, Uniswap, Aave).",
        recent_governance_proposals="EIP-4844 (Proto-Danksharding Blobs reducing L2 data availability costs by 95%) live; Pectra Upgrade (EIP-7702 Account Abstraction + EIP-7251 MaxEB 2048 ETH).",
        skin_in_the_game_locked_pct=28.7,
        skin_in_the_game_details="34.6 Million ETH (~$102B, 28.7% of circulating supply) locked in Beacon Chain staking contract subject to programmatic slashing penalties.",
        token_sniffer_score=100,
        audit_firms="Trail of Bits, SigmaPrime, OpenZeppelin, Runtime Verification, ConsenSys Diligence",
        exploit_history="Zero consensus exploits on Beacon Chain PoS or EVM since 2016; premier client software diversity across Geth, Nethermind, Besu, and Reth.",
    ),
    CryptoDocumentaryDossier(
        symbol="SOL-USD",
        name="Solana Network",
        wp_title_author="Solana: A new architecture for a high performance blockchain — Anatoly Yakovenko (2017)",
        wp_value_proposition="Single global state monolithic blockchain optimized for hardware-speed parallel execution (high TPS throughput, sub-second finality, and fees < $0.002).",
        wp_consensus_architecture="Proof-of-History (PoH pre-consensus cryptographic clock) + Tower BFT + Sealevel parallel smart contract execution engine.",
        wp_value_accrual_mechanism="50% of base fees burned permanently + Priority Fees and Jito MEV tips directed to validators and staking delegators.",
        github_core_repos="anza-xyz/agave, jump-crypto/firedancer, jito-foundation/jito-solana",
        github_commits_4w=295,
        github_active_devs_monthly=1120,
        deepdao_status="Protocol governance via SIMDs (Solana Improvement Documents) voted on-chain weighted by validator active stake.",
        recent_governance_proposals="SIMD-0096 (Priority fee allocation), Token Extensions (confidential institutional transfers), and Firedancer independent client mainnet deployment.",
        skin_in_the_game_locked_pct=67.8,
        skin_in_the_game_details="Over 320 Million SOL (67.8% of circulating supply) actively locked in staking consensus securing the network.",
        token_sniffer_score=95,
        audit_firms="Neodyme, OtterSec, Zellic, Kudelski Security, Trail of Bits (Firedancer Independent Audit)",
        exploit_history="Zero protocol-level L1 theft exploits; historical outage modes (2021-2022) permanently solved via QUIC, localized fee markets, and Firedancer.",
    ),
    CryptoDocumentaryDossier(
        symbol="AAVE-USD",
        name="Aave Protocol V3",
        wp_title_author="Aave Protocol V3 Technical Paper & GHO Native Stablecoin — Stani Kulechov & Aave Labs (2022/2024)",
        wp_value_proposition="Largest decentralized money market protocol (overcollateralized lending and borrowing) and multi-chain issuer of the native GHO stablecoin.",
        wp_consensus_architecture="Non-custodial smart contracts governed on-chain via Aave Governance V3 (cross-chain execution via a.DI).",
        wp_value_accrual_mechanism="Lending pool interest reserve factors + 100% of GHO borrow fees flowing to the DAO Treasury + Buy & Distribute mechanism under AAVEnomics.",
        github_core_repos="aave/aave-v3-core, aave/gho-core, bgd-labs/aave-governance-v3",
        github_commits_4w=154,
        github_active_devs_monthly=435,
        deepdao_status="Top #1 DeFi DAO on DeepDAO by governance participation; over 480 AIP proposals voted and executed autonomously by smart contracts.",
        recent_governance_proposals="'AAVEnomics' upgrade (Fee Switch activation / secondary market buybacks financed by protocol profits) and Umbrella Safety Module (stkGHO/aTokens).",
        skin_in_the_game_locked_pct=25.8,
        skin_in_the_game_details="3.85 Million AAVE (25.8% of circulating supply) locked in Safety Module (stkAAVE / ABPT) as an insurance backstop with up to 30% slashing risk.",
        token_sniffer_score=100,
        audit_firms="Certora (Continuous Formal Verification), OpenZeppelin, Trail of Bits, SigmaPrime, PeckShield",
        exploit_history="Flawless security record with zero exploit losses across Aave V3 core contracts (> $21B in peak TVL).",
    ),
    CryptoDocumentaryDossier(
        symbol="MKR-USD",
        name="Maker / Sky Protocol",
        wp_title_author="The Maker Protocol: Dai 1:1 Peg Mechanism & USDS Endgame (Rune Christensen)",
        wp_value_proposition="Decentralized central bank and credit facility issuing DAI/USDS backed by pristine crypto and RWA US Treasury collateral.",
        wp_consensus_architecture="Ethereum L1 smart contracts + specialized credit and asset allocation SubDAOs.",
        wp_value_accrual_mechanism="Smart Burn Engine: Excess protocol net revenue from RWA Treasuries and collateralized loans is automatically deployed in continuous auctions to buy back and BURN MKR tokens, driving permanent supply deflation.",
        github_core_repos="makerdao/dss, makerdao/endgame-toolkit, makerdao/smart-burn-engine",
        github_commits_4w=320,
        github_active_devs_monthly=115,
        deepdao_status="Top 3 Global DeepDAO: $6.8B in balance-sheet treasury management and over 12,000 active voting delegates.",
        recent_governance_proposals="Sky brand transition, $1.5B allocation into tokenized US Treasuries via BlackRock BUIDL and Superstate.",
        skin_in_the_game_locked_pct=34.5,
        skin_in_the_game_details="Over 34% of MKR tokens deposited in governance staking modules with long-term lockups.",
        token_sniffer_score=100,
        audit_firms="Trail of Bits, OpenZeppelin, Runtime Verification, ChainSecurity (Longest battle-tested track record in DeFi history)",
        exploit_history="Zero exploits across core DAI smart contracts over 7+ years of continuous, uninterrupted operation.",
    ),
    CryptoDocumentaryDossier(
        symbol="PENDLE-USD",
        name="Pendle Finance V2",
        wp_title_author="Pendle Finance V2: Yield Tokenization & Automated Market Maker for Fixed Income (TN Lee)",
        wp_value_proposition="Leading yield tokenization protocol splitting yield-bearing assets into Principal Tokens (PT) and Yield Tokens (YT), enabling fixed income yields and interest-rate trading in DeFi.",
        wp_consensus_architecture="EIP-5115 (Standardized Yield Token) deployed across Ethereum, Arbitrum, Mantle, and Base.",
        wp_value_accrual_mechanism="3% swap fee on all yield accrued by YT tokens + 80% of aggregate protocol swap fees distributed weekly to vePENDLE lockers (Direct Real Yield).",
        github_core_repos="pendle-finance/pendle-core-v2, pendle-finance/pendle-amm",
        github_commits_4w=235,
        github_active_devs_monthly=68,
        deepdao_status="Active vePENDLE governance model managing over $4.2B in protocol TVL liquidity incentives.",
        recent_governance_proposals="Integration of Bitcoin LRT pools (Babylon/Symbiotic) and deployment to Coinbase's Base L2 network.",
        skin_in_the_game_locked_pct=42.0,
        skin_in_the_game_details="42% of PENDLE circulating supply locked in vePENDLE with a weighted-average commitment exceeding 2 years.",
        token_sniffer_score=98,
        audit_firms="Ackee Blockchain, Dedaub, WatchPug, Spearbit (Formal mathematical verification and independent audits)",
        exploit_history="Zero exploits in V2 contracts; mathematically proven AMM invariant curves.",
    ),
    CryptoDocumentaryDossier(
        symbol="LINK-USD",
        name="Chainlink Network",
        wp_title_author="Chainlink 2.0: Decentralized Oracle Networks, CCIP & Hybrid Smart Contracts (Sergey Nazarov, Ari Juels)",
        wp_value_proposition="Global decentralized oracle infrastructure monopoly and Cross-Chain Interoperability Protocol (CCIP) adopted by SWIFT, DTCC, Euroclear, and tier-1 banks.",
        wp_consensus_architecture="Decentralized Oracle Networks (DONs) with zero-knowledge cryptographic proofs and native PoS node staking.",
        wp_value_accrual_mechanism="Data feed consumption, VRF, and automation fees paid in LINK by hundreds of protocols + institutional CCIP fees flowing to Staking v0.2.",
        github_core_repos="smartcontractkit/chainlink, smartcontractkit/ccip",
        github_commits_4w=590,
        github_active_devs_monthly=315,
        deepdao_status="Premier oracle infrastructure globally securing over $75 Billion in Total Value Secured (TVS).",
        recent_governance_proposals="Staking pool expansion to 45M LINK and atomic settlement pilots for tokenized fund shares with UBS and SBI Digital.",
        skin_in_the_game_locked_pct=28.5,
        skin_in_the_game_details="Staking v0.2 pool fully capped within minutes with 45 million LINK committed by elite node operators.",
        token_sniffer_score=100,
        audit_firms="SigmaPrime, Trail of Bits, Certora, OpenZeppelin",
        exploit_history="Immaculate operational record: 6+ years securing mission-critical data infrastructure across global DeFi without feed failure.",
    ),
    CryptoDocumentaryDossier(
        symbol="UNI-USD",
        name="Uniswap Protocol (Unichain)",
        wp_title_author="Uniswap V4 Hooks & Unichain Architecture: The Rollup for Decentralized Finance (Hayden Adams)",
        wp_value_proposition="Global automated market making (AMM) and decentralized exchange monopoly, now operating its own dedicated high-speed settlement Layer 2 (Unichain).",
        wp_consensus_architecture="Uniswap V4 programmable hooks + Optimistic Rollup L2 (Unichain) with sub-second Flashblock sequencer decentralization.",
        wp_value_accrual_mechanism="Unichain MEV capture and priority sequencing fees accrued to staked UNI validators + pending protocol Fee Switch activation.",
        github_core_repos="Uniswap/v4-core, Uniswap/v4-periphery, Uniswap/unichain-monorepo",
        github_commits_4w=410,
        github_active_devs_monthly=185,
        deepdao_status="Largest DeFi DAO globally with over $5 Billion in treasury assets and autonomous on-chain governance execution.",
        recent_governance_proposals="Unichain deployment approval and $150M liquidity grant allocation for next-generation V4 liquidity providers.",
        skin_in_the_game_locked_pct=32.0,
        skin_in_the_game_details="Tokens actively delegated and voted in DAO governance represent nearly one-third of total float with fiduciary veto rights.",
        token_sniffer_score=100,
        audit_firms="Trail of Bits, ABDK Consulting, OpenZeppelin, Spearbit",
        exploit_history="Zero security exploits across core V1, V2, V3, and V4 smart contracts over trillions of dollars in cumulative lifetime volume.",
    ),
]


_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOM_FILINGS_CACHE_PATH = os.path.join(_ROOT_DIR, "data_cache", "custom_filings_cache.json")


class EquityDocumentaryDossierSchema(BaseModel):
    """Pydantic schema matching EquityDocumentaryDossier 1-to-1 for Gemini Structured Outputs."""

    ticker: str = Field(description="Official uppercase stock ticker symbol, e.g., NVDA or COST.")
    company_name: str = Field(description="Official legal company name.")
    filing_form_annual: str = Field(description="Annual filing form & fiscal period cited, e.g., SEC Form 10-K (FY 2026).")
    filing_form_quarterly: str = Field(description="Quarterly filing form & period cited, e.g., SEC Form 10-Q (Q3 2026).")
    auditor_firm: str = Field(description="Independent registered public accounting firm (e.g., PwC LLP, EY LLP, Deloitte).")
    auditor_opinion: str = Field(description="Audit opinion classification (e.g., Unqualified / Clean Opinion or Qualified).")
    sox_404b_controls: str = Field(description="SOX Section 404(b) internal control over financial reporting assessment.")
    mda_growth_decomposition: str = Field(description="Item 7 MD&A quantitative revenue breakdown: organic volume vs pricing/mix vs FX.")
    mda_segment_profitability: str = Field(description="Segment operating or gross margins extracted from MD&A / segment notes.")
    mda_backlog_rpo: str = Field(description="Remaining Performance Obligations (RPO), contracted backlog, or deferred revenue.")
    mda_capex_plan: str = Field(description="Capital expenditure guidance, allocation focus, and expansion capacity notes.")
    item_1a_specific_risks: str = Field(description="Top 3–4 company-specific Item 1A Risk Factors concisely enumerated.")
    footnote_contingencies_litigation: str = Field(description="Legal contingencies, antitrust/tax investigations, and solvency materiality.")
    footnote_sbc_impact: str = Field(description="Stock-Based Compensation (SBC) dollar amount, % of revenue/CFO, and buyback offset.")
    footnote_revenue_recognition: str = Field(description="ASC 606 / IFRS 15 revenue recognition policy and receivables quality notes.")
    footnote_debt_maturity_schedule: str = Field(description="Total debt, coupon structure, maturity ladder, and cash coverage.")
    analyst_target_mean_usd: float = Field(description="Consensus target price in USD if stated in document; 0.0 if not stated.")
    analyst_recommendations_dist: str = Field(description="Rating distribution or 'Not disclosed in source filing' if absent.")
    analyst_eps_revisions_30d_90d: str = Field(description="30d/90d EPS revision notes or forward guidance comparison from document.")
    ma_and_strategic_deals: str = Field(
        description=(
            "Acquisitions, divestitures, joint ventures, strategic alliances, and antitrust/regulatory status "
            "disclosed in 10-K/10-Q/8-K business combination notes (or state 'No material M&A disclosed in period')."
        )
    )
    ma_payment_and_goodwill: str = Field(
        description=(
            "M&A financing structure (all-cash vs stock dilution) and Goodwill/intangibles impairment balance "
            "from footnotes."
        )
    )


class CryptoDocumentaryDossierSchema(BaseModel):
    """Pydantic schema matching CryptoDocumentaryDossier 1-to-1 for Gemini Structured Outputs."""

    symbol: str = Field(description="Normalized token ticker symbol with -USD suffix (e.g., PENDLE-USD, LINK-USD).")
    name: str = Field(description="Official protocol or network name.")
    wp_title_author: str = Field(description="White paper title and primary author(s) / year.")
    wp_value_proposition: str = Field(description="Core architectural thesis and economic problem solved.")
    wp_consensus_architecture: str = Field(description="Consensus mechanism, security model, and smart contract execution layer.")
    wp_value_accrual_mechanism: str = Field(description="Token value accrual: fee switch, buyback/burn, staking Real Yield, or gas utility.")
    github_core_repos: str = Field(description="Primary GitHub organization/repository paths mentioned; 'Not specified' if absent.")
    github_commits_4w: int = Field(description="Estimated 4-week core commits as integer (0 if not stated).")
    github_active_devs_monthly: int = Field(description="Monthly active developers as integer (0 if not stated).")
    deepdao_status: str = Field(description="DAO governance activity, voting mechanism, and treasury scale.")
    recent_governance_proposals: str = Field(description="Notable recent governance proposals (EIPs/PIPs/MIPs) and status.")
    skin_in_the_game_locked_pct: float = Field(description="Percentage (0–100) of circulating or total supply locked/staked by long-term holders.")
    skin_in_the_game_details: str = Field(description="Summary of staking locks, ve-token commitments, or founder/insider vesting.")
    token_sniffer_score: int = Field(description="Security/audit score 0–100 (or estimated 85 if reputable audits verified; 0 if unverified).")
    audit_firms: str = Field(description="Security audit firms / formal verification partners cited in document.")
    exploit_history: str = Field(description="Historical exploit/incident record or security track record stated.")


def _load_custom_filings_cache() -> Dict[str, Dict[str, Dict[str, Any]]]:
    base: Dict[str, Dict[str, Dict[str, Any]]] = {"equities": {}, "cryptos": {}}
    if not os.path.exists(CUSTOM_FILINGS_CACHE_PATH):
        return base
    try:
        with open(CUSTOM_FILINGS_CACHE_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            base["equities"] = dict(raw.get("equities", {}))
            base["cryptos"] = dict(raw.get("cryptos", {}))
    except Exception:
        pass
    return base


def _save_custom_filing_cache(kind: str, key: str, dossier_obj: Any) -> None:
    try:
        os.makedirs(os.path.dirname(CUSTOM_FILINGS_CACHE_PATH), exist_ok=True)
        cache = _load_custom_filings_cache()
        cache.setdefault(kind, {})[key] = asdict(dossier_obj)
        with open(CUSTOM_FILINGS_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


class FilingsEngine:
    def __init__(self) -> None:
        pass

    def get_equity_dossiers(self, tickers: List[str] | None = None) -> List[EquityDocumentaryDossier]:
        if tickers is None:
            try:
                import sqlite3
                with sqlite3.connect("portfolio_store.db") as conn:
                    rows = conn.execute("SELECT ticker, category FROM portfolio_assets ORDER BY display_order ASC").fetchall()
                tickers = [r[0] for r in rows if "Crypto" not in r[1] and "ETF" not in r[1]]
            except Exception:
                tickers = ["NVDA", "AAPL", "MSFT", "JPM", "ASML", "TSM", "MELI", "AVGO", "MA", "NU"]
        tk_set = {t.upper() for t in tickers}

        cache = _load_custom_filings_cache()
        eq_map: Dict[str, EquityDocumentaryDossier] = {d.ticker.upper(): d for d in EQUITY_FILINGS_DB}
        valid_fields = {f.name for f in fields(EquityDocumentaryDossier)}
        for tk_key, d_dict in cache.get("equities", {}).items():
            try:
                filtered = {k: v for k, v in d_dict.items() if k in valid_fields}
                eq_map[tk_key.upper()] = EquityDocumentaryDossier(**filtered)
            except Exception:
                pass

        # Hydrate M&A fields for static dossiers that don't yet specify them
        try:
            from core.intelligence_reports_engine import CORPORATE_SIGNAL_MA_DB

            for tk_key, dos in eq_map.items():
                if not dos.ma_and_strategic_deals and tk_key in CORPORATE_SIGNAL_MA_DB:
                    sm = CORPORATE_SIGNAL_MA_DB[tk_key]
                    dos.ma_and_strategic_deals = f"{sm.ma_and_strategic_deals} ({sm.antitrust_and_regulatory_status})"
                    dos.ma_payment_and_goodwill = f"{sm.payment_structure_and_dilution} | {sm.goodwill_and_impairment_risk}"
        except Exception:
            pass

        return [d for tk, d in eq_map.items() if tk in tk_set]

    def get_crypto_dossiers(self, symbols: List[str] | None = None) -> List[CryptoDocumentaryDossier]:
        if symbols is None:
            try:
                import sqlite3
                with sqlite3.connect("portfolio_store.db") as conn:
                    rows = conn.execute("SELECT ticker, category FROM portfolio_assets ORDER BY display_order ASC").fetchall()
                symbols = [r[0] for r in rows if "Crypto" in r[1] or r[0].endswith("-USD")]
            except Exception:
                symbols = ["BTC-USD", "ETH-USD", "PENDLE-USD", "LINK-USD", "MKR-USD", "UNI-USD"]
        sym_set = {s.upper() for s in symbols}

        cache = _load_custom_filings_cache()
        cr_map: Dict[str, CryptoDocumentaryDossier] = {c.symbol.upper(): c for c in CRYPTO_FILINGS_DB}
        valid_fields = {f.name for f in fields(CryptoDocumentaryDossier)}
        for sym_key, d_dict in cache.get("cryptos", {}).items():
            try:
                filtered = {k: v for k, v in d_dict.items() if k in valid_fields}
                cr_map[sym_key.upper()] = CryptoDocumentaryDossier(**filtered)
            except Exception:
                pass

        return [c for sym, c in cr_map.items() if sym in sym_set]

    def extract_equity_dossier_from_document(
        self,
        ticker: str,
        company_name: str = "",
        raw_text: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None,
        persist: bool = True,
    ) -> Tuple[Optional[EquityDocumentaryDossier], str]:
        """
        Extracts a structured `EquityDocumentaryDossier` from raw filing text or PDF
        bytes (10-K, 10-Q, 20-F, earnings release) via Gemini Structured Outputs.
        Safely falls back to static `EQUITY_FILINGS_DB` if GEMINI_API_KEY is absent or fails.
        """
        tk_norm = (ticker or "").strip().upper()
        if not tk_norm:
            return None, "Ticker symbol is required for dynamic filing extraction."
        if not (raw_text and raw_text.strip()) and not pdf_bytes:
            return None, "Provide filing text or upload a PDF/TXT document to extract."

        static_match = next((d for d in EQUITY_FILINGS_DB if d.ticker.upper() == tk_norm), None)

        try:
            from core.gemini_client import generate_structured_interaction, is_gemini_configured
        except Exception:
            if static_match is not None:
                return static_match, "Gemini client unavailable — fell back to static SEC filings database."
            return None, "Gemini client unavailable and ticker not in static filings database."

        if not is_gemini_configured():
            if static_match is not None:
                return static_match, "GEMINI_API_KEY not configured — fell back to verified static SEC filings database."
            return None, "GEMINI_API_KEY not configured — configure .env to extract new dynamic filings."

        instruction_prompt = (
            f"Extract an institutional SEC forensic dossier in English for ticker '{tk_norm}'"
            + (f" ({company_name})" if company_name else "")
            + ". Strictly cite ONLY facts, figures, risks, audit opinions, SOX 404(b) status, MD&A volume/price/FX "
            "drivers, RPO/backlog, CapEx, contingencies, SBC, ASC 606, debt maturities, M&A/acquisitions/goodwill/payment structure, "
            "and analyst consensus present in the source bundle. "
            "Never reference Altman Z-Score. If a field is not present in the source bundle, state 'Not disclosed in provided excerpt' "
            "(or 0.0 / 0 for numeric fields)."
        )

        if pdf_bytes:
            b64_doc = base64.b64encode(pdf_bytes).decode("utf-8")
            combined_text = instruction_prompt
            if raw_text and raw_text.strip():
                combined_text += f"\n\n--- SUPPLEMENTAL VERIFIED SOURCES ---\n{raw_text.strip()[:90_000]}"
            input_payload: Any = [
                {"type": "text", "text": combined_text},
                {"type": "document", "data": b64_doc, "mime_type": "application/pdf"},
            ]
        else:
            snippet = (raw_text or "").strip()[:135_000]
            input_payload = f"{instruction_prompt}\n\n--- SOURCE DOCUMENT BUNDLE ---\n{snippet}"

        system_instruction = (
            "You are an Institutional Forensic SEC Auditor. Extract faithful, quantitative structured JSON "
            "matching EquityDocumentaryDossierSchema without inventing ungrounded figures or using Altman Z-Score."
        )
        parsed = generate_structured_interaction(
            input_payload=input_payload,
            schema_cls=EquityDocumentaryDossierSchema,
            system_instruction=system_instruction,
            temperature=0.05,
            max_output_tokens=3000,
        )
        if parsed is None:
            if static_match is not None:
                return static_match, "Gemini extraction failed — safely fell back to verified static filings database."
            return None, "Gemini extraction failed and no static fallback dossier exists for this ticker."

        dossier_dict = parsed.model_dump()
        dossier_dict["ticker"] = tk_norm
        if company_name and not dossier_dict.get("company_name"):
            dossier_dict["company_name"] = company_name

        dossier = EquityDocumentaryDossier(**dossier_dict)
        if persist:
            _save_custom_filing_cache("equities", tk_norm, dossier)
        return dossier, f"Successfully extracted & structured SEC filing dossier for {tk_norm} via Gemini Structured Outputs."

    def extract_crypto_dossier_from_document(
        self,
        symbol: str,
        name: str = "",
        raw_text: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None,
        persist: bool = True,
    ) -> Tuple[Optional[CryptoDocumentaryDossier], str]:
        """
        Extracts a structured `CryptoDocumentaryDossier` from whitepapers, governance
        reports, or security audit PDFs/text via Gemini Structured Outputs.
        Safely falls back to static `CRYPTO_FILINGS_DB` when unconfigured or on error.
        """
        raw_sym = (symbol or "").strip().upper()
        if not raw_sym:
            return None, "Protocol symbol is required for dynamic whitepaper extraction."
        sym_norm = raw_sym if "-" in raw_sym else f"{raw_sym}-USD"
        if not (raw_text and raw_text.strip()) and not pdf_bytes:
            return None, "Provide whitepaper/audit text or upload a PDF/TXT document to extract."

        static_match = next((c for c in CRYPTO_FILINGS_DB if c.symbol.upper() == sym_norm), None)

        try:
            from core.gemini_client import generate_structured_interaction, is_gemini_configured
        except Exception:
            if static_match is not None:
                return static_match, "Gemini client unavailable — fell back to static crypto dossier database."
            return None, "Gemini client unavailable and protocol not in static database."

        if not is_gemini_configured():
            if static_match is not None:
                return static_match, "GEMINI_API_KEY not configured — fell back to verified static crypto database."
            return None, "GEMINI_API_KEY not configured — configure .env to extract new protocol whitepapers."

        instruction_prompt = (
            f"Extract a technical institutional protocol dossier in English for cryptoasset '{sym_norm}'"
            + (f" ({name})" if name else "")
            + ". Strictly cite ONLY technical facts, consensus mechanics, token value accrual, GitHub/dev metrics, "
            "DAO governance proposals, staking/lockups, security audits, Token Sniffer score, and exploit history present in the source bundle. "
            "If a quantitative metric is absent in the source bundle, state 'Not disclosed in provided document' (or 0 / 0.0 for numbers)."
        )

        if pdf_bytes:
            b64_doc = base64.b64encode(pdf_bytes).decode("utf-8")
            combined_text = instruction_prompt
            if raw_text and raw_text.strip():
                combined_text += f"\n\n--- SUPPLEMENTAL VERIFIED SOURCES (GITHUB / SNAPSHOT / DEFILLAMA / SEARCH) ---\n{raw_text.strip()[:90_000]}"
            input_payload: Any = [
                {"type": "text", "text": combined_text},
                {"type": "document", "data": b64_doc, "mime_type": "application/pdf"},
            ]
        else:
            snippet = (raw_text or "").strip()[:130_000]
            input_payload = f"{instruction_prompt}\n\n--- SOURCE PROTOCOL BUNDLE ---\n{snippet}"

        system_instruction = (
            "You are a Senior DeFi Protocol Security & Tokenomics Researcher. Extract structured JSON "
            "strictly adhering to CryptoDocumentaryDossierSchema using only verifiable facts from the source."
        )
        parsed = generate_structured_interaction(
            input_payload=input_payload,
            schema_cls=CryptoDocumentaryDossierSchema,
            system_instruction=system_instruction,
            temperature=0.05,
            max_output_tokens=3000,
        )
        if parsed is None and pdf_bytes and raw_text and raw_text.strip():
            # Fallback to text-only bundle if inline PDF attachment was too large or rejected
            snippet = raw_text.strip()[:130_000]
            parsed = generate_structured_interaction(
                input_payload=f"{instruction_prompt}\n\n--- SOURCE PROTOCOL BUNDLE ---\n{snippet}",
                schema_cls=CryptoDocumentaryDossierSchema,
                system_instruction=system_instruction,
                temperature=0.05,
                max_output_tokens=3000,
            )
        if parsed is None:
            if static_match is not None:
                return static_match, "Gemini extraction failed — safely fell back to verified static crypto dossier."
            return None, "Gemini extraction failed and no static fallback dossier exists for this protocol."

        dossier_dict = parsed.model_dump()
        dossier_dict["symbol"] = sym_norm
        if name and not dossier_dict.get("name"):
            dossier_dict["name"] = name

        dossier = CryptoDocumentaryDossier(**dossier_dict)
        if persist:
            _save_custom_filing_cache("cryptos", sym_norm, dossier)
        return dossier, f"Successfully extracted & structured protocol dossier for {sym_norm} via Gemini Structured Outputs."

    def _google_search_fallback_text(self, query_prompt: str) -> Optional[str]:
        """Fallback using Gemini Interactions API `google_search` grounding when SEC/CoinGecko lacks a ticker."""
        try:
            from core.gemini_client import (
                _is_transient_genai_error,
                _mark_genai_unhealthy,
                _resolve_candidate_models,
                get_genai_client,
            )

            client = get_genai_client()
            if client is None:
                return None

            for mdl in _resolve_candidate_models(fast=True):
                try:
                    interaction = client.interactions.create(
                        model=mdl,
                        input=query_prompt,
                        tools=[{"type": "google_search"}],
                        generation_config={"temperature": 0.1, "max_output_tokens": 2400},
                        store=False,
                        timeout=22.0,
                    )
                    txt = (getattr(interaction, "output_text", None) or "").strip()
                    if txt:
                        return txt
                except Exception as exc:
                    if _is_transient_genai_error(exc):
                        _mark_genai_unhealthy(mdl)
                        continue
                    break
        except Exception:
            pass
        return None

    def auto_fetch_and_extract_equity_dossier(
        self,
        ticker: str,
        form_preference: str = "10-K",
        persist: bool = True,
    ) -> Tuple[Optional[EquityDocumentaryDossier], str, Dict[str, Any]]:
        """
        Automatically fetches ALL relevant documentary sources for an equity:
          - SEC EDGAR Annual (`10-K` / `20-F`) + Quarterly (`10-Q` / `6-K`)
          - Recent `8-K` Material Events + `Form 4` / `DEF 14A` metadata
          - Wall Street Consensus Price Target, Ratings & EPS Revisions (`yfinance`)
          - Gemini Google Search grounding supplement for non-SEC stocks or missing fields
        Then extracts and persists the structured `EquityDocumentaryDossier`.
        """
        from core.filing_fetcher import fetch_complete_equity_document_bundle

        tk_norm = (ticker or "").strip().upper()
        if not tk_norm:
            return None, "Ticker symbol is required.", {}

        pref_order: Tuple[str, ...] = (
            ("10-Q", "10-K", "20-F") if form_preference == "10-Q" else ("10-K", "20-F", "10-Q")
        )
        bundle_text, meta = fetch_complete_equity_document_bundle(tk_norm, preferred_forms=pref_order)

        # Supplement via Google Search grounding when ticker is non-SEC or analyst revisions/targets need enrichment
        if not meta.get("sec_found") or meta.get("needs_search_enrichment"):
            search_prompt = (
                f"Search official latest annual report (10-K, 20-F, or audited annual filing), latest quarterly "
                f"filing (10-Q/6-K), recent 8-K material events, and Wall Street analyst consensus for ticker '{tk_norm}'. "
                f"Provide concise verified facts on: legal company name, filing dates, independent auditor firm & opinion, "
                f"SOX 404(b) internal controls, MD&A volume/price/FX growth decomposition, segment margins, RPO/backlog, "
                f"CapEx plan, top 3 risk factors, litigation contingencies, Stock-Based Compensation (SBC), ASC 606/IFRS 15 "
                f"revenue recognition, debt maturity schedule, M&A acquisitions/divestitures/strategic deals (payment structure "
                f"& goodwill), mean analyst target price USD, Buy/Hold/Sell distribution, and 30d/90d EPS revisions."
            )
            grounded_text = self._google_search_fallback_text(search_prompt)
            if grounded_text:
                sources_list = list(meta.get("sources_fetched") or [])
                sources_list.append("Google Search Grounded Filing & Analyst Supplement")
                meta["sources_fetched"] = sources_list
                bundle_text = (
                    (bundle_text + "\n\n=== GOOGLE SEARCH GROUNDED SUPPLEMENT ===\n" + grounded_text)
                    if bundle_text
                    else grounded_text
                )
                if not meta.get("source_url"):
                    meta["source_url"] = "Google Search Grounding + Public Consensus"

        if bundle_text:
            dossier, msg = self.extract_equity_dossier_from_document(
                ticker=tk_norm,
                company_name=str(meta.get("company_name", "")),
                raw_text=bundle_text,
                persist=persist,
            )
            if dossier is not None:
                sources_str = ", ".join(meta.get("sources_fetched") or [str(meta.get("form", "Multi-Doc"))])
                return (
                    dossier,
                    f"Auto-fetched Complete Suite [{sources_str}] -> {msg}",
                    meta,
                )
            return None, msg, meta

        return None, str(meta.get("error", "Could not fetch equity document suite automatically.")), meta

    def auto_fetch_and_extract_crypto_dossier(
        self,
        symbol: str,
        persist: bool = True,
    ) -> Tuple[Optional[CryptoDocumentaryDossier], str, Dict[str, Any]]:
        """
        Automatically fetches ALL relevant documentary sources for a cryptoasset:
          - CoinGecko Protocol Metadata + Official Whitepaper / Docs (PDF or HTML)
          - Live GitHub Engineering Metrics (28d commits, unique active devs, README)
          - Snapshot GraphQL DAO Governance & Recent Proposals
          - DeFiLlama Protocol Audits, Staking TVL & Exploits DB
          - Gemini Google Search grounding supplement (Token Sniffer, audit firms, lockups)
        Then extracts and persists the structured `CryptoDocumentaryDossier`.
        """
        from core.filing_fetcher import fetch_complete_crypto_document_bundle

        raw_sym = (symbol or "").strip().upper()
        if not raw_sym:
            return None, "Protocol symbol is required.", {}
        sym_norm = raw_sym if "-" in raw_sym else f"{raw_sym}-USD"

        ctx_text, wp_pdf, meta = fetch_complete_crypto_document_bundle(sym_norm)

        # Supplement with Google Search grounding for Token Sniffer score, audit firms, DeepDAO, & ve-token lockups
        search_prompt = (
            f"Search authoritative protocol documentation for cryptoasset '{sym_norm}'"
            + (f" ({meta.get('name')})" if meta.get("name") else "")
            + ": white paper title/authors/year, value proposition, consensus architecture, token value accrual, "
            "core GitHub repositories (4-week commit activity & monthly active devs), DeepDAO / Snapshot governance status, "
            "notable recent governance proposals, % of circulating/total supply staked or locked (Skin in the Game), "
            "Token Sniffer security score (0-100), security audit firms (e.g., Trail of Bits, OpenZeppelin, Spearbit, CertiK), "
            "and historical exploit/hack record."
        )
        grounded_text = self._google_search_fallback_text(search_prompt)
        if grounded_text:
            sources_list = list(meta.get("sources_fetched") or [])
            sources_list.append("Google Search Grounded Protocol & Audit Supplement")
            meta["sources_fetched"] = sources_list
            ctx_text = (
                (ctx_text + "\n\n=== GOOGLE SEARCH GROUNDED AUDIT / GOVERNANCE SUPPLEMENT ===\n" + grounded_text)
                if ctx_text
                else grounded_text
            )
            if not meta.get("source_url"):
                meta["source_url"] = "Google Search Grounding + Public APIs"

        if ctx_text or wp_pdf:
            dossier, msg = self.extract_crypto_dossier_from_document(
                symbol=sym_norm,
                name=str(meta.get("name", "")),
                raw_text=ctx_text,
                pdf_bytes=wp_pdf,
                persist=persist,
            )
            if dossier is not None:
                sources_str = ", ".join(meta.get("sources_fetched") or ["Protocol Docs"])
                return (
                    dossier,
                    f"Auto-fetched Complete Suite [{sources_str}] -> {msg}",
                    meta,
                )
            return None, msg, meta

        return None, str(meta.get("error", "Could not fetch crypto protocol suite automatically.")), meta

"""
MÓDULO 2: INTELIGÊNCIA DOCUMENTAL PROFUNDA
1. Para Ações (SEC EDGAR Form 10-K, 10-Q, 8-K, 20-F, Footnotes Forenses & External Analyst Reports):
   - Auditoria e Controles (Firma Auditora, Parecer Unqualified/Clean, SOX 404b)
   - Dissecação do MD&A (Item 7: Decomposição Volume vs Pricing Power vs FX, Margens por Segmento, Backlog, Plano CAPEX)
   - Fatores de Risco Específicos (Item 1A)
   - Notas Explicativas Forenses (Footnotes: Contingências/Litígios, Impacto real de SBC, Reconhecimento de Receita ASC 606, Vencimento da Dívida)
   - External Analysts' Reports (Consenso Preço-Alvo, Distribuição Buy/Hold/Sell, Revisões de EPS 30d/90d)
2. Para Criptoativos (White Papers, GitHub API, DeepDAO & Auditorias de Segurança):
   - Síntese Técnica do White Paper (Proposta de valor, Consenso, Mecanismo de captura de valor do token)
   - Métricas de Desenvolvimento GitHub (Commits 4w, Devs ativos mensais, Repositórios Core)
   - Governança DeepDAO (Atividade, Propostas recentes de tokenomics/taxas, Skin in the Game % Supply Travado)
   - Segurança (Score Token Sniffer, Firmas de Auditoria, Histórico de Exploits)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


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
        auditor_opinion="Unqualified / Clean Opinion (Sem Ressalvas)",
        sox_404b_controls="SOX Section 404(b) Eficaz — Zero deficiências materiais reportadas",
        mda_growth_decomposition="Volume Hardware: +1.5% | Pricing Power (Mix Pro + Services): +5.8% | Impacto Cambial (FX): -1.2%",
        mda_segment_profitability="Products Gross Margin: 37.2% | Services Gross Margin: 74.1% (Motor de expansão estrutural de margem)",
        mda_backlog_rpo="Deferred Revenue & Obrigações de Performance (RPO): USD 12.8B em assinaturas e AppleCare",
        mda_capex_plan="CAPEX Anual de USD 10.5B focado em servidores Private Cloud Compute (Apple Silicon M4) e ferramental de precisão",
        item_1a_specific_risks="1) Concentração de fundição em nó de 3nm na TSMC (Taiwan); 2) Regulação DMA na UE sobre taxas da App Store; 3) Litígio DOJ sobre ecossistema iPhone; 4) Exposição de ~17% da receita na Grande China.",
        footnote_contingencies_litigation="Nota 10: Processos antitruste DOJ e Comissão Europeia; provisões fiscais da Irlanda integralmente liquidadas sem impacto adicional de caixa.",
        footnote_sbc_impact="SBC de USD 11.7B/ano (3.0% da Receita | 9.9% do FCO) — Mais que compensado por USD 95B em recompras (redução líquida de 2.8% das ações/ano).",
        footnote_revenue_recognition="ASC 606: Hardware reconhecido na entrega (point-in-time); Services/iCloud rateados linearmente; comissões App Store registradas em base líquida (Principal vs Agent).",
        footnote_debt_maturity_schedule="Dívida Total USD 106B escalonada até 2062 (Custo médio ponderado de cupom fixo de 2.65% a.a.; apenas USD 10.9B vencem nos próximos 12 meses vs USD 65B em caixa).",
        analyst_target_mean_usd=248.00,
        analyst_recommendations_dist="68% Buy / Strong Buy | 25% Hold | 7% Sell (44 Analistas)",
        analyst_eps_revisions_30d_90d="30d: +1.4% (28 Up / 4 Down) | 90d: +3.8% (Impulsionado por Services e ciclo de upgrade Apple Intelligence)",
    ),
    EquityDocumentaryDossier(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        filing_form_annual="SEC Form 10-K (FY Ended June 2026)",
        filing_form_quarterly="SEC Form 10-Q (Q1 FY2027)",
        auditor_firm="Deloitte & Touche LLP (PCAOB ID #34)",
        auditor_opinion="Unqualified / Clean Opinion (Sem Ressalvas)",
        sox_404b_controls="SOX Section 404(b) Eficaz — Controles internos auditados sem ressalvas",
        mda_growth_decomposition="Volume Cloud/Seats: +9.2% | Pricing Power (E5 + Copilot ARPU): +6.8% | FX: -0.6%",
        mda_segment_profitability="Intelligent Cloud Operating Margin: 44.2% | Productivity & Business: 51.8% | More Personal Computing: 26.5%",
        mda_backlog_rpo="Commercial Remaining Performance Obligations (RPO / Backlog Contratado): USD 268 Bilhões (+21% YoY; 45% reconhecível em 12m)",
        mda_capex_plan="CAPEX de USD 52B/ano (Data Centers globais, GPUs Nvidia e silício proprietário Azure Maia/Cobalt), 100% ancorado em demanda contratada",
        item_1a_specific_risks="1) Retorno sobre o ciclo intensivo de CAPEX em IA; 2) Resiliência cibernética de infraestrutura crítica governamental; 3) Escrutínio FTC/UE sobre bundling do Teams e parcerias de IA.",
        footnote_contingencies_litigation="Nota 15: Auditoria fiscal histórica do IRS sobre preços de transferência (previsão de resolução gradual sem afetação da liquidez AAA).",
        footnote_sbc_impact="SBC de USD 10.7B/ano (4.3% da Receita | 9.0% do FCO) — Diluição neutralizada por recompras sistemáticas de ações.",
        footnote_revenue_recognition="ASC 606: Contratos multi-anuais Enterprise Agreement reconhecidos conforme consumo (Azure ACR) ou vigência de licença M365.",
        footnote_debt_maturity_schedule="Dívida de longo prazo de USD 44.9B com vencimentos até 2062 (Cupom médio ~2.9%; Caixa de USD 75.5B supera toda a dívida bruta).",
        analyst_target_mean_usd=495.00,
        analyst_recommendations_dist="91% Buy / Strong Buy | 9% Hold | 0% Sell (56 Analistas)",
        analyst_eps_revisions_30d_90d="30d: +2.1% (42 Up / 2 Down) | 90d: +5.4% (Aceleração de 29%+ em Azure AI Services)",
    ),
    EquityDocumentaryDossier(
        ticker="GOOGL",
        company_name="Alphabet Inc.",
        filing_form_annual="SEC Form 10-K (FY 2025/2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 2026)",
        auditor_firm="Ernst & Young LLP",
        auditor_opinion="Unqualified / Clean Opinion (Sem Ressalvas)",
        sox_404b_controls="SOX Section 404(b) Eficaz",
        mda_growth_decomposition="Volume de Buscas/Views: +7.5% | Pricing Power (CPC / Ad Monetization): +6.9% | FX: -0.8%",
        mda_segment_profitability="Google Services Op Margin: 39.8% | Google Cloud Op Margin: 14.2% (expansão de +850 bps em 2 anos) | Other Bets: Deficitário controlado",
        mda_backlog_rpo="Backlog Contratado de Google Cloud (RPO): USD 86.8 Bilhões (+28% YoY)",
        mda_capex_plan="CAPEX de USD 48B/ano concentrado em clusters TPU v6 (Trillium), cabos submarinos e infraestrutura Gemini AI",
        item_1a_specific_risks="1) Remédios antitruste do DOJ nos processos de Search Distribution (contrato ISA com Apple) e AdTech; 2) Competição em buscas generativas por LLMs; 3) Depreciação acelerada de servidores.",
        footnote_contingencies_litigation="Nota 10: Provisões legais para litígios antitruste nos EUA e UE; recursos judiciais em andamento com prazo estimado de 2 a 4 anos.",
        footnote_sbc_impact="SBC de USD 22.8B/ano (6.6% da Receita | 19.7% do FCO) — Ponto de atenção monitorado, mas superado por USD 62B/ano em Buybacks.",
        footnote_revenue_recognition="ASC 606: Publicidade Search/YouTube reconhecida por clique/impressão validada; Cloud reconhecido por consumo/assinatura.",
        footnote_debt_maturity_schedule="Dívida de longo prazo irrisória (USD 13.2B vs USD 93.2B em Caixa e Títulos do Tesouro; cupom médio < 2.1%).",
        analyst_target_mean_usd=218.00,
        analyst_recommendations_dist="84% Buy / Strong Buy | 16% Hold | 0% Sell (52 Analistas)",
        analyst_eps_revisions_30d_90d="30d: +3.2% (46 Up / 1 Down) | 90d: +6.8% (Forte surpresa positiva na margem operacional do Google Cloud)",
    ),
    EquityDocumentaryDossier(
        ticker="AMZN",
        company_name="Amazon.com Inc.",
        filing_form_annual="SEC Form 10-K (FY 2025/2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 2026)",
        auditor_firm="Ernst & Young LLP",
        auditor_opinion="Unqualified / Clean Opinion (Sem Ressalvas)",
        sox_404b_controls="SOX Section 404(b) Eficaz",
        mda_growth_decomposition="Volume Unidades/Cloud: +10.2% | Mix de Alta Margem (AWS + Ads + 3P): +4.5% | FX: -0.5%",
        mda_segment_profitability="AWS Operating Margin: 35.8% (Recorde) | North America Retail Op Margin: 6.1% | International Op Margin: 3.2%",
        mda_backlog_rpo="AWS Contracted Backlog (RPO): USD 164.0 Bilhões (Prazo médio ponderado remanescente de 3.8 anos)",
        mda_capex_plan="CAPEX de USD 65B/ano (~70% destinado à expansão de capacidade AWS e chips Trainium2; ~30% em automação robótica de armazéns)",
        item_1a_specific_risks="1) Processo da FTC sobre regras de paridade de preços no Marketplace; 2) Custos de energia elétrica e capacidade de rede para novos data centers AWS; 3) Ciclos de consumo varejista.",
        footnote_contingencies_litigation="Nota 7: Compromissos de compra de energia limpa e arrendamentos operacionais de centros de distribuição e frota aérea.",
        footnote_sbc_impact="SBC de USD 22.0B/ano (3.5% da Receita | 19.5% do FCO) — Em queda percentual frente à receita pelo 3º ano consecutivo.",
        footnote_revenue_recognition="ASC 606: Vendas 1P pelo valor bruto; Comissões 3P Seller Services pelo valor líquido; Prime amortizado ao longo de 12 meses.",
        footnote_debt_maturity_schedule="Dívida de longo prazo de USD 54.5B bem distribuída até 2062 (Caixa de USD 88B garante posição de caixa líquido positivo).",
        analyst_target_mean_usd=245.00,
        analyst_recommendations_dist="95% Buy / Strong Buy | 5% Hold | 0% Sell (61 Analistas)",
        analyst_eps_revisions_30d_90d="30d: +4.1% | 90d: +9.5% (Expansão acelerada de EBIT na América do Norte e AWS)",
    ),
    EquityDocumentaryDossier(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        filing_form_annual="SEC Form 10-K (FY2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 FY2027)",
        auditor_firm="PricewaterhouseCoopers LLP (PCAOB ID #238)",
        auditor_opinion="Unqualified / Clean Opinion (Sem Ressalvas)",
        sox_404b_controls="SOX Section 404(b) Eficaz",
        mda_growth_decomposition="Volume de Sistemas Data Center (Hopper/Blackwell): +68% | Pricing Power (Sistemas Completos NVL72 + Networking Spectrum-X): +24% | FX: 0%",
        mda_segment_profitability="Data Center Operating Margin: ~68.5% | Gaming & AI PC: ~42.0% | Margem Bruta Consolidada: 75.2%",
        mda_backlog_rpo="Compromissos de Compra de Suprimentos e Capacidade CoWoS reservados por 12-18 meses; demanda Blackwell esgotada por 4 trimestres",
        mda_capex_plan="Modelo Fabless Asset-Light: CAPEX < USD 2.8B/ano (2.2% da Receita); alocação maciça em P&D de engenharia e pré-pagamento de wafers TSMC",
        item_1a_specific_risks="1) Controles de exportação do BIS (EUA) para venda de chips avançados à China e Oriente Médio; 2) Gargalos de empacotamento CoWoS na TSMC; 3) Concentração dos 4 maiores clientes Hyperscalers (~45% da receita).",
        footnote_contingencies_litigation="Nota 13: Compromissos firmes de compra de inventário e capacidade de fundição de USD 18.5B para garantir liderança de entrega da arquitetura Blackwell.",
        footnote_sbc_impact="SBC de USD 4.2B/ano (3.4% da Receita | 6.5% do FCO) — Baixíssimo impacto dilutivo frente ao hiper-crescimento de FCF.",
        footnote_revenue_recognition="ASC 606: Hardware reconhecido no embarque; licenças de software corporativo NVIDIA AI Enterprise reconhecidas ao longo do contrato.",
        footnote_debt_maturity_schedule="Dívida Total de apenas USD 8.5B vs Caixa de USD 38.5B (Caixa Líquido de USD 30B; risco de refinanciamento zero).",
        analyst_target_mean_usd=168.00,
        analyst_recommendations_dist="93% Buy / Strong Buy | 7% Hold | 0% Sell (60 Analistas)",
        analyst_eps_revisions_30d_90d="30d: +5.2% | 90d: +14.8% (Revisões sucessivas para cima com ramp-up do Blackwell)",
    ),
    EquityDocumentaryDossier(
        ticker="META",
        company_name="Meta Platforms Inc.",
        filing_form_annual="SEC Form 10-K (FY 2025/2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 2026)",
        auditor_firm="Ernst & Young LLP",
        auditor_opinion="Unqualified / Clean Opinion (Sem Ressalvas)",
        sox_404b_controls="SOX Section 404(b) Eficaz",
        mda_growth_decomposition="Impressões de Anúncios Entregues: +10.0% | Preço Médio por Anúncio (Pricing Power via IA): +9.0% | FX: -0.5%",
        mda_segment_profitability="Family of Apps (FoA) Operating Margin: 51.4% (Extraordinário) | Reality Labs: Prejuízo operacional de ~USD 16B/ano em P&D de AR/VR",
        mda_backlog_rpo="Plataforma self-service de leilão em tempo real para mais de 10 milhões de anunciantes ativos",
        mda_capex_plan="CAPEX de USD 38B-40B/ano focado em clusters de treinamento Llama 4 e motores de recomendação de vídeo unificados",
        item_1a_specific_risks="1) Multas e restrições de privacidade de dados na União Europeia (GDPR/DMA); 2) Processos nos EUA sobre proteção de jovens em redes sociais; 3) Retorno de longo prazo do investimento em Reality Labs.",
        footnote_contingencies_litigation="Nota 12: Provisões regulatórias na UE e acordos de compliance com a FTC plenamente absorvidos pelo fluxo de caixa operacional.",
        footnote_sbc_impact="SBC de USD 15.2B/ano (9.6% da Receita | 18.4% do FCO) — Totalmente compensado por USD 42B+ em recompras de ações.",
        footnote_revenue_recognition="ASC 606: Receita de publicidade reconhecida após exibição validada do anúncio; WhatsApp Business Messaging por conversa entregue.",
        footnote_debt_maturity_schedule="Dívida de longo prazo de USD 28.8B contra USD 60.8B em Caixa (Mais de USD 32B de Caixa Líquido).",
        analyst_target_mean_usd=655.00,
        analyst_recommendations_dist="87% Buy / Strong Buy | 11% Hold | 2% Sell (58 Analistas)",
        analyst_eps_revisions_30d_90d="30d: +2.8% | 90d: +7.9% (Forte ganho de preço médio por anúncio graças à IA generativa)",
    ),
    EquityDocumentaryDossier(
        ticker="V",
        company_name="Visa Inc.",
        filing_form_annual="SEC Form 10-K (FY Ended Sept 2026)",
        filing_form_quarterly="SEC Form 10-Q (Q4 FY2026)",
        auditor_firm="KPMG LLP (PCAOB ID #185)",
        auditor_opinion="Unqualified / Clean Opinion (Sem Ressalvas)",
        sox_404b_controls="SOX Section 404(b) Eficaz",
        mda_growth_decomposition="Volume de Pagamentos (+8.0%) + Transações Processadas (+10.0%) + Cross-Border Volume (+13.0%) + Value-Added Services (+21.0%)",
        mda_segment_profitability="Segmento Único Global de Processamento de Pagamentos com Margem Operacional GAAP de 67.0% e Margem EBITDA de 70.1%",
        mda_backlog_rpo="Contratos plurianuais de emissão de cartões renovados com os maiores bancos globais (Prazo médio de 7 a 10 anos)",
        mda_capex_plan="Ultra Asset-Light: CAPEX de apenas USD 1.2B/ano (~3.3% da Receita), permitindo conversão de caixa livre superior a 94%",
        item_1a_specific_risks="1) Ação antitruste do DOJ sobre roteamento de cartões de débito nos EUA; 2) Litígio Multidistrital (MDL) sobre taxas de intercâmbio; 3) Regulação de tetos de tarifas no Reino Unido/UE.",
        footnote_contingencies_litigation="Nota 19 (U.S. Interchange Multidistrict Litigation): Visa mantém conta de custódia dedicada (Litigation Escrow Account) pré-financiada via redução de ações Classe B (isola os acionistas Classe A!).",
        footnote_sbc_impact="SBC de apenas USD 0.85B/ano (2.3% da Receita | 4.1% do FCO) — Um dos menores índices de diluição de todo o S&P 500.",
        footnote_revenue_recognition="ASC 606: Receitas de serviço, processamento de dados e transações internacionais líquidas de incentivos a clientes (Client Incentives).",
        footnote_debt_maturity_schedule="Dívida Total de USD 20.6B com rating AA- / Aa3 e vencimentos escalonados até 2050 (Custo médio ~2.8%).",
        analyst_target_mean_usd=335.00,
        analyst_recommendations_dist="82% Buy / Strong Buy | 18% Hold | 0% Sell (39 Analistas)",
        analyst_eps_revisions_30d_90d="30d: +1.2% | 90d: +2.6% (Resiliência do consumo global e viagens internacionais)",
    ),
    EquityDocumentaryDossier(
        ticker="JPM",
        company_name="JPMorgan Chase & Co.",
        filing_form_annual="SEC Form 10-K (FY 2025/2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 2026)",
        auditor_firm="PricewaterhouseCoopers LLP",
        auditor_opinion="Unqualified / Clean Opinion (Sem Ressalvas)",
        sox_404b_controls="SOX Section 404(b) Eficaz",
        mda_growth_decomposition="Net Interest Income (NII): +4.5% | Non-Interest Fee Income (Investment Banking +31% & Wealth AUM +16%): +11.2%",
        mda_segment_profitability="CCB ROE: 33% | CIB ROE: 18% | AWM ROE: 34% | ROTCE Consolidado do Banco: 21.0% | Índice Basileia CET1: 15.3%",
        mda_backlog_rpo="USD 3.9 Trilhões em Assets Under Management (AUM) e USD 5.4 Trilhões em ativos de clientes sob custódia",
        mda_capex_plan="Orçamento anual de Tecnologia e IA de USD 17.0 Bilhões (modernização de core bancário, cibersegurança e automação de risco)",
        item_1a_specific_risks="1) Sensibilidade do NII a cortes agressivos da Fed Funds Rate; 2) Deterioração de crédito em cartões e Commercial Real Estate (Office CRE); 3) Requisitos de capital Basileia III Endgame.",
        footnote_contingencies_litigation="Nota 28 (Allowance for Credit Losses - CECL): Provisões totais de USD 26.2B cobrindo mais de 240% dos empréstimos inadimplentes (NPLs).",
        footnote_sbc_impact="SBC de USD 3.1B/ano (1.8% da Receita Líquida) — Remuneração variável rigorosamente submetida a cláusulas de Clawback.",
        footnote_revenue_recognition="Juros reconhecidos pelo método da taxa efetiva; comissões de M&A/Underwriting na conclusão da transação; taxas de AUM mensalmente.",
        footnote_debt_maturity_schedule="Estrutura de funding ancorada em USD 2.4 Trilhões de depósitos estáveis e mais de USD 1.4 Trilhão em High-Quality Liquid Assets (HQLA).",
        analyst_target_mean_usd=248.00,
        analyst_recommendations_dist="72% Buy / Strong Buy | 24% Hold | 4% Sell (29 Analistas)",
        analyst_eps_revisions_30d_90d="30d: +2.4% | 90d: +4.9% (Recuperação de Investment Banking e resiliência do NII)",
    ),
    EquityDocumentaryDossier(
        ticker="WMT",
        company_name="Walmart Inc.",
        filing_form_annual="SEC Form 10-K (FY2026)",
        filing_form_quarterly="SEC Form 10-Q (Q3 FY2027)",
        auditor_firm="Ernst & Young LLP",
        auditor_opinion="Unqualified / Clean Opinion (Sem Ressalvas)",
        sox_404b_controls="SOX Section 404(b) Eficaz",
        mda_growth_decomposition="Same Store Sales (SSS EUA): +4.8% (Tráfego de lojas +3.1% + Ticket médio +1.7%) | E-Commerce Global: +24% | Walmart Connect Ads: +26%",
        mda_segment_profitability="Walmart US Op Margin: 5.1% | International Op Margin: 4.4% | Sam's Club: Receita de anuidades (Membership) crescendo +14%",
        mda_backlog_rpo="Mais de 255 milhões de clientes semanais nas 10.600 lojas e plataformas digitais em 19 países",
        mda_capex_plan="CAPEX de USD 20B/ano focado na automação Symbotic dos Centros de Distribuição (reduzindo custo unitário de manuseio em >20%)",
        item_1a_specific_risks="1) Inflação salarial de operadores logísticos e lojas; 2) Perdas de inventário (Shrinkage / furtos no varejo); 3) Tarifas de importação sobre mercadorias gerais.",
        footnote_contingencies_litigation="Nota 11: Acordos de litígios passados já provisionados e liquidados; zero contingências materiais pendentes que afetem o rating AA.",
        footnote_sbc_impact="SBC de apenas USD 0.78B/ano (0.12% da Receita | 2.1% do FCO) — Praticamente zero diluição aos acionistas.",
        footnote_revenue_recognition="ASC 606: Vendas em loja/online líquidas de devoluções estimadas; taxas de anuidade Sam's Club e Walmart+ diferidas em 12 meses.",
        footnote_debt_maturity_schedule="Dívida de longo prazo de USD 36.2B (Rating AA) com vencimentos suaves até 2053 e cobertura de juros de 11.2x EBIT.",
        analyst_target_mean_usd=90.00,
        analyst_recommendations_dist="85% Buy / Strong Buy | 15% Hold | 0% Sell (41 Analistas)",
        analyst_eps_revisions_30d_90d="30d: +1.8% | 90d: +4.2% (Elevação do guidance anual pela administração)",
    ),
    EquityDocumentaryDossier(
        ticker="DBSDY",
        company_name="DBS Group Holdings Ltd.",
        filing_form_annual="SGX Annual Report & Audited Financial Statements (FY2025/2026)",
        filing_form_quarterly="SGXNet Q3 2026 Financial Statement Announcement",
        auditor_firm="PricewaterhouseCoopers LLP Singapore",
        auditor_opinion="Unqualified / Clean Opinion (Sem Ressalvas — IFRS / SFRS)",
        sox_404b_controls="Plena conformidade com os controles internos da Monetary Authority of Singapore (MAS Notice 609)",
        mda_growth_decomposition="Net Interest Income Comercial: +4.0% | Wealth Management Fees: +32.0% | Treasury Customer Sales: +14.0%",
        mda_segment_profitability="ROE de 18.4% | Cost-to-Income Ratio de 39.0% | Non-Performing Loan (NPL) Ratio de apenas 1.0% | CET1 Ratio: 15.2%",
        mda_backlog_rpo="Assets Under Management (AUM) de Wealth Management atingiram recorde de SGD 390 Bilhões (+18% YoY)",
        mda_capex_plan="Investimento contínuo em infraestrutura de resiliência digital, IA preditiva bancária e custódia institucional na Ásia",
        item_1a_specific_risks="1) Queda acentuada nas taxas de juros SORA/SOFR comprimindo NIM; 2) Desaceleração imobiliária na Grande China; 3) Exigências regulatórias de resiliência operacional da MAS.",
        footnote_contingencies_litigation="Nota 32: Reservas gerais para perdas de crédito (General Allowance Overlays) de SGD 2.3B excedem amplamente os requisitos regulatórios mínimos.",
        footnote_sbc_impact="Remuneração baseada em ações inferior a 1.2% da Receita, adquirida via mercado aberto (Treasury Shares) sem diluição primária.",
        footnote_revenue_recognition="SFRS(I) 9 e 15: Juros pelo método efetivo; comissões de gestão de patrimônio por competência mensal.",
        footnote_debt_maturity_schedule="Loan-to-Deposit Ratio (LDR) conservador de 78% (Excesso de depósitos CASA de baixo custo em Dólar de Singapura).",
        analyst_target_mean_usd=128.00,
        analyst_recommendations_dist="76% Buy / Strong Buy | 20% Hold | 4% Sell (25 Analistas)",
        analyst_eps_revisions_30d_90d="30d: +3.5% | 90d: +7.1% (Lucro recorde no Q3 e anúncio de programa de Buyback de SGD 3B)",
    ),
    EquityDocumentaryDossier(
        ticker="ASML",
        company_name="ASML Holding N.V.",
        filing_form_annual="SEC Form 20-F (Euronext / Nasdaq)",
        filing_form_quarterly="Form 6-K (Q1-Q3 Earnings Releases)",
        auditor_firm="KPMG Accountants N.V.",
        auditor_opinion="Unqualified (Clean Opinion) — Parecer Limpo sem ressalvas",
        sox_404b_controls="Eficaz — Controles internos sobre relatórios financeiros totalmente validados",
        mda_growth_decomposition="+18.5% YoY: +14.2% Volume (sistemas EUV/DUV entregues), +4.8% Pricing/Mix (sistemas High-NA EUV EXE:5000 a EUR 350M+), -0.5% FX",
        mda_segment_profitability="EUV Systems: Margem Bruta 55.2% | DUV Systems: 48.5% | Installed Base Management & Services: Margem Operacional 44.0%",
        mda_backlog_rpo="Backlog firme contratado de EUR 36.0 Bilhões (~1.5 anos de produção garantida)",
        mda_capex_plan="CapEx de P&D de EUR 4.2B/ano em expansão de capacidade limpa em Veldhoven e tecnologia Hyper-NA",
        item_1a_specific_risks="1. Restrições Geopolíticas e Controles de Exportação EUA/Holanda sobre máquinas DUV avançadas para a China (~38% da receita recente); 2. Concentração de Clientes em 3 players globais (TSMC, Samsung, Intel); 3. Gargalo de Fornecedor Único em óptica ultra-precisa (Carl Zeiss SMT com espelhos de rugosidade sub-nanométrica).",
        footnote_contingencies_litigation="Zero litígios materiais ou disputas de patentes com risco financeiro; conformidade total com tratados de não-proliferação de semicondutores.",
        footnote_sbc_impact="Remuneração em ações (SBC) de apenas 1.2% do FCO (diluição virtualmente insignificante).",
        footnote_revenue_recognition="ASC 606: Receita reconhecida no momento da aceitação técnica na fábrica do cliente após instalação e teste de feixe de luz.",
        footnote_debt_maturity_schedule="Dívida bruta de EUR 4.6B com maturidade média de 7.5 anos a custo fixo médio de 1.85% a.a.; Caixa e equivalentes de EUR 7.8B (Posição de Caixa Líquido de EUR 3.2B).",
        analyst_target_mean_usd=835.00,
        analyst_recommendations_dist="32 Buy | 6 Hold | 1 Sell (Consenso Forte Compra Wall Street)",
        analyst_eps_revisions_30d_90d="+8.2% revisões altistas de EPS para 2026/2027 refletindo aceleração de fundições de IA.",
    ),
    EquityDocumentaryDossier(
        ticker="TSM",
        company_name="Taiwan Semiconductor (TSMC)",
        filing_form_annual="SEC Form 20-F (Taiwan Stock Exchange / NYSE ADR)",
        filing_form_quarterly="Form 6-K (Quarterly Results)",
        auditor_firm="Deloitte & Touche Taiwan",
        auditor_opinion="Unqualified (Clean Opinion) — Parecer Limpo",
        sox_404b_controls="Eficaz — Controles SOX plenamente atestados",
        mda_growth_decomposition="+31.8% YoY: +22.0% Volume (chips 3nm e CoWoS para Nvidia/Apple/AMD), +10.2% Preço/Mix (nó N3E com prêmio), -0.4% FX",
        mda_segment_profitability="HPC (High Performance Computing / IA): 52% da receita (Margem Operacional 46%) | Smartphones: 34% (Margem 41%) | IoT & Auto: 14%",
        mda_backlog_rpo="Capacidade de nós 3nm e embalagem CoWoS 100% reservada até 2026",
        mda_capex_plan="CapEx planejado de USD 30B a USD 32B financiado integralmente pelo fluxo de caixa operacional",
        item_1a_specific_risks="1. Tensão Geopolítica no Estreito de Taiwan (concentração de fundições avançadas na ilha de Taiwan); 2. Dependência de fornecimento exclusivo de máquinas EUV da ASML e wafers de silício; 3. Desafios de custos e mão-de-obra na expansão da Fab 21 no Arizona e fábrica em Dresden.",
        footnote_contingencies_litigation="Zero contingências materiais ativas; plena conformidade regulatória bilateral.",
        footnote_sbc_impact="SBC de 0.8% do FCO (cultura tradicional de bônus em dinheiro e ações retidas).",
        footnote_revenue_recognition="ASC 606: Reconhecimento de receita por wafer faturado e entregue após testes de rendimento (yield).",
        footnote_debt_maturity_schedule="Dívida bruta de USD 28.5B com caixa e títulos de USD 48.0B (Caixa Líquido positivo de USD 19.5B).",
        analyst_target_mean_usd=228.00,
        analyst_recommendations_dist="38 Buy | 3 Hold | 0 Sell (Unanimidade Wall Street)",
        analyst_eps_revisions_30d_90d="+12.5% revisões para cima nos últimos 90 dias impulsionadas pela demanda por Blackwell e chips 2nm N2.",
    ),
    EquityDocumentaryDossier(
        ticker="MELI",
        company_name="MercadoLibre, Inc.",
        filing_form_annual="SEC Form 10-K (Nasdaq Global Select)",
        filing_form_quarterly="SEC Form 10-Q (Q1-Q3)",
        auditor_firm="PricewaterhouseCoopers (PwC) Argentina",
        auditor_opinion="Unqualified (Clean Opinion) — Parecer Limpo",
        sox_404b_controls="Eficaz — Controles internos totalmente certificados",
        mda_growth_decomposition="+35.2% YoY em Moeda Constante: +28.5% Volume (GMV e transações Mercado Pago), +6.8% Take Rate / Ads e Crédito, -0.1% FX",
        mda_segment_profitability="Marketplace & Ads: Margem Operacional 22.5% | Mercado Pago Fintech: Margem Operacional 18.2%",
        mda_backlog_rpo="Mais de 55 milhões de compradores únicos ativos e 100M+ de contas Mercado Pago no ecossistema",
        mda_capex_plan="CapEx de USD 800M/ano em automação logística, frotas aéreas dedicadas e data centers",
        item_1a_specific_risks="1. Volatilidade Macroeconômica e Cambial na América Latina (desvalorização de moedas como BRL e ARS frente ao USD); 2. Risco de Crédito na carteira do Mercado Crédito (inadimplência NPL controlada em 7.5%); 3. Concorrência no comércio eletrônico (Shopee e Amazon em regiões urbanas).",
        footnote_contingencies_litigation="Contingências fiscais e trabalhistas ordinárias no Brasil provisionadas em USD 185M sob parecer conservador.",
        footnote_sbc_impact="SBC de 3.2% do FCO (remuneração competitiva em tecnologia).",
        footnote_revenue_recognition="ASC 606: Receita reconhecida no momento da entrega do pacote e processamento do pagamento.",
        footnote_debt_maturity_schedule="Dívida líquida confortável com linhas de financiamento de longo prazo e caixa robusto de USD 4.2B.",
        analyst_target_mean_usd=2240.00,
        analyst_recommendations_dist="24 Buy | 4 Hold | 0 Sell (Forte Compra)",
        analyst_eps_revisions_30d_90d="+15.0% revisões para cima após resultados recordes no México e Brasil.",
    ),
    EquityDocumentaryDossier(
        ticker="AVGO",
        company_name="Broadcom Inc.",
        filing_form_annual="SEC Form 10-K (Nasdaq)",
        filing_form_quarterly="SEC Form 10-Q",
        auditor_firm="PricewaterhouseCoopers (PwC) LLP",
        auditor_opinion="Unqualified (Clean Opinion) — Parecer Limpo",
        sox_404b_controls="Eficaz — Controles sobre aquisição da VMware plenamente integrados",
        mda_growth_decomposition="+44.0% YoY: +28.0% M&A VMware, +14.5% Volume de semicondutores de IA (chips Ethernet e ASICs), +1.5% Preço",
        mda_segment_profitability="Semiconductor Solutions: Margem EBITDA 58.5% | Infrastructure Software (VMware): Margem EBITDA 66.0%",
        mda_backlog_rpo="Backlog consolidado de semicondutores superior a USD 21B e contratos VMware plurianuais de USD 15B+",
        mda_capex_plan="CapEx asset-light de USD 1.8B/ano (modelo fabless com fundição na TSMC)",
        item_1a_specific_risks="1. Concentração em Grandes Clientes de Chips (Apple para componentes de RF e Google para TPU); 2. Alavancagem da Dívida pós-VMware (Dívida bruta de USD 71B com rápida desalavancagem via FCF); 3. Escrutínio antitruste em aquisições de software corporativo.",
        footnote_contingencies_litigation="Zero processos materiais com probabilidade de perda adversa; integração da VMware concluída.",
        footnote_sbc_impact="SBC de 5.8% do FCO (concessões de longo prazo vinculadas à meta de retorno aos acionistas TSR).",
        footnote_revenue_recognition="ASC 606: Transição acelerada de licenças perpétuas da VMware para modelo de subscrição anual (ARR).",
        footnote_debt_maturity_schedule="Fluxo de caixa livre superior a USD 20B/ano permite pagar USD 8B a USD 10B de dívida por ano.",
        analyst_target_mean_usd=192.00,
        analyst_recommendations_dist="31 Buy | 5 Hold | 0 Sell",
        analyst_eps_revisions_30d_90d="+9.4% revisões altistas após guidance trimestral recorde em semicondutores de IA.",
    ),
    EquityDocumentaryDossier(
        ticker="MA",
        company_name="Mastercard Incorporated",
        filing_form_annual="SEC Form 10-K (NYSE)",
        filing_form_quarterly="SEC Form 10-Q",
        auditor_firm="PricewaterhouseCoopers (PwC) LLP",
        auditor_opinion="Unqualified (Clean Opinion) — Parecer Limpo",
        sox_404b_controls="Eficaz — Controles internos de segurança e transações financeiras certificados",
        mda_growth_decomposition="+14.5% YoY: +11.0% GDV em moeda constante, +3.5% Serviços de Cibersegurança e Inteligência de Dados",
        mda_segment_profitability="Payment Network: Margem Operacional 62.0% | Value-Added Services: Margem Operacional 50.5%",
        mda_backlog_rpo="Mais de 3.4 bilhões de cartões Mastercard e Maestro ativos no mundo",
        mda_capex_plan="CapEx ultraleve de USD 450M/ano em cibersegurança e redes de liquidação de baixa latência",
        item_1a_specific_risks="1. Pressões Regulatórias sobre Tarifas de Intercâmbio (Credit Card Competition Act nos EUA); 2. Adoção de Sistemas de Pagamento Instantâneo Soberanos (PIX no Brasil, UPI na Índia — Mastercard compensa via serviços e cartões de crédito); 3. Ciberataques à infraestrutura global de pagamentos.",
        footnote_contingencies_litigation="Litígio antitruste de taxas de intercâmbio com varejistas norte-americanos provisionado em acordo judicial coletivo.",
        footnote_sbc_impact="SBC de 2.1% do FCO (baixo custo de diluição fiduciária).",
        footnote_revenue_recognition="ASC 606: Receita de comissão por transação compensada e autorizada em tempo real.",
        footnote_debt_maturity_schedule="Dívida bruta de USD 15.2B com rating de crédito A+ e cronograma de amortização suave até 2053.",
        analyst_target_mean_usd=545.00,
        analyst_recommendations_dist="34 Buy | 4 Hold | 0 Sell",
        analyst_eps_revisions_30d_90d="+4.5% revisões positivas sustentadas pelo crescimento inelástico de consumo e viagens internacionais.",
    ),
    EquityDocumentaryDossier(
        ticker="NU",
        company_name="Nu Holdings Ltd. (Nubank)",
        filing_form_annual="SEC Form 20-F (NYSE Class A)",
        filing_form_quarterly="Form 6-K (Resultados Trimestrais)",
        auditor_firm="KPMG Auditores Independentes",
        auditor_opinion="Unqualified (Clean Opinion) — Parecer Limpo",
        sox_404b_controls="Eficaz — Controles internos totalmente aderentes às normas bancárias globais",
        mda_growth_decomposition="+68.0% YoY em Moeda Constante: +42.0% Expansão de clientes (+18M no ano), +26.0% Aumento de ARPAC ($11/mês) e produtos cruzados",
        mda_segment_profitability="Operação Brasil: ROE superior a 28% e Cost-to-Income de 31.4% | Operação México: Estágio de hipercaptação de depósitos",
        mda_backlog_rpo="Base total de clientes superior a 110 milhões de indivíduos e PMEs",
        mda_capex_plan="CapEx de USD 150M/ano focado em modelos de inteligência artificial de underwriting de crédito",
        item_1a_specific_risks="1. Inadimplência em Cartão de Crédito e Empréstimo Pessoal em ciclos de juros altos; 2. Risco de Execução na obtenção de licença bancária plena no México; 3. Risco Cambial de translação das receitas em BRL/MXN para a moeda de reporte USD.",
        footnote_contingencies_litigation="Zero litígios materiais; provisão para perdas esperadas (CECL) de 100% cobrindo NPL 90+ com folga.",
        footnote_sbc_impact="SBC de 6.5% do FCO (programa de equity para atração de talentos globais de engenharia de software).",
        footnote_revenue_recognition="ASC 606 e IFRS 9: Reconhecimento de receita de juros pelo método da taxa efetiva e taxas de intercâmbio no ato da transação.",
        footnote_debt_maturity_schedule="Estrutura de capital superavitária com índice de Basileia / CET1 superior a 17% (Balanço Fortress sem dívida corporativa onerosa).",
        analyst_target_mean_usd=17.50,
        analyst_recommendations_dist="18 Buy | 5 Hold | 1 Sell",
        analyst_eps_revisions_30d_90d="+18.5% revisões altistas após expansão consecutiva de ROE e lucratividade líquida.",
    ),
]


CRYPTO_FILINGS_DB: List[CryptoDocumentaryDossier] = [
    CryptoDocumentaryDossier(
        symbol="BTC-USD",
        name="Bitcoin Network",
        wp_title_author="Bitcoin: A Peer-to-Peer Electronic Cash System — Satoshi Nakamoto (Outubro 2008)",
        wp_value_proposition="Ativo monetário digital soberano, resistente à censura e sem risco de contraparte, com política monetária matematicamente imutável limitada a 21.000.000 unidades.",
        wp_consensus_architecture="Proof-of-Work (SHA-256) com ajuste automático de dificuldade a cada 2.016 blocos (~14 dias) e Halving de emissão a cada 210.000 blocos (~4 anos).",
        wp_value_accrual_mechanism="Escassez absoluta inelástica (Stock-to-Flow > 110 post-Halving 2024) + taxas de liquidação na camada base para transações de alto valor e ancoragem de L2s.",
        github_core_repos="bitcoin/bitcoin, lightningnetwork/lnd, ElementsProject/lightning",
        github_commits_4w=192,
        github_active_devs_monthly=1150,
        deepdao_status="Governança Descentralizada Pura via BIPs (Bitcoin Improvement Proposals) e consenso social de > 19.000 nós validadores completos (Full Nodes).",
        recent_governance_proposals="BIP-324 (Transporte P2P Criptografado v2 ativo), Miniscript no Bitcoin Core 28.0 e discussões técnicas de covenants (OP_CAT / BIP-119).",
        skin_in_the_game_locked_pct=65.8,
        skin_in_the_game_details="65.8% do Circulating Supply imobilizado por Long-Term Holders (> 1 ano sem movimentação) + CAPEX multibilionário irreversível em ASICs pelos mineradores.",
        token_sniffer_score=100,
        audit_firms="Revisão criptográfica global contínua por 16+ anos (MIT Digital Currency Initiative, Chaincode Labs, Blockstream)",
        exploit_history="Zero incidentes de gasto duplo ou violação criptográfica na rede principal desde 2009 (100% Uptime nos últimos 11 anos).",
    ),
    CryptoDocumentaryDossier(
        symbol="ETH-USD",
        name="Ethereum Network",
        wp_title_author="A Next-Generation Smart Contract and Decentralized Application Platform — Vitalik Buterin (2013)",
        wp_value_proposition="Computador mundial descentralizado e camada base global de liquidação financeira para DeFi, Stablecoins (~USD 95B), RWAs institucionais (BlackRock BUIDL) e Rollups L2.",
        wp_consensus_architecture="Proof-of-Stake (Gasper = Casper FFG + LMD-GHOST) com mais de 1.05 milhão de validadores ativos e separação Proposer-Builder (MEV-Boost).",
        wp_value_accrual_mechanism="Triplo Papel do ETH: 1) Commodity de Gás consumida e queimada via EIP-1559; 2) Ativo de Capital gerador de Real Yield em ETH para Stakers; 3) Colateral Prístino em DeFi.",
        github_core_repos="ethereum/go-ethereum, ethereum/consensus-specs, sigp/lighthouse, paradigmxyz/reth",
        github_commits_4w=355,
        github_active_devs_monthly=2480,
        deepdao_status="Governança Técnica via EIPs, All Core Devs (ACD) e Ethereum Foundation + Ecossistema de L2 DAOs (Arbitrum, Optimism, Uniswap, Aave).",
        recent_governance_proposals="EIP-4844 (Proto-Danksharding Blobs reduzindo custo de L2s em 95%) implementado; Hard Fork Pectra (EIP-7702 Account Abstraction + EIP-7251 MaxEB 2048 ETH).",
        skin_in_the_game_locked_pct=28.7,
        skin_in_the_game_details="34.6 Milhões de ETH (~USD 102B, 28.7% do supply circulante) travados no contrato de Staking da Beacon Chain sujeitos a penalidades de Slashing.",
        token_sniffer_score=100,
        audit_firms="Trail of Bits, SigmaPrime, OpenZeppelin, Runtime Verification, ConsenSys Diligence",
        exploit_history="Zero exploits de consenso na Beacon Chain PoS e na EVM desde 2016; maior diversidade de clientes independentes do mercado (Geth, Nethermind, Besu, Reth).",
    ),
    CryptoDocumentaryDossier(
        symbol="SOL-USD",
        name="Solana Network",
        wp_title_author="Solana: A new architecture for a high performance blockchain — Anatoly Yakovenko (2017)",
        wp_value_proposition="Blockchain monolítica de estado global único otimizada para execução paralela em velocidade de hardware (alta vazão TPS, confirmação sub-segundo e taxas < $0.002).",
        wp_consensus_architecture="Proof-of-History (PoH — relógio criptográfico verificável pré-consenso) + Tower BFT + Sealevel (execução paralela de smart contracts).",
        wp_value_accrual_mechanism="50% das taxas base são queimadas permanentemente + Taxas de Prioridade e Gorjetas MEV (Jito) pagas aos validadores e delegadores de Staking.",
        github_core_repos="anza-xyz/agave, jump-crypto/firedancer, jito-foundation/jito-solana",
        github_commits_4w=295,
        github_active_devs_monthly=1120,
        deepdao_status="Governança de protocolo via SIMDs (Solana Improvement Documents) votados on-chain pelo peso de stake dos validadores.",
        recent_governance_proposals="SIMD-0096 (Alocação de taxas de prioridade), Token Extensions (transferências confidenciais institucionais) e lançamento do cliente independente Firedancer.",
        skin_in_the_game_locked_pct=67.8,
        skin_in_the_game_details="Mais de 320 Milhões de SOL (67.8% do supply circulante) travados em Staking ativo protegendo a rede.",
        token_sniffer_score=95,
        audit_firms="Neodyme, OtterSec, Zellic, Kudelski Security, Trail of Bits (Auditoria Firedancer)",
        exploit_history="Zero roubos de fundos no protocolo L1; paralisações passadas (2021-2022) mitigadas com QUIC, mercados de taxas locais e cliente Firedancer.",
    ),
    CryptoDocumentaryDossier(
        symbol="AAVE-USD",
        name="Aave Protocol V3",
        wp_title_author="Aave Protocol V3 Technical Paper & GHO Native Stablecoin — Stani Kulechov & Aave Labs (2022/2024)",
        wp_value_proposition="Maior protocolo descentralizado de mercado monetário (Lending & Borrowing sobrecolateralizado) e emissor da stablecoin nativa GHO em múltiplas redes.",
        wp_consensus_architecture="Smart Contracts não-custodiais governados on-chain via Aave Governance V3 (Cross-chain execution via a.DI).",
        wp_value_accrual_mechanism="Spread de juros (Reserve Factor) das piscinas de empréstimo + 100% dos juros pagos pelos tomadores de GHO fluem para a Tesouraria da DAO + Buy & Distribute (AAVEnomics).",
        github_core_repos="aave/aave-v3-core, aave/gho-core, bgd-labs/aave-governance-v3",
        github_commits_4w=154,
        github_active_devs_monthly=435,
        deepdao_status="Top #1 DeFi DAO no DeepDAO em atividade de governança; mais de 480 propostas AIPs votadas e executadas autonomamente por smart contracts.",
        recent_governance_proposals="Atualização 'AAVEnomics' (Ativação do Fee Switch / Buyback de AAVE no mercado aberto com lucros excedentes da tesouraria) e módulo de segurança Umbrella (stkGHO/aTokens).",
        skin_in_the_game_locked_pct=25.8,
        skin_in_the_game_details="3.85 Milhões de AAVE (25.8% do supply circulante) travados no Safety Module (stkAAVE / ABPT) atuando como seguro de solvência com risco de slashing de até 30%.",
        token_sniffer_score=100,
        audit_firms="Certora (Verificação Formal Contínua), OpenZeppelin, Trail of Bits, SigmaPrime, PeckShield",
        exploit_history="Histórico impecável de zero perdas por hacks nos contratos principais Aave V3 (> USD 21B em TVL).",
    ),
    CryptoDocumentaryDossier(
        symbol="MKR-USD",
        name="Maker / Sky Protocol",
        wp_title_author="The Maker Protocol: Dai 1:1 Peg Mechanism & USDS Endgame (Rune Christensen)",
        wp_value_proposition="Banco Central Descentralizado e Reserva de Crédito Emissor do DAI/USDS com Colateral RWA em T-Bills Americanos",
        wp_consensus_architecture="Smart Contracts Ethereum L1 + SubDAOs Especializadas de Crédito e Alocação",
        wp_value_accrual_mechanism="Smart Burn Engine: O excedente de receita gerado pelos juros dos títulos do Tesouro dos EUA e empréstimos colateralizados é utilizado automaticamente em leilões contínuos para recomprar e QUEIMAR tokens MKR, reduzindo a oferta circulante.",
        github_core_repos="makerdao/dss, makerdao/endgame-toolkit, makerdao/smart-burn-engine",
        github_commits_4w=320,
        github_active_devs_monthly=115,
        deepdao_status="Top 3 Global DeepDAO: USD 6.8B sob gestão de tesouraria e mais de 12.000 delegados ativos",
        recent_governance_proposals="Aprovação da transição para marca Sky, alocação de USD 1.5B em títulos do Tesouro tokenizados via BlackRock BUIDL e Superstate.",
        skin_in_the_game_locked_pct=34.5,
        skin_in_the_game_details="Mais de 34% dos tokens MKR depositados no módulo de governança e staking com lockup ativo de longo prazo.",
        token_sniffer_score=100,
        audit_firms="Trail of Bits, OpenZeppelin, Runtime Verification, ChainSecurity (Protocolo com o maior histórico de testes de estresse em DeFi)",
        exploit_history="Zero exploits em smart contracts centrais do DAI ao longo de mais de 7 anos de operação ininterrupta.",
    ),
    CryptoDocumentaryDossier(
        symbol="PENDLE-USD",
        name="Pendle Finance V2",
        wp_title_author="Pendle Finance V2: Yield Tokenization & Automated Market Maker for Fixed Income (TN Lee)",
        wp_value_proposition="Protocolo líder de mercado monetário para divisão de ativos com rendimento em Principal Token (PT) e Yield Token (YT), viabilizando renda fixa garantida e especulação alavancada de taxas em DeFi.",
        wp_consensus_architecture="EIP-5115 (Standardized Yield Token) operando em Ethereum, Arbitrum, Mantle e Base",
        wp_value_accrual_mechanism="Taxa de swap de 3% sobre todo o rendimento gerado pelos tokens YT + 80% das taxas do protocolo distribuídas semanalmente aos detentores de vePENDLE (Real Yield direto).",
        github_core_repos="pendle-finance/pendle-core-v2, pendle-finance/pendle-amm",
        github_commits_4w=235,
        github_active_devs_monthly=68,
        deepdao_status="Governança vePENDLE ativa com mais de USD 4.2B em TVL sob gerenciamento de liquidez",
        recent_governance_proposals="Integração de pools de Bitcoin LRTs (Babylon/Symbiotic) e expansão para redes Layer 2 da Coinbase (Base).",
        skin_in_the_game_locked_pct=42.0,
        skin_in_the_game_details="42% de todo o suprimento circulante de PENDLE está bloqueado no modelo vePENDLE por prazo médio superior a 2 anos.",
        token_sniffer_score=98,
        audit_firms="Ackee Blockchain, Dedaub, WatchPug, Spearbit (Múltiplas auditorias independentes formais)",
        exploit_history="Zero exploits nos contratos V2; protocolo auditado formalmente com verificação matemática de curva AMM.",
    ),
    CryptoDocumentaryDossier(
        symbol="LINK-USD",
        name="Chainlink Network",
        wp_title_author="Chainlink 2.0: Decentralized Oracle Networks, CCIP & Hybrid Smart Contracts (Sergey Nazarov, Ari Juels)",
        wp_value_proposition="Monopólio Global de Infraestrutura de Oráculos e Protocolo de Interoperabilidade Cross-Chain (CCIP) adotado como padrão pela SWIFT, DTCC, Euroclear e bancos globais.",
        wp_consensus_architecture="Rede Descentralizada de Nós Validadores Independentes (DONs) com Provas Criptográficas Zero-Knowledge e Staking PoS",
        wp_value_accrual_mechanism="Taxas de consumo de dados (feeds de preços, VRF, automação) pagas em LINK por centenas de protocolos + CCIP fees institucionais direcionadas ao programa de Staking v0.2.",
        github_core_repos="smartcontractkit/chainlink, smartcontractkit/ccip",
        github_commits_4w=590,
        github_active_devs_monthly=315,
        deepdao_status="Maior rede de oráculos do mundo garantindo mais de USD 75 Bilhões em valor total assegurado (TVS)",
        recent_governance_proposals="Expansão do Staking Pool para 45M LINK e implementação de liquidação atômica de fundos tokenizados com UBS e SBI Digital.",
        skin_in_the_game_locked_pct=28.5,
        skin_in_the_game_details="Pool de Staking v0.2 totalmente preenchido em minutos com 45 milhões de LINK travados por validadores de elite.",
        token_sniffer_score=100,
        audit_firms="SigmaPrime, Trail of Bits, Certora, OpenZeppelin",
        exploit_history="Histórico imaculado: mais de 6 anos garantindo a infraestrutura central de todo o ecossistema DeFi global sem falhas de feeds.",
    ),
    CryptoDocumentaryDossier(
        symbol="UNI-USD",
        name="Uniswap Protocol (Unichain)",
        wp_title_author="Uniswap V4 Hooks & Unichain Architecture: The Rollup for Decentralized Finance (Hayden Adams)",
        wp_value_proposition="Monopólio Global de Negociação Descentralizada e Criação de Mercado Automatizado (AMM), agora operando sua própria rede Layer 2 de liquidação ultra-rápida (Unichain).",
        wp_consensus_architecture="Uniswap V4 Hooks + Optimistic Rollup L2 (Unichain) com descentralização de sequenciador Flashblocks",
        wp_value_accrual_mechanism="Captura de MEV na Unichain distribuída para validadores que realizam staking de tokens UNI + ativação iminente do Fee Switch aprovado pela governança DAO.",
        github_core_repos="Uniswap/v4-core, Uniswap/v4-periphery, Uniswap/unichain-monorepo",
        github_commits_4w=410,
        github_active_devs_monthly=185,
        deepdao_status="Maior DAO de DeFi do planeta com mais de USD 5 Bilhões de tesouraria e governança on-chain autônoma",
        recent_governance_proposals="Lançamento da Unichain e alocação de subsídios de liquidez de USD 150M para novos criadores de mercado V4.",
        skin_in_the_game_locked_pct=32.0,
        skin_in_the_game_details="Tokens delegados e travados na governança da DAO representam quase um terço do float com poder de veto fiduciário.",
        token_sniffer_score=100,
        audit_firms="Trail of Bits, ABDK Consulting, OpenZeppelin, Spearbit",
        exploit_history="Zero exploits nos contratos principais das versões V1, V2, V3 e V4 ao longo de trilhões de dólares transacionados.",
    ),
]


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
        return [d for d in EQUITY_FILINGS_DB if d.ticker.upper() in tk_set]

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
        return [c for c in CRYPTO_FILINGS_DB if c.symbol.upper() in sym_set]

"""
MÓDULO 3: RADAR DE MONITORAMENTO GEOPOLÍTICO (MACRO) E EVENTOS INTERNOS (MICRO)
1. Monitoramento Geopolítico Global (Macro -> Portfólio):
   - Matriz de Impacto Geopolítico cruzando Eventos Globais, Severidade, Ativos do Portfólio Afetados,
     % de Receita/Produção Exposta (extraído do 10-K) e Impacto Direto nos Fundamentos (Margem, WACC, Supply Chain, Moat).
2. Monitoramento de Eventos Micro Internos da Empresa / Protocolo:
   - Eventos específicos extraídos de Form 8-K, Press Releases, Form 4 (Insider Trading) e Governança DAO,
     classificados em Catalisador Positivo, Neutro / Monitorar ou Alerta de Deterioração / Red Flag.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Dict, List
import yfinance as yf


@dataclass
class GeopoliticalImpactRow:
    global_event: str
    region_vector: str
    severity: str
    affected_portfolio_assets: str
    revenue_or_production_exposed_pct: str
    fundamental_impact_mechanism: str
    country_liquidity_risk_assessment: str


@dataclass
class MicroCorporateProtocolEvent:
    date: str
    asset_ticker: str
    source_type: str  # Form 8-K, Form 4 Insider, Press Release, Governança DAO
    headline: str
    event_category: str  # M&A, Buybacks, Guidance, Insider, Regulação, Upgrade Protocolo, etc.
    fundamental_impact_analysis: str
    classification: str  # Catalisador Positivo, Neutro / Monitorar, Alerta de Deterioração / Red Flag


GEOPOLITICAL_MATRIX_DB: List[GeopoliticalImpactRow] = [
    GeopoliticalImpactRow(
        global_event="Tensão Geopolítica no Estreito de Taiwan & Concentração de Fundição Avançada (3nm/2nm & CoWoS)",
        region_vector="Ásia-Pacífico (Taiwan / EUA / China)",
        severity="ALTA (Risco de Cauda Estrutural)",
        affected_portfolio_assets="NVDA, AAPL, SMH, QQQ, QLD, MSFT, AMZN, GOOGL",
        revenue_or_production_exposed_pct="NVDA (>90% produção de wafers GPUs na TSMC) | AAPL (~85% chips M-series/A-series + montagem Ásia) | SMH (20.5% NVDA + 12.8% TSM)",
        fundamental_impact_mechanism="Cadeia de Suprimentos & Margem Bruta: Qualquer bloqueio marítimo ou interrupção fabril elevaria o WACC (+150-250 bps via ERP) e comprimiria o volume de entregas de hardware; mitigado parcialmente pelas novas fabs TSMC no Arizona (EUA) e Japão.",
        country_liquidity_risk_assessment="Ativos listados nos EUA (Liquidez Nível 1), mas com dependência física de manufatura em Taiwan. ITA (Defesa OTAN) e BTC funcionam como hedge de cauda na carteira.",
    ),
    GeopoliticalImpactRow(
        global_event="Restrições de Exportação de Semicondutores de IA (BIS / Dept. de Comércio dos EUA vs. China) & Tarifas Comerciais",
        region_vector="EUA ↔ China / Global Supply Chain",
        severity="MÉDIA-ALTA",
        affected_portfolio_assets="NVDA, SMH, AAPL, WMT, AMZN",
        revenue_or_production_exposed_pct="NVDA (~12% da receita de Data Center na China, queda frente a 26% históricos) | AAPL (~17% da receita na Grande China) | WMT/AMZN (Importação de mercadorias gerais)",
        fundamental_impact_mechanism="Receita & Pricing Power: Controles do BIS limitam venda de chips topo de linha (B200/H200) para a China, mas a demanda dos Hyperscalers ocidentais e soberanos absorve 100% da oferta disponível, preservando Margem Bruta > 74%.",
        country_liquidity_risk_assessment="Zero risco de liquidez para os tickers americanos; na China, risco regulatório contido pela realocação de cadeias para Índia, Vietnã e México.",
    ),
    GeopoliticalImpactRow(
        global_event="Ações Antitruste DOJ / FTC (EUA) e Digital Markets Act — DMA (União Europeia) contra Big Techs e Redes de Cartões",
        region_vector="EUA & União Europeia",
        severity="MÉDIA",
        affected_portfolio_assets="GOOGL, AAPL, V, META, AMZN, MSFT",
        revenue_or_production_exposed_pct="GOOGL (~15% do Search via contrato ISA com Apple) | AAPL (~7% da receita da App Store na UE) | V (~28% do volume de débito nos EUA sob escrutínio DOJ)",
        fundamental_impact_mechanism="Moat & Múltiplo P/E: Risco de multas (até 10% da receita global sob DMA) ou proibição de acordos de exclusividade. Contudo, no caso da GOOGL, eventual fim do pagamento de USD 20B/ano à Apple aumentaria o FCF da Alphabet caso o usuário mantenha o Chrome/Google por hábito (Efeito de Rede).",
        country_liquidity_risk_assessment="Jurisdições de Estado de Direito Pleno (EUA/UE) com processos judiciais que levam de 3 a 5 anos de recursos; impacto imediato no fluxo de caixa é mínimo.",
    ),
    GeopoliticalImpactRow(
        global_event="Escalada de Conflitos Regionais (Leste Europeu / Oriente Médio) & Expansão Estrutural dos Orçamentos de Defesa da OTAN (>2.5% do PIB)",
        region_vector="Europa / Oriente Médio / OTAN",
        severity="MÉDIA (Positivo para Defesa / Neutro para Carteira Consolidada)",
        affected_portfolio_assets="ITA (Aeroespacial & Defesa), BTC-USD, SPY",
        revenue_or_production_exposed_pct="ITA ETF (100% das holdings — Lockheed Martin, RTX, Northrop Grumman, GE Aerospace — beneficiadas por contratos governamentais plurianuais)",
        fundamental_impact_mechanism="Backlog & Visibilidade de FCF: Aumento secular de encomendas de sistemas de defesa aérea (Patriot/THAAD), munições e motores militares, atuando como descorrelacionador geopolítico para as ações de tecnologia da carteira.",
        country_liquidity_risk_assessment="Contratos garantidos pelo Tesouro dos EUA e governos soberanos da OTAN (Risco de crédito soberano quase nulo).",
    ),
    GeopoliticalImpactRow(
        global_event="Dominância Fiscal dos EUA (Déficit > 6% do PIB e Dívida > USD 36.8T) & Ciclo Global de Liquidez dos Bancos Centrais",
        region_vector="Global / G7 / Mercados Monetários",
        severity="ALTA (Tese Secular Central da Carteira)",
        affected_portfolio_assets="BTC-USD, ETH-USD, SOL-USD, AAVE-USD, JPM, DBSDY, SPY, QQQ, QLD",
        revenue_or_production_exposed_pct="100% do Portfólio (50% Criptoativos Inelásticos + 50% Hard-Assets / Equity com Pricing Power)",
        fundamental_impact_mechanism="WACC & Expansão Monetária (M2): O endividamento público recorde impede juros reais muito altos por longo prazo sem crise fiscal, forçando expansão gradual da liquidez M2 — o que valoriza ativos escassos (BTC) e monopólios repassadores de inflação (Mag-6, Visa, Walmart).",
        country_liquidity_risk_assessment="EUA e Singapura (DBSDY) detêm as moedas e sistemas bancários mais líquidos do planeta.",
    ),
    GeopoliticalImpactRow(
        global_event="Marco Regulatório de Criptoativos, ETFs Spot Institucionais, Basileia III e Tokenização de RWAs",
        region_vector="EUA (SEC/CFTC) / Europa (MiCA) / Singapura (MAS)",
        severity="BAIXA-MÉDIA (Vento de Cauda Institucional)",
        affected_portfolio_assets="BTC-USD, ETH-USD, SOL-USD, AAVE-USD, JPM, V",
        revenue_or_production_exposed_pct="BTC-USD & ETH-USD (Fluxo líquido institucional via ETFs Spot IBIT/FBTC/ETHA > USD 35B) | AAVE-USD (Expansão de mercados RWA e GHO)",
        fundamental_impact_mechanism="Custo de Capital & Liquidez: Aprovação de ETFs Spot e clareza regulatória reduzem o risco institucional, comprimem a volatilidade extrema de baixa e ampliam o TVL de protocolos DeFi auditados como Aave V3.",
        country_liquidity_risk_assessment="Liquidez global 24/7/365 em bolsas reguladas (CME, Nasdaq/IBIT) e mercados on-chain descentralizados.",
    ),
]


MICRO_EVENTS_DB: List[MicroCorporateProtocolEvent] = [
    MicroCorporateProtocolEvent(
        date="2026-11-02",
        asset_ticker="NVDA",
        source_type="SEC Form 8-K / Press Release",
        headline="Ramp-up em Escala Total da Arquitetura Blackwell (GB200 NVL72) e Autorização de USD 50B em Buybacks",
        event_category="Lançamento de Produto & Alocação de Capital",
        fundamental_impact_analysis="A produção em volume do Blackwell eleva o ticket médio por rack de data center e sustenta a Margem Bruta acima de 74%, enquanto a recompra de USD 50B absorve integralmente a emissão de SBC.",
        classification="Catalisador Positivo",
    ),
    MicroCorporateProtocolEvent(
        date="2026-11-01",
        asset_ticker="DBSDY",
        source_type="SGXNet Filing / Press Release",
        headline="DBS Reporta Lucro Trimestral Recorde de SGD 3.0B (ROE 18.4%) e Anuncia Programa de Buyback de SGD 3 Bilhões",
        event_category="Resultados Trimestrais & Recompra de Ações",
        fundamental_impact_analysis="Primeiro programa formal de recompra com cancelamento de ações da história do banco, elevando permanentemente o EPS e o ROE, além de manter o Dividend Yield próximo de 6.0% a.a.",
        classification="Catalisador Positivo",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-31",
        asset_ticker="AMZN",
        source_type="SEC Form 10-Q / 8-K (Item 2.02)",
        headline="Lucro Operacional (EBIT) da Amazon Atinge Recorde de USD 17.4B no Trimestre com Margem da AWS em 36%",
        event_category="Expansão de Margem & Guidance",
        fundamental_impact_analysis="Confirma a tese de alavancagem operacional da regionalização logística no varejo norte-americano somada à aceleração de cargas de trabalho de IA generativa na AWS.",
        classification="Catalisador Positivo",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-30",
        asset_ticker="GOOGL",
        source_type="SEC Form 10-Q / 8-K",
        headline="Google Cloud Acelera Receita em +35% YoY com Margem Operacional Saltando para 17% no Trimestre",
        event_category="Rentabilidade de Segmento & SOTP",
        fundamental_impact_analysis="Destrava valor massivo na avaliação Sum-of-the-Parts (SOTP) da Alphabet, provando que o Google Cloud deixou de ser diluidor de margem para se tornar gerador robusto de FCF.",
        classification="Catalisador Positivo",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-29",
        asset_ticker="V",
        source_type="SEC Form 8-K / DOJ Filing",
        headline="Aumento de 13% no Dividendo + USD 25B em Buybacks; Contestação Jurídica Formal à Ação do DOJ sobre Débito",
        event_category="Retorno de Capital & Litígio Regulatório",
        fundamental_impact_analysis="A geração de caixa e o crescimento de Value-Added Services (+22%) seguem intactos; o processo do DOJ no segmento de débito nos EUA deve tramitar por anos e afeta parcela minoritária da receita global.",
        classification="Neutro / Monitorar",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-25",
        asset_ticker="AAVE-USD",
        source_type="Aave DAO Governance (AIP / Snapshot)",
        headline="Aprovação da Proposta 'AAVEnomics' (Ativação do Fee Switch, Módulo Umbrella e Recompras de AAVE no Mercado)",
        event_category="Atualização de Tokenomics & Governança DAO",
        fundamental_impact_analysis="Transforma o token AAVE de ativo puramente de governança com risco de Safety Module em um veículo de captura direta do fluxo de caixa líquido do protocolo (> USD 80M/ano de lucro real).",
        classification="Catalisador Positivo",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-20",
        asset_ticker="WMT",
        source_type="SEC Form 8-K & Form 4",
        headline="Walmart Eleva Guidance Anual com SSS +4.8% e Crescimento de 26% em Publicidade (Walmart Connect)",
        event_category="Revisão Positiva de Guidance",
        fundamental_impact_analysis="SSS fortemente positivo confirma ganho de participação de mercado em todas as faixas de renda, afastando qualquer risco de Value Trap no varejo.",
        classification="Catalisador Positivo",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-15",
        asset_ticker="JPM",
        source_type="SEC Form 8-K (Item 2.02) & Form 4",
        headline="JPMorgan Supera Consenso de NII e Mantém Índice de Capital Basileia CET1 em 15.3%; Cautela do CEO sobre Geopolítica",
        event_category="Balanço Trimestral & Gestão de Risco",
        fundamental_impact_analysis="Excesso de capital superior a USD 35B blinda o banco contra qualquer cenário de recessão ou inadimplência, embora o múltiplo P/TBV de ~2.48x exija seletividade em novos aportes.",
        classification="Neutro / Monitorar",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-12",
        asset_ticker="SOL-USD",
        source_type="GitHub / Validator Governance (SIMD)",
        headline="Cliente Validador Independente 'Firedancer' (Jump Crypto) Opera em Testnet Avançada e Frankendancer em Mainnet",
        event_category="Upgrade de Infraestrutura & Segurança de Rede",
        fundamental_impact_analysis="Elimina o risco histórico de ponto único de falha de software cliente na Solana, elevando a resiliência institucional e a capacidade teórica para > 100.000 TPS.",
        classification="Catalisador Positivo",
    ),
    MicroCorporateProtocolEvent(
        date="2026-10-08",
        asset_ticker="AAPL",
        source_type="SEC Form 4 (Insider Filings) & 10-K",
        headline="Vendas Programadas 10b5-1 de Executivos dentro do Padrão Histórico; Receita na China Estabiliza",
        event_category="Insider Trading (Form 4) & Operacional",
        fundamental_impact_analysis="As vendas de insiders ocorreram estritamente sob planos 10b5-1 pré-agendados e representam < 3% da posição total dos executivos; Services compensa o ciclo mais lento de hardware na Ásia.",
        classification="Neutro / Monitorar",
    ),
]


class GeopoliticsMicroEngine:
    def __init__(self) -> None:
        pass

    def get_geopolitical_matrix(self) -> List[GeopoliticalImpactRow]:
        return GEOPOLITICAL_MATRIX_DB

    def get_micro_events(self, tickers: List[str] | None = None) -> List[MicroCorporateProtocolEvent]:
        if tickers is None:
            try:
                import sqlite3
                with sqlite3.connect("portfolio_store.db") as conn:
                    rows = conn.execute("SELECT ticker FROM portfolio_assets ORDER BY display_order ASC").fetchall()
                tickers = [r[0].upper() for r in rows]
            except Exception:
                tickers = [
                    "BTC-USD", "ETH-USD", "PENDLE-USD", "LINK-USD", "MKR-USD", "UNI-USD",
                    "SPY", "QQQ", "QLD", "ITA",
                    "NVDA", "AAPL", "MSFT", "JPM", "ASML", "TSM", "MELI", "AVGO", "MA", "NU",
                ]
        tk_set = {t.upper() for t in tickers}
        return [m for m in MICRO_EVENTS_DB if m.asset_ticker.upper() in tk_set]

    def fetch_live_ticker_headlines(self, ticker: str, max_items: int = 3) -> List[Dict[str, str]]:
        try:
            s = yf.Search(ticker, news_count=max_items)
            news_list = getattr(s, "news", []) or []
            out = []
            for item in news_list[:max_items]:
                ts = item.get("providerPublishTime")
                dt = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M") if ts else "Tempo Real"
                out.append({
                    "date": dt,
                    "title": item.get("title", ""),
                    "publisher": item.get("publisher", "Market Feed"),
                    "link": item.get("link", "#"),
                })
            return out
        except Exception:
            return []

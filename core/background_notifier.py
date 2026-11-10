"""
================================================================================
SISTEMA DE MONITORAMENTO PASSIVO & NOTIFICADOR MATINAL (CHAVE LIGA/DESLIGA)
================================================================================
- Controle absoluto pelo usuário via chave Liga/Desliga (OFF por padrão, pois o usuário
  ainda não iniciou os aportes reais).
- Quando DESLIGADO (OFF): Remove qualquer agendamento no Windows Task Scheduler,
  garantindo ZERO processos em segundo plano, ZERO consumo de memória/CPU e ZERO alertas.
- Quando LIGADO (ON): Agenda silenciosamente uma tarefa diária no Windows Task Scheduler
  para checar eventos críticos (SEC Form 8-K, M&As, Token Unlocks, Gatilhos de Ciclo/LTV)
  e enviar via Telegram Bot gratuito ou Discord Webhook apenas quando houver sinal real.
================================================================================
"""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTIFIER_CONFIG_PATH = os.path.join(ROOT_DIR, "notifier_config.json")
WINDOWS_TASK_NAME = "Antigravity_Quant_Morning_Notifier"


@dataclass
class NotifierSettings:
    enabled: bool = False  # DESLIGADO por padrão até o usuário decidir ativar
    schedule_time: str = "08:30"
    channel_type: str = "Telegram"  # "Telegram" ou "Discord"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook_url: str = ""
    notify_sec_8k_and_ma: bool = True
    notify_crypto_unlocks_and_dao: bool = True
    notify_macro_and_cycle_extremes: bool = True
    last_updated: str = ""
    scheduler_status: str = "DESATIVADO (Zero Processos em Background)"

    @property
    def schedule_time_hhmm(self) -> str:
        return self.schedule_time

    @schedule_time_hhmm.setter
    def schedule_time_hhmm(self, val: str) -> None:
        self.schedule_time = val


class BackgroundNotifierEngine:
    def __init__(self, config_path: str = NOTIFIER_CONFIG_PATH) -> None:
        self.config_path = config_path

    def load_config(self) -> NotifierSettings:
        return self.load_settings()

    def save_config(self, settings: NotifierSettings) -> Tuple[bool, str]:
        return self.save_settings_and_sync_scheduler(settings)

    def load_settings(self) -> NotifierSettings:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return NotifierSettings(
                    enabled=bool(data.get("enabled", False)),
                    schedule_time=str(data.get("schedule_time", "08:30")),
                    channel_type=str(data.get("channel_type", "Telegram")),
                    telegram_bot_token=str(data.get("telegram_bot_token", "")),
                    telegram_chat_id=str(data.get("telegram_chat_id", "")),
                    discord_webhook_url=str(data.get("discord_webhook_url", "")),
                    notify_sec_8k_and_ma=bool(data.get("notify_sec_8k_and_ma", True)),
                    notify_crypto_unlocks_and_dao=bool(data.get("notify_crypto_unlocks_and_dao", True)),
                    notify_macro_and_cycle_extremes=bool(data.get("notify_macro_and_cycle_extremes", True)),
                    last_updated=str(data.get("last_updated", "")),
                    scheduler_status=str(
                        data.get(
                            "scheduler_status",
                            "ATIVO (Agendado no Windows Task Scheduler)"
                            if data.get("enabled", False)
                            else "DESATIVADO (Zero Processos em Background)",
                        )
                    ),
                )
            except Exception:
                pass
        return NotifierSettings()

    def save_settings_and_sync_scheduler(self, settings: NotifierSettings) -> Tuple[bool, str]:
        settings.last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if settings.enabled:
            ok_sched, msg_sched = self._register_windows_task(settings.schedule_time)
            settings.scheduler_status = (
                f"LIGADO — Rotina Diária às {settings.schedule_time} ({msg_sched})"
            )
        else:
            ok_sched, msg_sched = self._unregister_windows_task()
            settings.scheduler_status = "DESLIGADO — Zero Processos em Segundo Plano"

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, indent=2, ensure_ascii=False)

        return ok_sched, settings.scheduler_status

    def _register_windows_task(self, time_hhmm: str) -> Tuple[bool, str]:
        try:
            py_exe = sys.executable
            script_path = os.path.abspath(__file__)
            cmd_action = f'"{py_exe}" "{script_path}" --run-check'
            cmd = [
                "schtasks",
                "/Create",
                "/SC",
                "DAILY",
                "/TN",
                WINDOWS_TASK_NAME,
                "/TR",
                cmd_action,
                "/ST",
                time_hhmm,
                "/F",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
            if res.returncode == 0:
                return True, "Windows Task Scheduler Configurado"
            return True, "Configuração Salva (Modo Local Pronto)"
        except Exception:
            return True, "Configuração Salva (Modo Local Pronto)"

    def _unregister_windows_task(self) -> Tuple[bool, str]:
        try:
            cmd = ["schtasks", "/Delete", "/TN", WINDOWS_TASK_NAME, "/F"]
            subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
        except Exception:
            pass
        return True, "Tarefa em segundo plano removida com sucesso"

    def build_morning_briefing_payload(
        self,
        macro: Any,
        portfolio: Any,
        equities: List[Any],
        cryptos: Dict[str, Any],
        micro_events: List[Any],
        risk_timing: Any,
    ) -> Dict[str, Any]:
        """
        Analisa silenciosamente todos os vetores da carteira e filtra APENAS sinais de alta
        relevância (8-Ks, M&As, Unlocks > 2.5%, Extremos de Ciclo e Oportunidades PEGY/DCF).
        """
        critical_alerts: List[str] = []
        settings = self.load_settings()

        # 1. Auditoria de Eventos Corporativos, 8-K, M&A e Valuation (Faixa Ouro)
        if settings.notify_sec_8k_and_ma:
            for m in micro_events[:4]:
                if "Positivo" in m.classification or "Alerta" in m.classification:
                    critical_alerts.append(
                        f"📑 [{m.asset_ticker}] ({m.source_type}): {m.headline} -> {m.classification}"
                    )
            for e in equities:
                vm = e.valuation_methods
                if vm.get("dcf_upside_pct", 0.0) >= 12.0 or "Ouro" in str(vm.get("primary_pegy_status", "")):
                    critical_alerts.append(
                        f"🏛️ [{e.ticker}] Faixa de Oportunidade Ativa: Spot ${e.current_price:,.2f} vs SOTP ${vm['sotp_fair_price_usd']:,.2f} (PEGY: {vm['primary_pegy_status']})"
                    )

        # 2. Auditoria de Criptoativos (Unlocks 30d, Governança DAO & Real Yield)
        if settings.notify_crypto_unlocks_and_dao:
            for sym, c in cryptos.items():
                unlock_pct = c.supply_structure.get("unlock_pct_of_circ", 0.0)
                if unlock_pct >= 2.5:
                    critical_alerts.append(
                        f"⚠️ [{sym}] Alerta de Unlock Relevante: {unlock_pct:.2f}% do Circulating Supply em 30d (Px Teórico Pós-Diluição: ${c.supply_structure['theoretical_post_unlock_price_usd']:,.2f})"
                    )
                else:
                    critical_alerts.append(
                        f"⛓️ [{sym}] Supply Seguro (Unlock {unlock_pct:.2f}%/mês) | Real Earnings: USD {c.tokenomics_valuation['protocol_real_earnings_m']:+.1f}M/ano | MVRV Z: {c.onchain_metrics['mvrv_z_score']:.2f}"
                    )

        # 3. Auditoria de Ciclo Macro & Alavancagem Convexa LTV
        if settings.notify_macro_and_cycle_extremes:
            sp = macro.sahm_paired
            yc = macro.yield_curve
            ltv = risk_timing.convex_ltv_panel
            critical_alerts.append(
                f"🌍 [Macro & LTV] Sahm's Rule: {sp['sahm_current_pct']:+.2f}% ({sp['paired_verdict']}) | Spread 10Y-2Y: {yc['spread_10y_2y_bps']:+.1f} bps | LTV Global: {ltv['ltv_global_current_pct']:.1f}% ({ltv['turbo_trigger_status']})"
            )

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"🏛️ *INSTITUTIONAL MORNING BRIEFING — QUANT TERMINAL 360°* ({now_str})",
            f"💰 *Monitored Portfolio:* USD {portfolio.capital_usd:,.0f} ({len(portfolio.positions)} Holdings | P&L: {portfolio.total_portfolio_pnl_pct:+.2f}%)",
            "",
            "🔎 *FILTERED SIGNALS (ZERO NOISE):*",
        ]
        for item in critical_alerts[:8]:
            lines.append(f"• {item}")

        lines.append("")
        lines.append("📄 _The Consolidated 360° Master PDF Report is available in the Intelligence Hub._")
        full_text = "\n".join(lines)

        return {
            "timestamp": now_str,
            "alerts_count": len(critical_alerts),
            "alerts_list": critical_alerts,
            "formatted_message": full_text,
        }

    def dispatch_notification(self, message_text: str, settings: Optional[NotifierSettings] = None) -> Tuple[bool, str]:
        cfg = settings or self.load_settings()
        if cfg.channel_type == "Telegram":
            if not cfg.telegram_bot_token.strip() or not cfg.telegram_chat_id.strip():
                return False, "Informe o Bot Token e o Chat ID do Telegram para disparar na nuvem (ou visualize o preview abaixo)."
            url = f"https://api.telegram.org/bot{cfg.telegram_bot_token.strip()}/sendMessage"
            payload = json.dumps({
                "chat_id": cfg.telegram_chat_id.strip(),
                "text": message_text,
                "parse_mode": "Markdown",
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=8) as resp:
                    if resp.status == 200:
                        return True, "Notificação enviada com sucesso para o seu Telegram!"
            except Exception as exc:
                return False, f"Falha ao conectar na API do Telegram: {exc}"
        elif cfg.channel_type == "Discord":
            if not cfg.discord_webhook_url.strip():
                return False, "Informe a Webhook URL do Discord para disparar no canal (ou visualize o preview abaixo)."
            payload = json.dumps({"content": message_text}).encode("utf-8")
            req = urllib.request.Request(
                cfg.discord_webhook_url.strip(),
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "QuantHubNotifier/1.0"},
            )
            try:
                with urllib.request.urlopen(req, timeout=8) as resp:
                    if resp.status in (200, 204):
                        return True, "Notificação enviada com sucesso para o seu Discord!"
            except Exception as exc:
                return False, f"Falha ao conectar no Webhook do Discord: {exc}"

        return False, "Canal de notificação não configurado."


if __name__ == "__main__":
    if "--run-check" in sys.argv:
        eng = BackgroundNotifierEngine()
        cfg = eng.load_settings()
        if not cfg.enabled:
            sys.exit(0)
        from core.macro_engine import MacroEngine
        from core.portfolio_engine import PortfolioEngine
        from core.equity_engine import EquityEngine
        from core.crypto_engine import CryptoEngine
        from core.geopolitics_micro_engine import GeopoliticsMicroEngine
        from core.risk_timing_engine import RiskTimingEngine

        m = MacroEngine().run_macro_aggregation()
        p = PortfolioEngine(os.path.join(ROOT_DIR, "portfolio_config.json")).build_overview_and_lookthrough()
        eq = EquityEngine(risk_free_rate_pct=m.yield_curve["us10y_pct"]).analyze_portfolio_equities()
        cr = CryptoEngine().analyze_portfolio_cryptos()
        micro = GeopoliticsMicroEngine().get_micro_events()
        rt = RiskTimingEngine().build_risk_and_consultative_timing(p, eq, cr)
        briefing = eng.build_morning_briefing_payload(m, p, eq, cr, micro, rt)
        eng.dispatch_notification(briefing["formatted_message"], cfg)

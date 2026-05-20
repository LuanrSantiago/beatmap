"""
scraper/scheduler.py — BeatMap
Versão 2.0 — Preparado para múltiplos scrapers

MUDANÇAS em relação à v1:
- Estrutura preparada para adicionar Ingresso Rápido e Ticket360 facilmente
- Cada scraper tem seu próprio job isolado (falha de um não afeta o outro)
- Log mais detalhado com separação visual por scraper
"""

import asyncio
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from scraper.ticket360 import scrape_ticket360
from scraper.sympla import scrape_sympla
from scraper.save_to_db import save_eventos

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)


def job_sympla():
    """Job do Sympla — roda todas as cidades configuradas em CIDADES."""
    log.info("=" * 50)
    log.info("Iniciando scraper Sympla (multi-cidades)...")
    try:
        dados = asyncio.run(scrape_sympla(headless=True))
        resultado = save_eventos(dados, fonte="Sympla")
        log.info(
            f"Sympla concluído — "
            f"criados: {resultado['criados']}, "
            f"duplicatas: {resultado['duplicatas']}, "
            f"erros: {resultado['erros']}"
        )
    except Exception as e:
        log.error(f"Falha no scraper Sympla: {e}")
    log.info("=" * 50)


def job_ticket360():
    log.info("Iniciando scraper Ticket360...")
    try:
        dados = asyncio.run(scrape_ticket360(headless=True))
        resultado = save_eventos(dados, fonte="Ticket360")
        log.info(f"Ticket360 concluído — {resultado}")
    except Exception as e:
        log.error(f"Falha no scraper Ticket360: {e}")


def iniciar_scheduler():
    scheduler = BlockingScheduler(timezone="America/Sao_Paulo")

    # Sympla: diário às 9h
    scheduler.add_job(
        job_sympla,
        trigger=CronTrigger(hour=9, minute=0),
        id="sympla_daily",
        name="Scraper Sympla diário",
        replace_existing=True
    )

    # Roda imediatamente ao iniciar (para não esperar até às 9h do dia seguinte)
    scheduler.add_job(
        job_sympla,
        trigger="date",
        id="sympla_startup",
        name="Scraper Sympla inicialização"
    )

    scheduler.add_job(
    job_ticket360,
    trigger=CronTrigger(hour=9, minute=15),
    id="ticket360_daily",
    name="Scraper Ticket360 diário",
    replace_existing=True
    )

    log.info("Scheduler iniciado. Jobs registrados:")
    for job in scheduler.get_jobs():
        log.info(f"  • {job.name}")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("Scheduler encerrado pelo usuário.")


if __name__ == "__main__":
    iniciar_scheduler()
"""
scraper/jobs.py — BeatMap
Funções de job dos scrapers (Sympla e Ticket360), extraídas de
scheduler.py na consolidação que removeu o BlockingScheduler (não usado
mais desde que os scrapers migraram para GitHub Actions, na Fase 5.2).
Usadas por run_once.py, que dispara os dois scrapers uma única vez.
"""

import asyncio
import logging
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
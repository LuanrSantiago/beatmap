import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from scraper.sympla import scrape_sympla
from scraper.save_to_db import save_eventos

# configura logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

def job_sympla():
    log.info("Iniciando scraper Sympla...")
    try:
        dados = asyncio.run(scrape_sympla(headless=True))
        resultado = save_eventos(dados)
        log.info(
            f"Sympla concluído — "
            f"criados: {resultado['criados']}, "
            f"duplicatas: {resultado['duplicatas']}, "
            f"erros: {resultado['erros']}"
        )
    except Exception as e:
        log.error(f"Falha no scraper Sympla: {e}")

def iniciar_scheduler():
    scheduler = BlockingScheduler(timezone="America/Sao_Paulo")

    scheduler.add_job(
        job_sympla,
        trigger=CronTrigger(hour=9, minute=0),
        id="sympla_daily",
        name="Scraper Sympla diário",
        replace_existing=True,
    )

    # roda uma vez imediatamente ao iniciar
    scheduler.add_job(
        job_sympla,
        trigger="date",  # executa uma vez agora
        id="sympla_startup",
        name="Scraper Sympla inicialização",
    )

    log.info("Scheduler iniciado e aguardando execuções agendadas.")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("Scheduler encerrado.")

if __name__ == "__main__":
    # se quiser rodar uma vez agora para testar, descomente:
    #job_sympla()
    iniciar_scheduler()
"""
scraper/run_once.py — BeatMap
Executa os scrapers uma única vez (usado pelo GitHub Actions).
"""
import logging
from scraper.jobs import job_sympla, job_ticket360

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

if __name__ == "__main__":
    log.info("Execução única disparada pelo GitHub Actions")
    job_sympla()
    job_ticket360()
    log.info("Execução única finalizada")
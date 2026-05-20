"""
scraper/ticket360.py — BeatMap
Versão 1.0 — Scraper do Ticket360

Diferenças em relação ao Sympla:
- URL única: filtra por categoria "eletrônico", sem separação por cidade
- Raspa eventos de todo o Brasil e filtra por estado no final
- Estrutura HTML diferente: seletores específicos do Ticket360
- Data separada em 3 elementos (mês, dia, hora) em vez de texto único
"""

import asyncio
import re
from playwright.async_api import async_playwright
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────

URL_BASE = "https://www.ticket360.com.br/sub-categoria/2/eletronico"

# Estados que o BeatMap cobre (Sudeste + Sul)
# Eventos de outros estados são descartados após o scraping
ESTADOS_COBERTOS = {"SP", "RJ", "MG", "PR", "SC", "RS"}

MESES = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4,
    "mai": 5, "jun": 6, "jul": 7, "ago": 8,
    "set": 9, "out": 10, "nov": 11, "dez": 12
}


# ─────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ─────────────────────────────────────────────

def _montar_datetime(dia: int, mes: int, hora: int, minuto: int) -> datetime:
    """
    Monta datetime com lógica de ano:
    se a data já passou esse ano, assume o próximo.
    (mesma lógica do sympla.py — reutilizável)
    """
    hoje = datetime.now()
    data = datetime(hoje.year, mes, dia, hora, minuto)
    if data < hoje:
        data = datetime(hoje.year + 1, mes, dia, hora, minuto)
    return data


def parse_data_ticket360(mes_raw: str, dia_raw: str, hora_raw: str) -> datetime | None:
    """
    Monta datetime a partir dos 3 elementos separados do Ticket360.

    No Sympla a data vinha num texto único: "Sábado, 20 de Jun às 22:00"
    No Ticket360 vem em 3 elementos distintos:
      - .data-mes  → "MAI"
      - .data-layer → "23"
      - .card-info span → "Abertura: 20:00"

    Essa separação na verdade facilita o parse — sem regex complexo.
    """
    try:
        mes = MESES.get(mes_raw.strip().lower()[:3])
        if not mes:
            return None

        dia = int(re.search(r"\d+", dia_raw).group())

        # Hora pode vir como "Abertura: 20:00" ou só "20:00"
        hora_match = re.search(r"(\d{1,2}):(\d{2})", hora_raw)
        if hora_match:
            h, m = int(hora_match.group(1)), int(hora_match.group(2))
        else:
            h, m = 0, 0  # Sem hora definida → meia-noite

        return _montar_datetime(dia, mes, h, m)

    except Exception:
        return None


def parse_local_ticket360(endereco_raw: str) -> tuple[str, str]:
    """
    Extrai cidade e estado do texto de endereço do Ticket360.
    Exemplo: "Leopoldina / MG" → ("Leopoldina", "MG")
    Exemplo: "São Paulo / SP"  → ("São Paulo", "SP")

    O formato é consistente: sempre "Cidade / UF"
    """
    try:
        if "/" in endereco_raw:
            partes = endereco_raw.split("/")
            cidade = partes[0].strip()
            estado = partes[1].strip().upper()
            if len(estado) == 2:
                return cidade, estado
        return endereco_raw.strip(), ""
    except Exception:
        return endereco_raw.strip(), ""


# ─────────────────────────────────────────────
# PROCESSAMENTO DE CARDS
# ─────────────────────────────────────────────

async def _processar_card(card) -> dict | None:
    """
    Extrai dados de um card de evento do Ticket360.

    Estrutura HTML que identificamos no DevTools:
    <a class="event-click" href="/evento/32787/ingressos-para-dubdogz">
      ...
      <div class="data-mes">MAI</div>
      <div class="data-layer">23</div>
      <span>Abertura: 20:00</span>
      <span class="card-endereco">Leopoldina / MG</span>
      <strong>Stone House</strong>       ← venue
      <span class="card-name-evento">Dubdogz</span>
    </a>
    """
    try:
        # ── Nome do evento ────────────────────────────────────────
        nome_el = await card.query_selector(".card-name-evento")
        nome = (await nome_el.inner_text()).strip() if nome_el else None
        if not nome:
            return None

        # ── Data ─────────────────────────────────────────────────
        mes_el  = await card.query_selector(".data-mes")
        dia_el  = await card.query_selector(".data-layer")
        hora_el = await card.query_selector(".card-info span")

        mes_raw  = (await mes_el.inner_text()).strip()  if mes_el  else ""
        dia_raw  = (await dia_el.inner_text()).strip()  if dia_el  else ""
        hora_raw = (await hora_el.inner_text()).strip() if hora_el else ""

        data_dt = parse_data_ticket360(mes_raw, dia_raw, hora_raw)

        if not data_dt:
            print(f"  ⚠ data não parseável (ignorado): {nome} | {mes_raw} {dia_raw} {hora_raw!r}")
            return None

        if data_dt < datetime.now():
            return None  # Evento passado

        # ── Local ─────────────────────────────────────────────────
        endereco_el = await card.query_selector(".card-endereco")
        endereco_raw = (await endereco_el.inner_text()).strip() if endereco_el else ""
        cidade, estado = parse_local_ticket360(endereco_raw)

        # ── Venue ─────────────────────────────────────────────────
        venue_el = await card.query_selector(".card-name-local strong")
        venue = (await venue_el.inner_text()).strip() if venue_el else cidade

        # ── URL do evento ─────────────────────────────────────────
        href = await card.get_attribute("href")
        url_evento = f"https://www.ticket360.com.br{href}" if href else None

        # ── Filtra estados fora da cobertura ──────────────────────
        # O Ticket360 não tem filtro por estado na URL,
        # então filtramos aqui após extrair os dados
        if estado and estado not in ESTADOS_COBERTOS:
            return None  # Evento fora da região coberta — descarta silenciosamente

        if not estado:
            print(f"  ⚠ estado não identificado (ignorado): {nome} | {endereco_raw!r}")
            return None

        return {
            "nome":   nome,
            "venue":  venue,
            "cidade": cidade,
            "estado": estado,
            "data":   data_dt,
            "url":    url_evento,
            "fonte":  "Ticket360",
        }

    except Exception as e:
        print(f"  ✗ Erro ao processar card: {e}")
        return None


# ─────────────────────────────────────────────
# PAGINAÇÃO
# ─────────────────────────────────────────────

async def _ir_para_proxima_pagina(page) -> bool:
    """
    Tenta clicar no botão de próxima página do Ticket360.

    O Ticket360 pode ter paginação diferente do Sympla.
    Se não achar botão, assume que é página única (sem paginação).
    """
    try:
        proximo = await page.query_selector(
            "nav button:has-text('Próximo'), "
            "nav a:has-text('Próximo'), "
            "[class*='pagination'] a:has-text('Próximo'), "
            "a[rel='next'], "
            "[aria-label='Next page']"
        )

        if not proximo:
            return False

        desabilitado = await proximo.get_attribute("disabled")
        if desabilitado is not None:
            return False

        await proximo.click()
        await page.wait_for_timeout(3000)
        return True

    except Exception:
        return False


# ─────────────────────────────────────────────
# SCRAPER PRINCIPAL
# ─────────────────────────────────────────────

async def scrape_ticket360(headless: bool = False) -> list[dict]:
    """
    Raspa todos os eventos eletrônicos do Ticket360.

    Diferente do Sympla (que separava por cidade), aqui:
    1. Abrimos UMA URL com todos os eventos eletrônicos do Brasil
    2. Passamos por todas as páginas
    3. Filtramos por estado dentro de _processar_card()
    """
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        print(f"🎵 BeatMap Scraper — Ticket360 v1.0")
        print(f"🔗 URL: {URL_BASE}")
        print(f"📍 Filtrando por estados: {', '.join(sorted(ESTADOS_COBERTOS))}")

        await page.goto(URL_BASE, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        # Verifica se carregou eventos
        try:
            await page.wait_for_selector("a.event-click", timeout=10000)
        except:
            print("⚠  Nenhum evento encontrado na página inicial.")
            await browser.close()
            return []

        pagina = 1

        while True:
            print(f"\n  📄 Página {pagina}...")
            cards = await page.query_selector_all("a.event-click")
            print(f"  → {len(cards)} cards encontrados")

            for card in cards:
                evento = await _processar_card(card)
                if evento:
                    resultados.append(evento)
                    print(f"    ✓ {evento['nome']} ({evento['cidade']}/{evento['estado']})")

            tem_proxima = await _ir_para_proxima_pagina(page)
            if not tem_proxima:
                print(f"\n  → Última página ({pagina} página(s) total)")
                break

            pagina += 1
            await page.wait_for_timeout(1500)

        await browser.close()

    # Remove duplicatas
    vistos = set()
    unicos = []
    for ev in resultados:
        chave = (ev["nome"], str(ev["data"]))
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(ev)

    descartados = len(resultados) - len(unicos)
    print(f"\n{'='*60}")
    print(f"✅ Eventos na região coberta: {len(resultados)}")
    print(f"🔁 Duplicatas removidas:      {descartados}")
    print(f"📦 Eventos únicos:            {len(unicos)}")
    print(f"{'='*60}")

    return unicos


# ─────────────────────────────────────────────
# EXECUÇÃO DIRETA
# ─────────────────────────────────────────────

if __name__ == "__main__":
    dados = asyncio.run(scrape_ticket360(headless=False))

    print("\nSalvando no banco...")
    from scraper.save_to_db import save_eventos
    resultado = save_eventos(dados, fonte="Ticket360")
    print(f"\nResultado final: {resultado}")
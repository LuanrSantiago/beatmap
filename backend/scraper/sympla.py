"""
scraper/sympla.py — BeatMap
Versão 2.1 — Multi-cidades + Paginação por botões (corrigido)

MUDANÇAS v2.1 (correções):
- CORRIGIDO: paginação agora clica no botão "Próximo >" em vez de fazer scroll
  O Sympla usa botões numerados (1,2,3...7), não scroll infinito
- CORRIGIDO: eventos sem data são ignorados antes de chegar no banco
  Antes: tentava salvar com event_date=None → erro NOT NULL do PostgreSQL
  Agora: filtra logo após o parse, com aviso no terminal
"""

import asyncio
import re
from playwright.async_api import async_playwright
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────

BUSCA = "música+eletrônica"

CIDADES = [
    # ── São Paulo ──
    {"cidade": "São Paulo",   "estado": "SP", "slug": "sao-paulo-sp"},
    {"cidade": "Campinas",    "estado": "SP", "slug": "campinas-sp"},

    # ── Rio de Janeiro ──
    {"cidade": "Rio de Janeiro", "estado": "RJ", "slug": "rio-de-janeiro-rj"},

    # ── Minas Gerais ──
    {"cidade": "Belo Horizonte", "estado": "MG", "slug": "belo-horizonte-mg"},
    {"cidade": "Nova Lima",      "estado": "MG", "slug": "nova-lima-mg"},

    # ── Paraná ──
    {"cidade": "Curitiba", "estado": "PR", "slug": "curitiba-pr"},

    # ── Santa Catarina ──
    {"cidade": "Florianópolis", "estado": "SC", "slug": "florianopolis-sc"},
    {"cidade": "Camboriú",      "estado": "SC", "slug": "camboriu-sc"},

    # ── Rio Grande do Sul ──
    {"cidade": "Porto Alegre", "estado": "RS", "slug": "porto-alegre-rs"},
]

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
    Monta um datetime com lógica de ano:
    se a data já passou esse ano, assume que é no próximo.

    Separada em função própria para não repetir o mesmo código
    nos dois formatos do parse_data.
    """
    hoje = datetime.now()
    data = datetime(hoje.year, mes, dia, hora, minuto)
    if data < hoje:
        data = datetime(hoje.year + 1, mes, dia, hora, minuto)
    return data

def parse_data(data_raw: str) -> datetime | None:
    """
    Reconhece dois formatos do Sympla:

    Formato 1 — evento de um dia com horário:
      "Sábado, 20 de Jun às 22:00"  →  datetime(2026, 6, 20, 22, 0)

    Formato 2 — evento multi-dia (sem horário fixo):
      "21 de Mai a 23 de Mai"  →  datetime(2026, 5, 21, 0, 0)
      Usamos o PRIMEIRO dia como data de início, horário 00:00
    """
    try:
        # ── Formato 1: com horário ────────────────────────────────
        match = re.search(
            r"(\d{1,2})\s+de\s+(\w{3,}).*?às\s+(\d{2}:\d{2})",
            data_raw, re.IGNORECASE
        )
        if match:
            dia, mes_str, hora = match.groups()
            mes = MESES.get(mes_str.lower()[:3])
            if mes:
                h, m = map(int, hora.split(":"))
                return _montar_datetime(int(dia), mes, h, m)

        # ── Formato 2: multi-dia sem horário ──────────────────────
        # Pega só o primeiro "DD de MMM" antes do " a "
        match = re.search(
            r"(\d{1,2})\s+de\s+(\w{3,})",
            data_raw, re.IGNORECASE
        )
        if match:
            dia, mes_str = match.groups()
            mes = MESES.get(mes_str.lower()[:3])
            if mes:
                return _montar_datetime(int(dia), mes, 0, 0)

        return None

    except Exception:
        return None

def parse_local(local_raw: str, cidade_padrao: str, estado_padrao: str) -> tuple[str, str, str]:
    """
    Extrai venue, cidade e estado do texto de local do Sympla.
    Exemplo: "Club Vibe - Curitiba, PR" → ("Club Vibe", "Curitiba", "PR")
    """
    try:
        partes = local_raw.split(" - ")
        venue = partes[0].strip()

        if len(partes) > 1:
            cidade_estado = partes[1].strip()
            if "," in cidade_estado:
                cidade, estado = cidade_estado.rsplit(",", 1)
                estado = estado.strip()
                if len(estado) == 2:
                    return venue, cidade.strip(), estado.upper()

        return venue, cidade_padrao, estado_padrao

    except Exception:
        return local_raw, cidade_padrao, estado_padrao


# ─────────────────────────────────────────────
# PAGINAÇÃO — BOTÕES NUMERADOS (corrigido)
# ─────────────────────────────────────────────

async def _extrair_cards_pagina_atual(page) -> list:
    """
    Extrai todos os cards da página atual do Sympla.

    Função separada para poder chamar tanto na página 1
    quanto em cada página seguinte após clicar em "Próximo".
    """
    await page.wait_for_selector("[class*='sympla-card']", timeout=8000)
    return await page.query_selector_all("[class*='sympla-card']")


async def _ir_para_proxima_pagina(page) -> bool:
    """
    Clica no botão "Próximo" da paginação do Sympla.

    CORRIGIDO v2.2: seletor restrito à área de paginação.
    Antes: buscava "Próximo" em qualquer lugar da página
           → pegava endereços como "próximo ao Largo do Paissandú"
    Agora: busca dentro de <nav> ou elementos com 'pagination' no nome da classe
           → só acha o botão real de paginação
    """
    try:
        # Estratégia 1: botão dentro de nav ou container de paginação
        # aria-label="Next page" é o padrão de acessibilidade mais comum
        proximo = await page.query_selector(
            "nav button:has-text('Próximo'), "
            "nav a:has-text('Próximo'), "
            "[class*='pagination'] button:has-text('Próximo'), "
            "[class*='pagination'] a:has-text('Próximo'), "
            "[aria-label='Next page'], "
            "[aria-label='Próxima página']"
        )

        # Estratégia 2 (fallback): pega TODOS os botões com "Próximo"
        # e verifica qual deles é realmente de paginação (não está dentro de um card)
        if not proximo:
            candidatos = await page.query_selector_all("button:has-text('Próximo')")
            for candidato in candidatos:
                # Verifica se o botão pai NÃO é um card de evento
                dentro_de_card = await candidato.evaluate(
                    "el => !!el.closest('[class*=\"sympla-card\"]')"
                )
                if not dentro_de_card:
                    proximo = candidato
                    break

        if not proximo:
            return False

        desabilitado = await proximo.get_attribute("disabled")
        if desabilitado is not None:
            return False

        await proximo.click()
        await page.wait_for_timeout(3000)
        return True

    except Exception as e:
        print(f"  [paginação] Erro ao clicar em Próximo: {e}")
        return False

# ─────────────────────────────────────────────
# PROCESSAMENTO DE CARDS
# ─────────────────────────────────────────────

async def _processar_card(card, cidade: str, estado: str) -> dict | None:
    """
    Extrai os dados de um card de evento.

    Retorna um dicionário com os dados, ou None se o card for inválido.

    CORRIGIDO v2.1: retorna None se a data não for parseável.
    Antes deixava data=None passar → banco reclamava de NOT NULL.
    Agora filtramos aqui mesmo, antes de chegar no save_to_db.
    """
    try:
        nome_el = await card.query_selector("h3")
        nome = (await nome_el.inner_text()).strip() if nome_el else None
        if not nome:
            return None

        local_el = await card.query_selector("p.pn67h1h")
        local_raw = (await local_el.inner_text()).strip() if local_el else ""

        data_el = await card.query_selector("[class*='qtfy415']")
        data_raw = (await data_el.inner_text()).strip() if data_el else None

        url_evento = await card.get_attribute("href")
        if not url_evento:
            link_el = await card.query_selector("a")
            url_evento = await link_el.get_attribute("href") if link_el else None

        # ── CORRIGIDO: filtra sem data aqui ──────────────────────
        if not data_raw:
            print(f"  ⚠ sem data (ignorado): {nome}")
            return None

        data_dt = parse_data(data_raw)

        if not data_dt:
            print(f"  ⚠ data não parseável (ignorado): {nome} | data_raw={data_raw!r}")
            return None
        # ─────────────────────────────────────────────────────────

        # Descarta eventos que já passaram
        if data_dt < datetime.now():
            return None

        venue, cidade_ev, estado_ev = parse_local(local_raw, cidade, estado)

        return {
            "nome":     nome,
            "venue":    venue,
            "cidade":   cidade_ev,
            "estado":   estado_ev,
            "data":     data_dt,
            "data_raw": data_raw,
            "url":      url_evento,
            "fonte":    "Sympla",
        }

    except Exception as e:
        print(f"  ✗ Erro ao processar card: {e}")
        return None


# ─────────────────────────────────────────────
# SCRAPER POR CIDADE
# ─────────────────────────────────────────────

async def scrape_cidade(page, cidade_info: dict) -> list[dict]:
    """
    Raspa TODAS as páginas de eventos de uma cidade.

    Fluxo:
    1. Abre a URL da cidade
    2. Extrai os cards da página 1
    3. Clica em "Próximo" → extrai página 2
    4. Repete até não ter mais "Próximo"
    """
    cidade = cidade_info["cidade"]
    estado = cidade_info["estado"]
    slug   = cidade_info["slug"]
    url    = f"https://www.sympla.com.br/eventos/{slug}?s={BUSCA}"

    print(f"\n{'='*60}")
    print(f"🏙  Cidade: {cidade}/{estado}")
    print(f"🔗 URL: {url}")

    resultados = []

    try:
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        # Aceita banner de cookies (aparece só 1x por sessão)
        try:
            await page.click("button:has-text('Aceitar')", timeout=3000)
            await page.wait_for_timeout(1000)
        except:
            pass

        # Verifica se há eventos nessa cidade
        try:
            await page.wait_for_selector("[class*='sympla-card']", timeout=10000)
        except:
            print(f"  ⚠  Nenhum evento em {cidade}/{estado}")
            return []

        pagina = 1

        # Loop de paginação — continua enquanto houver "Próximo"
        while True:
            print(f"\n  📄 Página {pagina}...")
            cards = await _extrair_cards_pagina_atual(page)
            print(f"  → {len(cards)} cards encontrados")

            for card in cards:
                evento = await _processar_card(card, cidade, estado)
                if evento:
                    resultados.append(evento)
                    print(f"    ✓ {evento['nome']}")

            # Tenta ir para a próxima página
            tem_proxima = await _ir_para_proxima_pagina(page)
            if not tem_proxima:
                print(f"  → Última página atingida ({pagina} página(s) no total)")
                break

            pagina += 1

            # Pausa entre páginas para não sobrecarregar o servidor
            await page.wait_for_timeout(1500)

    except Exception as e:
        print(f"  ✗ Falha em {cidade}/{estado}: {e}")

    print(f"\n→ {len(resultados)} eventos válidos em {cidade}/{estado}")
    return resultados


# ─────────────────────────────────────────────
# SCRAPER PRINCIPAL
# ─────────────────────────────────────────────

async def scrape_sympla(headless: bool = False) -> list[dict]:
    """
    Abre o browser UMA VEZ e raspa todas as cidades + todas as páginas.
    """
    todos_eventos = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        print(f"🎵 BeatMap Scraper — Sympla v2.1")
        print(f"📍 Cidades: {len(CIDADES)}")

        for cidade_info in CIDADES:
            eventos_cidade = await scrape_cidade(page, cidade_info)
            todos_eventos.extend(eventos_cidade)
            await page.wait_for_timeout(2000)  # Pausa gentil entre cidades

        await browser.close()

    # Remove duplicatas globais pelo par (nome, data)
    vistos = set()
    unicos = []
    for ev in todos_eventos:
        chave = (ev["nome"], str(ev["data"]))
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(ev)

    duplicatas = len(todos_eventos) - len(unicos)
    print(f"\n{'='*60}")
    print(f"✅ Total extraído:       {len(todos_eventos)}")
    print(f"🔁 Duplicatas removidas: {duplicatas}")
    print(f"📦 Eventos únicos:       {len(unicos)}")
    print(f"{'='*60}")

    return unicos


# ─────────────────────────────────────────────
# EXECUÇÃO DIRETA
# ─────────────────────────────────────────────

if __name__ == "__main__":
    dados = asyncio.run(scrape_sympla(headless=False))

    print("\nSalvando no banco...")
    from scraper.save_to_db import save_eventos
    resultado = save_eventos(dados)
    print(f"\nResultado final: {resultado}")
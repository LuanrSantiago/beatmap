import asyncio
import re
from playwright.async_api import async_playwright
from datetime import datetime

BASE_URL = "https://www.sympla.com.br/eventos/sao-paulo-sp?s=música+eletrônica"

MESES = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4,
    "mai": 5, "jun": 6, "jul": 7, "ago": 8,
    "set": 9, "out": 10, "nov": 11, "dez": 12
}

def parse_data(data_raw: str) -> datetime | None:
    try:
        match = re.search(
            r"(\d{1,2})\s+de\s+(\w{3}).*?(\d{2}:\d{2})",
            data_raw, re.IGNORECASE
        )
        if not match:
            return None
        dia, mes_str, hora = match.groups()
        mes = MESES.get(mes_str.lower()[:3])
        if not mes:
            return None
        ano = datetime.now().year
        h, m = map(int, hora.split(":"))
        dt = datetime(ano, mes, int(dia), h, m)
        return dt  # retorna sem ajuste de ano
    except Exception:
        return None

ESTADOS_BR = {
    "são paulo": "SP", "rio de janeiro": "RJ", "minas gerais": "MG",
    "bahia": "BA", "paraná": "PR", "santa catarina": "SC",
    "rio grande do sul": "RS", "pernambuco": "PE", "ceará": "CE",
    "goiás": "GO", "amazonas": "AM", "pará": "PA",
}

def parse_local(local_raw: str) -> tuple[str, str, str]:
    try:
        partes = local_raw.split(" - ")
        venue = partes[0].strip()
        if len(partes) > 1:
            cidade_estado = partes[1].strip()
            if "," in cidade_estado:
                cidade, estado = cidade_estado.rsplit(",", 1)
                estado = estado.strip()
                # se estado é nome completo, converte para sigla
                if len(estado) > 2:
                    estado = ESTADOS_BR.get(estado.lower(), "SP")
                return venue, cidade.strip(), estado
        return venue, local_raw, "SP"
    except Exception:
        return local_raw, "", "SP"

async def scrape_sympla(headless: bool = False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        print("Abrindo Sympla...")
        await page.goto(BASE_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        # Fecha banner de cookies
        try:
            await page.click("button:has-text('Aceitar')", timeout=5000)
            print("Cookie aceito")
            await page.wait_for_timeout(1000)
        except:
            print("Sem banner de cookie")

        await page.wait_for_selector("[class*='sympla-card']", timeout=15000)
        cards = await page.query_selector_all("[class*='sympla-card']")
        print(f"Encontrados: {len(cards)} cards\n")

        resultados = []

        for card in cards:
            try:
                # Nome
                nome_el = await card.query_selector("h3")
                nome = (await nome_el.inner_text()).strip() if nome_el else None

                # Local
                local_el = await card.query_selector("p.pn67h1h")
                local_raw = (await local_el.inner_text()).strip() if local_el else None

                # Data
                data_el = await card.query_selector("[class*='qtfy415']")
                data_raw = (await data_el.inner_text()).strip() if data_el else None

                # URL
                url = await card.get_attribute("href")
                if not url:
                    link_el = await card.query_selector("a")
                    url = await link_el.get_attribute("href") if link_el else None

                if not nome or not local_raw:
                    continue

                venue, cidade, estado = parse_local(local_raw)
                data_dt = parse_data(data_raw) if data_raw else None
                if data_dt and data_dt < datetime.now():
                    continue

                evento = {
                    "nome":    nome,
                    "venue":   venue,
                    "cidade":  cidade,
                    "estado":  estado,
                    "data":    data_dt,
                    "data_raw": data_raw,
                    "url":     url,
                    "fonte":   "Sympla",
                }
                resultados.append(evento)

                print(f"✓ {nome}")
                print(f"  Local: {venue} — {cidade}/{estado}")
                print(f"  Data:  {data_raw} → {data_dt}")
                print(f"  URL:   {url[:60] if url else 'N/A'}...")
                print()

            except Exception as e:
                print(f"✗ Erro em card: {e}")
                continue

        await browser.close()

        print(f"\nTotal extraído: {len(resultados)} eventos")
        return resultados

if __name__ == "__main__":
    dados = asyncio.run(scrape_sympla())

    print("\nSalvando no banco...")
    from scraper.save_to_db import save_eventos
    resultado = save_eventos(dados)
    print(f"\nResultado: {resultado}")
"""
scraper/cleanup_genre.py — BeatMap
Script de execução única (não faz parte do fluxo agendado do GitHub Actions).

Aplica o filtro de gênero eletrônico (scraper/genre_filter.py) retroativamente
nos eventos JÁ SALVOS no banco — o filtro em sympla.py só passou a agir a
partir de hoje, então eventos antigos (de antes do filtro existir) podem
estar "errados" (fora do escopo de música eletrônica) e nunca foram checados.

Roda contra as duas fontes (Sympla e Ticket360), por segurança — mesmo o
Ticket360 já filtrando por categoria no site de origem.

Fluxo:
1. Busca todos os eventos futuros no banco e EXTRAI os dados pra memória
   (fecha a conexão logo em seguida — não fica presa durante o Playwright)
2. Classifica cada um pelo título (Camada 1)
3. Título ambíguo → visita a página do evento e checa a descrição (Camada 2)
4. Mostra a lista completa do que seria apagado
5. Pede confirmação (s/n) e apaga usando uma conexão isolada (sem pool
   compartilhado com o resto do app — evita "server closed the connection
   unexpectedly" em conexões que ficaram ociosas por muito tempo)

Uso:
    python -m scraper.cleanup_genre
"""

import asyncio
import os
from datetime import datetime, timezone
from playwright.async_api import async_playwright
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.database import SessionLocal
from app.models.event import Event, Venue
import app.models.scraper  # registra o model ScraperSource no SQLAlchemy
from scraper.genre_filter import classificar_titulo, contem_exclusao


async def _checar_descricao(browser, url_evento: str | None) -> bool:
    """
    Mesma lógica da Camada 2 usada em sympla.py — abre a página do evento
    e checa a tag <meta property="og:description">.

    Retorna True se deve ser rejeitado. Em qualquer erro (timeout, tag
    ausente, evento fora do ar), retorna False — erra para o lado de
    MANTER o evento, nunca apaga por falha técnica.
    """
    if not url_evento:
        return False

    pagina = None
    try:
        pagina = await browser.new_page()
        await pagina.goto(url_evento, wait_until="domcontentloaded", timeout=15000)
        meta = await pagina.query_selector("meta[property='og:description']")
        descricao = await meta.get_attribute("content") if meta else ""
        return contem_exclusao(descricao or "")
    except Exception as e:
        print(f"    ⚠ erro ao checar descrição (mantendo evento): {e}")
        return False
    finally:
        if pagina:
            await pagina.close()


def buscar_eventos_futuros() -> list[dict]:
    """
    Busca os eventos futuros e já extrai tudo pra dicionários simples
    (id, nome, cidade, ticket_url, fonte) ANTES de fechar a sessão.

    Importante: a sessão fica aberta só durante essa função, rápida —
    não durante o loop lento do Playwright que vem depois. Isso evita
    manter uma conexão ociosa por minutos, que é o que causou o erro
    "server closed the connection unexpectedly".
    """
    db = SessionLocal()
    try:
        fontes = db.execute(text("SELECT id, name FROM scraper_sources")).fetchall()
        nome_por_source_id = {str(f[0]): f[1] for f in fontes}

        eventos_orm = (
            db.query(Event)
            .join(Venue, Event.venue_id == Venue.id)
            .filter(Event.event_date >= datetime.now(timezone.utc))
            .all()
        )

        # Extrai tudo pra dict simples ENQUANTO a sessão ainda está viva —
        # depois que a função retorna e a sessão fecha, os objetos ORM
        # (evento.venue etc.) não poderiam mais ser acessados sem erro.
        eventos = [
            {
                "id": e.id,
                "nome": e.name,
                "cidade": e.venue.city if e.venue else "?",
                "ticket_url": e.ticket_url,
                "fonte": nome_por_source_id.get(str(e.source_id), "desconhecida"),
            }
            for e in eventos_orm
        ]

        return eventos
    finally:
        db.close()


async def encontrar_eventos_reprovados(eventos: list[dict]) -> list[dict]:
    """
    Recebe a lista já extraída (sem sessão de banco aberta) e classifica
    cada evento. Só abre o navegador aqui — a parte lenta acontece toda
    sem nenhuma conexão de banco pendurada.
    """
    reprovados = []

    print(f"🔍 {len(eventos)} eventos futuros no banco. Classificando...\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for evento in eventos:
            classificacao = classificar_titulo(evento["nome"])

            if classificacao == "rejeitado":
                reprovados.append({**evento, "motivo": "título"})
                print(f"  ✗ [{evento['fonte']}] {evento['nome']} — rejeitado (título)")

            elif classificacao == "ambiguo":
                rejeitado = await _checar_descricao(browser, evento["ticket_url"])
                if rejeitado:
                    reprovados.append({**evento, "motivo": "descrição"})
                    print(f"  ✗ [{evento['fonte']}] {evento['nome']} — rejeitado (descrição)")
                else:
                    print(f"  ✓ [{evento['fonte']}] {evento['nome']} — mantido (ambíguo, descrição ok)")

            else:
                print(f"  ✓ [{evento['fonte']}] {evento['nome']} — mantido (aceito)")

        await browser.close()

    return reprovados


def apagar_eventos(ids: list) -> int:
    """
    Apaga os eventos pelos IDs informados.

    Usa um engine PRÓPRIO, isolado do engine compartilhado em
    app/database.py, com NullPool — cada conexão é aberta na hora e
    descartada depois, sem cache. Isso garante que, mesmo depois de um
    processo longo (o loop do Playwright), o DELETE final sempre usa uma
    conexão fresca, nunca uma que possa ter sido derrubada por timeout de
    inatividade do Supabase.
    """
    database_url = os.getenv("DATABASE_URL")
    engine_isolado = create_engine(database_url, poolclass=NullPool)
    SessionIsolada = sessionmaker(bind=engine_isolado)

    db = SessionIsolada()
    try:
        apagados = (
            db.query(Event)
            .filter(Event.id.in_(ids))
            .delete(synchronize_session=False)
        )
        db.commit()
        return apagados
    finally:
        db.close()
        engine_isolado.dispose()


async def main():
    eventos = buscar_eventos_futuros()
    reprovados = await encontrar_eventos_reprovados(eventos)

    print(f"\n{'='*60}")
    print(f"Resultado da classificação")
    print(f"{'='*60}")

    if not reprovados:
        print("✅ Nenhum evento reprovado. Banco já está alinhado com o filtro atual.")
        return

    print(f"\n{len(reprovados)} evento(s) seriam apagados:\n")
    for r in reprovados:
        print(f"  - [{r['fonte']}] {r['nome']} ({r['cidade']}) — motivo: {r['motivo']}")

    resposta = input(f"\nConfirma a exclusão desses {len(reprovados)} evento(s)? (s/n): ").strip().lower()

    if resposta != "s":
        print("Cancelado. Nenhum evento foi apagado.")
        return

    ids = [r["id"] for r in reprovados]
    apagados = apagar_eventos(ids)
    print(f"\n✅ {apagados} evento(s) apagado(s) do banco.")


if __name__ == "__main__":
    asyncio.run(main())
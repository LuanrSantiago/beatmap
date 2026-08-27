"""
scraper/genre_filter.py — BeatMap
Filtro por gênero musical (eletrônica), usado pelo scraper do Sympla.

O Sympla não tem categoria de "música eletrônica" — a busca usada no scraper
(BUSCA em sympla.py) é textual e pode achar a palavra em qualquer lugar da
página do evento, não só no título. Isso traz falsos positivos: eventos
mistos, onde a eletrônica é só uma atração entre várias (ex: um evento com
sertanejo, pagode, e um DJ de eletrônica no fim da noite).

Duas camadas de checagem:

- classificar_titulo(): Camada 1, decide só pelo título do card (rápido,
  sem requisição extra). Resultado: "aceito", "rejeitado" ou "ambiguo".
- contem_exclusao(): Camada 2, usada só quando o título é "ambiguo" — checa
  a descrição completa da página do evento com uma regra mais rígida.

Por que a regra é diferente entre título e descrição:
No título, um evento como "Funk & Tech House" é uma fusão deliberada — faz
sentido aceitar. Na descrição (texto mais longo, geralmente com o line-up
completo), qualquer menção a outro gênero geralmente indica um evento
misto/genérico (tipo "balada com vários estilos"), não um evento eletrônico
de verdade — por isso a Camada 2 rejeita mesmo se também mencionar eletrônica.
"""

EXCLUSAO_KEYWORDS = [
    "sertanejo", "pagode", "forró", "axé", "gospel", "samba",
    "mpb", "rock", "arrocha", "piseiro", "funk",
]

ELETRONICA_KEYWORDS = [
    "eletrônica", "eletronica", "eletronic", "techno", "house", "tech house",
    "trance", "psytrance", "edm", "rave", "dnb", "drum and bass", "dub",
    "minimal", "progressive", "deep house", "afro house", "melodic techno",
    "big room",
]


def _contem_alguma(texto: str, palavras: list[str]) -> bool:
    texto_lower = texto.lower()
    return any(palavra in texto_lower for palavra in palavras)


def classificar_titulo(titulo: str) -> str:
    """
    Classifica o título de um evento em três categorias:

    - "aceito": tem palavra eletrônica → aceita direto, sem checar mais nada
    - "rejeitado": tem palavra de exclusão e NENHUMA palavra eletrônica junto
    - "ambiguo": não bate em nenhuma das duas listas → precisa da Camada 2

    A presença de uma palavra eletrônica sempre "salva" o título, mesmo que
    também tenha uma palavra de exclusão — é isso que faz "Funk & Tech House"
    ser aceito, em vez de rejeitado só por causa da palavra "funk".
    """
    tem_eletronica = _contem_alguma(titulo, ELETRONICA_KEYWORDS)
    tem_exclusao = _contem_alguma(titulo, EXCLUSAO_KEYWORDS)

    if tem_eletronica:
        return "aceito"
    if tem_exclusao:
        return "rejeitado"
    return "ambiguo"


def contem_exclusao(texto: str) -> bool:
    """
    Usado na Camada 2 (checagem da descrição completa de eventos ambíguos).

    Regra mais rígida que a do título: qualquer palavra de exclusão presente
    já rejeita o evento, mesmo que a descrição também mencione uma palavra
    eletrônica. Exemplo real: "BALADA FEST" tem "(Música Eletrônica)" E
    "(Pagode)"/"(Sertanejo)" na descrição — é rejeitado, porque a eletrônica
    é só uma entre várias atrações, não o foco do evento.
    """
    return _contem_alguma(texto, EXCLUSAO_KEYWORDS)
"""
tests/test_genre_filter.py — BeatMap
Testa a lógica de classificação de gênero (Camada 1 e Camada 2), sem
depender de rede — só testa as funções puras de scraper/genre_filter.py.
"""

from scraper.genre_filter import classificar_titulo, contem_exclusao


# ─── Camada 1: classificar_titulo() ─────────────────────────────

def test_titulo_com_palavra_eletronica_e_aceito():
    assert classificar_titulo("TECHNO NIGHT") == "aceito"
    assert classificar_titulo("Festival de House Music") == "aceito"
    assert classificar_titulo("Rave na Serra") == "aceito"


def test_titulo_com_exclusao_e_sem_eletronica_e_rejeitado():
    assert classificar_titulo("Noite do Sertanejo") == "rejeitado"
    assert classificar_titulo("Pagode da Firma") == "rejeitado"
    assert classificar_titulo("Baile Funk do Bairro") == "rejeitado"


def test_titulo_sem_nenhuma_palavra_e_ambiguo():
    assert classificar_titulo("BALADA FEST") == "ambiguo"
    assert classificar_titulo("Festa da Firma") == "ambiguo"


def test_titulo_misto_com_eletronica_e_aceito_mesmo_com_exclusao():
    # Regra do "funk": se tiver uma palavra eletrônica junto, aceita
    assert classificar_titulo("Funk & Tech House") == "aceito"
    assert classificar_titulo("Sertanejo e Eletrônica Open Bar") == "aceito"


def test_classificacao_e_case_insensitive():
    assert classificar_titulo("techno NIGHT") == "aceito"
    assert classificar_titulo("SERTANEJO UNIVERSITÁRIO") == "rejeitado"


# ─── Camada 2: contem_exclusao() ────────────────────────────────

def test_descricao_com_exclusao_retorna_true_mesmo_com_eletronica():
    # Caso real: BALADA FEST — tem pagode/sertanejo E eletrônica na descrição
    descricao = (
        "Música ao vivo: (Pagode) Os Parças (Sertanejo) Lu Gang "
        "(Música Eletrônica) DJ Thiago Cézar"
    )
    assert contem_exclusao(descricao) is True


def test_descricao_so_com_eletronica_retorna_false():
    descricao = "Uma noite de techno e house com os melhores DJs da cena"
    assert contem_exclusao(descricao) is False


def test_descricao_vazia_retorna_false():
    assert contem_exclusao("") is False
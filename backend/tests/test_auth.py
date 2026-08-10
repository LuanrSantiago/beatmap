"""
Testes de app/auth.py — usam um par de chaves ES256 gerado localmente,
simulando o formato do Supabase, sem depender de rede (o endpoint JWKS
real do Supabase é mockado via monkeypatch).
"""
import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app import auth as auth_module


@pytest.fixture(scope="module")
def chave_teste():
    chave_privada = ec.generate_private_key(ec.SECP256R1())
    chave_publica = chave_privada.public_key()
    return chave_privada, chave_publica


@pytest.fixture(autouse=True)
def mock_jwks(monkeypatch, chave_teste):
    """Troca a busca real de chaves no Supabase pela chave pública de teste."""
    _, chave_publica = chave_teste

    class ChaveFake:
        key = chave_publica

    def fake_get_signing_key_from_jwt(self, token):
        return ChaveFake()

    monkeypatch.setattr(
        type(auth_module.jwks_client),
        "get_signing_key_from_jwt",
        fake_get_signing_key_from_jwt,
    )


def _gerar_token(chave_privada, exp_delta_segundos=3600, aud="authenticated", sub=None):
    payload = {
        "sub": sub or str(uuid.uuid4()),
        "aud": aud,
        "exp": int(time.time()) + exp_delta_segundos,
    }
    return jwt.encode(payload, chave_privada, algorithm="ES256")


def test_token_ausente_retorna_422(client_auth_real):
    # Authorization é um Header(...) obrigatório — sem ele o FastAPI barra
    # a requisição ANTES de chamar get_current_user_id (422, não 401).
    resp = client_auth_real.get("/status/")
    assert resp.status_code == 422


def test_token_malformado_retorna_401(client_auth_real):
    # String que não é um JWT de verdade (sem estrutura header.payload.assinatura) —
    # antes da correção, isso gerava PyJWKClientError não tratado (500).
    resp = client_auth_real.get(
        "/status/", headers={"Authorization": "Bearer isso-nao-e-um-jwt"}
    )
    assert resp.status_code == 401


def test_token_valido_retorna_200(client_auth_real, chave_teste):
    chave_privada, _ = chave_teste
    token = _gerar_token(chave_privada)
    resp = client_auth_real.get("/status/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_token_expirado_retorna_401(client_auth_real, chave_teste):
    chave_privada, _ = chave_teste
    token = _gerar_token(chave_privada, exp_delta_segundos=-10)
    resp = client_auth_real.get("/status/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token expirado"


def test_token_audience_errada_retorna_401(client_auth_real, chave_teste):
    chave_privada, _ = chave_teste
    token = _gerar_token(chave_privada, aud="outra-audiencia")
    resp = client_auth_real.get("/status/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
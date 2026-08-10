"""Testes das rotas de status (POST/GET/DELETE /status/), com auth mockada."""
import uuid


def test_criar_status(client, event_futuro):
    resp = client.post("/status/", json={"event_id": str(event_futuro.id), "status": "going"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "going"
    assert body["event_id"] == str(event_futuro.id)


def test_atualizar_status_existente_faz_upsert(client, event_futuro):
    client.post("/status/", json={"event_id": str(event_futuro.id), "status": "thinking"})
    resp = client.post("/status/", json={"event_id": str(event_futuro.id), "status": "bought"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "bought"

    # upsert = continua sendo 1 registro só, não cria um segundo
    listagem = client.get("/status/")
    assert len(listagem.json()) == 1


def test_criar_status_evento_inexistente_retorna_404(client):
    resp = client.post("/status/", json={"event_id": str(uuid.uuid4()), "status": "going"})
    assert resp.status_code == 404


def test_listar_status_do_usuario(client, event_futuro):
    client.post("/status/", json={"event_id": str(event_futuro.id), "status": "going"})
    resp = client.get("/status/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["status"] == "going"


def test_deletar_status(client, event_futuro):
    client.post("/status/", json={"event_id": str(event_futuro.id), "status": "going"})
    resp = client.delete(f"/status/{event_futuro.id}")
    assert resp.status_code == 204

    listagem = client.get("/status/")
    assert listagem.json() == []


def test_deletar_status_inexistente_retorna_404(client, event_futuro):
    resp = client.delete(f"/status/{event_futuro.id}")
    assert resp.status_code == 404
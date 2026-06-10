import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.core.config import settings
from tests.utils.specimen_type import create_random_specimen_type

PREFIX = f"{settings.API_V1_STR}/specimen-types"

def test_create(client, superuser_token_headers):
    r = client.post(PREFIX + "/", headers=superuser_token_headers, json={"name": "Sang veineux", "description": "Prélèvement veineux standard", "color": "#ff0000"})
    assert r.status_code == 200
    c = r.json()
    assert c["name"] == "Sang veineux"
    assert c["description"] == "Prélèvement veineux standard"
    assert c["color"] == "#ff0000"

def test_read_list(client, superuser_token_headers, db):
    create_random_specimen_type(db)
    create_random_specimen_type(db)
    r = client.get(PREFIX + "/", headers=superuser_token_headers)
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 2


def test_search_specimen_types(client, superuser_token_headers):
    r = client.post(
        PREFIX + "/",
        headers=superuser_token_headers,
        json={
            "name": "Tube recherche",
            "description": "Recherche citrate",
            "color": "#0000ff",
        },
    )
    assert r.status_code == 200
    created_id = r.json()["id"]

    search_response = client.get(
        PREFIX + "/?search=citrate&limit=20",
        headers=superuser_token_headers,
    )
    assert search_response.status_code == 200
    ids = [item["id"] for item in search_response.json()["data"]]
    assert created_id in ids


def test_read_one(client, superuser_token_headers, db):
    obj = create_random_specimen_type(db)
    r = client.get(f"{PREFIX}/{obj.id}", headers=superuser_token_headers)
    assert r.status_code == 200
    assert r.json()["name"] == obj.name

def test_read_not_found(client, superuser_token_headers):
    r = client.get(f"{PREFIX}/{uuid.uuid4()}", headers=superuser_token_headers)
    assert r.status_code == 404

def test_update(client, superuser_token_headers, db):
    obj = create_random_specimen_type(db)
    r = client.put(f"{PREFIX}/{obj.id}", headers=superuser_token_headers, json={"name": "Urine", "color": "#ffff00"})
    assert r.status_code == 200
    assert r.json()["name"] == "Urine"
    assert r.json()["color"] == "#ffff00"

def test_update_not_found(client, superuser_token_headers):
    r = client.put(f"{PREFIX}/{uuid.uuid4()}", headers=superuser_token_headers, json={"name": "X"})
    assert r.status_code == 404

def test_delete(client, superuser_token_headers, db):
    obj = create_random_specimen_type(db)
    r = client.delete(f"{PREFIX}/{obj.id}", headers=superuser_token_headers)
    assert r.status_code == 200
    r2 = client.get(PREFIX + "/", headers=superuser_token_headers)
    assert str(obj.id) not in [x["id"] for x in r2.json()["data"]]
    r3 = client.get(PREFIX + "/?include_deleted=true", headers=superuser_token_headers)
    assert str(obj.id) in [x["id"] for x in r3.json()["data"]]

def test_restore(client, superuser_token_headers, db):
    obj = create_random_specimen_type(db)
    client.delete(f"{PREFIX}/{obj.id}", headers=superuser_token_headers)
    r = client.post(f"{PREFIX}/{obj.id}/restore", headers=superuser_token_headers)
    assert r.status_code == 200
    assert r.json()["is_deleted"] is False

def test_delete_not_found(client, superuser_token_headers):
    r = client.delete(f"{PREFIX}/{uuid.uuid4()}", headers=superuser_token_headers)
    assert r.status_code == 404

def test_forbidden(client, normal_user_token_headers):
    r = client.post(PREFIX + "/", headers=normal_user_token_headers, json={"name": "X"})
    assert r.status_code == 403

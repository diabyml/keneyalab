import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.core.config import settings
from tests.utils.patient_context import create_random_patient_context

PREFIX = f"{settings.API_V1_STR}/patient-contexts"

def test_create(client, superuser_token_headers):
    r = client.post(PREFIX + "/", headers=superuser_token_headers, json={"name": "À jeun"})
    assert r.status_code == 200
    c = r.json()
    assert c["name"] == "À jeun"
    assert "id" in c

def test_read_list(client, superuser_token_headers, db):
    create_random_patient_context(db)
    create_random_patient_context(db)
    r = client.get(PREFIX + "/", headers=superuser_token_headers)
    assert r.status_code == 200
    c = r.json()
    assert len(c["data"]) >= 2
    assert "count" in c

def test_search_patient_contexts(client, superuser_token_headers):
    r = client.post(PREFIX + "/", headers=superuser_token_headers, json={"name": "Grossesse"})
    assert r.status_code == 200
    created_id = r.json()["id"]
    search = client.get(PREFIX + "/?search=gross", headers=superuser_token_headers)
    assert search.status_code == 200
    assert created_id in [item["id"] for item in search.json()["data"]]

def test_read_one(client, superuser_token_headers, db):
    obj = create_random_patient_context(db)
    r = client.get(f"{PREFIX}/{obj.id}", headers=superuser_token_headers)
    assert r.status_code == 200
    assert r.json()["name"] == obj.name

def test_read_not_found(client, superuser_token_headers):
    r = client.get(f"{PREFIX}/{uuid.uuid4()}", headers=superuser_token_headers)
    assert r.status_code == 404

def test_update(client, superuser_token_headers, db):
    obj = create_random_patient_context(db)
    r = client.put(f"{PREFIX}/{obj.id}", headers=superuser_token_headers, json={"name": "Post-prandial"})
    assert r.status_code == 200
    assert r.json()["name"] == "Post-prandial"

def test_update_not_found(client, superuser_token_headers):
    r = client.put(f"{PREFIX}/{uuid.uuid4()}", headers=superuser_token_headers, json={"name": "X"})
    assert r.status_code == 404

def test_delete(client, superuser_token_headers, db):
    obj = create_random_patient_context(db)
    r = client.delete(f"{PREFIX}/{obj.id}", headers=superuser_token_headers)
    assert r.status_code == 200
    # Verify excluded from default list
    r2 = client.get(PREFIX + "/", headers=superuser_token_headers)
    assert str(obj.id) not in [x["id"] for x in r2.json()["data"]]
    # Verify included when include_deleted=true
    r3 = client.get(PREFIX + "/?include_deleted=true", headers=superuser_token_headers)
    assert str(obj.id) in [x["id"] for x in r3.json()["data"]]

def test_restore(client, superuser_token_headers, db):
    obj = create_random_patient_context(db)
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

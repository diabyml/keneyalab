import uuid

from app.core.audit import audit_record_id, serialize_value


def test_serialize_value_redacts_nested_secrets() -> None:
    value = serialize_value(
        {
            "email": "audit@example.com",
            "password": "secret",
            "nested": {
                "access_token": "token",
                "record_id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            },
        }
    )

    assert value == {
        "email": "audit@example.com",
        "password": "[MASQUÉ]",
        "nested": {
            "access_token": "[MASQUÉ]",
            "record_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        },
    }


def test_audit_record_id_normalizes_integer_primary_keys() -> None:
    assert audit_record_id(1) == uuid.UUID(int=1)
    assert audit_record_id(uuid.UUID(int=2)) == uuid.UUID(int=2)
    assert audit_record_id(None) is None

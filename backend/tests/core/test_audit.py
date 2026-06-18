import uuid

from app.core.audit import serialize_value


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

import uuid
from types import SimpleNamespace

from app.models import GlobalSearchResultPublic
from app.services import global_search


def _result(kind: str, resource: str) -> GlobalSearchResultPublic:
    record_id = uuid.uuid4()
    return GlobalSearchResultPublic(
        kind=kind,
        title=f"{kind} title",
        subtitle=None,
        badge=None,
        href=f"/{resource}/{record_id}",
        resource=resource,
        record_id=record_id,
    )


def test_global_search_returns_empty_for_short_query() -> None:
    result = global_search.search(
        session=SimpleNamespace(),
        user=SimpleNamespace(),
        query="a",
        limit=5,
    )

    assert result.data == []


def test_global_search_omits_groups_without_permission(monkeypatch) -> None:
    monkeypatch.setattr(
        global_search,
        "_can",
        lambda *, resource, action, **_: resource == "patients" and action == "view",
    )
    monkeypatch.setattr(
        global_search,
        "_patients",
        lambda **_: [_result("patients", "patients")],
    )
    monkeypatch.setattr(
        global_search,
        "_order_results",
        lambda **_: [_result("orders", "orders")],
    )

    result = global_search.search(
        session=SimpleNamespace(),
        user=SimpleNamespace(),
        query="diallo",
        limit=5,
    )

    assert [item.kind for item in result.data] == ["patients"]


def test_global_search_includes_superuser_allowed_groups(monkeypatch) -> None:
    monkeypatch.setattr(global_search, "_can", lambda **_: True)
    monkeypatch.setattr(
        global_search,
        "_order_results",
        lambda *, kind, resource, **_: [_result(kind, resource)],
    )
    monkeypatch.setattr(
        global_search,
        "_patients",
        lambda **_: [_result("patients", "patients")],
    )
    monkeypatch.setattr(
        global_search,
        "_doctors",
        lambda **_: [_result("doctors", "doctors")],
    )
    monkeypatch.setattr(
        global_search,
        "_invoices",
        lambda **_: [_result("invoices", "invoices")],
    )
    monkeypatch.setattr(
        global_search,
        "_catalog",
        lambda **_: [_result("catalog", "catalog")],
    )
    monkeypatch.setattr(
        global_search,
        "_reagents",
        lambda **_: [_result("reagents", "reagents")],
    )

    result = global_search.search(
        session=SimpleNamespace(),
        user=SimpleNamespace(),
        query="kl",
        limit=5,
    )

    assert [item.kind for item in result.data] == [
        "orders",
        "patients",
        "doctors",
        "invoices",
        "catalog",
        "specimens",
        "results",
        "reagents",
    ]

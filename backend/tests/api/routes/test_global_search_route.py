from collections.abc import Generator
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import deps
from app.main import app
from app.models import GlobalSearchResultsPublic
from app.services import global_search as global_search_service


def test_global_search_requires_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/global-search/", params={"query": "kl"})

    assert response.status_code == 401


def test_global_search_returns_empty_for_short_query(monkeypatch) -> None:
    def override_db() -> Generator[SimpleNamespace, None, None]:
        yield SimpleNamespace()

    def override_user() -> SimpleNamespace:
        return SimpleNamespace(is_superuser=True)

    monkeypatch.setattr(
        global_search_service,
        "search",
        lambda **_: GlobalSearchResultsPublic(data=[]),
    )
    app.dependency_overrides[deps.get_db] = override_db
    app.dependency_overrides[deps.get_current_user] = override_user

    try:
        client = TestClient(app)
        response = client.get("/api/v1/global-search/", params={"query": "k"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"data": []}

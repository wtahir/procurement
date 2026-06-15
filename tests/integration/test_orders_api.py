from fastapi.testclient import TestClient

from apps.api.main import app


def test_dashboard_is_served() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Procura" in response.text


def test_pipeline_creates_order_with_recommendation() -> None:
    client = TestClient(app)

    response = client.post(
        "/orders",
        json={
            "raw_input": "Need 500 tons of rebar steel in Sydney.",
            "material_code": "rebar_steel",
            "quantity": 500,
            "region": "sydney",
        },
    )

    assert response.status_code == 200
    order = response.json()
    assert len(order["bidding"]["quotes_received"]) == 6
    assert order["bidding"]["recommended_bid"]["supplier_id"]
    assert order["pipeline_control"]["status"] == "awaiting_human"
    assert order["approval"]["required_level"] == "director"


def test_small_order_auto_approves() -> None:
    client = TestClient(app)

    order = client.post(
        "/orders",
        json={
            "raw_input": "10 cement bags",
            "material_code": "cement_bag",
            "quantity": 10,
            "region": "sydney",
        },
    ).json()

    assert order["approval"]["status"] == "approved"
    assert order["pipeline_control"]["status"] == "completed"


def test_approval_transitions_order() -> None:
    client = TestClient(app)

    order = client.post(
        "/orders",
        json={
            "raw_input": "Need 800 tons of rebar steel in Melbourne.",
            "material_code": "rebar_steel",
            "quantity": 800,
            "region": "melbourne",
        },
    ).json()
    order_id = order["identity"]["order_id"]

    approved = client.post(f"/approvals/{order_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["pipeline_control"]["status"] == "completed"


def test_missing_order_returns_404() -> None:
    client = TestClient(app)
    assert client.get("/orders/does-not-exist").status_code == 404

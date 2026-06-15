from fastapi.testclient import TestClient

from apps.suppliers.main import app


def test_rest_supplier_returns_quote() -> None:
    client = TestClient(app)

    response = client.post(
        "/rest/alrajhi/rfq",
        json={
            "order_id": "ord-1",
            "material_code": "rebar_steel",
            "quantity": 500,
            "unit": "ton",
            "region": "riyadh",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["supplier_id"] == "al_rajhi_steel"
    assert data["total"] > 0

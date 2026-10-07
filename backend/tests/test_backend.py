import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.database import init_db, get_db_connection
from app.services.meta_service import meta_service
from app.services.lead_service import lead_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads")
    conn.commit()
    conn.close()
    yield

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "meta-lead-ads-backend"

def test_webhook_verification_success():
    challenge = "987654321"
    response = client.get(
        f"/webhook?hub.mode=subscribe&hub.challenge={challenge}&hub.verify_token=meta_lead_poc_token_2026"
    )
    assert response.status_code == 200
    assert response.text == challenge

def test_webhook_verification_failure():
    response = client.get(
        "/webhook?hub.mode=subscribe&hub.challenge=123&hub.verify_token=wrong_token"
    )
    assert response.status_code == 403

def test_lead_normalization():
    raw_meta_lead = {
        "id": "meta_lead_999",
        "created_time": "2026-10-07T10:00:00+0000",
        "form_id": "form_123",
        "field_data": [
            {"name": "full_name", "values": ["Alice Wonderland"]},
            {"name": "email", "values": ["alice@wonderland.example"]},
            {"name": "phone_number", "values": ["+1234567890"]}
        ]
    }
    normalized = meta_service.normalize_lead_data(raw_meta_lead)
    assert normalized["meta_lead_id"] == "meta_lead_999"
    assert normalized["name"] == "Alice Wonderland"
    assert normalized["email"] == "alice@wonderland.example"
    assert normalized["phone"] == "+1234567890"

def test_duplicate_lead_handling():
    lead_data = {
        "meta_lead_id": "unique_lead_001",
        "name": "Bob Smith",
        "email": "bob@example.com",
        "phone": "+1987654321"
    }
    # First save
    lead1, is_new1 = lead_service.save_lead(lead_data)
    assert is_new1 is True
    assert lead1["meta_lead_id"] == "unique_lead_001"

    # Second save with same meta_lead_id
    lead2, is_new2 = lead_service.save_lead(lead_data)
    assert is_new2 is False
    assert lead2["id"] == lead1["id"]

    # Verify database has only 1 lead
    all_leads = lead_service.get_all_leads()
    assert len(all_leads) == 1

def test_leads_get_endpoint():
    # Insert a test lead
    lead_service.save_lead({
        "meta_lead_id": "lead_test_get",
        "name": "Charlie Brown",
        "email": "charlie@example.com",
        "phone": "+1122334455"
    })
    response = client.get("/leads")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["leads"][0]["name"] == "Charlie Brown"

def test_mock_lead_creation():
    response = client.post("/leads/mock", json={
        "name": "David Miller",
        "email": "david@example.com",
        "phone": "+1444555666"
    })
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["is_new"] is True
    assert res_data["lead"]["name"] == "David Miller"

@pytest.mark.asyncio
async def test_webhook_post_processing():
    fake_meta_lead = {
        "id": "leadgen_evt_100",
        "created_time": "2026-10-07T10:15:00+0000",
        "form_id": "form_888",
        "field_data": [
            {"name": "full_name", "values": ["Eva Green"]},
            {"name": "email", "values": ["eva@green.example"]},
            {"name": "phone_number", "values": ["+1777888999"]}
        ]
    }
    
    with patch.object(meta_service, "get_lead_details", new=AsyncMock(return_value=fake_meta_lead)):
        payload = {
            "object": "page",
            "entry": [
                {
                    "id": "page_123",
                    "time": 1712000000,
                    "changes": [
                        {
                            "field": "leadgen",
                            "value": {
                                "created_time": 1712000000,
                                "leadgen_id": "leadgen_evt_100",
                                "page_id": "page_123",
                                "form_id": "form_888"
                            }
                        }
                    ]
                }
            ]
        }
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"status": "EVENT_RECEIVED"}

        # Verify lead was retrieved and stored
        leads = lead_service.get_all_leads()
        assert len(leads) == 1
        assert leads[0]["name"] == "Eva Green"
        assert leads[0]["meta_lead_id"] == "leadgen_evt_100"

def test_websocket_connection_and_broadcast():
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert data == "pong"

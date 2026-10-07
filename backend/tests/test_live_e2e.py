import asyncio
import json
import httpx
import websockets
import sys

async def test_live_websocket_and_webhook():
    print("[1] Testing Backend Health...")
    async with httpx.AsyncClient() as client:
        res = await client.get("http://127.0.0.1:8000/health")
        assert res.status_code == 200
        print(f"    Health check passed: {res.json()}")

    print("[2] Connecting to Backend WebSocket ws://127.0.0.1:8000/ws...")
    uri = "ws://127.0.0.1:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("    WebSocket connected successfully! (Simulating open React Native client)")

        # Send a ping to verify bidirectional socket
        await websocket.send("ping")
        pong = await websocket.recv()
        assert pong == "pong"
        print(f"    WebSocket ping-pong successful: received '{pong}'")

        print("[3] Simulating Meta Leadgen Webhook POST event from Meta Lead Testing Tool...")
        fake_leadgen_id = "meta_test_lead_88291039"
        webhook_payload = {
            "object": "page",
            "entry": [
                {
                    "id": "1002348572910",
                    "time": 1712000000,
                    "changes": [
                        {
                            "field": "leadgen",
                            "value": {
                                "created_time": 1712000000,
                                "leadgen_id": fake_leadgen_id,
                                "page_id": "1002348572910",
                                "form_id": "form_99382910"
                            }
                        }
                    ]
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            webhook_res = await client.post("http://127.0.0.1:8000/webhook", json=webhook_payload)
            print(f"    Webhook HTTP POST status: {webhook_res.status_code}, response: {webhook_res.json()}")
            assert webhook_res.status_code == 200

        print("[4] Waiting for real-time WebSocket broadcast to arrive on client...")
        # Receive the broadcast message on WebSocket
        raw_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        msg = json.loads(raw_msg)
        print(f"    RECEIVED REAL-TIME BROADCAST ON WEBSOCKET: {json.dumps(msg, indent=2)}")

        assert msg["type"] == "new_lead"
        assert msg["lead"]["meta_lead_id"] == fake_leadgen_id
        print("    VERIFICATION SUCCEEDED: Lead broadcasted and received over WebSocket in real time!")

        print("[5] Verifying persistence via GET /leads...")
        async with httpx.AsyncClient() as client:
            leads_res = await client.get("http://127.0.0.1:8000/leads")
            data = leads_res.json()
            print(f"    GET /leads total count: {data['total']}")
            assert data["total"] >= 1
            lead_found = any(l["meta_lead_id"] == fake_leadgen_id for l in data["leads"])
            assert lead_found
            print("    VERIFICATION SUCCEEDED: Lead is persisted in database and queryable!")

if __name__ == "__main__":
    asyncio.run(test_live_websocket_and_webhook())

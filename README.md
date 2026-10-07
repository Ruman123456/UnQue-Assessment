# Meta Lead Ads + React Native PoC

A real-time integration Proof of Concept demonstrating instantaneous, zero-touch lead delivery from Meta Lead Ads into an open React Native application screen using WebSockets and FastAPI.

---

## Objective

When a user submits a test lead form using Meta's **Lead Ads Testing Tool**, the submitted lead automatically appears in the already-open React Native application screen without requiring any manual action, pull-to-refresh, or interaction on the mobile device.

---

## Architecture

```
                          META
                            │
                            ▼
                 Meta Lead Testing Tool
                            │
                            │ leadgen webhook (HTTPS POST)
                            ▼
                     FastAPI Backend
                            │
                            │ leadgen_id
                            ▼
                     Meta Graph API
                            │
                            │ lead details (field_data)
                            ▼
                     Lead Processing
                            │
                     ┌──────┴──────┐
                     ▼             ▼
                  SQLite       WebSocket (/ws)
               (leads.db)          │
                                   ▼
                          React Native App
                                   │
                                   ▼
                         Leads List (Real-Time)
```

1. **Meta Lead Testing Tool** submits a test lead form.
2. Meta triggers a `leadgen` event to the backend's `/webhook` endpoint over HTTPS.
3. **FastAPI** acknowledges receipt with `200 OK` and queries Meta Graph API (`/{leadgen_id}`) for the actual field values (Name, Email, Phone).
4. The backend normalizes the data and saves it to **SQLite**, ignoring duplicates.
5. The backend immediately broadcasts the new lead over a persistent **WebSocket** connection.
6. The **React Native** application updates its state and renders the new lead at the top of the list instantly.

---

## Tech Stack

- **Backend:** Python 3.12, FastAPI, Uvicorn, HTTPX, Pydantic v2
- **Mobile / Frontend:** React Native 0.76, TypeScript, Expo 52 (supports iOS, Android, and Web)
- **Real-Time Layer:** Native WebSockets (`/ws`) with auto-reconnect client
- **Database:** SQLite 3 (`leads.db`)
- **Meta Integration:** Meta Graph API v21.0, Meta Webhooks (Lead Ads / leadgen)
- **Tunnels / Public URL:** Cloudflare Tunnels (`cloudflared`) or ngrok

---

## Repository Structure

```
meta-lead-react-native-poc/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application & WebSocket router
│   │   ├── config.py               # Pydantic Settings & environment loader
│   │   ├── database.py             # SQLite connection & table initialization
│   │   ├── models.py               # Database schemas
│   │   ├── schemas.py              # Pydantic request/response models
│   │   ├── routes/
│   │   │   ├── leads.py            # GET /leads, POST /leads/mock, DELETE /leads/clear
│   │   │   └── webhook.py          # GET /webhook (verify), POST /webhook (ingest)
│   │   └── services/
│   │       ├── meta_service.py     # Graph API client & field normalizer
│   │       ├── lead_service.py     # SQLite persistence & broadcast trigger
│   │       └── websocket_manager.py# Active WebSocket connection manager
│   ├── tests/
│   │   ├── test_backend.py         # Unit tests (health, webhook, deduplication, etc.)
│   │   └── test_live_e2e.py        # End-to-end live socket test script
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
│
├── mobile/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConnectionBadge.tsx # Visual real-time connection status
│   │   │   └── LeadCard.tsx        # Polished card with new lead indicator
│   │   ├── screens/
│   │   │   └── LeadsScreen.tsx     # Primary screen with zero-touch auto-update
│   │   ├── services/
│   │   │   └── api.ts              # REST client & auto-reconnecting WebSocket
│   │   └── types/
│   │       └── lead.ts             # TypeScript interfaces
│   ├── App.tsx
│   ├── index.ts
│   ├── app.json
│   ├── tsconfig.json
│   └── package.json
│
├── docs/
│   ├── architecture.md             # Complete architecture & design choices
│   └── demo-script.md              # Loom #1 and Loom #2 video walkthrough scripts
├── README.md
└── .gitignore
```

---

## Prerequisites

- **Python:** 3.10+ (Tested on Python 3.12.2)
- **Node.js:** 18+ (Tested on Node 24.11.1)
- **Meta Developer Account & Facebook Page**
- **HTTPS Tunnel:** `cloudflared` or `ngrok`

---

## Backend Setup

1. Open a terminal in `backend/`:
   ```bash
   cd backend
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Linux/macOS:
   # source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure environment variables in `backend/.env`:
   ```ini
   META_APP_ID=your_meta_app_id
   META_APP_SECRET=your_meta_app_secret
   META_PAGE_ID=your_facebook_page_id
   META_PAGE_ACCESS_TOKEN=your_page_access_token
   META_WEBHOOK_VERIFY_TOKEN=meta_lead_poc_token_2026
   META_API_VERSION=v21.0
   DATABASE_PATH=leads.db
   HOST=0.0.0.0
   PORT=8000
   ```

3. Run backend tests:
   ```bash
   .\.venv\Scripts\pytest -v
   ```

4. Start the backend:
   ```bash
   .\.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## React Native Setup

1. Open another terminal in `mobile/`:
   ```bash
   cd mobile
   npm install
   ```

2. Start the application:
   ```bash
   # Start Web version (accessible at http://localhost:8081):
   npm run web

   # Or run on physical phone via Expo Go:
   npm start
   ```

---

## Public Webhook Setup (HTTPS Tunnel)

Meta Webhooks require an HTTPS callback URL.

Using **Cloudflare Tunnel**:
```bash
cloudflared tunnel --url http://localhost:8000
```
*Take note of the assigned public URL (e.g. `https://random-subdomain.trycloudflare.com`).*

Or using **ngrok**:
```bash
ngrok http 8000
```

---

## Meta Configuration & Webhook Subscription

1. Go to **Meta for Developers** -> **My Apps** -> Select/Create App.
2. Under **Products**, add **Webhooks**:
   - Choose object: **Page**.
   - Callback URL: `https://<YOUR-PUBLIC-URL>/webhook`
   - Verify Token: `meta_lead_poc_token_2026` (must match `META_WEBHOOK_VERIFY_TOKEN` in `.env`).
   - Click **Verify and Save**.
3. Under Page Webhook fields, locate **leadgen** and click **Subscribe**.
4. Subscribe your Facebook Page to the App:
   - Make a Graph API call:
     ```bash
     curl -X POST "https://graph.facebook.com/v21.0/{PAGE_ID}/subscribed_apps?subscribed_fields=leadgen&access_token={PAGE_ACCESS_TOKEN}"
     ```
   - Successful response: `{"success": true}`.

---

## End-to-End Test (Using Meta Lead Testing Tool)

1. Open [Meta Lead Ads Testing Tool](https://developers.facebook.com/tools/lead-ads-testing/).
2. Select your **Page** and **Instant Form**.
3. (If a previous test lead exists, click **Delete lead** first).
4. Click **Preview form**.
5. Fill out the test lead form (e.g., Name: `Alex Rivera`, Email: `alex@example.com`, Phone: `+1 555-0123`).
6. Click **Submit**.
7. **Observe the React Native application screen**:
   - Without touching or refreshing the screen, the new lead appears at the top within seconds.
   - Total lead count increments automatically.
   - Connection status remains `Connected (Live)`.

---

## Local Verification Without Live Meta Account

If testing offline or before configuring Meta credentials:
1. Run the included live end-to-end verification script:
   ```bash
   cd backend
   .\.venv\Scripts\python tests\test_live_e2e.py
   ```
2. Or trigger a mock lead directly via REST API:
   ```bash
   curl -X POST http://127.0.0.1:8000/leads/mock -H "Content-Type: application/json" -d "{\"name\": \"John Doe\", \"email\": \"john@example.com\", \"phone\": \"+1 555-0199\"}"
   ```
   The lead will immediately broadcast over WebSocket to the open React Native screen.

---

## Assumptions & Limitations

- **Single Page Context:** Designed for Proof of Concept with one Facebook Page at a time.
- **SQLite Persistence:** Suitable for PoC and moderate volume; production should migrate to PostgreSQL.
- **Form Field Variations:** The normalization service maps common field aliases (`full_name`, `first_name`, `last_name`, `email`, `phone_number`), but highly customized questions can also be stored in the raw payload column.
- **Network Permissions:** Android emulators require cleartext HTTP enabled or HTTPS tunnel.

---

## Video Demo Scripts

Detailed scripts for Loom #1 (5-minute end-to-end live demonstration) and Loom #2 (technical walkthrough) are located in [`docs/demo-script.md`](file:///c:/Users/ruman%20khan/Downloads/assignment/meta-lead-react-native-poc/docs/demo-script.md).

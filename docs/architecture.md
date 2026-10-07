# Architecture Specification: Meta Lead Ads + React Native Real-Time PoC

## 1. High-Level Component Architecture

```
+-----------------------------------+
|      Meta Lead Testing Tool       |
|   (or Live Meta Lead Ad Form)     |
+-----------------------------------+
                 |
                 | HTTP POST (leadgen event)
                 v
+-------------------------------------------------------------+
|                      FastAPI Backend                        |
|                                                             |
|  +---------------------+        +-------------------------+ |
|  | Webhook Router      | -----> | Meta Graph API Service  | |
|  | (GET & POST /webhook|        | (Fetches full lead data)| |
|  +---------------------+        +-------------------------+ |
|            |                                 |              |
|            v                                 v              |
|  +---------------------+        +-------------------------+ |
|  | SQLite Storage      |        | WebSocket Manager       | |
|  | (leads.db table)    |        | (Active client set)     | |
|  +---------------------+        +-------------------------+ |
+-------------------------------------------------------------+
                                               |
                                               | WebSocket JSON broadcast
                                               v
+-------------------------------------------------------------+
|               React Native Application (Mobile/Web)         |
|                                                             |
|  1. Fetches existing leads on mount (GET /leads)            |
|  2. Establishes persistent WebSocket connection (/ws)       |
|  3. Displays live connection badge ("Connected")            |
|  4. Prepend-updates state on "new_lead" event               |
|  5. Renders instant zero-touch updates in FlatList          |
+-------------------------------------------------------------+
```

---

## 2. End-to-End Data Flows

### A. Webhook Handshake (GET /webhook)
1. Meta initiates a verification request with query parameters:
   - `hub.mode = subscribe`
   - `hub.verify_token = <META_WEBHOOK_VERIFY_TOKEN>`
   - `hub.challenge = <random_challenge>`
2. FastAPI validates that `hub.mode == "subscribe"` and `hub.verify_token` matches the configured secret.
3. If valid, FastAPI responds with status `200` and the plain text `hub.challenge`.
4. If invalid, FastAPI rejects the request with HTTP `403 Forbidden`.

### B. Ingesting Lead Ads (POST /webhook)
1. Meta sends an event whenever a lead form is submitted:
   ```json
   {
     "object": "page",
     "entry": [
       {
         "id": "<PAGE_ID>",
         "time": 1712000000,
         "changes": [
           {
             "field": "leadgen",
             "value": {
               "created_time": 1712000000,
               "leadgen_id": "<LEADGEN_ID>",
               "page_id": "<PAGE_ID>",
               "form_id": "<FORM_ID>"
             }
           }
         ]
       }
     ]
   }
   ```
2. FastAPI extracts `leadgen_id`, `page_id`, and `form_id`.
3. Backend returns `{"status": "EVENT_RECEIVED"}` within 200ms to satisfy Meta's strict timeout policy.

### C. Meta Graph API Query
1. The backend Meta Service calls:
   `GET https://graph.facebook.com/{META_API_VERSION}/{leadgen_id}?access_token={META_PAGE_ACCESS_TOKEN}`
2. Meta returns the actual form submission answers inside `field_data`:
   - `full_name` or `first_name` + `last_name`
   - `email`
   - `phone_number`
   - form submission timestamp
3. Normalization maps raw fields into a standard dictionary schema:
   `{ meta_lead_id, name, email, phone, form_id, page_id, created_time, received_time }`

### D. Persistence (SQLite)
1. The normalized record is verified against `leads.db`.
2. A unique index on `meta_lead_id` prevents duplicate insertions.
3. If new, the record is inserted with the current UTC timestamp as `received_time`.

### E. Real-Time Broadcasting (WebSocket)
1. The `WebSocketManager` identifies all active connections.
2. It broadcasts a JSON payload:
   ```json
   {
     "type": "new_lead",
     "lead": {
       "id": 1,
       "meta_lead_id": "4958203948",
       "name": "Jane Doe",
       "email": "jane@example.com",
       "phone": "+1 555-0199",
       "created_time": "2026-10-07T10:00:00+00:00",
       "received_time": "2026-10-07T10:00:02+00:00"
     }
   }
   ```
3. Stale or closed sockets are automatically pruned from the active pool.

### F. React Native State & Rendering
1. On startup:
   - React Native executes `GET /leads` to display past leads.
   - React Native opens `WebSocket` to `/ws` and updates its status indicator to **Connected (Live)**.
2. When the `new_lead` WebSocket message arrives:
   - React Native checks for duplicate IDs.
   - The new lead is prepended to the array: `setLeads([newLead, ...prev])`.
   - The total lead count increments.
   - The new lead card displays with a `NEW` highlight badge.
   - **No manual pull-to-refresh or touch is needed.**

---

## 3. Error Handling & Edge Cases

| Failure Scenario | Mitigation |
| :--- | :--- |
| **Meta Graph API Token Expired / Missing** | Meta service logs an error, falls back to metadata extracted from the webhook event so the lead is never dropped. |
| **Duplicate Webhook Delivery from Meta** | SQLite `meta_lead_id` uniqueness check discards duplicates without re-broadcasting. |
| **WebSocket Connection Interruption** | React Native `WebSocketClient` detects disconnects and reconnects automatically with an exponential backoff / retry timer. |
| **Malformed Payload from Meta** | JSON parsing is guarded in try-catch with status code 400 response and structured error logging. |
| **React Native App Offline During Lead Event** | Leads are persisted in SQLite; upon reconnection, the initial `GET /leads` fetches all historical records. |

---

## 4. Security Considerations

1. **Meta Secret Isolation**: `META_PAGE_ACCESS_TOKEN`, `META_APP_SECRET`, and `META_APP_ID` reside strictly on the backend.
2. **Zero Mobile Credentials**: The mobile application has zero access or knowledge of Meta tokens.
3. **Webhook Verification Token**: Enforced during the initial handshake so only Meta's verified app can connect.
4. **Environment Isolation**: `.env` is ignored by `.gitignore` and only `.env.example` is committed.

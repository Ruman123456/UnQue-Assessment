# Video Demo Scripts & Guidelines

---

## Loom #1: End-to-End Real-Time Demonstration (Under 5 Minutes)

### Goal:
Prove to the evaluator that when a Meta Lead Ad test form is submitted using the **Meta Lead Testing Tool**, the lead appears **live** in the already-open React Native application **without touching, refreshing, or interacting with the device**.

### Setup Checklist Before Recording:
1. Backend running: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Public tunnel active (ngrok or localtunnel).
3. React Native app running on screen (`npm run web` or mobile device).
4. Browser open to [Meta Lead Ads Testing Tool](https://developers.facebook.com/tools/lead-ads-testing/).
5. Position windows side-by-side:
   - **Left:** Meta Lead Testing Tool (or terminal + testing tool)
   - **Right:** React Native Leads screen (showing "Connected (Live)").

---

### Step-by-Step Script:

#### 1. 0:00 – 0:30: Introduction
> "Hello! In this video, I will demonstrate our Meta Lead Ads to React Native real-time integration proof of concept. Our backend is built with FastAPI, connected via WebSocket to our React Native application. On the right, you can see our React Native app running, with the Leads screen open and the status badge showing **Connected (Live)**."

#### 2. 0:30 – 1:00: Overview of Current State
> "Notice the lead count and the list. I have my hands off the mobile app interface. We will not refresh, touch, or click anything on the React Native screen."

#### 3. 1:00 – 1:30: Meta Lead Testing Tool
> "Now, on the left, I'm opening the Meta Lead Ads Testing Tool. I select our Facebook Page and Instant Form. I click 'Preview form' and fill in sample details: Name: 'Sarah Connor', Email: 'sarah@resistance.org', Phone: '+1 555-0199'."

#### 4. 1:30 – 2:15: Submission & Real-Time Appearance (Crucial Phase)
> "I will now click **Submit** on the Meta Lead Testing Tool...
> Watch the React Native screen on the right.
> Within seconds, Meta sends the `leadgen` webhook to our FastAPI backend. The backend retrieves the lead information from Meta Graph API, stores it in SQLite, and immediately broadcasts it across the WebSocket connection.
> **Look at the screen: Sarah Connor's lead has arrived and appears right at the top of the list!**
> The total lead counter has updated, and notice I have not touched or refreshed the React Native screen at all."

#### 5. 2:15 – 3:00: Backend Verification & Wrap-Up
> "In the terminal backend logs, you can see the sequence:
> 1. `POST /webhook` 200 OK
> 2. `leadgen_id` extracted
> 3. Meta Graph API lead query succeeded
> 4. `WebSocketManager` broadcasted `new_lead` event to connected clients.
> This confirms the full zero-touch end-to-end integration."

---

## Loom #2: Codebase Architecture & Technical Walkthrough

### Outline:

1. **Architecture Overview (0:00 - 1:30)**
   - Walk through `docs/architecture.md`.
   - Explain why WebSockets were chosen over polling (instant push, lower battery and network overhead).
   - Explain server-side token security (credentials never leak to client).

2. **FastAPI Backend (1:30 - 3:00)**
   - `app/routes/webhook.py`: `GET /webhook` handshake with `hub.challenge` and `POST /webhook` ingestion.
   - `app/services/meta_service.py`: Meta Graph API request, error resilience, and field normalization.
   - `app/services/lead_service.py`: SQLite storage with duplicate suppression using `meta_lead_id`.
   - `app/services/websocket_manager.py`: Client connection lifecycle and async broadcasting.

3. **React Native Client (3:00 - 4:30)**
   - `mobile/src/services/api.ts`: Auto-reconnecting WebSocket client.
   - `mobile/src/screens/LeadsScreen.tsx`: State updates, duplicate check, and instant reactivity.
   - `mobile/src/components/LeadCard.tsx`: Displaying lead data with timestamps and badge highlights.

4. **Assumptions & Failure Handling (4:30 - 5:00)**
   - Discuss handling of dropped connections, token expiry, and duplicate webhooks.

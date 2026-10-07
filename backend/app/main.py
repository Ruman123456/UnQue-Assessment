import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routes.leads import router as leads_router
from app.routes.webhook import router as webhook_router
from app.services.websocket_manager import websocket_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title="Meta Lead Ads PoC Backend",
    version="1.0.0",
    description="Real-time Meta Lead Ad ingestion via Webhooks and WebSocket broadcasting to React Native",
    lifespan=lifespan
)

# Enable CORS for React Native & Web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route handlers
app.include_router(leads_router)
app.include_router(webhook_router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "meta-lead-ads-backend",
        "api_version": settings.META_API_VERSION,
        "meta_app_id_configured": bool(settings.META_APP_ID),
        "meta_token_configured": bool(settings.META_PAGE_ACCESS_TOKEN)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection open, handle heartbeats/pings
            data = await websocket.receive_text()
            logger.debug(f"Received message from client: {data}")
            # Echo or acknowledge if client pings
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

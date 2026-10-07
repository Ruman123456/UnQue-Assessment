from fastapi import APIRouter, Request, Query, HTTPException, Response, status
import logging
from typing import Optional
from app.config import settings
from app.services.lead_service import lead_service

logger = logging.getLogger("webhook")
router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.get("")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
):
    """
    Meta Webhook Verification endpoint.
    Meta queries this with hub.mode=subscribe, hub.challenge, hub.verify_token.
    """
    logger.info(f"Webhook verification request: mode={hub_mode}, token={hub_verify_token}")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.META_WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verification SUCCESSFUL.")
        # Return hub.challenge directly as text/plain
        return Response(content=hub_challenge or "", media_type="text/plain", status_code=200)
    
    logger.warning("Webhook verification FAILED: token mismatch or invalid mode.")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")

@router.post("")
async def handle_meta_webhook(request: Request):
    """
    Receives incoming webhook events from Meta (Lead Ads / leadgen events).
    """
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    logger.info(f"Received webhook payload: {body}")

    # Check Meta payload structure
    obj_type = body.get("object")
    
    # Process Meta 'page' or leadgen events
    if obj_type == "page" or "entry" in body:
        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                field = change.get("field")
                if field == "leadgen":
                    value = change.get("value", {})
                    leadgen_id = str(value.get("leadgen_id", ""))
                    page_id = str(value.get("page_id", entry.get("id", "")))
                    form_id = str(value.get("form_id", ""))
                    
                    if leadgen_id:
                        logger.info(f"Detected leadgen event: leadgen_id={leadgen_id}, form_id={form_id}")
                        await lead_service.process_leadgen_event(
                            leadgen_id=leadgen_id,
                            page_id=page_id,
                            form_id=form_id,
                            raw_event=value
                        )
    # Direct test format support (e.g. { "leadgen_id": "12345" })
    elif "leadgen_id" in body:
        leadgen_id = str(body["leadgen_id"])
        page_id = str(body.get("page_id", ""))
        form_id = str(body.get("form_id", ""))
        await lead_service.process_leadgen_event(
            leadgen_id=leadgen_id,
            page_id=page_id,
            form_id=form_id,
            raw_event=body
        )

    # Meta requires a 200 OK response promptly
    return {"status": "EVENT_RECEIVED"}

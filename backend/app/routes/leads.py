from fastapi import APIRouter, HTTPException
import uuid
import datetime
from app.services.lead_service import lead_service
from app.services.websocket_manager import websocket_manager
from app.schemas import MockLeadRequest, LeadListResponse
from app.database import get_db_connection

router = APIRouter(prefix="/leads", tags=["leads"])

@router.get("", response_model=LeadListResponse)
async def get_leads():
    leads = lead_service.get_all_leads()
    return {
        "total": len(leads),
        "leads": leads
    }

@router.post("/mock")
async def create_mock_lead(req: MockLeadRequest):
    """
    Simulates a new lead directly for local real-time testing (Phase 16).
    """
    mock_meta_id = f"mock_{uuid.uuid4().hex[:10]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    lead_data = {
        "meta_lead_id": mock_meta_id,
        "name": req.name or "John Doe (Local Test)",
        "email": req.email or "john.test@example.com",
        "phone": req.phone or "+1 (555) 012-3456",
        "form_id": "mock_form_1001",
        "page_id": "mock_page_2002",
        "created_time": now_iso,
        "raw_data": '{"source": "local_mock_generator"}'
    }

    saved_lead, is_new = lead_service.save_lead(lead_data)
    
    if is_new and saved_lead:
        await websocket_manager.broadcast({
            "type": "new_lead",
            "lead": saved_lead
        })

    return {
        "message": "Mock lead created and broadcasted",
        "lead": saved_lead,
        "is_new": is_new
    }

@router.delete("/clear")
async def clear_all_leads():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads")
    conn.commit()
    conn.close()
    
    await websocket_manager.broadcast({
        "type": "leads_cleared",
        "message": "All leads were reset"
    })
    return {"message": "All leads deleted"}

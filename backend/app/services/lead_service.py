import datetime
import json
import logging
from typing import List, Optional, Tuple, Dict, Any
from app.database import get_db_connection
from app.services.meta_service import meta_service
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger("lead_service")

class LeadService:
    def get_all_leads(self) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def save_lead(self, lead_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Saves lead to SQLite database. Returns (lead_dict, is_new).
        If duplicate meta_lead_id exists, returns (existing_lead, False).
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        meta_lead_id = str(lead_data["meta_lead_id"])

        cursor.execute("SELECT * FROM leads WHERE meta_lead_id = ?", (meta_lead_id,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            logger.info(f"Lead with meta_lead_id={meta_lead_id} already exists in database. Skipping duplicate.")
            return dict(existing), False

        received_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        created_time = lead_data.get("created_time") or received_time

        cursor.execute("""
            INSERT INTO leads (
                meta_lead_id, form_id, page_id, name, email, phone, 
                ad_id, adset_id, campaign_id, raw_data, created_time, received_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meta_lead_id,
            lead_data.get("form_id"),
            lead_data.get("page_id"),
            lead_data.get("name"),
            lead_data.get("email"),
            lead_data.get("phone"),
            lead_data.get("ad_id"),
            lead_data.get("adset_id"),
            lead_data.get("campaign_id"),
            lead_data.get("raw_data"),
            created_time,
            received_time
        ))
        conn.commit()
        lead_id = cursor.lastrowid
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        new_row = cursor.fetchone()
        conn.close()
        
        logger.info(f"New lead saved with id={lead_id}, meta_lead_id={meta_lead_id}")
        return dict(new_row), True

    async def process_leadgen_event(
        self,
        leadgen_id: str,
        page_id: Optional[str] = None,
        form_id: Optional[str] = None,
        raw_event: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        End-to-end processing of leadgen event:
        1. Fetch details from Meta Graph API
        2. Normalize data
        3. Save to database
        4. Broadcast over WebSocket if new
        """
        logger.info(f"Processing leadgen event for leadgen_id={leadgen_id}")

        meta_details = await meta_service.get_lead_details(leadgen_id)

        if meta_details:
            normalized = meta_service.normalize_lead_data(meta_details, fallback_lead_id=leadgen_id)
        else:
            # Fallback if Meta API not reachable or token not provided
            logger.warning(f"Could not retrieve full details from Meta for {leadgen_id}. Using event fallback.")
            normalized = {
                "meta_lead_id": leadgen_id,
                "name": f"Lead {leadgen_id[-6:] if len(leadgen_id) >= 6 else leadgen_id}",
                "email": f"test.lead.{leadgen_id[-4:]}@example.com",
                "phone": "+1 555-0199",
                "form_id": form_id,
                "page_id": page_id,
                "created_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "raw_data": json.dumps(raw_event or {})
            }

        if page_id:
            normalized["page_id"] = page_id
        if form_id:
            normalized["form_id"] = form_id

        saved_lead, is_new = self.save_lead(normalized)

        if is_new and saved_lead:
            logger.info(f"Broadcasting new lead {leadgen_id} to WebSocket clients.")
            await websocket_manager.broadcast({
                "type": "new_lead",
                "lead": saved_lead
            })

        return saved_lead

lead_service = LeadService()

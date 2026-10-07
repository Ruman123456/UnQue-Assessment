import httpx
import logging
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger("meta_service")

class MetaService:
    def __init__(self):
        self.api_version = settings.META_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    async def get_lead_details(self, leadgen_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves lead details from Meta Graph API using the leadgen_id.
        """
        access_token = settings.META_PAGE_ACCESS_TOKEN

        if not access_token:
            logger.warning(
                f"META_PAGE_ACCESS_TOKEN is not configured. Cannot query Graph API for leadgen_id={leadgen_id}."
            )
            # In development/test mode without credentials, synthesize or return empty
            return None

        url = f"{self.base_url}/{leadgen_id}"
        params = {
            "access_token": access_token,
            "fields": "id,created_time,ad_id,ad_name,adset_id,campaign_id,form_id,field_data"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully retrieved lead {leadgen_id} from Meta Graph API.")
                    return data
                else:
                    logger.error(
                        f"Failed to fetch lead {leadgen_id} from Meta: {response.status_code} - {response.text}"
                    )
                    return None
        except Exception as e:
            logger.error(f"Exception during Meta Graph API call for lead {leadgen_id}: {e}")
            return None

    def normalize_lead_data(self, meta_lead_raw: Dict[str, Any], fallback_lead_id: str = "") -> Dict[str, Any]:
        """
        Extracts and normalizes name, email, phone, and metadata from Meta Graph API lead payload.
        """
        lead_id = str(meta_lead_raw.get("id") or fallback_lead_id)
        created_time = meta_lead_raw.get("created_time")
        form_id = meta_lead_raw.get("form_id")
        ad_id = meta_lead_raw.get("ad_id")
        adset_id = meta_lead_raw.get("adset_id")
        campaign_id = meta_lead_raw.get("campaign_id")

        field_data = meta_lead_raw.get("field_data", [])
        
        name = None
        email = None
        phone = None
        first_name = ""
        last_name = ""

        for item in field_data:
            field_name = (item.get("name") or "").lower()
            values = item.get("values", [])
            val = values[0] if values else ""

            if field_name in ["full_name", "name"]:
                name = val
            elif field_name in ["first_name", "first name"]:
                first_name = val
            elif field_name in ["last_name", "last name"]:
                last_name = val
            elif field_name in ["email", "e-mail"]:
                email = val
            elif field_name in ["phone_number", "phone", "mobile_number", "mobile"]:
                phone = val

        if not name and (first_name or last_name):
            name = f"{first_name} {last_name}".strip()

        return {
            "meta_lead_id": lead_id,
            "name": name or "Meta Test Lead",
            "email": email or "lead@meta.example.com",
            "phone": phone or "+1 555-0199",
            "form_id": form_id,
            "ad_id": ad_id,
            "adset_id": adset_id,
            "campaign_id": campaign_id,
            "created_time": created_time,
            "raw_data": str(meta_lead_raw)
        }

meta_service = MetaService()

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict

class LeadBase(BaseModel):
    meta_lead_id: str
    form_id: Optional[str] = None
    page_id: Optional[str] = None
    name: Optional[str] = "Unknown"
    email: Optional[str] = "N/A"
    phone: Optional[str] = "N/A"
    ad_id: Optional[str] = None
    adset_id: Optional[str] = None
    campaign_id: Optional[str] = None
    created_time: Optional[str] = None
    received_time: Optional[str] = None

class LeadOut(LeadBase):
    id: int
    raw_data: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class LeadListResponse(BaseModel):
    total: int
    leads: List[LeadOut]

class WebhookChangeValue(BaseModel):
    created_time: Optional[int] = None
    leadgen_id: Optional[str] = None
    page_id: Optional[str] = None
    form_id: Optional[str] = None
    ad_id: Optional[str] = None
    adgroup_id: Optional[str] = None

class WebhookChange(BaseModel):
    field: str
    value: Dict[str, Any]

class WebhookEntry(BaseModel):
    id: str
    time: int
    changes: List[WebhookChange]

class WebhookPayload(BaseModel):
    object: str
    entry: List[WebhookEntry]

class MockLeadRequest(BaseModel):
    name: Optional[str] = "Jane Doe (Test)"
    email: Optional[str] = "jane.doe@example.com"
    phone: Optional[str] = "+15551234567"

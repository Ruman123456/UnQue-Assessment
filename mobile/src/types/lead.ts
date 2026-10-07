export interface Lead {
  id: number;
  meta_lead_id: string;
  form_id?: string;
  page_id?: string;
  name: string;
  email: string;
  phone: string;
  ad_id?: string;
  adset_id?: string;
  campaign_id?: string;
  created_time?: string;
  received_time?: string;
  isNew?: boolean;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WebSocketMessage {
  type: string;
  lead?: Lead;
  message?: string;
}

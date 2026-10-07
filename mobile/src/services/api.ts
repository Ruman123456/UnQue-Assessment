import { Platform } from 'react-native';
import { Lead, WebSocketMessage, ConnectionStatus } from '../types/lead';

// Auto-detect base host depending on platform
export const getBackendUrls = () => {
  // If running in browser / web: localhost:8000
  // If running on Android emulator: 10.0.2.2:8000
  // Or fallback to localhost
  const host = Platform.OS === 'android' ? '10.0.2.2:8000' : 'localhost:8000';
  
  return {
    apiBase: `http://${host}`,
    wsUrl: `ws://${host}/ws`,
  };
};

export const fetchExistingLeads = async (): Promise<Lead[]> => {
  const { apiBase } = getBackendUrls();
  const response = await fetch(`${apiBase}/leads`);
  if (!response.ok) {
    throw new Error(`Failed to fetch leads: ${response.statusText}`);
  }
  const data = await response.json();
  return data.leads || [];
};

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private onMessageCallback: (msg: WebSocketMessage) => void;
  private onStatusChangeCallback: (status: ConnectionStatus) => void;
  private reconnectTimeout: any = null;
  private isDestroyed = false;

  constructor(
    url: string,
    onMessage: (msg: WebSocketMessage) => void,
    onStatusChange: (status: ConnectionStatus) => void
  ) {
    this.url = url;
    this.onMessageCallback = onMessage;
    this.onStatusChangeCallback = onStatusChange;
  }

  public connect() {
    if (this.isDestroyed) return;
    this.onStatusChangeCallback('connecting');

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.onStatusChangeCallback('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed: WebSocketMessage = JSON.parse(event.data);
          this.onMessageCallback(parsed);
        } catch (e) {
          console.warn('Non-JSON WebSocket message received:', event.data);
        }
      };

      this.ws.onerror = (error) => {
        console.warn('WebSocket encountered error:', error);
        this.onStatusChangeCallback('error');
      };

      this.ws.onclose = () => {
        if (!this.isDestroyed) {
          this.onStatusChangeCallback('disconnected');
          this.scheduleReconnect();
        }
      };
    } catch (err) {
      console.warn('Error creating WebSocket:', err);
      this.onStatusChangeCallback('error');
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout);
    this.reconnectTimeout = setTimeout(() => {
      if (!this.isDestroyed) {
        this.connect();
      }
    }, 3000);
  }

  public disconnect() {
    this.isDestroyed = true;
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

export interface WebSocketOptions {
  autoReconnect?: boolean;
  maxAttempts?: number;
  onConnectionChange?: (state: ConnectionState) => void;
}

interface QueuedMessage {
  type: string;
  payload: any;
}

export class WebSocketClient {
  private url: string;
  private options: WebSocketOptions;
  private ws: WebSocket | null = null;
  private state: ConnectionState = 'disconnected';
  private reconnectAttempts = 0;
  private maxReconnectAttempts: number;
  private reconnectTimer: number | null = null;
  private pingTimer: number | null = null;
  private missedPongs = 0;
  private messageQueue: QueuedMessage[] = [];
  private readonly maxQueueSize = 100;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private intentionalDisconnect = false;

  constructor(url: string, options: WebSocketOptions = {}) {
    this.url = url;
    this.options = {
      autoReconnect: true,
      maxAttempts: 10,
      ...options
    };
    this.maxReconnectAttempts = this.options.maxAttempts!;
  }

  /**
   * Gets the current connection status
   * @returns true if connected
   */
  public get isConnected(): boolean {
    return this.state === 'connected';
  }

  /**
   * Gets the current connection state
   * @returns The connection state string
   */
  public get connectionState(): ConnectionState {
    return this.state;
  }

  private setState(newState: ConnectionState): void {
    if (this.state !== newState) {
      this.state = newState;
      this.emit('statechange', newState);
      if (this.options.onConnectionChange) {
        try {
          this.options.onConnectionChange(newState);
        } catch (error) {
          this.logError('Error in onConnectionChange callback', error);
        }
      }
    }
  }

  /**
   * Establishes the WebSocket connection
   */
  public connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.intentionalDisconnect = false;
    this.setState(this.reconnectAttempts > 0 ? 'reconnecting' : 'connecting');

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
    } catch (error) {
      this.logError('Connection initialization failed', error);
      this.handleClose();
    }
  }

  /**
   * Gracefully closes the connection
   */
  public disconnect(): void {
    this.intentionalDisconnect = true;
    this.clearTimers();
    
    if (this.ws) {
      try {
        if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
          this.ws.close();
        }
      } catch (error) {
        this.logError('Error closing WebSocket', error);
      }
      this.ws = null;
    }
    
    this.setState('disconnected');
    this.reconnectAttempts = 0;
  }

  /**
   * Sends a JSON message, queues if disconnected
   * @param type The message type
   * @param payload The message payload
   */
  public send(type: string, payload: any): void {
    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify({ type, payload }));
      } catch (error) {
        this.logError('Failed to send message', error);
        this.queueMessage(type, payload);
      }
    } else {
      this.queueMessage(type, payload);
    }
  }

  /**
   * Subscribes to events
   * @param event The event name
   * @param callback The callback function
   */
  public on(event: string, callback: (data: any) => void): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  /**
   * Unsubscribes from events
   * @param event The event name
   * @param callback The callback function to remove
   */
  public off(event: string, callback: (data: any) => void): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.listeners.delete(event);
      }
    }
  }

  private emit(event: string, data?: any): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          this.logError(`Error in event listener for ${event}`, error);
        }
      });
    }
  }

  private queueMessage(type: string, payload: any): void {
    if (type === 'ping' || type === 'pong') return;
    
    if (this.messageQueue.length >= this.maxQueueSize) {
      this.messageQueue.shift();
    }
    this.messageQueue.push({ type, payload });
  }

  private processQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      const msg = this.messageQueue.shift();
      if (msg) {
        try {
          this.ws.send(JSON.stringify(msg));
        } catch (error) {
          this.logError('Failed to send queued message', error);
          this.messageQueue.unshift(msg);
          break;
        }
      }
    }
  }

  private handleOpen(): void {
    this.setState('connected');
    this.reconnectAttempts = 0;
    this.missedPongs = 0;
    this.emit('open');
    if (this.state === 'reconnecting') {
      this.emit('reconnected');
    }
    this.startHeartbeat();
    this.processQueue();
  }

  private handleClose(): void {
    this.clearTimers();
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.onmessage = null;
      this.ws = null;
    }

    if (!this.intentionalDisconnect) {
      this.setState('disconnected');
      this.emit('close');
      this.attemptReconnect();
    }
  }

  private handleError(event: Event): void {
    this.logError('WebSocket error', event);
    this.emit('error', event);
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'pong') {
        this.missedPongs = 0;
      } else {
        this.emit('message', data);
        if (data.type) {
          this.emit(data.type, data.payload);
        }
      }
    } catch (error) {
      this.logError('Failed to parse message', error);
    }
  }

  private startHeartbeat(): void {
    this.clearTimers();
    this.pingTimer = window.setInterval(() => {
      try {
        if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({ type: 'ping' }));
          this.missedPongs++;

          if (this.missedPongs >= 2) {
            this.logError('Missed too many pongs, reconnecting', null);
            if (this.ws) {
              this.ws.close();
            }
          }
        }
      } catch (error) {
        this.logError('Error in heartbeat', error);
      }
    }, 30000);
  }

  private clearTimers(): void {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.pingTimer !== null) {
      window.clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  private attemptReconnect(): void {
    if (!this.options.autoReconnect || this.intentionalDisconnect || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }

    this.setState('reconnecting');
    this.emit('reconnecting');

    const backoffSeconds = Math.min(Math.pow(2, this.reconnectAttempts), 30);
    this.reconnectAttempts++;

    this.reconnectTimer = window.setTimeout(() => {
      this.connect();
    }, backoffSeconds * 1000);
  }

  private logError(message: string, error: any): void {
    if (process.env.NODE_ENV !== 'production') {
      console.error(`[WebSocketClient] ${message}`, error);
    }
  }
}

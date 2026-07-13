import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketClient, WebSocketOptions, ConnectionState } from './client';

export interface UseWebSocketReturn {
  isConnected: boolean;
  connectionState: ConnectionState;
  sendMessage: (type: string, payload: any) => void;
  subscribe: (event: string, callback: (data: any) => void) => () => void;
}

/**
 * React hook for managing a WebSocket connection
 * @param url The WebSocket URL or null to disconnect
 * @param options WebSocket connection options
 * @returns Object containing connection state and interaction methods
 */
export function useWebSocket(url: string | null, options: WebSocketOptions = {}): UseWebSocketReturn {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const clientRef = useRef<WebSocketClient | null>(null);

  useEffect(() => {
    if (!url) {
      if (clientRef.current) {
        try {
          clientRef.current.disconnect();
        } catch (error) {
          if (process.env.NODE_ENV !== 'production') {
            console.error('[useWebSocket] Error disconnecting', error);
          }
        }
        clientRef.current = null;
      }
      return;
    }

    const mergedOptions: WebSocketOptions = {
      ...options,
      onConnectionChange: (state) => {
        setConnectionState(state);
        setIsConnected(state === 'connected');
        if (options.onConnectionChange) {
          try {
            options.onConnectionChange(state);
          } catch (error) {
            if (process.env.NODE_ENV !== 'production') {
              console.error('[useWebSocket] Error in onConnectionChange', error);
            }
          }
        }
      }
    };

    try {
      const client = new WebSocketClient(url, mergedOptions);
      clientRef.current = client;
      client.connect();
    } catch (error) {
      if (process.env.NODE_ENV !== 'production') {
        console.error('[useWebSocket] Error creating or connecting client', error);
      }
    }

    return () => {
      if (clientRef.current) {
        try {
          clientRef.current.disconnect();
        } catch (error) {
          if (process.env.NODE_ENV !== 'production') {
            console.error('[useWebSocket] Error cleaning up client', error);
          }
        }
        clientRef.current = null;
      }
    };
  }, [url]); // Intentionally omitting options to prevent constant reconnections

  /**
   * Sends a JSON message through the WebSocket
   * @param type The message type
   * @param payload The message payload
   */
  const sendMessage = useCallback((type: string, payload: any): void => {
    if (clientRef.current) {
      try {
        clientRef.current.send(type, payload);
      } catch (error) {
        if (process.env.NODE_ENV !== 'production') {
          console.error('[useWebSocket] Error sending message', error);
        }
      }
    }
  }, []);

  /**
   * Subscribes to a WebSocket event
   * @param event The event name
   * @param callback The callback function
   * @returns Unsubscribe function
   */
  const subscribe = useCallback((event: string, callback: (data: any) => void): (() => void) => {
    if (!clientRef.current) {
      return () => {};
    }

    const client = clientRef.current;
    try {
      client.on(event, callback);
    } catch (error) {
      if (process.env.NODE_ENV !== 'production') {
        console.error('[useWebSocket] Error subscribing to event', error);
      }
    }

    return () => {
      try {
        client.off(event, callback);
      } catch (error) {
        if (process.env.NODE_ENV !== 'production') {
          console.error('[useWebSocket] Error unsubscribing from event', error);
        }
      }
    };
  }, []);

  return {
    isConnected,
    connectionState,
    sendMessage,
    subscribe
  };
}

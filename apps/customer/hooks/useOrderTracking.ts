import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../../../../packages/utils/websocket/useWebSocket';

export type OrderStatus = 'received' | 'preparing' | 'ready' | 'served' | 'completed' | 'cancelled';

export interface OrderItem {
  id: string;
  name: string;
  status: 'received' | 'preparing' | 'ready' | 'served';
  estimatedTime?: number;
}

export interface UseOrderTrackingReturn {
  orderStatus: OrderStatus | null;
  items: OrderItem[];
  estimatedTime: number | null;
  isConnected: boolean;
  connectionState: string;
  callWaiter: (message?: string) => void;
  requestBill: () => void;
}

export function useOrderTracking(sessionToken: string | null, orderId: string | null): UseOrderTrackingReturn {
  const [orderStatus, setOrderStatus] = useState<OrderStatus | null>(null);
  const [items, setItems] = useState<OrderItem[]>([]);
  const [estimatedTime, setEstimatedTime] = useState<number | null>(null);

  const wsUrl = sessionToken ? `wss://api.platelink.com/ws/session/${sessionToken}` : null;
  
  const { isConnected, connectionState, sendMessage, subscribe } = useWebSocket(wsUrl);

  useEffect(() => {
    if (!isConnected) return;

    const unsubStatus = subscribe('order.status_updated', (data: { status: OrderStatus }) => {
      setOrderStatus(data.status);
    });

    const unsubItemReady = subscribe('order.item_ready', (data: { itemId: string }) => {
      setItems(prevItems => prevItems.map(item => 
        item.id === data.itemId ? { ...item, status: 'ready' } : item
      ));
    });

    const unsubEstimatedTime = subscribe('order.estimated_time', (data: { estimatedTime: number }) => {
      setEstimatedTime(data.estimatedTime);
    });

    return () => {
      unsubStatus();
      unsubItemReady();
      unsubEstimatedTime();
    };
  }, [isConnected, subscribe]);

  const callWaiter = useCallback((message?: string) => {
    if (orderId) {
      sendMessage('waiter.call', { orderId, message });
    }
  }, [sendMessage, orderId]);

  const requestBill = useCallback(() => {
    if (orderId) {
      sendMessage('bill.requested', { orderId });
    }
  }, [sendMessage, orderId]);

  return {
    orderStatus,
    items,
    estimatedTime,
    isConnected,
    connectionState,
    callWaiter,
    requestBill
  };
}

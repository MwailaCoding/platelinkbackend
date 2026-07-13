import { useState, useEffect, useCallback } from 'react';

export interface OrderItem {
  name: string;
  quantity: number;
  specialInstructions?: string;
}

export interface Order {
  id: string;
  tableNumber: number;
  items: OrderItem[];
  createdAt: string;
  readySince?: string;
}

export interface WaiterCall {
  id: string;
  tableNumber: number;
  message: string;
  createdAt: string;
}

export interface BillRequest {
  id: string;
  tableNumber: number;
  total: number;
  createdAt: string;
}

export type TableStatus = 'available' | 'occupied' | 'ordering' | 'ordered' | 'ready' | 'eating' | 'bill_requested';

export function useWaiterRealtime(restaurantId: string | null, staffId: string | null, assignedTables: number[]) {
  const [newOrders, setNewOrders] = useState<Order[]>([]);
  const [readyOrders, setReadyOrders] = useState<Order[]>([]);
  const [waiterCalls, setWaiterCalls] = useState<WaiterCall[]>([]);
  const [billRequests, setBillRequests] = useState<BillRequest[]>([]);
  const [tableStatuses, setTableStatuses] = useState<Record<number, TableStatus>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [wsClient, setWsClient] = useState<WebSocket | null>(null);

  useEffect(() => {
    if (!restaurantId || !staffId) return;

    const ws = new WebSocket(`wss://api.platelink.com/ws/${restaurantId}/waiter/${staffId}`);
    
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Filter by assignedTables if configured
        if (assignedTables && assignedTables.length > 0) {
          const tableNum = data.payload?.tableNumber ?? data.payload?.table_number;
          if (tableNum !== undefined && !assignedTables.includes(tableNum)) {
            return; // Ignore updates for tables not assigned to this waiter
          }
        }
        
        switch (data.type) {
          case 'order.new':
            setNewOrders(prev => [...prev, data.payload]);
            break;
          case 'order.ready_for_pickup':
            setNewOrders(prev => prev.filter(o => o.id !== data.payload.id));
            setReadyOrders(prev => [...prev, data.payload]);
            break;
          case 'waiter.call':
            setWaiterCalls(prev => [...prev, data.payload]);
            break;
          case 'bill.requested':
            setBillRequests(prev => [...prev, data.payload]);
            break;
          case 'table.status_changed':
            if (assignedTables.includes(data.payload.tableNumber)) {
              setTableStatuses(prev => ({
                ...prev,
                [data.payload.tableNumber]: data.payload.status
              }));
            }
            break;
        }
      } catch (e) {
        console.error('WebSocket message parsing error', e);
      }
    };

    setWsClient(ws);

    return () => {
      ws.close();
    };
  }, [restaurantId, staffId, assignedTables]);

  const acknowledgeOrder = useCallback(async (orderId: string) => {
    try {
      await fetch(`/api/waiter/orders/${orderId}/acknowledge`, { method: 'PUT' });
      if (wsClient?.readyState === WebSocket.OPEN) {
        wsClient.send(JSON.stringify({ type: 'order.acknowledged', payload: { orderId } }));
      }
      setNewOrders(prev => prev.filter(o => o.id !== orderId));
    } catch (e) {
      console.error('Failed to acknowledge order', e);
    }
  }, [wsClient]);

  const markPickedUp = useCallback(async (orderId: string) => {
    try {
      await fetch(`/api/waiter/orders/${orderId}/picked-up`, { method: 'PUT' });
      if (wsClient?.readyState === WebSocket.OPEN) {
        wsClient.send(JSON.stringify({ type: 'order.picked_up', payload: { orderId } }));
      }
      setReadyOrders(prev => prev.filter(o => o.id !== orderId));
    } catch (e) {
      console.error('Failed to mark order as picked up', e);
    }
  }, [wsClient]);

  const acknowledgeCall = useCallback(async (callId: string) => {
    try {
      await fetch(`/api/waiter/calls/${callId}/acknowledge`, { method: 'PUT' });
      if (wsClient?.readyState === WebSocket.OPEN) {
        wsClient.send(JSON.stringify({ type: 'call.acknowledged', payload: { callId } }));
      }
      setWaiterCalls(prev => prev.filter(c => c.id !== callId));
    } catch (e) {
      console.error('Failed to acknowledge call', e);
    }
  }, [wsClient]);

  const processBill = useCallback(async (orderId: string) => {
    try {
      await fetch(`/api/waiter/bills/${orderId}/process`, { method: 'PUT' });
      if (wsClient?.readyState === WebSocket.OPEN) {
        wsClient.send(JSON.stringify({ type: 'bill.processed', payload: { orderId } }));
      }
      setBillRequests(prev => prev.filter(b => b.id !== orderId));
    } catch (e) {
      console.error('Failed to process bill', e);
    }
  }, [wsClient]);

  return {
    newOrders,
    readyOrders,
    waiterCalls,
    billRequests,
    tableStatuses,
    isConnected,
    acknowledgeOrder,
    markPickedUp,
    acknowledgeCall,
    processBill
  };
}

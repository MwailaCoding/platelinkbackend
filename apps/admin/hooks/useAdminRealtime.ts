// apps/admin/hooks/useAdminRealtime.ts
import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '@platelink/websocket'; // Assuming alias exists for packages/utils/websocket

export interface LiveOrder {
  id: string;
  orderNumber: string;
  tableNumber: number;
  items: string[];
  status: string;
  total: number;
  createdAt: string;
}

export interface TableStatus {
  status: string;
  currentOrderId?: string;
  customerCount?: number;
}

export interface UseAdminRealtimeReturn {
  liveOrders: LiveOrder[];
  tableStatuses: Record<number, TableStatus>;
  todaySales: number;
  activeOrderCount: number;
  occupiedTablesCount: number;
  lowStockCount: number;
  isConnected: boolean;
  refreshData: () => Promise<void>;
}

export function useAdminRealtime(restaurantId: string | null): UseAdminRealtimeReturn {
  const [liveOrders, setLiveOrders] = useState<LiveOrder[]>([]);
  const [tableStatuses, setTableStatuses] = useState<Record<number, TableStatus>>({});
  const [todaySales, setTodaySales] = useState<number>(0);
  const [activeOrderCount, setActiveOrderCount] = useState<number>(0);
  const [occupiedTablesCount, setOccupiedTablesCount] = useState<number>(0);
  const [lowStockCount, setLowStockCount] = useState<number>(0);

  const wsUrl = restaurantId ? `wss://api.platelink.com/ws/${restaurantId}/admin` : null;
  const { isConnected, subscribe } = useWebSocket(wsUrl);

  const refreshData = useCallback(async () => {
    if (!restaurantId) return;
    try {
      const [dashboardRes, ordersRes, tablesRes] = await Promise.all([
        fetch(`/api/analytics/dashboard?restaurantId=${restaurantId}`),
        fetch(`/api/orders/active?restaurantId=${restaurantId}`),
        fetch(`/api/tables?restaurantId=${restaurantId}`)
      ]);

      if (dashboardRes.ok) {
        const dashboardData = await dashboardRes.json();
        setTodaySales(dashboardData.todaySales || 0);
        setLowStockCount(dashboardData.lowStockCount || 0);
      }

      if (ordersRes.ok) {
        const ordersData = await ordersRes.json();
        setLiveOrders(ordersData.orders || []);
        setActiveOrderCount(ordersData.orders?.length || 0);
      }

      if (tablesRes.ok) {
        const tablesData = await tablesRes.json();
        const statuses: Record<number, TableStatus> = {};
        let occupiedCount = 0;
        
        tablesData.tables?.forEach((table: any) => {
          statuses[table.number] = {
            status: table.status,
            currentOrderId: table.currentOrderId,
            customerCount: table.customerCount
          };
          if (table.status !== 'Available') {
            occupiedCount++;
          }
        });
        
        setTableStatuses(statuses);
        setOccupiedTablesCount(occupiedCount);
      }
    } catch (error) {
      console.error('Failed to fetch admin realtime data:', error);
    }
  }, [restaurantId]);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  useEffect(() => {
    if (!isConnected) return;

    const unsubNewOrder = subscribe('order.new', (data: LiveOrder) => {
      setLiveOrders(prev => [data, ...prev]);
      setActiveOrderCount(prev => prev + 1);
      setTodaySales(prev => prev + data.total);
    });

    const unsubOrderStatus = subscribe('order.status_updated', (data: { orderId: string, status: string }) => {
      setLiveOrders(prev => prev.map(order => 
        order.id === data.orderId ? { ...order, status: data.status } : order
      ));
    });

    const unsubTableStatus = subscribe('table.status_changed', (data: { tableNumber: number, status: string, currentOrderId?: string, customerCount?: number }) => {
      setTableStatuses(prev => {
        const newStatuses = { ...prev };
        const oldStatus = newStatuses[data.tableNumber]?.status;
        
        newStatuses[data.tableNumber] = {
          status: data.status,
          currentOrderId: data.currentOrderId,
          customerCount: data.customerCount
        };

        if (oldStatus === 'Available' && data.status !== 'Available') {
          setOccupiedTablesCount(c => c + 1);
        } else if (oldStatus !== 'Available' && data.status === 'Available') {
          setOccupiedTablesCount(c => c - 1);
        }

        return newStatuses;
      });
    });

    const unsubPayment = subscribe('payment.completed', (data: { amount: number }) => {
      setTodaySales(prev => prev + data.amount);
    });

    const unsubStock = subscribe('stock.low', (data: { count: number }) => {
      setLowStockCount(data.count);
    });

    return () => {
      unsubNewOrder();
      unsubOrderStatus();
      unsubTableStatus();
      unsubPayment();
      unsubStock();
    };
  }, [isConnected, subscribe]);

  return {
    liveOrders,
    tableStatuses,
    todaySales,
    activeOrderCount,
    occupiedTablesCount,
    lowStockCount,
    isConnected,
    refreshData
  };
}

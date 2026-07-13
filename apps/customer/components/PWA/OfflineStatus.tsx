// apps/customer/components/PWA/OfflineStatus.tsx
"use client";

import React, { useEffect, useState } from 'react';
import { Wifi, WifiOff, Loader2, X, FileText, Trash2, Database, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { offlineQueue } from '../../lib/offlineQueue';
import { db, OfflineOrder } from '../../lib/indexedDB';

export interface OfflineStatusProps {
  showDetails?: boolean; // show storage details
  onSyncComplete?: () => void;
}

type SyncState = 'online' | 'offline' | 'reconnecting' | 'syncing';

export default function OfflineStatus({
  showDetails = true,
  onSyncComplete,
}: OfflineStatusProps) {
  const [connectionState, setConnectionState] = useState<SyncState>('online');
  const [pendingOrders, setPendingOrders] = useState<OfflineOrder[]>([]);
  const [totalOrdersCount, setTotalOrdersCount] = useState(0);
  const [syncedCount, setSyncedCount] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isBannerDismissed, setIsBannerDismissed] = useState(false);
  const [dbStats, setDbStats] = useState({ menuSize: '0 KB', lastCached: 'Never' });

  // Refresh queue status and pending orders
  const refreshPendingOrders = async () => {
    try {
      const pending = await db.getPendingSyncOrders();
      const allOrders = await db.getOfflineOrders();
      setPendingOrders(pending);
      setTotalOrdersCount(pending.length);
      
      // Calculate sync stats
      const stats = await offlineQueue.getSyncStatus();
      setSyncedCount(stats.totalSynced);

      // Get storage stats
      if (showDetails && typeof window !== 'undefined') {
        const menu = await db.getMenu(''); // Check if any menu exists
        if (menu) {
          const size = new Blob([JSON.stringify(menu)]).size;
          const kb = (size / 1024).toFixed(1);
          const cachedTime = new Date(menu.cached_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          setDbStats({ menuSize: `${kb} KB`, lastCached: cachedTime });
        }
      }
    } catch (error) {
      console.error('Error refreshing offline status details:', error);
    }
  };

  // Connection monitoring & queue sync hook
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleOnline = () => {
      setConnectionState('reconnecting');
      setIsBannerDismissed(false); // Make sure reconnection banner is visible

      offlineQueue.syncAllOrders().then((result) => {
        setConnectionState('online');
        if (result.synced > 0) {
          toast.success(`${result.synced} orders synced successfully!`);
        }
        if (onSyncComplete) {
          onSyncComplete();
        }
        refreshPendingOrders();
      }).catch((err) => {
        console.error('Failed auto syncing orders on reconnect:', err);
        setConnectionState('online');
      });
    };

    const handleOffline = () => {
      setConnectionState('offline');
      setIsBannerDismissed(false); // Show offline banner immediately
      refreshPendingOrders();
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial check
    const isOnlineNow = navigator.onLine;
    setConnectionState(isOnlineNow ? 'online' : 'offline');
    refreshPendingOrders();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [onSyncComplete]);

  // Subscribe to offline queue events
  useEffect(() => {
    const onSyncStart = () => {
      setConnectionState('syncing');
    };
    
    const onSyncCompleteEvent = () => {
      setConnectionState(navigator.onLine ? 'online' : 'offline');
      refreshPendingOrders();
    };

    const onOrderSuccess = (localId: string) => {
      toast.success(`Order #${localId.substring(0, 5).toUpperCase()} has been synced!`);
      refreshPendingOrders();
    };

    const onOrderFailed = (localId: string, err: any) => {
      toast.error(`Sync failed for Order #${localId.substring(0, 5).toUpperCase()}: ${err.message || 'Server error'}`);
      refreshPendingOrders();
    };

    offlineQueue.on('sync:start', onSyncStart);
    offlineQueue.on('sync:complete', onSyncCompleteEvent);
    offlineQueue.on('sync:order_success', onOrderSuccess);
    offlineQueue.on('sync:order_failed', onOrderFailed);

    return () => {
      offlineQueue.off('sync:start', onSyncStart);
      offlineQueue.off('sync:complete', onSyncCompleteEvent);
      offlineQueue.off('sync:order_success', onOrderSuccess);
      offlineQueue.off('sync:order_failed', onOrderFailed);
    };
  }, []);

  const handleManualSync = async () => {
    if (connectionState === 'syncing' || !navigator.onLine) return;
    
    setConnectionState('syncing');
    try {
      const result = await offlineQueue.syncAllOrders();
      if (result.synced > 0) {
        toast.success(`Synced ${result.synced} pending orders!`);
      } else if (result.failed > 0) {
        toast.error(`Failed to sync ${result.failed} orders.`);
      } else {
        toast.info('All orders are up to date.');
      }
    } catch (err) {
      toast.error('Manual order synchronization failed.');
    } finally {
      setConnectionState(navigator.onLine ? 'online' : 'offline');
      refreshPendingOrders();
    }
  };

  const handleCancelOrder = async (localId: string) => {
    const success = await offlineQueue.cancelOrder(localId);
    if (success) {
      toast.success('Order cancelled successfully.');
      refreshPendingOrders();
    } else {
      toast.error('Failed to cancel order.');
    }
  };

  const handleClearCache = async () => {
    try {
      await db.clearExpiredData();
      toast.success('Menu cache cleared.');
      refreshPendingOrders();
    } catch (err) {
      toast.error('Failed to clear cache.');
    }
  };

  // If online with no pending orders, we don't display anything (hidden state)
  if (connectionState === 'online' && pendingOrders.length === 0) {
    return null;
  }

  // If dismissed temporarily during this offline event, we hide the banner
  if (isBannerDismissed && connectionState === 'offline') {
    return null;
  }

  // Define visual themes based on states
  const theme = {
    offline: {
      bg: 'bg-red-50/95 border-red-200 text-red-900',
      icon: <WifiOff className="h-5 w-5 text-red-600 animate-pulse" />,
      title: 'OFFLINE',
      message: 'You are offline. Menu is still available. Orders will be saved.',
    },
    reconnecting: {
      bg: 'bg-amber-50/95 border-amber-200 text-amber-900',
      icon: <Wifi className="h-5 w-5 text-amber-600 animate-bounce" />,
      title: 'RECONNECTING',
      message: 'Reconnecting... Syncing your orders.',
    },
    syncing: {
      bg: 'bg-blue-50/95 border-blue-200 text-blue-900',
      icon: <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />,
      title: 'SYNCING',
      message: `Syncing ${pendingOrders.length} pending orders...`,
    }
  }[connectionState === 'online' && pendingOrders.length > 0 ? 'reconnecting' : connectionState === 'online' ? 'online' as any : connectionState] || {
    bg: 'bg-slate-50 border-slate-200 text-slate-900',
    icon: <AlertCircle className="h-5 w-5 text-slate-600" />,
    title: 'OFFLINE',
    message: 'Reviewing connectivity...',
  };

  return (
    <>
      {/* Sticky Banner Top Section */}
      <AnimatePresence>
        {(!isBannerDismissed || pendingOrders.length > 0) && (
          <motion.div
            initial={{ y: -60, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -60, opacity: 0 }}
            className="fixed top-0 left-0 right-0 z-50 p-2 md:p-3"
          >
            <div className={`mx-auto max-w-3xl overflow-hidden rounded-2xl border ${theme.bg} p-4 shadow-[0_10px_30px_rgba(0,0,0,0.08)] backdrop-blur-md transition-all duration-300`}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 shrink-0">
                    {theme.icon}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-black uppercase tracking-wider">
                        {theme.title}
                      </span>
                      {pendingOrders.length > 0 && (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-black text-red-600">
                          {pendingOrders.length} pending
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 text-xs font-semibold leading-relaxed">
                      {connectionState === 'syncing' 
                        ? `Syncing ${totalOrdersCount - pendingOrders.length + 1} of ${totalOrdersCount} orders...`
                        : theme.message
                      }
                    </p>
                  </div>
                </div>

                {/* Banner Actions */}
                <div className="flex items-center justify-between gap-3 sm:justify-end shrink-0">
                  <div className="flex items-center gap-2">
                    {pendingOrders.length > 0 && (
                      <button
                        onClick={() => setIsModalOpen(true)}
                        className="rounded-xl bg-white px-3.5 py-2 text-[10px] font-black uppercase tracking-wider text-slate-800 shadow-sm border border-slate-200/50 hover:bg-slate-50 active:scale-98 transition-all cursor-pointer"
                      >
                        View Saved Orders
                      </button>
                    )}
                    
                    {connectionState === 'offline' ? (
                      <button
                        onClick={handleManualSync}
                        disabled={!navigator.onLine}
                        className={`rounded-xl px-3.5 py-2 text-[10px] font-black uppercase tracking-wider text-white shadow-sm active:scale-98 transition-all ${
                          navigator.onLine 
                            ? 'bg-slate-900 hover:bg-slate-800 cursor-pointer' 
                            : 'bg-slate-300 cursor-not-allowed'
                        }`}
                      >
                        Retry
                      </button>
                    ) : (
                      connectionState === 'syncing' && (
                        <button
                          onClick={() => setConnectionState(navigator.onLine ? 'online' : 'offline')}
                          className="rounded-xl bg-red-600 px-3.5 py-2 text-[10px] font-black uppercase tracking-wider text-white shadow-sm hover:bg-red-700 active:scale-98 transition-all cursor-pointer"
                        >
                          Cancel
                        </button>
                      )
                    )}
                  </div>

                  <button
                    onClick={() => setIsBannerDismissed(true)}
                    className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors cursor-pointer"
                    aria-label="Dismiss connectivity notification"
                  >
                    <X className="h-4.5 w-4.5" />
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Pending Orders details modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-55 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsModalOpen(false)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
            />
            
            <motion.div
              initial={{ scale: 0.95, y: 30, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.95, y: 30, opacity: 0 }}
              className="relative w-full max-w-lg rounded-[2.5rem] bg-white p-6 shadow-2xl border border-slate-100 max-h-[85vh] flex flex-col"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <Database className="h-5 w-5 text-emerald-600" />
                  <h3 className="text-base font-black text-slate-900">
                    Offline Saved Orders
                  </h3>
                </div>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-full p-1 text-slate-400 hover:bg-slate-100 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Modal Body / Orders list */}
              <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
                {pendingOrders.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-xs font-semibold text-slate-400">No pending offline orders found.</p>
                  </div>
                ) : (
                  pendingOrders.map((order) => (
                    <div 
                      key={order.local_id} 
                      className="rounded-2xl border border-slate-100 bg-slate-50/50 p-4 flex flex-col gap-3 justify-between"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <span className="text-[10px] font-black uppercase text-slate-400 tracking-wider">
                            Local Ref ID
                          </span>
                          <h4 className="text-xs font-bold text-slate-800 mt-0.5">
                            #{order.local_id.substring(0, 10).toUpperCase()}
                          </h4>
                          <span className="text-[10px] font-semibold text-slate-400 mt-1 block">
                            Created: {new Date(order.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                        <span className={`rounded-full px-2.5 py-1 text-[9px] font-black uppercase tracking-wider ${
                          order.status === 'pending' ? 'bg-amber-50 border border-amber-200 text-amber-700' :
                          order.status === 'syncing' ? 'bg-blue-50 border border-blue-200 text-blue-700 animate-pulse' :
                          order.status === 'failed' ? 'bg-red-50 border border-red-200 text-red-700' :
                          'bg-emerald-50 border border-emerald-200 text-emerald-700'
                        }`}>
                          {order.status}
                        </span>
                      </div>

                      {/* Items details block */}
                      <div className="text-xs space-y-1.5 border-t border-slate-100/50 pt-2 bg-white/60 p-2.5 rounded-xl border border-dashed border-slate-200/50">
                        {order.items.map((item, idx) => (
                          <div key={idx} className="flex justify-between items-center text-[11px]">
                            <span className="text-slate-500 font-semibold">
                              <span className="font-bold text-slate-800">{item.quantity}x</span> {item.name}
                            </span>
                            <span className="font-bold text-slate-800">KES {item.price * item.quantity}</span>
                          </div>
                        ))}
                        <div className="flex justify-between items-center pt-1.5 border-t border-slate-100 font-black text-slate-900 text-xs">
                          <span>Total</span>
                          <span className="text-emerald-600">KES {order.total}</span>
                        </div>
                      </div>

                      {/* Item Actions */}
                      <div className="flex justify-end gap-2 pt-1">
                        <button
                          onClick={() => handleCancelOrder(order.local_id)}
                          className="flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50/50 px-3 py-1.5 text-[10px] font-black uppercase text-red-600 tracking-wider hover:bg-red-50 active:scale-95 transition-all"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Delete Order
                        </button>
                      </div>
                    </div>
                  ))
                )}

                {/* Storage & details section */}
                {showDetails && (
                  <div className="mt-6 border-t border-slate-100 pt-4 space-y-3">
                    <div className="flex items-center gap-2 text-xs font-black text-slate-800">
                      <Database className="h-4 w-4 text-slate-500" />
                      <span>OFFLINE STORAGE MONITOR</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] font-semibold bg-slate-50 p-3 rounded-2xl border border-slate-100">
                      <div>
                        <span className="text-slate-400">Cached Menu Size:</span>
                        <p className="text-slate-800 font-black mt-0.5">{dbStats.menuSize}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Last Menu Sync:</span>
                        <p className="text-slate-800 font-black mt-0.5">{dbStats.lastCached}</p>
                      </div>
                    </div>
                    <button
                      onClick={handleClearCache}
                      className="w-full rounded-xl border border-slate-200 bg-white py-2 text-[10px] font-black uppercase text-slate-600 tracking-wider hover:bg-slate-50 transition-colors"
                    >
                      Clear Cached Menu Data
                    </button>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="border-t border-slate-100 pt-4 flex gap-3">
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 rounded-2xl border border-slate-200 bg-white py-3.5 text-xs font-black uppercase tracking-wider text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  Close
                </button>
                {pendingOrders.length > 0 && navigator.onLine && (
                  <button
                    onClick={handleManualSync}
                    className="flex-1 rounded-2xl bg-slate-900 py-3.5 text-xs font-black uppercase tracking-wider text-white hover:bg-slate-800 transition-colors"
                  >
                    Sync All Now
                  </button>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}

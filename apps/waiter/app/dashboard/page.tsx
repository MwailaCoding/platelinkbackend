'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useWaiterRealtime } from '../../hooks/useWaiterRealtime';

const useAuthStore = () => ({
  user: { name: 'John Doe', restaurantId: 'rest-123', staffId: 'staff-456' },
  logout: () => console.log('Logging out...')
});

export default function WaiterDashboard() {
  const { user, logout } = useAuthStore();
  const assignedTables = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
  
  const {
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
  } = useWaiterRealtime(user?.restaurantId || null, user?.staffId || null, assignedTables);

  const [currentTime, setCurrentTime] = useState(new Date());
  const [isMuted, setIsMuted] = useState(false);
  const [selectedTable, setSelectedTable] = useState<number | null>(null);
  const audioContext = useRef<AudioContext | null>(null);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      if (Notification.permission === 'default') {
        Notification.requestPermission();
      }
    }
  }, []);

  const playSound = (type: 'new' | 'ready' | 'call') => {
    if (isMuted) return;
    
    if (!audioContext.current) {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) {
        audioContext.current = new AudioCtx();
      } else {
        return;
      }
    }
    
    const ctx = audioContext.current;
    if (ctx.state === 'suspended') {
      ctx.resume();
    }

    const osc = ctx.createOscillator();
    const gainNode = ctx.createGain();
    
    osc.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    if (type === 'new') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(523.25, ctx.currentTime);
      gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 1);
    } else if (type === 'ready') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(523.25, ctx.currentTime);
      osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.2);
      gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.4);
    } else if (type === 'call') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gainNode.gain.setValueAtTime(0.2, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.5);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 1.5);
    }
  };

  useEffect(() => {
    if (newOrders.length > 0) playSound('new');
  }, [newOrders]);

  useEffect(() => {
    if (readyOrders.length > 0) playSound('ready');
  }, [readyOrders]);

  useEffect(() => {
    if (waiterCalls.length > 0) playSound('call');
  }, [waiterCalls]);

  const getTableColor = (status?: string) => {
    switch (status) {
      case 'available': return 'bg-emerald-600';
      case 'occupied': return 'bg-yellow-400';
      case 'ordering': return 'bg-yellow-200';
      case 'ordered': return 'bg-blue-500';
      case 'ready': return 'bg-orange-600';
      case 'eating': return 'bg-purple-500';
      case 'bill_requested': return 'bg-red-600';
      default: return 'bg-emerald-600';
    }
  };

  const getRelativeTime = (dateString: string) => {
    const diff = Math.floor((new Date().getTime() - new Date(dateString).getTime()) / 60000);
    if (diff < 1) return 'Just now';
    return `${diff} min ago`;
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      <header className="bg-white shadow-sm px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Waiter Station</h1>
          <p className="text-sm text-gray-500">
            {user?.name} | Tables {assignedTables.join(', ')}
          </p>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className="text-sm font-medium text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div className="text-lg font-semibold text-gray-700 tabular-nums">
            {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
          <Link 
            href="/cashier"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-emerald-600 border border-emerald-200 rounded-lg hover:bg-emerald-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
            Cashier
          </Link>
          <button 
            onClick={() => setIsMuted(!isMuted)}
            className="p-2 rounded-full hover:bg-gray-100 transition-colors"
            title={isMuted ? "Unmute notifications" : "Mute notifications"}
          >
            {isMuted ? '🔇' : '🔊'}
          </button>
          <button 
            onClick={logout}
            className="px-4 py-2 text-sm font-medium text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
          >
            Logout
          </button>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          <section className="bg-white rounded-xl shadow-md p-6 border-t-4 border-emerald-600 flex flex-col h-[400px]">
            <div className="flex items-center justify-between mb-4 shrink-0">
              <h2 className="text-lg font-bold text-gray-800">New Orders</h2>
              <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-1 rounded-full">
                {newOrders.length}
              </span>
            </div>
            <div className="space-y-4 overflow-y-auto pr-2 flex-1">
              {newOrders.map(order => (
                <div key={order.id} className="border border-gray-100 rounded-lg p-4 bg-gray-50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="font-bold text-lg mb-1">Table {order.tableNumber}</div>
                    <ul className="text-sm space-y-1 mb-2">
                      {order.items.map((item, idx) => (
                        <li key={idx}>
                          {item.quantity}x {item.name}
                          {item.specialInstructions && (
                            <span className="text-red-500 italic ml-2">({item.specialInstructions})</span>
                          )}
                        </li>
                      ))}
                    </ul>
                    <div className="text-xs text-gray-500 font-medium">{getRelativeTime(order.createdAt)}</div>
                  </div>
                  <button 
                    onClick={() => acknowledgeOrder(order.id)}
                    className="px-4 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors w-full sm:w-auto shrink-0"
                  >
                    Acknowledge
                  </button>
                </div>
              ))}
              {newOrders.length === 0 && (
                <p className="text-gray-500 text-center py-8">No new orders</p>
              )}
            </div>
          </section>

          <section className="bg-white rounded-xl shadow-md p-6 border-t-4 border-orange-600 flex flex-col h-[400px]">
            <div className="flex items-center justify-between mb-4 shrink-0">
              <h2 className="text-lg font-bold text-gray-800">Ready for Pickup</h2>
              <span className="bg-orange-100 text-orange-800 text-xs font-bold px-3 py-1 rounded-full">
                {readyOrders.length}
              </span>
            </div>
            <div className="space-y-4 overflow-y-auto pr-2 flex-1">
              {readyOrders.map(order => (
                <div key={order.id} className="border border-gray-100 rounded-lg p-4 bg-orange-50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="font-bold text-lg text-orange-900 mb-1">Table {order.tableNumber}</div>
                    <ul className="text-sm text-orange-800 space-y-1 mb-2">
                      {order.items.map((item, idx) => (
                        <li key={idx}>{item.quantity}x {item.name}</li>
                      ))}
                    </ul>
                    <div className="text-xs text-orange-600 font-medium">
                      Ready {order.readySince ? getRelativeTime(order.readySince) : 'Just now'}
                    </div>
                  </div>
                  <button 
                    onClick={() => markPickedUp(order.id)}
                    className="px-4 py-2 bg-orange-600 text-white rounded-lg font-medium hover:bg-orange-700 transition-colors w-full sm:w-auto shrink-0 shadow-sm"
                  >
                    Picked Up
                  </button>
                </div>
              ))}
              {readyOrders.length === 0 && (
                <p className="text-gray-500 text-center py-8">No orders to pick up</p>
              )}
            </div>
          </section>

          <section className="bg-white rounded-xl shadow-md p-6 border-t-4 border-blue-500 flex flex-col h-[300px]">
            <div className="flex items-center justify-between mb-4 shrink-0">
              <h2 className="text-lg font-bold text-gray-800">Call Waiter Alerts</h2>
              <span className="bg-blue-100 text-blue-800 text-xs font-bold px-3 py-1 rounded-full">
                {waiterCalls.length}
              </span>
            </div>
            <div className="space-y-4 overflow-y-auto pr-2 flex-1">
              {waiterCalls.map(call => (
                <div key={call.id} className="border border-blue-100 rounded-lg p-4 bg-blue-50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="font-bold text-lg text-blue-900 mb-1">Table {call.tableNumber}</div>
                    <p className="text-sm text-blue-800 mb-2">{call.message}</p>
                    <div className="text-xs text-blue-600 font-medium">
                      {getRelativeTime(call.createdAt)}
                    </div>
                  </div>
                  <button 
                    onClick={() => acknowledgeCall(call.id)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors w-full sm:w-auto shrink-0"
                  >
                    Acknowledge
                  </button>
                </div>
              ))}
              {waiterCalls.length === 0 && (
                <p className="text-gray-500 text-center py-8">No active calls</p>
              )}
            </div>
          </section>

          <section className="bg-white rounded-xl shadow-md p-6 border-t-4 border-purple-500 flex flex-col h-[300px]">
            <div className="flex items-center justify-between mb-4 shrink-0">
              <h2 className="text-lg font-bold text-gray-800">Bill Requests</h2>
              <span className="bg-purple-100 text-purple-800 text-xs font-bold px-3 py-1 rounded-full">
                {billRequests.length}
              </span>
            </div>
            <div className="space-y-4 overflow-y-auto pr-2 flex-1">
              {billRequests.map(req => (
                <div key={req.id} className="border border-purple-100 rounded-lg p-4 bg-purple-50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="font-bold text-lg text-purple-900 mb-1">Table {req.tableNumber}</div>
                    <div className="text-xl font-bold text-purple-700 mb-2">KES {req.total.toLocaleString()}</div>
                    <div className="text-xs text-purple-600 font-medium">
                      {getRelativeTime(req.createdAt)}
                    </div>
                  </div>
                  <button 
                    onClick={() => processBill(req.id)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors w-full sm:w-auto shrink-0 shadow-sm"
                  >
                    Process
                  </button>
                </div>
              ))}
              {billRequests.length === 0 && (
                <p className="text-gray-500 text-center py-8">No bill requests</p>
              )}
            </div>
          </section>
        </div>

        <section className="bg-white rounded-xl shadow-md p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
            <h2 className="text-lg font-bold text-gray-800">Table Status</h2>
            <div className="flex flex-wrap gap-4 text-xs font-medium text-gray-600">
              <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-emerald-600 shadow-sm"></div> Available</span>
              <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-yellow-400 shadow-sm"></div> Occupied</span>
              <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-blue-500 shadow-sm"></div> Order Placed</span>
              <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-orange-600 shadow-sm"></div> Ready</span>
              <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-purple-500 shadow-sm"></div> Eating</span>
              <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-red-600 shadow-sm"></div> Bill Req.</span>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {assignedTables.map(tableNum => {
              const status = tableStatuses[tableNum] || 'available';
              return (
                <button
                  key={tableNum}
                  onClick={() => setSelectedTable(tableNum)}
                  className={`relative p-4 h-24 rounded-xl border-2 transition-all hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400 ${
                    status === 'available' ? 'border-emerald-200 bg-emerald-50 hover:border-emerald-300' :
                    status === 'occupied' ? 'border-yellow-200 bg-yellow-50 hover:border-yellow-300' :
                    status === 'ordering' || status === 'ordered' ? 'border-blue-200 bg-blue-50 hover:border-blue-300' :
                    status === 'ready' ? 'border-orange-200 bg-orange-50 hover:border-orange-300' :
                    status === 'eating' ? 'border-purple-200 bg-purple-50 hover:border-purple-300' :
                    status === 'bill_requested' ? 'border-red-200 bg-red-50 hover:border-red-300' :
                    'border-gray-200 bg-gray-50 hover:border-gray-300'
                  }`}
                >
                  <div className="absolute top-3 right-3">
                    <div className={`w-3.5 h-3.5 rounded-full shadow-sm ${getTableColor(status)}`} />
                  </div>
                  <div className="text-left h-full flex flex-col justify-end">
                    <div className="text-2xl font-bold text-gray-900 mb-0.5">T{tableNum}</div>
                    <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider truncate">
                      {status.replace('_', ' ')}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </section>
      </main>

      {selectedTable && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSelectedTable(null)}>
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md transform transition-all" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-900">Table {selectedTable} Details</h3>
              <button 
                onClick={() => setSelectedTable(null)} 
                className="text-gray-400 hover:text-gray-600 transition-colors rounded-full p-1"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 bg-gray-50 rounded-xl text-center border border-gray-100">
              <div className="text-sm text-gray-500 font-medium uppercase tracking-wider mb-1">Current Status</div>
              <div className="text-lg font-bold text-gray-900 capitalize flex items-center justify-center gap-2">
                <div className={`w-3 h-3 rounded-full ${getTableColor(tableStatuses[selectedTable])}`} />
                {(tableStatuses[selectedTable] || 'available').replace('_', ' ')}
              </div>
            </div>
            <div className="mt-6 flex justify-end">
              <button 
                onClick={() => setSelectedTable(null)}
                className="px-5 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

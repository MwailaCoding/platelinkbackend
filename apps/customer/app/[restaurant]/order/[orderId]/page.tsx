'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { useOrderTracking } from '../../../../../hooks/useOrderTracking';
import DigitalReceipt from '../../../../components/Payment/DigitalReceipt';

// Note: Using a local component as requested when an exact path for shared UI isn't given
const ConnectionStatus = ({ state }: { state: string }) => {
  const color = state === 'connected' ? 'bg-emerald-500' : state === 'connecting' ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="flex items-center space-x-2 text-sm text-gray-600">
      <div className={`w-2 h-2 rounded-full ${color}`} />
      <span>{state.charAt(0).toUpperCase() + state.slice(1)}</span>
    </div>
  );
};

export default function OrderTrackingPage() {
  const params = useParams();
  const orderId = params?.orderId as string;
  // Fallback for session token
  const [sessionToken] = useState<string | null>('demo-session-token'); 
  const tableNumber = '12';
  const orderNumber = orderId ? orderId.slice(0, 6).toUpperCase() : 'UNKNOWN';

  const {
    orderStatus,
    items,
    estimatedTime,
    connectionState,
    callWaiter,
    requestBill
  } = useOrderTracking(sessionToken, orderId);

  const [isWaiterModalOpen, setIsWaiterModalOpen] = useState(false);
  const [waiterMessage, setWaiterMessage] = useState('');
  const [isReceiptModalOpen, setIsReceiptModalOpen] = useState(false);

  const handleCallWaiter = () => {
    callWaiter(waiterMessage);
    setIsWaiterModalOpen(false);
    setWaiterMessage('');
  };

  const getStageIndex = (status: string | null) => {
    if (!status) return -1;
    switch (status) {
      case 'received': return 0;
      case 'preparing': return 1;
      case 'ready': return 2;
      case 'served':
      case 'completed': return 3;
      default: return -1;
    }
  };

  const currentStage = getStageIndex(orderStatus);

  if (connectionState === 'connecting' && !orderStatus) {
    return (
      <div className="max-w-[428px] mx-auto min-h-screen bg-white p-6 flex flex-col justify-center items-center">
        <div className="animate-pulse space-y-4 w-full">
          <div className="h-8 bg-gray-200 rounded w-1/2 mx-auto"></div>
          <div className="h-4 bg-gray-200 rounded w-1/3 mx-auto"></div>
          <div className="h-32 bg-gray-200 rounded w-full mt-8"></div>
        </div>
      </div>
    );
  }

  if (connectionState === 'disconnected' && !orderStatus) {
    return (
      <div className="max-w-[428px] mx-auto min-h-screen bg-white p-6 flex flex-col justify-center items-center text-center">
        <div className="text-red-500 mb-4">
          <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-gray-800 mb-2">Connection Failed</h2>
        <p className="text-gray-600">Unable to connect to order tracking service. Please check your internet connection.</p>
      </div>
    );
  }

  return (
    <div className="max-w-[428px] mx-auto min-h-screen bg-white flex flex-col relative pb-24">
      <header className="p-6 pb-4 border-b border-gray-100 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">#{orderNumber}</h1>
          <div className="text-sm font-medium text-emerald-600 mt-1">TABLE {tableNumber}</div>
        </div>
        <div className="flex flex-col items-end gap-3">
          <ConnectionStatus state={connectionState} />
          {orderStatus === 'completed' && (
            <button 
              onClick={() => setIsReceiptModalOpen(true)}
              className="text-gray-500 hover:text-emerald-600 transition-colors p-1"
              aria-label="View Receipt"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </button>
          )}
        </div>
      </header>

      {orderStatus === 'completed' && (
        <div className="bg-emerald-50 border-l-4 border-emerald-500 p-4 mx-6 mt-6 rounded-r-md flex justify-between items-center shadow-sm">
          <div>
            <p className="text-emerald-800 font-bold">Payment Successful!</p>
            <p className="text-emerald-600 text-sm">Receipt available</p>
          </div>
          <button 
            onClick={() => setIsReceiptModalOpen(true)}
            className="px-3 py-1.5 border-2 border-emerald-500 text-emerald-700 text-sm font-bold rounded-lg hover:bg-emerald-100 transition-colors"
          >
            View Receipt
          </button>
        </div>
      )}

      {(orderStatus === 'preparing' || orderStatus === 'received') && estimatedTime !== null && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mx-6 mt-6 rounded-r-md">
          <p className="text-yellow-800 text-sm font-medium">
            Your order will be ready in approximately {estimatedTime} minutes
          </p>
        </div>
      )}

      <div className="px-6 py-8">
        <div className="flex justify-between items-center relative">
          <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-full h-1 bg-gray-200 -z-10 rounded"></div>
          <div 
            className="absolute left-0 top-1/2 transform -translate-y-1/2 h-1 bg-emerald-600 -z-10 rounded transition-all duration-500 ease-in-out"
            style={{ width: `${Math.max(0, currentStage * 33.33)}%` }}
          ></div>
          
          {[
            { label: 'Received', icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /> },
            { label: 'Preparing', icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /> },
            { label: 'Ready', icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /> },
            { label: 'Served', icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /> }
          ].map((stage, index) => {
            const isActive = currentStage >= index;
            const isCurrent = currentStage === index;
            
            return (
              <div key={stage.label} className="flex flex-col items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors duration-300 ${
                  isActive ? 'bg-emerald-600 border-emerald-600 text-white' : 'bg-white border-gray-300 text-gray-300'
                } ${isCurrent ? 'ring-4 ring-emerald-100 animate-pulse' : ''}`}>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    {stage.icon}
                  </svg>
                </div>
                <div className={`text-[10px] font-bold mt-2 uppercase tracking-wide ${isActive ? 'text-emerald-800' : 'text-gray-400'}`}>
                  {stage.label}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex-1 px-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Your Items</h2>
        <div className="space-y-4">
          {items.map(item => {
            const statusConfig = {
              received: { color: 'bg-gray-100 text-gray-700', label: 'Received' },
              preparing: { color: 'bg-yellow-100 text-yellow-800', label: 'Preparing' },
              ready: { color: 'bg-green-100 text-green-800', label: 'Ready' },
              served: { color: 'bg-emerald-100 text-emerald-800', label: 'Served' }
            }[item.status];

            return (
              <div key={item.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-100">
                <div className="flex flex-col">
                  <span className="font-semibold text-gray-900">{item.name}</span>
                  {item.status === 'preparing' && item.estimatedTime && (
                    <span className="text-xs text-gray-500 mt-1">Est. {item.estimatedTime} min</span>
                  )}
                </div>
                <div className="flex items-center space-x-3">
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${statusConfig.color}`}>
                    {statusConfig.label}
                  </span>
                  {(item.status === 'ready' || item.status === 'served') && (
                    <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 max-w-[428px] mx-auto bg-white border-t border-gray-100 p-4 px-6 flex gap-4">
        <button 
          onClick={requestBill}
          className="flex-1 py-3 px-4 rounded-xl font-bold text-gray-700 bg-white border-2 border-gray-200 active:bg-gray-50 transition-colors"
        >
          Request Bill
        </button>
        <button 
          onClick={() => setIsWaiterModalOpen(true)}
          className="flex-1 py-3 px-4 rounded-xl font-bold text-white bg-orange-600 active:bg-orange-700 transition-colors shadow-sm shadow-orange-200"
        >
          Call Waiter
        </button>
      </div>

      {isWaiterModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl w-full max-w-sm p-6 shadow-xl">
            <h3 className="text-xl font-bold text-gray-900 mb-2">Call Waiter</h3>
            <p className="text-sm text-gray-500 mb-4">How can we help you?</p>
            <textarea
              value={waiterMessage}
              onChange={(e) => setWaiterMessage(e.target.value)}
              placeholder="Optional message..."
              className="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent min-h-[100px]"
            />
            <div className="flex gap-3">
              <button 
                onClick={() => setIsWaiterModalOpen(false)}
                className="flex-1 py-2.5 px-4 rounded-xl font-bold text-gray-600 bg-gray-100 active:bg-gray-200"
              >
                Cancel
              </button>
              <button 
                onClick={handleCallWaiter}
                className="flex-1 py-2.5 px-4 rounded-xl font-bold text-white bg-orange-600 active:bg-orange-700"
              >
                Call
              </button>
            </div>
          </div>
        </div>
      )}

      {isReceiptModalOpen && (
        <DigitalReceipt 
          orderId={orderId} 
          onClose={() => setIsReceiptModalOpen(false)} 
        />
      )}
    </div>
  );
}

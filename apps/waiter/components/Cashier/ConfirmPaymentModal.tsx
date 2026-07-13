'use client';

import React, { useState } from 'react';

interface ConfirmPaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (amount: number) => Promise<void>;
  order: {
    id: string;
    orderNumber: string;
    tableNumber: number;
    items: Array<{ name: string; quantity: number; price: number }>;
    total: number;
  };
}

export default function ConfirmPaymentModal({ isOpen, onClose, onConfirm, order }: ConfirmPaymentModalProps) {
  const [receivedAmount, setReceivedAmount] = useState<string>(order?.total?.toString() || '0');
  const [isProcessing, setIsProcessing] = useState(false);

  // Update receivedAmount when order changes
  React.useEffect(() => {
    if (order?.total) {
      setReceivedAmount(order.total.toString());
    }
  }, [order?.total]);

  if (!isOpen || !order) return null;

  const handleConfirm = async () => {
    const amount = parseFloat(receivedAmount);
    if (isNaN(amount) || amount <= 0) return;
    
    setIsProcessing(true);
    try {
      await onConfirm(amount);
    } finally {
      setIsProcessing(false);
    }
  };

  const amountReceived = parseFloat(receivedAmount) || 0;
  const change = amountReceived > order.total ? amountReceived - order.total : 0;
  const remaining = amountReceived < order.total ? order.total - amountReceived : 0;
  const isPartial = amountReceived > 0 && amountReceived < order.total;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md transform transition-all flex flex-col max-h-[90vh]" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center p-6 border-b border-gray-100 shrink-0">
          <h2 className="text-xl font-bold text-gray-900">Confirm Cash Payment</h2>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors rounded-full p-1"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          <div className="flex justify-between items-center mb-6 bg-gray-50 p-4 rounded-lg border border-gray-100">
            <div>
              <div className="text-sm text-gray-500 font-medium">Order</div>
              <div className="font-bold text-gray-900">{order.orderNumber}</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500 font-medium">Table</div>
              <div className="font-bold text-gray-900 text-xl">{order.tableNumber}</div>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-3">Order Items</h3>
            <div className="space-y-2 border border-gray-100 rounded-lg p-3 bg-gray-50 max-h-40 overflow-y-auto">
              {order.items.map((item, idx) => (
                <div key={idx} className="flex justify-between text-sm">
                  <span className="text-gray-700">{item.quantity}x {item.name}</span>
                  <span className="font-medium text-gray-900">KES {(item.price * item.quantity).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Amount Received (KES)</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={receivedAmount}
                onChange={(e) => setReceivedAmount(e.target.value)}
                className="w-full text-lg p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 font-medium text-gray-900"
                placeholder="0.00"
              />
            </div>

            {isPartial && (
              <div className="bg-orange-50 border border-orange-200 text-orange-800 px-4 py-3 rounded-lg text-sm flex items-start gap-2">
                <svg className="w-5 h-5 text-orange-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>This is a partial payment. The order will remain open for the remaining balance.</span>
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-gray-600 font-medium">Total Amount:</span>
                <span className="text-xl font-bold text-gray-900">KES {order.total.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-500">Amount Received:</span>
                <span className="font-medium text-gray-700">KES {amountReceived.toLocaleString()}</span>
              </div>
              
              <div className="h-px bg-gray-200 my-2"></div>
              
              {change > 0 && (
                <div className="flex justify-between items-center text-emerald-600">
                  <span className="font-medium">Change to Return:</span>
                  <span className="text-lg font-bold">KES {change.toLocaleString()}</span>
                </div>
              )}
              {remaining > 0 && (
                <div className="flex justify-between items-center text-orange-600">
                  <span className="font-medium">Remaining Balance:</span>
                  <span className="text-lg font-bold">KES {remaining.toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-gray-100 shrink-0 flex gap-3">
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors focus:ring-2 focus:ring-offset-2 focus:ring-gray-200"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={isProcessing || isNaN(amountReceived) || amountReceived <= 0}
            className="flex-1 px-4 py-3 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isProcessing ? (
              <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              'Confirm Payment'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

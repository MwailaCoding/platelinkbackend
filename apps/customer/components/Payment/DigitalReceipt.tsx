// apps/customer/components/Payment/DigitalReceipt.tsx
import React, { useState } from 'react';

interface DigitalReceiptProps {
  orderId: string;
  onClose: () => void;
  onShare?: () => void;
}

export default function DigitalReceipt({ orderId, onClose, onShare }: DigitalReceiptProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // In a real app we would fetch receipt data, but this is a mock implementation
  // since we don't have the backend API fully integrated yet
  const receiptData = {
    restaurantName: 'PlateLink Demo Restaurant',
    orderNumber: orderId ? orderId.slice(0, 6).toUpperCase() : 'UNKNOWN',
    date: new Date().toLocaleString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }),
    tableNumber: '12',
    serverName: 'John D.',
    items: [
      { name: 'Burger', qty: 2, price: 15.00, total: 30.00 },
      { name: 'Fries', qty: 1, price: 5.00, total: 5.00 }
    ],
    subtotal: 35.00,
    tax: 5.60,
    total: 40.60,
    paymentMethod: 'M-PESA',
    transactionId: 'NK29XJ3P',
    receiptUrl: typeof window !== 'undefined' ? `${window.location.origin}/receipt/${orderId}` : ''
  };

  const handleShareSMS = () => {
    const text = `PlateLink Receipt: ${receiptData.restaurantName} Order #${receiptData.orderNumber} KES ${receiptData.total.toFixed(2)}. View full receipt: ${receiptData.receiptUrl}`;
    window.open(`sms:?body=${encodeURIComponent(text)}`);
    if (onShare) onShare();
  };

  const handleShareEmail = () => {
    const subject = `Receipt from ${receiptData.restaurantName}`;
    const body = `Here is your receipt for Order #${receiptData.orderNumber}. View full receipt: ${receiptData.receiptUrl}`;
    window.open(`mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`);
    if (onShare) onShare();
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(receiptData.receiptUrl);
      alert('Link copied to clipboard!');
      if (onShare) onShare();
    } catch (err) {
      console.error('Failed to copy', err);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPDF = () => {
    // Basic implementation that just triggers print dialog
    // In production we would use html2canvas + jsPDF
    window.print();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex justify-center items-center p-4 z-50">
      <div className="bg-white rounded-xl w-full max-w-md max-h-[90vh] overflow-y-auto relative flex flex-col">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 no-print"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="p-8 print:p-0 flex-1" id="receipt-content">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">{receiptData.restaurantName}</h2>
            <p className="text-gray-500 font-medium tracking-wide">TAX RECEIPT</p>
          </div>

          <div className="flex justify-between items-end mb-6 text-sm text-gray-600 border-b border-gray-200 pb-4">
            <div>
              <p className="font-mono">Order #{receiptData.orderNumber}</p>
              <p>{receiptData.date}</p>
            </div>
            <div className="text-right">
              <p>Table {receiptData.tableNumber}</p>
              <p>Server: {receiptData.serverName}</p>
            </div>
          </div>

          <table className="w-full mb-6">
            <thead>
              <tr className="text-left text-sm text-gray-500 border-b border-gray-200">
                <th className="pb-2 font-medium">Item</th>
                <th className="pb-2 font-medium text-center">Qty</th>
                <th className="pb-2 font-medium text-right">Price</th>
                <th className="pb-2 font-medium text-right">Total</th>
              </tr>
            </thead>
            <tbody className="text-sm text-gray-800">
              {receiptData.items.map((item, index) => (
                <tr key={index} className="border-b border-gray-100 last:border-0">
                  <td className="py-2">{item.name}</td>
                  <td className="py-2 text-center">{item.qty}</td>
                  <td className="py-2 text-right">{item.price.toFixed(2)}</td>
                  <td className="py-2 text-right">{item.total.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="space-y-2 text-sm text-gray-600 border-t border-gray-200 pt-4">
            <div className="flex justify-between">
              <span>Subtotal</span>
              <span>KES {receiptData.subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>VAT 16%</span>
              <span>KES {receiptData.tax.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-lg font-bold text-emerald-600 pt-2 border-t border-gray-200">
              <span>Total</span>
              <span>KES {receiptData.total.toFixed(2)}</span>
            </div>
          </div>

          <div className="mt-8 bg-gray-50 p-4 rounded-lg text-sm print:bg-white print:border print:border-gray-200">
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-600">Payment Method</span>
              <span className="font-medium bg-gray-200 px-2 py-1 rounded text-xs">{receiptData.paymentMethod}</span>
            </div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-600">Transaction ID</span>
              <span className="font-mono text-gray-900">{receiptData.transactionId}</span>
            </div>
            <div className="flex justify-between items-center font-bold text-gray-900">
              <span>Amount Paid</span>
              <span>KES {receiptData.total.toFixed(2)}</span>
            </div>
          </div>

          <div className="text-center mt-8 text-gray-500 text-sm">
            <p className="font-medium text-gray-700 mb-1">Thank you for dining with us!</p>
            <p>Please keep this receipt for your records</p>
            <p className="mt-4">Questions? Call +254 700 000 000</p>
          </div>
        </div>

        <div className="p-4 border-t border-gray-200 bg-gray-50 no-print">
          <div className="grid grid-cols-2 gap-3 mb-3">
            <button 
              onClick={handleShareSMS}
              className="py-2 px-4 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Share via SMS
            </button>
            <button 
              onClick={handleShareEmail}
              className="py-2 px-4 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Share via Email
            </button>
          </div>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <button 
              onClick={handleCopyLink}
              className="py-2 px-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors flex flex-col items-center justify-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              Copy Link
            </button>
            <button 
              onClick={handleDownloadPDF}
              className="py-2 px-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors flex flex-col items-center justify-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download PDF
            </button>
            <button 
              onClick={handlePrint}
              className="py-2 px-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors flex flex-col items-center justify-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              Print
            </button>
          </div>
          <button 
            onClick={onClose}
            className="w-full py-2.5 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

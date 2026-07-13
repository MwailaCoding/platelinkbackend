// apps/customer/app/receipt/[id]/page.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

export default function PublicReceiptPage() {
  const params = useParams();
  const receiptId = params?.id as string;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock fetching receipt data based on ID
  // In production, this would be fetched from GET /api/orders/{receiptId}/receipt
  const receiptData = {
    restaurantName: 'PlateLink Demo Restaurant',
    orderNumber: receiptId ? receiptId.slice(0, 6).toUpperCase() : 'UNKNOWN',
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
  };

  useEffect(() => {
    // Simulate API fetch delay
    const timer = setTimeout(() => {
      setLoading(false);
      // To test error states you could conditionally setError here based on ID
    }, 800);
    return () => clearTimeout(timer);
  }, [receiptId]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center p-4">
        <div className="bg-white p-8 rounded-xl max-w-md w-full text-center shadow-sm">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Receipt Not Found</h2>
          <p className="text-gray-600 mb-6">{error === 'expired' ? 'This receipt has expired. Please contact the restaurant.' : 'We could not find a receipt with that link.'}</p>
          <button 
            onClick={() => window.location.reload()}
            className="w-full py-3 bg-emerald-600 text-white rounded-lg font-bold hover:bg-emerald-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <head>
        <title>Receipt for Order #{receiptData.orderNumber} - PlateLink Africa</title>
        <meta name="robots" content="noindex, nofollow" />
      </head>
      
      <div className="min-h-screen bg-gray-50 print:bg-white py-10 px-4">
        <div className="max-w-2xl mx-auto">
          {/* Action bar for web viewing - hidden when printing */}
          <div className="mb-6 flex justify-end no-print">
            <button 
              onClick={handlePrint}
              className="flex items-center gap-2 py-2 px-4 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors shadow-sm"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              Print Receipt
            </button>
          </div>

          <div className="bg-white rounded-xl shadow-sm print:shadow-none p-8 md:p-12 border border-gray-100 print:border-0" id="receipt-content">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-1">{receiptData.restaurantName}</h1>
              <p className="text-gray-500 font-medium tracking-widest text-sm">TAX RECEIPT</p>
            </div>

            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-8 text-sm text-gray-600 border-b border-gray-200 pb-6 gap-4 sm:gap-0">
              <div>
                <p className="font-mono text-base font-medium text-gray-900 mb-1">Order #{receiptData.orderNumber}</p>
                <p>{receiptData.date}</p>
              </div>
              <div className="sm:text-right">
                <p className="mb-1">Table {receiptData.tableNumber}</p>
                <p>Server: {receiptData.serverName}</p>
              </div>
            </div>

            <table className="w-full mb-8">
              <thead>
                <tr className="text-left text-sm text-gray-500 border-b border-gray-200">
                  <th className="pb-3 font-medium">Item</th>
                  <th className="pb-3 font-medium text-center">Qty</th>
                  <th className="pb-3 font-medium text-right">Price</th>
                  <th className="pb-3 font-medium text-right">Total</th>
                </tr>
              </thead>
              <tbody className="text-base text-gray-800">
                {receiptData.items.map((item, index) => (
                  <tr key={index} className="border-b border-gray-100 last:border-0">
                    <td className="py-4">{item.name}</td>
                    <td className="py-4 text-center">{item.qty}</td>
                    <td className="py-4 text-right">{item.price.toFixed(2)}</td>
                    <td className="py-4 text-right">{item.total.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="space-y-3 text-base text-gray-600 border-t border-gray-200 pt-6">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>KES {receiptData.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>VAT 16%</span>
                <span>KES {receiptData.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xl font-bold text-emerald-600 pt-4 border-t border-gray-200 print:text-black">
                <span>Total</span>
                <span>KES {receiptData.total.toFixed(2)}</span>
              </div>
            </div>

            <div className="mt-10 bg-gray-50 p-6 rounded-lg text-base print:bg-white print:border print:border-gray-200 print:p-0 print:mt-6 print:rounded-none">
              <div className="flex justify-between items-center mb-3">
                <span className="text-gray-600">Payment Method</span>
                <span className="font-medium bg-gray-200 px-3 py-1 rounded-md text-sm print:bg-transparent print:p-0">{receiptData.paymentMethod}</span>
              </div>
              <div className="flex justify-between items-center mb-3">
                <span className="text-gray-600">Transaction ID</span>
                <span className="font-mono text-gray-900">{receiptData.transactionId}</span>
              </div>
              <div className="flex justify-between items-center font-bold text-gray-900 mt-4 pt-4 border-t border-gray-200 print:pt-2">
                <span>Amount Paid</span>
                <span>KES {receiptData.total.toFixed(2)}</span>
              </div>
            </div>

            <div className="text-center mt-12 text-gray-500 text-sm">
              <p className="font-medium text-gray-800 mb-2 text-base">Thank you for dining with us!</p>
              <p>Please keep this receipt for your records</p>
              <p className="mt-6">Questions? Call +254 700 000 000</p>
            </div>
          </div>
        </div>
        
        <style dangerouslySetInnerHTML={{__html: `
          @media print {
            body {
              background-color: white !important;
            }
            .no-print {
              display: none !important;
            }
            * {
              color: black !important;
            }
          }
        `}} />
      </div>
    </>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import ConfirmPaymentModal from '../../components/Cashier/ConfirmPaymentModal';

const useAuthStore = () => ({
  user: { name: 'Jane Cashier', restaurantId: 'rest-123', staffId: 'staff-789', role: 'cashier' },
  logout: () => console.log('Logging out...')
});

// Mock hooks to simulate WebSocket and data fetching
const useCashierRealtime = (restaurantId: string | null) => {
  const [isConnected, setIsConnected] = useState(true);
  const [pendingPayments, setPendingPayments] = useState([
    {
      id: 'pay-1',
      orderId: 'ord-101',
      orderNumber: 'ORD-101',
      tableNumber: 4,
      items: [
        { name: 'Burger', quantity: 2, price: 800 },
        { name: 'Fries', quantity: 1, price: 300 }
      ],
      total: 1900,
      waitingSince: new Date(Date.now() - 1000 * 60 * 12).toISOString(), // 12 mins ago
    },
    {
      id: 'pay-2',
      orderId: 'ord-102',
      orderNumber: 'ORD-102',
      tableNumber: 7,
      items: [
        { name: 'Pizza', quantity: 1, price: 1200 },
        { name: 'Soda', quantity: 2, price: 150 }
      ],
      total: 1500,
      waitingSince: new Date(Date.now() - 1000 * 60 * 4).toISOString(), // 4 mins ago
    },
    {
      id: 'pay-3',
      orderId: 'ord-103',
      orderNumber: 'ORD-103',
      tableNumber: 2,
      items: [
        { name: 'Steak', quantity: 1, price: 2500 }
      ],
      total: 2500,
      waitingSince: new Date(Date.now() - 1000 * 60 * 25).toISOString(), // 25 mins ago
    }
  ]);

  const confirmPayment = async (orderId: string, amount: number, staffId: string) => {
    // API Call simulation
    await new Promise(resolve => setTimeout(resolve, 1000));
    setPendingPayments(prev => prev.filter(p => p.orderId !== orderId));
  };

  return { isConnected, pendingPayments, confirmPayment };
};

export default function CashierDashboard() {
  const { user, logout } = useAuthStore();
  const { isConnected, pendingPayments, confirmPayment } = useCashierRealtime(user?.restaurantId || null);
  
  const [currentTime, setCurrentTime] = useState(new Date());
  const [selectedPayment, setSelectedPayment] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});
  const [smsModalOpen, setSmsModalOpen] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState('');

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Stats
  const totalCashToday = 45000; // Mocked
  const pendingCount = pendingPayments.length;
  const servedCount = 42; // Mocked

  const getWaitStatus = (dateString: string) => {
    const diff = Math.floor((new Date().getTime() - new Date(dateString).getTime()) / 60000);
    if (diff < 5) return { label: `${diff}m`, color: 'bg-emerald-100 text-emerald-800', border: 'border-l-emerald-500' };
    if (diff < 15) return { label: `${diff}m`, color: 'bg-yellow-100 text-yellow-800', border: 'border-l-yellow-400' };
    if (diff < 30) return { label: `${diff}m`, color: 'bg-orange-100 text-orange-800', border: 'border-l-orange-500' };
    return { label: `${diff}m`, color: 'bg-red-100 text-red-800', border: 'border-l-red-600' };
  };

  const handleConfirmClick = (payment: any) => {
    setSelectedPayment(payment);
    setIsModalOpen(true);
  };

  const handlePaymentConfirmed = async (amount: number) => {
    if (!selectedPayment) return;
    try {
      await confirmPayment(selectedPayment.orderId, amount, user.staffId);
      setIsModalOpen(false);
      setSelectedPayment(null);
    } catch (error) {
      console.error('Payment failed', error);
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedCards(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const printReceipt = () => {
    window.print();
  };

  const handleSendSms = (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneNumber) return;
    // Simulate SMS send
    setTimeout(() => {
      setSmsModalOpen(false);
      setPhoneNumber('');
    }, 500);
  };

  if (!['cashier', 'manager', 'owner'].includes(user?.role || '')) {
    if (typeof window !== 'undefined') window.location.href = '/login';
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      <header className="bg-white shadow-sm px-6 py-4 flex flex-col md:flex-row md:items-center justify-between sticky top-0 z-10 gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Cashier Dashboard</h1>
          <p className="text-sm text-gray-500">
            {user?.name} | PlateLink Africa
          </p>
        </div>
        <div className="flex items-center gap-4 md:gap-6">
          <Link href="/dashboard" className="text-sm font-medium text-gray-600 hover:text-emerald-600 hidden md:block transition-colors">
            Back to Waiter Station
          </Link>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className="text-sm font-medium text-gray-600 hidden sm:inline">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div className="text-lg font-semibold text-gray-700 tabular-nums">
            {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
          <button 
            onClick={logout}
            className="px-4 py-2 text-sm font-medium text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
          >
            Logout
          </button>
        </div>
      </header>

      <main className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 flex items-center gap-4">
            <div className="p-3 bg-emerald-100 rounded-lg text-emerald-600 shrink-0">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Today's Cash Collection</p>
              <h3 className="text-2xl font-bold text-gray-900">KES {totalCashToday.toLocaleString()}</h3>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-lg text-orange-600 shrink-0">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Pending Payments</p>
              <h3 className="text-2xl font-bold text-gray-900">{pendingCount}</h3>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg text-blue-600 shrink-0">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Tables Served Today</p>
              <h3 className="text-2xl font-bold text-gray-900">{servedCount}</h3>
            </div>
          </div>
        </div>

        <div className="mt-8">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Pending Cash Payments</h2>
          
          {pendingPayments.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-12 flex flex-col items-center justify-center text-center border border-gray-100">
              <svg className="w-24 h-24 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-lg font-bold text-gray-900 mb-2">All caught up!</h3>
              <p className="text-gray-500 max-w-sm">There are currently no pending cash payments. Great job keeping the queue clear.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingPayments.map(payment => {
                const waitStatus = getWaitStatus(payment.waitingSince);
                const isExpanded = expandedCards[payment.id];
                
                return (
                  <div key={payment.id} className={`bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden ${waitStatus.border} border-l-4`}>
                    <div className="p-4 md:p-6">
                      <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                        <div className="flex items-center gap-4">
                          <div className="w-16 h-16 bg-gray-50 rounded-lg flex flex-col items-center justify-center border border-gray-100 shrink-0">
                            <span className="text-xs text-gray-500 font-bold uppercase tracking-wider">Table</span>
                            <span className="text-2xl font-bold text-gray-900">{payment.tableNumber}</span>
                          </div>
                          <div>
                            <div className="flex items-center gap-3 mb-1">
                              <h3 className="font-bold text-gray-900 text-lg">{payment.orderNumber}</h3>
                              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${waitStatus.color}`}>
                                {waitStatus.label}
                              </span>
                            </div>
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-800 border border-gray-200">
                              CASH
                            </span>
                          </div>
                        </div>
                        
                        <div className="text-right ml-auto">
                          <div className="text-sm text-gray-500 font-medium mb-1">Total Amount</div>
                          <div className="text-2xl font-bold text-gray-900">KES {payment.total.toLocaleString()}</div>
                        </div>
                      </div>

                      <div className="bg-gray-50 rounded-lg border border-gray-100 mb-4">
                        <button 
                          onClick={() => toggleExpand(payment.id)}
                          className="w-full px-4 py-3 flex items-center justify-between text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
                        >
                          <span>{payment.items.length} items</span>
                          <svg 
                            className={`w-5 h-5 text-gray-400 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                            fill="none" viewBox="0 0 24 24" stroke="currentColor"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        
                        {isExpanded && (
                          <div className="px-4 pb-4 pt-1 space-y-2 border-t border-gray-100">
                            {payment.items.map((item, idx) => (
                              <div key={idx} className="flex justify-between text-sm">
                                <span className="text-gray-600">{item.quantity}x {item.name}</span>
                                <span className="font-medium text-gray-900">KES {(item.price * item.quantity).toLocaleString()}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-3">
                        <button 
                          onClick={() => handleConfirmClick(payment)}
                          className="flex-1 md:flex-none px-6 py-2.5 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors shadow-sm text-center"
                        >
                          Confirm Payment
                        </button>
                        <button 
                          onClick={printReceipt}
                          className="flex-1 md:flex-none px-4 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors text-center flex items-center justify-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                          </svg>
                          Print Receipt
                        </button>
                        <button 
                          onClick={() => setSmsModalOpen(true)}
                          className="flex-1 md:flex-none px-4 py-2.5 bg-white border border-blue-300 text-blue-700 rounded-lg font-medium hover:bg-blue-50 transition-colors text-center"
                        >
                          Send SMS Receipt
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {selectedPayment && (
        <ConfirmPaymentModal
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedPayment(null);
          }}
          onConfirm={handlePaymentConfirmed}
          order={selectedPayment}
        />
      )}

      {smsModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSmsModalOpen(false)}>
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm transform transition-all flex flex-col p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-900 mb-4">Send SMS Receipt</h3>
            <form onSubmit={handleSendSms}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Customer Phone Number</label>
                <input
                  type="tel"
                  required
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="e.g. +254700000000"
                  className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setSmsModalOpen(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!phoneNumber}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  Send
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// apps/customer/components/Payment/CashPayment.tsx
'use client';

import React, { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Banknote, ChefHat, AlertCircle, Loader2 } from 'lucide-react';

interface CashPaymentProps {
  orderId: string;
  amount: number;
  onSuccess: () => void;
}

export default function CashPayment({ orderId, amount, onSuccess }: CashPaymentProps) {
  const router = useRouter();
  const params = useParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePlaceOrder = async () => {
    try {
      setLoading(true);
      setError(null);

      // Call cash payment confirmation endpoint
      const response = await fetch(`/api/payments/cash/${orderId}/confirm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to confirm cash order. Please try again.');
      }

      // Call onSuccess callback
      onSuccess();

      // Redirect to the order tracking page: /[restaurant]/order/[orderId]
      const restaurant = (params?.restaurant as string) || 'default';
      router.push(`/${restaurant}/order/${orderId}`);
    } catch (err: any) {
      console.error('Cash confirmation error:', err);
      setError(err.message || 'An unexpected error occurred while placing your order.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full rounded-xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col gap-5">
      {/* Visual Header card */}
      <div className="flex items-center gap-4 bg-emerald-50/50 p-4 rounded-xl border border-emerald-100">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 shrink-0">
          <Banknote className="h-6 w-6" />
        </div>
        <div className="min-w-0">
          <p className="text-[11px] font-black uppercase tracking-wider text-emerald-600">Cash Payment at Counter</p>
          <h3 className="text-sm font-bold text-slate-800 mt-0.5">
            Pay KES {amount.toLocaleString()} in cash at the counter
          </h3>
        </div>
      </div>

      {/* Kitchen status badge */}
      <div className="flex items-start gap-3 bg-slate-50 p-4 rounded-xl border border-slate-100">
        <ChefHat className="h-5 w-5 text-slate-500 mt-0.5 shrink-0" />
        <p className="text-xs text-slate-500 font-medium leading-relaxed">
          Your order has been sent to the kitchen. Please pay when you pick up your order.
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-2.5 bg-red-50 text-red-600 p-3.5 rounded-xl border border-red-100 text-xs font-semibold leading-relaxed">
          <AlertCircle className="h-4.5 w-4.5 shrink-0 mt-0.5 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Primary Action Button */}
      <button
        onClick={handlePlaceOrder}
        disabled={loading}
        className="w-full bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl py-3.5 font-bold text-sm transition-all shadow-sm active:scale-[0.98] disabled:bg-emerald-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Processing Order...
          </>
        ) : (
          'Place Order'
        )}
      </button>
    </div>
  );
}

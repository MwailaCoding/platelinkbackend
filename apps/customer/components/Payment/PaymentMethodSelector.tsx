// apps/customer/components/Payment/PaymentMethodSelector.tsx
'use client';

import React from 'react';
import { CreditCard, Smartphone, Banknote, Check } from 'lucide-react';

interface PaymentMethodSelectorProps {
  selectedMethod: 'pesapal' | 'mpesa' | 'cash';
  onSelect: (method: 'pesapal' | 'mpesa' | 'cash') => void;
  amount: number;
  restaurantPaymentTrack: 'pesapal' | 'mpesa_direct' | 'cash';
}

export default function PaymentMethodSelector({
  selectedMethod,
  onSelect,
  amount,
  restaurantPaymentTrack,
}: PaymentMethodSelectorProps) {
  // Determine if each option is active based on the restaurant's payment track
  const showPesapal = restaurantPaymentTrack === 'pesapal';
  const showMpesaDirect = restaurantPaymentTrack === 'mpesa_direct';
  const showCash = true; // Cash is always an option for PlateLink Africa orders

  const methods = [
    {
      id: 'pesapal' as const,
      title: 'Pay with M-Pesa / Card',
      description: 'Secure payment via Pesapal',
      show: showPesapal,
      icon: (
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600 transition-colors">
          <CreditCard className="h-5 w-5" />
        </div>
      ),
    },
    {
      id: 'mpesa' as const,
      title: 'Pay with M-Pesa (STK Push)',
      description: 'Instant payment request to your phone',
      show: showMpesaDirect,
      icon: (
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 transition-colors">
          <Smartphone className="h-5 w-5" />
        </div>
      ),
    },
    {
      id: 'cash' as const,
      title: 'Pay at Counter',
      description: 'Pay with cash when you receive your order',
      show: showCash,
      icon: (
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-600 transition-colors">
          <Banknote className="h-5 w-5" />
        </div>
      ),
    },
  ].filter((m) => m.show);

  return (
    <div className="w-full space-y-4">
      <div className="flex flex-col gap-1">
        <h3 className="text-sm font-bold text-slate-800 tracking-tight">Payment Method</h3>
        <p className="text-xs text-slate-500 font-medium">Select how you want to pay KES {amount.toLocaleString()}</p>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {methods.map((method) => {
          const isSelected = selectedMethod === method.id;
          return (
            <button
              key={method.id}
              onClick={() => onSelect(method.id)}
              className={`relative flex items-start gap-4 rounded-xl border p-4 text-left transition-all duration-300 ${
                isSelected
                  ? 'border-emerald-600 bg-emerald-50/20 ring-1 ring-emerald-600'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              <div className="shrink-0">{method.icon}</div>
              <div className="flex-1 min-w-0 pr-6">
                <h4 className="text-sm font-bold text-slate-800">{method.title}</h4>
                <p className="text-xs text-slate-500 font-medium mt-0.5 leading-relaxed">{method.description}</p>
              </div>

              {/* Custom Radio Button Indicator */}
              <div className="absolute right-4 top-4 shrink-0 flex items-center justify-center">
                <div
                  className={`h-5 w-5 rounded-full border flex items-center justify-center transition-all ${
                    isSelected ? 'border-emerald-600 bg-emerald-600' : 'border-slate-300 bg-white'
                  }`}
                >
                  {isSelected && <Check className="h-3 w-3 text-white stroke-[3]" />}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

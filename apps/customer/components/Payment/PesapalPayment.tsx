// apps/customer/components/Payment/PesapalPayment.tsx
'use client';

import React, { useEffect, useState, useRef } from 'react';
import { Loader2, AlertCircle, ShieldCheck, RefreshCw } from 'lucide-react';

interface PesapalPaymentProps {
  orderId: string;
  amount: number;
  customerPhone: string;
  customerEmail: string;
  onSuccess: () => void;
  onError: (error: string) => void;
}

export default function PesapalPayment({
  orderId,
  amount,
  customerPhone,
  customerEmail,
  onSuccess,
  onError,
}: PesapalPaymentProps) {
  const [status, setStatus] = useState<'initiating' | 'redirecting' | 'polling' | 'success' | 'error'>('initiating');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Check if the user is returning from a payment or if we already initiated
  useEffect(() => {
    const checkPaymentFlow = async () => {
      if (typeof window === 'undefined') return;

      const urlParams = new URLSearchParams(window.location.search);
      const hasPesapalParams = urlParams.has('OrderTrackingId') || urlParams.has('pesapal_transaction_tracking_id');
      const isAlreadyInitiated = sessionStorage.getItem(`pesapal_initiated_${orderId}`) === 'true';

      if (hasPesapalParams || isAlreadyInitiated) {
        // We are in polling state (returned from Pesapal page or already redirected once)
        setStatus('polling');
        startPolling();
      } else {
        // First-time mount: Initiate payment
        await initiatePesapalPayment();
      }
    };

    checkPaymentFlow();

    return () => {
      stopPolling();
    };
  }, [orderId, retryCount]);

  const initiatePesapalPayment = async () => {
    try {
      setStatus('initiating');
      setErrorMessage(null);

      const response = await fetch('/api/payments/pesapal/initiate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          order_id: orderId,
          amount: amount,
          phone_number: customerPhone,
          email: customerEmail,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to initiate payment via Pesapal. Please try again.');
      }

      const data = await response.json();
      const redirectUrl = data.redirect_url;

      if (!redirectUrl) {
        throw new Error('Payment gateway response was missing redirect URL.');
      }

      // Mark as initiated to prevent redirect loops when they return
      sessionStorage.setItem(`pesapal_initiated_${orderId}`, 'true');
      setStatus('redirecting');

      // Redirect user to the secure Pesapal checkout page
      window.location.href = redirectUrl;
    } catch (err: any) {
      console.error('Pesapal initiation error:', err);
      const msg = err.message || 'An error occurred while connecting to Pesapal.';
      setStatus('error');
      setErrorMessage(msg);
      onError(msg);
    }
  };

  const startPolling = () => {
    stopPolling(); // Clear existing if any

    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`/api/orders/${orderId}`);
        if (!response.ok) {
          throw new Error('Failed to query order payment status.');
        }

        const orderData = await response.json();
        
        // Check if payment_status is 'paid' (based on PaymentStatus.paid enum)
        if (orderData.payment_status === 'paid') {
          stopPolling();
          setStatus('success');
          sessionStorage.removeItem(`pesapal_initiated_${orderId}`);
          onSuccess();
        } else if (orderData.payment_status === 'failed') {
          stopPolling();
          throw new Error('Payment failed or was declined. Please try another method.');
        }
      } catch (err: any) {
        console.error('Polling order status error:', err);
        // We do not stop polling on a temporary network/server error to remain resilient,
        // but if it is an explicit failure from the backend, we handle it
        if (err.message.includes('failed') || err.message.includes('declined')) {
          stopPolling();
          const msg = err.message;
          setStatus('error');
          setErrorMessage(msg);
          onError(msg);
        }
      }
    }, 3000); // Poll every 3 seconds
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const handleManualCheckStatus = async () => {
    try {
      setStatus('polling');
      const response = await fetch(`/api/orders/${orderId}`);
      if (response.ok) {
        const orderData = await response.json();
        if (orderData.payment_status === 'paid') {
          sessionStorage.removeItem(`pesapal_initiated_${orderId}`);
          onSuccess();
          return;
        }
      }
      startPolling();
    } catch (err) {
      startPolling();
    }
  };

  return (
    <div className="w-full rounded-xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col items-center justify-center text-center min-h-[220px]">
      {status === 'initiating' && (
        <div className="space-y-4">
          <Loader2 className="h-10 w-10 text-emerald-600 animate-spin mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">Initiating Secure Payment</h3>
          <p className="text-xs text-slate-500 max-w-xs leading-relaxed mx-auto">
            Connecting to Pesapal secure servers to prepare your transaction of KES {amount.toLocaleString()}...
          </p>
        </div>
      )}

      {status === 'redirecting' && (
        <div className="space-y-4">
          <Loader2 className="h-10 w-10 text-emerald-600 animate-spin mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">Redirecting to Pesapal</h3>
          <p className="text-xs text-slate-500 max-w-xs leading-relaxed mx-auto">
            You are being redirected to the secure Pesapal checkout page to complete your payment...
          </p>
        </div>
      )}

      {status === 'polling' && (
        <div className="space-y-4 w-full">
          <div className="relative flex items-center justify-center">
            <Loader2 className="h-10 w-10 text-emerald-600 animate-spin mx-auto" />
            <ShieldCheck className="h-4.5 w-4.5 text-emerald-600 absolute" />
          </div>
          <h3 className="text-sm font-bold text-slate-800">Awaiting Payment Confirmation</h3>
          <p className="text-xs text-slate-500 max-w-xs leading-relaxed mx-auto">
            Please complete the payment on the secure page. We are listening for the confirmation from Pesapal.
          </p>
          <div className="flex flex-col gap-2 pt-2 max-w-xs mx-auto">
            <button
              onClick={handleManualCheckStatus}
              className="flex items-center justify-center gap-2 w-full rounded-xl bg-slate-900 hover:bg-slate-800 text-white py-2.5 text-xs font-bold transition-all shadow-sm"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Check Status Now
            </button>
            <button
              onClick={() => {
                sessionStorage.removeItem(`pesapal_initiated_${orderId}`);
                setRetryCount((prev) => prev + 1);
              }}
              className="text-xs font-semibold text-slate-500 hover:text-slate-700 transition-colors py-1"
            >
              Restart Payment Process
            </button>
          </div>
        </div>
      )}

      {status === 'success' && (
        <div className="space-y-4">
          <div className="h-12 w-12 rounded-full bg-emerald-100 flex items-center justify-center mx-auto text-emerald-600">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-800">Payment Confirmed</h3>
          <p className="text-xs text-slate-500 max-w-xs leading-relaxed mx-auto">
            Your payment has been successfully processed! Preparing your order now...
          </p>
        </div>
      )}

      {status === 'error' && (
        <div className="space-y-4 w-full">
          <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center mx-auto text-red-600">
            <AlertCircle className="h-6 w-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-800">Payment Connection Failed</h3>
          <p className="text-xs text-red-600 bg-red-50 p-3 rounded-lg max-w-xs mx-auto leading-relaxed font-medium">
            {errorMessage || 'We were unable to set up the Pesapal transaction.'}
          </p>
          <div className="flex gap-2 max-w-xs mx-auto pt-2">
            <button
              onClick={() => {
                sessionStorage.removeItem(`pesapal_initiated_${orderId}`);
                setRetryCount((prev) => prev + 1);
              }}
              className="flex-1 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white py-2.5 text-xs font-bold transition-all shadow-sm"
            >
              Retry Payment
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

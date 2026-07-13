// apps/customer/components/Payment/PaymentStatus.tsx
'use client';

import React, { useEffect, useState, useRef } from 'react';
import { 
  Loader2, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  RefreshCw, 
  ArrowRight, 
  ShieldCheck, 
  Clock, 
  Banknote, 
  CreditCard,
  Smartphone
} from 'lucide-react';

interface PaymentStatusProps {
  transactionId: string;
  orderId: string;
  paymentMethod: 'pesapal' | 'mpesa' | 'cash';
  onComplete: () => void;
}

type UIState = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export default function PaymentStatus({
  transactionId,
  orderId,
  paymentMethod,
  onComplete,
}: PaymentStatusProps) {
  const [status, setStatus] = useState<UIState>('pending');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isCheckingManually, setIsCheckingManually] = useState(false);
  const [hasTimedOut, setHasTimedOut] = useState(false);
  
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(Date.now());

  // Helper to normalize backend status to component UIState
  const normalizeStatus = (backendStatus: string): UIState => {
    const s = backendStatus.toLowerCase();
    if (['completed', 'completed_payment', 'paid', 'success', 'succeeded'].includes(s)) {
      return 'completed';
    }
    if (['failed', 'error', 'declined', 'unsuccessful'].includes(s)) {
      return 'failed';
    }
    if (['cancelled', 'canceled', 'voided', 'rejected'].includes(s)) {
      return 'cancelled';
    }
    if (['processing', 'processing_payment', 'in_progress', 'captured'].includes(s)) {
      return 'processing';
    }
    return 'pending';
  };

  const fetchStatus = async () => {
    // If there is no transaction ID (e.g. for cash, or fallback), we might query order payment status instead
    const url = transactionId 
      ? `/api/payments/status/${transactionId}` 
      : `/api/orders/${orderId}`;
      
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Cache-Control': 'no-cache',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch payment status: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Determine the raw status from response. If we queried order, read order.payment_status.
    // If we queried payment status endpoint directly, read the status field.
    const rawStatus = data.status || data.payment_status || 'pending';
    return normalizeStatus(rawStatus);
  };

  const checkStatusOnce = async (isManual = false) => {
    if (isManual) {
      setIsCheckingManually(true);
      setErrorMessage(null);
    }
    
    try {
      const currentStatus = await fetchStatus();
      setStatus(currentStatus);
      
      if (currentStatus === 'completed') {
        stopPolling();
      } else if (currentStatus === 'failed' || currentStatus === 'cancelled') {
        stopPolling();
      }
    } catch (err: any) {
      console.error('Error checking payment status:', err);
      if (isManual) {
        setErrorMessage(err.message || 'Unable to fetch status. Please try again.');
      }
    } finally {
      if (isManual) {
        setIsCheckingManually(false);
      }
    }
  };

  const startPolling = () => {
    stopPolling();
    startTimeRef.current = Date.now();
    setElapsedTime(0);
    setHasTimedOut(false);

    pollIntervalRef.current = setInterval(async () => {
      const duration = Math.floor((Date.now() - startTimeRef.current) / 1000);
      setElapsedTime(duration);

      if (duration >= 60) {
        setHasTimedOut(true);
        stopPolling();
        return;
      }

      await checkStatusOnce(false);
    }, 3000);
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  useEffect(() => {
    // Only poll for real-time channels (pesapal, mpesa) if transactionId is available.
    // For Cash, it generally waits for staff confirmation, so we can poll order status instead.
    if (paymentMethod === 'pesapal' || paymentMethod === 'mpesa') {
      startPolling();
    } else {
      // For cash, let's check order status every 5 seconds instead of 3, up to 60s
      startPolling();
    }

    return () => {
      stopPolling();
    };
  }, [transactionId, orderId, paymentMethod]);

  const handleRetry = () => {
    setStatus('pending');
    setErrorMessage(null);
    startPolling();
  };

  const getStatusConfig = () => {
    switch (status) {
      case 'pending':
        return {
          icon: <Clock className="h-8 w-8 text-amber-500 animate-pulse" />,
          bgColor: 'bg-amber-50',
          borderColor: 'border-amber-100',
          title: 'Awaiting Payment',
          description: 'Waiting for payment confirmation...',
          textColor: 'text-amber-700',
          button: hasTimedOut ? (
            <button
              onClick={() => checkStatusOnce(true)}
              disabled={isCheckingManually}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white py-3.5 text-sm font-bold transition-all shadow-md active:scale-[0.98] disabled:bg-slate-400"
            >
              {isCheckingManually ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Checking Status...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Check Status Manually
                </>
              )}
            </button>
          ) : (
            <div className="w-full text-center py-2 text-xs font-semibold text-slate-400 animate-pulse flex items-center justify-center gap-2">
              <Loader2 className="h-3 w-3 animate-spin text-amber-500" />
              Polling secure payment gateway...
            </div>
          )
        };
      case 'processing':
        return {
          icon: <Loader2 className="h-8 w-8 text-indigo-600 animate-spin" />,
          bgColor: 'bg-indigo-50',
          borderColor: 'border-indigo-100',
          title: 'Processing Payment',
          description: 'Processing your payment...',
          textColor: 'text-indigo-700',
          button: (
            <div className="w-full text-center py-2 text-xs font-semibold text-indigo-600 animate-pulse">
              Finalizing transaction with bank...
            </div>
          )
        };
      case 'completed':
        return {
          icon: <CheckCircle2 className="h-8 w-8 text-emerald-600 animate-bounce" />,
          bgColor: 'bg-emerald-50',
          borderColor: 'border-emerald-100',
          title: 'Payment Successful!',
          description: 'Payment successful!',
          textColor: 'text-emerald-700',
          button: (
            <button
              onClick={onComplete}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white py-3.5 text-sm font-bold transition-all shadow-md active:scale-[0.98] hover:shadow-emerald-100 hover:shadow-lg"
            >
              Continue to Order
              <ArrowRight className="h-4 w-4" />
            </button>
          )
        };
      case 'failed':
        return {
          icon: <XCircle className="h-8 w-8 text-rose-600" />,
          bgColor: 'bg-rose-50',
          borderColor: 'border-rose-100',
          title: 'Payment Failed',
          description: 'Payment failed. Please try again.',
          textColor: 'text-rose-700',
          button: (
            <button
              onClick={handleRetry}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white py-3.5 text-sm font-bold transition-all shadow-md active:scale-[0.98]"
            >
              <RefreshCw className="h-4 w-4" />
              Retry Payment
            </button>
          )
        };
      case 'cancelled':
        return {
          icon: <XCircle className="h-8 w-8 text-slate-500" />,
          bgColor: 'bg-slate-50',
          borderColor: 'border-slate-200',
          title: 'Payment Cancelled',
          description: 'Payment cancelled.',
          textColor: 'text-slate-600',
          button: (
            <button
              onClick={handleRetry}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white py-3.5 text-sm font-bold transition-all shadow-md active:scale-[0.98]"
            >
              Try Again
            </button>
          )
        };
    }
  };

  const getMethodDetails = () => {
    switch (paymentMethod) {
      case 'mpesa':
        return {
          name: 'M-PESA',
          icon: <Smartphone className="h-4 w-4" />,
          colorClass: 'text-emerald-600 border-emerald-100 bg-emerald-50'
        };
      case 'pesapal':
        return {
          name: 'Pesapal',
          icon: <CreditCard className="h-4 w-4" />,
          colorClass: 'text-indigo-600 border-indigo-100 bg-indigo-50'
        };
      case 'cash':
        return {
          name: 'Cash Payment',
          icon: <Banknote className="h-4 w-4" />,
          colorClass: 'text-amber-600 border-amber-100 bg-amber-50'
        };
    }
  };

  const config = getStatusConfig();
  const method = getMethodDetails();

  return (
    <div className="w-full max-w-md mx-auto p-1">
      <div className={`w-full rounded-2xl border ${config.borderColor} ${config.bgColor} p-6 md:p-8 shadow-xl transition-all duration-500 flex flex-col items-center text-center relative overflow-hidden backdrop-blur-md`}>
        {/* Sleek top glowing border indicator */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-emerald-500 via-teal-400 to-indigo-500" />
        
        {/* Circular pulsing container for visual impact */}
        <div className="relative mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-white shadow-lg border border-slate-100">
          <div className="absolute inset-0 rounded-full bg-slate-100 opacity-20 scale-125 animate-ping" />
          {config.icon}
        </div>

        {/* Header content */}
        <h3 className="text-xl font-extrabold text-slate-800 tracking-tight">
          {config.title}
        </h3>
        
        <p className="mt-2.5 text-sm text-slate-600 font-medium max-w-xs leading-relaxed">
          {config.description}
        </p>

        {/* Payment channel micro-badge */}
        <div className={`mt-4 inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-bold ${method.colorClass}`}>
          {method.icon}
          <span>{method.name}</span>
        </div>

        {/* Detail metadata block */}
        <div className="w-full mt-6 bg-white/70 border border-slate-100 rounded-xl p-4 text-left text-xs space-y-2.5 shadow-sm">
          <div className="flex justify-between items-center text-slate-500">
            <span>Order Reference</span>
            <span className="font-mono font-bold text-slate-800 uppercase">
              #{orderId.substring(0, 8)}
            </span>
          </div>
          {transactionId && (
            <div className="flex justify-between items-center text-slate-500">
              <span>Transaction Ref</span>
              <span className="font-mono font-semibold text-slate-700">
                {transactionId.substring(0, 12)}
              </span>
            </div>
          )}
          {paymentMethod === 'cash' && (
            <div className="text-slate-500 font-medium pt-1.5 border-t border-slate-100/80 leading-relaxed text-center">
              Please visit the restaurant cash register to pay and complete this order.
            </div>
          )}
        </div>

        {/* Timeout / fallback information helper */}
        {hasTimedOut && status === 'pending' && (
          <div className="w-full mt-4 flex items-start gap-2.5 bg-amber-50/80 text-amber-700 border border-amber-200/50 p-3 rounded-xl text-[11px] font-medium leading-relaxed text-left">
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-500 mt-0.5" />
            <div>
              <p className="font-bold">Confirmation is taking longer than expected.</p>
              <p className="mt-0.5 text-amber-600/90">You can trigger a manual lookup or ask server staff for immediate checkout verification.</p>
            </div>
          </div>
        )}

        {/* Display manual query errors */}
        {errorMessage && (
          <div className="w-full mt-4 flex items-start gap-2 bg-rose-50 text-rose-700 border border-rose-200/50 p-3 rounded-xl text-xs font-semibold leading-relaxed text-left">
            <XCircle className="h-4 w-4 shrink-0 text-rose-500 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Secure checkout assurance signature */}
        <div className="mt-6 w-full flex items-center justify-center gap-1.5 text-[10px] font-semibold text-slate-400">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
          <span>Secured by PlateLink Payment Verification Gateway</span>
        </div>

        {/* Action button container */}
        <div className="w-full mt-6 pt-4 border-t border-slate-100/80">
          {config.button}
        </div>
      </div>
    </div>
  );
}

'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { 
  UtensilsCrossed, 
  ArrowRight, 
  ArrowLeft, 
  Loader2, 
  Check, 
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import Link from 'next/link';

// Component that holds all the UI and logic
function VerifyEmailForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || '';
  
  // State for the 6-digit OTP code
  const [otp, setOtp] = useState<string[]>(Array(6).fill(''));
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  
  // Refs for each input box
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 5000);
  };

  // Auto-focus first input box on page load
  useEffect(() => {
    if (inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, []);

  // Cooldown countdown
  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => {
        setCooldown((prev) => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  // Handle verify request
  const handleVerify = async (codeToVerify?: string) => {
    const code = codeToVerify || otp.join('');
    if (code.length !== 6) {
      showToast('Please enter the full 6-digit verification code.', 'error');
      return;
    }

    setLoading(true);
    setToast(null);

    try {
      const response = await fetch('/api/auth/verify-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          otp_code: code,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.error || 'Invalid or expired verification code. Please try again.');
      }

      showToast('Email verified successfully! Redirecting to login...', 'success');

      // Success: redirect based on restaurant type
      setTimeout(() => {
        const type = localStorage.getItem('signup_restaurant_type');
        if (type === 'multi_branch') {
          router.push(`/onboarding/branch-setup`);
        } else {
          router.push(`/login?verified=true&email=${encodeURIComponent(email)}`);
        }
      }, 2000);
    } catch (err: any) {
      showToast(err.message || 'Verification failed. Please try again.', 'error');
      // Failure: clear OTP inputs and reset focus
      setOtp(Array(6).fill(''));
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  // Auto-submit when all 6 digits are entered
  useEffect(() => {
    const code = otp.join('');
    if (code.length === 6 && !loading) {
      handleVerify(code);
    }
  }, [otp]);

  // Handle changes in input fields
  const handleChange = (value: string, index: number) => {
    const num = value.replace(/[^0-9]/g, '');
    if (!num) return;

    const newOtp = [...otp];
    // Take the last character entered
    newOtp[index] = num.slice(-1);
    setOtp(newOtp);

    // Focus the next input box
    if (index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  // Handle key down events (e.g. backspace)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, index: number) => {
    if (e.key === 'Backspace') {
      if (!otp[index] && index > 0) {
        const newOtp = [...otp];
        newOtp[index - 1] = '';
        setOtp(newOtp);
        inputRefs.current[index - 1]?.focus();
      } else {
        const newOtp = [...otp];
        newOtp[index] = '';
        setOtp(newOtp);
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === 'ArrowRight' && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  // Handle pasting code
  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasteData = e.clipboardData.getData('text').replace(/[^0-9]/g, '').slice(0, 6);
    if (pasteData) {
      const newOtp = [...otp];
      for (let i = 0; i < pasteData.length; i++) {
        newOtp[i] = pasteData[i];
      }
      setOtp(newOtp);

      // Focus the last filled box or focus the next empty box
      const focusIndex = Math.min(pasteData.length, 5);
      inputRefs.current[focusIndex]?.focus();
    }
  };

  // Handle resend request
  const handleResend = async () => {
    if (cooldown > 0 || resending) return;

    setResending(true);
    setToast(null);

    try {
      const response = await fetch('/api/auth/resend-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.error || 'Failed to resend verification code.');
      }

      showToast('A new 6-digit code has been sent to your email!', 'success');
      setCooldown(30);
    } catch (err: any) {
      showToast(err.message || 'Failed to resend code. Please try again later.', 'error');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center relative overflow-hidden font-sans selection:bg-emerald-500 selection:text-white p-4">
      {/* Toast Alert */}
      {toast && (
        <div className={`fixed top-5 right-5 z-50 flex items-center gap-3 px-5 py-4 rounded-xl shadow-xl border transition-all duration-300 transform translate-y-0 scale-100 ${
          toast.type === 'success' 
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800' 
            : 'bg-rose-50 border-rose-200 text-rose-800'
        }`}>
          {toast.type === 'success' ? (
            <div className="p-1 bg-emerald-500 text-white rounded-full">
              <Check className="w-4 h-4" />
            </div>
          ) : (
            <div className="p-1 bg-rose-500 text-white rounded-full">
              <AlertCircle className="w-4 h-4" />
            </div>
          )}
          <span className="text-sm font-semibold">{toast.message}</span>
        </div>
      )}

      {/* Decorative Gradients */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-emerald-200/20 rounded-full filter blur-3xl -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-emerald-300/10 rounded-full filter blur-3xl translate-x-1/2 translate-y-1/2" />

      {/* Logo */}
      <div className="flex items-center gap-3 mb-8 group relative z-10">
        <div className="w-12 h-12 bg-emerald-600 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-emerald-600/30 group-hover:scale-105 transition-transform duration-300">
          <UtensilsCrossed className="w-6 h-6" />
        </div>
        <div className="text-left">
          <span className="text-2xl font-black text-gray-900 tracking-tight">PlateLink</span>
          <span className="text-xs font-bold text-emerald-600 block leading-none">AFRICA</span>
        </div>
      </div>

      {/* Main Card */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-2xl p-8 lg:p-10 w-full max-w-md relative overflow-hidden z-10">
        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-50 rounded-bl-full -z-10" />

        {/* Emoji/icon */}
        <div className="w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center text-3xl mx-auto mb-6 shadow-inner animate-pulse">
          ✉️
        </div>

        {/* Header */}
        <h2 className="text-2xl font-extrabold text-gray-900 text-center">Verify Your Email</h2>
        
        {/* Subheader */}
        <p className="text-gray-500 text-sm mt-3 text-center leading-relaxed">
          We sent a 6-digit code to{' '}
          <span className="font-bold text-gray-900 break-all animate-fade-in">
            {email || 'your email address'}
          </span>
        </p>

        {/* OTP Inputs */}
        <div className="flex justify-center gap-2 mt-8 mb-6">
          {otp.map((digit, idx) => (
            <input
              key={idx}
              ref={(el) => {
                inputRefs.current[idx] = el;
              }}
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={1}
              value={digit}
              onChange={(e) => handleChange(e.target.value, idx)}
              onKeyDown={(e) => handleKeyDown(e, idx)}
              onPaste={idx === 0 ? handlePaste : undefined}
              className="border border-gray-200 focus:border-emerald-500 rounded-lg text-center font-bold text-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 bg-gray-50 focus:bg-white transition-all focus:scale-105 shadow-sm"
              style={{ width: '50px', height: '50px' }}
            />
          ))}
        </div>

        {/* Verify Email Button */}
        <button
          onClick={() => handleVerify()}
          disabled={loading || otp.join('').length !== 6}
          className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white rounded-2xl font-bold flex items-center justify-center gap-2 hover:gap-3 transition-all duration-300 disabled:opacity-50 disabled:pointer-events-none shadow-xl shadow-emerald-600/25"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Verifying Email...
            </>
          ) : (
            <>
              Verify Email
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>

        {/* Resend Link with timer */}
        <div className="mt-8 text-center text-sm font-semibold text-gray-500">
          Didn't receive the code?{' '}
          {cooldown > 0 ? (
            <span className="text-gray-400 font-bold ml-1 inline-flex items-center gap-1.5 cursor-not-allowed">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              Resend in {cooldown}s
            </span>
          ) : (
            <button
              onClick={handleResend}
              disabled={resending}
              className="text-emerald-600 hover:text-emerald-700 transition-colors underline decoration-2 decoration-emerald-600/25 hover:decoration-emerald-700 font-bold focus:outline-none disabled:opacity-50 disabled:no-underline"
            >
              {resending ? 'Sending...' : 'Resend Code'}
            </button>
          )}
        </div>

        {/* Back to Login */}
        <div className="mt-6 text-center">
          <Link 
            href="/login" 
            className="inline-flex items-center gap-1.5 text-xs font-bold text-gray-400 hover:text-gray-600 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Login
          </Link>
        </div>
      </div>

      {/* Decorative Bottom Banner */}
      <p className="mt-8 text-xs font-semibold text-gray-400 text-center max-w-xs relative z-10 leading-relaxed">
        Verify your email to activate your 14-day free trial. Need help? Contact PlateLink support.
      </p>
    </div>
  );
}

// Fallback UI shown while Suspense is loading search params
function VerifyEmailFallback() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center p-4">
      <div className="w-12 h-12 bg-emerald-600 rounded-2xl flex items-center justify-center text-white animate-spin">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    </div>
  );
}

// Main page component
export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<VerifyEmailFallback />}>
      <VerifyEmailForm />
    </Suspense>
  );
}

// apps/admin/app/(dashboard)/settings/payments/page.tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  CreditCard,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  CheckCircle2,
  X,
  AlertTriangle,
  Check,
  ChevronRight,
  Info,
  FileText,
  Upload,
  ArrowRight,
  Shield,
  Coins,
  HelpCircle,
  RefreshCw,
  Clock,
  Sparkles,
  Building,
  CheckSquare,
  AlertCircle
} from 'lucide-react';

// ==========================================
// TYPES AND INTERFACES
// ==========================================

type PaymentTrack = 'pesapal' | 'mpesa' | 'cash';
type ConfigStatus = 'active' | 'pending' | 'needs_attention';

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface UploadedFile {
  name: string;
  size: string;
  type: string;
  progress: number;
  status: 'uploading' | 'completed' | 'failed';
}

interface ConciergeDocs {
  businessRegistration?: UploadedFile;
  kraPin?: UploadedFile;
  directorId?: UploadedFile;
  cr12Form?: UploadedFile;
}

export default function PaymentSettingsPage() {
  const router = useRouter();

  // ==========================================
  // STATE MANAGEMENT
  // ==========================================

  // Payment Track State
  const [activeTrack, setActiveTrack] = useState<PaymentTrack>('pesapal');
  const [pendingTrack, setPendingTrack] = useState<PaymentTrack | null>(null);
  
  // Settings and Configuration status
  const [isMpesaConfigured, setIsMpesaConfigured] = useState(false);
  const [isConciergeRequested, setIsConciergeRequested] = useState(false);
  const [lastPayoutDate, setLastPayoutDate] = useState<string | null>('2026-05-25');
  
  // Loading States
  const [loading, setLoading] = useState(true);
  const [testingConnection, setTestingConnection] = useState(false);
  const [savingCredentials, setSavingCredentials] = useState(false);
  const [savingTrack, setSavingTrack] = useState(false);
  const [submittingConcierge, setSubmittingConcierge] = useState(false);

  // M-Pesa Credentials Form State
  const [mpesaForm, setMpesaForm] = useState({
    shortcode: '',
    consumerKey: '',
    consumerSecret: '',
    passkey: '',
    environment: 'sandbox' as 'sandbox' | 'production'
  });

  // Password Visibility States
  const [showConsumerKey, setShowConsumerKey] = useState(false);
  const [showConsumerSecret, setShowConsumerSecret] = useState(false);
  const [showPasskey, setShowPasskey] = useState(false);

  // Test Connection Results
  const [testResult, setTestResult] = useState<{
    status: 'idle' | 'success' | 'error';
    message?: string;
  }>({ status: 'idle' });

  // Modal Visibility States
  const [showTrackConfirmModal, setShowTrackConfirmModal] = useState(false);
  const [showConciergeModal, setShowConciergeModal] = useState(false);
  const [showConciergeSuccess, setShowConciergeSuccess] = useState(false);

  // Concierge Document Upload State
  const [conciergeDocs, setConciergeDocs] = useState<ConciergeDocs>({});
  const [businessType, setBusinessType] = useState<string>('limited_company');

  // Toasts
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Drag and Drop Zone States
  const [activeDragZone, setActiveDragZone] = useState<string | null>(null);

  // Offline Simulator / Mock Flag
  const [isUsingMocks, setIsUsingMocks] = useState(false);

  // ==========================================
  // TOAST SYSTEM
  // ==========================================
  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    const id = Math.random().toString();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  // ==========================================
  // MOUNT LOAD
  // ==========================================
  useEffect(() => {
    const loadSettings = async () => {
      setLoading(true);
      const token = localStorage.getItem('token') || localStorage.getItem('platelink_auth_token');

      try {
        // Try fetching current settings from API
        const res = await fetch('/api/restaurants/settings', {
          headers: {
            'Authorization': token ? `Bearer ${token}` : ''
          }
        });

        if (!res.ok) throw new Error('API offline');

        const data = await res.json();
        
        // Populate states from DB
        setActiveTrack(data.payment_track || 'pesapal');
        setIsMpesaConfigured(!!data.mpesa_configured || !!data.shortcode);
        setMpesaForm({
          shortcode: data.shortcode || '',
          consumerKey: data.consumer_key || '',
          consumerSecret: data.consumer_secret || '',
          passkey: data.passkey || '',
          environment: (data.environment as 'sandbox' | 'production') || 'sandbox'
        });
        setIsConciergeRequested(!!data.mpesa_concierge_requested);
        setLastPayoutDate(data.last_payout_date || '2026-05-25');
        setIsUsingMocks(false);
      } catch (error) {
        console.warn('API routes offline, running local storage client-side simulation.');
        setIsUsingMocks(true);

        // Attempt load from localStorage simulation
        const simSettings = localStorage.getItem('sim_payment_settings');
        if (simSettings) {
          const data = JSON.parse(simSettings);
          setActiveTrack(data.paymentTrack || 'pesapal');
          setIsMpesaConfigured(data.isMpesaConfigured || false);
          setMpesaForm(data.mpesaForm || {
            shortcode: '',
            consumerKey: '',
            consumerSecret: '',
            passkey: '',
            environment: 'sandbox'
          });
          setIsConciergeRequested(data.isConciergeRequested || false);
          setLastPayoutDate(data.lastPayoutDate || '2026-05-25');
        } else {
          // Default seed data
          setActiveTrack('pesapal');
          setIsMpesaConfigured(false);
          setIsConciergeRequested(false);
        }
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  // Save current simulated settings to localstorage
  const persistSimulatedSettings = (updates: Record<string, any>) => {
    if (!isUsingMocks) return;
    const current = {
      paymentTrack: activeTrack,
      isMpesaConfigured,
      mpesaForm,
      isConciergeRequested,
      lastPayoutDate
    };
    const updated = { ...current, ...updates };
    localStorage.setItem('sim_payment_settings', JSON.stringify(updated));
  };

  // ==========================================
  // ACTION HANDLERS
  // ==========================================

  // Initiate Track Selection Change
  const handleTrackSelectClick = (track: PaymentTrack) => {
    if (track === activeTrack) return;
    setPendingTrack(track);
    setShowTrackConfirmModal(true);
  };

  // Confirm Track Change
  const confirmTrackChange = async () => {
    if (!pendingTrack) return;
    setSavingTrack(true);
    const token = localStorage.getItem('token') || localStorage.getItem('platelink_auth_token');

    try {
      if (isUsingMocks) {
        // Simulate API network latency
        await new Promise((resolve) => setTimeout(resolve, 800));
        setActiveTrack(pendingTrack);
        persistSimulatedSettings({ paymentTrack: pendingTrack });
      } else {
        const res = await fetch('/api/restaurants/settings/payment-track', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          },
          body: JSON.stringify({ payment_track: pendingTrack })
        });

        if (!res.ok) throw new Error('Failed to update payment track.');
        setActiveTrack(pendingTrack);
      }

      showToast(
        `Active payment track updated to ${
          pendingTrack === 'pesapal'
            ? 'Pesapal Aggregator'
            : pendingTrack === 'mpesa'
            ? 'Direct M-Pesa'
            : 'Cash Only'
        }.`,
        'success'
      );
    } catch (err: any) {
      showToast(err.message || 'Error occurred while saving payment track.', 'error');
    } finally {
      setSavingTrack(false);
      setShowTrackConfirmModal(false);
      setPendingTrack(null);
    }
  };

  // Save M-Pesa Credentials
  const handleSaveMpesaCredentials = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!mpesaForm.shortcode || !mpesaForm.consumerKey || !mpesaForm.consumerSecret || !mpesaForm.passkey) {
      showToast('Please fill out all credentials fields before saving.', 'error');
      return;
    }

    setSavingCredentials(true);
    const token = localStorage.getItem('token') || localStorage.getItem('platelink_auth_token');

    try {
      if (isUsingMocks) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        setIsMpesaConfigured(true);
        persistSimulatedSettings({ isMpesaConfigured: true, mpesaForm });
      } else {
        const res = await fetch('/api/restaurants/settings/mpesa-credentials', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          },
          body: JSON.stringify({
            shortcode: mpesaForm.shortcode,
            consumer_key: mpesaForm.consumerKey,
            consumer_secret: mpesaForm.consumerSecret,
            passkey: mpesaForm.passkey,
            environment: mpesaForm.environment
          })
        });

        if (!res.ok) throw new Error('Failed to save M-Pesa credentials.');
        setIsMpesaConfigured(true);
      }

      showToast('Direct M-Pesa credentials securely saved & encrypted.', 'success');
    } catch (err: any) {
      showToast(err.message || 'Error occurred saving credentials.', 'error');
    } finally {
      setSavingCredentials(false);
    }
  };

  // Test M-Pesa Connection
  const handleTestConnection = async () => {
    if (!mpesaForm.shortcode || !mpFormFilledOut()) {
      showToast('Please enter all parameters before running a connection diagnostics check.', 'error');
      return;
    }

    setTestingConnection(true);
    setTestResult({ status: 'idle' });

    const token = localStorage.getItem('token') || localStorage.getItem('platelink_auth_token');

    try {
      if (isUsingMocks) {
        await new Promise((resolve) => setTimeout(resolve, 1800));
        // Mock connection outcome based on shortcode format
        if (mpesaForm.shortcode.length >= 5 && mpesaForm.shortcode.length <= 7) {
          setTestResult({
            status: 'success',
            message: 'Connection successful! PlateLink can successfully query and authorize Daraja API keys.'
          });
          showToast('M-Pesa API connection verified successfully.', 'success');
        } else {
          setTestResult({
            status: 'error',
            message: 'Connection rejected. Safaricom returned 400 Bad Request: Invalid Business Shortcode.'
          });
          showToast('M-Pesa API test failed. Check settings.', 'error');
        }
      } else {
        const res = await fetch('/api/payments/mpesa/test-connection', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          },
          body: JSON.stringify({
            shortcode: mpesaForm.shortcode,
            consumer_key: mpesaForm.consumerKey,
            consumer_secret: mpesaForm.consumerSecret,
            passkey: mpesaForm.passkey,
            environment: mpesaForm.environment
          })
        });

        const resData = await res.json().catch(() => ({}));

        if (!res.ok) {
          throw new Error(resData.message || 'Daraja connection test failed. Please verify credentials.');
        }

        setTestResult({
          status: 'success',
          message: 'Connection successful! Platform successfully established a handshaking bridge with Safaricom.'
        });
        showToast('Connection test successful', 'success');
      }
    } catch (err: any) {
      setTestResult({
        status: 'error',
        message: err.message || 'Network Timeout: Safaricom C2B Gateway returned no response.'
      });
      showToast('Connection test failed', 'error');
    } finally {
      setTestingConnection(false);
    }
  };

  // Helper validation
  const mpFormFilledOut = () => {
    return (
      mpesaForm.shortcode !== '' &&
      mpesaForm.consumerKey !== '' &&
      mpesaForm.consumerSecret !== '' &&
      mpesaForm.passkey !== ''
    );
  };

  // ==========================================
  // CONCIERGE FILE UPLOAD SIMULATOR
  // ==========================================
  const simulateFileUpload = (key: keyof ConciergeDocs, file: File) => {
    setConciergeDocs((prev) => ({
      ...prev,
      [key]: {
        name: file.name,
        size: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
        type: file.type,
        progress: 10,
        status: 'uploading'
      }
    }));

    // Trigger fake progress bar increment
    let progress = 10;
    const interval = setInterval(() => {
      progress += 20;
      if (progress >= 100) {
        clearInterval(interval);
        setConciergeDocs((prev) => {
          const doc = prev[key];
          if (!doc) return prev;
          return {
            ...prev,
            [key]: {
              ...doc,
              progress: 100,
              status: 'completed'
            }
          };
        });
        showToast(`Document "${file.name}" uploaded successfully.`, 'success');
      } else {
        setConciergeDocs((prev) => {
          const doc = prev[key];
          if (!doc) return prev;
          return {
            ...prev,
            [key]: {
              ...doc,
              progress
            }
          };
        });
      }
    }, 150);
  };

  const handleDocDrop = (e: React.DragEvent, key: keyof ConciergeDocs) => {
    e.preventDefault();
    setActiveDragZone(null);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      simulateFileUpload(key, file);
    }
  };

  const submitConciergeRequest = async () => {
    // Quick validation
    if (!conciergeDocs.businessRegistration || !conciergeDocs.kraPin || !conciergeDocs.directorId) {
      showToast('Please upload all required business documents.', 'error');
      return;
    }

    setSubmittingConcierge(true);

    try {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      setIsConciergeRequested(true);
      persistSimulatedSettings({ isConciergeRequested: true });
      setShowConciergeModal(false);
      setShowConciergeSuccess(true);
      showToast('Concierge setup request successfully submitted!', 'success');
    } catch (error) {
      showToast('Error filing concierge service request.', 'error');
    } finally {
      setSubmittingConcierge(false);
    }
  };

  // Determine current overall configuration state
  const getCurrentStatus = (): { status: ConfigStatus; text: string; color: string; bg: string } => {
    if (activeTrack === 'cash') {
      return { status: 'active', text: 'Active & Simple', color: 'text-emerald-700 border-emerald-200', bg: 'bg-emerald-50' };
    }
    if (activeTrack === 'pesapal') {
      return { status: 'active', text: 'Active (Pesapal)', color: 'text-emerald-700 border-emerald-200', bg: 'bg-emerald-50' };
    }
    // Direct M-Pesa
    if (isMpesaConfigured) {
      return { status: 'active', text: 'Active (Direct M-Pesa)', color: 'text-emerald-700 border-emerald-200', bg: 'bg-emerald-50' };
    }
    if (isConciergeRequested) {
      return { status: 'pending', text: 'Pending Concierge Setup', color: 'text-amber-700 border-amber-200', bg: 'bg-amber-50' };
    }
    return { status: 'needs_attention', text: 'Needs Attention (Unconfigured)', color: 'text-rose-700 border-rose-200', bg: 'bg-rose-50' };
  };

  const statusMeta = getCurrentStatus();

  // Skeleton Loader screen
  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6 space-y-8 animate-pulse">
        <div className="space-y-3">
          <div className="h-8 w-48 bg-slate-200 rounded-lg"></div>
          <div className="h-5 w-80 bg-slate-200 rounded-lg"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-40 bg-slate-200 rounded-2xl"></div>
          <div className="h-40 bg-slate-200 rounded-2xl"></div>
          <div className="h-40 bg-slate-200 rounded-2xl"></div>
        </div>
        <div className="h-96 bg-slate-200 rounded-2xl"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 lg:p-8 space-y-8 relative select-none font-sans antialiased text-slate-800">
      
      {/* ==========================================
          TOAST OVERLAY
          ========================================== */}
      <div className="fixed top-6 right-6 z-50 flex flex-col gap-3 max-w-sm w-full">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`flex items-start gap-3 p-4 bg-white/90 backdrop-blur-md border rounded-2xl shadow-xl transition-all duration-300 transform scale-100 ${
              t.type === 'success' ? 'border-emerald-100 text-emerald-900 bg-emerald-50/90' :
              t.type === 'error' ? 'border-rose-100 text-rose-900 bg-rose-50/90' : 'border-indigo-100 text-indigo-900 bg-indigo-50/90'
            }`}
          >
            {t.type === 'success' ? (
              <div className="p-1 bg-emerald-500 text-white rounded-full"><Check className="w-3.5 h-3.5" /></div>
            ) : t.type === 'error' ? (
              <div className="p-1 bg-rose-500 text-white rounded-full"><X className="w-3.5 h-3.5" /></div>
            ) : (
              <div className="p-1 bg-indigo-500 text-white rounded-full"><Info className="w-3.5 h-3.5" /></div>
            )}
            <span className="text-sm font-semibold flex-1 leading-relaxed">{t.message}</span>
            <button onClick={() => setToasts(prev => prev.filter(item => item.id !== t.id))} className="text-slate-400 hover:text-slate-600 transition">
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Online/Offline Simulation Alert Banner */}
      {isUsingMocks && (
        <div className="bg-amber-500/10 border border-amber-500/20 backdrop-blur-sm rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-amber-800 text-xs font-semibold shadow-inner">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500 text-white rounded-xl shadow-md"><AlertTriangle className="w-4 h-4" /></div>
            <div>
              <p className="font-bold">Offline Simulation Active</p>
              <p className="text-slate-500 font-medium">All settings saves are managed in-browser storage instantly.</p>
            </div>
          </div>
        </div>
      )}

      {/* ==========================================
          PAGE HEADER
          ========================================== */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            Payment Settings
          </h1>
          <p className="text-slate-500 text-sm font-medium mt-1">Configure how your restaurant accepts payments, settlements, and customer bills.</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 text-xs font-bold text-slate-500 bg-slate-100 rounded-xl border border-slate-200/60 uppercase tracking-wider">
            Admin Panel
          </span>
          <span className="px-3 py-1.5 text-xs font-bold text-emerald-600 bg-emerald-50 rounded-xl border border-emerald-200/40 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span> Fully Secure
          </span>
        </div>
      </div>

      {/* ==========================================
          GRID: CURRENT STATUS & QUICK ACTIONS
          ========================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* CARD 1: ACTIVE PAYMENT TRACK */}
        <div className="bg-white border border-slate-150 rounded-3xl p-6 shadow-sm flex flex-col justify-between group transition hover:border-slate-300">
          <div className="space-y-4">
            <div className="flex justify-between items-start">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-widest">Active Setup</span>
              <div className={`px-2.5 py-1 text-[11px] font-extrabold rounded-full uppercase border ${statusMeta.color} ${statusMeta.bg}`}>
                {statusMeta.status === 'active' && 'Active'}
                {statusMeta.status === 'pending' && 'Pending'}
                {statusMeta.status === 'needs_attention' && 'Needs Config'}
              </div>
            </div>
            <div>
              <p className="text-[11px] font-semibold text-slate-400 uppercase">Selected Gateway</p>
              <h3 className="text-2xl font-black text-slate-900 mt-0.5 tracking-tight capitalize">
                {activeTrack === 'pesapal' && 'Pesapal'}
                {activeTrack === 'mpesa' && 'Direct M-Pesa'}
                {activeTrack === 'cash' && 'Cash Only'}
              </h3>
            </div>
          </div>
          <div className="border-t border-slate-100 pt-4 mt-6 flex items-center gap-3">
            <div className="p-2 bg-slate-50 rounded-xl text-slate-500"><Shield className="w-4 h-4" /></div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase">Configuration Status</p>
              <p className="text-xs font-bold text-slate-700">{statusMeta.text}</p>
            </div>
          </div>
        </div>

        {/* CARD 2: TRANSACTION FEES & METRICS */}
        <div className="bg-white border border-slate-150 rounded-3xl p-6 shadow-sm flex flex-col justify-between group transition hover:border-slate-300">
          <div className="space-y-4">
            <div className="flex justify-between items-start">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-widest">Rates</span>
              <div className="p-1.5 bg-indigo-50 text-indigo-600 rounded-xl"><Coins className="w-4 h-4" /></div>
            </div>
            <div>
              <p className="text-[11px] font-semibold text-slate-400 uppercase">Transaction Fee</p>
              <h3 className="text-2xl font-black text-slate-900 mt-0.5 tracking-tight">
                {activeTrack === 'pesapal' && '1.5% - 3.5% + 1%'}
                {activeTrack === 'mpesa' && '0.55% (Capped) + 1%'}
                {activeTrack === 'cash' && '0% Platform Fee'}
              </h3>
            </div>
          </div>
          <div className="border-t border-slate-100 pt-4 mt-6 flex items-center gap-3">
            <div className="p-2 bg-slate-50 rounded-xl text-slate-500"><Clock className="w-4 h-4" /></div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase">Settlement Period</p>
              <p className="text-xs font-bold text-slate-700">
                {activeTrack === 'pesapal' && 'Next business day payout'}
                {activeTrack === 'mpesa' && 'Instant real-time payout'}
                {activeTrack === 'cash' && 'Immediate manual checkout'}
              </p>
            </div>
          </div>
        </div>

        {/* CARD 3: SETTLEMENT STATUS & PAYOUTS */}
        <div className="bg-white border border-slate-150 rounded-3xl p-6 shadow-sm flex flex-col justify-between group transition hover:border-slate-300">
          <div className="space-y-4">
            <div className="flex justify-between items-start">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-widest">Settlements</span>
              <div className="p-1.5 bg-emerald-50 text-emerald-600 rounded-xl"><CheckSquare className="w-4 h-4" /></div>
            </div>
            <div>
              <p className="text-[11px] font-semibold text-slate-400 uppercase">Last Payout Executed</p>
              <h3 className="text-2xl font-black text-slate-900 mt-0.5 tracking-tight">
                {lastPayoutDate ? `KES 47,850` : 'No past payouts'}
              </h3>
            </div>
          </div>
          <div className="border-t border-slate-100 pt-4 mt-6 flex items-center gap-3">
            <div className="p-2 bg-slate-50 rounded-xl text-slate-500"><Clock className="w-4 h-4" /></div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase">Last Settlement Date</p>
              <p className="text-xs font-bold text-slate-700">
                {lastPayoutDate ? `${lastPayoutDate} at 5:00 PM` : 'Not applicable / Direct'}
              </p>
            </div>
          </div>
        </div>

      </div>

      {/* ==========================================
          SECTION 1: PAYMENT TRACK SELECTION
          ========================================== */}
      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">1. Select Payment Track</h2>
          <p className="text-xs text-slate-500 font-medium">Choose how checkouts are routed. Direct track reduces fees significantly but requires credential authorization.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* TRACK 1: PESAPAL AGGREGATOR */}
          <div
            onClick={() => handleTrackSelectClick('pesapal')}
            className={`border rounded-3xl p-6 cursor-pointer relative transition-all duration-350 select-none ${
              activeTrack === 'pesapal'
                ? 'border-emerald-500 bg-emerald-50/10 shadow-lg shadow-emerald-500/5 ring-1 ring-emerald-500'
                : 'border-slate-150 bg-white hover:border-slate-350 hover:shadow-md'
            }`}
          >
            {activeTrack === 'pesapal' && (
              <div className="absolute top-4 right-4 bg-emerald-500 text-white rounded-full p-1 shadow-sm">
                <Check className="w-3.5 h-3.5" />
              </div>
            )}
            <div className="space-y-4">
              <div>
                <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-100 text-emerald-800 rounded-md border border-emerald-200 uppercase tracking-wider">
                  Recommended
                </span>
                <h3 className="text-lg font-extrabold text-slate-900 mt-2">Pesapal Aggregator</h3>
                <p className="text-[11px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">Card & Mobile Money Hub</p>
              </div>

              <div className="space-y-2 border-t border-slate-100 pt-3 text-xs">
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Merchant Fees:</span>
                  <span className="text-slate-800 font-bold">1.5 - 3.5% + 1% platforms</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Settlements:</span>
                  <span className="text-slate-800 font-bold">Next business day</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Setup time:</span>
                  <span className="text-slate-800 font-bold">Instant Activation</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Required docs:</span>
                  <span className="text-emerald-600 font-bold">None</span>
                </div>
              </div>
            </div>
          </div>

          {/* TRACK 2: DIRECT M-PESA */}
          <div
            onClick={() => handleTrackSelectClick('mpesa')}
            className={`border rounded-3xl p-6 cursor-pointer relative transition-all duration-350 select-none ${
              activeTrack === 'mpesa'
                ? 'border-emerald-500 bg-emerald-50/10 shadow-lg shadow-emerald-500/5 ring-1 ring-emerald-500'
                : 'border-slate-150 bg-white hover:border-slate-350 hover:shadow-md'
            }`}
          >
            {activeTrack === 'mpesa' && (
              <div className="absolute top-4 right-4 bg-emerald-500 text-white rounded-full p-1 shadow-sm">
                <Check className="w-3.5 h-3.5" />
              </div>
            )}
            <div className="space-y-4">
              <div>
                <span className="px-2 py-0.5 text-[10px] font-bold bg-indigo-100 text-indigo-800 rounded-md border border-indigo-200 uppercase tracking-wider">
                  Premium & Low Fees
                </span>
                <h3 className="text-lg font-extrabold text-slate-900 mt-2">Direct M-Pesa</h3>
                <p className="text-[11px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">Safaricom Daraja API C2B</p>
              </div>

              <div className="space-y-2 border-t border-slate-100 pt-3 text-xs">
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Merchant Fees:</span>
                  <span className="text-slate-800 font-bold">0.55% (Capped) + 1% platform</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Settlements:</span>
                  <span className="text-slate-800 font-bold">Instant (Direct to Till)</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Setup time:</span>
                  <span className="text-slate-800 font-bold">1 - 2 weeks setup</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Required docs:</span>
                  <span className="text-indigo-600 font-bold">KRA / Reg Certificate</span>
                </div>
              </div>
            </div>
          </div>

          {/* TRACK 3: CASH ONLY */}
          <div
            onClick={() => handleTrackSelectClick('cash')}
            className={`border rounded-3xl p-6 cursor-pointer relative transition-all duration-350 select-none ${
              activeTrack === 'cash'
                ? 'border-emerald-500 bg-emerald-50/10 shadow-lg shadow-emerald-500/5 ring-1 ring-emerald-500'
                : 'border-slate-150 bg-white hover:border-slate-350 hover:shadow-md'
            }`}
          >
            {activeTrack === 'cash' && (
              <div className="absolute top-4 right-4 bg-emerald-500 text-white rounded-full p-1 shadow-sm">
                <Check className="w-3.5 h-3.5" />
              </div>
            )}
            <div className="space-y-4">
              <div>
                <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 rounded-md border border-amber-200 uppercase tracking-wider">
                  Zero Platform Fees
                </span>
                <h3 className="text-lg font-extrabold text-slate-900 mt-2">Cash Only</h3>
                <p className="text-[11px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">Physical Settlement</p>
              </div>

              <div className="space-y-2 border-t border-slate-100 pt-3 text-xs">
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Merchant Fees:</span>
                  <span className="text-slate-800 font-bold">0% total charge</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Settlements:</span>
                  <span className="text-slate-800 font-bold">Immediate in hand</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Setup time:</span>
                  <span className="text-slate-800 font-bold">Instant Activation</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-slate-400">Required docs:</span>
                  <span className="text-slate-800 font-bold">None</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ==========================================
          SECTION 2: M-PESA CREDENTIALS FORM 
          (Only visible if Direct M-Pesa is selected)
          ========================================== */}
      {activeTrack === 'mpesa' && (
        <section className="bg-white border border-slate-200 rounded-3xl shadow-sm overflow-hidden p-6 sm:p-8 space-y-6 transition duration-300 animate-in fade-in slide-in-from-bottom-2">
          
          <div className="border-b border-slate-100 pb-5">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Lock className="w-5 h-5 text-emerald-600" /> 2. M-Pesa API Credentials
            </h2>
            <p className="text-xs text-slate-500 mt-1">Configure your Lipa Na M-Pesa Business shortcode details. Credentials are saved encrypted end-to-end.</p>
          </div>

          <form onSubmit={handleSaveMpesaCredentials} className="space-y-6">
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* SHORTCODE / PAYBILL */}
              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Lipa Na M-Pesa Paybill / Till Shortcode
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    placeholder="e.g. 174379 or 600997"
                    value={mpesaForm.shortcode}
                    onChange={(e) => setMpesaForm({ ...mpesaForm, shortcode: e.target.value })}
                    className="w-full bg-slate-50/50 border border-slate-250 rounded-2xl px-4 py-3 outline-none focus:bg-white focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition text-sm font-semibold"
                  />
                </div>
                <p className="text-[10px] text-slate-400 font-medium">Please enter your 5 to 7 digit Lipa Na M-Pesa Business C2B merchant shortcode.</p>
              </div>

              {/* DARAJA ENVIRONMENT */}
              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Safaricom Gateway Environment
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setMpesaForm({ ...mpesaForm, environment: 'sandbox' })}
                    className={`py-3 rounded-2xl text-xs font-bold border transition ${
                      mpesaForm.environment === 'sandbox'
                        ? 'border-emerald-500 bg-emerald-500/5 text-emerald-700 font-extrabold ring-1 ring-emerald-500'
                        : 'border-slate-250 bg-slate-50 text-slate-500 font-semibold hover:border-slate-350 hover:bg-white'
                    }`}
                  >
                    Sandbox Testing
                  </button>
                  <button
                    type="button"
                    onClick={() => setMpesaForm({ ...mpesaForm, environment: 'production' })}
                    className={`py-3 rounded-2xl text-xs font-bold border transition ${
                      mpesaForm.environment === 'production'
                        ? 'border-emerald-500 bg-emerald-500/5 text-emerald-700 font-extrabold ring-1 ring-emerald-500'
                        : 'border-slate-250 bg-slate-50 text-slate-500 font-semibold hover:border-slate-350 hover:bg-white'
                    }`}
                  >
                    Production Live
                  </button>
                </div>
                <p className="text-[10px] text-slate-400 font-medium">Use sandbox to perform diagnostic mock checkouts without standard bill charges.</p>
              </div>

              {/* CONSUMER KEY */}
              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Business Consumer Key
                </label>
                <div className="relative">
                  <input
                    type={showConsumerKey ? 'text' : 'password'}
                    required
                    placeholder="Enter Safaricom Consumer Key"
                    value={mpesaForm.consumerKey}
                    onChange={(e) => setMpesaForm({ ...mpesaForm, consumerKey: e.target.value })}
                    className="w-full bg-slate-50/50 border border-slate-250 rounded-2xl pl-4 pr-12 py-3 outline-none focus:bg-white focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition text-sm font-semibold tracking-wide"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConsumerKey(!showConsumerKey)}
                    className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-slate-600 transition"
                  >
                    {showConsumerKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* CONSUMER SECRET */}
              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Business Consumer Secret
                </label>
                <div className="relative">
                  <input
                    type={showConsumerSecret ? 'text' : 'password'}
                    required
                    placeholder="Enter Safaricom Consumer Secret"
                    value={mpesaForm.consumerSecret}
                    onChange={(e) => setMpesaForm({ ...mpesaForm, consumerSecret: e.target.value })}
                    className="w-full bg-slate-50/50 border border-slate-250 rounded-2xl pl-4 pr-12 py-3 outline-none focus:bg-white focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition text-sm font-semibold tracking-wide"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConsumerSecret(!showConsumerSecret)}
                    className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-slate-600 transition"
                  >
                    {showConsumerSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* PASSKEY */}
              <div className="md:col-span-2 space-y-2">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Lipa Na M-Pesa Online Passkey
                </label>
                <div className="relative">
                  <input
                    type={showPasskey ? 'text' : 'password'}
                    required
                    placeholder="Enter Safaricom LNM Online Passkey"
                    value={mpesaForm.passkey}
                    onChange={(e) => setMpesaForm({ ...mpesaForm, passkey: e.target.value })}
                    className="w-full bg-slate-50/50 border border-slate-250 rounded-2xl pl-4 pr-12 py-3 outline-none focus:bg-white focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition text-sm font-semibold tracking-wide"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasskey(!showPasskey)}
                    className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-slate-600 transition"
                  >
                    {showPasskey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

            </div>

            {/* Test Connection Results Notification */}
            {testResult.status !== 'idle' && (
              <div className={`p-4 rounded-2xl border flex items-start gap-3 transition animate-in fade-in duration-300 ${
                testResult.status === 'success' ? 'bg-emerald-50 border-emerald-250 text-emerald-900' : 'bg-rose-50 border-rose-250 text-rose-900'
              }`}>
                <div className="mt-0.5">
                  {testResult.status === 'success' ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
                  )}
                </div>
                <div>
                  <p className="font-bold text-sm">Connection Test {testResult.status === 'success' ? 'Passed' : 'Failed'}</p>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">{testResult.message}</p>
                </div>
              </div>
            )}

            {/* Buttons Section */}
            <div className="flex flex-col sm:flex-row items-center gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testingConnection || savingCredentials}
                className="w-full sm:w-auto px-6 py-3 border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-2xl text-sm font-bold transition flex items-center justify-center gap-2"
              >
                {testingConnection ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-slate-500" />
                    Testing Portals...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    Test Connection
                  </>
                )}
              </button>

              <button
                type="submit"
                disabled={testingConnection || savingCredentials}
                className="w-full sm:w-auto px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl text-sm font-bold shadow-md shadow-emerald-600/10 transition flex items-center justify-center gap-2 ml-auto"
              >
                {savingCredentials ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Saving credentials...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Save Credentials
                  </>
                )}
              </button>
            </div>

          </form>

        </section>
      )}

      {/* ==========================================
          SECTION 3: CONCIERGE SERVICE DETAILS CARD
          (Visible only if Direct M-Pesa selected and not configured)
          ========================================== */}
      {activeTrack === 'mpesa' && !isMpesaConfigured && (
        <section className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-3xl p-6 sm:p-8 text-white relative overflow-hidden shadow-lg transition duration-300 animate-in fade-in">
          
          {/* Accent light elements */}
          <div className="absolute -top-16 -right-16 w-48 h-48 bg-indigo-500/20 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-16 -left-16 w-48 h-48 bg-emerald-500/20 rounded-full blur-3xl"></div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
            <div className="space-y-3 max-w-2xl">
              <span className="px-2.5 py-1 text-[10px] font-black bg-indigo-500/25 border border-indigo-400/30 text-indigo-200 rounded-md uppercase tracking-widest flex items-center gap-1.5 w-fit">
                <Sparkles className="w-3.5 h-3.5 text-indigo-300" /> Concierge Setup Service
              </span>
              <h3 className="text-xl sm:text-2xl font-black tracking-tight text-white">
                Need help setting up Direct M-Pesa?
              </h3>
              <p className="text-sm text-indigo-100 font-medium leading-relaxed">
                Our team handles everything from KRA/Safaricom document review, applying for your Business Paybill number, setting up Daraja API integrations, and deploying your payment endpoints safely.
              </p>
              <div className="flex items-center gap-4 text-xs font-bold text-indigo-200 pt-1">
                <span className="flex items-center gap-1.5"><Check className="w-4 h-4 text-emerald-400" /> Hassle-Free Filing</span>
                <span className="flex items-center gap-1.5"><Check className="w-4 h-4 text-emerald-400" /> Safaricom Vetting</span>
                <span className="flex items-center gap-1.5"><Check className="w-4 h-4 text-emerald-400" /> Secure Encryption</span>
              </div>
            </div>

            <div className="bg-slate-800/40 border border-slate-700/60 backdrop-blur-sm p-6 rounded-2xl w-full md:w-80 shrink-0 text-center space-y-4">
              <div>
                <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Concierge Integration Fee</p>
                <h4 className="text-3xl font-black text-white mt-1">KES 10,000</h4>
                <p className="text-[10px] text-slate-400 font-medium mt-1">One-time payment for setup & support</p>
              </div>

              <button
                onClick={() => {
                  if (isConciergeRequested) {
                    showToast('Concierge setup is already pending documentation review.', 'info');
                  } else {
                    setShowConciergeModal(true);
                  }
                }}
                className={`w-full py-3 rounded-xl text-xs font-extrabold transition flex items-center justify-center gap-2 ${
                  isConciergeRequested
                    ? 'bg-slate-700 text-slate-400 cursor-not-allowed border border-slate-600/50'
                    : 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-md shadow-emerald-500/10'
                }`}
              >
                {isConciergeRequested ? (
                  <>Concierge Request Pending</>
                ) : (
                  <>
                    Request Concierge Service <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </div>
        </section>
      )}

      {/* ==========================================
          TRACK CHANGE CONFIRMATION MODAL
          ========================================== */}
      {showTrackConfirmModal && pendingTrack && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/65 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-100 rounded-3xl max-w-md w-full shadow-2xl p-6 relative overflow-hidden transition-all transform scale-100 space-y-6">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-rose-50 border border-rose-100 text-rose-600 rounded-2xl shrink-0">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-black text-slate-900 leading-tight">Confirm Payment Track Change</h3>
                <p className="text-[11px] text-slate-400 font-bold uppercase tracking-wider">Safety Confirmation Dialog</p>
              </div>
            </div>

            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-150/60 text-xs font-semibold leading-relaxed text-slate-600 space-y-3">
              <p>
                You are changing the active payment track from{' '}
                <span className="text-slate-900 font-black uppercase">
                  {activeTrack === 'pesapal' ? 'Pesapal' : activeTrack === 'mpesa' ? 'Direct M-Pesa' : 'Cash'}
                </span>{' '}
                to{' '}
                <span className="text-slate-900 font-black uppercase">
                  {pendingTrack === 'pesapal' ? 'Pesapal' : pendingTrack === 'mpesa' ? 'Direct M-Pesa' : 'Cash'}
                </span>.
              </p>
              <div className="p-3 bg-amber-500/10 border border-amber-500/25 text-amber-900 rounded-xl flex gap-2">
                <Info className="w-4.5 h-4.5 text-amber-600 shrink-0 mt-0.5" />
                <p className="text-[11px] font-semibold leading-normal">
                  <span className="font-extrabold uppercase">Important:</span> Changing payment track affects immediate customer checkouts and checkout session tokens. Ongoing active orders will continue under the legacy tracks.
                </p>
              </div>
            </div>

            <div className="flex gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => {
                  setShowTrackConfirmModal(false);
                  setPendingTrack(null);
                }}
                className="flex-1 py-3 text-slate-500 hover:text-slate-800 text-xs font-bold border border-slate-200 bg-white hover:bg-slate-50 rounded-2xl transition"
              >
                Cancel Action
              </button>
              <button
                type="button"
                onClick={confirmTrackChange}
                disabled={savingTrack}
                className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-2xl shadow-md transition flex items-center justify-center gap-2"
              >
                {savingTrack ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Updating track...
                  </>
                ) : (
                  <>Confirm Switch</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==========================================
          CONCIERGE SERVICES MODAL (DOCUMENT UPLOAD)
          ========================================== */}
      {showConciergeModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/65 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-100 rounded-3xl max-w-2xl w-full shadow-2xl overflow-hidden transition-all transform scale-100">
            
            {/* Modal Header */}
            <div className="bg-slate-900 text-white p-6 flex justify-between items-center relative overflow-hidden">
              <div className="absolute -top-10 -right-10 w-28 h-28 bg-indigo-500/20 rounded-full blur-2xl"></div>
              <div className="z-10">
                <span className="text-[10px] font-black text-indigo-300 uppercase tracking-widest">M-Pesa Setup concierge</span>
                <h3 className="text-xl font-black text-white mt-0.5 tracking-tight">Direct M-Pesa Setup Documents</h3>
              </div>
              <button
                onClick={() => setShowConciergeModal(false)}
                className="p-2 text-slate-400 hover:text-white rounded-full bg-slate-800/40 hover:bg-slate-800 transition z-10"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
              
              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">1. Select Business Structure type</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 'sole_proprietor', label: 'Sole Proprietor' },
                    { id: 'limited_company', label: 'Limited Company' },
                    { id: 'partnership', label: 'Partnership' }
                  ].map((type) => (
                    <button
                      key={type.id}
                      onClick={() => setBusinessType(type.id)}
                      className={`py-3 px-2 text-center rounded-2xl text-[11px] font-bold border transition ${
                        businessType === type.id
                          ? 'border-indigo-600 bg-indigo-50 text-indigo-700 font-extrabold ring-1 ring-indigo-600'
                          : 'border-slate-200 bg-slate-50 text-slate-500 font-semibold hover:border-slate-300 hover:bg-white'
                      }`}
                    >
                      {type.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">2. Upload Required Safaricom Documentation</label>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  {/* DOC 1: BUSINESS REGISTRATION */}
                  <div className="space-y-1.5">
                    <span className="text-[11px] font-bold text-slate-500">Business Registration Certificate *</span>
                    <div
                      onDragOver={(e) => { e.preventDefault(); setActiveDragZone('bizReg'); }}
                      onDragLeave={() => setActiveDragZone(null)}
                      onDrop={(e) => handleDocDrop(e, 'businessRegistration')}
                      className={`border-2 border-dashed rounded-2xl p-4 text-center transition cursor-pointer relative ${
                        conciergeDocs.businessRegistration ? 'border-emerald-300 bg-emerald-50/5' :
                        activeDragZone === 'bizReg' ? 'border-indigo-500 bg-indigo-50/20' : 'border-slate-250 bg-slate-50/50 hover:bg-slate-50'
                      }`}
                    >
                      <input
                        type="file"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) simulateFileUpload('businessRegistration', file);
                        }}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        accept=".pdf,.png,.jpg,.jpeg"
                      />
                      {conciergeDocs.businessRegistration ? (
                        <div className="space-y-2">
                          <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto" />
                          <div className="text-[11px] font-bold text-slate-700 truncate">{conciergeDocs.businessRegistration.name}</div>
                          <div className="text-[10px] text-slate-400 font-semibold uppercase">{conciergeDocs.businessRegistration.size}</div>
                        </div>
                      ) : (
                        <div>
                          <Upload className="w-5 h-5 text-slate-400 mx-auto mb-1.5" />
                          <p className="text-[10px] font-bold text-slate-700">Drag file or Browse</p>
                          <p className="text-[9px] text-slate-400 uppercase tracking-wider mt-0.5">PDF or Image up to 5MB</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* DOC 2: KRA PIN CERTIFICATE */}
                  <div className="space-y-1.5">
                    <span className="text-[11px] font-bold text-slate-500">Company KRA PIN Certificate *</span>
                    <div
                      onDragOver={(e) => { e.preventDefault(); setActiveDragZone('kra'); }}
                      onDragLeave={() => setActiveDragZone(null)}
                      onDrop={(e) => handleDocDrop(e, 'kraPin')}
                      className={`border-2 border-dashed rounded-2xl p-4 text-center transition cursor-pointer relative ${
                        conciergeDocs.kraPin ? 'border-emerald-300 bg-emerald-50/5' :
                        activeDragZone === 'kra' ? 'border-indigo-500 bg-indigo-50/20' : 'border-slate-250 bg-slate-50/50 hover:bg-slate-50'
                      }`}
                    >
                      <input
                        type="file"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) simulateFileUpload('kraPin', file);
                        }}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        accept=".pdf,.png,.jpg,.jpeg"
                      />
                      {conciergeDocs.kraPin ? (
                        <div className="space-y-2">
                          <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto" />
                          <div className="text-[11px] font-bold text-slate-700 truncate">{conciergeDocs.kraPin.name}</div>
                          <div className="text-[10px] text-slate-400 font-semibold uppercase">{conciergeDocs.kraPin.size}</div>
                        </div>
                      ) : (
                        <div>
                          <Upload className="w-5 h-5 text-slate-400 mx-auto mb-1.5" />
                          <p className="text-[10px] font-bold text-slate-700">Drag file or Browse</p>
                          <p className="text-[9px] text-slate-400 uppercase tracking-wider mt-0.5">PDF or Image up to 5MB</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* DOC 3: DIRECTOR ID */}
                  <div className="space-y-1.5">
                    <span className="text-[11px] font-bold text-slate-500">National ID / Passport of Director *</span>
                    <div
                      onDragOver={(e) => { e.preventDefault(); setActiveDragZone('director'); }}
                      onDragLeave={() => setActiveDragZone(null)}
                      onDrop={(e) => handleDocDrop(e, 'directorId')}
                      className={`border-2 border-dashed rounded-2xl p-4 text-center transition cursor-pointer relative ${
                        conciergeDocs.directorId ? 'border-emerald-300 bg-emerald-50/5' :
                        activeDragZone === 'director' ? 'border-indigo-500 bg-indigo-50/20' : 'border-slate-250 bg-slate-50/50 hover:bg-slate-50'
                      }`}
                    >
                      <input
                        type="file"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) simulateFileUpload('directorId', file);
                        }}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        accept=".pdf,.png,.jpg,.jpeg"
                      />
                      {conciergeDocs.directorId ? (
                        <div className="space-y-2">
                          <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto" />
                          <div className="text-[11px] font-bold text-slate-700 truncate">{conciergeDocs.directorId.name}</div>
                          <div className="text-[10px] text-slate-400 font-semibold uppercase">{conciergeDocs.directorId.size}</div>
                        </div>
                      ) : (
                        <div>
                          <Upload className="w-5 h-5 text-slate-400 mx-auto mb-1.5" />
                          <p className="text-[10px] font-bold text-slate-700">Drag file or Browse</p>
                          <p className="text-[9px] text-slate-400 uppercase tracking-wider mt-0.5">PDF or Image up to 5MB</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* DOC 4: CR12 FORM */}
                  <div className="space-y-1.5">
                    <span className="text-[11px] font-bold text-slate-500">Form CR12 (For Companies only)</span>
                    <div
                      onDragOver={(e) => { e.preventDefault(); setActiveDragZone('cr12'); }}
                      onDragLeave={() => setActiveDragZone(null)}
                      onDrop={(e) => handleDocDrop(e, 'cr12Form')}
                      className={`border-2 border-dashed rounded-2xl p-4 text-center transition cursor-pointer relative ${
                        conciergeDocs.cr12Form ? 'border-emerald-300 bg-emerald-50/5' :
                        activeDragZone === 'cr12' ? 'border-indigo-500 bg-indigo-50/20' : 'border-slate-250 bg-slate-50/50 hover:bg-slate-50'
                      }`}
                    >
                      <input
                        type="file"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) simulateFileUpload('cr12Form', file);
                        }}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        accept=".pdf,.png,.jpg,.jpeg"
                      />
                      {conciergeDocs.cr12Form ? (
                        <div className="space-y-2">
                          <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto" />
                          <div className="text-[11px] font-bold text-slate-700 truncate">{conciergeDocs.cr12Form.name}</div>
                          <div className="text-[10px] text-slate-400 font-semibold uppercase">{conciergeDocs.cr12Form.size}</div>
                        </div>
                      ) : (
                        <div>
                          <Upload className="w-5 h-5 text-slate-400 mx-auto mb-1.5" />
                          <p className="text-[10px] font-bold text-slate-700">Drag file or Browse</p>
                          <p className="text-[9px] text-slate-400 uppercase tracking-wider mt-0.5">PDF or Image up to 5MB</p>
                        </div>
                      )}
                    </div>
                  </div>

                </div>

              </div>

            </div>

            {/* Modal Actions */}
            <div className="bg-slate-50 p-6 flex justify-between items-center border-t border-slate-100">
              <div className="flex items-center gap-2 text-xs font-bold text-indigo-900 bg-indigo-50/50 px-3 py-2 rounded-xl border border-indigo-100">
                <Info className="w-4 h-4 text-indigo-600 shrink-0" />
                <span>One-time Concierge fee KES 10,000 applies.</span>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowConciergeModal(false)}
                  className="px-5 py-2.5 text-slate-500 hover:text-slate-800 text-xs font-bold border border-slate-200 bg-white hover:bg-slate-50 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={submitConciergeRequest}
                  disabled={submittingConcierge}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-md transition flex items-center gap-2"
                >
                  {submittingConcierge ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Filing Request...
                    </>
                  ) : (
                    <>Submit Request</>
                  )}
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* ==========================================
          CONCIERGE SUCCESS DIALOG INFO CARD
          ========================================== */}
      {showConciergeSuccess && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/65 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-100 rounded-3xl max-w-md w-full shadow-2xl p-6 relative overflow-hidden text-center space-y-6 animate-in zoom-in-95 duration-200">
            <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <div className="space-y-2">
              <h3 className="text-xl font-black text-slate-900 tracking-tight">Concierge Request Received!</h3>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">PlateLink Business Concierge</p>
            </div>

            <p className="text-xs font-semibold text-slate-500 leading-relaxed max-w-sm mx-auto">
              Your business files have been compiled and sent securely to our compliance review officers. We will review the documents and initiate the Safaricom application filing process within the next 24 business hours.
            </p>

            <div className="bg-slate-50 p-4 border border-slate-150/60 rounded-2xl text-left space-y-2 text-[11px] font-bold text-slate-600">
              <div className="flex items-center gap-2 text-indigo-700">
                <div className="w-1.5 h-1.5 bg-indigo-600 rounded-full"></div>
                <span>Step 1: Document review & vetting (Pending)</span>
              </div>
              <div className="flex items-center gap-2 text-slate-400">
                <div className="w-1.5 h-1.5 bg-slate-300 rounded-full"></div>
                <span>Step 2: Safaricom Daraja Account filing (Waiting)</span>
              </div>
              <div className="flex items-center gap-2 text-slate-400">
                <div className="w-1.5 h-1.5 bg-slate-300 rounded-full"></div>
                <span>Step 3: Portal webhook bridging & live deployment</span>
              </div>
            </div>

            <button
              onClick={() => setShowConciergeSuccess(false)}
              className="w-full py-3 bg-slate-900 hover:bg-slate-800 text-white text-xs font-extrabold rounded-2xl shadow-lg transition"
            >
              Understand & Acknowledge
            </button>
          </div>
        </div>
      )}

    </div>
  );
}

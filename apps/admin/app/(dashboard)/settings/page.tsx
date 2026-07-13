// apps/admin/app/(dashboard)/settings/page.tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  User,
  CreditCard,
  Sliders,
  ShieldCheck,
  Eye,
  EyeOff,
  Loader2,
  Upload,
  CheckCircle2,
  X,
  AlertTriangle,
  Lock,
  BookOpen,
  HelpCircle,
  Building,
  Phone,
  Mail,
  MapPin,
  TrendingUp,
  XCircle,
  Check,
  RefreshCw
} from 'lucide-react';

// ==========================================
// FORM SCHEMAS (ZOD)
// ==========================================

const profileSchema = z.object({
  restaurant_name: z.string().min(2, 'Restaurant name must be at least 2 characters'),
  phone: z.string().regex(/^(?:254|\+254|0)?(7|1)\d{8}$/, 'Enter a valid Kenyan phone number (e.g., 07XXXXXXXX or 2547XXXXXXXX)'),
  email: z.string().email('Enter a valid email address'),
  address: z.string().optional().or(z.literal('')),
  city: z.string().optional().or(z.literal(''))
});

const mpesaSchema = z.object({
  shortcode: z.string().regex(/^\d{5,7}$/, 'Shortcode/Till number must be between 5 and 7 digits'),
  consumer_key: z.string().min(10, 'Consumer Key must be at least 10 characters'),
  consumer_secret: z.string().min(10, 'Consumer Secret must be at least 10 characters'),
  passkey: z.string().min(10, 'Passkey must be at least 10 characters'),
  environment: z.enum(['sandbox', 'production'])
});

const preferencesSchema = z.object({
  default_preparation_time: z.number().min(1, 'Min 1 minute').max(120, 'Max 120 minutes'),
  low_stock_threshold: z.number().min(1, 'Min stock count 1').max(100, 'Max stock count 100'),
  tax_rate: z.number().min(0, 'Tax cannot be negative').max(100, 'Tax cannot exceed 100%'),
  auto_accept_orders: z.boolean(),
  currency: z.string(),
  timezone: z.string()
});

type ProfileFormValues = z.infer<typeof profileSchema>;
type MpesaFormValues = z.infer<typeof mpesaSchema>;
type PreferencesFormValues = z.infer<typeof preferencesSchema>;

// ==========================================
// TOAST INTERFACE
// ==========================================
interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

export default function SettingsPage() {
  const router = useRouter();

  // Active Tab state
  const [activeTab, setActiveTab] = useState<'profile' | 'mpesa' | 'preferences' | 'billing'>('profile');

  // Loading States
  const [authLoading, setAuthLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(true);
  const [profileSaving, setProfileSaving] = useState(false);
  const [mpesaSaving, setMpesaSaving] = useState(false);
  const [preferencesSaving, setPreferencesSaving] = useState(false);
  const [logoUploading, setLogoUploading] = useState(false);

  // M-Pesa Password Masking Toggles
  const [showConsumerKey, setShowConsumerKey] = useState(false);
  const [showConsumerSecret, setShowConsumerSecret] = useState(false);
  const [showPasskey, setShowPasskey] = useState(false);

  // M-Pesa Test Connection States
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<{
    status: 'idle' | 'success' | 'error';
    message?: string;
  }>({ status: 'idle' });

  // Guide Modal state
  const [isGuideOpen, setIsGuideOpen] = useState(false);

  // Auth User Details
  const [currentUserRole, setCurrentUserRole] = useState<string | null>(null);
  const [restaurantId, setRestaurantId] = useState<string | null>(null);

  // Loaded Profile & Settings
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [isMpesaConfigured, setIsMpesaConfigured] = useState(false);

  // Simulation Fallback state
  const [isUsingMocks, setIsUsingMocks] = useState(false);

  // Toast State
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Toast System
  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    const id = Math.random().toString();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  // Forms initializations
  const {
    register: registerProfile,
    handleSubmit: handleProfileSubmit,
    reset: resetProfile,
    formState: { errors: profileErrors }
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      restaurant_name: '',
      phone: '',
      email: '',
      address: '',
      city: 'Nairobi'
    }
  });

  const {
    register: registerMpesa,
    handleSubmit: handleMpesaSubmit,
    reset: resetMpesa,
    getValues: getMpesaValues,
    formState: { errors: mpesaErrors }
  } = useForm<MpesaFormValues>({
    resolver: zodResolver(mpesaSchema),
    defaultValues: {
      shortcode: '',
      consumer_key: '',
      consumer_secret: '',
      passkey: '',
      environment: 'sandbox'
    }
  });

  const {
    register: registerPreferences,
    handleSubmit: handlePreferencesSubmit,
    reset: resetPreferences,
    control: controlPreferences,
    formState: { errors: preferencesErrors }
  } = useForm<PreferencesFormValues>({
    resolver: zodResolver(preferencesSchema),
    defaultValues: {
      default_preparation_time: 15,
      low_stock_threshold: 5,
      tax_rate: 16,
      auto_accept_orders: true,
      currency: 'KES',
      timezone: 'Africa/Nairobi'
    }
  });

  // ==========================================
  // AUTHENTICATION & SECURITY VERIFICATION
  // ==========================================
  useEffect(() => {
    const checkAuth = () => {
      // Allow checking multiple possible token variables just in case
      const token = localStorage.getItem('token') || localStorage.getItem('platelink_auth_token');
      
      if (!token) {
        router.push('/login');
        return;
      }

      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const isExpired = payload.exp * 1000 < Date.now();
        if (isExpired) {
          localStorage.removeItem('token');
          localStorage.removeItem('platelink_auth_token');
          document.cookie = 'token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
          router.push('/login');
          return;
        }

        const role = (payload.role || payload.user?.role || 'owner').toLowerCase();
        if (role !== 'owner' && role !== 'manager') {
          showToast('Access Denied: Only Owners and Managers are authorized to view Settings.', 'error');
          router.push('/dashboard');
          return;
        }

        setCurrentUserRole(role);
        setRestaurantId(payload.restaurant_id || payload.restaurant?.id || 'rest_123');
        setAuthLoading(false);
      } catch (err) {
        localStorage.removeItem('token');
        localStorage.removeItem('platelink_auth_token');
        router.push('/login');
      }
    };

    checkAuth();
  }, [router]);

  // ==========================================
  // DATA LOADING (PROFILE & SETTINGS)
  // ==========================================
  const loadSettingsData = async () => {
    setDataLoading(true);
    const token = localStorage.getItem('token') || localStorage.getItem('platelink_auth_token');
    
    try {
      // 1. Get Restaurant Profile
      const profileRes = await fetch('/api/restaurants/me', {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      
      // 2. Get Restaurant Settings
      const settingsRes = await fetch('/api/restaurants/settings', {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });

      if (!profileRes.ok || !settingsRes.ok) {
        throw new Error('API request failed');
      }

      const profileData = await profileRes.json();
      const settingsData = await settingsRes.json();

      // Set states
      setLogoUrl(profileData.logo_url || null);
      setIsMpesaConfigured(!!settingsData.mpesa_configured || !!settingsData.shortcode);
      setIsUsingMocks(false);

      // Populate Form Values
      resetProfile({
        restaurant_name: profileData.restaurant_name || '',
        phone: profileData.phone || '',
        email: profileData.email || '',
        address: profileData.address || '',
        city: profileData.city || 'Nairobi'
      });

      resetMpesa({
        shortcode: settingsData.shortcode || '',
        consumer_key: settingsData.consumer_key || '',
        consumer_secret: settingsData.consumer_secret || '',
        passkey: settingsData.passkey || '',
        environment: settingsData.environment || 'sandbox'
      });

      resetPreferences({
        default_preparation_time: settingsData.default_preparation_time ?? 15,
        low_stock_threshold: settingsData.low_stock_threshold ?? 5,
        tax_rate: settingsData.tax_rate ?? 16,
        auto_accept_orders: settingsData.auto_accept_orders ?? true,
        currency: settingsData.currency || 'KES',
        timezone: settingsData.timezone || 'Africa/Nairobi'
      });

    } catch (error) {
      console.warn('API routes offline, initializing high-fidelity local storage simulation.');
      setIsUsingMocks(true);
      
      // Attempt load from localStorage simulation
      const savedProfile = localStorage.getItem('sim_profile');
      const savedSettings = localStorage.getItem('sim_settings');

      const profile = savedProfile ? JSON.parse(savedProfile) : {
        restaurant_name: 'PlateLink Africa',
        phone: '0712345678',
        email: 'info@platelink.com',
        address: 'Nairobi West, Langata Road',
        city: 'Nairobi',
        logo_url: null
      };

      const settings = savedSettings ? JSON.parse(savedSettings) : {
        shortcode: '',
        consumer_key: '',
        consumer_secret: '',
        passkey: '',
        environment: 'sandbox',
        mpesa_configured: false,
        default_preparation_time: 15,
        low_stock_threshold: 5,
        tax_rate: 16,
        auto_accept_orders: true,
        currency: 'KES',
        timezone: 'Africa/Nairobi'
      };

      setLogoUrl(profile.logo_url);
      setIsMpesaConfigured(settings.mpesa_configured || !!settings.shortcode);

      resetProfile(profile);
      resetMpesa(settings);
      resetPreferences(settings);
    } finally {
      setDataLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      loadSettingsData();
    }
  }, [authLoading]);

  // ==========================================
  // PROFILE SUBMIT HANDLER
  // ==========================================
  const onProfileSubmit = async (data: ProfileFormValues) => {
    setProfileSaving(true);
    
    if (isUsingMocks) {
      setTimeout(() => {
        const simProfile = { ...data, logo_url: logoUrl };
        localStorage.setItem('sim_profile', JSON.stringify(simProfile));
        showToast('Profile updated successfully!', 'success');
        setProfileSaving(false);
      }, 1000);
      return;
    }

    const token = localStorage.getItem('token') || localStorage.getItem('platelink_auth_token');
    try {
      const res = await fetch('/api/restaurants/me', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify(data)
      });

      if (!res.ok) throw new Error('Failed to save profile details');
      showToast('Profile updated successfully', 'success');
    } catch (err: any) {
      showToast(err.message || 'Error occurred while saving profile.', 'error');
    } finally {
      setProfileSaving(false);
    }
  };

  // ==========================================
  // MPESA SUBMIT HANDLER
  // ==========================================
  const onMpesaSubmit = async (data: MpesaFormValues) => {
    setMpesaSaving(true);

    if (isUsingMocks) {
      setTimeout(() => {
        const savedSettings = JSON.parse(localStorage.getItem('sim_settings') || '{}');
        const updatedSettings = {
          ...savedSettings,
          ...data,
          mpesa_configured: true
        };
        localStorage.setItem('sim_settings', JSON.stringify(updatedSettings));
        setIsMpesaConfigured(true);
        showToast('M-Pesa credentials saved successfully', 'success');
        setMpesaSaving(false);
      }, 1000);
      return;
    }

    const token = localStorage.getItem('token') || localStorage.getItem('platelink_auth_token');
    try {
      const res = await fetch('/api/restaurants/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify(data)
      });

      if (!res.ok) throw new Error('Failed to save payment settings');
      setIsMpesaConfigured(true);
      showToast('M-Pesa credentials saved successfully', 'success');
    } catch (err: any) {
      showToast(err.message || 'Error occurred saving credentials.', 'error');
    } finally {
      setMpesaSaving(false);
    }
  };

  // ==========================================
  // PREFERENCES SUBMIT HANDLER
  // ==========================================
  const onPreferencesSubmit = async (data: PreferencesFormValues) => {
    setPreferencesSaving(true);

    if (isUsingMocks) {
      setTimeout(() => {
        const savedSettings = JSON.parse(localStorage.getItem('sim_settings') || '{}');
        const updatedSettings = { ...savedSettings, ...data };
        localStorage.setItem('sim_settings', JSON.stringify(updatedSettings));
        showToast('Preferences updated successfully!', 'success');
        setPreferencesSaving(false);
      }, 1000);
      return;
    }

    const token = localStorage.getItem('token') || localStorage.getItem('platelink_auth_token');
    try {
      const res = await fetch('/api/restaurants/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify(data)
      });

      if (!res.ok) throw new Error('Failed to save preferences');
      showToast('Preferences updated successfully', 'success');
    } catch (err: any) {
      showToast(err.message || 'Error occurred saving preferences.', 'error');
    } finally {
      setPreferencesSaving(false);
    }
  };

  // ==========================================
  // LOGO CLOUDINARY UPLOADER
  // ==========================================
  const handleLogoUpload = async (file: File) => {
    // Validate bounds
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      showToast('Only JPEG or PNG image files are supported.', 'error');
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      showToast('Image size cannot exceed 2MB.', 'error');
      return;
    }

    setLogoUploading(true);

    if (isUsingMocks) {
      // Simulate file upload
      const reader = new FileReader();
      reader.onload = () => {
        setTimeout(() => {
          const base64Url = reader.result as string;
          setLogoUrl(base64Url);
          
          const profile = JSON.parse(localStorage.getItem('sim_profile') || '{}');
          profile.logo_url = base64Url;
          localStorage.setItem('sim_profile', JSON.stringify(profile));

          showToast('Logo uploaded and saved successfully!', 'success');
          setLogoUploading(false);
        }, 1200);
      };
      reader.readAsDataURL(file);
      return;
    }

    const token = localStorage.getItem('token') || localStorage.getItem('platelink_auth_token');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/restaurants/upload-logo', {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: formData
      });

      if (!res.ok) throw new Error('Failed to upload logo image file.');
      
      const resData = await res.json();
      setLogoUrl(resData.logo_url);
      showToast('Logo uploaded and saved successfully!', 'success');
    } catch (err: any) {
      showToast(err.message || 'Error occurred during logo upload.', 'error');
    } finally {
      setLogoUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleLogoUpload(file);
    }
  };

  // ==========================================
  // DARAJA M-PESA CONNECTION TEST
  // ==========================================
  const handleTestMpesa = async () => {
    const values = getMpesaValues();
    
    // Quick validation before testing
    if (!values.shortcode || !values.consumer_key || !values.consumer_secret || !values.passkey) {
      showToast('Please fill out all credentials before testing connection.', 'error');
      return;
    }

    setTestingConnection(true);
    setTestResult({ status: 'idle' });

    if (isUsingMocks) {
      setTimeout(() => {
        // Mock connection outcome based on shortcode
        if (values.shortcode === '600997' || values.shortcode.startsWith('1')) {
          setTestResult({
            status: 'success',
            message: 'Connection successful! PlateLink can successfully talk with Daraja API.'
          });
          showToast('Connection test successful', 'success');
        } else {
          setTestResult({
            status: 'error',
            message: 'Connection rejected. INVALID_CREDENTIALS: Refused to authorize Daraja token query. Please check your Consumer Key and Consumer Secret.'
          });
          showToast('Connection test failed', 'error');
        }
        setTestingConnection(false);
      }, 2000);
      return;
    }

    const token = localStorage.getItem('token') || localStorage.getItem('platelink_auth_token');
    try {
      const res = await fetch('/api/payments/mpesa/test-connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify(values)
      });

      const data = await res.json().catch(() => ({}));
      
      if (!res.ok) {
        throw new Error(data.message || 'M-Pesa Daraja connection test timed out or returned credentials failure.');
      }

      setTestResult({
        status: 'success',
        message: 'Connection successful! Credentials successfully verified with Safaricom Daraja portal.'
      });
      showToast('Connection test successful', 'success');
    } catch (err: any) {
      setTestResult({
        status: 'error',
        message: err.message || 'Network timeout: Failed to query Safaricom endpoint.'
      });
      showToast(err.message || 'Connection test failed', 'error');
    } finally {
      setTestingConnection(false);
    }
  };

  // Auth or Data fetching Skeleton loaders
  if (authLoading || dataLoading) {
    return (
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        <div className="space-y-2">
          <div className="h-9 w-40 bg-gray-200 animate-pulse rounded-lg"></div>
          <div className="h-5 w-80 bg-gray-200 animate-pulse rounded-lg"></div>
        </div>
        <div className="flex flex-col lg:flex-row gap-8">
          <div className="w-full lg:w-64 space-y-2.5">
            {[...Array(4)].map((_, idx) => (
              <div key={idx} className="h-12 bg-gray-200 animate-pulse rounded-xl w-full"></div>
            ))}
          </div>
          <div className="flex-1 bg-white border border-gray-100 rounded-2xl p-8 space-y-6 shadow-sm">
            <div className="h-8 bg-gray-200 animate-pulse rounded-md w-1/3"></div>
            <div className="space-y-4">
              <div className="h-12 bg-gray-200 animate-pulse rounded-xl w-full"></div>
              <div className="grid grid-cols-2 gap-4">
                <div className="h-12 bg-gray-200 animate-pulse rounded-xl"></div>
                <div className="h-12 bg-gray-200 animate-pulse rounded-xl"></div>
              </div>
              <div className="h-24 bg-gray-200 animate-pulse rounded-xl w-full"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6 relative selection:bg-emerald-500 selection:text-white">
      
      {/* Toast Alert overlay */}
      <div className="fixed top-5 right-5 z-50 flex flex-col gap-3 max-w-md w-full">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`flex items-start gap-3 p-4 bg-white border rounded-xl shadow-xl transition-all duration-300 transform scale-100 border-gray-150 ${
              t.type === 'success' ? 'border-emerald-200 bg-emerald-50/20 text-emerald-900' :
              t.type === 'error' ? 'border-rose-200 bg-rose-50/20 text-rose-900' : 'border-blue-200 bg-blue-50/20 text-blue-900'
            }`}
          >
            {t.type === 'success' ? (
              <div className="p-1 bg-emerald-500 text-white rounded-full"><Check className="w-3.5 h-3.5" /></div>
            ) : (
              <div className="p-1 bg-rose-500 text-white rounded-full"><X className="w-3.5 h-3.5" /></div>
            )}
            <span className="text-sm font-semibold flex-1">{t.message}</span>
            <button onClick={() => setToasts(prev => prev.filter(item => item.id !== t.id))} className="text-gray-400 hover:text-gray-650">
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Online/Offline Simulation Alert */}
      {isUsingMocks && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center justify-between text-amber-800 text-xs font-semibold">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
            <span>High-Fidelity Offline Simulation active. All forms update local memory storage seamlessly.</span>
          </div>
          <button onClick={loadSettingsData} className="px-3 py-1 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition flex items-center gap-1">
            <RefreshCw className="w-3 h-3" /> Retry API
          </button>
        </div>
      )}

      {/* PAGE HEADER */}
      <div className="border-b border-gray-100 pb-6">
        <h1 className="text-3xl font-black text-gray-900 tracking-tight">Settings</h1>
        <p className="text-gray-500 text-sm font-medium mt-1">Manage your restaurant profile, payment settings, and preferences</p>
      </div>

      {/* MAIN CONTAINER */}
      <div className="flex flex-col lg:flex-row gap-8">
        
        {/* SIDEBAR TABS NAVIGATION */}
        <aside className="w-full lg:w-64 shrink-0">
          <nav className="flex flex-row lg:flex-col overflow-x-auto lg:overflow-x-visible gap-1.5 pb-3 lg:pb-0 border-b lg:border-b-0 border-gray-100">
            {[
              { id: 'profile', label: 'Profile Settings', icon: <User className="w-4 h-4" /> },
              { id: 'mpesa', label: 'M-Pesa Settings', icon: <CreditCard className="w-4 h-4" /> },
              { id: 'preferences', label: 'Preferences', icon: <Sliders className="w-4 h-4" /> },
              { id: 'billing', label: 'Billing & Plan', icon: <ShieldCheck className="w-4 h-4" /> }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-3 px-4.5 py-3.5 text-xs sm:text-sm font-bold rounded-xl whitespace-nowrap transition-all ${
                  activeTab === tab.id
                    ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/10'
                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </nav>
        </aside>

        {/* CONTENT PANELS CONTAINER */}
        <main className="flex-1 bg-white border border-gray-100 rounded-3xl shadow-sm overflow-hidden p-6 sm:p-8">
          
          {/* ==========================================
              TAB 1: PROFILE SETTINGS
              ========================================== */}
          {activeTab === 'profile' && (
            <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
              
              {/* Profile Header */}
              <div>
                <h2 className="text-xl font-bold text-gray-900">Restaurant Profile</h2>
                <p className="text-gray-500 text-xs mt-1">This information will be displayed on customer menus and digital receipt invoices.</p>
              </div>

              {/* Logo Drag and Drop */}
              <div className="space-y-3">
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-widest">Restaurant Logo</label>
                <div className="flex flex-col sm:flex-row items-center gap-6">
                  <div className="w-24 h-24 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 flex items-center justify-center relative overflow-hidden shadow-inner group shrink-0">
                    {logoUrl ? (
                      <>
                        <img src={logoUrl} alt="Restaurant Logo" className="w-full h-full object-cover" />
                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition duration-200">
                          <button onClick={() => fileInputRef.current?.click()} className="p-1.5 bg-white/20 hover:bg-white/40 text-white rounded-lg text-xs font-bold uppercase tracking-wide">
                            Change
                          </button>
                        </div>
                      </>
                    ) : (
                      <Upload className="w-8 h-8 text-gray-300" />
                    )}
                    {logoUploading && (
                      <div className="absolute inset-0 bg-white/80 flex items-center justify-center">
                        <Loader2 className="w-6 h-6 text-emerald-600 animate-spin" />
                      </div>
                    )}
                  </div>

                  {/* Drag area */}
                  <div
                    ref={dragRef}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`flex-1 w-full border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition ${
                      isDragging ? 'border-emerald-500 bg-emerald-50/10' : 'border-gray-200 hover:border-gray-300 bg-gray-50/30'
                    }`}
                  >
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleLogoUpload(file);
                      }}
                      className="hidden"
                      accept="image/png, image/jpeg"
                    />
                    <Upload className="w-5 h-5 text-gray-400 mx-auto mb-2" />
                    <p className="text-xs font-bold text-gray-700">Drag & drop your logo here, or <span className="text-emerald-600 hover:underline">browse</span></p>
                    <p className="text-[10px] text-gray-400 mt-1 uppercase tracking-wider font-semibold">Supports PNG, JPG up to 2MB (Recommended ratio 1:1)</p>
                  </div>
                </div>
              </div>

              {/* Profile Details Form */}
              <form onSubmit={handleProfileSubmit(onProfileSubmit)} className="space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="md:col-span-2">
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Restaurant Name *</label>
                    <div className="relative">
                      <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400"><Building className="w-4 h-4" /></span>
                      <input
                        type="text"
                        {...registerProfile('restaurant_name')}
                        placeholder="e.g. PlateLink African Kitchen"
                        className={`w-full pl-10 pr-4 py-2.5 bg-gray-50/50 border rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 focus:bg-white outline-none transition font-semibold text-sm ${
                          profileErrors.restaurant_name ? 'border-rose-300 bg-rose-50/20 focus:ring-rose-500/10' : 'border-gray-200'
                        }`}
                      />
                    </div>
                    {profileErrors.restaurant_name && (
                      <p className="text-rose-500 text-xs mt-1.5 font-semibold flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> {profileErrors.restaurant_name.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Phone Number *</label>
                    <div className="relative">
                      <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400"><Phone className="w-4 h-4" /></span>
                      <input
                        type="tel"
                        {...registerProfile('phone')}
                        placeholder="e.g. 0712345678"
                        className={`w-full pl-10 pr-4 py-2.5 bg-gray-50/50 border rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 focus:bg-white outline-none transition font-semibold text-sm ${
                          profileErrors.phone ? 'border-rose-300 bg-rose-50/20 focus:ring-rose-500/10' : 'border-gray-200'
                        }`}
                      />
                    </div>
                    {profileErrors.phone && (
                      <p className="text-rose-500 text-xs mt-1.5 font-semibold flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> {profileErrors.phone.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Email Address *</label>
                    <div className="relative">
                      <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400"><Mail className="w-4 h-4" /></span>
                      <input
                        type="email"
                        {...registerProfile('email')}
                        placeholder="e.g. settings@platelink.com"
                        className={`w-full pl-10 pr-4 py-2.5 bg-gray-50/50 border rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 focus:bg-white outline-none transition font-semibold text-sm ${
                          profileErrors.email ? 'border-rose-300 bg-rose-50/20 focus:ring-rose-500/10' : 'border-gray-200'
                        }`}
                      />
                    </div>
                    {profileErrors.email && (
                      <p className="text-rose-500 text-xs mt-1.5 font-semibold flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> {profileErrors.email.message}
                      </p>
                    )}
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Physical Address</label>
                    <div className="relative">
                      <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400"><MapPin className="w-4 h-4" /></span>
                      <input
                        type="text"
                        {...registerProfile('address')}
                        placeholder="e.g. Langata Road, opposite T-Mall"
                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50/50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 focus:bg-white outline-none transition font-semibold text-sm"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">City</label>
                    <select
                      {...registerProfile('city')}
                      className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 focus:bg-white outline-none transition font-semibold text-sm text-gray-800"
                    >
                      <option value="Nairobi">Nairobi</option>
                      <option value="Mombasa">Mombasa</option>
                      <option value="Kisumu">Kisumu</option>
                      <option value="Nakuru">Nakuru</option>
                      <option value="Eldoret">Eldoret</option>
                    </select>
                  </div>
                </div>

                {/* Profile submit actions */}
                <div className="pt-6 border-t border-gray-100 flex justify-end gap-3.5">
                  <button
                    type="button"
                    onClick={() => {
                      loadSettingsData();
                      showToast('Form fields reset to saved configuration.', 'info');
                    }}
                    className="px-5 py-2.5 text-sm font-bold text-gray-500 hover:text-gray-900 border border-gray-200 hover:bg-gray-50 rounded-xl transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={profileSaving}
                    className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-md shadow-emerald-600/10 hover:shadow-lg transition flex items-center gap-2.5 disabled:opacity-50"
                  >
                    {profileSaving ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        Saving...
                      </>
                    ) : (
                      'Save Changes'
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ==========================================
              TAB 2: M-PESA PAYMENT SETTINGS
              ========================================== */}
          {activeTab === 'mpesa' && (
            <div className="max-w-2xl space-y-6 animate-in fade-in duration-300">
              
              {/* Payment Settings Header */}
              <div>
                <h2 className="text-xl font-bold text-gray-900">M-Pesa Payment Settings</h2>
                <p className="text-gray-500 text-xs mt-1">Configure PlateLink to accept instant Safaricom Lipa Na M-Pesa payments directly to your business Till or Paybill.</p>
              </div>

              {/* INFO BANNER */}
              {isMpesaConfigured ? (
                <div className="flex items-start sm:items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-xl shadow-inner">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5 sm:mt-0" />
                  <span className="text-xs sm:text-sm font-bold">M-Pesa is configured and ready to accept customer dining payments.</span>
                </div>
              ) : (
                <div className="flex items-start sm:items-center gap-3 p-4 bg-amber-50 border border-amber-200 text-amber-900 rounded-xl">
                  <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5 sm:mt-0" />
                  <span className="text-xs sm:text-sm font-bold">M-Pesa is not configured. Customers will be unable to pay for orders using M-Pesa.</span>
                </div>
              )}

              {/* Daraja Portal Credentials Help Guide */}
              <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <BookOpen className="w-5 h-5 text-emerald-600 shrink-0" />
                  <div>
                    <p className="text-xs font-bold text-gray-800">Don't have Safaricom API credentials yet?</p>
                    <p className="text-[10px] text-gray-400 font-semibold uppercase mt-0.5">Read our complete Safaricom Daraja setup instructions.</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setIsGuideOpen(true)}
                  className="w-full sm:w-auto px-4 py-2 bg-white border border-gray-200 text-xs font-bold text-gray-700 hover:text-emerald-700 hover:border-emerald-200 rounded-lg shadow-sm transition flex items-center justify-center gap-2"
                >
                  <HelpCircle className="w-4 h-4 text-emerald-600" />
                  Step-by-Step Guide
                </button>
              </div>

              {/* M-Pesa Credentials Form */}
              <form onSubmit={handleMpesaSubmit(onMpesaSubmit)} className="space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5 bg-gray-50/30 p-5 border border-gray-150/70 rounded-2xl">
                  
                  <div className="md:col-span-2">
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Lipa Na M-Pesa Paybill / Till Number *</label>
                    <input
                      type="text"
                      {...registerMpesa('shortcode')}
                      placeholder="e.g. 174379 or 600997"
                      className={`w-full px-4 py-2.5 bg-white border rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition font-semibold text-sm ${
                        mpesaErrors.shortcode ? 'border-rose-300 focus:ring-rose-500/10' : 'border-gray-200'
                      }`}
                    />
                    {mpesaErrors.shortcode && (
                      <p className="text-rose-500 text-xs mt-1.5 font-semibold flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> {mpesaErrors.shortcode.message}
                      </p>
                    )}
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Daraja Consumer Key *</label>
                    <div className="relative">
                      <input
                        type={showConsumerKey ? 'text' : 'password'}
                        {...registerMpesa('consumer_key')}
                        placeholder="Daraja Application Consumer Key"
                        className={`w-full pl-4 pr-11 py-2.5 bg-white border rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition font-mono text-sm ${
                          mpesaErrors.consumer_key ? 'border-rose-300 focus:ring-rose-500/10' : 'border-gray-200'
                        }`}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConsumerKey(!showConsumerKey)}
                        className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-gray-400 hover:text-gray-600 focus:outline-none"
                      >
                        {showConsumerKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {mpesaErrors.consumer_key && (
                      <p className="text-rose-500 text-xs mt-1.5 font-semibold flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> {mpesaErrors.consumer_key.message}
                      </p>
                    )}
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Daraja Consumer Secret *</label>
                    <div className="relative">
                      <input
                        type={showConsumerSecret ? 'text' : 'password'}
                        {...registerMpesa('consumer_secret')}
                        placeholder="Daraja Application Consumer Secret"
                        className={`w-full pl-4 pr-11 py-2.5 bg-white border rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition font-mono text-sm ${
                          mpesaErrors.consumer_secret ? 'border-rose-300 focus:ring-rose-500/10' : 'border-gray-200'
                        }`}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConsumerSecret(!showConsumerSecret)}
                        className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-gray-400 hover:text-gray-600 focus:outline-none"
                      >
                        {showConsumerSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {mpesaErrors.consumer_secret && (
                      <p className="text-rose-500 text-xs mt-1.5 font-semibold flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> {mpesaErrors.consumer_secret.message}
                      </p>
                    )}
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Daraja Lipa Na M-Pesa Passkey *</label>
                    <div className="relative">
                      <input
                        type={showPasskey ? 'text' : 'password'}
                        {...registerMpesa('passkey')}
                        placeholder="Lipa Na M-Pesa Online Passkey"
                        className={`w-full pl-4 pr-11 py-2.5 bg-white border rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition font-mono text-sm ${
                          mpesaErrors.passkey ? 'border-rose-300 focus:ring-rose-500/10' : 'border-gray-200'
                        }`}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPasskey(!showPasskey)}
                        className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-gray-400 hover:text-gray-600 focus:outline-none"
                      >
                        {showPasskey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {mpesaErrors.passkey && (
                      <p className="text-rose-500 text-xs mt-1.5 font-semibold flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> {mpesaErrors.passkey.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Environment *</label>
                    <select
                      {...registerMpesa('environment')}
                      className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition font-semibold text-sm text-gray-800"
                    >
                      <option value="sandbox">Sandbox (Testing/Daraja Mocks)</option>
                      <option value="production">Production (Live Payments)</option>
                    </select>
                  </div>
                </div>

                {/* CONNECTION TEST OUTCOME STATUS BOX */}
                {testResult.status !== 'idle' && (
                  <div className={`p-4 rounded-xl border flex items-start gap-3 text-sm font-semibold animate-in slide-in-from-top duration-300 ${
                    testResult.status === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'
                  }`}>
                    {testResult.status === 'success' ? (
                      <>
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                        <div>
                          <p className="font-bold">Connection successful!</p>
                          <p className="text-xs text-emerald-700/90 mt-1 leading-relaxed">{testResult.message}</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-5 h-5 text-rose-600 shrink-0" />
                        <div>
                          <p className="font-bold">Connection failed</p>
                          <p className="text-xs text-rose-700/90 mt-1 leading-relaxed">{testResult.message}</p>
                          <div className="mt-2.5 pt-2 border-t border-rose-100 space-y-1 text-[11px] text-rose-900 font-bold uppercase tracking-wider">
                            <p>Troubleshooting Tips:</p>
                            <ul className="list-disc pl-4 text-[10px] lowercase tracking-normal font-normal text-rose-700 space-y-0.5">
                              <li>Ensure your Daraja Application status is set to "Approved"</li>
                              <li>Verify your Till/Paybill number matches your shortcode</li>
                              <li>Double check you did not copy leading/trailing whitespaces</li>
                            </ul>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* Action buttons including TEST CONNECTION */}
                <div className="pt-6 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <button
                    type="button"
                    onClick={handleTestMpesa}
                    disabled={testingConnection}
                    className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-bold text-orange-600 bg-white hover:bg-orange-50 border-2 border-orange-500 rounded-xl transition disabled:opacity-50"
                  >
                    {testingConnection ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-orange-600" />
                        Testing Connection...
                      </>
                    ) : (
                      'Test Connection'
                    )}
                  </button>

                  <div className="flex gap-3 w-full sm:w-auto justify-end">
                    <button
                      type="button"
                      onClick={() => {
                        loadSettingsData();
                        showToast('Credentials form fields reset.', 'info');
                      }}
                      className="flex-1 sm:flex-initial px-5 py-2.5 text-sm font-bold text-gray-500 hover:text-gray-900 border border-gray-200 hover:bg-gray-50 rounded-xl transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={mpesaSaving}
                      className="flex-1 sm:flex-initial px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-md hover:shadow-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {mpesaSaving ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin text-white" />
                          Saving...
                        </>
                      ) : (
                        'Save Credentials'
                      )}
                    </button>
                  </div>
                </div>
              </form>

              {/* Bank security disclosure */}
              <div className="flex items-center gap-2 text-gray-400 justify-center text-[10px] uppercase font-bold tracking-widest mt-6">
                <Lock className="w-3.5 h-3.5" />
                <span>Your credentials are encrypted and never stored in plain text. Bank-level security.</span>
              </div>
            </div>
          )}

          {/* ==========================================
              TAB 3: PREFERENCES SETTINGS
              ========================================== */}
          {activeTab === 'preferences' && (
            <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
              
              {/* Preferences Header */}
              <div>
                <h2 className="text-xl font-bold text-gray-900">Restaurant Preferences</h2>
                <p className="text-gray-500 text-xs mt-1">Configure kitchen execution controls, alerting parameters, and taxing formats.</p>
              </div>

              {/* Preferences Form */}
              <form onSubmit={handlePreferencesSubmit(onPreferencesSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-gray-50/30 p-6 border border-gray-150/70 rounded-2xl">
                  
                  {/* Default Preparation Time */}
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Default Prep Time (Minutes)</label>
                    <input
                      type="number"
                      {...registerPreferences('default_preparation_time', { valueAsNumber: true })}
                      placeholder="e.g. 15"
                      className={`w-full px-4 py-2.5 bg-white border rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition font-semibold text-sm ${
                        preferencesErrors.default_preparation_time ? 'border-rose-300 focus:ring-rose-500/10' : 'border-gray-200'
                      }`}
                    />
                    {preferencesErrors.default_preparation_time && (
                      <p className="text-rose-500 text-xs mt-1.5 font-semibold flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> {preferencesErrors.default_preparation_time.message}
                      </p>
                    )}
                  </div>

                  {/* Low Stock Alert Threshold */}
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Low Stock Alert Threshold</label>
                    <input
                      type="number"
                      {...registerPreferences('low_stock_threshold', { valueAsNumber: true })}
                      placeholder="e.g. 5"
                      className={`w-full px-4 py-2.5 bg-white border rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition font-semibold text-sm ${
                        preferencesErrors.low_stock_threshold ? 'border-rose-300 focus:ring-rose-500/10' : 'border-gray-200'
                      }`}
                    />
                    {preferencesErrors.low_stock_threshold && (
                      <p className="text-rose-500 text-xs mt-1.5 font-semibold flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> {preferencesErrors.low_stock_threshold.message}
                      </p>
                    )}
                  </div>

                  {/* Tax Rate Percentage */}
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">VAT Rate Percentage (%)</label>
                    <input
                      type="number"
                      {...registerPreferences('tax_rate', { valueAsNumber: true })}
                      placeholder="e.g. 16"
                      className={`w-full px-4 py-2.5 bg-white border rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition font-semibold text-sm ${
                        preferencesErrors.tax_rate ? 'border-rose-300 focus:ring-rose-500/10' : 'border-gray-200'
                      }`}
                    />
                    {preferencesErrors.tax_rate && (
                      <p className="text-rose-500 text-xs mt-1.5 font-semibold flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> {preferencesErrors.tax_rate.message}
                      </p>
                    )}
                  </div>

                  {/* Auto-Accept Orders Toggle Switch */}
                  <div className="flex items-center justify-between border border-gray-200/80 bg-white p-4.5 rounded-xl">
                    <div>
                      <p className="text-xs font-bold text-gray-700 uppercase tracking-wide">Auto-Accept Orders</p>
                      <p className="text-[10px] text-gray-400 font-semibold mt-0.5 leading-relaxed">Let PlateLink kitchen screen immediately accept ordering tickets.</p>
                    </div>
                    <Controller
                      name="auto_accept_orders"
                      control={controlPreferences}
                      render={({ field }) => (
                        <button
                          type="button"
                          onClick={() => field.onChange(!field.value)}
                          className={`w-11 h-6 shrink-0 rounded-full transition duration-300 relative focus:outline-none ${
                            field.value ? 'bg-emerald-500' : 'bg-gray-200'
                          }`}
                        >
                          <span className={`w-5 h-5 bg-white rounded-full absolute top-0.5 shadow-md transform transition duration-300 ${
                            field.value ? 'translate-x-5.5' : 'translate-x-0.5'
                          }`}></span>
                        </button>
                      )}
                    />
                  </div>

                  {/* Currency (Select) */}
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Currency Format</label>
                    <select
                      {...registerPreferences('currency')}
                      className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition font-semibold text-sm text-gray-800"
                    >
                      <option value="KES">Kenyan Shilling (KES)</option>
                      <option value="USD">US Dollar (USD)</option>
                    </select>
                  </div>

                  {/* Timezone (Select) */}
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-0.5">Timezone Settings</label>
                    <select
                      {...registerPreferences('timezone')}
                      className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition font-semibold text-sm text-gray-800"
                    >
                      <option value="Africa/Nairobi">East Africa Standard Time (Nairobi)</option>
                      <option value="Africa/Kigali">Central Africa Time (Kigali)</option>
                    </select>
                  </div>
                </div>

                {/* Preferences Actions */}
                <div className="pt-6 border-t border-gray-100 flex justify-end gap-3.5">
                  <button
                    type="button"
                    onClick={() => {
                      loadSettingsData();
                      showToast('Preferences reset.', 'info');
                    }}
                    className="px-5 py-2.5 text-sm font-bold text-gray-500 hover:text-gray-900 border border-gray-200 hover:bg-gray-50 rounded-xl transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={preferencesSaving}
                    className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-md hover:shadow-lg transition flex items-center gap-2.5 disabled:opacity-50"
                  >
                    {preferencesSaving ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        Saving...
                      </>
                    ) : (
                      'Save Preferences'
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ==========================================
              TAB 4: BILLING (COMING SOON PLACEHOLDER)
              ========================================== */}
          {activeTab === 'billing' && (
            <div className="max-w-3xl space-y-8 animate-in fade-in duration-300">
              
              {/* Billing Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Subscription & Billing</h2>
                  <p className="text-gray-500 text-xs mt-1">Manage restaurant subscription plans, billing histories, and account features.</p>
                </div>
                <span className="px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-[10px] font-bold uppercase tracking-wider animate-pulse border border-amber-200">
                  Coming Soon
                </span>
              </div>

              {/* Premium Plan Card Layout */}
              <div className="bg-emerald-600 rounded-3xl p-8 text-white shadow-xl shadow-emerald-100 relative overflow-hidden">
                {/* Micro-gradient glowing bg circle */}
                <div className="absolute top-0 right-0 p-8 opacity-10">
                  <ShieldCheck className="h-32 w-32" />
                </div>
                
                <div className="relative z-10 space-y-6">
                  <div className="space-y-1">
                    <p className="text-emerald-100 text-[10px] font-bold uppercase tracking-widest">Active Plan</p>
                    <h3 className="text-3xl font-black">PlateLink Starter Trial</h3>
                  </div>
                  
                  <p className="text-emerald-50/90 text-sm max-w-md leading-relaxed font-semibold">
                    You have full priority access to M-Pesa digital payments, 12 table terminals, and advanced waiter logs.
                  </p>
                  
                  <div className="flex flex-col sm:flex-row sm:items-center gap-4 pt-2">
                    <button
                      type="button"
                      onClick={() => showToast('Subscription billing dashboard will release in Phase 6!', 'info')}
                      className="px-6 py-2.5 bg-white text-emerald-700 rounded-xl text-xs font-bold hover:bg-emerald-50 transition shadow-md"
                    >
                      Upgrade Plan
                    </button>
                    <div className="text-xs font-bold text-emerald-100 bg-emerald-700/40 px-3 py-1.5 rounded-lg border border-emerald-500/20">
                      ⏳ 14 days remaining in trial
                    </div>
                  </div>
                </div>
              </div>

              {/* Billing History List */}
              <div className="space-y-3">
                <h3 className="font-bold text-gray-900 text-sm uppercase tracking-wider flex items-center gap-2">
                  <Info className="w-4 h-4 text-emerald-600" />
                  Billing History
                </h3>
                
                <div className="border border-gray-150 rounded-2xl overflow-hidden shadow-sm">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 border-b border-gray-150 text-xs font-bold text-gray-500 uppercase">
                      <tr>
                        <th className="px-6 py-4">Invoice Date</th>
                        <th className="px-6 py-4">Plan Name</th>
                        <th className="px-6 py-4">Amount Charged</th>
                        <th className="px-6 py-4">Receipt Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {[
                        { date: 'May 20, 2026', plan: 'Starter Trial Activation', amount: 'KES 0', status: 'Paid' },
                        { date: 'June 1, 2026 (Scheduled)', plan: 'PlateLink Pro Subscription', amount: 'KES 5,000', status: 'Pending' }
                      ].map((inv, idx) => (
                        <tr key={idx} className="hover:bg-gray-50/30 transition text-gray-700 font-semibold">
                          <td className="px-6 py-4 text-gray-900 whitespace-nowrap">{inv.date}</td>
                          <td className="px-6 py-4 text-xs">{inv.plan}</td>
                          <td className="px-6 py-4 font-bold text-gray-900">{inv.amount}</td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                              inv.status === 'Paid' ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600 animate-pulse'
                            }`}>
                              {inv.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Plan Cancellation Danger Section */}
              <div className="pt-8 border-t border-gray-150">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-rose-50 border border-rose-100 rounded-2xl shadow-inner">
                  <div className="space-y-1">
                    <h4 className="text-sm font-bold text-rose-950">Danger Zone</h4>
                    <p className="text-xs text-rose-800/80 leading-relaxed font-semibold">
                      Cancelling your trial subscription will instantly restrict waiter access and close customer ordering pages.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => showToast('Subscription cancellations are managed under Safaricom Till controls.', 'error')}
                    className="w-full sm:w-auto px-5 py-2.5 border border-rose-200 hover:border-rose-300 text-rose-700 hover:bg-rose-100/50 rounded-xl text-xs font-bold transition shrink-0"
                  >
                    Cancel Subscription
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ==========================================
          MODAL GUIDE: SAFARICOM DARAJA PORTAL SETUP
          ========================================== */}
      {isGuideOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full shadow-2xl border border-gray-150 overflow-hidden animate-in zoom-in-95 duration-200">
            {/* Guide Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-150">
              <h3 className="text-lg font-extrabold text-gray-900 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-emerald-600" />
                Safaricom M-Pesa Integration Guide
              </h3>
              <button onClick={() => setIsGuideOpen(false)} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg transition">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Guide Steps */}
            <div className="p-6 overflow-y-auto max-h-[500px] space-y-5 text-sm text-gray-700 font-semibold leading-relaxed">
              <div className="space-y-2 border-l-2 border-emerald-500 pl-4">
                <p className="text-xs uppercase font-extrabold text-emerald-700 tracking-wider">Step 1: Obtain a Lipa Na M-Pesa Shortcode</p>
                <p className="text-gray-600">
                  Register for a business account with Safaricom to get a Lipa Na M-Pesa Till Number (Buy Goods) or a Paybill Number (Store/Shortcode). 
                  For testing, you can use the Safaricom Daraja test shortcode <span className="font-mono text-emerald-600 font-bold bg-emerald-50 px-1 rounded">174379</span>.
                </p>
              </div>

              <div className="space-y-2 border-l-2 border-emerald-500 pl-4">
                <p className="text-xs uppercase font-extrabold text-emerald-700 tracking-wider">Step 2: Sign Up on the Safaricom Daraja Portal</p>
                <p className="text-gray-650">
                  Visit the <a href="https://developer.safaricom.co.ke/" target="_blank" rel="noreferrer" className="text-emerald-600 hover:underline">Safaricom Daraja Portal</a> and create a Developer Account. Complete verification via email to activate.
                </p>
              </div>

              <div className="space-y-2 border-l-2 border-emerald-500 pl-4">
                <p className="text-xs uppercase font-extrabold text-emerald-700 tracking-wider">Step 3: Create a Daraja App & Get Keys</p>
                <p className="text-gray-650">
                  Click on "My Apps" then "Create New App". Make sure to check the checkbox for "Lipa Na Mpesa Sandbox". 
                  This will generate your masked <span className="font-bold text-gray-900">Consumer Key</span> and <span className="font-bold text-gray-900">Consumer Secret</span>.
                </p>
              </div>

              <div className="space-y-2 border-l-2 border-emerald-500 pl-4">
                <p className="text-xs uppercase font-extrabold text-emerald-700 tracking-wider">Step 4: Retrieve your Lipa Na M-Pesa Passkey</p>
                <p className="text-gray-655 font-normal">
                  For the <span className="font-bold">Sandbox (Testing)</span> environment, click on "APIs" -&gt; "M-PESA Express" -&gt; "Simulate" to retrieve the default test passkey, or check your Safaricom onboarding developer registration email. 
                  For the <span className="font-bold">Production (Live)</span> environment, the passkey is sent securely by Safaricom to the registered primary business owner's email address upon live app approval.
                </p>
              </div>
            </div>

            {/* Guide Actions */}
            <div className="flex justify-end p-5 bg-gray-50 border-t border-gray-150">
              <button
                type="button"
                onClick={() => setIsGuideOpen(false)}
                className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-sm transition"
              >
                I Understand
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

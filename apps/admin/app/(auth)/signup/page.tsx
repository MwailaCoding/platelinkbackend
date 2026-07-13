// apps/admin/app/(auth)/signup/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Building2, 
  Mail, 
  Lock, 
  Phone, 
  ArrowRight, 
  Check, 
  AlertCircle, 
  Loader2,
  Sparkles,
  UtensilsCrossed,
  Info,
  Globe,
  Network
} from 'lucide-react';
import Link from 'next/link';

export default function SignupPage() {
  const router = useRouter();
  
  // Form values
  const [restaurantName, setRestaurantName] = useState('');
  const [subdomain, setSubdomain] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [restaurantType, setRestaurantType] = useState<'single' | 'multi_branch'>('single');
  
  // Form states
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Auto-generate subdomain from restaurant name
  useEffect(() => {
    if (restaurantName) {
      const suggested = restaurantName
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '')
        .substring(0, 20);
      setSubdomain(suggested);
    }
  }, [restaurantName]);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 5000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setToast(null);

    // Validation
    if (!restaurantName.trim() || !subdomain.trim() || !email.trim() || !password.trim()) {
      showToast('Please fill in all required fields.', 'error');
      return;
    }

    if (password.length < 8) {
      showToast('Password must be at least 8 characters long.', 'error');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          restaurant_name: restaurantName.trim(),
          subdomain: subdomain.trim(),
          owner_name: 'Admin', // default owner name
          email: email.trim(),
          password,
          phone: phone.trim() || undefined,
          restaurant_type: restaurantType,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.error || 'Something went wrong. Please check your credentials.');
      }

      setSuccess(true);
      showToast('Verification email sent! Check your inbox.', 'success');
      
      // Store type temporarily so verify page knows where to route next
      if (typeof window !== 'undefined') {
        localStorage.setItem('signup_restaurant_type', restaurantType);
      }
      
      const userEmail = data.user?.email || data.email || email.trim();
      setTimeout(() => {
        router.push(`/verify-email?email=${encodeURIComponent(userEmail)}`);
      }, 1500);
    } catch (err: any) {
      showToast(err.message || 'Connection failed. Please check your API backend.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center relative overflow-hidden font-sans selection:bg-emerald-500 selection:text-white">
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

      <div className="flex-1 flex flex-col lg:flex-row max-w-7xl w-full mx-auto p-4 lg:p-8 items-center justify-center relative z-10 gap-8">
        
        {/* LEFT COLUMN: MARKETING */}
        <div className="w-full lg:w-1/2 text-left flex flex-col justify-center p-6 lg:p-12">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8 group">
            <div className="w-12 h-12 bg-emerald-600 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-emerald-600/30 group-hover:scale-105 transition-transform duration-300">
              <UtensilsCrossed className="w-6 h-6" />
            </div>
            <div>
              <span className="text-2xl font-black text-gray-900 tracking-tight">PlateLink</span>
              <span className="text-xs font-bold text-emerald-600 block leading-none">AFRICA</span>
            </div>
          </div>

          {/* Headline */}
          <h1 className="text-4xl lg:text-5xl font-black text-gray-900 leading-tight tracking-tight mb-4">
            Get started in <span className="text-emerald-600">30 seconds</span>
          </h1>
          <p className="text-gray-500 text-lg mb-8 max-w-md">
            Streamline your restaurant operations, QR code ordering, payments, and staff coordination under a single hub.
          </p>

          {/* Bullet Points */}
          <div className="space-y-4 mb-10 max-w-md">
            {[
              "No credit card required",
              "14-day free trial",
              "Add menu items immediately",
              "Set up tables and QR codes",
              "Add staff later"
            ].map((text, idx) => (
              <div key={idx} className="flex items-center gap-3 bg-white p-3.5 rounded-xl border border-gray-100 shadow-sm hover:border-emerald-200 transition-colors duration-300">
                <div className="flex-shrink-0 w-6 h-6 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center">
                  <Check className="w-4 h-4 stroke-[3]" />
                </div>
                <span className="text-sm font-semibold text-gray-700">{text}</span>
              </div>
            ))}
          </div>

          {/* Trusted Badge */}
          <div className="flex items-center gap-3 mt-4 border-t border-gray-100 pt-6">
            <div className="flex -space-x-2">
              {[1, 2, 3].map((num) => (
                <div key={num} className="w-8 h-8 rounded-full bg-emerald-100 border-2 border-white flex items-center justify-center text-xs font-bold text-emerald-800">
                  R{num}
                </div>
              ))}
            </div>
            <p className="text-sm text-gray-500 font-semibold flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-amber-500 fill-amber-500" />
              Trusted by 50+ restaurants in Kenya
            </p>
          </div>
        </div>

        {/* RIGHT COLUMN: FORM CARD */}
        <div className="w-full lg:w-1/2 flex flex-col justify-center max-w-md lg:max-w-xl">
          <div className="bg-white rounded-3xl border border-gray-100 shadow-2xl p-8 lg:p-10 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-50 rounded-bl-full -z-10" />
            
            <div className="mb-8">
              <h2 className="text-2xl font-extrabold text-gray-900">Create your account</h2>
              <p className="text-gray-500 text-sm mt-1">Start your 14-day free trial</p>
            </div>

            {/* Info Banner */}
            <div className="mb-6 p-4 bg-emerald-50 border border-emerald-100 text-emerald-800 rounded-2xl flex items-start gap-3 shadow-sm">
              <Info className="w-5 h-5 flex-shrink-0 mt-0.5 text-emerald-600 animate-pulse" />
              <div className="text-xs font-semibold leading-relaxed">
                We'll send a 6-digit verification code to your email
              </div>
            </div>

            {/* ERROR SUMMARY */}
            {toast && toast.type === 'error' && (
              <div className="mb-6 p-4 bg-rose-50 border border-rose-100 text-rose-800 rounded-2xl flex items-start gap-3">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-500" />
                <span className="text-xs font-semibold leading-relaxed">{toast.message}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              
              {/* Type Selection */}
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Restaurant Type *</label>
                <div className="flex gap-4">
                  <button
                    type="button"
                    onClick={() => setRestaurantType('single')}
                    className={`flex-1 p-4 rounded-2xl border-2 text-left transition-all ${
                      restaurantType === 'single' 
                        ? 'border-emerald-500 bg-emerald-50 shadow-sm' 
                        : 'border-gray-200 hover:border-emerald-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Building2 className={`w-5 h-5 ${restaurantType === 'single' ? 'text-emerald-600' : 'text-gray-400'}`} />
                      <div className="font-bold text-gray-900">Single Location</div>
                    </div>
                    <div className="text-xs text-gray-500">Perfect for independent restaurants</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setRestaurantType('multi_branch')}
                    className={`flex-1 p-4 rounded-2xl border-2 text-left transition-all ${
                      restaurantType === 'multi_branch' 
                        ? 'border-emerald-500 bg-emerald-50 shadow-sm' 
                        : 'border-gray-200 hover:border-emerald-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Network className={`w-5 h-5 ${restaurantType === 'multi_branch' ? 'text-emerald-600' : 'text-gray-400'}`} />
                      <div className="font-bold text-gray-900">Multi-Branch</div>
                    </div>
                    <div className="text-xs text-gray-500">Manage multiple locations easily</div>
                  </button>
                </div>
              </div>

              {/* Restaurant Name */}
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Restaurant Name *</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400">
                    <Building2 className="w-5 h-5" />
                  </span>
                  <input
                    type="text"
                    required
                    value={restaurantName}
                    onChange={(e) => setRestaurantName(e.target.value)}
                    placeholder="e.g. Mama Nyama Restaurant"
                    className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white text-sm text-gray-900 transition-all font-semibold"
                  />
                </div>
              </div>

              {/* Subdomain */}
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Workspace URL *</label>
                <div className="relative flex items-center">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400">
                    <Globe className="w-5 h-5" />
                  </span>
                  <input
                    type="text"
                    required
                    value={subdomain}
                    onChange={(e) => setSubdomain(e.target.value)}
                    placeholder="mamanyama"
                    className="w-full pl-11 pr-32 py-3 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white text-sm text-gray-900 transition-all font-semibold"
                  />
                  <span className="absolute right-4 text-gray-400 font-medium text-sm">.platelink.africa</span>
                </div>
              </div>

              {/* Email Address */}
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Email Address *</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400">
                    <Mail className="w-5 h-5" />
                  </span>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. contact@mamanyama.com"
                    className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white text-sm text-gray-900 transition-all font-semibold"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Password *</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400">
                    <Lock className="w-5 h-5" />
                  </span>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="At least 8 characters"
                    className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white text-sm text-gray-900 transition-all font-semibold"
                  />
                </div>
              </div>

              {/* Phone Number */}
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Phone Number (Optional)</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400">
                    <Phone className="w-5 h-5" />
                  </span>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="e.g. +254 712 345 678"
                    className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white text-sm text-gray-900 transition-all font-semibold"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading || success}
                className="w-full mt-6 py-4 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white rounded-2xl font-bold flex items-center justify-center gap-2 hover:gap-3 transition-all duration-300 disabled:opacity-50 disabled:pointer-events-none shadow-xl shadow-emerald-600/25"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Creating account...
                  </>
                ) : success ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Redirecting to verification...
                  </>
                ) : (
                  <>
                    Create Account
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </form>

            {/* Footer */}
            <div className="mt-8 text-center text-sm font-semibold text-gray-500">
              Already have an account?{' '}
              <Link href="/login" className="text-emerald-600 hover:text-emerald-700 transition-colors underline decoration-2 decoration-emerald-600/25 hover:decoration-emerald-700">
                Log in
              </Link>
            </div>
          </div>

          {/* Bottom Banner */}
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-2 px-4 py-3 bg-emerald-50 border border-emerald-100 rounded-2xl text-center sm:text-left shadow-sm">
            <span className="flex-shrink-0 w-6 h-6 bg-emerald-500 text-white rounded-lg flex items-center justify-center shadow-sm">
              <Check className="w-4 h-4 stroke-[3]" />
            </span>
            <div className="text-xs font-semibold text-emerald-800 flex flex-col sm:flex-row sm:gap-1.5 justify-center">
              <span>No business documents needed to get started.</span>
              <span className="text-emerald-600 font-bold">You'll get immediate access to your dashboard!</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

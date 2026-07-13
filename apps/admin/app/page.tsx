// apps/admin/app/page.tsx
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Menu, X, QrCode, Monitor, Tablet,
  Smartphone, Package,
  Star, Check, ArrowRight,
  TrendingUp, Shield, CreditCard,
  Phone, Mail, MapPin, Facebook, Twitter, Instagram,
  Linkedin, Sparkles, Crown, CircleCheck
} from 'lucide-react';

// ============================================================
// TYPES & SCHEMAS
// ============================================================

const signupSchema = z.object({
  restaurant_name: z.string().min(2, 'Restaurant name is required'),
  owner_name: z.string().min(2, 'Full name is required'),
  email: z.string().email('Valid email is required'),
  phone: z.string().regex(/^(07|01|254)\d{8,9}$/, 'Valid Kenyan phone number is required'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string()
}).refine(data => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword']
});

type SignupFormData = z.infer<typeof signupSchema>;

// ============================================================
// COMPONENTS
// ============================================================

function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">P</span>
              </div>
              <span className="font-bold text-xl text-gray-900">PlateLink <span className="text-emerald-600">Africa</span></span>
            </Link>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <Link href="#features" className="text-gray-600 hover:text-emerald-600 transition">Features</Link>
            <Link href="#how-it-works" className="text-gray-600 hover:text-emerald-600 transition">How It Works</Link>
            <Link href="#testimonials" className="text-gray-600 hover:text-emerald-600 transition">Testimonials</Link>
            <Link href="#pricing" className="text-gray-600 hover:text-emerald-600 transition">Pricing</Link>
          </div>
          <div className="hidden md:block">
            <a href="#signup" className="bg-emerald-600 text-white px-5 py-2 rounded-lg hover:bg-emerald-700 transition font-medium">
              Get Started
            </a>
          </div>
          <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="md:hidden">
            {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>
      {isMenuOpen && (
        <div className="md:hidden bg-white border-b border-gray-100 py-4">
          <div className="flex flex-col gap-4 px-4">
            <Link href="#features" className="text-gray-600 py-2" onClick={() => setIsMenuOpen(false)}>Features</Link>
            <Link href="#how-it-works" className="text-gray-600 py-2" onClick={() => setIsMenuOpen(false)}>How It Works</Link>
            <Link href="#testimonials" className="text-gray-600 py-2" onClick={() => setIsMenuOpen(false)}>Testimonials</Link>
            <Link href="#pricing" className="text-gray-600 py-2" onClick={() => setIsMenuOpen(false)}>Pricing</Link>
            <a href="#signup" className="bg-emerald-600 text-white px-5 py-2 rounded-lg text-center" onClick={() => setIsMenuOpen(false)}>
              Get Started
            </a>
          </div>
        </div>
      )}
    </nav>
  );
}

function Hero() {
  return (
    <section className="pt-32 pb-20 px-4 bg-gradient-to-br from-white via-emerald-50/30 to-white">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 bg-orange-100 text-orange-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
              <Sparkles className="w-4 h-4" />
              Now serving 50+ restaurants across Kenya
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">
              Digitize Your Restaurant.
              <span className="text-emerald-600"> Delight Your Customers.</span>
            </h1>
            <p className="text-lg text-gray-600 mb-8">
              Join 50+ restaurants across Kenya using PlateLink to take orders, accept M-Pesa payments,
              and serve more customers. No app download needed.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <a href="#signup" className="bg-emerald-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-emerald-700 transition text-center">
                Start Free Trial <ArrowRight className="inline w-4 h-4 ml-2" />
              </a>
              <a href="#how-it-works" className="border border-gray-300 text-gray-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-50 transition text-center">
                See How It Works
              </a>
            </div>
            <p className="text-sm text-gray-500 mt-6">No credit card required. 14-day free trial. Cancel anytime.</p>
          </div>
          <div className="relative">
            <div className="bg-gray-900 rounded-3xl p-4 shadow-2xl">
              <div className="bg-white rounded-2xl overflow-hidden">
                <div className="bg-emerald-600 px-4 py-3 flex justify-between items-center">
                  <span className="text-white font-semibold">Riverside Hotel - Table 12</span>
                  <div className="w-6 h-6 bg-white rounded-full flex items-center justify-center">
                    <span className="text-emerald-600 text-xs">2</span>
                  </div>
                </div>
                <div className="p-4">
                  <div className="flex gap-2 mb-4 overflow-x-auto">
                    {['Appetizers', 'Main Course', 'Desserts', 'Beverages'].map(cat => (
                      <span key={cat} className={`text-sm px-3 py-1 rounded-full whitespace-nowrap ${cat === 'Main Course' ? 'bg-emerald-600 text-white' : 'bg-gray-100'}`}>
                        {cat}
                      </span>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {['Grilled Chicken', 'Beef Steak', 'Vegetable Curry', 'Spring Rolls'].map(item => (
                      <div key={item} className="border rounded-lg p-2">
                        <div className="w-full h-16 bg-gray-200 rounded mb-2"></div>
                        <p className="font-medium text-sm">{item}</p>
                        <p className="text-emerald-600 font-bold text-sm">
                          KES {item === 'Grilled Chicken' ? '850' : item === 'Beef Steak' ? '1,200' : item === 'Vegetable Curry' ? '600' : '450'}
                        </p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-3 border-t flex justify-between items-center">
                    <span className="font-bold">Total KES 2,450</span>
                    <span className="bg-emerald-600 text-white px-4 py-1.5 rounded-lg text-sm">View Cart</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute -top-4 -right-4 bg-orange-500 text-white px-3 py-1 rounded-full text-sm font-medium shadow-lg">
              QR Code Ordering
            </div>
            <div className="absolute -bottom-4 -left-4 bg-emerald-500 text-white px-3 py-1 rounded-full text-sm font-medium shadow-lg">
              M-Pesa Ready
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Features() {
  const features = [
    { icon: QrCode, title: 'QR Code on Every Table', description: 'Customers scan, view menu, order from their phone. No app download needed.', color: 'emerald' as const },
    { icon: Monitor, title: 'Kitchen Display System', description: 'Orders appear instantly on kitchen screen. Special instructions highlighted. Never lose a ticket.', color: 'orange' as const },
    { icon: Tablet, title: 'Waiter Station', description: 'One shared screen at pickup area. Multiple waiters, one device. See ready orders, call alerts, bill requests.', color: 'blue' as const },
    { icon: Smartphone, title: 'Customer PWA', description: 'Works on any phone. No app store required. Offline menu available.', color: 'purple' as const },
    { icon: Package, title: 'Order Tracking', description: 'Real-time updates from kitchen to table. Customers know exactly when food is ready.', color: 'green' as const },
    { icon: CreditCard, title: 'M-Pesa Integration', description: 'STK Push payments. Customers pay in 15 seconds. No manual entry.', color: 'pink' as const },
  ];

  const colorClasses: Record<string, string> = {
    emerald: 'bg-emerald-100 text-emerald-600',
    orange: 'bg-orange-100 text-orange-600',
    blue: 'bg-blue-100 text-blue-600',
    purple: 'bg-purple-100 text-purple-600',
    green: 'bg-green-100 text-green-600',
    pink: 'bg-pink-100 text-pink-600',
  };

  return (
    <section id="features" className="py-20 px-4 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Everything you need to digitize your restaurant</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">A complete platform for modern restaurants. From ordering to payment, we&apos;ve got you covered.</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, idx) => (
            <div key={idx} className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm hover:shadow-md transition">
              <div className={`w-12 h-12 rounded-lg ${colorClasses[feature.color]} flex items-center justify-center mb-4`}>
                <feature.icon className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { icon: QrCode, title: 'Scan QR Code', description: 'At their table, scan with phone camera', color: 'emerald' as const },
    { icon: Smartphone, title: 'View Menu & Order', description: 'See photos, prices, dietary info. Add to cart.', color: 'orange' as const },
    { icon: CreditCard, title: 'Pay with M-Pesa', description: 'STK Push to phone. 15 seconds. No typing.', color: 'blue' as const },
    { icon: Package, title: 'Track Order', description: 'Real-time updates: Preparing, Ready, Served', color: 'purple' as const },
  ];

  const colorClasses: Record<string, string> = {
    emerald: 'bg-emerald-100 text-emerald-600',
    orange: 'bg-orange-100 text-orange-600',
    blue: 'bg-blue-100 text-blue-600',
    purple: 'bg-purple-100 text-purple-600',
  };

  return (
    <section id="how-it-works" className="py-20 px-4 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Your Customers Will Love This</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">Simple, fast, and no app required. Customers can order from their phone in seconds.</p>
        </div>
        <div className="grid md:grid-cols-4 gap-8">
          {steps.map((step, idx) => (
            <div key={idx} className="text-center relative">
              <div className={`w-16 h-16 rounded-full ${colorClasses[step.color]} flex items-center justify-center mx-auto mb-4 relative`}>
                <step.icon className="w-8 h-8" />
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-gray-800 text-white rounded-full flex items-center justify-center text-xs font-bold">
                  {idx + 1}
                </div>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{step.title}</h3>
              <p className="text-gray-600 text-sm">{step.description}</p>
            </div>
          ))}
        </div>
        <div className="mt-16 max-w-md mx-auto bg-white rounded-xl shadow-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <span className="font-semibold">Order #1042</span>
            <span className="text-sm text-gray-500">Table 12</span>
          </div>
          <div className="flex justify-between mb-6">
            {['Received', 'Preparing', 'Ready', 'Served'].map((stage, idx) => (
              <div key={stage} className="text-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-1 ${idx <= 1 ? 'bg-emerald-600 text-white' : 'bg-gray-200 text-gray-400'}`}>
                  {idx <= 1 ? <Check className="w-4 h-4" /> : <span className="text-xs">{idx + 1}</span>}
                </div>
                <span className="text-xs text-gray-500">{stage}</span>
              </div>
            ))}
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
            <p className="text-yellow-800 text-sm">Your order will be ready in approximately 10 minutes</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function Testimonials() {
  const testimonials = [
    {
      quote: "PlateLink saved us 2 hours of waiter time every shift. Our customers love ordering from their phones. Best decision we made.",
      author: "James Mwangi",
      role: "Owner, Riverside Hotel Nairobi",
      rating: 5,
    },
    {
      quote: "The kitchen display eliminated all order mistakes. Special instructions are highlighted in red. My chefs love it.",
      author: "Mary Wanjiku",
      role: "Manager, Java House",
      rating: 5,
    },
  ];

  const partners = ['Java House', 'Artcaffe', 'The Big Fish', 'Thorntree Riverside', 'Tamarind Nairobi', 'Tribe Hotel'];

  return (
    <section id="testimonials" className="py-20 px-4 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Trusted by Restaurant Owners Across Kenya</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">Join the growing community of restaurants using PlateLink</p>
        </div>
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          {testimonials.map((t, idx) => (
            <div key={idx} className="bg-gray-50 rounded-xl p-6">
              <div className="flex gap-1 mb-4">
                {[...Array(t.rating)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-700 mb-4 italic">&ldquo;{t.quote}&rdquo;</p>
              <div>
                <p className="font-semibold text-gray-900">{t.author}</p>
                <p className="text-sm text-gray-500">{t.role}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="text-center">
          <p className="text-gray-600 mb-6">Trusted by 50+ restaurants across Kenya</p>
          <div className="flex flex-wrap justify-center gap-8 opacity-60">
            {partners.map(partner => (
              <span key={partner} className="text-gray-500 font-medium">{partner}</span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  const plans = [
    {
      name: 'Starter',
      price: '5,000',
      period: '/month',
      features: ['Up to 10 tables', 'Digital menu', 'QR ordering', 'Basic reports', 'Email support'],
      cta: 'Get Started',
      highlighted: false,
    },
    {
      name: 'Pro',
      price: '12,000',
      period: '/month',
      features: ['Up to 30 tables', 'Kitchen display', 'Waiter station', 'Cashier dashboard', 'Analytics', 'Occasion menus', 'WhatsApp support'],
      cta: 'Start Free Trial',
      highlighted: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      features: ['Unlimited tables', 'Multi-location', 'Custom reports', 'API access', 'Phone support', 'Dedicated account manager'],
      cta: 'Contact Sales',
      highlighted: false,
    },
  ];

  return (
    <section id="pricing" className="py-20 px-4 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Simple, Transparent Pricing</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">No hidden fees. Cancel anytime. 1% transaction fee only on M-Pesa payments.</p>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan, idx) => (
            <div key={idx} className={`rounded-xl p-6 ${plan.highlighted ? 'bg-emerald-600 text-white shadow-xl scale-105' : 'bg-white border border-gray-200'}`}>
              {plan.highlighted && (
                <div className="bg-orange-500 text-white text-xs font-semibold px-3 py-1 rounded-full inline-block mb-4">Most Popular</div>
              )}
              <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
              <div className="mb-4">
                <span className={`text-3xl font-bold ${plan.highlighted ? 'text-white' : 'text-gray-900'}`}>KES {plan.price}</span>
                <span className={plan.highlighted ? 'text-white/70' : 'text-gray-500'}>{plan.period}</span>
              </div>
              <ul className="space-y-2 mb-6">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm">
                    <Check className={`w-4 h-4 ${plan.highlighted ? 'text-white' : 'text-emerald-500'}`} />
                    <span className={plan.highlighted ? 'text-white/90' : 'text-gray-600'}>{feature}</span>
                  </li>
                ))}
              </ul>
              <a href="#signup" className={`block text-center py-2 rounded-lg font-medium transition ${plan.highlighted ? 'bg-white text-emerald-600 hover:bg-gray-100' : 'bg-emerald-600 text-white hover:bg-emerald-700'}`}>
                {plan.cta}
              </a>
            </div>
          ))}
        </div>
        <p className="text-center text-gray-500 text-sm mt-8">14-day free trial. No credit card required. Cancel anytime.</p>
      </div>
    </section>
  );
}

function SignupForm() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema)
  });

  const onSubmit = async (data: SignupFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'https://api.platelink.com/api/v1';

      const response = await fetch(`${apiBase}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          restaurant_name: data.restaurant_name,
          owner_name: data.owner_name,
          email: data.email,
          phone: data.phone,
          password: data.password
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Registration failed. Please try again.');
      }

      setSuccess(true);

      const loginResponse = await fetch(`${apiBase}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: data.email, password: data.password })
      });

      if (loginResponse.ok) {
        const loginData = await loginResponse.json();
        const token = loginData.access_token || loginData.token;
        if (token) {
          localStorage.setItem('token', token);
          localStorage.setItem('platelink_auth_token', token);
        }
        setTimeout(() => router.push('/dashboard'), 1500);
      } else {
        setTimeout(() => router.push('/login'), 1500);
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section id="signup" className="py-20 px-4 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
              <Crown className="w-4 h-4" />
              Start Free Trial
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Create Your Restaurant Account</h2>
            <p className="text-gray-600 mb-6">Start your 14-day free trial. No credit card required. Get instant access to your dashboard.</p>
            <div className="space-y-4">
              {[
                { icon: QrCode, text: 'QR Code Ordering' },
                { icon: CreditCard, text: 'M-Pesa Payments' },
                { icon: Monitor, text: 'Kitchen Display' },
                { icon: TrendingUp, text: 'Business Analytics' }
              ].map((item, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                    <item.icon className="w-5 h-5 text-emerald-600" />
                  </div>
                  <span className="text-gray-700">{item.text}</span>
                </div>
              ))}
            </div>
            <div className="mt-8 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-emerald-600" />
                <span className="font-medium">Secure &amp; Reliable</span>
              </div>
              <p className="text-sm text-gray-600">Bank-level security. Local support. Made with ❤️ in Kenya</p>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-lg">
            <h3 className="text-xl font-bold text-gray-900 mb-2">Create your account</h3>
            <p className="text-gray-500 text-sm mb-6">Start your 14-day free trial. No credit card required.</p>

            {success ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                <CircleCheck className="w-12 h-12 text-green-500 mx-auto mb-3" />
                <h4 className="font-semibold text-green-800 mb-1">Account created successfully!</h4>
                <p className="text-green-600 text-sm">Redirecting to your dashboard...</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Restaurant Name *</label>
                  <input {...register('restaurant_name')} id="restaurant_name" type="text" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="e.g. Riverside Hotel Nairobi" />
                  {errors.restaurant_name && <p className="text-red-500 text-xs mt-1">{errors.restaurant_name.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Your Full Name *</label>
                  <input {...register('owner_name')} id="owner_name" type="text" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="e.g. John Mwangi" />
                  {errors.owner_name && <p className="text-red-500 text-xs mt-1">{errors.owner_name.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email Address *</label>
                  <input {...register('email')} id="email" type="email" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="e.g. john@riverside.co.ke" />
                  {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number *</label>
                  <div className="flex">
                    <span className="inline-flex items-center px-3 border border-r-0 border-gray-300 rounded-l-lg bg-gray-50 text-gray-500 text-sm">+254</span>
                    <input {...register('phone')} id="phone" type="tel" className="flex-1 px-3 py-2 border border-gray-300 rounded-r-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="712 345 678" />
                  </div>
                  {errors.phone && <p className="text-red-500 text-xs mt-1">{errors.phone.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
                  <input {...register('password')} id="password" type="password" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="Create a strong password" />
                  {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password *</label>
                  <input {...register('confirmPassword')} id="confirmPassword" type="password" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="Confirm your password" />
                  {errors.confirmPassword && <p className="text-red-500 text-xs mt-1">{errors.confirmPassword.message}</p>}
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-red-600 text-sm">{error}</p>
                  </div>
                )}

                <button id="signup-submit" type="submit" disabled={isLoading} className="w-full bg-emerald-600 text-white py-3 rounded-lg font-semibold hover:bg-emerald-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
                  {isLoading ? 'Creating account...' : 'Create Account →'}
                </button>

                <p className="text-center text-sm text-gray-600">
                  Already have an account?{' '}
                  <Link href="/login" className="text-emerald-600 hover:underline font-medium">Log in</Link>
                </p>
                <p className="text-xs text-gray-500 text-center mt-4">
                  By creating an account, you agree to our Terms of Service and Privacy Policy
                </p>
              </form>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section className="py-20 px-4 bg-emerald-600">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Ready to Transform Your Restaurant?</h2>
        <p className="text-emerald-100 text-lg mb-8">Join 50+ Kenyan restaurants already using PlateLink</p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a href="#signup" className="bg-white text-emerald-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition">Start Free Trial →</a>
          <a href="#how-it-works" className="border border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-emerald-700 transition">Schedule a Demo</a>
        </div>
        <p className="text-emerald-100 text-sm mt-6">No credit card required. 14-day free trial. Cancel anytime.</p>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-5 gap-8 mb-8">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">P</span>
              </div>
              <span className="font-bold text-xl text-white">PlateLink Africa</span>
            </div>
            <p className="text-sm">Digital ordering platform for Kenyan restaurants. Simple. Fast. Reliable.</p>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="#features" className="hover:text-white transition">Features</Link></li>
              <li><Link href="#how-it-works" className="hover:text-white transition">How It Works</Link></li>
              <li><Link href="#pricing" className="hover:text-white transition">Pricing</Link></li>
              <li><Link href="#" className="hover:text-white transition">Integrations</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="#" className="hover:text-white transition">Blog</Link></li>
              <li><Link href="#" className="hover:text-white transition">Help Center</Link></li>
              <li><Link href="#" className="hover:text-white transition">Guides</Link></li>
              <li><Link href="#" className="hover:text-white transition">FAQ</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Company</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="#" className="hover:text-white transition">About Us</Link></li>
              <li><Link href="#" className="hover:text-white transition">Careers</Link></li>
              <li><Link href="#" className="hover:text-white transition">Terms of Service</Link></li>
              <li><Link href="#" className="hover:text-white transition">Privacy Policy</Link></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex gap-6">
            <a href="#" className="hover:text-white transition" aria-label="Facebook"><Facebook className="w-5 h-5" /></a>
            <a href="#" className="hover:text-white transition" aria-label="Twitter"><Twitter className="w-5 h-5" /></a>
            <a href="#" className="hover:text-white transition" aria-label="Instagram"><Instagram className="w-5 h-5" /></a>
            <a href="#" className="hover:text-white transition" aria-label="LinkedIn"><Linkedin className="w-5 h-5" /></a>
          </div>
          <div className="flex flex-wrap gap-4 text-sm justify-center">
            <span className="flex items-center gap-1"><Phone className="w-3 h-3" /> +254 700 123 456</span>
            <span className="flex items-center gap-1"><Mail className="w-3 h-3" /> hello@platelink.africa</span>
            <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> Nairobi, Kenya</span>
          </div>
          <p className="text-sm">© 2026 PlateLink Africa. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

function FloatingCTA() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsVisible(window.scrollY > 500);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  if (!isVisible) return null;

  return (
    <a href="#signup" aria-label="Get Started" className="fixed bottom-6 right-6 z-40 bg-emerald-600 text-white p-4 rounded-full shadow-lg hover:bg-emerald-700 transition animate-bounce">
      <Sparkles className="w-6 h-6" />
    </a>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navigation />
      <Hero />
      <Features />
      <HowItWorks />
      <Testimonials />
      <Pricing />
      <SignupForm />
      <CTASection />
      <Footer />
      <FloatingCTA />
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Network, ArrowRight, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function UpgradeBanner() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('/api/restaurants/upgrade-to-multi-branch', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!res.ok) throw new Error('Upgrade failed');
      
      // Update local context/state if needed
      window.location.reload();
      
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  if (dismissed) return null;

  return (
    <div className="mb-6 relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-50 to-emerald-50 border border-emerald-100 p-6 shadow-sm">
      <button 
        onClick={() => setDismissed(true)}
        className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
      >
        <X className="w-5 h-5" />
      </button>
      
      <div className="flex flex-col sm:flex-row items-center gap-6">
        <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-sm flex-shrink-0 border border-emerald-100">
          <Network className="w-8 h-8 text-emerald-600" />
        </div>
        
        <div className="flex-1 text-center sm:text-left">
          <h3 className="text-lg font-bold text-gray-900 mb-1">
            Opening a new location?
          </h3>
          <p className="text-sm text-gray-600 max-w-2xl">
            Upgrade to a Multi-Branch setup to manage all your locations from a single dashboard. 
            Sync menus, aggregate analytics, and share staff across branches.
          </p>
        </div>
        
        <div className="flex-shrink-0 mt-4 sm:mt-0">
          <Button 
            onClick={handleUpgrade} 
            disabled={loading}
            className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-md rounded-xl px-6"
          >
            {loading ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Upgrading...</>
            ) : (
              <>Upgrade Now <ArrowRight className="w-4 h-4 ml-2" /></>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

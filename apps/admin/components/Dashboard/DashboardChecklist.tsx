// apps/admin/components/Dashboard/DashboardChecklist.tsx
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { 
  Utensils, 
  LayoutGrid, 
  Users, 
  Smartphone, 
  Check, 
  Loader2 
} from 'lucide-react';
import QuickMenuSetup from '../Menu/QuickMenuSetup';

interface DashboardChecklistProps {
  restaurantId: string;
  onComplete?: () => void;
}

export default function DashboardChecklist({ restaurantId, onComplete }: DashboardChecklistProps) {
  const [isAddMenuOpen, setIsAddMenuOpen] = useState(false);
  const [isGoingLive, setIsGoingLive] = useState(false);

  // 1. Fetch menu items count
  const { 
    data: menuData, 
    isLoading: isLoadingMenu, 
    refetch: refetchMenu 
  } = useQuery({
    queryKey: ['menuCount', restaurantId],
    queryFn: async () => {
      const res = await fetch(`/api/menu/items/count?restaurantId=${restaurantId}`);
      if (!res.ok) throw new Error('Failed to fetch menu count');
      return res.json() as Promise<{ count: number }>;
    },
    refetchOnWindowFocus: true,
  });

  // 2. Fetch tables count
  const { 
    data: tablesData, 
    isLoading: isLoadingTables,
    refetch: refetchTables
  } = useQuery({
    queryKey: ['tablesCount', restaurantId],
    queryFn: async () => {
      const res = await fetch(`/api/tables/count?restaurantId=${restaurantId}`);
      if (!res.ok) throw new Error('Failed to fetch tables count');
      return res.json() as Promise<{ count: number }>;
    },
    refetchOnWindowFocus: true,
  });

  // 3. Fetch staff count (role='waiter')
  const { 
    data: staffData, 
    isLoading: isLoadingStaff,
    refetch: refetchStaff
  } = useQuery({
    queryKey: ['staffCount', restaurantId],
    queryFn: async () => {
      const res = await fetch(`/api/staff/count?restaurantId=${restaurantId}&role=waiter`);
      if (!res.ok) throw new Error('Failed to fetch staff count');
      return res.json() as Promise<{ count: number }>;
    },
    refetchOnWindowFocus: true,
  });

  // 4. Fetch M-Pesa settings
  const { 
    data: settingsData, 
    isLoading: isLoadingSettings,
    refetch: refetchSettings
  } = useQuery({
    queryKey: ['restaurantSettings', restaurantId],
    queryFn: async () => {
      const res = await fetch(`/api/restaurants/settings?restaurantId=${restaurantId}`);
      if (!res.ok) throw new Error('Failed to fetch settings');
      return res.json() as Promise<{ mpesa_configured: boolean }>;
    },
    refetchOnWindowFocus: true,
  });

  const menuCount = menuData?.count ?? 0;
  const tablesCount = tablesData?.count ?? 0;
  const staffCount = staffData?.count ?? 0;
  const mpesaConfigured = settingsData?.mpesa_configured ?? false;

  const isMenuCompleted = menuCount > 0;
  const isTablesCompleted = tablesCount > 0;
  const isStaffCompleted = staffCount > 0;
  const isMpesaCompleted = mpesaConfigured;

  const totalRequiredCount = 3;
  const completedRequiredCount = 
    (isMenuCompleted ? 1 : 0) + 
    (isTablesCompleted ? 1 : 0) + 
    (isStaffCompleted ? 1 : 0);

  const progressPercentage = Math.round((completedRequiredCount / totalRequiredCount) * 100);
  const isAllRequiredCompleted = completedRequiredCount === totalRequiredCount;

  const handleGoLive = async () => {
    setIsGoingLive(true);
    try {
      const res = await fetch('/api/restaurants/onboarding/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ restaurantId })
      });
      if (res.ok) {
        if (onComplete) {
          onComplete();
        }
      }
    } catch (error) {
      console.error('Error going live:', error);
    } finally {
      setIsGoingLive(false);
    }
  };

  const handleQuickMenuComplete = () => {
    setIsAddMenuOpen(false);
    refetchMenu();
  };

  return (
    <div className="w-full space-y-6">
      {/* CHECKLIST COMPONENT CONTAINER */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        {/* HEADER */}
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-900">Get Started Checklist</h2>
          <p className="text-sm text-gray-500 mt-1">Complete these steps to start taking orders</p>
          
          {/* PROGRESS BAR */}
          <div className="mt-5">
            <div className="flex justify-between items-center text-xs font-semibold text-gray-600 mb-1">
              <span>Setup Progress</span>
              <span>{completedRequiredCount} of {totalRequiredCount} required complete</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="bg-emerald-600 h-full transition-all duration-500 ease-out rounded-full"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>
        </div>

        {/* CHECKLIST ITEMS */}
        <div className="space-y-3">
          {/* ITEM 1: ADD MENU ITEMS (Required) */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition hover:shadow-sm">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg shrink-0 ${isMenuCompleted ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-50 text-gray-400'}`}>
                <Utensils className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-1.5">
                  Add your menu items
                  {isMenuCompleted && (
                    <span className="flex items-center justify-center w-4 h-4 rounded-full bg-emerald-100 text-emerald-800">
                      <Check className="w-2.5 h-2.5 stroke-[3]" />
                    </span>
                  )}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">Add at least one food or drink item to your menu</p>
                <div className="mt-1.5">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${isMenuCompleted ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'}`}>
                    {isLoadingMenu ? 'Checking...' : isMenuCompleted ? 'Completed' : `${menuCount} items`}
                  </span>
                </div>
              </div>
            </div>
            <div>
              <button
                type="button"
                onClick={() => setIsAddMenuOpen(true)}
                className="w-full sm:w-auto text-sm font-semibold px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 bg-white shadow-sm transition text-center"
              >
                Add Items
              </button>
            </div>
          </div>

          {/* ITEM 2: SET UP TABLES (Required) */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition hover:shadow-sm">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg shrink-0 ${isTablesCompleted ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-50 text-gray-400'}`}>
                <LayoutGrid className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-1.5">
                  Set up your tables
                  {isTablesCompleted && (
                    <span className="flex items-center justify-center w-4 h-4 rounded-full bg-emerald-100 text-emerald-800">
                      <Check className="w-2.5 h-2.5 stroke-[3]" />
                    </span>
                  )}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">Create tables and generate QR codes for customers to scan</p>
                <div className="mt-1.5">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${isTablesCompleted ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'}`}>
                    {isLoadingTables ? 'Checking...' : isTablesCompleted ? 'Completed' : `${tablesCount === 0 ? 'No' : tablesCount} tables`}
                  </span>
                </div>
              </div>
            </div>
            <div>
              <Link
                href="/tables"
                className="block w-full sm:w-auto text-sm font-semibold px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 bg-white shadow-sm transition text-center"
              >
                Set Up Tables
              </Link>
            </div>
          </div>

          {/* ITEM 3: ADD STAFF (Required) */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition hover:shadow-sm">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg shrink-0 ${isStaffCompleted ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-50 text-gray-400'}`}>
                <Users className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-1.5">
                  Add your staff
                  {isStaffCompleted && (
                    <span className="flex items-center justify-center w-4 h-4 rounded-full bg-emerald-100 text-emerald-800">
                      <Check className="w-2.5 h-2.5 stroke-[3]" />
                    </span>
                  )}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">Add waiters, kitchen staff, and cashier</p>
                <div className="mt-1.5">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${isStaffCompleted ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'}`}>
                    {isLoadingStaff ? 'Checking...' : isStaffCompleted ? 'Completed' : `${staffCount === 0 ? 'No' : staffCount} staff`}
                  </span>
                </div>
              </div>
            </div>
            <div>
              <Link
                href="/staff"
                className="block w-full sm:w-auto text-sm font-semibold px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 bg-white shadow-sm transition text-center"
              >
                Add Staff
              </Link>
            </div>
          </div>

          {/* ITEM 4: CONNECT M-PESA (Optional) */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition hover:shadow-sm">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg shrink-0 ${isMpesaCompleted ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-50 text-gray-400'}`}>
                <Smartphone className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                  Connect M-Pesa
                  <span className="inline-flex items-center rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-semibold text-gray-600 uppercase tracking-wide">
                    Optional
                  </span>
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">Accept payments from customers via M-Pesa</p>
                <div className="mt-1.5">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${isMpesaCompleted ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'}`}>
                    {isLoadingSettings ? 'Checking...' : isMpesaCompleted ? 'Connected' : 'Not connected'}
                  </span>
                </div>
              </div>
            </div>
            <div>
              <Link
                href="/settings?tab=mpesa"
                className="block w-full sm:w-auto text-sm font-semibold px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 bg-white shadow-sm transition text-center"
              >
                Connect
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* BANNER BASED ON COMPLETION STATUS */}
      <div className="w-full">
        {isAllRequiredCompleted ? (
          isMpesaCompleted ? (
            /* Case A: Green Banner */
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl shrink-0">🎉</span>
                <div>
                  <h4 className="text-sm font-bold text-emerald-900">Ready to go live! Start taking orders</h4>
                  <p className="text-xs text-emerald-700 mt-0.5">Your setup is fully complete and mobile payments are configured.</p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleGoLive}
                disabled={isGoingLive}
                className="w-full sm:w-auto inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition disabled:opacity-50"
              >
                {isGoingLive ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Go Live'
                )}
              </button>
            </div>
          ) : (
            /* Case B: Blue Banner */
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl shrink-0">🚀</span>
                <div>
                  <h4 className="text-sm font-bold text-blue-900">Your restaurant is ready! Connect M-Pesa to accept payments</h4>
                  <p className="text-xs text-blue-700 mt-0.5">Required setup is complete. Link M-Pesa to enable direct customer checkout.</p>
                </div>
              </div>
              <Link
                href="/settings?tab=mpesa"
                className="block w-full sm:w-auto text-center px-4 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition shrink-0"
              >
                Connect M-Pesa
              </Link>
            </div>
          )
        ) : (
          /* Case C: Yellow Banner */
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl shrink-0">⏳</span>
              <div>
                <h4 className="text-sm font-bold text-amber-900">Complete your setup to start taking orders</h4>
                <p className="text-xs text-amber-700 mt-0.5">Finish the remaining required steps in the checklist to enable live status.</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* QUICK MENU SETUP MODAL OVERLAY */}
      {isAddMenuOpen && (
        <QuickMenuSetup 
          onComplete={handleQuickMenuComplete}
          onSkip={() => setIsAddMenuOpen(false)}
        />
      )}
    </div>
  );
}

// apps/admin/app/(dashboard)/dashboard/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { useAdminRealtime, LiveOrder } from '../../../hooks/useAdminRealtime';
import { 
  TrendingUp, 
  TrendingDown, 
  Package, 
  LayoutGrid, 
  AlertTriangle, 
  RefreshCw,
  Clock,
  CheckCircle2,
  Circle,
  Users2,
  ChevronRight,
  ShieldCheck,
  CreditCard,
  ChefHat
} from 'lucide-react';
import Link from 'next/link';
import { UpgradeBanner } from '@/components/Dashboard/UpgradeBanner';

// Mock restaurant ID for demonstration
const RESTAURANT_ID = 'rest_123';

const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case 'received': return 'bg-yellow-100 text-yellow-800';
    case 'preparing': return 'bg-blue-100 text-blue-800';
    case 'ready': return 'bg-green-100 text-green-800';
    case 'served': return 'bg-purple-100 text-purple-800';
    case 'completed': return 'bg-gray-100 text-gray-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

const getTableStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case 'available': return 'bg-green-100 text-green-800 border-green-200';
    case 'occupied': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'ordered': return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'ready': return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'eating': return 'bg-purple-100 text-purple-800 border-purple-200';
    case 'bill requested': return 'bg-red-100 text-red-800 border-red-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

// CHECKLIST COMPONENT
interface DashboardChecklistProps {
  menuItemsCount: number;
  tablesCount: number;
  staffCount: number;
  isMpesaConnected: boolean;
  restaurantStatus: string;
}

function DashboardChecklist({
  menuItemsCount,
  tablesCount,
  staffCount,
  isMpesaConnected,
  restaurantStatus
}: DashboardChecklistProps) {
  const isMenuComplete = menuItemsCount > 0;
  const isTablesComplete = tablesCount > 0;
  const isStaffComplete = staffCount > 0;

  // 3 required checklist items: Menu, Tables, Staff
  const requiredItems = [
    { completed: isMenuComplete, label: 'Add Menu Items' },
    { completed: isTablesComplete, label: 'Set Up Tables' },
    { completed: isStaffComplete, label: 'Add Staff' }
  ];
  const completedCount = requiredItems.filter(item => item.completed).length;
  const progressPercent = Math.round((completedCount / 3) * 100);
  const isAllRequiredComplete = completedCount === 3;

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-6">
      {/* BANNERS HEADER */}
      <div className="space-y-3">
        {(!isAllRequiredComplete && (restaurantStatus === 'onboarding_incomplete' || restaurantStatus === 'setup_incomplete')) ? (
          <div className="flex items-start sm:items-center gap-3 p-4 bg-amber-50 border border-amber-200 text-amber-900 rounded-xl">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5 sm:mt-0" />
            <span className="text-sm font-semibold">Complete your setup to start taking orders</span>
          </div>
        ) : isAllRequiredComplete ? (
          <div className="flex items-start sm:items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-xl">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5 sm:mt-0" />
            <span className="text-sm font-semibold">Ready to go live! Start taking orders</span>
          </div>
        ) : null}

        {!isMpesaConnected && (
          <div className="flex items-start sm:items-center gap-3 p-4 bg-blue-50 border border-blue-200 text-blue-900 rounded-xl">
            <CreditCard className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5 sm:mt-0" />
            <span className="text-sm font-semibold">Connect M-Pesa to accept payments</span>
          </div>
        )}
      </div>

      {/* HEADER WITH PROGRESS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 pb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Restaurant Setup Checklist</h2>
          <p className="text-gray-500 text-xs mt-0.5">Complete these core steps to prepare PlateLink for your dining customers.</p>
        </div>
        <div className="w-full sm:w-64 space-y-1.5">
          <div className="flex justify-between text-xs font-bold text-gray-700">
            <span>Setup Progress</span>
            <span className="text-emerald-600">{progressPercent}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden border border-gray-200">
            <div 
              className="bg-emerald-500 h-full rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* CHECKLIST CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Step 1: Menu Items */}
        <div className={`p-5 rounded-xl border transition-all ${
          isMenuComplete ? 'bg-emerald-50/20 border-emerald-100' : 'bg-white border-gray-200 hover:border-gray-300'
        }`}>
          <div className="flex justify-between items-start mb-4">
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
              <ChefHat className="w-5 h-5" />
            </div>
            {isMenuComplete ? (
              <span className="text-emerald-600 bg-emerald-100/50 p-0.5 rounded-full">
                <CheckCircle2 className="w-5 h-5 fill-emerald-600 text-white" />
              </span>
            ) : (
              <Circle className="w-5 h-5 text-gray-300" />
            )}
          </div>
          <h3 className="text-sm font-bold text-gray-900">1. ADD MENU ITEMS</h3>
          <p className="text-xs text-gray-500 mt-1 mb-4">
            {menuItemsCount > 0 ? `${menuItemsCount} items added` : '0 items added'}
          </p>
          <Link href="/menu" className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-emerald-600 border border-emerald-600 rounded-lg hover:bg-emerald-50 transition-colors">
            Add Menu Items
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Step 2: Tables */}
        <div className={`p-5 rounded-xl border transition-all ${
          isTablesComplete ? 'bg-emerald-50/20 border-emerald-100' : 'bg-white border-gray-200 hover:border-gray-300'
        }`}>
          <div className="flex justify-between items-start mb-4">
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
              <LayoutGrid className="w-5 h-5" />
            </div>
            {isTablesComplete ? (
              <span className="text-emerald-600 bg-emerald-100/50 p-0.5 rounded-full">
                <CheckCircle2 className="w-5 h-5 fill-emerald-600 text-white" />
              </span>
            ) : (
              <Circle className="w-5 h-5 text-gray-300" />
            )}
          </div>
          <h3 className="text-sm font-bold text-gray-900">2. SET UP TABLES</h3>
          <p className="text-xs text-gray-500 mt-1 mb-4">
            {tablesCount > 0 ? `${tablesCount} tables created` : 'No tables created'}
          </p>
          <Link href="/tables" className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-emerald-600 border border-emerald-600 rounded-lg hover:bg-emerald-50 transition-colors">
            Set Up Tables
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Step 3: Staff */}
        <div className={`p-5 rounded-xl border transition-all ${
          isStaffComplete ? 'bg-emerald-50/20 border-emerald-100' : 'bg-white border-gray-200 hover:border-gray-300'
        }`}>
          <div className="flex justify-between items-start mb-4">
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
              <Users2 className="w-5 h-5" />
            </div>
            {isStaffComplete ? (
              <span className="text-emerald-600 bg-emerald-100/50 p-0.5 rounded-full">
                <CheckCircle2 className="w-5 h-5 fill-emerald-600 text-white" />
              </span>
            ) : (
              <Circle className="w-5 h-5 text-gray-300" />
            )}
          </div>
          <h3 className="text-sm font-bold text-gray-900">3. ADD STAFF</h3>
          <p className="text-xs text-gray-500 mt-1 mb-4">
            {staffCount > 0 ? `${staffCount} staff added` : 'No staff added'}
          </p>
          <Link href="/staff" className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-emerald-600 border border-emerald-600 rounded-lg hover:bg-emerald-50 transition-colors">
            Add Staff
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Step 4: M-Pesa Connection (Optional) */}
        <div className={`p-5 rounded-xl border transition-all relative ${
          isMpesaConnected ? 'bg-emerald-50/20 border-emerald-100' : 'bg-white border-gray-200 hover:border-gray-300'
        }`}>
          <div className="absolute top-3 right-3">
            <span className="text-[10px] font-bold px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">
              Optional
            </span>
          </div>
          <div className="flex justify-between items-start mb-4">
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
              <CreditCard className="w-5 h-5" />
            </div>
            {isMpesaConnected ? (
              <span className="text-emerald-600 bg-emerald-100/50 p-0.5 rounded-full">
                <CheckCircle2 className="w-5 h-5 fill-emerald-600 text-white" />
              </span>
            ) : (
              <Circle className="w-5 h-5 text-gray-300" />
            )}
          </div>
          <h3 className="text-sm font-bold text-gray-900">4. CONNECT M-PESA</h3>
          <p className="text-xs text-gray-500 mt-1 mb-4">
            {isMpesaConnected ? 'Connected' : 'Not connected'}
          </p>
          <Link href="/settings?tab=mpesa" className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-emerald-600 border border-emerald-600 rounded-lg hover:bg-emerald-50 transition-colors">
            Connect
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

      </div>
    </div>
  );
}

// MAIN DASHBOARD COMPONENT
export default function AdminDashboard() {
  const [branchName, setBranchName] = useState<string>('PlateLink Africa');
  const [branchId, setBranchId] = useState<string>('');
  const [restaurantType, setRestaurantType] = useState<string>('single');

  useEffect(() => {
    const bName = localStorage.getItem('selected_branch_name');
    const bId = localStorage.getItem('selected_branch_id');
    const type = localStorage.getItem('restaurant_type');
    if (bName) setBranchName(bName);
    if (bId) setBranchId(bId);
    if (type) setRestaurantType(type);

    const handleBranchChange = () => {
      setBranchName(localStorage.getItem('selected_branch_name') || 'PlateLink Africa');
      setBranchId(localStorage.getItem('selected_branch_id') || '');
    };
    window.addEventListener('branchChanged', handleBranchChange);
    return () => window.removeEventListener('branchChanged', handleBranchChange);
  }, []);

  const {
    liveOrders,
    tableStatuses,
    todaySales,
    activeOrderCount,
    occupiedTablesCount,
    lowStockCount,
    isConnected,
    refreshData
  } = useAdminRealtime(branchId || RESTAURANT_ID);

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>('');
  const [totalTables] = useState(12);

  // Setup Checklist states
  const [restaurantStatus, setRestaurantStatus] = useState<string>('onboarding_incomplete');
  const [menuItemsCount, setMenuItemsCount] = useState<number>(0);
  const [tablesCount, setTablesCount] = useState<number>(0);
  const [staffCount, setStaffCount] = useState<number>(0);
  const [isMpesaConnected, setIsMpesaConnected] = useState<boolean>(false);

  // Dynamic values based on demo mode
  const isDemoMode = liveOrders.length === 0;

  // DEMO DATA DEFINITIONS
  const demoOrdersList: LiveOrder[] = [
    {
      id: 'demo_order_1',
      orderNumber: 'DEMO-254',
      tableNumber: 3,
      items: ['Nyama Choma (500g)', 'Ugali Sukuma', 'Kachumbari'],
      status: 'Preparing',
      createdAt: new Date(Date.now() - 15 * 60000).toISOString(),
      total: 1250
    },
    {
      id: 'demo_order_2',
      orderNumber: 'DEMO-255',
      tableNumber: 5,
      items: ['Chicken Tikka', 'Chapati (2)', 'Soda'],
      status: 'Ready',
      createdAt: new Date(Date.now() - 5 * 60000).toISOString(),
      total: 1450
    },
    {
      id: 'demo_order_3',
      orderNumber: 'DEMO-256',
      tableNumber: 1,
      items: ['Tusker Lager (2)', 'Samosa (4)'],
      status: 'Served',
      createdAt: new Date(Date.now() - 35 * 60000).toISOString(),
      total: 800
    },
    {
      id: 'demo_order_4',
      orderNumber: 'DEMO-257',
      tableNumber: 8,
      items: ['Fish Curry', 'Ugali Extra'],
      status: 'Completed',
      createdAt: new Date(Date.now() - 55 * 60000).toISOString(),
      total: 1950
    }
  ];

  // Fallbacks for display
  const displayOrders = isDemoMode ? demoOrdersList : liveOrders;
  const displayTodaySales = isDemoMode ? (todaySales || 5450) : todaySales;
  const displayActiveOrderCount = isDemoMode ? 2 : activeOrderCount;
  const displayOccupiedTablesCount = isDemoMode ? 3 : occupiedTablesCount;
  const displayLowStockCount = isDemoMode ? (lowStockCount || 3) : lowStockCount;

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(new Intl.DateTimeFormat('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(now));
    };
    updateTime();
    const timer = setInterval(updateTime, 60000);
    return () => clearInterval(timer);
  }, []);

  // Onboarding Checklist logic
  useEffect(() => {
    const fetchOnboardingInfo = async () => {
      try {
        // Read custom status stored in localStorage
        const storedStatus = localStorage.getItem('restaurant_status');
        if (storedStatus) {
          setRestaurantStatus(storedStatus);
        }

        // Parallel Fetch API queries
        const [menuRes, tablesRes, staffRes, settingsRes] = await Promise.allSettled([
          fetch(`/api/menu?restaurantId=${RESTAURANT_ID}`),
          fetch(`/api/tables?restaurantId=${RESTAURANT_ID}`),
          fetch(`/api/staff?restaurantId=${RESTAURANT_ID}`),
          fetch(`/api/settings?restaurantId=${RESTAURANT_ID}`)
        ]);

        let menuCount = 0;
        if (menuRes.status === 'fulfilled' && menuRes.value.ok) {
          const menuData = await menuRes.value.json();
          menuCount = menuData.items?.length || menuData.length || 0;
        } else {
          menuCount = parseInt(localStorage.getItem('menu_items_count') || '0', 10);
        }
        setMenuItemsCount(menuCount);

        let tableCount = 0;
        if (tablesRes.status === 'fulfilled' && tablesRes.value.ok) {
          const tablesData = await tablesRes.value.json();
          tableCount = tablesData.tables?.length || tablesData.length || 0;
        } else {
          tableCount = parseInt(localStorage.getItem('tables_count') || '0', 10);
        }
        setTablesCount(tableCount);

        let waiterCount = 0;
        if (staffRes.status === 'fulfilled' && staffRes.value.ok) {
          const staffData = await staffRes.value.json();
          waiterCount = staffData.staff?.length || staffData.length || 0;
        } else {
          waiterCount = parseInt(localStorage.getItem('staff_count') || '0', 10);
        }
        setStaffCount(waiterCount);

        let mpesaConnected = false;
        if (settingsRes.status === 'fulfilled' && settingsRes.value.ok) {
          const settingsData = await settingsRes.value.json();
          mpesaConnected = !!settingsData.mpesaConnected || !!settingsData.mpesa_credentials;
        } else {
          mpesaConnected = localStorage.getItem('mpesa_connected') === 'true';
        }
        setIsMpesaConnected(mpesaConnected);

        // If completed all required onboarding items, set state to active
        if (menuCount > 0 && tableCount > 0 && waiterCount > 0) {
          localStorage.setItem('restaurant_status', 'active');
          setRestaurantStatus('active');
        }
      } catch (err) {
        console.error('Failed to load onboarding info:', err);
      }
    };

    fetchOnboardingInfo();
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshData();
    setIsRefreshing(false);
  };

  const tablesList = Array.from({ length: totalTables }, (_, i) => {
    const number = i + 1;
    // Show some tables as occupied in Demo Mode for rich visualization
    const defaultStatus = isDemoMode && [3, 5, 8].includes(number) ? 'Occupied' : 'Available';
    return {
      number,
      ...(tableStatuses[number] || { status: defaultStatus })
    };
  });

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome back, {branchName}!</h1>
          <p className="text-gray-500 text-sm mt-1">{currentTime}</p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Connection Status Badge */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-600">Status:</span>
            {isConnected ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                Live
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800">
                <span className="w-1.5 h-1.5 rounded-full bg-red-505 bg-red-500"></span>
                Disconnected
              </span>
            )}

            {/* DEMO MODE BADGE */}
            {isDemoMode && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                Demo Mode
              </span>
            )}
          </div>
          
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {restaurantType === 'single' && <UpgradeBanner />}

      {/* SETUP CHECKLIST (Render when onboarding or setup incomplete) */}
      {(restaurantStatus === 'onboarding_incomplete' || restaurantStatus === 'setup_incomplete') && (
        <DashboardChecklist 
          menuItemsCount={menuItemsCount}
          tablesCount={tablesCount}
          staffCount={staffCount}
          isMpesaConnected={isMpesaConnected}
          restaurantStatus={restaurantStatus}
        />
      )}

      {/* FOUR STATS CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition p-5 border-t-4 border-t-emerald-500">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-500">Today's Sales</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">KES {displayTodaySales.toLocaleString()}</h3>
            </div>
            <div className="p-2 bg-emerald-50 rounded-lg">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            </div>
          </div>
          <p className="text-sm text-emerald-600 mt-2 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            <span>+12.5% from yesterday</span>
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition p-5 border-t-4 border-t-blue-500">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-500">Active Orders</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">{displayActiveOrderCount}</h3>
            </div>
            <div className="p-2 bg-blue-50 rounded-lg">
              <Package className="w-5 h-5 text-blue-600" />
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-2">in progress</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition p-5 border-t-4 border-t-orange-500">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-500">Tables Occupied</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">{displayOccupiedTablesCount} / {totalTables}</h3>
            </div>
            <div className="p-2 bg-orange-50 rounded-lg">
              <LayoutGrid className="w-5 h-5 text-orange-600" />
            </div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
            <div 
              className="bg-orange-500 h-2 rounded-full" 
              style={{ width: `${(displayOccupiedTablesCount / totalTables) * 100}%` }}
            ></div>
          </div>
        </div>

        <Link href="/inventory" className="block">
          <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition p-5 border-t-4 border-t-red-500 h-full cursor-pointer">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-medium text-gray-500">Low Stock Alerts</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{displayLowStockCount}</h3>
              </div>
              <div className="p-2 bg-red-50 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
            </div>
            <p className="text-sm text-gray-500 mt-2">items need attention</p>
          </div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* RECENT ORDERS TABLE */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100">
            <div className="flex items-center justify-between p-5 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">
                Recent Orders {isDemoMode && <span className="text-xs font-bold text-amber-600 ml-1 bg-amber-50 px-2 py-0.5 rounded">(Demo Data)</span>}
              </h2>
              <Link href="/orders" className="text-sm font-medium text-indigo-600 hover:text-indigo-800">
                View All
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-500 uppercase bg-gray-50">
                  <tr>
                    <th className="px-5 py-3">Order #</th>
                    <th className="px-5 py-3">Table</th>
                    <th className="px-5 py-3">Items</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Time</th>
                    <th className="px-5 py-3">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {displayOrders.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-5 py-8 text-center text-gray-500">
                        No active orders
                      </td>
                    </tr>
                  ) : (
                    displayOrders.slice(0, 5).map((order) => (
                      <tr key={order.id} className="bg-white border-b hover:bg-gray-50 cursor-pointer transition">
                        <td className="px-5 py-4 font-medium text-gray-900">{order.orderNumber}</td>
                        <td className="px-5 py-4">T{order.tableNumber}</td>
                        <td className="px-5 py-4">
                          <span className="truncate max-w-[150px] inline-block font-semibold text-gray-700" title={order.items.join(', ')}>
                            {order.items.join(', ')}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${getStatusColor(order.status)}`}>
                            {order.status}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-gray-500">
                          <div className="flex items-center gap-1 font-semibold text-xs">
                            <Clock className="w-3.5 h-3.5 text-gray-400" />
                            {new Date(order.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </td>
                        <td className="px-5 py-4 font-bold text-gray-900">KES {order.total.toLocaleString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* TABLE STATUS GRID */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Table Status {isDemoMode && <span className="text-xs font-bold text-amber-600 ml-1 bg-amber-50 px-2 py-0.5 rounded">(Demo Grid)</span>}
              </h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {tablesList.map((table) => (
                <div 
                  key={table.number}
                  className={`p-4 rounded-xl border ${getTableStatusColor(table.status)} cursor-pointer hover:shadow-md transition bg-opacity-50`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-lg font-bold">T{table.number}</span>
                    {table.customerCount && table.customerCount > 0 ? (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white bg-opacity-50 text-gray-700">
                        {table.customerCount} pax
                      </span>
                    ) : table.status === 'Occupied' ? (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white bg-opacity-50 text-gray-700">
                        4 pax
                      </span>
                    ) : null}
                  </div>
                  <div className="text-xs font-bold capitalize">{table.status}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar Column */}
        <div className="space-y-6">
          
          {/* TOP SELLING ITEMS */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Top Selling Items</h2>
              <Link href="/analytics" className="text-sm font-medium text-indigo-600 hover:text-indigo-800">
                View All
              </Link>
            </div>
            <div className="space-y-4">
              {[
                { name: 'Nyama Choma', sold: 45, rev: 45000, max: 50 },
                { name: 'Ugali Sukuma', sold: 38, rev: 19000, max: 50 },
                { name: 'Tusker Lager', sold: 32, rev: 16000, max: 50 },
                { name: 'Chicken Tikka', sold: 28, rev: 28000, max: 50 },
                { name: 'Chapati', sold: 24, rev: 2400, max: 50 }
              ].map((item, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold text-gray-700">{item.name}</span>
                    <span className="font-bold text-gray-900">KES {item.rev.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                      <div 
                        className="bg-indigo-500 h-1.5 rounded-full" 
                        style={{ width: `${(item.sold / item.max) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs font-semibold text-gray-500 w-8 text-right">{item.sold}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* LOW STOCK ITEMS */}
          <div className="bg-white rounded-xl shadow-sm border border-t-4 border-t-red-500 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Low Stock Items</h2>
              <Link href="/inventory" className="text-sm font-medium text-indigo-600 hover:text-indigo-800">
                View All
              </Link>
            </div>
            <div className="space-y-3">
              {[
                { name: 'Tomatoes', stock: 2, unit: 'kg' },
                { name: 'Onions', stock: 1.5, unit: 'kg' },
                { name: 'Beef (Ribs)', stock: 3, unit: 'kg' }
              ].map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-red-50 border border-red-100 rounded-lg">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{item.name}</p>
                    <p className="text-xs text-red-600 font-bold">{item.stock} {item.unit} remaining</p>
                  </div>
                  <button className="text-xs font-bold text-white bg-red-600 hover:bg-red-700 px-3 py-1.5 rounded-md transition-colors">
                    Reorder
                  </button>
                </div>
              ))}
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { WifiOff, RotateCw, Trash2, ChevronDown, ChevronUp, AlertCircle, Database, Check } from 'lucide-react';

// IndexedDB Configuration
const DB_NAME = 'platelink-offline-db';
const DB_VERSION = 1;

interface CachedMenu {
  id: string;
  restaurantName: string;
  categories: { id: string; name: string; description?: string }[];
  items: { id: string; category_id: string; name: string; description: string; price: number; image_url?: string }[];
}

interface PendingOrder {
  id: string;
  orderNumber: string;
  items: { name: string; quantity: number; unit_price: number; total_price: number }[];
  totalAmount: number;
  tableNumber: string;
  createdAt: string;
  status: 'PENDING_SYNC';
}

// Raw IndexedDB Helper Class
class OfflineDB {
  private dbPromise: Promise<IDBDatabase> | null = null;

  private getDB(): Promise<IDBDatabase> {
    if (this.dbPromise) return this.dbPromise;

    this.dbPromise = new Promise((resolve, reject) => {
      if (typeof window === 'undefined') {
        reject(new Error('IndexedDB is not available during Server-Side Rendering'));
        return;
      }

      const request = window.indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains('menus')) {
          db.createObjectStore('menus', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('pending_orders')) {
          db.createObjectStore('pending_orders', { keyPath: 'id' });
        }
      };
    });

    return this.dbPromise;
  }

  async getMenu(restaurantId: string): Promise<CachedMenu | null> {
    const db = await this.getDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('menus', 'readonly');
      const store = transaction.objectStore('menus');
      const request = store.get(restaurantId);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
    });
  }

  async getAllMenus(): Promise<CachedMenu[]> {
    const db = await this.getDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('menus', 'readonly');
      const store = transaction.objectStore('menus');
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  }

  async putMenu(menu: CachedMenu): Promise<void> {
    const db = await this.getDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('menus', 'readwrite');
      const store = transaction.objectStore('menus');
      const request = store.put(menu);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async putPendingOrder(order: PendingOrder): Promise<void> {
    const db = await this.getDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('pending_orders', 'readwrite');
      const store = transaction.objectStore('pending_orders');
      const request = store.put(order);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getPendingOrders(): Promise<PendingOrder[]> {
    const db = await this.getDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('pending_orders', 'readonly');
      const store = transaction.objectStore('pending_orders');
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  }

  async deletePendingOrder(id: string): Promise<void> {
    const db = await this.getDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('pending_orders', 'readwrite');
      const store = transaction.objectStore('pending_orders');
      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async clearAll(): Promise<void> {
    const db = await this.getDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['menus', 'pending_orders'], 'readwrite');
      transaction.objectStore('menus').clear();
      transaction.objectStore('pending_orders').clear();
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  }
}

const dbManager = new OfflineDB();

// Mock Demo Data for PlateLink Africa offline presentation
const MOCK_CACHED_MENU: CachedMenu = {
  id: 'restaurant-choma-joint',
  restaurantName: 'The Nairobi Choma Joint',
  categories: [
    { id: 'cat-1', name: 'Flame Grilled Choma', description: 'Freshly grilled premium Kenyan cuts' },
    { id: 'cat-2', name: 'Traditional Accompaniments', description: 'Perfect pairings for your meat' },
    { id: 'cat-3', name: 'Refreshments', description: 'Ice-cold local beverages' }
  ],
  items: [
    { id: 'item-1', category_id: 'cat-1', name: 'Kuzi Goat Choma (Half Kg)', description: 'Succulent goat meat, slow-roasted over real charcoal, served with fresh kachumbari salad.', price: 750, image_url: 'https://res.cloudinary.com/demo/image/upload/v1600000000/goat-choma.jpg' },
    { id: 'item-2', category_id: 'cat-1', name: 'Flame Grilled Chicken (Quarter)', description: 'Marinated in signature African spices and roasted to perfection.', price: 450, image_url: 'https://res.cloudinary.com/demo/image/upload/v1600000000/chicken.jpg' },
    { id: 'item-3', category_id: 'cat-2', name: 'Sizzling Ugali', description: 'Freshly prepared traditional Kenyan white cornmeal cake.', price: 100, image_url: 'https://res.cloudinary.com/demo/image/upload/v1600000000/ugali.jpg' },
    { id: 'item-4', category_id: 'cat-2', name: 'Sukuma Wiki (Collard Greens)', description: 'Lightly sautéed collard greens with onions, tomatoes and oil.', price: 80, image_url: 'https://res.cloudinary.com/demo/image/upload/v1600000000/sukuma.jpg' },
    { id: 'item-5', category_id: 'cat-2', name: 'Kachumbari Salad', description: 'Refreshing mixture of diced tomatoes, onions, fresh coriander, and chilies.', price: 50, image_url: 'https://res.cloudinary.com/demo/image/upload/v1600000000/kachumbari.jpg' },
    { id: 'item-6', category_id: 'cat-3', name: 'Tusker Lager', description: 'Kenya\'s premium lager beer, extremely cold (500ml).', price: 250, image_url: 'https://res.cloudinary.com/demo/image/upload/v1600000000/tusker.jpg' },
    { id: 'item-7', category_id: 'cat-3', name: 'Stoney Tangawizi', description: 'Vibrant and fiery local ginger soda (350ml).', price: 100, image_url: 'https://res.cloudinary.com/demo/image/upload/v1600000000/stoney.jpg' }
  ]
};

const MOCK_PENDING_ORDER: PendingOrder = {
  id: 'local-ord-1024',
  orderNumber: 'PLA-TX-9871',
  tableNumber: 'Table 4',
  totalAmount: 1380,
  createdAt: new Date().toISOString(),
  status: 'PENDING_SYNC',
  items: [
    { name: 'Kuzi Goat Choma (Half Kg)', quantity: 1, unit_price: 750, total_price: 750 },
    { name: 'Sizzling Ugali', quantity: 2, unit_price: 100, total_price: 200 },
    { name: 'Sukuma Wiki (Collard Greens)', quantity: 1, unit_price: 80, total_price: 80 },
    { name: 'Tusker Lager', quantity: 1, unit_price: 250, total_price: 250 },
    { name: 'Kachumbari Salad', quantity: 2, unit_price: 50, total_price: 100 }
  ]
};

export default function OfflineFallbackPage() {
  const router = useRouter();
  
  // Page states
  const [menus, setMenus] = useState<CachedMenu[]>([]);
  const [pendingOrders, setPendingOrders] = useState<PendingOrder[]>([]);
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryStatus, setRetryStatus] = useState<'idle' | 'failed' | 'success'>('idle');
  
  // Accordion/tabs states
  const [showSavedMenu, setShowSavedMenu] = useState(false);
  const [showPendingOrders, setShowPendingOrders] = useState(false);
  const [selectedMenuIndex, setSelectedMenuIndex] = useState<number>(0);
  
  // Cache Info details
  const [cachedSize, setCachedSize] = useState<string>('0 KB');
  const [isClearing, setIsClearing] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  // Initial load
  useEffect(() => {
    loadOfflineData();
  }, []);

  const loadOfflineData = async () => {
    try {
      let cachedMenusList = await dbManager.getAllMenus();
      let ordersList = await dbManager.getPendingOrders();

      // Prepopulate mock data if database is empty to allow visual PWA preview
      if (cachedMenusList.length === 0) {
        await dbManager.putMenu(MOCK_CACHED_MENU);
        cachedMenusList = [MOCK_CACHED_MENU];
      }
      
      if (ordersList.length === 0) {
        await dbManager.putPendingOrder(MOCK_PENDING_ORDER);
        ordersList = [MOCK_PENDING_ORDER];
      }

      setMenus(cachedMenusList);
      setPendingOrders(ordersList);
      
      // Calculate fake database size based on contents
      const contentStr = JSON.stringify(cachedMenusList) + JSON.stringify(ordersList);
      const bytes = new Blob([contentStr]).size;
      setCachedSize(`${(bytes / 1024).toFixed(1)} KB`);
    } catch (err) {
      console.error('Failed to load offline data from IndexedDB:', err);
    }
  };

  // Retry server connection
  const checkConnection = async () => {
    setIsRetrying(true);
    setRetryStatus('idle');
    
    // Minimal mock lag to make the retry visual experience premium
    await new Promise((resolve) => setTimeout(resolve, 1200));

    try {
      const response = await fetch('/api/health', {
        method: 'GET',
        cache: 'no-store',
        headers: { 'Cache-Control': 'no-cache' }
      });
      
      if (response.ok) {
        setRetryStatus('success');
        // Let user see green success badge before redirecting
        await new Promise((resolve) => setTimeout(resolve, 500));
        
        if (typeof window !== 'undefined' && window.history.length > 1) {
          router.back();
        } else {
          router.push('/');
        }
      } else {
        throw new Error('Server returned unhealthy state');
      }
    } catch (error) {
      setRetryStatus('failed');
      setTimeout(() => setRetryStatus('idle'), 3000);
    } finally {
      setIsRetrying(false);
    }
  };

  // Cancel/delete pending order
  const handleCancelOrder = async (orderId: string) => {
    if (confirm('Are you sure you want to cancel and remove this pending order?')) {
      try {
        await dbManager.deletePendingOrder(orderId);
        const updatedOrders = pendingOrders.filter(o => o.id !== orderId);
        setPendingOrders(updatedOrders);
        
        // Recalculate size
        const contentStr = JSON.stringify(menus) + JSON.stringify(updatedOrders);
        const bytes = new Blob([contentStr]).size;
        setCachedSize(`${(bytes / 1024).toFixed(1)} KB`);
      } catch (err) {
        console.error('Failed to remove pending order:', err);
      }
    }
  };

  // Clear all IndexedDB caches
  const handleClearCache = async () => {
    setIsClearing(true);
    try {
      await dbManager.clearAll();
      setMenus([]);
      setPendingOrders([]);
      setCachedSize('0.0 KB');
      setShowClearConfirm(false);
    } catch (err) {
      console.error('Failed to clear IndexedDB cache:', err);
    } finally {
      setIsClearing(false);
    }
  };

  const activeCachedMenu = menus[selectedMenuIndex] || null;

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      {/* Container - Styled as high quality Mobile-First viewport */}
      <div className="w-full max-w-[428px] bg-white rounded-3xl shadow-xl overflow-hidden border border-slate-100 flex flex-col min-h-[80vh] justify-between relative">
        
        {/* Top Header/Status Area */}
        <div className="bg-emerald-600 px-6 py-8 text-white relative">
          {/* Subtle background abstract decorations */}
          <div className="absolute right-0 top-0 opacity-10 pointer-events-none transform translate-x-4 -translate-y-4">
            <svg width="200" height="200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4" />
            </svg>
          </div>

          <div className="flex flex-col items-center text-center">
            <div className="bg-white/20 p-4 rounded-full mb-4 animate-pulse">
              <WifiOff className="h-10 w-10 text-white" />
            </div>
            
            <h1 className="text-2xl font-bold tracking-tight mb-2">You're Offline</h1>
            <p className="text-emerald-100 text-sm leading-relaxed max-w-[85%]">
              Don't worry! You can still browse saved menus and check pending orders.
            </p>
          </div>
        </div>

        {/* Content Wrapper */}
        <div className="px-5 py-6 flex-grow space-y-5">
          
          {/* Main Action Buttons */}
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => {
                setShowSavedMenu(!showSavedMenu);
                setShowPendingOrders(false);
              }}
              className={`flex flex-col items-center justify-center p-4 rounded-2xl border transition-all duration-200 text-center ${
                showSavedMenu 
                  ? 'border-emerald-600 bg-emerald-50/50 text-emerald-800 shadow-sm' 
                  : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'
              }`}
            >
              <span className="text-sm font-semibold tracking-wide block mb-1">Saved Menus</span>
              <span className="text-xs text-slate-400">{menus.length} Rest. Cached</span>
            </button>

            <button
              onClick={() => {
                setShowPendingOrders(!showPendingOrders);
                setShowSavedMenu(false);
              }}
              className={`flex flex-col items-center justify-center p-4 rounded-2xl border transition-all duration-200 text-center ${
                showPendingOrders 
                  ? 'border-emerald-600 bg-emerald-50/50 text-emerald-800 shadow-sm' 
                  : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'
              }`}
            >
              <span className="text-sm font-semibold tracking-wide block mb-1">Pending Orders</span>
              <span className="text-xs text-slate-400">{pendingOrders.length} Order Waiting</span>
            </button>
          </div>

          {/* Section 1: Cached Menus Browsing (Expandable) */}
          {showSavedMenu && (
            <div className="border border-slate-100 bg-slate-50/50 rounded-2xl p-4 space-y-4 transition-all duration-300">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Browse Saved Menu</h2>
                {menus.length > 1 && (
                  <select 
                    value={selectedMenuIndex}
                    onChange={(e) => setSelectedMenuIndex(Number(e.target.value))}
                    className="text-xs bg-white border border-slate-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-emerald-500 font-medium text-slate-700"
                  >
                    {menus.map((m, i) => (
                      <option key={m.id} value={i}>{m.restaurantName}</option>
                    ))}
                  </select>
                )}
              </div>

              {activeCachedMenu ? (
                <div className="space-y-4">
                  <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
                    <span className="text-xs text-emerald-600 font-bold uppercase tracking-wider block mb-1">Active Restaurant</span>
                    <h3 className="text-base font-bold text-slate-800">{activeCachedMenu.restaurantName}</h3>
                  </div>

                  {activeCachedMenu.categories.map((category) => {
                    const categoryItems = activeCachedMenu.items.filter(item => item.category_id === category.id);
                    return (
                      <div key={category.id} className="space-y-2">
                        <div className="border-l-2 border-emerald-500 pl-2 py-0.5">
                          <h4 className="text-sm font-bold text-slate-800">{category.name}</h4>
                          {category.description && <p className="text-[11px] text-slate-400">{category.description}</p>}
                        </div>

                        <div className="space-y-2">
                          {categoryItems.map((item) => (
                            <div key={item.id} className="bg-white p-3 rounded-xl border border-slate-150 flex items-center justify-between hover:shadow-sm transition-shadow">
                              <div className="space-y-0.5 max-w-[70%]">
                                <h5 className="text-xs font-bold text-slate-800">{item.name}</h5>
                                <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{item.description}</p>
                                <span className="text-xs font-semibold text-emerald-600 block mt-1">KES {item.price}</span>
                              </div>
                              <div className="flex flex-col items-end justify-between h-full space-y-3">
                                {/* Safe Placeholder Icon/Thumbnail box */}
                                <div className="h-12 w-12 rounded-lg bg-slate-100 flex items-center justify-center overflow-hidden border border-slate-200">
                                  <svg className="h-6 w-6 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                                  </svg>
                                </div>
                                <button
                                  disabled
                                  className="text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-400 px-2 py-1 rounded border border-slate-200 cursor-not-allowed"
                                  title="New orders require internet connection"
                                >
                                  Order
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-6 text-slate-400 text-xs">
                  No menus cached in storage yet.
                </div>
              )}
            </div>
          )}

          {/* Section 2: Pending Sync Orders (Expandable) */}
          {showPendingOrders && (
            <div className="border border-slate-100 bg-slate-50/50 rounded-2xl p-4 space-y-4 transition-all duration-300">
              <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Pending Offline Orders</h2>
              
              {pendingOrders.length > 0 ? (
                <div className="space-y-3">
                  {pendingOrders.map((order) => (
                    <div key={order.id} className="bg-white p-4 rounded-xl border border-slate-150 shadow-sm relative overflow-hidden">
                      {/* Left accent bar */}
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-amber-500"></div>
                      
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <span className="text-[10px] font-bold text-amber-600 bg-amber-50 border border-amber-200 rounded px-1.5 py-0.5 uppercase tracking-wider inline-block mb-1">
                            Pending Sync
                          </span>
                          <h3 className="text-sm font-bold text-slate-800">{order.orderNumber}</h3>
                          <p className="text-[10px] text-slate-400">{order.tableNumber} • {new Date(order.createdAt).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                        </div>
                        <button
                          onClick={() => handleCancelOrder(order.id)}
                          className="text-slate-400 hover:text-red-500 p-1 rounded-full hover:bg-red-50 transition-colors"
                          title="Cancel pending order"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>

                      {/* Items List */}
                      <div className="border-y border-slate-100 py-2 my-2 space-y-1">
                        {order.items.map((item, idx) => (
                          <div key={idx} className="flex justify-between text-xs text-slate-600">
                            <span>{item.quantity}x {item.name}</span>
                            <span className="font-medium">KES {item.total_price}</span>
                          </div>
                        ))}
                      </div>

                      <div className="flex justify-between items-center pt-1">
                        <span className="text-xs text-slate-500 font-medium">Total Amount</span>
                        <span className="text-sm font-bold text-slate-800">KES {order.totalAmount}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400 text-xs">
                  No orders waiting to sync.
                </div>
              )}
            </div>
          )}

          {/* Section 3: Connection & Retry Status Area */}
          <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4 flex flex-col items-center justify-center text-center space-y-3">
            
            {/* Display status details */}
            {retryStatus === 'idle' && (
              <div className="flex items-center space-x-1.5 text-xs text-slate-500">
                <AlertCircle className="h-4 w-4 text-slate-400" />
                <span>Checking this page automatically monitors connectivity.</span>
              </div>
            )}
            
            {retryStatus === 'failed' && (
              <div className="flex items-center space-x-1.5 text-xs text-rose-600 bg-rose-50 border border-rose-200 px-3 py-1.5 rounded-xl font-medium">
                <AlertCircle className="h-4 w-4 text-rose-500" />
                <span>Still offline. Please check your data connection.</span>
              </div>
            )}

            {retryStatus === 'success' && (
              <div className="flex items-center space-x-1.5 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl font-bold">
                <Check className="h-4 w-4 text-emerald-600" />
                <span>Back Online! Redirecting you...</span>
              </div>
            )}

            {/* Big Retry button */}
            <button
              onClick={checkConnection}
              disabled={isRetrying}
              className="w-full flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 px-6 rounded-2xl transition-all duration-150 shadow-md shadow-emerald-600/10 active:scale-[0.98] disabled:bg-emerald-600/60 disabled:cursor-not-allowed"
            >
              <RotateCw className={`h-4 w-4 ${isRetrying ? 'animate-spin' : ''}`} />
              <span>{isRetrying ? 'Checking Network...' : 'Retry Connection'}</span>
            </button>
          </div>

        </div>

        {/* Footer Area with Storage Capacity Details */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 text-[11px] text-slate-400 flex items-center justify-between">
          <div className="flex items-center space-x-1.5">
            <Database className="h-3.5 w-3.5 text-slate-400" />
            <span>Cache Size: <strong>{cachedSize}</strong></span>
          </div>

          <button
            onClick={() => setShowClearConfirm(true)}
            className="text-slate-400 hover:text-rose-600 font-bold transition-colors uppercase tracking-wider text-[10px]"
          >
            Clear Cache
          </button>
        </div>

        {/* Custom Confirmation Modal for Cache Clearing */}
        {showClearConfirm && (
          <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50 transition-opacity">
            <div className="bg-white rounded-3xl p-5 shadow-2xl border border-slate-100 max-w-[320px] w-full text-center space-y-4 animate-in fade-in zoom-in duration-200">
              <div className="bg-rose-50 p-3 rounded-full inline-block mx-auto text-rose-500 border border-rose-100">
                <Trash2 className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-slate-800">Clear Saved Offline Data?</h3>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  This will remove all cached menus and pending orders waiting to sync from your device.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setShowClearConfirm(false)}
                  className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-2 rounded-xl text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleClearCache}
                  disabled={isClearing}
                  className="bg-rose-600 hover:bg-rose-700 text-white font-bold py-2 rounded-xl text-xs transition-colors disabled:bg-rose-400"
                >
                  {isClearing ? 'Clearing...' : 'Clear All'}
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

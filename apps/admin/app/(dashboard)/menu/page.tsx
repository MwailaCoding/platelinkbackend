'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { RefreshCw, Search, Plus, Save, ChefHat } from 'lucide-react';

export default function MenuManagement() {
  const router = useRouter();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [branchId, setBranchId] = useState<string | null>(null);

  useEffect(() => {
    const bId = localStorage.getItem('selected_branch_id');
    setBranchId(bId);

    const fetchMenu = async () => {
      try {
        const token = localStorage.getItem('platelink_auth_token');
        const url = bId 
          ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/menu?branch_id=${bId}`
          : `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/menu`;
          
        const res = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setItems(data);
        }
      } catch (err) {
        console.error("Failed to load menu", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchMenu();
  }, []);

  const handleSyncMenu = async () => {
    if (!branchId) return alert("Select a branch first");
    
    if (!confirm("This will pull the latest menu from the main restaurant. Existing custom items might be overwritten. Continue?")) return;
    
    setSyncing(true);
    try {
      const token = localStorage.getItem('platelink_auth_token');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/branches/${branchId}/sync-menu`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        alert("Menu synced successfully");
        window.location.reload();
      } else {
        const err = await res.json();
        alert(err.detail || "Sync failed");
      }
    } catch (err) {
      console.error(err);
      alert("Error syncing menu");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Menu Management</h1>
          <p className="text-sm text-gray-500 mt-1">Manage categories, items, and pricing for this branch.</p>
        </div>
        <div className="flex items-center gap-3">
          {branchId && (
            <button 
              onClick={handleSyncMenu}
              disabled={syncing}
              className="bg-blue-50 text-blue-600 border border-blue-200 px-4 py-2 rounded-lg font-medium hover:bg-blue-100 flex items-center gap-2 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing...' : 'Sync from Master'}
            </button>
          )}
          <button className="bg-emerald-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-emerald-700 flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add Item
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="w-5 h-5 text-gray-400 absolute left-3 top-2.5" />
            <input 
              type="text" 
              placeholder="Search menu items..." 
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading menu...</div>
        ) : items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-500 uppercase bg-gray-50">
                <tr>
                  <th className="px-4 py-3">Item Name</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Price</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item: any) => (
                  <tr key={item.id} className="border-b">
                    <td className="px-4 py-3 font-medium text-gray-900">{item.name}</td>
                    <td className="px-4 py-3 text-gray-500">{item.category?.name || 'Uncategorized'}</td>
                    <td className="px-4 py-3 font-bold">KES {item.price}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${item.is_available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {item.is_available ? 'Available' : 'Unavailable'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-indigo-600 hover:underline cursor-pointer font-medium">Edit</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <ChefHat className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-bold text-gray-900">No menu items</h3>
            <p className="text-gray-500 mt-1">Add items manually or sync from the master menu.</p>
          </div>
        )}
      </div>
    </div>
  );
}

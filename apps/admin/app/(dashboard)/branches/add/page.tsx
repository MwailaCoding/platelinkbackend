'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Store, MapPin, Phone, Save } from 'lucide-react';

export default function AddBranch() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    phone: '',
    copyMenu: true,
    copyStaff: false
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('platelink_auth_token');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/branches`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: formData.name,
          address: formData.address,
          phone: formData.phone,
          copy_menu: formData.copyMenu,
          copy_staff: formData.copyStaff
        })
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to create branch');
      }
      
      const newBranch = await res.json();
      
      // Auto-select the new branch and go to dashboard
      localStorage.setItem('selected_branch_id', newBranch.id);
      localStorage.setItem('selected_branch_name', newBranch.name);
      window.dispatchEvent(new Event('branchChanged'));
      
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 md:p-12">
      <div className="max-w-2xl mx-auto space-y-8">
        <button 
          onClick={() => router.back()}
          className="text-gray-500 hover:text-gray-900 flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Branches
        </button>
        
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Add New Branch</h1>
          <p className="text-gray-500 mt-2">Create a new location for your restaurant business.</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm space-y-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Branch Name</label>
              <div className="relative">
                <Store className="w-5 h-5 text-gray-400 absolute left-3 top-3" />
                <input 
                  type="text" 
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="pl-10 w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="e.g., Riverside Branch"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Address / Location</label>
              <div className="relative">
                <MapPin className="w-5 h-5 text-gray-400 absolute left-3 top-3" />
                <input 
                  type="text" 
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  className="pl-10 w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="e.g., 123 Riverside Drive, Nairobi"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
              <div className="relative">
                <Phone className="w-5 h-5 text-gray-400 absolute left-3 top-3" />
                <input 
                  type="text" 
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  className="pl-10 w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="e.g., +254 700 000000"
                />
              </div>
            </div>
          </div>

          <div className="border-t border-gray-100 pt-6 space-y-4">
            <h3 className="font-semibold text-gray-900">Initial Setup</h3>
            
            <label className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition">
              <div className="mt-1 flex items-center h-5">
                <input 
                  type="checkbox" 
                  checked={formData.copyMenu}
                  onChange={(e) => setFormData({...formData, copyMenu: e.target.checked})}
                  className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                />
              </div>
              <div>
                <span className="block font-medium text-gray-900">Copy Master Menu</span>
                <span className="block text-sm text-gray-500">Automatically import all categories and menu items from your main restaurant configuration.</span>
              </div>
            </label>
          </div>

          <div className="pt-4 flex justify-end">
            <button 
              type="submit" 
              disabled={loading}
              className="bg-emerald-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-emerald-700 transition flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? 'Creating...' : <><Save className="w-4 h-4" /> Create Branch</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

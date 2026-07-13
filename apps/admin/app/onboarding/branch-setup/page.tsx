'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Building2, Plus, ArrowRight, Loader2, Network, Trash2, MapPin } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function BranchSetupPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [branches, setBranches] = useState([{ name: '', address: '', phone: '' }]);
  
  const addBranch = () => {
    setBranches([...branches, { name: '', address: '', phone: '' }]);
  };
  
  const removeBranch = (index: number) => {
    if (branches.length > 1) {
      const newBranches = [...branches];
      newBranches.splice(index, 1);
      setBranches(newBranches);
    }
  };
  
  const updateBranch = (index: number, field: string, value: string) => {
    const newBranches = [...branches];
    newBranches[index] = { ...newBranches[index], [field]: value };
    setBranches(newBranches);
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const token = localStorage.getItem('access_token');
      // Create branches sequentially
      for (const branch of branches) {
        if (!branch.name) continue;
        
        await fetch('/api/branches', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            name: branch.name,
            address: branch.address,
            phone: branch.phone,
            city: '',
            email: ''
          })
        });
      }
      
      // Redirect to login or dashboard
      router.push('/login?setup_complete=true');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-3xl">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center">
            <Network className="w-8 h-8" />
          </div>
        </div>
        <h2 className="text-center text-3xl font-extrabold text-gray-900">
          Set up your Branches
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Add the initial locations for your multi-branch restaurant. You can always add more later.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-3xl">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {branches.map((branch, index) => (
              <div key={index} className="p-6 border border-gray-200 rounded-xl relative bg-gray-50/50">
                {branches.length > 1 && (
                  <button 
                    type="button" 
                    onClick={() => removeBranch(index)}
                    className="absolute top-4 right-4 text-gray-400 hover:text-red-500"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                )}
                
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-emerald-600" />
                  Branch {index + 1}
                </h3>
                
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700">Branch Name *</label>
                    <input
                      type="text"
                      required
                      value={branch.name}
                      onChange={(e) => updateBranch(index, 'name', e.target.value)}
                      placeholder="e.g. Westlands Branch"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm"
                    />
                  </div>
                  
                  <div className="col-span-1">
                    <label className="block text-sm font-medium text-gray-700">Address / Location</label>
                    <input
                      type="text"
                      value={branch.address}
                      onChange={(e) => updateBranch(index, 'address', e.target.value)}
                      placeholder="e.g. 123 Main St"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm"
                    />
                  </div>
                  
                  <div className="col-span-1">
                    <label className="block text-sm font-medium text-gray-700">Phone</label>
                    <input
                      type="text"
                      value={branch.phone}
                      onChange={(e) => updateBranch(index, 'phone', e.target.value)}
                      placeholder="e.g. +254..."
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm"
                    />
                  </div>
                </div>
              </div>
            ))}
            
            <button
              type="button"
              onClick={addBranch}
              className="w-full py-4 border-2 border-dashed border-gray-300 text-gray-600 rounded-xl hover:bg-gray-50 hover:border-emerald-300 hover:text-emerald-600 transition-colors flex items-center justify-center gap-2 font-medium"
            >
              <Plus className="w-5 h-5" />
              Add Another Branch
            </button>
            
            <div className="pt-4 border-t border-gray-200">
              <Button
                type="submit"
                disabled={loading || branches.some(b => !b.name)}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-6 text-lg rounded-xl flex items-center justify-center gap-2"
              >
                {loading ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> Saving Branches...</>
                ) : (
                  <>Complete Setup <ArrowRight className="w-5 h-5" /></>
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

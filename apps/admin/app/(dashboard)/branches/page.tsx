'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Store, Plus, ChevronRight, User } from 'lucide-react';

interface Branch {
  id: string;
  name: string;
  address: string;
  is_active: boolean;
}

export default function BranchSelection() {
  const router = useRouter();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [userRole, setUserRole] = useState<string>('');

  useEffect(() => {
    const fetchBranches = async () => {
      try {
        const token = localStorage.getItem('platelink_auth_token');
        // Decode token to check role (simple check)
        if (token) {
          const payload = JSON.parse(atob(token.split('.')[1]));
          setUserRole(payload.role || '');
          
          // If branch manager, they shouldn't be here, redirect to their dashboard
          if (payload.role === 'branch_manager' && payload.branch_id) {
             localStorage.setItem('selected_branch_id', payload.branch_id);
             router.push('/dashboard');
             return;
          }
        }

        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/branches`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
          const data = await res.json();
          setBranches(data);
          
          // If only 1 branch, auto-select and skip this page
          if (data.length === 1) {
            selectBranch(data[0].id, data[0].name);
          }
        }
      } catch (error) {
        console.error("Failed to load branches", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchBranches();
  }, [router]);

  const selectBranch = (id: string, name: string) => {
    localStorage.setItem('selected_branch_id', id);
    localStorage.setItem('selected_branch_name', name);
    // Dispatch event so other components know branch changed
    window.dispatchEvent(new Event('branchChanged'));
    router.push('/dashboard');
  };

  if (loading) return <div className="flex h-screen items-center justify-center">Loading branches...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-6 md:p-12">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex justify-between items-end border-b pb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Select a Branch</h1>
            <p className="text-gray-500 mt-2">Choose which location you want to manage today.</p>
          </div>
          {(userRole === 'owner' || userRole === 'admin') && (
            <button 
              onClick={() => router.push('/branches/add')}
              className="bg-emerald-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-emerald-700"
            >
              <Plus className="w-4 h-4" /> Add Branch
            </button>
          )}
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {branches.map(branch => (
            <div 
              key={branch.id} 
              onClick={() => selectBranch(branch.id, branch.name)}
              className="bg-white p-6 rounded-xl border border-gray-200 hover:border-emerald-500 hover:shadow-md cursor-pointer transition flex items-center justify-between group"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition">
                  <Store className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900">{branch.name}</h3>
                  <p className="text-sm text-gray-500 flex items-center gap-1">
                    <span className={`w-2 h-2 rounded-full ${branch.is_active ? 'bg-green-500' : 'bg-red-500'}`}></span>
                    {branch.is_active ? 'Active' : 'Inactive'} • {branch.address || 'No address set'}
                  </p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-emerald-600" />
            </div>
          ))}

          {branches.length === 0 && (
            <div className="col-span-2 bg-yellow-50 border border-yellow-200 p-8 rounded-xl text-center">
              <Store className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
              <h3 className="text-lg font-bold text-yellow-800 mb-2">No Branches Found</h3>
              <p className="text-yellow-700 mb-4">You need to set up at least one branch to start using PlateLink.</p>
              <button 
                onClick={() => router.push('/branches/add')}
                className="bg-yellow-600 text-white px-6 py-2 rounded-lg hover:bg-yellow-700"
              >
                Create Your First Branch
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

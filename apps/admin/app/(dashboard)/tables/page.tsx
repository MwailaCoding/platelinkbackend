// apps/admin/src/app/(dashboard)/tables/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Plus, 
  Layers, 
  Trash2, 
  RefreshCw, 
  Download, 
  Loader2, 
  MapPin, 
  Users, 
  QrCode, 
  X, 
  Check, 
  AlertCircle,
  HelpCircle
} from 'lucide-react';
import { api, ENDPOINTS, getErrorMessage } from '@platelink/utils';
import { toast } from 'sonner';
import QRCodeDownloadButton from '@/components/Tables/QRCodeDownloadButton';

interface Table {
  id: string;
  table_number: number;
  capacity: number;
  location?: string;
  status: string;
  qr_code_token?: string;
  qr_code_url?: string;
}

export default function TableManagementPage() {
  const router = useRouter();

  // Authentication & Auth check states
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);

  // Table data states
  const [tables, setTables] = useState<Table[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal Open States
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);
  
  // Confirmation Modal States
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    type: 'delete' | 'regenerate';
    tableId: string;
    tableNumber: number;
  } | null>(null);

  // Form States (Add Single)
  const [singleTableNumber, setSingleTableNumber] = useState<string>('');
  const [singleCapacity, setSingleCapacity] = useState<number>(4);
  const [singleLocation, setSingleLocation] = useState<string>('');
  const [submittingSingle, setSubmittingSingle] = useState(false);

  // Form States (Bulk Create)
  const [bulkStartNumber, setBulkStartNumber] = useState<string>('1');
  const [bulkCount, setBulkCount] = useState<number>(10);
  const [bulkCapacity, setBulkCapacity] = useState<number>(4);
  const [bulkLocation, setBulkLocation] = useState<string>('');
  const [submittingBulk, setSubmittingBulk] = useState(false);

  // Action Pending States
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [restaurantName, setRestaurantName] = useState<string>('Restaurant');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.get<any>('/restaurants/me');
        if (res.data?.name) {
          setRestaurantName(res.data.name);
        }
      } catch (err) {
        // Fallback silently
      }
    };
    if (isAuthenticated) {
      fetchProfile();
    }
  }, [isAuthenticated]);

  // Route Protection & Role Verification
  useEffect(() => {
    const checkAuth = () => {
      const token = typeof window !== 'undefined' ? (localStorage.getItem('platelink_auth_token') || localStorage.getItem('token')) : null;
      if (!token) {
        router.push('/login');
        return;
      }

      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const isExpired = payload.exp * 1000 < Date.now();
        if (isExpired) {
          localStorage.removeItem('token');
          localStorage.removeItem('platelink_auth_token');
          router.push('/login');
          return;
        }

        const role = (payload.role || 'owner').toLowerCase();
        if (role !== 'owner' && role !== 'manager') {
          toast.error('Access Denied: Only owners and managers are authorized to view Table Management.');
          router.push('/dashboard');
          return;
        }

        setIsAuthenticated(true);
      } catch (err) {
        localStorage.removeItem('token');
        localStorage.removeItem('platelink_auth_token');
        router.push('/login');
      } finally {
        setAuthLoading(false);
      }
    };

    checkAuth();
  }, [router]);

  // Fetch Tables from backend
  const fetchTablesList = async () => {
    setLoading(true);
    try {
      const res = await api.get<Table[]>(ENDPOINTS.TABLES.LIST);
      const data = res.data || [];
      // Sort tables by number ascending
      const sorted = [...data].sort((a, b) => a.table_number - b.table_number);
      setTables(sorted);
    } catch (error: any) {
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchTablesList();
    }
  }, [isAuthenticated]);

  // Handle Add Single Table
  const handleAddSingle = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!singleTableNumber || parseInt(singleTableNumber) < 1 || parseInt(singleTableNumber) > 999) {
      toast.error('Please specify a valid Table Number between 1 and 999.');
      return;
    }

    const num = parseInt(singleTableNumber);
    // Check if table number already exists
    if (tables.some(t => t.table_number === num)) {
      toast.error(`Table number ${num} already exists.`);
      return;
    }

    try {
      setSubmittingSingle(true);
      
      // The backend creates single tables inside tables bulk endpoint or single table CREATE.
      // Since backend TableBulkCreate schema handles creation range, we can call bulk-create with start = end = num!
      // This maps perfectly to the FastAPI TableBulkCreate schema!
      const payload = {
        start_number: num,
        end_number: num,
        capacity: singleCapacity,
        location: singleLocation.trim() || undefined,
      };

      await api.post(ENDPOINTS.TABLES.BULK_CREATE, payload);
      
      toast.success(`Table ${num} created successfully!`);
      setIsAddModalOpen(false);
      setSingleTableNumber('');
      setSingleCapacity(4);
      setSingleLocation('');
      fetchTablesList();
    } catch (err: any) {
      toast.error(getErrorMessage(err));
    } finally {
      setSubmittingSingle(false);
    }
  };

  // Handle Bulk Create Tables
  const handleBulkCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const start = parseInt(bulkStartNumber);
    const count = bulkCount;
    if (isNaN(start) || start < 1) {
      toast.error('Starting Table Number must be at least 1.');
      return;
    }
    if (count < 1 || count > 50) {
      toast.error('You can only bulk create between 1 and 50 tables.');
      return;
    }

    try {
      setSubmittingBulk(true);
      
      // TableBulkCreate expected schema: start_number, end_number, capacity, location
      const payload = {
        start_number: start,
        end_number: start + count - 1,
        capacity: bulkCapacity,
        location: bulkLocation.trim() || undefined,
      };

      await api.post(ENDPOINTS.TABLES.BULK_CREATE, payload);
      
      toast.success(`Successfully bulk created ${count} tables!`);
      setIsBulkModalOpen(false);
      setBulkStartNumber('');
      setBulkCount(10);
      setBulkCapacity(4);
      setBulkLocation('');
      fetchTablesList();
    } catch (err: any) {
      toast.error(getErrorMessage(err));
    } finally {
      setSubmittingBulk(false);
    }
  };

  // Action Executer: Delete Table
  const executeDelete = async (id: string, num: number) => {
    try {
      setActionLoading(id);
      await api.del(ENDPOINTS.TABLES.DELETE(id));
      toast.success(`Table ${num} and its QR code successfully deleted.`);
      setTables(prev => prev.filter(t => t.id !== id));
    } catch (err: any) {
      toast.error(getErrorMessage(err));
    } finally {
      setActionLoading(null);
      setConfirmModal(null);
    }
  };

  // Action Executer: Regenerate QR Code
  const executeRegenerateQr = async (id: string, num: number) => {
    try {
      setActionLoading(id);
      await api.post(ENDPOINTS.TABLES.REGENERATE_QR(id));
      toast.success(`QR Code regenerated for Table ${num}. Old QR links are now invalid.`);
      fetchTablesList();
    } catch (err: any) {
      toast.error(getErrorMessage(err));
    } finally {
      setActionLoading(null);
      setConfirmModal(null);
    }
  };

  // Download individual QR Code as image
  const handleDownloadQrImage = async (tableNumber: number, qrCodeUrl: string) => {
    if (!qrCodeUrl) return;
    try {
      const response = await fetch(qrCodeUrl);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `table_${tableNumber}_qr.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      // Fallback
      window.open(qrCodeUrl, '_blank');
    }
  };

  // Download PDF consisting of all table QR codes
  const handleDownloadAllQrPdf = async () => {
    try {
      setDownloadingPdf(true);
      
      const token = localStorage.getItem('platelink_auth_token') || localStorage.getItem('token');
      // Fetch the binary stream directly using window fetch or Axios config responseType 'blob'
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}${ENDPOINTS.TABLES.DOWNLOAD_PDF}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });

      if (!response.ok) throw new Error('Failed to generate PDF document on server.');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'restaurant_tables_qrcodes.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('All QR codes PDF downloaded successfully!');
    } catch (err: any) {
      toast.error(err.message || 'Error occurred during PDF generation.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  // Badge coloring depending on status
  const getBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'available': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'ordering': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'ordered': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'ready': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'eating': return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'bill_requested': return 'bg-red-100 text-red-700 border-red-200';
      case 'occupied': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'dirty': case 'cleaning': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'reserved': return 'bg-indigo-100 text-indigo-700 border-indigo-200';
      case 'held': return 'bg-slate-100 text-slate-700 border-slate-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-primary animate-spin mx-auto mb-4" />
          <p className="text-sm font-bold text-gray-500">Checking credentials & loading terminal...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6 relative font-sans text-dark selection:bg-primary selection:text-white">
      {/* HEADER SECTION */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-6">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight flex items-center gap-2">
            <QrCode className="w-8 h-8 text-primary" />
            Table Management
          </h1>
          <p className="text-gray-500 text-sm font-medium mt-1">Manage restaurant tables, seating capacities, locations, and print QR codes.</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          {tables.length > 0 && (
            <QRCodeDownloadButton 
              restaurantName={restaurantName}
            />
          )}

          <button
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-bold text-gray-700 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 shadow-sm transition"
          >
            <Plus className="w-4 h-4 text-primary stroke-[3]" />
            Add Single Table
          </button>

          <button
            onClick={() => setIsBulkModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-bold text-white bg-primary hover:bg-emerald-600 rounded-xl shadow-lg shadow-primary/20 transition"
          >
            <Layers className="w-4 h-4" />
            Bulk Create Tables
          </button>
        </div>
      </div>

      {/* MAIN VIEW AREA */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center">
          <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
          <p className="text-gray-500 font-semibold text-sm">Retrieving active tables from backend...</p>
        </div>
      ) : tables.length === 0 ? (
        <div className="bg-white rounded-3xl border border-gray-200 p-12 text-center max-w-xl mx-auto shadow-sm mt-12 animate-in fade-in slide-in-from-bottom-6 duration-500">
          <div className="w-20 h-20 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-inner">
            <QrCode className="w-10 h-10 text-primary animate-pulse" />
          </div>
          <h3 className="text-xl font-bold text-gray-900">No tables created yet</h3>
          <p className="text-gray-500 text-sm mt-2 max-w-sm mx-auto leading-relaxed">
            Create restaurant tables individually or in bulk to automatically generate downloadable QR code links for diners.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3 text-sm font-bold text-gray-700 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition"
            >
              <Plus className="w-4 h-4 text-primary stroke-[3]" />
              Add Single Table
            </button>
            <button
              onClick={() => setIsBulkModalOpen(true)}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3 text-sm font-bold text-white bg-primary hover:bg-emerald-600 rounded-xl transition shadow-lg shadow-primary/20"
            >
              <Layers className="w-4 h-4" />
              Bulk Create Tables
            </button>
          </div>
        </div>
      ) : (
        /* GRID OF TABLES */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
          {tables.map((table) => (
            <div 
              key={table.id} 
              className="bg-white rounded-2xl border border-gray-150 p-5 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between"
            >
              <div>
                {/* Header of Table Card */}
                <div className="flex justify-between items-start mb-4">
                  <span className="text-2xl font-black text-gray-800">
                    TABLE {table.table_number}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-[10px] font-black border uppercase tracking-wider ${getBadgeColor(table.status)}`}>
                    {table.status}
                  </span>
                </div>

                {/* Details Section */}
                <div className="flex gap-4 items-center bg-gray-50/50 p-3 rounded-xl border border-gray-150 mb-5">
                  <div className="w-[85px] h-[85px] shrink-0 bg-white rounded-lg p-1.5 border border-gray-200 shadow-sm flex items-center justify-center overflow-hidden">
                    {table.qr_code_url ? (
                      <img 
                        src={table.qr_code_url} 
                        alt={`Table ${table.table_number} QR Preview`}
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center bg-gray-100 text-gray-400 font-bold text-[8px]">
                        <QrCode className="w-5 h-5 mb-1" />
                        <span>NO QR LINK</span>
                      </div>
                    )}
                  </div>
                  <div className="space-y-1 text-sm font-semibold text-gray-600">
                    <p className="flex items-center gap-1.5 text-[9px] text-gray-400 uppercase tracking-widest font-black">
                      <HelpCircle className="w-3.5 h-3.5 text-gray-400" />
                      Table Specs
                    </p>
                    <p className="flex items-center gap-1.5 text-gray-700 text-xs">
                      <Users className="w-4 h-4 text-gray-400" />
                      <span>Capacity: {table.capacity} seats</span>
                    </p>
                    {table.location && (
                      <p className="flex items-center gap-1.5 text-gray-700 text-xs">
                        <MapPin className="w-4 h-4 text-gray-400" />
                        <span>Location: {table.location}</span>
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Actions Section */}
              <div className="grid grid-cols-3 gap-2 border-t border-gray-100 pt-4 mt-auto">
                <button
                  onClick={() => setConfirmModal({ isOpen: true, type: 'regenerate', tableId: table.id, tableNumber: table.table_number })}
                  disabled={actionLoading === table.id}
                  className="flex flex-col sm:flex-row items-center justify-center gap-1 py-2 text-xs font-bold text-gray-600 hover:text-primary bg-gray-50 hover:bg-primary/5 rounded-xl transition"
                  title="Regenerate QR token and invalidate existing link"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${actionLoading === table.id ? 'animate-spin' : ''}`} />
                  <span className="text-[10px] sm:text-xs">Regen QR</span>
                </button>

                <button
                  onClick={() => handleDownloadQrImage(table.table_number, table.qr_code_url || '')}
                  disabled={!table.qr_code_url}
                  className="flex flex-col sm:flex-row items-center justify-center gap-1 py-2 text-xs font-bold text-gray-600 hover:text-primary bg-gray-50 hover:bg-primary/5 rounded-xl transition disabled:opacity-50"
                  title="Download individual table QR as PNG image"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span className="text-[10px] sm:text-xs">Download</span>
                </button>

                <button
                  onClick={() => setConfirmModal({ isOpen: true, type: 'delete', tableId: table.id, tableNumber: table.table_number })}
                  disabled={actionLoading === table.id}
                  className="flex flex-col sm:flex-row items-center justify-center gap-1 py-2 text-xs font-bold text-gray-600 hover:text-rose-700 bg-gray-50 hover:bg-rose-50 rounded-xl transition"
                  title="Delete Table permanently"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span className="text-[10px] sm:text-xs">Delete</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* MODAL 1: ADD SINGLE TABLE */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 bg-gray-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center p-6 border-b border-gray-100">
              <h3 className="text-lg font-black text-gray-900">Add Single Table</h3>
              <button onClick={() => setIsAddModalOpen(false)} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg transition">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddSingle} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Table Number *</label>
                <input
                  type="number"
                  required
                  min="1"
                  max="999"
                  value={singleTableNumber}
                  onChange={(e) => setSingleTableNumber(e.target.value)}
                  placeholder="e.g. 5"
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-205 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-gray-900 font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Capacity (Seats) *</label>
                <input
                  type="number"
                  required
                  min="1"
                  max="20"
                  value={singleCapacity}
                  onChange={(e) => setSingleCapacity(parseInt(e.target.value))}
                  placeholder="Default: 4"
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-205 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-gray-900 font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Location (Optional)</label>
                <input
                  type="text"
                  value={singleLocation}
                  onChange={(e) => setSingleLocation(e.target.value)}
                  placeholder="e.g. Indoor, Outdoor, VIP, Balcony"
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-205 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-gray-900 font-semibold"
                />
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-5 py-2.5 text-sm font-bold text-gray-500 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingSingle}
                  className="px-5 py-2.5 text-sm font-bold text-white bg-primary hover:bg-emerald-600 rounded-xl transition shadow-lg shadow-primary/20 disabled:opacity-50 inline-flex items-center gap-1.5"
                >
                  {submittingSingle && <Loader2 className="w-4 h-4 animate-spin text-white" />}
                  Create Table
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: BULK CREATE TABLES */}
      {isBulkModalOpen && (
        <div className="fixed inset-0 z-50 bg-gray-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center p-6 border-b border-gray-100">
              <h3 className="text-lg font-black text-gray-900">Bulk Create Tables</h3>
              <button onClick={() => setIsBulkModalOpen(false)} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg transition">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleBulkCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Starting Table Number *</label>
                <input
                  type="number"
                  required
                  min="1"
                  value={bulkStartNumber}
                  onChange={(e) => setBulkStartNumber(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-205 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-gray-900 font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Number of Tables to Create *</label>
                <input
                  type="number"
                  required
                  min="1"
                  max="50"
                  value={bulkCount}
                  onChange={(e) => setBulkCount(parseInt(e.target.value))}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-205 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-gray-900 font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Capacity (Seats per Table) *</label>
                <input
                  type="number"
                  required
                  min="1"
                  max="20"
                  value={bulkCapacity}
                  onChange={(e) => setBulkCapacity(parseInt(e.target.value))}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-205 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-gray-900 font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Location (Optional)</label>
                <input
                  type="text"
                  value={bulkLocation}
                  onChange={(e) => setBulkLocation(e.target.value)}
                  placeholder="e.g. Main Hall"
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-205 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-gray-900 font-semibold"
                />
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setIsBulkModalOpen(false)}
                  className="px-5 py-2.5 text-sm font-bold text-gray-500 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingBulk}
                  className="px-5 py-2.5 text-sm font-bold text-white bg-primary hover:bg-emerald-700 rounded-xl transition shadow-lg shadow-primary/20 disabled:opacity-50 inline-flex items-center gap-1.5"
                >
                  {submittingBulk && <Loader2 className="w-4 h-4 animate-spin text-white" />}
                  Generate Tables
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CONFIRMATION DIALOG (DELETE OR REGENERATE QR) */}
      {confirmModal?.isOpen && (
        <div className="fixed inset-0 z-50 bg-gray-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-2xl border border-gray-100 overflow-hidden animate-in zoom-in-95 duration-200 text-center">
            <div className={`w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-4 ${confirmModal.type === 'delete' ? 'bg-red-50 text-red-500' : 'bg-amber-50 text-amber-500'}`}>
              <AlertCircle className="w-7 h-7" />
            </div>
            
            <h3 className="text-lg font-extrabold text-gray-900">
              {confirmModal.type === 'delete' ? 'Delete Table' : 'Regenerate QR Code'}
            </h3>
            
            <p className="text-gray-500 text-xs mt-2 leading-relaxed font-semibold">
              {confirmModal.type === 'delete' 
                ? `Are you sure you want to permanently delete Table ${confirmModal.tableNumber}? This will expire its QR menu instantly.`
                : `Regenerating will expire the current QR code token for Table ${confirmModal.tableNumber}. Diners currently scanning it will need to scan the new code.`}
            </p>

            <div className="flex gap-3 justify-center mt-6">
              <button
                type="button"
                onClick={() => setConfirmModal(null)}
                className="px-4 py-2 text-xs font-bold text-gray-500 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition"
              >
                No, Cancel
              </button>
              <button
                type="button"
                onClick={() => confirmModal.type === 'delete' 
                  ? executeDelete(confirmModal.tableId, confirmModal.tableNumber) 
                  : executeRegenerateQr(confirmModal.tableId, confirmModal.tableNumber)}
                className={`px-4 py-2 text-xs font-bold text-white rounded-xl shadow-md transition ${confirmModal.type === 'delete' ? 'bg-red-500 hover:bg-red-600 shadow-red-500/10' : 'bg-amber-500 hover:bg-amber-600 shadow-amber-500/10'}`}
              >
                Yes, Continue
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

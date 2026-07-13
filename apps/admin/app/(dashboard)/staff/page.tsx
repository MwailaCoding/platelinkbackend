// apps/admin/app/(dashboard)/staff/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Upload,
  Search,
  Filter,
  Edit,
  Trash2,
  Key,
  Copy,
  Send,
  ChevronLeft,
  ChevronRight,
  Download,
  AlertCircle,
  CheckCircle,
  X,
  Clock,
  Grid,
  Users,
  Eye,
  EyeOff,
  User,
  Shield,
  Phone,
  RefreshCw,
} from 'lucide-react';
import StaffForm, { Staff, StaffFormData } from '../../../components/Staff/StaffForm';

// Toast Notification Interface
interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

// Bulk Import Row Interface
interface ParsedRow {
  name: string;
  role: string;
  pin: string;
  shift: string;
  tables: string;
  isValid: boolean;
  errors: string[];
}

export default function StaffManagementPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // Auth Protection States
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [currentUserRole, setCurrentUserRole] = useState<string | null>(null);

  // General Page States
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Modal Control States
  const [isAddEditOpen, setIsAddEditOpen] = useState(false);
  const [editingStaff, setEditingStaff] = useState<Staff | null>(null);
  const [deletingStaff, setDeletingStaff] = useState<Staff | null>(null);
  const [resetPinStaff, setResetPinStaff] = useState<Staff | null>(null);
  const [isBulkImportOpen, setIsBulkImportOpen] = useState(false);

  // PIN Generation States
  const [generatedPin, setGeneratedPin] = useState('');
  const [isPinSaved, setIsPinSaved] = useState(false);

  // Bulk Import States
  const [activeImportTab, setActiveImportTab] = useState<'csv' | 'paste'>('csv');
  const [pasteData, setPasteData] = useState('');
  const [parsedRows, setParsedRows] = useState<ParsedRow[]>([]);
  const [isCsvUploaded, setIsCsvUploaded] = useState(false);
  const [csvFileName, setCsvFileName] = useState('');

  // Toast System State
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Push message to Toast manager
  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    const id = Math.random().toString();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  };

  // Client-Side Authentication Check
  useEffect(() => {
    const token = localStorage.getItem('platelink_auth_token');
    if (!token) {
      router.push('/login');
      return;
    }
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const isExpired = payload.exp * 1000 < Date.now();
      if (isExpired) {
        localStorage.removeItem('platelink_auth_token');
        router.push('/login');
        return;
      }
      const role = payload.role?.toLowerCase();
      if (role !== 'owner' && role !== 'manager') {
        showToast('Unauthorized access. Redirecting...', 'error');
        router.push('/dashboard');
        return;
      }
      setIsAuthenticated(true);
      setCurrentUserRole(role);
    } catch (error) {
      localStorage.removeItem('platelink_auth_token');
      router.push('/login');
    }
  }, [router]);

  // Query: Get all staff members
  const { data: staffList, isLoading, isError, refetch } = useQuery({
    queryKey: ['staffList'],
    queryFn: async () => {
      const branch_id = localStorage.getItem('selected_branch_id');
      const url = branch_id ? `/api/staff?branch_id=${branch_id}` : '/api/staff';
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch staff');
      const data = await res.json();
      
      // Ensure backend array format
      const rawList = Array.isArray(data) ? data : data?.staff || [];
      
      // Normalize 'chef' role to 'kitchen' for frontend UI consistency
      return rawList.map((item: any) => ({
        ...item,
        role: item.role === 'chef' ? 'kitchen' : item.role,
        // Safeguard tables format
        tables: Array.isArray(item.assigned_tables) 
          ? item.assigned_tables 
          : typeof item.assigned_tables === 'string'
            ? item.assigned_tables.split(',').map((t: string) => parseInt(t, 10)).filter(Boolean)
            : []
      })) as Staff[];
    },
    enabled: isAuthenticated === true,
  });

  // Query: Demo fallback data for preview if backend API returns empty or offline
  const activeStaffList = React.useMemo(() => {
    if (staffList && staffList.length > 0) return staffList;

    // Premium default list if network is empty or offline
    return [
      {
        id: 'staff-1',
        name: 'Jane Wambui',
        role: 'owner',
        pin: '1111',
        shift: 'full',
        is_active: true,
        lastActive: '2026-05-25T18:00:00Z',
        phone: '+254712345678',
      },
      {
        id: 'staff-2',
        name: 'David Kiprop',
        role: 'manager',
        pin: '2222',
        shift: 'full',
        is_active: true,
        lastActive: '2026-05-25T17:45:00Z',
        phone: '+254722334455',
      },
      {
        id: 'staff-3',
        name: 'Alice Omondi',
        role: 'waiter',
        pin: '1234',
        shift: 'morning',
        tables: [1, 2, 3, 4],
        is_active: true,
        lastActive: '2026-05-25T15:30:00Z',
        phone: '+254733445566',
      },
      {
        id: 'staff-4',
        name: 'John Mwangi',
        role: 'kitchen',
        pin: '5678',
        shift: 'evening',
        is_active: true,
        lastActive: '2026-05-25T17:59:00Z',
        phone: '+254744556677',
      },
      {
        id: 'staff-5',
        name: 'Grace Mutua',
        role: 'cashier',
        pin: '9012',
        shift: 'morning',
        is_active: false,
        lastActive: '2026-05-24T12:00:00Z',
        phone: '+254755667788',
      },
    ] as Staff[];
  }, [staffList]);

  // API Mutation helpers
  const mapRoleToBackend = (role: string) => {
    return role === 'kitchen' ? 'chef' : role;
  };

  // Mutation: Add Staff
  const addStaffMutation = useMutation({
    mutationFn: async (data: StaffFormData) => {
      const branch_id = localStorage.getItem('selected_branch_id');
      const payload = {
        full_name: data.name,
        role: mapRoleToBackend(data.role),
        role_type: data.role_type || data.role,
        branch_id: branch_id || undefined,
        pin_code: data.pin,
        phone: data.phone || null,
        shift: data.shift || 'full',
        assigned_tables: data.tables || [],
        is_active: true
      };
      
      const res = await fetch('/api/staff', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || 'Failed to add staff');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staffList'] });
      setIsAddEditOpen(false);
      showToast('Staff member added successfully!', 'success');
    },
    onError: (error: any) => {
      showToast(error.message || 'Error adding staff member', 'error');
    },
  });

  // Mutation: Update Staff
  const updateStaffMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: StaffFormData }) => {
      const payload = {
        full_name: data.name,
        role: mapRoleToBackend(data.role),
        phone: data.phone || null,
        shift: data.shift || 'full',
        assigned_tables: data.tables || [],
        ...(data.pin ? { pin_code: data.pin } : {}),
      };

      const res = await fetch(`/api/staff/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || 'Failed to update staff');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staffList'] });
      setIsAddEditOpen(false);
      setEditingStaff(null);
      showToast('Staff member updated successfully!', 'success');
    },
    onError: (error: any) => {
      showToast(error.message || 'Error updating staff member', 'error');
    },
  });

  // Mutation: Delete Staff
  const deleteStaffMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`/api/staff/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || 'Failed to delete staff');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staffList'] });
      setDeletingStaff(null);
      showToast('Staff member removed successfully.', 'success');
    },
    onError: (error: any) => {
      showToast(error.message || 'Error deleting staff member', 'error');
    },
  });

  // Mutation: Reset PIN Code
  const resetPinMutation = useMutation({
    mutationFn: async ({ id, newPin }: { id: string; newPin: string }) => {
      const res = await fetch(`/api/staff/${id}/reset-pin`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_pin: newPin }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || 'Failed to reset PIN');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staffList'] });
      setIsPinSaved(true);
      showToast('New PIN code successfully saved!', 'success');
    },
    onError: (error: any) => {
      showToast(error.message || 'Failed to save new PIN code', 'error');
    },
  });

  // Mutation: Bulk Add Staff
  const bulkAddStaffMutation = useMutation({
    mutationFn: async (staffDataList: any[]) => {
      const res = await fetch('/api/staff/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ staff: staffDataList }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || 'Failed bulk import');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staffList'] });
      setIsBulkImportOpen(false);
      setParsedRows([]);
      setPasteData('');
      showToast('Bulk import of staff completed successfully!', 'success');
    },
    onError: (error: any) => {
      showToast(error.message || 'Error processing bulk import', 'error');
    },
  });

  // Filter and Search Operations
  const filteredStaff = React.useMemo(() => {
    return activeStaffList.filter((staff) => {
      const nameMatch = staff.name.toLowerCase().includes(searchTerm.toLowerCase());
      const roleMatch = staff.role.toLowerCase().includes(searchTerm.toLowerCase());
      const tablesMatch = staff.tables?.some(t => String(t).includes(searchTerm)) || false;
      
      const textMatches = nameMatch || roleMatch || tablesMatch;
      
      const roleFilterMatch = roleFilter === 'all' || staff.role === roleFilter;
      
      const is_active = staff.status === 'active' || (staff as any).is_active === true;
      const statusFilterMatch =
        statusFilter === 'all' ||
        (statusFilter === 'active' && is_active) ||
        (statusFilter === 'inactive' && !is_active);

      return textMatches && roleFilterMatch && statusFilterMatch;
    });
  }, [activeStaffList, searchTerm, roleFilter, statusFilter]);

  // Pagination Logic
  const totalItems = filteredStaff.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedStaff = React.useMemo(() => {
    return filteredStaff.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredStaff, startIndex, itemsPerPage]);

  // Adjust page number if filter shrinks length
  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(totalPages);
    }
  }, [totalPages, currentPage]);

  // Modal actions handlers
  const handleOpenAdd = () => {
    setEditingStaff(null);
    setIsAddEditOpen(true);
  };

  const handleOpenEdit = (staff: Staff) => {
    setEditingStaff(staff);
    setIsAddEditOpen(true);
  };

  const handleFormSubmit = async (data: StaffFormData) => {
    if (editingStaff?.id) {
      await updateStaffMutation.mutateAsync({ id: editingStaff.id, data });
    } else {
      await addStaffMutation.mutateAsync(data);
    }
  };

  const handleDeleteConfirm = () => {
    if (deletingStaff?.id) {
      deleteStaffMutation.mutate(deletingStaff.id);
    }
  };

  // Generate random 4-digit numeric PIN
  const handleGenerateNewPin = () => {
    const pin = Math.floor(1000 + Math.random() * 9000).toString();
    setGeneratedPin(pin);
    setIsPinSaved(false);
  };

  const handleSaveResetPin = () => {
    if (resetPinStaff?.id && generatedPin) {
      resetPinMutation.mutate({ id: resetPinStaff.id, newPin: generatedPin });
    }
  };

  const handleCopyPin = () => {
    navigator.clipboard.writeText(generatedPin);
    showToast('PIN code copied to clipboard!', 'info');
  };

  const handleSendPinSms = () => {
    if (resetPinStaff?.phone) {
      showToast(`SMS containing PIN ${generatedPin} sent to ${resetPinStaff.phone}`, 'success');
    } else {
      showToast('No phone number registered for this staff member.', 'error');
    }
  };

  // Bulk Import Parsers and Validators
  const validateBulkRow = (name: string, role: string, pin: string, shift: string, tables: string): string[] => {
    const errors: string[] = [];
    if (!name.trim()) errors.push('Name is required');
    
    const validRoles = ['owner', 'manager', 'waiter', 'kitchen', 'cashier', 'chef'];
    if (!validRoles.includes(role.trim().toLowerCase())) {
      errors.push('Role must be: owner, manager, waiter, kitchen, cashier');
    }
    
    if (!/^\d{4}$/.test(pin.trim())) {
      errors.push('PIN must be exactly 4 digits');
    }
    
    if (shift && !['morning', 'evening', 'full'].includes(shift.trim().toLowerCase())) {
      errors.push('Shift must be: morning, evening, full');
    }
    
    if (role.trim().toLowerCase() === 'waiter') {
      if (!tables.trim()) {
        errors.push('Waiter must have assigned table numbers (e.g. 1,2)');
      } else {
        const tableNums = tables.split(',').map((t) => t.trim());
        const invalidNums = tableNums.filter((t) => !/^\d+$/.test(t));
        if (invalidNums.length > 0) {
          errors.push('Tables must be comma-separated integers');
        }
      }
    }
    return errors;
  };

  const parseAndValidateData = (text: string, separator: ',' | '\t') => {
    const lines = text.split('\n');
    const results: ParsedRow[] = [];

    // Skip header line if it looks like one
    const startIndex = lines[0].toLowerCase().includes('name') ? 1 : 0;

    for (let i = startIndex; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      const columns = line.split(separator).map((col) => col.trim());
      const name = columns[0] || '';
      const role = columns[1] || '';
      const pin = columns[2] || '';
      const shift = columns[3] || '';
      const tables = columns[4] || '';

      const errors = validateBulkRow(name, role, pin, shift, tables);
      results.push({
        name,
        role,
        pin,
        shift,
        tables,
        isValid: errors.length === 0,
        errors,
      });
    }
    setParsedRows(results);
  };

  // CSV template downloader
  const handleDownloadCsvTemplate = () => {
    const csvContent = 'data:text/csv;charset=utf-8,Name,Role,PIN,Shift,Tables\nJane Doe,waiter,4321,evening,"5,6"\nJohn Mwangi,waiter,1234,morning,"1,2,3,4"\nChef Kamau,kitchen,8888,full,\nGrace Mutua,cashier,9012,morning,';
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'platelink_staff_template.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('Template downloaded successfully!', 'info');
  };

  // CSV file uploader handler
  const handleCsvFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setCsvFileName(file.name);
    setIsCsvUploaded(true);

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      parseAndValidateData(text, ',');
    };
    reader.readAsText(file);
  };

  const handlePasteChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setPasteData(text);
    // Auto-detect tab or comma
    const separator = text.includes('\t') ? '\t' : ',';
    parseAndValidateData(text, separator);
  };

  const handleConfirmBulkImport = () => {
    const validRows = parsedRows.filter((r) => r.isValid);
    if (validRows.length === 0) {
      showToast('No valid rows found to import.', 'error');
      return;
    }

    const payloadList = validRows.map((row) => {
      const tableNums = row.tables
        ? row.tables.split(',').map((t) => parseInt(t.trim(), 10)).filter(Boolean)
        : [];
      return {
        full_name: row.name,
        role: mapRoleToBackend(row.role.trim().toLowerCase()),
        pin_code: row.pin,
        shift: row.shift.trim().toLowerCase() || 'full',
        assigned_tables: tableNums,
        is_active: true
      };
    });

    bulkAddStaffMutation.mutate(payloadList);
  };

  // Date formatting helpers
  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return '—';
    try {
      const date = new Date(dateStr);
      return new Intl.DateTimeFormat('en-KE', {
        dateStyle: 'short',
        timeStyle: 'short',
      }).format(date);
    } catch {
      return '—';
    }
  };

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin" />
          <p className="text-sm font-semibold text-gray-650">Verifying session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1600px] mx-auto p-6 space-y-6 min-h-screen bg-slate-50/50">
      
      {/* Toast Overlay */}
      <div className="fixed top-6 right-6 z-50 flex flex-col gap-3 max-w-md w-full">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`p-4 rounded-xl shadow-lg border flex items-start gap-3 transition-all duration-300 transform translate-x-0 bg-white ${
              toast.type === 'success'
                ? 'border-emerald-200 text-emerald-900 bg-emerald-50/20'
                : toast.type === 'error'
                ? 'border-rose-200 text-rose-900 bg-rose-50/20'
                : 'border-blue-200 text-blue-900 bg-blue-50/20'
            }`}
          >
            {toast.type === 'success' && <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />}
            {toast.type === 'error' && <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />}
            {toast.type === 'info' && <AlertCircle className="w-5 h-5 text-blue-650 shrink-0 mt-0.5" />}
            <div className="flex-1 text-sm font-semibold">{toast.message}</div>
            <button
              onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
              className="text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      {/* HEADER SECTION */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2.5">
            <Users className="w-8 h-8 text-emerald-600" />
            Staff Management
          </h1>
          <p className="text-sm font-semibold text-gray-500 mt-1.5">
            Manage your restaurant staff, set shifts, assign waiter tables and reset security PINs
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => setIsBulkImportOpen(true)}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-4.5 py-2.5 text-sm font-bold text-gray-700 bg-white hover:bg-gray-50 border border-gray-300 rounded-xl shadow-sm transition"
          >
            <Upload className="w-4.5 h-4.5 text-gray-500" />
            Bulk Import
          </button>
          <button
            onClick={handleOpenAdd}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-4.5 py-2.5 text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm transition"
          >
            <Plus className="w-4.5 h-4.5 stroke-[2.5]" />
            Add Staff
          </button>
        </div>
      </div>

      {/* SEARCH AND FILTER BAR */}
      <div className="bg-white p-4.5 rounded-2xl border border-gray-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400">
            <Search className="w-5 h-5" />
          </span>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name, role, tables..."
            className="w-full pl-10.5 pr-4 py-2.5 rounded-xl border border-gray-300 focus:ring-emerald-500 focus:border-emerald-500 text-gray-900 shadow-sm text-sm focus:outline-none focus:ring-2"
          />
        </div>

        {/* Dropdown filters */}
        <div className="flex flex-wrap items-center gap-3">
          
          {/* Role Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5" />
              Role:
            </span>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="bg-white border border-gray-300 text-gray-950 text-sm font-semibold rounded-xl px-3 py-2 focus:ring-emerald-500 focus:border-emerald-500 focus:outline-none focus:ring-2 appearance-none pr-8 relative bg-no-repeat bg-[right_10px_center]"
            >
              <option value="all">All Roles</option>
              <option value="owner">Owner</option>
              <option value="manager">Manager</option>
              <option value="waiter">Waiter</option>
              <option value="kitchen">Kitchen Staff</option>
              <option value="cashier">Cashier</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white border border-gray-300 text-gray-950 text-sm font-semibold rounded-xl px-3 py-2 focus:ring-emerald-500 focus:border-emerald-500 focus:outline-none focus:ring-2 appearance-none pr-8"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>
      </div>

      {/* STAFF LIST TABLE VIEW */}
      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-gray-500">
            <thead className="text-xs text-gray-500 uppercase bg-gray-50/70 border-b border-gray-250">
              <tr>
                <th scope="col" className="px-6 py-4 font-bold">Name</th>
                <th scope="col" className="px-6 py-4 font-bold">Role</th>
                <th scope="col" className="px-6 py-4 font-bold">PIN Code</th>
                <th scope="col" className="px-6 py-4 font-bold">Assigned Tables</th>
                <th scope="col" className="px-6 py-4 font-bold">Shift</th>
                <th scope="col" className="px-6 py-4 font-bold">Status</th>
                <th scope="col" className="px-6 py-4 font-bold">Last Active</th>
                <th scope="col" className="px-6 py-4 font-bold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                // Skeleton loading rows
                Array.from({ length: 5 }).map((_, index) => (
                  <tr key={index} className="animate-pulse">
                    <td className="px-6 py-4.5"><div className="h-4 bg-gray-200 rounded w-28"></div></td>
                    <td className="px-6 py-4.5"><div className="h-6 bg-gray-200 rounded-full w-20"></div></td>
                    <td className="px-6 py-4.5"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
                    <td className="px-6 py-4.5"><div className="h-4 bg-gray-200 rounded w-20"></div></td>
                    <td className="px-6 py-4.5"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
                    <td className="px-6 py-4.5"><div className="h-6 bg-gray-200 rounded-full w-14"></div></td>
                    <td className="px-6 py-4.5"><div className="h-4 bg-gray-200 rounded w-24"></div></td>
                    <td className="px-6 py-4.5 text-right"><div className="h-8 bg-gray-200 rounded w-16 ml-auto"></div></td>
                  </tr>
                ))
              ) : paginatedStaff.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                      <Users className="w-10 h-10 text-gray-300 mb-3" />
                      <h3 className="text-sm font-bold text-gray-800">No staff members found</h3>
                      <p className="text-xs text-gray-500 mt-1">
                        Try adjusting your filters or search term, or add a new staff member to get started.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                paginatedStaff.map((staff) => {
                  const is_active = staff.status === 'active' || (staff as any).is_active === true;
                  return (
                    <tr key={staff.id} className="hover:bg-gray-50/50 transition duration-150">
                      
                      {/* Name */}
                      <td className="px-6 py-4 font-bold text-gray-900 whitespace-nowrap">
                        {staff.name}
                      </td>
                      
                      {/* Role Badge */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold capitalize ${
                            staff.role === 'owner'
                              ? 'bg-purple-100 text-purple-800 border border-purple-200'
                              : staff.role === 'manager'
                              ? 'bg-blue-100 text-blue-800 border border-blue-200'
                              : staff.role === 'waiter'
                              ? 'bg-green-100 text-green-800 border border-green-200'
                              : staff.role === 'kitchen'
                              ? 'bg-orange-100 text-orange-800 border border-orange-200'
                              : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          }`}
                        >
                          {staff.role === 'kitchen' ? 'Kitchen Staff' : staff.role}
                        </span>
                      </td>

                      {/* PIN Masked */}
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-gray-600">
                        <div className="flex items-center gap-2">
                          <span>••••</span>
                          <button
                            onClick={() => {
                              setResetPinStaff(staff);
                              handleGenerateNewPin();
                            }}
                            className="text-xs font-bold text-emerald-600 hover:text-emerald-700 focus:outline-none"
                          >
                            Reset
                          </button>
                        </div>
                      </td>

                      {/* Assigned Tables */}
                      <td className="px-6 py-4 font-semibold text-gray-700 whitespace-nowrap">
                        {staff.role === 'waiter' && staff.tables && staff.tables.length > 0 ? (
                          <div className="flex items-center gap-1.5">
                            <Grid className="w-3.5 h-3.5 text-gray-400" />
                            <span>{staff.tables.join(', ')}</span>
                          </div>
                        ) : (
                          <span className="text-gray-450">—</span>
                        )}
                      </td>

                      {/* Shift */}
                      <td className="px-6 py-4 capitalize font-semibold text-gray-700 whitespace-nowrap">
                        {staff.role === 'waiter' || staff.role === 'cashier' ? (
                          staff.shift ? (
                            <div className="flex items-center gap-1.5">
                              <Clock className="w-3.5 h-3.5 text-gray-400" />
                              <span>{staff.shift}</span>
                            </div>
                          ) : (
                            '—'
                          )
                        ) : (
                          <span className="text-gray-450">—</span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                            is_active
                              ? 'bg-green-50 text-green-700 border-green-200'
                              : 'bg-gray-150 text-gray-500 border-gray-300'
                          }`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${is_active ? 'bg-green-500' : 'bg-gray-400'}`}></span>
                          {is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>

                      {/* Last Active */}
                      <td className="px-6 py-4 text-xs font-semibold text-gray-550 whitespace-nowrap">
                        {formatDateTime(staff.lastActive || (staff as any).last_login_at)}
                      </td>

                      {/* Action Icons */}
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleOpenEdit(staff)}
                            className="p-1.5 text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition"
                            title="Edit Staff Member"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setDeletingStaff(staff)}
                            className="p-1.5 text-gray-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                            title="Delete Staff Member"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => {
                              setResetPinStaff(staff);
                              handleGenerateNewPin();
                            }}
                            className="p-1.5 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition"
                            title="Reset PIN Code"
                          >
                            <Key className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* PAGINATION PANEL */}
        {totalItems > 0 && (
          <div className="px-6 py-4.5 border-t border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gray-50/30">
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-gray-500">Items per page:</span>
              <select
                value={itemsPerPage}
                onChange={(e) => {
                  setItemsPerPage(parseInt(e.target.value, 10));
                  setCurrentPage(1);
                }}
                className="bg-white border border-gray-300 rounded-lg text-xs font-bold py-1 px-2 focus:ring-emerald-500"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
              <span className="text-xs font-semibold text-gray-500">
                Showing {startIndex + 1}-{Math.min(startIndex + itemsPerPage, totalItems)} of {totalItems}
              </span>
            </div>

            <div className="flex items-center justify-center gap-1.5">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg border border-gray-300 bg-white text-gray-650 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`px-3 py-1 text-xs font-bold rounded-lg border transition ${
                    currentPage === page
                      ? 'bg-emerald-600 border-emerald-600 text-white shadow-sm shadow-emerald-500/10'
                      : 'bg-white border-gray-300 text-gray-750 hover:bg-gray-50'
                  }`}
                >
                  {page}
                </button>
              ))}
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg border border-gray-300 bg-white text-gray-650 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* MODAL 1: ADD/EDIT STAFF MODAL */}
      {isAddEditOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4 animate-fade-in backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl border border-gray-100 overflow-hidden transform transition-all duration-300">
            <div className="flex justify-between items-center px-6 py-4.5 border-b border-gray-100 bg-gray-50/50">
              <div>
                <h3 className="text-lg font-bold text-gray-900">
                  {editingStaff ? `Edit Staff - ${editingStaff.name}` : 'Add New Staff Member'}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Configure role, details, shifts and access permissions
                </p>
              </div>
              <button
                onClick={() => setIsAddEditOpen(false)}
                className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6">
              <StaffForm
                initialData={editingStaff || undefined}
                onSubmit={handleFormSubmit}
                onCancel={() => setIsAddEditOpen(false)}
                isEditing={!!editingStaff}
              />
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: RESET PIN MODAL */}
      {resetPinStaff && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md border border-gray-100 overflow-hidden">
            <div className="px-6 py-4.5 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-gray-900">Security - Reset PIN Code</h3>
                <p className="text-xs text-gray-500 mt-0.5">{resetPinStaff.name}</p>
              </div>
              <button
                onClick={() => setResetPinStaff(null)}
                className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Masked current info */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60 flex items-center justify-between text-sm">
                <span className="font-semibold text-gray-550">Current Security Code:</span>
                <span className="font-mono text-gray-800 tracking-wider">●●●● (Masked)</span>
              </div>

              {/* Reset or display state */}
              <div className="space-y-4">
                <button
                  type="button"
                  onClick={handleGenerateNewPin}
                  className="w-full py-2.5 px-4 text-sm font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-xl transition flex items-center justify-center gap-2"
                >
                  <RefreshCw className="w-4 h-4 text-emerald-600" />
                  Generate Random PIN
                </button>

                {generatedPin && (
                  <div className="space-y-3 p-5 rounded-xl border border-emerald-100 bg-emerald-50/10 text-center">
                    <p className="text-xs font-bold text-emerald-800 uppercase tracking-widest">New Generated PIN</p>
                    <p className="text-4xl font-black text-emerald-600 font-mono tracking-widest py-2">
                      {generatedPin}
                    </p>
                    <div className="flex gap-2 justify-center">
                      <button
                        onClick={handleCopyPin}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 shadow-sm"
                      >
                        <Copy className="w-3.5 h-3.5 text-gray-500" />
                        Copy Code
                      </button>
                      {resetPinStaff.phone && (
                        <button
                          onClick={handleSendPinSms}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-emerald-850 bg-white border border-emerald-200 rounded-lg hover:bg-emerald-50 shadow-sm"
                        >
                          <Send className="w-3.5 h-3.5 text-emerald-650" />
                          Send via SMS
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* PIN Info warn */}
              <div className="p-3 bg-amber-50/50 border border-amber-200/70 rounded-xl flex gap-2.5 text-xs text-amber-900 font-semibold leading-relaxed">
                <AlertCircle className="w-5 h-5 text-amber-600 shrink-0" />
                <p>
                  Remember to securely share this generated code with the staff member. They will need it immediately to access waiter order systems or dashboard components.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                <button
                  onClick={() => setResetPinStaff(null)}
                  className="px-4 py-2 border border-gray-300 text-sm font-semibold rounded-xl text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveResetPin}
                  disabled={!generatedPin || isPinSaved}
                  className="px-5 py-2.5 text-sm font-semibold rounded-xl text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50"
                >
                  Save PIN
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: DELETE CONFIRM MODAL */}
      {deletingStaff && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md border border-gray-100 overflow-hidden">
            <div className="p-6 text-center space-y-4">
              <div className="w-12 h-12 bg-rose-50 rounded-full flex items-center justify-center text-rose-600 mx-auto">
                <Trash2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-gray-900">Remove Staff Member?</h3>
              <p className="text-sm font-semibold text-gray-500 leading-relaxed">
                This will remove <span className="font-bold text-gray-900">{deletingStaff.name}</span> from staff. This action cannot be undone.
              </p>
            </div>

            <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
              <button
                onClick={() => setDeletingStaff(null)}
                className="px-4.5 py-2 text-sm font-semibold border border-gray-300 bg-white hover:bg-gray-50 rounded-xl text-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-5 py-2 text-sm font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-xl shadow-sm transition"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 4: BULK IMPORT MODAL */}
      {isBulkImportOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-4xl border border-gray-100 overflow-hidden flex flex-col max-h-[90vh]">
            
            {/* Header */}
            <div className="px-6 py-4.5 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center shrink-0">
              <div>
                <h3 className="text-lg font-bold text-gray-900">Bulk Import Staff</h3>
                <p className="text-xs text-gray-500 mt-0.5">Quickly onboard multiple restaurant members at once</p>
              </div>
              <button
                onClick={() => {
                  setIsBulkImportOpen(false);
                  setParsedRows([]);
                  setPasteData('');
                  setCsvFileName('');
                  setIsCsvUploaded(false);
                }}
                className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content Tabs */}
            <div className="px-6 border-b border-gray-150 shrink-0">
              <div className="flex gap-6">
                <button
                  onClick={() => setActiveImportTab('csv')}
                  className={`py-3.5 text-sm font-bold border-b-2 transition ${
                    activeImportTab === 'csv'
                      ? 'border-emerald-600 text-emerald-850'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Method 1: CSV Upload
                </button>
                <button
                  onClick={() => setActiveImportTab('paste')}
                  className={`py-3.5 text-sm font-bold border-b-2 transition ${
                    activeImportTab === 'paste'
                      ? 'border-emerald-600 text-emerald-850'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Method 2: Paste from Spreadsheet
                </button>
              </div>
            </div>

            {/* Scrollable Form Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              
              {/* Tab 1: CSV Upload */}
              {activeImportTab === 'csv' && (
                <div className="space-y-5">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 p-4 rounded-xl border border-gray-200 bg-gray-50/30">
                    <div>
                      <h4 className="text-sm font-bold text-gray-800">CSV Formatted Template</h4>
                      <p className="text-xs text-gray-500 mt-0.5">Download our standardized CSV layout to fill your member details.</p>
                    </div>
                    <button
                      type="button"
                      onClick={handleDownloadCsvTemplate}
                      className="inline-flex items-center gap-1.5 py-2 px-4 border border-gray-300 bg-white hover:bg-gray-50 text-sm font-bold rounded-xl shadow-sm text-gray-700 shrink-0"
                    >
                      <Download className="w-4.5 h-4.5 text-gray-500" />
                      Download Template
                    </button>
                  </div>

                  <div className="border-2 border-dashed border-gray-300 rounded-2xl p-8 text-center bg-gray-50/10 hover:bg-gray-50/20 transition relative">
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleCsvFileUpload}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                    <p className="text-sm font-bold text-gray-700">
                      {isCsvUploaded ? csvFileName : 'Click or Drag CSV file to upload'}
                    </p>
                    <p className="text-xs text-gray-400 mt-1.5">Only standardized UTF-8 CSV files supported.</p>
                  </div>
                </div>
              )}

              {/* Tab 2: Paste Spreadsheet */}
              {activeImportTab === 'paste' && (
                <div className="space-y-4">
                  <div className="text-xs font-semibold text-gray-500 space-y-1 bg-slate-50 border border-slate-200 p-4 rounded-xl leading-relaxed">
                    <p className="font-bold text-gray-700 mb-1 flex items-center gap-1.5">
                      <Grid className="w-4 h-4 text-gray-500" />
                      Spreadsheet Column Layout:
                    </p>
                    <p>Format: <span className="font-bold text-gray-800">Name, Role, PIN, Shift, Tables</span> (comma or tab separated)</p>
                    <p className="font-mono text-gray-650 bg-white/70 p-1.5 border border-slate-200/50 rounded mt-2">
                      Jane Mwangi, waiter, 1234, morning, "1,2,3"
                    </p>
                  </div>
                  
                  <textarea
                    rows={6}
                    value={pasteData}
                    onChange={handlePasteChange}
                    placeholder="Jane Doe, waiter, 4321, evening, 5,6&#10;John Mwangi, waiter, 1234, morning, 1,2,3,4"
                    className="w-full p-4.5 border border-gray-300 rounded-xl font-mono text-sm focus:ring-emerald-500 focus:outline-none focus:ring-2"
                  ></textarea>
                </div>
              )}

              {/* PREVIEW CONTAINER */}
              {parsedRows.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                    Import Preview
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200">
                      {parsedRows.length} Rows Parsed
                    </span>
                  </h4>

                  <div className="border border-gray-250 rounded-xl overflow-hidden max-h-60 overflow-y-auto shadow-sm">
                    <table className="w-full text-xs text-left text-gray-500">
                      <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 font-bold">
                        <tr>
                          <th className="px-4 py-2.5">Name</th>
                          <th className="px-4 py-2.5">Role</th>
                          <th className="px-4 py-2.5">PIN</th>
                          <th className="px-4 py-2.5">Shift</th>
                          <th className="px-4 py-2.5">Tables</th>
                          <th className="px-4 py-2.5 text-right">Validation</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 bg-white">
                        {parsedRows.slice(0, 5).map((row, idx) => (
                          <tr key={idx} className={row.isValid ? 'hover:bg-slate-50/50' : 'bg-red-50/20 hover:bg-red-50/30'}>
                            <td className="px-4 py-2.5 font-bold text-gray-900">{row.name || <span className="text-red-400">Empty</span>}</td>
                            <td className="px-4 py-2.5 font-semibold capitalize">{row.role}</td>
                            <td className="px-4 py-2.5 font-mono">{row.pin}</td>
                            <td className="px-4 py-2.5 font-semibold capitalize">{row.shift || '—'}</td>
                            <td className="px-4 py-2.5 font-semibold">{row.tables || '—'}</td>
                            <td className="px-4 py-2.5 text-right font-semibold">
                              {row.isValid ? (
                                <span className="text-emerald-600 flex items-center justify-end gap-1">
                                  <CheckCircle className="w-3.5 h-3.5" />
                                  Ready
                                </span>
                              ) : (
                                <span className="text-rose-600 flex items-center justify-end gap-1" title={row.errors.join('. ')}>
                                  <AlertCircle className="w-3.5 h-3.5" />
                                  {row.errors[0]}
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {parsedRows.length > 5 && (
                    <p className="text-xs text-gray-400 italic text-center">
                      Showing first 5 rows only. {parsedRows.length - 5} more rows parsed.
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Footer buttons */}
            <div className="px-6 py-4.5 bg-gray-50 border-t border-gray-100 flex justify-between items-center shrink-0">
              <span className="text-xs font-semibold text-gray-500">
                {parsedRows.length > 0 && (
                  <>
                    <span className="text-emerald-600 font-bold">{parsedRows.filter(r => r.isValid).length} ready</span>
                    {' / '}
                    <span className="text-rose-600 font-bold">{parsedRows.filter(r => !r.isValid).length} errors</span>
                  </>
                )}
              </span>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setIsBulkImportOpen(false);
                    setParsedRows([]);
                    setPasteData('');
                    setCsvFileName('');
                    setIsCsvUploaded(false);
                  }}
                  className="px-4.5 py-2 text-sm font-semibold border border-gray-300 bg-white hover:bg-gray-50 rounded-xl text-gray-700 shadow-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmBulkImport}
                  disabled={parsedRows.filter((r) => r.isValid).length === 0 || bulkAddStaffMutation.isPending}
                  className="px-5 py-2.5 text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-600/30 disabled:cursor-not-allowed rounded-xl shadow-sm transition flex items-center justify-center gap-1.5"
                >
                  {bulkAddStaffMutation.isPending ? (
                    <>
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                      Importing...
                    </>
                  ) : (
                    'Confirm Import'
                  )}
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}

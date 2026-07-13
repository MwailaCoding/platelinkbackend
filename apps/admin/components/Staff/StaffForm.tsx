// apps/admin/components/Staff/StaffForm.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Eye, EyeOff, User, Lock, Shield, Phone, Clock, Grid, AlertCircle } from 'lucide-react';

export interface Staff {
  id?: string;
  name: string;
  role: 'owner' | 'manager' | 'branch_manager' | 'waiter' | 'kitchen' | 'cashier';
  pin?: string;
  shift?: 'morning' | 'evening' | 'full';
  tables?: number[];
  status?: 'active' | 'inactive';
  lastActive?: string;
  phone?: string;
}

export interface StaffFormData {
  name: string;
  role: 'owner' | 'manager' | 'branch_manager' | 'waiter' | 'kitchen' | 'cashier';
  role_type?: string;
  pin?: string;
  shift?: 'morning' | 'evening' | 'full' | '';
  tables?: number[];
  phone?: string;
}

interface StaffFormProps {
  initialData?: Staff;
  onSubmit: (data: StaffFormData) => Promise<void>;
  onCancel: () => void;
  isEditing?: boolean;
}

export default function StaffForm({
  initialData,
  onSubmit,
  onCancel,
  isEditing = false,
}: StaffFormProps) {
  // Form State
  const [name, setName] = useState(initialData?.name || '');
  const [role, setRole] = useState<'owner' | 'manager' | 'branch_manager' | 'waiter' | 'kitchen' | 'cashier'>(
    initialData?.role || 'waiter'
  );
  const [pin, setPin] = useState('');
  const [shift, setShift] = useState<'morning' | 'evening' | 'full' | ''>(
    initialData?.shift || ''
  );
  const [selectedTables, setSelectedTables] = useState<number[]>(
    initialData?.tables || []
  );
  const [phone, setPhone] = useState(initialData?.phone || '');

  // UI State
  const [showPin, setShowPin] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [touched, setTouched] = useState<{ [key: string]: boolean }>({});

  // Fetch existing tables from DB
  const { data: tablesData } = useQuery({
    queryKey: ['tablesList'],
    queryFn: async () => {
      const res = await fetch('/api/tables');
      if (!res.ok) throw new Error('Failed to fetch tables');
      return res.json() as Promise<{ tables: { id: string; number: number; status: string }[] }>;
    },
    retry: 1,
  });

  // Fallback to 15 default tables if DB table fetch fails or is empty
  const availableTables = React.useMemo(() => {
    if (tablesData?.tables && tablesData.tables.length > 0) {
      return tablesData.tables.map(t => t.number).sort((a, b) => a - b);
    }
    return Array.from({ length: 15 }, (_, i) => i + 1);
  }, [tablesData]);

  // Handle table selection toggle
  const handleTableToggle = (tableNumber: number) => {
    setSelectedTables((prev) =>
      prev.includes(tableNumber)
        ? prev.filter((t) => t !== tableNumber)
        : [...prev, tableNumber].sort((a, b) => a - b)
    );
  };

  // Real-time validation logic
  const validate = () => {
    const newErrors: { [key: string]: string } = {};

    // Name Validation
    if (!name.trim()) {
      newErrors.name = 'Full Name is required';
    } else if (name.trim().length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    }

    // Role Validation
    if (!role) {
      newErrors.role = 'Role is required';
    }

    // PIN Validation
    if (!isEditing && !pin) {
      newErrors.pin = 'PIN Code is required';
    } else if (pin && !/^\d{4}$/.test(pin)) {
      newErrors.pin = 'PIN must be exactly 4 digits (numbers only)';
    }

    // Phone Validation (Optional, but must be valid if provided)
    if (phone && !/^\+?[1-9]\d{1,14}$/.test(phone.replace(/[\s()-]/g, ''))) {
      newErrors.phone = 'Please enter a valid phone number (e.g. +254712345678)';
    }

    // Waiter validations
    if (role === 'waiter') {
      if (selectedTables.length === 0) {
        newErrors.tables = 'At least 1 table must be assigned to waiters';
      }
      if (!shift) {
        newErrors.shift = 'Shift is required for waiters';
      }
    }

    // Cashier validations
    if (role === 'cashier') {
      if (!shift) {
        newErrors.shift = 'Shift is required for cashiers';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Run validation whenever inputs change
  useEffect(() => {
    validate();
  }, [name, role, pin, shift, selectedTables, phone]);

  // Handle Form Submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Mark everything as touched
    setTouched({
      name: true,
      role: true,
      pin: true,
      shift: true,
      phone: true,
      tables: true,
    });

    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const data: StaffFormData = {
        name: name.trim(),
        role: role === 'branch_manager' ? 'manager' : role, // fallback for DB enum if needed
        role_type: role,
        phone: phone.trim() || undefined,
        ...(role === 'waiter' || role === 'cashier' ? { shift } : { shift: '' }),
        ...(role === 'waiter' ? { tables: selectedTables } : { tables: [] }),
      };

      // Only send PIN if it was entered
      if (pin) {
        data.pin = pin;
      }

      await onSubmit(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isFormValid = Object.keys(errors).length === 0;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Full Name Field */}
        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700 block">Full Name *</label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400">
              <User className="w-5 h-5" />
            </span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onBlur={() => setTouched(prev => ({ ...prev, name: true }))}
              placeholder="e.g. John Mwangi"
              className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${
                touched.name && errors.name 
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-500 bg-red-50/30' 
                  : 'border-gray-300 focus:ring-emerald-500 focus:border-emerald-500'
              } text-gray-900 shadow-sm focus:outline-none focus:ring-2`}
            />
          </div>
          {touched.name && errors.name && (
            <p className="text-xs text-red-600 flex items-center gap-1 mt-1">
              <AlertCircle className="w-3.5 h-3.5" />
              {errors.name}
            </p>
          )}
        </div>

        {/* Role Select Field */}
        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700 block">Role *</label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400">
              <Shield className="w-5 h-5" />
            </span>
            <select
              value={role}
              onChange={(e) => {
                const selectedRole = e.target.value as any;
                setRole(selectedRole);
                // Clear tables and shifts if role changes
                if (selectedRole !== 'waiter') setSelectedTables([]);
                if (selectedRole !== 'waiter' && selectedRole !== 'cashier') setShift('');
              }}
              onBlur={() => setTouched(prev => ({ ...prev, role: true }))}
              className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${
                touched.role && errors.role
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-500 bg-red-50/30'
                  : 'border-gray-300 focus:ring-emerald-500 focus:border-emerald-500'
              } text-gray-900 shadow-sm focus:outline-none focus:ring-2 appearance-none bg-white`}
            >
              <option value="owner">Owner</option>
              <option value="manager">Manager</option>
              <option value="branch_manager">Branch Manager</option>
              <option value="waiter">Waiter</option>
              <option value="kitchen">Kitchen Staff</option>
              <option value="cashier">Cashier</option>
            </select>
          </div>
          {touched.role && errors.role && (
            <p className="text-xs text-red-600 flex items-center gap-1 mt-1">
              <AlertCircle className="w-3.5 h-3.5" />
              {errors.role}
            </p>
          )}
        </div>

        {/* PIN Code Field */}
        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700 block">
            PIN Code {isEditing ? '(Optional)' : '*'}
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400">
              <Lock className="w-5 h-5" />
            </span>
            <input
              type={showPin ? 'text' : 'password'}
              value={pin}
              maxLength={4}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
              onBlur={() => setTouched(prev => ({ ...prev, pin: true }))}
              placeholder={isEditing ? '•••• (Leave blank to keep current)' : 'e.g. 1234'}
              className={`w-full pl-10 pr-10 py-2.5 rounded-xl border ${
                touched.pin && errors.pin
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-500 bg-red-50/30'
                  : 'border-gray-300 focus:ring-emerald-500 focus:border-emerald-500'
              } text-gray-900 shadow-sm focus:outline-none focus:ring-2 font-mono tracking-widest`}
            />
            <button
              type="button"
              onClick={() => setShowPin(!showPin)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              {showPin ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
          {touched.pin && errors.pin ? (
            <p className="text-xs text-red-600 flex items-center gap-1 mt-1">
              <AlertCircle className="w-3.5 h-3.5" />
              {errors.pin}
            </p>
          ) : (
            <p className="text-xs text-gray-400 mt-1">Must be exactly 4 numeric digits.</p>
          )}
        </div>

        {/* Phone Number Field */}
        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700 block">Phone Number (Optional)</label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400">
              <Phone className="w-5 h-5" />
            </span>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              onBlur={() => setTouched(prev => ({ ...prev, phone: true }))}
              placeholder="e.g. +254712345678"
              className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${
                touched.phone && errors.phone
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-500 bg-red-50/30'
                  : 'border-gray-300 focus:ring-emerald-500 focus:border-emerald-500'
              } text-gray-900 shadow-sm focus:outline-none focus:ring-2`}
            />
          </div>
          {touched.phone && errors.phone ? (
            <p className="text-xs text-red-600 flex items-center gap-1 mt-1">
              <AlertCircle className="w-3.5 h-3.5" />
              {errors.phone}
            </p>
          ) : (
            <p className="text-xs text-gray-400 mt-1">Used to send credentials/PIN updates via SMS.</p>
          )}
        </div>

        {/* Conditional Shift Field (Waiter or Cashier only) */}
        {(role === 'waiter' || role === 'cashier') && (
          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-semibold text-gray-700 block">Shift *</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400">
                <Clock className="w-5 h-5" />
              </span>
              <select
                value={shift}
                onChange={(e) => setShift(e.target.value as any)}
                onBlur={() => setTouched(prev => ({ ...prev, shift: true }))}
                className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${
                  touched.shift && errors.shift
                    ? 'border-red-300 focus:ring-red-500 focus:border-red-500 bg-red-50/30'
                    : 'border-gray-300 focus:ring-emerald-500 focus:border-emerald-500'
                } text-gray-900 shadow-sm focus:outline-none focus:ring-2 bg-white appearance-none`}
              >
                <option value="">Select Shift</option>
                <option value="morning">Morning Shift</option>
                <option value="evening">Evening Shift</option>
                <option value="full">Full Time</option>
              </select>
            </div>
            {touched.shift && errors.shift && (
              <p className="text-xs text-red-600 flex items-center gap-1 mt-1">
                <AlertCircle className="w-3.5 h-3.5" />
                {errors.shift}
              </p>
            )}
          </div>
        )}

        {/* Conditional Assigned Tables (Waiter only) */}
        {role === 'waiter' && (
          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-semibold text-gray-700 block">
              Assigned Tables * <span className="text-xs text-gray-500 font-normal">({selectedTables.length} selected)</span>
            </label>
            
            <div className={`p-4 rounded-xl border ${
              touched.tables && errors.tables ? 'border-red-300 bg-red-50/10' : 'border-gray-200'
            } bg-gray-50/50 max-h-48 overflow-y-auto`}>
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
                {availableTables.map((tableNumber) => {
                  const isChecked = selectedTables.includes(tableNumber);
                  return (
                    <button
                      type="button"
                      key={tableNumber}
                      onClick={() => handleTableToggle(tableNumber)}
                      className={`py-2 px-3 rounded-lg border text-xs font-bold text-center transition-all ${
                        isChecked
                          ? 'bg-emerald-50 border-emerald-500 text-emerald-800 ring-2 ring-emerald-500/20'
                          : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-center gap-1">
                        <Grid className={`w-3.5 h-3.5 ${isChecked ? 'text-emerald-600' : 'text-gray-400'}`} />
                        <span>T{tableNumber}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
            {touched.tables && errors.tables && (
              <p className="text-xs text-red-600 flex items-center gap-1 mt-1">
                <AlertCircle className="w-3.5 h-3.5" />
                {errors.tables}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Buttons */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
        <button
          type="button"
          onClick={onCancel}
          className="px-5 py-2.5 rounded-xl border border-gray-300 text-sm font-semibold text-gray-700 bg-white hover:bg-gray-50 hover:text-gray-900 transition shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-200"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting || !isFormValid}
          className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-600/40 disabled:cursor-not-allowed transition shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              Saving...
            </>
          ) : (
            'Save Staff'
          )}
        </button>
      </div>
    </form>
  );
}

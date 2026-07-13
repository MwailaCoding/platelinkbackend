// apps/admin/components/Analytics/SalesChart.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend 
} from 'recharts';
import { BarChart3, Calendar, AlertCircle } from 'lucide-react';

interface SalesChartProps {
  data: Array<{ 
    date: string; // date or hour, e.g. "08:00", "2026-05-25"
    sales: number; 
    orders: number; 
  }>;
  period: 'daily' | 'weekly' | 'monthly' | 'today' | '30days' | 'yearly' | 'custom' | string;
  onPeriodChange: (period: string) => void;
  loading: boolean;
}

export default function SalesChart({ 
  data, 
  period, 
  onPeriodChange, 
  loading 
}: SalesChartProps) {
  const [isMounted, setIsMounted] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Next.js hydration mismatch safety
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Parse custom dates from parent if they exist in format "custom:YYYY-MM-DD:YYYY-MM-DD"
  useEffect(() => {
    if (period.startsWith('custom:')) {
      const parts = period.split(':');
      if (parts.length === 3) {
        setStartDate(parts[1]);
        setEndDate(parts[2]);
      }
    }
  }, [period]);

  const handleCustomRangeApply = () => {
    if (startDate && endDate) {
      onPeriodChange(`custom:${startDate}:${endDate}`);
    }
  };

  // Custom tooltips for Recharts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-900 border border-gray-800 text-white p-3.5 rounded-xl shadow-xl space-y-1.5 text-xs min-w-[150px]">
          <p className="font-bold border-b border-gray-800 pb-1.5 mb-1.5 text-gray-200">
            {label}
          </p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                <span className="text-gray-400 font-medium">{entry.name}:</span>
              </div>
              <span className="font-bold text-gray-50">
                {entry.name === 'Sales' 
                  ? `KES ${Number(entry.value).toLocaleString()}` 
                  : Number(entry.value).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const periodOptions = [
    { label: 'Today', value: 'today', subtext: 'Hourly sales' },
    { label: 'This Week', value: 'weekly', subtext: 'Daily breakdown' },
    { label: 'This Month', value: 'monthly', subtext: 'Daily breakdown' },
    { label: 'Last 30 Days', value: '30days', subtext: 'Daily breakdown' },
    { label: 'This Year', value: 'yearly', subtext: 'Monthly sales' },
    { label: 'Custom Range', value: 'custom', subtext: 'Select range' },
  ];

  // Helper to determine if a period is selected
  const isActive = (val: string) => {
    if (val === 'custom') {
      return period.startsWith('custom');
    }
    return period === val;
  };

  // Render header details
  const renderHeader = () => (
    <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-4 border-b border-gray-100 pb-5">
      <div>
        <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-emerald-600" />
          Sales & Orders Overview
        </h2>
        <p className="text-gray-500 text-xs mt-0.5">
          Interactive line analysis of order volumes and total sales revenues.
        </p>
      </div>

      {/* Selectors */}
      <div className="flex flex-wrap items-center gap-1.5">
        {periodOptions.map((opt) => (
          <button
            key={opt.value}
            onClick={() => {
              if (opt.value === 'custom') {
                onPeriodChange('custom');
              } else {
                onPeriodChange(opt.value);
              }
            }}
            className={`px-3.5 py-2 text-xs font-semibold rounded-lg shadow-sm border transition-all ${
              isActive(opt.value)
                ? 'bg-emerald-600 border-emerald-600 text-white hover:bg-emerald-700'
                : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );

  // loading or SSR mounting skeleton
  if (!isMounted || loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 space-y-5">
        {/* Header Skeleton */}
        <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-4 border-b border-gray-100 pb-5 animate-pulse">
          <div className="space-y-2">
            <div className="h-5 bg-gray-200 rounded w-44"></div>
            <div className="h-3 bg-gray-200 rounded w-64"></div>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-8 bg-gray-200 rounded-lg w-20"></div>
            ))}
          </div>
        </div>

        {/* Chart Skeleton */}
        <div className="h-[350px] w-full flex flex-col justify-between border-l border-b border-gray-100 p-4 animate-pulse relative bg-gray-50/10 rounded-xl">
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
            <span className="w-6 h-6 border-2 border-emerald-500/20 border-t-emerald-600 rounded-full animate-spin"></span>
            <span className="text-xs font-semibold text-gray-400">Loading chart analytics...</span>
          </div>
          <div className="space-y-10 w-full">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="border-t border-dashed border-gray-100 w-full h-0"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5 space-y-4">
      {renderHeader()}

      {/* Custom range date inputs picker */}
      {period.startsWith('custom') && (
        <div className="flex flex-wrap items-center gap-3 p-4 bg-gray-50 border border-gray-100 rounded-xl mt-1 animate-fadeIn">
          <div className="flex items-center gap-2.5">
            <Calendar className="w-4 h-4 text-gray-400" />
            <span className="text-xs font-bold text-gray-600">Custom Period:</span>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">From</span>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="px-2.5 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 text-gray-700 bg-white"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">To</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="px-2.5 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 text-gray-700 bg-white"
            />
          </div>

          <button
            onClick={handleCustomRangeApply}
            disabled={!startDate || !endDate}
            className="px-4 py-1.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-600/30 disabled:cursor-not-allowed rounded-lg shadow-sm transition-all"
          >
            Apply Range
          </button>
        </div>
      )}

      {/* Chart Legend */}
      <div className="flex items-center gap-5 px-1 py-1.5 border-b border-gray-50">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-emerald-600" />
          <span className="text-xs font-bold text-gray-700">Sales (KES)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-orange-500" />
          <span className="text-xs font-bold text-gray-700">Orders</span>
        </div>
      </div>

      {/* Main Chart content */}
      <div className="w-full h-[350px] mt-4">
        {!data || data.length === 0 ? (
          <div className="h-full w-full flex flex-col items-center justify-center border border-dashed border-gray-200 rounded-xl bg-gray-50/50 p-6 text-center">
            <div className="p-3.5 bg-gray-100 text-gray-400 rounded-full mb-3">
              <BarChart3 className="w-7 h-7" />
            </div>
            <h3 className="text-sm font-bold text-gray-800">No Sales Data Found</h3>
            <p className="text-xs text-gray-500 max-w-xs mt-1">
              There are no orders or sales records found for this timeframe. Try shifting your active calendar filter.
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{ top: 10, right: 10, left: 10, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
              
              <XAxis 
                dataKey="date" 
                stroke="#9CA3AF" 
                fontSize={11} 
                tickLine={false}
                dy={10}
                fontFamily="inherit"
                fontWeight={500}
              />
              
              <YAxis 
                yAxisId="left" 
                orientation="left" 
                stroke="#059669"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                tickFormatter={(val) => `KES ${val >= 1000 ? (val / 1000) + 'k' : val}`}
                fontFamily="inherit"
                fontWeight={500}
              />
              
              <YAxis 
                yAxisId="right" 
                orientation="right" 
                stroke="#EA580C"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                tickFormatter={(val) => val.toLocaleString()}
                fontFamily="inherit"
                fontWeight={500}
              />
              
              <Tooltip content={<CustomTooltip />} />
              
              <Line 
                yAxisId="left" 
                type="monotone" 
                dataKey="sales" 
                stroke="#059669" 
                strokeWidth={2.5}
                dot={{ r: 3, stroke: '#059669', strokeWidth: 1.5, fill: '#FFFFFF' }}
                activeDot={{ r: 6, fill: '#059669', stroke: '#FFFFFF', strokeWidth: 2 }}
                name="Sales"
                animationDuration={600}
              />
              
              <Line 
                yAxisId="right" 
                type="monotone" 
                dataKey="orders" 
                stroke="#EA580C" 
                strokeWidth={2.5}
                dot={{ r: 3, stroke: '#EA580C', strokeWidth: 1.5, fill: '#FFFFFF' }}
                activeDot={{ r: 6, fill: '#EA580C', stroke: '#FFFFFF', strokeWidth: 2 }}
                name="Orders"
                animationDuration={600}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

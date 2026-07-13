// apps/admin/components/Analytics/CategoryBreakdown.tsx
'use client';

import React, { useState, useMemo, useEffect } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import {
  Calendar,
  ChevronDown,
  PieChart as PieIcon,
  BarChart3,
  Loader2,
  AlertCircle
} from 'lucide-react';

interface CategoryItem {
  category: string;
  revenue: number;
  percentage: number;
  color: string;
}

interface CategoryBreakdownProps {
  data: CategoryItem[];
  loading: boolean;
  onTimePeriodChange?: (period: string, customRange?: { start: string; end: string }) => void;
}

type TimePeriod = 'this_week' | 'this_month' | 'last_30_days' | 'custom';

const COLOR_MAP: Record<string, string> = {
  emerald: '#10b981',
  orange: '#f97316',
  blue: '#3b82f6',
  purple: '#8b5cf6',
  pink: '#ec4899',
};

const FALLBACK_COLORS = ['#10b981', '#f97316', '#3b82f6', '#8b5cf6', '#ec4899'];

export default function CategoryBreakdown({
  data = [],
  loading,
  onTimePeriodChange
}: CategoryBreakdownProps) {
  const [isMounted, setIsMounted] = useState(false);
  const [viewMode, setViewMode] = useState<'pie' | 'bar'>('pie');
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('this_month');
  const [customRange, setCustomRange] = useState({ start: '', end: '' });
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [hiddenCategories, setHiddenCategories] = useState<string[]>([]);

  // Next.js hydration safety
  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handlePeriodChange = (period: TimePeriod) => {
    setTimePeriod(period);
    if (period !== 'custom') {
      setShowDatePicker(false);
      onTimePeriodChange?.(period);
    } else {
      setShowDatePicker(true);
    }
  };

  const handleCustomRangeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customRange.start && customRange.end) {
      setShowDatePicker(false);
      onTimePeriodChange?.('custom', customRange);
    }
  };

  const formatPeriodLabel = (period: TimePeriod) => {
    switch (period) {
      case 'this_week': return 'This Week';
      case 'this_month': return 'This Month';
      case 'last_30_days': return 'Last 30 Days';
      case 'custom':
        return customRange.start && customRange.end
          ? `${customRange.start} to ${customRange.end}`
          : 'Custom Range';
      default: return 'Select Period';
    }
  };

  const toggleCategoryVisibility = (category: string) => {
    setHiddenCategories(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  // Helper to retrieve color
  const getCategoryColor = (item: CategoryItem, index: number) => {
    if (item.color) {
      const lowerColor = item.color.toLowerCase();
      if (COLOR_MAP[lowerColor]) {
        return COLOR_MAP[lowerColor];
      }
      if (item.color.startsWith('#')) {
        return item.color;
      }
    }
    return FALLBACK_COLORS[index % FALLBACK_COLORS.length];
  };

  // Calculate visible data for rendering
  const visibleData = useMemo(() => {
    if (!data) return [];
    return data.filter(item => !hiddenCategories.includes(item.category));
  }, [data, hiddenCategories]);

  // Calculate total revenue of all categories (or only visible, let's do visible to reflect center updates dynamically)
  const totalRevenue = useMemo(() => {
    return visibleData.reduce((sum, item) => sum + item.revenue, 0);
  }, [visibleData]);

  // Custom tooltips for Pie chart
  const CustomPieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const itemData = payload[0].payload as CategoryItem;
      const index = data.findIndex(d => d.category === itemData.category);
      const color = getCategoryColor(itemData, index);
      return (
        <div className="bg-white p-4 border border-gray-100 shadow-xl rounded-xl text-xs space-y-1.5 min-w-[180px]">
          <p className="font-bold text-gray-900 border-b border-gray-100 pb-1 mb-1.5 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            {itemData.category}
          </p>
          <div className="flex justify-between items-center text-gray-600">
            <span>Revenue:</span>
            <span className="font-semibold text-emerald-600">KES {itemData.revenue.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center text-gray-600">
            <span>Percentage:</span>
            <span className="font-semibold text-blue-600">{itemData.percentage.toFixed(1)}%</span>
          </div>
        </div>
      );
    }
    return null;
  };

  // Custom tooltips for Bar chart
  const CustomBarTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const itemData = payload[0].payload as CategoryItem;
      const index = data.findIndex(d => d.category === itemData.category);
      const color = getCategoryColor(itemData, index);
      return (
        <div className="bg-white p-4 border border-gray-100 shadow-xl rounded-xl text-xs space-y-1.5 min-w-[180px]">
          <p className="font-bold text-gray-900 border-b border-gray-100 pb-1 mb-1.5 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            {itemData.category}
          </p>
          <div className="flex justify-between items-center text-gray-600">
            <span>Revenue:</span>
            <span className="font-semibold text-emerald-600">KES {itemData.revenue.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center text-gray-600">
            <span>Percentage:</span>
            <span className="font-semibold text-blue-600">{itemData.percentage.toFixed(1)}%</span>
          </div>
        </div>
      );
    }
    return null;
  };

  // Pre-loading fallback or SSR safety
  if (!isMounted) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex flex-col min-h-[480px] animate-pulse">
        <div className="h-6 bg-gray-100 rounded w-48 mb-6" />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex flex-col relative overflow-hidden transition-all duration-300 hover:shadow-md min-h-[480px]">
      
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 border-b border-gray-50 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 bg-emerald-50 rounded-lg text-emerald-600">
              <PieIcon className="w-5 h-5" />
            </span>
            <h3 className="text-lg font-bold text-gray-900">Category Breakdown</h3>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Revenue distribution across sales categories
          </p>
        </div>

        {/* CONTROLS */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Time Selector */}
          <div className="relative">
            <button
              onClick={() => setShowDatePicker(!showDatePicker)}
              className="flex items-center gap-2 px-3 py-1.5 border border-gray-200 rounded-lg text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 shadow-sm transition"
            >
              <Calendar className="w-3.5 h-3.5 text-gray-400" />
              <span>{formatPeriodLabel(timePeriod)}</span>
              <ChevronDown className="w-3 h-3 text-gray-400" />
            </button>

            {showDatePicker && (
              <div className="absolute right-0 mt-2 w-64 bg-white border border-gray-100 rounded-xl shadow-xl p-4 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                <div className="space-y-3">
                  <div className="text-xs font-bold text-gray-900 border-b border-gray-50 pb-2">Select Time Period</div>
                  <div className="grid grid-cols-1 gap-1">
                    {(['this_week', 'this_month', 'last_30_days', 'custom'] as TimePeriod[]).map((period) => (
                      <button
                        key={period}
                        onClick={() => handlePeriodChange(period)}
                        className={`text-left px-2.5 py-1.5 rounded-lg text-xs transition ${
                          timePeriod === period
                            ? 'bg-emerald-50 text-emerald-700 font-semibold'
                            : 'text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        {period === 'this_week' && 'This Week'}
                        {period === 'this_month' && 'This Month'}
                        {period === 'last_30_days' && 'Last 30 Days'}
                        {period === 'custom' && 'Custom Range'}
                      </button>
                    ))}
                  </div>

                  {timePeriod === 'custom' && (
                    <form onSubmit={handleCustomRangeSubmit} className="space-y-2.5 pt-2 border-t border-gray-50">
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-gray-400 uppercase">Start Date</label>
                        <input
                          type="date"
                          value={customRange.start}
                          onChange={(e) => setCustomRange(prev => ({ ...prev, start: e.target.value }))}
                          required
                          className="w-full text-xs p-1.5 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-emerald-500"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-gray-400 uppercase">End Date</label>
                        <input
                          type="date"
                          value={customRange.end}
                          onChange={(e) => setCustomRange(prev => ({ ...prev, end: e.target.value }))}
                          required
                          className="w-full text-xs p-1.5 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-emerald-500"
                        />
                      </div>
                      <button
                        type="submit"
                        className="w-full py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-semibold shadow-sm transition"
                      >
                        Apply Range
                      </button>
                    </form>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Toggle View (Pie vs Bar) */}
          <div className="flex items-center border border-gray-200 rounded-lg p-0.5 shadow-sm bg-gray-50">
            <button
              onClick={() => setViewMode('pie')}
              className={`p-1.5 rounded-md transition ${viewMode === 'pie' ? 'bg-white text-emerald-600 shadow-xs' : 'text-gray-400 hover:text-gray-600'}`}
              title="Pie Chart View"
            >
              <PieIcon className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('bar')}
              className={`p-1.5 rounded-md transition ${viewMode === 'bar' ? 'bg-white text-emerald-600 shadow-xs' : 'text-gray-400 hover:text-gray-600'}`}
              title="Bar Chart View"
            >
              <BarChart3 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* CHART CONTENT */}
      <div className="flex-1 flex flex-col justify-center">
        {loading ? (
          <div className="flex flex-col items-center justify-center space-y-3 h-[300px]">
            <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
            <p className="text-xs text-gray-500 animate-pulse">Loading category analytics...</p>
          </div>
        ) : !data || data.length === 0 ? (
          <div className="flex flex-col items-center justify-center border border-dashed border-gray-200 rounded-xl p-8 text-center h-[300px]">
            <AlertCircle className="w-10 h-10 text-gray-300 mb-2" />
            <p className="text-sm font-semibold text-gray-700">No category breakdown data found</p>
            <p className="text-xs text-gray-400 mt-1 max-w-[280px]">There are no category sales recorded for this selection.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            
            {/* LEFT / CENTER: THE CHART (Takes 7 cols on desktop) */}
            <div className="lg:col-span-7 flex justify-center items-center relative w-full h-[300px]">
              
              {visibleData.length === 0 ? (
                <div className="text-center p-4 border border-dashed border-gray-100 rounded-xl w-full h-full flex flex-col items-center justify-center bg-gray-50/30">
                  <AlertCircle className="w-6 h-6 text-gray-300 mb-1" />
                  <p className="text-xs text-gray-400">All categories hidden. Click legend to show.</p>
                </div>
              ) : viewMode === 'pie' ? (
                <>
                  {/* DONUT CHART */}
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Tooltip content={<CustomPieTooltip />} />
                      <Pie
                        data={visibleData}
                        cx="50%"
                        cy="50%"
                        innerRadius="65%"
                        outerRadius="85%"
                        paddingAngle={4}
                        dataKey="revenue"
                        nameKey="category"
                      >
                        {visibleData.map((entry) => {
                          const index = data.findIndex(d => d.category === entry.category);
                          const color = getCategoryColor(entry, index);
                          return (
                            <Cell
                              key={`cell-${entry.category}`}
                              fill={color}
                              className="transition-all duration-200 hover:opacity-90 outline-none"
                            />
                          );
                        })}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>

                  {/* CENTER TEXT */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-10">
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                      Total Revenue
                    </span>
                    <span className="text-lg md:text-xl font-extrabold text-gray-900 mt-0.5">
                      KES {totalRevenue.toLocaleString()}
                    </span>
                  </div>
                </>
              ) : (
                /* BAR CHART (Alternative View) */
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={visibleData}
                    margin={{ top: 20, right: 10, left: 10, bottom: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
                    <XAxis
                      dataKey="category"
                      axisLine={false}
                      tickLine={false}
                      stroke="#4b5563"
                      fontSize={10}
                      fontWeight={500}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      stroke="#9ca3af"
                      fontSize={9}
                      tickFormatter={(val) => `KES ${val >= 1000 ? (val / 1000) + 'k' : val}`}
                    />
                    <Tooltip content={<CustomBarTooltip />} cursor={{ fill: '#f9fafb' }} />
                    <Bar
                      dataKey="revenue"
                      radius={[6, 6, 0, 0]}
                      maxBarSize={45}
                    >
                      {visibleData.map((entry) => {
                        const index = data.findIndex(d => d.category === entry.category);
                        const color = getCategoryColor(entry, index);
                        return (
                          <Cell
                            key={`cell-${entry.category}`}
                            fill={color}
                            className="transition-all duration-200 hover:opacity-85"
                          />
                        );
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* RIGHT: THE LEGEND (Takes 5 cols on desktop) */}
            <div className="lg:col-span-5 flex flex-col space-y-2">
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2 hidden lg:block">
                Categories
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-2 max-h-[280px] overflow-y-auto pr-1">
                {data.map((item, index) => {
                  const color = getCategoryColor(item, index);
                  const isHidden = hiddenCategories.includes(item.category);
                  return (
                    <button
                      key={item.category}
                      onClick={() => toggleCategoryVisibility(item.category)}
                      className={`flex items-center justify-between p-2.5 rounded-xl border transition text-left w-full hover:shadow-xs group ${
                        isHidden
                          ? 'bg-gray-50/50 border-gray-100 text-gray-400 opacity-60'
                          : 'bg-white border-gray-100 text-gray-700 hover:bg-gray-50 hover:border-gray-200'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <span
                          className={`w-3 h-3 rounded-full transition-transform shrink-0 ${
                            isHidden ? 'scale-75' : 'group-hover:scale-110'
                          }`}
                          style={{ backgroundColor: isHidden ? '#cbd5e1' : color }}
                        />
                        <span className={`text-xs font-semibold truncate ${isHidden ? 'line-through' : 'text-gray-900'}`}>
                          {item.category}
                        </span>
                      </div>
                      
                      <span className="text-xs font-bold text-gray-500 shrink-0 ml-2">
                        {item.percentage.toFixed(1)}%
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

          </div>
        )}
      </div>

      {/* FOOTER */}
      <div className="mt-6 pt-4 border-t border-gray-50 flex items-center justify-between">
        <span className="text-[10px] text-gray-400 italic">
          * Click category card to filter slice
        </span>
        <span className="text-[10px] font-bold text-gray-400 uppercase">
          PlateLink Analytics
        </span>
      </div>

    </div>
  );
}

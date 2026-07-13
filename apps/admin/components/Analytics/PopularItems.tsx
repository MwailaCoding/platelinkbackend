// apps/admin/components/Analytics/PopularItems.tsx
'use client';

import React, { useState, useMemo } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell
} from 'recharts';
import { 
  Calendar, 
  ChevronDown, 
  ArrowUpDown, 
  TrendingUp, 
  TrendingDown, 
  LayoutList, 
  BarChart3,
  Loader2,
  AlertCircle
} from 'lucide-react';

interface PopularItem {
  name: string;
  quantity: number;
  revenue: number;
  percentage: number;
}

interface PopularItemsProps {
  data: PopularItem[];
  limit?: number;
  onItemClick?: (itemName: string) => void;
  loading: boolean;
  onTimePeriodChange?: (period: string, customRange?: { start: string; end: string }) => void;
}

type TimePeriod = 'this_week' | 'this_month' | 'last_30_days' | 'custom';
type SortKey = 'quantity' | 'revenue';
type SortOrder = 'asc' | 'desc';

export default function PopularItems({
  data = [],
  limit = 10,
  onItemClick,
  loading,
  onTimePeriodChange
}: PopularItemsProps) {
  // State variables
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('this_month');
  const [customRange, setCustomRange] = useState({ start: '', end: '' });
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showLeastPopular, setShowLeastPopular] = useState(false);
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');
  
  // Table sorting states
  const [tableSortKey, setTableSortKey] = useState<SortKey>('quantity');
  const [tableSortOrder, setTableSortOrder] = useState<SortOrder>('desc');

  // Handle time period change
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

  // Sort and process data based on Top vs Bottom toggle and limit
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    // Create a copy to avoid mutation
    const items = [...data];
    
    // Sort for Top vs Least Popular
    items.sort((a, b) => {
      if (showLeastPopular) {
        return a.quantity - b.quantity; // Ascending for least popular
      } else {
        return b.quantity - a.quantity; // Descending for most popular
      }
    });

    return items.slice(0, limit);
  }, [data, showLeastPopular, limit]);

  // Sort specifically for table viewing (allows users to re-sort columns)
  const tableData = useMemo(() => {
    const items = [...processedData];
    items.sort((a, b) => {
      const valA = a[tableSortKey];
      const valB = b[tableSortKey];
      
      if (tableSortOrder === 'asc') {
        return valA > valB ? 1 : -1;
      } else {
        return valA < valB ? 1 : -1;
      }
    });
    return items;
  }, [processedData, tableSortKey, tableSortOrder]);

  const handleSort = (key: SortKey) => {
    if (tableSortKey === key) {
      setTableSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setTableSortKey(key);
      setTableSortOrder('desc');
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

  // Custom tooltips for Recharts
  const CustomTooltipComponent = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const itemData = payload[0].payload as PopularItem;
      return (
        <div className="bg-white p-4 border border-gray-100 shadow-xl rounded-xl text-xs space-y-1.5 min-w-[200px]">
          <p className="font-bold text-gray-900 border-b border-gray-100 pb-1 mb-1.5">{itemData.name}</p>
          <div className="flex justify-between items-center text-gray-600">
            <span>Quantity Sold:</span>
            <span className="font-semibold text-gray-950">{itemData.quantity.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center text-gray-600">
            <span>Revenue:</span>
            <span className="font-semibold text-emerald-600">KES {itemData.revenue.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center text-gray-600">
            <span>Sales Share:</span>
            <span className="font-semibold text-blue-600">{itemData.percentage.toFixed(1)}%</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex flex-col relative overflow-hidden transition-all duration-300 hover:shadow-md">
      
      {/* HEADER SECTION */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 border-b border-gray-50 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 bg-emerald-50 rounded-lg text-emerald-600">
              {showLeastPopular ? <TrendingDown className="w-5 h-5" /> : <TrendingUp className="w-5 h-5" />}
            </span>
            <h3 className="text-lg font-bold text-gray-900">
              {showLeastPopular ? 'Least Popular Items' : 'Popular Items'}
            </h3>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {showLeastPopular 
              ? `Bottom ${limit} dishes and drinks by volume sold` 
              : `Top ${limit} best-selling dishes and drinks`
            }
          </p>
        </div>

        {/* CONTROLS */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Time Selector Dropdown */}
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

          {/* Toggle View (Chart vs Table) */}
          <div className="flex items-center border border-gray-200 rounded-lg p-0.5 shadow-sm bg-gray-50">
            <button
              onClick={() => setViewMode('chart')}
              className={`p-1.5 rounded-md transition ${viewMode === 'chart' ? 'bg-white text-emerald-600 shadow-xs' : 'text-gray-400 hover:text-gray-600'}`}
              title="Chart View"
            >
              <BarChart3 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-md transition ${viewMode === 'table' ? 'bg-white text-emerald-600 shadow-xs' : 'text-gray-400 hover:text-gray-600'}`}
              title="Table View"
            >
              <LayoutList className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* MAIN CONTAINER */}
      <div className="flex-1 min-h-[400px] flex flex-col justify-center">
        {loading ? (
          <div className="flex flex-col items-center justify-center space-y-3 h-[400px]">
            <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
            <p className="text-xs text-gray-500 animate-pulse">Loading analytics data...</p>
          </div>
        ) : processedData.length === 0 ? (
          <div className="flex flex-col items-center justify-center border border-dashed border-gray-200 rounded-xl p-8 text-center h-[400px]">
            <AlertCircle className="w-10 h-10 text-gray-300 mb-2" />
            <p className="text-sm font-semibold text-gray-700">No popular items data found</p>
            <p className="text-xs text-gray-400 mt-1 max-w-[280px]">There are no sales recorded for the selected time period.</p>
          </div>
        ) : (
          <>
            {/* DESKTOP CHART VIEW (Hidden on mobile fallback, default view mode 'chart') */}
            <div className={`w-full h-[400px] transition-all duration-300 ${viewMode === 'chart' ? 'block md:block' : 'hidden'} ${viewMode === 'table' ? 'hidden' : 'block md:block'}`}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  layout="vertical"
                  data={processedData}
                  margin={{ top: 10, right: 35, left: 45, bottom: 10 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={true} vertical={false} />
                  <XAxis 
                    type="number" 
                    tickLine={false} 
                    axisLine={false} 
                    stroke="#9ca3af" 
                    fontSize={10} 
                  />
                  <YAxis 
                    type="category" 
                    dataKey="name" 
                    tickLine={false} 
                    axisLine={false} 
                    stroke="#374151" 
                    fontSize={10}
                    width={90}
                    tickFormatter={(value) => value.length > 12 ? `${value.substring(0, 12)}...` : value}
                  />
                  <Tooltip content={<CustomTooltipComponent />} cursor={{ fill: '#f9fafb' }} />
                  <Bar 
                    dataKey="quantity" 
                    radius={[0, 6, 6, 0]}
                    maxBarSize={30}
                    cursor="pointer"
                    onClick={(entry) => onItemClick?.(entry.name)}
                  >
                    {processedData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill="#10b981" 
                        className="transition-all duration-200 hover:opacity-85"
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* MOBILE FALLBACK & MANUAL TABLE VIEW */}
            <div className={`w-full transition-all duration-300 ${viewMode === 'table' ? 'block' : 'hidden md:block'} ${viewMode === 'chart' ? 'md:hidden block' : 'block'}`}>
              <div className="overflow-x-auto border border-gray-100 rounded-xl">
                <table className="min-w-full divide-y divide-gray-100 text-left">
                  <thead>
                    <tr className="bg-gray-50 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                      <th className="px-4 py-3">Item</th>
                      <th 
                        className="px-4 py-3 cursor-pointer hover:bg-gray-100 transition" 
                        onClick={() => handleSort('quantity')}
                      >
                        <div className="flex items-center gap-1">
                          <span>Qty Sold</span>
                          <ArrowUpDown className="w-3 h-3 text-gray-400" />
                        </div>
                      </th>
                      <th 
                        className="px-4 py-3 cursor-pointer hover:bg-gray-100 transition" 
                        onClick={() => handleSort('revenue')}
                      >
                        <div className="flex items-center gap-1">
                          <span>Revenue</span>
                          <ArrowUpDown className="w-3 h-3 text-gray-400" />
                        </div>
                      </th>
                      <th className="px-4 py-3">% of Sales</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50 text-xs text-gray-700 bg-white">
                    {tableData.map((item, index) => (
                      <tr 
                        key={item.name} 
                        onClick={() => onItemClick?.(item.name)}
                        className={`hover:bg-emerald-50/30 transition cursor-pointer ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}
                      >
                        <td className="px-4 py-3 font-semibold text-gray-900">{item.name}</td>
                        <td className="px-4 py-3 font-medium">{item.quantity.toLocaleString()}</td>
                        <td className="px-4 py-3 font-medium text-emerald-600">KES {item.revenue.toLocaleString()}</td>
                        <td className="px-4 py-3 text-gray-500">{item.percentage.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>

      {/* BOTTOM LEAST POPULAR TOGGLE BUTTON */}
      <div className="mt-5 pt-4 border-t border-gray-50 flex items-center justify-between">
        <button
          onClick={() => setShowLeastPopular(!showLeastPopular)}
          className={`px-4 py-2 border rounded-xl text-xs font-bold transition shadow-sm ${
            showLeastPopular 
              ? 'bg-amber-50 border-amber-200 text-amber-700 hover:bg-amber-100 hover:border-amber-300' 
              : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
          }`}
        >
          {showLeastPopular ? 'Show Top Selling Items' : 'Show Least Popular Items'}
        </button>

        <span className="text-[10px] font-semibold text-gray-400 uppercase">
          PlateLink Analytics
        </span>
      </div>

    </div>
  );
}

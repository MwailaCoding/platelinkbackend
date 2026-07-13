// apps/admin/components/Analytics/WaiterPerformance.tsx
'use client';

import React, { useState, useMemo } from 'react';
import {
  User,
  TrendingUp,
  Award,
  Star,
  Clock,
  DollarSign,
  Search,
  Download,
  Printer,
  ArrowUpDown,
  ChevronUp,
  ChevronDown,
  Calendar,
  BarChart3,
  LayoutList,
  Loader2,
  AlertCircle,
  Coffee,
  Sparkles
} from 'lucide-react';
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

export interface WaiterPerformanceData {
  id: string;
  name: string;
  orders: number;
  avgTime: number; // in minutes
  revenue: number; // KES
  avgTicket: number; // KES
  rating: number; // 1-5
  tablesServed: number;
}

interface WaiterPerformanceProps {
  data: WaiterPerformanceData[];
  loading: boolean;
  onDateRangeChange?: (range: { start: string; end: string } | null) => void;
}

type SortKey = 'name' | 'orders' | 'avgTime' | 'revenue' | 'avgTicket' | 'rating' | 'tablesServed';
type SortOrder = 'asc' | 'desc';
type ChartMetric = 'orders' | 'revenue';

export default function WaiterPerformance({
  data = [],
  loading,
  onDateRangeChange
}: WaiterPerformanceProps) {
  // State variables
  const [searchTerm, setSearchTerm] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('orders');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [chartMetric, setChartMetric] = useState<ChartMetric>('orders');
  const [viewMode, setViewMode] = useState<'table' | 'chart'>('table');
  
  // Date Range state
  const [datePreset, setDatePreset] = useState<string>('all');
  const [customRange, setCustomRange] = useState({ start: '', end: '' });
  const [showDatePicker, setShowDatePicker] = useState(false);

  // Helper for generating dynamic initials & colors for avatars
  const getAvatarDetails = (name: string) => {
    const colors = [
      'bg-indigo-50 text-indigo-600 border-indigo-100/80',
      'bg-emerald-50 text-emerald-600 border-emerald-100/80',
      'bg-amber-50 text-amber-600 border-amber-100/80',
      'bg-rose-50 text-rose-600 border-rose-100/80',
      'bg-sky-50 text-sky-600 border-sky-100/80',
      'bg-purple-50 text-purple-600 border-purple-100/80'
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const initials = name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
    const styleClass = colors[Math.abs(hash) % colors.length];
    return { initials, styleClass };
  };

  // Badge configuration for Avg Time (min)
  const getAvgTimeBadge = (time: number) => {
    if (time < 10) {
      return {
        label: 'Fast',
        classes: 'bg-emerald-50 text-emerald-700 border-emerald-200/60'
      };
    } else if (time <= 20) {
      return {
        label: 'Average',
        classes: 'bg-amber-50 text-amber-700 border-amber-200/60'
      };
    } else {
      return {
        label: 'Slow',
        classes: 'bg-orange-50 text-orange-700 border-orange-200/60'
      };
    }
  };

  // CSV Export handler
  const handleExportCSV = () => {
    if (!data || data.length === 0) return;
    
    const headers = [
      'Waiter Name',
      'Orders Served',
      'Avg Time (min)',
      'Total Revenue (KES)',
      'Avg Ticket (KES)',
      'Rating',
      'Tables Served'
    ];

    const rows = sortedAndFilteredData.map((w) => [
      w.name,
      w.orders,
      w.avgTime.toFixed(1),
      w.revenue,
      w.avgTicket.toFixed(1),
      w.rating.toFixed(1),
      w.tablesServed
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `waiter_performance_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Print Report handler
  const handlePrint = () => {
    window.print();
  };

  // Sorting columns handler
  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortOrder(key === 'name' ? 'asc' : 'desc');
    }
  };

  // Handle Preset Date Range updates
  const handleDatePresetChange = (preset: string) => {
    setDatePreset(preset);
    if (preset !== 'custom') {
      setShowDatePicker(false);
      onDateRangeChange?.(null);
    } else {
      setShowDatePicker(true);
    }
  };

  // Submit custom date filter
  const handleCustomRangeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customRange.start && customRange.end) {
      setShowDatePicker(false);
      onDateRangeChange?.(customRange);
    }
  };

  // Process data (Search filter & Column sorting)
  const sortedAndFilteredData = useMemo(() => {
    let result = [...data];

    // Search filter
    if (searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      result = result.filter(item => item.name.toLowerCase().includes(term));
    }

    // Sorting
    result.sort((a, b) => {
      let valA = a[sortKey];
      let valB = b[sortKey];

      if (typeof valA === 'string' && typeof valB === 'string') {
        return sortOrder === 'asc' 
          ? valA.localeCompare(valB) 
          : valB.localeCompare(valA);
      }

      // Numeric comparison
      valA = valA as number;
      valB = valB as number;
      return sortOrder === 'asc' ? valA - valB : valB - valA;
    });

    return result;
  }, [data, searchTerm, sortKey, sortOrder]);

  // Calculate Leaderboard Metrics
  const leaderBoard = useMemo(() => {
    if (!data || data.length === 0) return null;

    const topOrders = [...data].sort((a, b) => b.orders - a.orders)[0];
    const topRevenue = [...data].sort((a, b) => b.revenue - a.revenue)[0];
    const topRating = [...data].sort((a, b) => b.rating !== a.rating ? b.rating - a.rating : b.orders - a.orders)[0];

    return {
      orders: topOrders,
      revenue: topRevenue,
      rating: topRating
    };
  }, [data]);

  // Custom tooltips for Chart
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const itemData = payload[0].payload as WaiterPerformanceData;
      return (
        <div className="bg-white/95 backdrop-blur-md p-4 border border-gray-100 shadow-2xl rounded-2xl text-xs space-y-1.5 min-w-[220px]">
          <p className="font-bold text-gray-900 border-b border-gray-100 pb-1 mb-1.5 flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${chartMetric === 'orders' ? 'bg-emerald-500' : 'bg-indigo-500'}`}></span>
            {itemData.name}
          </p>
          <div className="flex justify-between items-center text-gray-600">
            <span>Orders Served:</span>
            <span className="font-semibold text-gray-950">{itemData.orders.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center text-gray-600">
            <span>Avg Served Time:</span>
            <span className="font-semibold text-gray-950">{itemData.avgTime.toFixed(1)} mins</span>
          </div>
          <div className="flex justify-between items-center text-gray-600">
            <span>Total Revenue:</span>
            <span className="font-semibold text-emerald-600">KES {itemData.revenue.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center text-gray-600">
            <span>Avg Ticket:</span>
            <span className="font-semibold text-indigo-600">KES {itemData.avgTicket.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center text-gray-600">
            <span>Rating:</span>
            <span className="font-semibold text-amber-500">★ {itemData.rating.toFixed(1)}</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* LEADERBOARD SECTION */}
      {!loading && leaderBoard && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 print:hidden">
          {/* Card 1: Top Orders */}
          <div className="bg-gradient-to-br from-emerald-50 to-white border border-emerald-100 rounded-xl shadow-sm p-4 relative overflow-hidden transition-all duration-300 hover:shadow-md hover:scale-[1.01]">
            <div className="absolute right-3 top-3 text-2xl animate-bounce">🥇</div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-emerald-100 rounded-xl text-emerald-700">
                <Coffee className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-semibold text-emerald-800/80 uppercase tracking-wider">Most Active Waiter</p>
                <h4 className="text-base font-bold text-gray-900 mt-0.5">{leaderBoard.orders.name}</h4>
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-gray-900">{leaderBoard.orders.orders}</span>
              <span className="text-xs text-gray-500 font-medium">orders served</span>
            </div>
            <div className="mt-2 text-xs text-emerald-700 font-semibold flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" />
              Leader in high volume service
            </div>
          </div>

          {/* Card 2: Top Revenue */}
          <div className="bg-gradient-to-br from-indigo-50 to-white border border-indigo-100 rounded-xl shadow-sm p-4 relative overflow-hidden transition-all duration-300 hover:shadow-md hover:scale-[1.01]">
            <div className="absolute right-3 top-3 text-2xl">🥈</div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-indigo-100 rounded-xl text-indigo-700">
                <TrendingUp className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-semibold text-indigo-800/80 uppercase tracking-wider">Top Earner</p>
                <h4 className="text-base font-bold text-gray-900 mt-0.5">{leaderBoard.revenue.name}</h4>
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="text-2xl font-extrabold text-gray-900">KES {leaderBoard.revenue.revenue.toLocaleString()}</span>
            </div>
            <div className="mt-3.5 text-xs text-indigo-700 font-semibold flex items-center gap-1">
              <Award className="w-3.5 h-3.5" />
              Highest order volume value generated
            </div>
          </div>

          {/* Card 3: Top Rating */}
          <div className="bg-gradient-to-br from-amber-50 to-white border border-amber-100 rounded-xl shadow-sm p-4 relative overflow-hidden transition-all duration-300 hover:shadow-md hover:scale-[1.01]">
            <div className="absolute right-3 top-3 text-2xl">🥉</div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-amber-100 rounded-xl text-amber-700">
                <Star className="w-5 h-5 fill-amber-400 text-amber-500" />
              </div>
              <div>
                <p className="text-xs font-semibold text-amber-800/80 uppercase tracking-wider">Guest Favorite</p>
                <h4 className="text-base font-bold text-gray-900 mt-0.5">{leaderBoard.rating.name}</h4>
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-gray-900">{leaderBoard.rating.rating.toFixed(1)}</span>
              <span className="text-xs text-gray-500 font-medium">/ 5.0 Rating</span>
            </div>
            <div className="mt-2 text-xs text-amber-700 font-semibold flex items-center gap-1">
              <Award className="w-3.5 h-3.5" />
              Outstanding hospitality performance
            </div>
          </div>
        </div>
      )}

      {/* FILTER & CONTROL BAR */}
      <div className="bg-white border border-gray-100 rounded-xl shadow-sm p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 print:hidden">
        {/* Search */}
        <div className="relative flex-1 max-w-sm">
          <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-gray-400" />
          </span>
          <input
            type="text"
            placeholder="Search waiter name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full text-xs pl-9 pr-4 py-2 border border-gray-200 rounded-lg bg-gray-50/50 text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
          />
        </div>

        {/* Date Filter & View toggle */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Preset Date range */}
          <div className="relative">
            <button
              onClick={() => setShowDatePicker(!showDatePicker)}
              className="flex items-center gap-2 px-3 py-1.5 border border-gray-200 rounded-lg text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 shadow-sm transition"
            >
              <Calendar className="w-3.5 h-3.5 text-gray-400" />
              <span>
                {datePreset === 'all' && 'All Time'}
                {datePreset === 'today' && 'Today'}
                {datePreset === 'week' && 'This Week'}
                {datePreset === 'month' && 'This Month'}
                {datePreset === 'custom' && (customRange.start && customRange.end ? `${customRange.start} - ${customRange.end}` : 'Custom Range')}
              </span>
              <ChevronDown className="w-3 h-3 text-gray-400" />
            </button>

            {showDatePicker && (
              <div className="absolute right-0 mt-2 w-64 bg-white border border-gray-100 rounded-xl shadow-xl p-4 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                <div className="space-y-3">
                  <div className="text-xs font-bold text-gray-900 border-b border-gray-50 pb-2">Select Range</div>
                  <div className="grid grid-cols-1 gap-1">
                    {[
                      { key: 'all', label: 'All Time' },
                      { key: 'today', label: 'Today' },
                      { key: 'week', label: 'This Week' },
                      { key: 'month', label: 'This Month' },
                      { key: 'custom', label: 'Custom Range' }
                    ].map((preset) => (
                      <button
                        key={preset.key}
                        onClick={() => handleDatePresetChange(preset.key)}
                        className={`text-left px-2.5 py-1.5 rounded-lg text-xs transition ${
                          datePreset === preset.key 
                            ? 'bg-emerald-50 text-emerald-700 font-semibold' 
                            : 'text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>

                  {datePreset === 'custom' && (
                    <form onSubmit={handleCustomRangeSubmit} className="space-y-2.5 pt-2 border-t border-gray-50">
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-gray-400 uppercase">Start</label>
                        <input
                          type="date"
                          value={customRange.start}
                          onChange={(e) => setCustomRange(prev => ({ ...prev, start: e.target.value }))}
                          required
                          className="w-full text-xs p-1.5 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-emerald-500"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-gray-400 uppercase">End</label>
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
                        Apply Filter
                      </button>
                    </form>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Toggle chart vs table view */}
          <div className="flex items-center border border-gray-200 rounded-lg p-0.5 shadow-sm bg-gray-50">
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-md transition ${viewMode === 'table' ? 'bg-white text-emerald-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
              title="Table view"
            >
              <LayoutList className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('chart')}
              className={`p-1.5 rounded-md transition ${viewMode === 'chart' ? 'bg-white text-emerald-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
              title="Chart view"
            >
              <BarChart3 className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleExportCSV}
              disabled={loading || data.length === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 rounded-lg text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              title="Export report data to CSV"
            >
              <Download className="w-3.5 h-3.5 text-gray-500" />
              <span className="hidden sm:inline">Export CSV</span>
            </button>

            <button
              onClick={handlePrint}
              disabled={loading || data.length === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 rounded-lg text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              title="Print Waiter Performance Report"
            >
              <Printer className="w-3.5 h-3.5 text-gray-500" />
              <span className="hidden sm:inline">Print Report</span>
            </button>
          </div>
        </div>
      </div>

      {/* PERFORMANCE TABLE & CHART VIEW CARD */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col min-h-[460px] relative">
        {/* Loading Spinner */}
        {loading && (
          <div className="absolute inset-0 bg-white/70 z-10 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
            <p className="text-xs font-medium text-gray-500 animate-pulse">Loading waiter analytics...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && sortedAndFilteredData.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center min-h-[400px]">
            <AlertCircle className="w-12 h-12 text-gray-300 mb-3" />
            <p className="text-sm font-bold text-gray-700">No Waiter Data Found</p>
            <p className="text-xs text-gray-400 mt-1 max-w-sm">No waiters matched your filter or search query. Try modifying your filters or entering a different search term.</p>
          </div>
        )}

        {/* Dynamic content rendering */}
        {!loading && sortedAndFilteredData.length > 0 && (
          <>
            {/* VIEW MODE: TABLE */}
            {viewMode === 'table' && (
              <div className="overflow-x-auto w-full">
                <table className="min-w-full divide-y divide-gray-100 text-left">
                  <thead>
                    <tr className="bg-gray-50/70 border-b border-gray-100">
                      {/* Column Waiter */}
                      <th
                        onClick={() => handleSort('name')}
                        className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100/50 transition-all select-none"
                      >
                        <div className="flex items-center gap-1">
                          <span>Waiter</span>
                          <ArrowUpDown className="w-3.5 h-3.5 text-gray-400/80" />
                        </div>
                      </th>
                      {/* Column Orders */}
                      <th
                        onClick={() => handleSort('orders')}
                        className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100/50 transition-all select-none"
                      >
                        <div className="flex items-center justify-end gap-1">
                          <span>Orders Served</span>
                          <ArrowUpDown className="w-3.5 h-3.5 text-gray-400/80" />
                        </div>
                      </th>
                      {/* Column Avg Time */}
                      <th
                        onClick={() => handleSort('avgTime')}
                        className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100/50 transition-all select-none"
                      >
                        <div className="flex items-center justify-end gap-1">
                          <span>Avg Time (min)</span>
                          <ArrowUpDown className="w-3.5 h-3.5 text-gray-400/80" />
                        </div>
                      </th>
                      {/* Column Total Revenue */}
                      <th
                        onClick={() => handleSort('revenue')}
                        className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100/50 transition-all select-none"
                      >
                        <div className="flex items-center justify-end gap-1">
                          <span>Total Revenue</span>
                          <ArrowUpDown className="w-3.5 h-3.5 text-gray-400/80" />
                        </div>
                      </th>
                      {/* Column Avg Ticket */}
                      <th
                        onClick={() => handleSort('avgTicket')}
                        className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100/50 transition-all select-none"
                      >
                        <div className="flex items-center justify-end gap-1">
                          <span>Avg Ticket</span>
                          <ArrowUpDown className="w-3.5 h-3.5 text-gray-400/80" />
                        </div>
                      </th>
                      {/* Column Rating */}
                      <th
                        onClick={() => handleSort('rating')}
                        className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100/50 transition-all select-none"
                      >
                        <div className="flex items-center justify-center gap-1">
                          <span>Rating</span>
                          <ArrowUpDown className="w-3.5 h-3.5 text-gray-400/80" />
                        </div>
                      </th>
                      {/* Column Tables Served */}
                      <th
                        onClick={() => handleSort('tablesServed')}
                        className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100/50 transition-all select-none"
                      >
                        <div className="flex items-center justify-end gap-1">
                          <span>Tables Served</span>
                          <ArrowUpDown className="w-3.5 h-3.5 text-gray-400/80" />
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-xs text-gray-700 bg-white">
                    {sortedAndFilteredData.map((waiter, index) => {
                      const { initials, styleClass } = getAvatarDetails(waiter.name);
                      const timeBadge = getAvgTimeBadge(waiter.avgTime);

                      return (
                        <tr
                          key={waiter.id}
                          className={`hover:bg-emerald-50/10 transition-all duration-150 group ${
                            index % 2 === 0 ? 'bg-white' : 'bg-gray-50/20'
                          }`}
                        >
                          {/* Waiter Details Column */}
                          <td className="px-6 py-4 font-semibold text-gray-900 whitespace-nowrap">
                            <div className="flex items-center gap-3">
                              <div
                                className={`w-8 h-8 rounded-full border flex items-center justify-center text-xs font-bold ${styleClass} shadow-sm`}
                              >
                                {initials}
                              </div>
                              <span className="group-hover:text-emerald-600 transition-colors">
                                {waiter.name}
                              </span>
                            </div>
                          </td>

                          {/* Orders Served Column */}
                          <td className="px-6 py-4 text-right font-medium whitespace-nowrap">
                            {waiter.orders.toLocaleString()}
                          </td>

                          {/* Avg Time (min) Column */}
                          <td className="px-6 py-4 text-right whitespace-nowrap">
                            <div className="flex items-center justify-end gap-2">
                              <span className="font-semibold text-gray-900">
                                {waiter.avgTime.toFixed(1)}m
                              </span>
                              <span
                                className={`inline-flex px-1.5 py-0.5 rounded-full text-[9px] font-extrabold border uppercase tracking-wider shadow-2xs ${timeBadge.classes}`}
                              >
                                {timeBadge.label}
                              </span>
                            </div>
                          </td>

                          {/* Total Revenue Column */}
                          <td className="px-6 py-4 text-right font-bold text-gray-950 whitespace-nowrap">
                            KES {waiter.revenue.toLocaleString()}
                          </td>

                          {/* Avg Ticket Column */}
                          <td className="px-6 py-4 text-right font-semibold text-gray-800 whitespace-nowrap">
                            KES {waiter.avgTicket.toLocaleString()}
                          </td>

                          {/* Rating Column */}
                          <td className="px-6 py-4 text-center whitespace-nowrap">
                            <div
                              className="inline-flex items-center gap-0.5 cursor-help"
                              title={`Rating: ${waiter.rating.toFixed(2)} out of 5 stars`}
                            >
                              {Array.from({ length: 5 }).map((_, idx) => {
                                const starVal = idx + 1;
                                const isFilled = waiter.rating >= starVal;
                                return (
                                  <span
                                    key={idx}
                                    className={`text-sm ${
                                      isFilled ? 'text-amber-400' : 'text-gray-200'
                                    }`}
                                  >
                                    ★
                                  </span>
                                );
                              })}
                              <span className="ml-1 text-[10px] text-gray-400 font-bold bg-gray-50 border border-gray-100 rounded px-1 group-hover:bg-white group-hover:border-gray-200 transition-all">
                                {waiter.rating.toFixed(1)}
                              </span>
                            </div>
                          </td>

                          {/* Tables Served Column */}
                          <td className="px-6 py-4 text-right font-semibold text-gray-600 whitespace-nowrap">
                            {waiter.tablesServed.toLocaleString()}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* VIEW MODE: CHART */}
            {viewMode === 'chart' && (
              <div className="flex-1 flex flex-col p-6 min-h-[400px]">
                {/* Metric Selector toggle inside chart */}
                <div className="flex justify-between items-center mb-5 border-b border-gray-50 pb-4">
                  <div>
                    <h4 className="text-sm font-bold text-gray-900">Waiter Comparison</h4>
                    <p className="text-[10px] text-gray-500">Visualizing comparative performance metrics</p>
                  </div>
                  <div className="flex items-center border border-gray-200 rounded-lg p-0.5 shadow-sm bg-gray-50 text-xs font-bold text-gray-700">
                    <button
                      onClick={() => setChartMetric('orders')}
                      className={`px-3 py-1 rounded-md transition-all ${
                        chartMetric === 'orders' ? 'bg-white text-emerald-600 shadow-xs' : 'hover:text-gray-900'
                      }`}
                    >
                      Orders Served
                    </button>
                    <button
                      onClick={() => setChartMetric('revenue')}
                      className={`px-3 py-1 rounded-md transition-all ${
                        chartMetric === 'revenue' ? 'bg-white text-indigo-600 shadow-xs' : 'hover:text-gray-900'
                      }`}
                    >
                      Total Revenue
                    </button>
                  </div>
                </div>

                {/* Recharts Bar Chart */}
                <div className="flex-1 w-full h-[360px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      layout="vertical"
                      data={sortedAndFilteredData}
                      margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={true} vertical={false} />
                      <XAxis
                        type="number"
                        tickLine={false}
                        axisLine={false}
                        stroke="#9ca3af"
                        fontSize={10}
                        tickFormatter={(value) => chartMetric === 'revenue' ? `KES ${value.toLocaleString()}` : value}
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
                      <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f8fafc' }} />
                      <Bar
                        dataKey={chartMetric}
                        radius={[0, 6, 6, 0]}
                        maxBarSize={28}
                        cursor="pointer"
                      >
                        {sortedAndFilteredData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={chartMetric === 'orders' ? '#10b981' : '#6366f1'}
                            className="transition-all duration-200 hover:opacity-85"
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </>
        )}

        {/* BOTTOM METADATA BAR */}
        <div className="mt-auto px-6 py-4 border-t border-gray-50 bg-gray-50/50 flex flex-col sm:flex-row justify-between items-center gap-2">
          <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider">
            PlateLink Africa Performance Hub
          </p>
          <p className="text-[10px] text-gray-500 font-medium">
            Total active waiters evaluated: <span className="font-bold text-gray-800">{data.length}</span>
          </p>
        </div>
      </div>

      {/* PRINT-ONLY HEADER AND TAIL */}
      <style jsx global>{`
        @media print {
          body {
            background: white !important;
            color: black !important;
          }
          .print\\:hidden {
            display: none !important;
          }
          /* Ensure table does not split or overflow in printing */
          table {
            page-break-inside: auto;
          }
          tr {
            page-break-inside: avoid;
            page-break-after: auto;
          }
        }
      `}</style>
    </div>
  );
}

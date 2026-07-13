// apps/admin/components/Analytics/PeakHoursHeatmap.tsx
'use client';

import React, { useState, useMemo, useRef } from 'react';
import { 
  Download, 
  Clock, 
  Calendar, 
  TrendingUp, 
  TrendingDown, 
  SlidersHorizontal,
  ChevronRight
} from 'lucide-react';

export interface HeatmapItem {
  day: string;
  hour: number;
  orders: number;
  revenue: number;
}

interface PeakHoursHeatmapProps {
  data: HeatmapItem[];
  loading: boolean;
}

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const HOURS = Array.from({ length: 16 }, (_, i) => i + 8); // 8 AM to 11 PM (8 to 23)

const normalizeDay = (d: string): string => {
  const lower = d.toLowerCase();
  if (lower.startsWith('mon')) return 'Monday';
  if (lower.startsWith('tue')) return 'Tuesday';
  if (lower.startsWith('wed')) return 'Wednesday';
  if (lower.startsWith('thu')) return 'Thursday';
  if (lower.startsWith('fri')) return 'Friday';
  if (lower.startsWith('sat')) return 'Saturday';
  if (lower.startsWith('sun')) return 'Sunday';
  return d;
};

const formatHour = (h: number): string => {
  if (h === 12) return '12 PM';
  if (h === 0 || h === 24) return '12 AM';
  return h > 12 ? `${h - 12} PM` : `${h} AM`;
};

const formatCompact = (val: number): string => {
  if (val >= 1000000) return `KES ${(val / 1000000).toFixed(1)}M`;
  if (val >= 1000) return `KES ${(val / 1000).toFixed(1)}k`;
  return `KES ${val}`;
};

export default function PeakHoursHeatmap({ data = [], loading }: PeakHoursHeatmapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Controls state
  const [activeMetric, setActiveMetric] = useState<'orders' | 'revenue'>('orders');
  const [dayGrouping, setDayGrouping] = useState<'all' | 'weekday' | 'weekend'>('all');
  const [startHour, setStartHour] = useState<number>(8);
  const [endHour, setEndHour] = useState<number>(23);
  
  // Tooltip state
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    day: string;
    hour: number;
    orders: number;
    revenue: number;
    percentage: number;
    x: number;
    y: number;
  } | null>(null);

  // 1. Build comprehensive grid data (pre-populating all days & hours)
  const gridData = useMemo(() => {
    const grid: Record<string, Record<number, { orders: number; revenue: number }>> = {};
    
    DAYS.forEach(day => {
      grid[day] = {};
      HOURS.forEach(hour => {
        grid[day][hour] = { orders: 0, revenue: 0 };
      });
    });

    if (data && data.length > 0) {
      data.forEach(item => {
        const normalizedDay = normalizeDay(item.day);
        if (grid[normalizedDay] && grid[normalizedDay][item.hour] !== undefined) {
          grid[normalizedDay][item.hour].orders += item.orders;
          grid[normalizedDay][item.hour].revenue += item.revenue;
        }
      });
    }

    return grid;
  }, [data]);

  // 2. Filter days based on Weekday vs Weekend toggle
  const visibleDays = useMemo(() => {
    if (dayGrouping === 'weekday') {
      return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    }
    if (dayGrouping === 'weekend') {
      return ['Saturday', 'Sunday'];
    }
    return DAYS;
  }, [dayGrouping]);

  // 3. Filter hours based on time range select
  const visibleHours = useMemo(() => {
    return HOURS.filter(h => h >= startHour && h <= endHour);
  }, [startHour, endHour]);

  // 4. Calculate daily totals for the percentage calculation
  const dailyTotals = useMemo(() => {
    const totals: Record<string, number> = {};
    DAYS.forEach(day => {
      let total = 0;
      HOURS.forEach(hour => {
        total += gridData[day][hour][activeMetric];
      });
      totals[day] = total;
    });
    return totals;
  }, [gridData, activeMetric]);

  // 5. Calculate visible Min/Max values to dynamically scale visual intensity
  const { minVal, maxVal } = useMemo(() => {
    let min = Infinity;
    let max = -Infinity;
    
    visibleDays.forEach(day => {
      visibleHours.forEach(hour => {
        const val = gridData[day][hour][activeMetric];
        if (val < min) min = val;
        if (val > max) max = val;
      });
    });

    if (min === Infinity) min = 0;
    if (max === -Infinity) max = 0;
    if (min === max) {
      min = 0;
      max = max || 1;
    }

    return { minVal: min, maxVal: max };
  }, [gridData, visibleDays, visibleHours, activeMetric]);

  // 6. Global insights calculation on overall data
  const insights = useMemo(() => {
    let peakHour = { day: 'N/A', hour: 0, orders: 0, revenue: 0 };
    let quietestHour = { day: 'N/A', hour: 0, orders: Infinity, revenue: Infinity };
    
    const daySums: Record<string, { orders: number; revenue: number }> = {};
    DAYS.forEach(day => {
      daySums[day] = { orders: 0, revenue: 0 };
    });

    if (data && data.length > 0) {
      data.forEach(item => {
        const normalizedDay = normalizeDay(item.day);
        
        if (item.orders > peakHour.orders) {
          peakHour = { day: normalizedDay, hour: item.hour, orders: item.orders, revenue: item.revenue };
        }
        
        if (item.orders < quietestHour.orders && item.orders > 0) {
          quietestHour = { day: normalizedDay, hour: item.hour, orders: item.orders, revenue: item.revenue };
        }
        
        if (daySums[normalizedDay]) {
          daySums[normalizedDay].orders += item.orders;
          daySums[normalizedDay].revenue += item.revenue;
        }
      });
    }

    // Fallback if no positive values found for quietest
    if (quietestHour.orders === Infinity) {
      quietestHour = { day: 'N/A', hour: 0, orders: 0, revenue: 0 };
      if (data && data.length > 0) {
        let absoluteMin = data[0];
        data.forEach(item => {
          if (item.orders < absoluteMin.orders) {
            absoluteMin = item;
          }
        });
        quietestHour = {
          day: normalizeDay(absoluteMin.day),
          hour: absoluteMin.hour,
          orders: absoluteMin.orders,
          revenue: absoluteMin.revenue
        };
      }
    }

    let busiestDay = { day: 'N/A', orders: 0 };
    DAYS.forEach(day => {
      if (daySums[day] && daySums[day].orders > busiestDay.orders) {
        busiestDay = { day, orders: daySums[day].orders };
      }
    });

    return { peakHour, busiestDay, quietestHour };
  }, [data]);

  // Color interpolation helpers
  const getCellStyles = (val: number) => {
    if (maxVal === minVal) return { backgroundColor: 'rgb(254, 245, 231)', color: '#111827' };
    const ratio = (val - minVal) / (maxVal - minVal);
    
    // Light Yellow (HSL 48, 100%, 96%) to Warm Orange (HSL 24, 100%, 70%) to Bold Red (HSL 0, 100%, 45%)
    const h = Math.round(48 - ratio * 48);
    const s = 100;
    const l = Math.round(96 - ratio * 51);
    
    const bgColor = `hsl(${h}, ${s}%, ${l}%)`;
    // Text contrast adjustment based on lightness
    const textColor = l < 65 ? '#ffffff' : '#111827';
    
    return {
      backgroundColor: bgColor,
      color: textColor,
    };
  };

  const handleMouseEnter = (
    e: React.MouseEvent<HTMLTableCellElement>,
    day: string,
    hour: number,
    orders: number,
    revenue: number
  ) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const parentRect = containerRef.current?.getBoundingClientRect() || { left: 0, top: 0 };
    
    const val = activeMetric === 'orders' ? orders : revenue;
    const dayTotal = dailyTotals[day] || 0;
    const percentage = dayTotal > 0 ? (val / dayTotal) * 100 : 0;

    setTooltip({
      visible: true,
      day,
      hour,
      orders,
      revenue,
      percentage,
      x: rect.left - parentRect.left + rect.width / 2,
      y: rect.top - parentRect.top - 8
    });
  };

  const handleExportCSV = () => {
    if (!data || data.length === 0) return;
    
    const headers = ['Day', 'Hour', 'Orders', 'Revenue (KES)'];
    
    const escapeCSV = (val: string | number) => {
      const str = String(val);
      if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    };

    const csvRows = [
      headers.map(escapeCSV).join(','),
      ...data.map(item => [
        normalizeDay(item.day),
        formatHour(item.hour),
        item.orders,
        item.revenue
      ].map(escapeCSV).join(','))
    ];
    
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `peak_hours_heatmap_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Adjust hours dynamically so start is always less than end
  const handleStartHourChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newStart = parseInt(e.target.value, 10);
    setStartHour(newStart);
    if (newStart >= endHour) {
      setEndHour(Math.min(newStart + 1, 23));
    }
  };

  const handleEndHourChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newEnd = parseInt(e.target.value, 10);
    setEndHour(newEnd);
    if (newEnd <= startHour) {
      setStartHour(Math.max(newEnd - 1, 8));
    }
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-100 rounded-xl shadow-sm p-4 md:p-6 animate-pulse space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-100 pb-4">
          <div className="space-y-2">
            <div className="h-6 bg-gray-200 rounded w-48"></div>
            <div className="h-4 bg-gray-100 rounded w-64"></div>
          </div>
          <div className="h-10 bg-gray-200 rounded-lg w-36"></div>
        </div>
        <div className="flex flex-wrap items-center gap-4 py-2 border-b border-gray-50">
          <div className="h-9 bg-gray-200 rounded-lg w-44"></div>
          <div className="h-9 bg-gray-200 rounded-lg w-48"></div>
          <div className="h-9 bg-gray-200 rounded-lg w-36"></div>
        </div>
        <div className="h-96 bg-gray-100 rounded-lg border border-gray-200 flex items-center justify-center">
          <div className="text-gray-400 font-medium">Analyzing dashboard peaks...</div>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className="bg-white border border-gray-100 rounded-xl shadow-sm p-4 md:p-6 relative space-y-6 select-none"
    >
      {/* 1. Header & Export Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-100 pb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
            <Clock className="w-5 h-5 text-orange-500" />
            Peak Hours Heatmap
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Identify your busiest dining hours, delivery peaks, and high-revenue periods
          </p>
        </div>
        <button
          onClick={handleExportCSV}
          className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 border border-gray-200 rounded-lg shadow-sm transition-all hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-500/20 active:scale-95"
        >
          <Download className="w-3.5 h-3.5 text-gray-500" />
          Export Heatmap Data
        </button>
      </div>

      {/* 2. Advanced Controls & Interactive Filters */}
      <div className="flex flex-wrap items-center gap-y-4 gap-x-6 py-2 border-b border-gray-50">
        
        {/* Metric Selector (Orders vs Revenue) */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Active Analysis Metric</span>
          <div className="bg-gray-100/80 p-0.5 rounded-lg flex items-center border border-gray-200/50">
            <button
              onClick={() => setActiveMetric('orders')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 ${
                activeMetric === 'orders'
                  ? 'bg-white text-gray-900 shadow-sm border border-gray-200/20'
                  : 'text-gray-500 hover:text-gray-900'
              }`}
            >
              Order Count
            </button>
            <button
              onClick={() => setActiveMetric('revenue')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 ${
                activeMetric === 'revenue'
                  ? 'bg-white text-gray-900 shadow-sm border border-gray-200/20'
                  : 'text-gray-500 hover:text-gray-900'
              }`}
            >
              Revenue Amount
            </button>
          </div>
        </div>

        {/* Time Window Slicers */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Hour Window Filter</span>
          <div className="flex items-center gap-2 bg-gray-50 px-2 py-1 border border-gray-200 rounded-lg">
            <select
              value={startHour}
              onChange={handleStartHourChange}
              className="text-xs font-semibold text-gray-700 bg-transparent border-none focus:outline-none cursor-pointer pr-1"
            >
              {HOURS.slice(0, -1).map(h => (
                <option key={h} value={h}>{formatHour(h)}</option>
              ))}
            </select>
            <ChevronRight className="w-3 h-3 text-gray-400" />
            <select
              value={endHour}
              onChange={handleEndHourChange}
              className="text-xs font-semibold text-gray-700 bg-transparent border-none focus:outline-none cursor-pointer pr-1"
            >
              {HOURS.slice(1).map(h => (
                <option key={h} value={h}>{formatHour(h)}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Day Grouping Filters */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Day Segment filter</span>
          <div className="bg-gray-100/80 p-0.5 rounded-lg flex items-center border border-gray-200/50">
            {(['all', 'weekday', 'weekend'] as const).map(group => (
              <button
                key={group}
                onClick={() => setDayGrouping(group)}
                className={`px-3 py-1.5 text-xs font-semibold capitalize rounded-md transition-all duration-200 ${
                  dayGrouping === group
                    ? 'bg-white text-gray-900 shadow-sm border border-gray-200/20'
                    : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                {group === 'all' ? 'All Days' : group}
              </button>
            ))}
          </div>
        </div>

      </div>

      {/* 3. Heatmap Responsive Table Container */}
      <div className="overflow-x-auto rounded-xl border border-gray-100 bg-gray-50/50 p-1">
        <table className="w-full border-collapse border-spacing-0">
          <thead>
            <tr>
              <th className="sticky left-0 bg-white z-10 min-w-[100px] text-left p-3 text-xs font-bold text-gray-400 uppercase border-b border-r border-gray-100 shadow-[2px_0_5px_rgba(0,0,0,0.02)]">
                Day
              </th>
              {visibleHours.map(hour => (
                <th 
                  key={hour} 
                  className="min-w-[80px] text-center p-3 text-xs font-bold text-gray-500 uppercase border-b border-gray-100 tracking-wider whitespace-nowrap"
                >
                  {formatHour(hour)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleDays.map(day => (
              <tr key={day} className="hover:bg-gray-50/40 transition-colors">
                <td className="sticky left-0 bg-white z-10 min-w-[100px] text-left p-3 font-bold text-xs text-gray-800 border-r border-b border-gray-100 shadow-[2px_0_5px_rgba(0,0,0,0.02)]">
                  {day}
                </td>
                {visibleHours.map(hour => {
                  const cell = gridData[day][hour];
                  const primaryVal = activeMetric === 'orders' ? cell.orders : cell.revenue;
                  const secondaryVal = activeMetric === 'orders' ? cell.revenue : cell.orders;

                  const mainDisplay = activeMetric === 'orders' ? primaryVal : formatCompact(primaryVal);
                  const subDisplay = activeMetric === 'orders' ? formatCompact(secondaryVal) : `${secondaryVal} ord`;

                  return (
                    <td
                      key={hour}
                      onMouseEnter={(e) => handleMouseEnter(e, day, hour, cell.orders, cell.revenue)}
                      onMouseLeave={() => setTooltip(null)}
                      style={getCellStyles(primaryVal)}
                      className="min-w-[80px] text-center p-2 border-r border-b border-gray-100 transition-all duration-150 cursor-crosshair font-medium relative group"
                    >
                      <div className="font-bold text-sm tracking-tight">{mainDisplay}</div>
                      <div className="text-[10px] opacity-75 mt-0.5 tracking-tight font-medium">{subDisplay}</div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 4. Color Scale Legend */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-gray-50/70 p-3 rounded-lg border border-gray-100">
        <div className="flex items-center gap-2 text-xs font-semibold text-gray-600">
          <SlidersHorizontal className="w-3.5 h-3.5 text-gray-500" />
          Color Intensity Gradient
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider whitespace-nowrap">
            Low {activeMetric === 'orders' ? 'Volume' : 'Revenue'}
          </span>
          <div 
            className="h-3.5 w-44 rounded-full border border-gray-200"
            style={{
              background: 'linear-gradient(to right, hsl(48, 100%, 96%), hsl(36, 100%, 83%), hsl(24, 100%, 70%), hsl(12, 100%, 57%), hsl(0, 100%, 45%))'
            }}
          />
          <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider whitespace-nowrap">
            High Peak
          </span>
        </div>
      </div>

      {/* 5. Dynamic Insights Panel */}
      <div className="space-y-3 pt-4 border-t border-gray-100">
        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4 text-emerald-500" />
          Peak Hour Insights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          
          {/* Peak Hour Item */}
          <div className="bg-emerald-50/50 border border-emerald-100 rounded-xl p-4 flex items-start gap-3.5 hover:shadow-sm transition-all duration-300">
            <div className="p-2.5 bg-emerald-100 rounded-lg shrink-0">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider">Absolute Hourly Peak</p>
              <p className="text-sm font-bold text-emerald-950 mt-1">
                Peak hour: {formatHour(insights.peakHour.hour)} on {insights.peakHour.day} with {insights.peakHour.orders} orders
              </p>
            </div>
          </div>

          {/* Busiest Day Item */}
          <div className="bg-orange-50/50 border border-orange-100 rounded-xl p-4 flex items-start gap-3.5 hover:shadow-sm transition-all duration-300">
            <div className="p-2.5 bg-orange-100 rounded-lg shrink-0">
              <Calendar className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-[10px] font-bold text-orange-700 uppercase tracking-wider">Most Active Day</p>
              <p className="text-sm font-bold text-orange-950 mt-1">
                Busiest day: {insights.busiestDay.day} with {insights.busiestDay.orders} orders
              </p>
            </div>
          </div>

          {/* Quietest Hour Item */}
          <div className="bg-slate-50 border border-slate-200/60 rounded-xl p-4 flex items-start gap-3.5 hover:shadow-sm transition-all duration-300">
            <div className="p-2.5 bg-slate-200/60 rounded-lg shrink-0">
              <TrendingDown className="w-5 h-5 text-slate-600" />
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Lowest Activity Hour</p>
              <p className="text-sm font-bold text-slate-900 mt-1">
                Quietest hour: {formatHour(insights.quietestHour.hour)} on {insights.quietestHour.day} with {insights.quietestHour.orders} orders
              </p>
            </div>
          </div>

        </div>
      </div>

      {/* 6. Dynamic Absolute Tooltip */}
      {tooltip && tooltip.visible && (
        <div 
          className="absolute z-50 bg-gray-900 text-white rounded-xl shadow-xl p-3 w-52 pointer-events-none transition-all duration-100 ease-out border border-gray-800"
          style={{
            left: `${tooltip.x}px`,
            top: `${tooltip.y}px`,
            transform: 'translate(-50%, -100%)',
          }}
        >
          {/* Caret arrow down */}
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full w-0 h-0 border-x-[6px] border-x-transparent border-t-[6px] border-t-gray-900" />
          
          <div className="font-bold text-gray-200 border-b border-gray-800 pb-1.5 mb-2 text-xs flex justify-between">
            <span>{tooltip.day}</span>
            <span className="text-orange-400 font-semibold">{formatHour(tooltip.hour)}</span>
          </div>
          <div className="space-y-1.5 text-[11px]">
            <div className="flex justify-between">
              <span className="text-gray-400">Total Orders:</span>
              <span className="font-bold text-gray-100">{tooltip.orders}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Total Revenue:</span>
              <span className="font-bold text-emerald-400">KES {tooltip.revenue.toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-t border-gray-800 pt-1.5 mt-1 font-semibold">
              <span className="text-gray-400">% of Daily Total:</span>
              <span className="font-bold text-orange-400">{tooltip.percentage.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

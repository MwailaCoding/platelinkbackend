// apps/admin/components/Analytics/ExportReports.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  Download, 
  X, 
  Loader2, 
  Calendar, 
  FileSpreadsheet, 
  FileText, 
  CheckCircle, 
  AlertCircle,
  HelpCircle,
  TrendingUp,
  Settings
} from 'lucide-react';

export interface ExportOptions {
  reportType: 'sales' | 'popular_items' | 'waiter_performance' | 'inventory';
  dateRange: 'today' | 'week' | 'month' | 'last_30_days' | 'custom';
  startDate?: string;
  endDate?: string;
  includeCharts?: boolean;
  includeSummary?: boolean;
  groupBy?: 'day' | 'week' | 'month';
}

interface ExportReportsProps {
  onExport: (format: string, options: ExportOptions) => Promise<void>;
}

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

export default function ExportReports({ onExport }: ExportReportsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Form state
  const [reportType, setReportType] = useState<ExportOptions['reportType']>('sales');
  const [dateRange, setDateRange] = useState<ExportOptions['dateRange']>('last_30_days');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [format, setFormat] = useState<'csv' | 'pdf' | 'excel'>('csv');
  
  // Conditional Options state
  const [includeCharts, setIncludeCharts] = useState(true);
  const [includeSummary, setIncludeSummary] = useState(true);
  const [groupBy, setGroupBy] = useState<ExportOptions['groupBy']>('day');

  // Local Toasts state
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    const id = Math.random().toString();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  // Set default dates for custom picker
  useEffect(() => {
    if (!startDate || !endDate) {
      const today = new Date();
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(today.getDate() - 30);
      
      setStartDate(thirtyDaysAgo.toISOString().split('T')[0]);
      setEndDate(today.toISOString().split('T')[0]);
    }
  }, [startDate, endDate]);

  // Compute estimated rows and file size preview dynamically
  const previewData = React.useMemo(() => {
    let daysCount = 30;
    if (dateRange === 'today') daysCount = 1;
    else if (dateRange === 'week') daysCount = 7;
    else if (dateRange === 'month') daysCount = 30;
    else if (dateRange === 'last_30_days') daysCount = 30;
    else if (dateRange === 'custom' && startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);
      const diffTime = Math.abs(end.getTime() - start.getTime());
      daysCount = Math.max(1, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
    }

    let baseRowsPerDay = 45;
    let baseBytesPerRow = 120; // for CSV

    if (reportType === 'sales') {
      baseRowsPerDay = 55;
      baseBytesPerRow = 140;
    } else if (reportType === 'popular_items') {
      // Items list doesn't grow linearly with time, it caps out based on menu size
      return {
        rows: Math.min(180, 20 + daysCount * 2),
        sizeStr: format === 'pdf' ? '145 KB' : format === 'excel' ? '42 KB' : '15 KB'
      };
    } else if (reportType === 'waiter_performance') {
      // Waiter counts are static based on employee size
      return {
        rows: 12,
        sizeStr: format === 'pdf' ? '98 KB' : format === 'excel' ? '18 KB' : '3 KB'
      };
    } else if (reportType === 'inventory') {
      // Inventory reports have high row count but static
      return {
        rows: 245,
        sizeStr: format === 'pdf' ? '280 KB' : format === 'excel' ? '95 KB' : '32 KB'
      };
    }

    const estimatedRows = baseRowsPerDay * daysCount;
    let sizeInBytes = estimatedRows * baseBytesPerRow;

    if (format === 'pdf') {
      // PDFs have heavy wrapper size, fonts, layout, and optionals
      sizeInBytes = 85000 + (estimatedRows * 80);
      if (includeCharts) sizeInBytes += 180000; // extra bytes for charts image data
      if (includeSummary) sizeInBytes += 15000;
    } else if (format === 'excel') {
      // Excel xlsx uses compressed xml structure
      sizeInBytes = 25000 + (estimatedRows * 35);
    }

    let sizeStr = '';
    if (sizeInBytes < 1024) {
      sizeStr = `${sizeInBytes} B`;
    } else if (sizeInBytes < 1024 * 1024) {
      sizeStr = `${(sizeInBytes / 1024).toFixed(1)} KB`;
    } else {
      sizeStr = `${(sizeInBytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    return {
      rows: estimatedRows,
      sizeStr
    };
  }, [reportType, dateRange, startDate, endDate, format, includeCharts, includeSummary]);

  const handleExportSubmit = async () => {
    setLoading(true);
    try {
      const options: ExportOptions = {
        reportType,
        dateRange,
        format,
        ...(dateRange === 'custom' ? { startDate, endDate } : {}),
        ...(format === 'pdf' ? { includeCharts, includeSummary } : {}),
        ...(reportType === 'sales' ? { groupBy } : {}),
      };

      // 1. Build Query Parameters
      const queryParams = new URLSearchParams();
      queryParams.append('reportType', reportType);
      queryParams.append('format', format);
      queryParams.append('dateRange', dateRange);

      if (dateRange === 'custom') {
        if (startDate) queryParams.append('startDate', startDate);
        if (endDate) queryParams.append('endDate', endDate);
      }

      if (format === 'pdf') {
        queryParams.append('includeCharts', String(includeCharts));
        queryParams.append('includeSummary', String(includeSummary));
      }

      if (reportType === 'sales' && groupBy) {
        queryParams.append('groupBy', groupBy);
      }

      // 2. Call GET /api/analytics/export
      const url = `/api/analytics/export?${queryParams.toString()}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText || 'Server Error'}`);
      }

      // Determine Content Type
      let mimeType = 'text/csv';
      let fileExtension = 'csv';

      if (format === 'pdf') {
        mimeType = 'application/pdf';
        fileExtension = 'pdf';
      } else if (format === 'excel') {
        mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
        fileExtension = 'xlsx';
      }

      // 3. Download File
      const blob = await response.blob();
      const downloadBlob = new Blob([blob], { type: mimeType });
      const downloadUrl = window.URL.createObjectURL(downloadBlob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      const fileName = `PlateLink_${reportType}_Report_${new Date().toISOString().split('T')[0]}.${fileExtension}`;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      
      link.click();
      
      // Clean up
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      // 4. Trigger Prop callback
      await onExport(format, options);

      // 5. Toast success
      showToast(`${reportType.replace('_', ' ')} exported successfully as ${format.toUpperCase()}`, 'success');
      
      // Close modal
      setTimeout(() => {
        setIsOpen(false);
      }, 500);

    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Error occurred while exporting report', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Toast notifications container */}
      <div className="fixed top-6 right-6 z-[100] flex flex-col gap-3 max-w-md w-full">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`p-4 rounded-xl shadow-xl border flex items-start gap-3 transition-all duration-300 transform translate-x-0 bg-white ${
              t.type === 'success'
                ? 'border-emerald-200 text-emerald-950 bg-emerald-50/30'
                : t.type === 'error'
                ? 'border-rose-200 text-rose-950 bg-rose-50/30'
                : 'border-blue-200 text-blue-950 bg-blue-50/30'
            }`}
          >
            {t.type === 'success' && <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />}
            {t.type === 'error' && <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />}
            {t.type === 'info' && <HelpCircle className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />}
            <div className="flex-1 text-sm font-semibold">{t.message}</div>
            <button
              onClick={() => setToasts((prev) => prev.filter((item) => item.id !== t.id))}
              className="text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      {/* TRIGGER BUTTON */}
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 rounded-xl shadow-md transition-all duration-150 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
      >
        <Download className="w-4.5 h-4.5 stroke-[2.5]" />
        Export
      </button>

      {/* EXPORT MODAL OVERLAY */}
      {isOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 transition-all duration-300 animate-fadeIn">
          {/* Modal Container */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-2xl max-w-xl w-full max-h-[90vh] overflow-y-auto overflow-x-hidden flex flex-col scale-100 transition-transform">
            
            {/* Header */}
            <div className="flex justify-between items-center px-6 py-5 border-b border-gray-100 shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-emerald-50 text-emerald-700 rounded-xl border border-emerald-100">
                  <Download className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-extrabold text-gray-900">Export Analytics Report</h3>
                  <p className="text-xs text-gray-500 font-semibold mt-0.5">Customize your export settings and download report</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-gray-450 hover:bg-gray-50 hover:text-gray-700 border border-transparent hover:border-gray-200 transition focus:outline-none"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body */}
            <div className="p-6 space-y-6 overflow-y-auto">
              
              {/* 1. REPORT TYPE SELECTION */}
              <div className="space-y-2.5">
                <label className="text-xs font-bold uppercase tracking-wider text-gray-550 flex items-center gap-1.5">
                  <Settings className="w-3.5 h-3.5 text-gray-400" />
                  Report Type
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { id: 'sales', label: 'Sales Report', desc: 'Revenue, orders & tickets' },
                    { id: 'popular_items', label: 'Popular Items', desc: 'Top selling menu choices' },
                    { id: 'waiter_performance', label: 'Waiter Performance', desc: 'Ratings, times & tips' },
                    { id: 'inventory', label: 'Inventory Report', desc: 'Stock alerts & levels' }
                  ].map((type) => {
                    const isSelected = reportType === type.id;
                    return (
                      <button
                        key={type.id}
                        type="button"
                        onClick={() => setReportType(type.id as any)}
                        className={`text-left p-3.5 rounded-xl border text-sm transition-all flex flex-col ${
                          isSelected
                            ? 'bg-emerald-50/50 border-emerald-500 text-emerald-950 ring-2 ring-emerald-500/10'
                            : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50/60'
                        }`}
                      >
                        <span className="font-extrabold">{type.label}</span>
                        <span className="text-xxs text-gray-400 mt-1 font-semibold leading-relaxed">{type.desc}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 2. DATE RANGE SELECTION */}
              <div className="space-y-3">
                <label className="text-xs font-bold uppercase tracking-wider text-gray-550 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-gray-400" />
                  Date Range
                </label>
                <div className="flex flex-wrap gap-2">
                  {[
                    { id: 'today', label: 'Today' },
                    { id: 'week', label: 'This Week' },
                    { id: 'month', label: 'This Month' },
                    { id: 'last_30_days', label: 'Last 30 Days' },
                    { id: 'custom', label: 'Custom Range' }
                  ].map((preset) => {
                    const isSelected = dateRange === preset.id;
                    return (
                      <button
                        key={preset.id}
                        type="button"
                        onClick={() => setDateRange(preset.id as any)}
                        className={`px-3 py-1.5 rounded-lg border text-xs font-bold transition-all ${
                          isSelected
                            ? 'bg-emerald-600 border-emerald-650 text-white shadow-sm'
                            : 'bg-white border-gray-200 text-gray-650 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {preset.label}
                      </button>
                    );
                  })}
                </div>

                {/* Conditional Custom Date Pickers */}
                {dateRange === 'custom' && (
                  <div className="grid grid-cols-2 gap-4 pt-2.5 animate-slideDown">
                    <div className="space-y-1">
                      <span className="text-xxs font-bold text-gray-500 uppercase">Start Date</span>
                      <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="w-full px-3.5 py-2 border border-gray-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 text-sm font-semibold text-gray-900 shadow-sm focus:outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <span className="text-xxs font-bold text-gray-500 uppercase">End Date</span>
                      <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="w-full px-3.5 py-2 border border-gray-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 text-sm font-semibold text-gray-900 shadow-sm focus:outline-none"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* 3. FORMAT SELECTION */}
              <div className="space-y-2.5">
                <label className="text-xs font-bold uppercase tracking-wider text-gray-550 flex items-center gap-1.5">
                  <FileSpreadsheet className="w-3.5 h-3.5 text-gray-400" />
                  Format
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 'csv', label: 'CSV (Excel)', icon: FileSpreadsheet, desc: 'Raw table data' },
                    { id: 'pdf', label: 'PDF (Document)', icon: FileText, desc: 'Beautiful formatting' },
                    { id: 'excel', label: 'Excel (.xlsx)', icon: FileSpreadsheet, desc: 'Spreadsheet formula ready' }
                  ].map((fmt) => {
                    const isSelected = format === fmt.id;
                    const Icon = fmt.icon;
                    return (
                      <button
                        key={fmt.id}
                        type="button"
                        onClick={() => setFormat(fmt.id as any)}
                        className={`p-3 rounded-xl border text-sm transition-all flex flex-col items-center text-center gap-1 ${
                          isSelected
                            ? 'bg-emerald-50/50 border-emerald-500 text-emerald-950 ring-2 ring-emerald-500/10'
                            : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50/60'
                        }`}
                      >
                        <Icon className={`w-5 h-5 ${isSelected ? 'text-emerald-600' : 'text-gray-400'}`} />
                        <span className="font-extrabold mt-1 text-xs">{fmt.label}</span>
                        <span className="text-[10px] text-gray-400 font-semibold">{fmt.desc}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 4. CONDITIONAL OPTIONS */}
              {(format === 'pdf' || reportType === 'sales') && (
                <div className="p-4.5 bg-gray-50/50 border border-gray-200 rounded-xl space-y-4 animate-fadeIn">
                  <span className="text-xxs font-extrabold text-gray-500 uppercase tracking-widest block">Extra Configurations</span>
                  
                  {/* PDF Only Options */}
                  {format === 'pdf' && (
                    <div className="grid grid-cols-2 gap-4">
                      <label className="flex items-start gap-2.5 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={includeCharts}
                          onChange={(e) => setIncludeCharts(e.target.checked)}
                          className="mt-0.5 h-4 w-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                        />
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-gray-800">Include charts</span>
                          <span className="text-[10px] text-gray-450 font-semibold leading-normal">Embed charts & trend indicators</span>
                        </div>
                      </label>

                      <label className="flex items-start gap-2.5 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={includeSummary}
                          onChange={(e) => setIncludeSummary(e.target.checked)}
                          className="mt-0.5 h-4 w-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                        />
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-gray-800">Include summary</span>
                          <span className="text-[10px] text-gray-450 font-semibold leading-normal">Generate smart summary paragraphs</span>
                        </div>
                      </label>
                    </div>
                  )}

                  {/* Sales Report Options */}
                  {reportType === 'sales' && (
                    <div className="space-y-1.5">
                      <span className="text-[11px] font-bold text-gray-700 block">Group Data By</span>
                      <select
                        value={groupBy}
                        onChange={(e) => setGroupBy(e.target.value as any)}
                        className="w-full bg-white border border-gray-300 text-gray-900 text-xs font-semibold rounded-lg px-2.5 py-1.5 focus:ring-emerald-500 focus:border-emerald-500 focus:outline-none"
                      >
                        <option value="day">Day (Detailed rows)</option>
                        <option value="week">Week (Weekly aggregation)</option>
                        <option value="month">Month (Monthly aggregation)</option>
                      </select>
                    </div>
                  )}
                </div>
              )}

              {/* 5. ESTIMATION PREVIEW CARD */}
              <div className="border border-emerald-100 bg-emerald-50/20 rounded-xl p-4.5 flex justify-between items-center gap-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-100/50 text-emerald-800 rounded-lg">
                    <TrendingUp className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-extrabold text-emerald-950 uppercase tracking-wide">Export Estimation</h4>
                    <p className="text-xxs text-emerald-850 mt-0.5 font-semibold">Based on current selection parameters</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-extrabold text-emerald-900">
                    ~{previewData.rows.toLocaleString()} rows
                  </div>
                  <div className="text-[11px] font-bold text-emerald-700/80 mt-0.5">
                    Est. Size: {previewData.sizeStr}
                  </div>
                </div>
              </div>

            </div>

            {/* Footer */}
            <div className="px-6 py-4.5 border-t border-gray-100 bg-gray-50 flex justify-end gap-3 shrink-0 rounded-b-2xl">
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                disabled={loading}
                className="px-4.5 py-2.5 rounded-xl border border-gray-350 text-xs font-extrabold text-gray-700 bg-white hover:bg-gray-100 transition shadow-sm focus:outline-none"
              >
                Cancel
              </button>
              
              <button
                type="button"
                onClick={handleExportSubmit}
                disabled={loading}
                className="px-5 py-2.5 rounded-xl text-xs font-extrabold text-white bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-600/40 disabled:cursor-not-allowed transition shadow-md flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating Report...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 stroke-[2.5]" />
                    Export Report
                  </>
                )}
              </button>
            </div>

          </div>
        </div>
      )}
    </>
  );
}

// apps/admin/components/Tables/QrCodePreview.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { Loader2, Download, RefreshCw, AlertCircle } from 'lucide-react';

interface QrCodePreviewProps {
  tableNumber: number;
  qrCodeUrl: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  onDownload?: () => void;
}

export default function QrCodePreview({
  tableNumber,
  qrCodeUrl,
  size = 'md',
  showLabel = true,
  onDownload,
}: QrCodePreviewProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Reset states when the URL changes
  useEffect(() => {
    setLoading(true);
    setError(false);
  }, [qrCodeUrl]);

  // Size mapping
  const sizeClasses = {
    sm: 'w-[100px] h-[100px]',
    md: 'w-[150px] h-[150px]',
    lg: 'w-[200px] h-[200px]',
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative group rounded-xl border border-gray-200 p-3 bg-white hover:shadow-md transition-shadow duration-300 flex items-center justify-center">
        {/* QR Code Container */}
        <div className={`relative flex items-center justify-center ${sizeClasses[size]}`}>
          {/* Loading Spinner */}
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/90 z-10 rounded-lg">
              <Loader2 className="w-6 h-6 text-emerald-600 animate-spin" />
            </div>
          )}

          {/* Error Fallback */}
          {error ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-rose-50 text-rose-500 rounded-lg border border-rose-100 p-2 text-center">
              <AlertCircle className="w-6 h-6 mb-1 text-rose-500" />
              <span className="text-[10px] font-bold uppercase tracking-wider">Failed to Load</span>
              <button 
                onClick={() => { setError(false); setLoading(true); }}
                className="mt-1 p-1 bg-white hover:bg-rose-100 border border-rose-200 rounded-md transition-colors"
                title="Retry loading"
              >
                <RefreshCw className="w-3 h-3 text-rose-600" />
              </button>
            </div>
          ) : (
            /* Actual QR Code Image */
            <img
              src={qrCodeUrl}
              alt={`QR Code for Table ${tableNumber}`}
              className={`object-contain rounded-lg transition-opacity duration-300 ${loading ? 'opacity-0' : 'opacity-100'}`}
              onLoad={() => setLoading(false)}
              onError={() => {
                setLoading(false);
                setError(true);
              }}
            />
          )}
        </div>

        {/* Hover Action overlay (only if onDownload is provided and not in error/loading state) */}
        {onDownload && !loading && !error && (
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl flex items-center justify-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDownload();
              }}
              className="p-2 bg-white text-gray-800 rounded-full hover:bg-emerald-600 hover:text-white transition-all transform scale-90 group-hover:scale-100 duration-300 shadow-lg"
              title="Download QR Code"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Label under QR Code */}
      {showLabel && (
        <div className="mt-2 text-center">
          <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">Table</span>
          <p className="text-sm font-extrabold text-gray-850 mt-0.5">{tableNumber}</p>
        </div>
      )}
    </div>
  );
}

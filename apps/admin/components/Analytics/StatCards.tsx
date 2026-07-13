// apps/admin/components/Analytics/StatCards.tsx
'use client';

import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Package, 
  Receipt, 
  LayoutGrid, 
  ArrowUpRight, 
  ArrowDownRight,
  RefreshCw
} from 'lucide-react';

export interface StatCardsData {
  todaySales: number;
  todayOrders: number;
  averageTicket: number;
  tablesOccupied: number;
  totalTables: number;
  salesChange: number; // percentage, e.g. +5.4 or -2.3
  ordersChange: number; // percentage, e.g. +3.1 or -1.5
}

interface StatCardsProps {
  data: StatCardsData;
  loading: boolean;
  onRefresh?: () => void;
}

export default function StatCards({ data, loading, onRefresh }: StatCardsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, idx) => (
          <div 
            key={idx} 
            className="animate-pulse bg-white border border-gray-200 rounded-xl p-4 shadow-sm h-32 flex flex-col justify-between"
          >
            <div className="flex justify-between items-start">
              <div className="h-4 bg-gray-200 rounded w-24"></div>
              <div className="h-8 w-8 bg-gray-200 rounded-lg"></div>
            </div>
            <div className="space-y-2">
              <div className="h-6 bg-gray-200 rounded w-32"></div>
              <div className="h-3 bg-gray-200 rounded w-20"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const {
    todaySales,
    todayOrders,
    averageTicket,
    tablesOccupied,
    totalTables,
    salesChange,
    ordersChange
  } = data;

  const isSalesIncrease = salesChange >= 0;
  const isOrdersIncrease = ordersChange >= 0;

  // Calculate table occupancy percentage
  const occupancyPercentage = totalTables > 0 
    ? Math.min(Math.max((tablesOccupied / totalTables) * 100, 0), 100) 
    : 0;

  return (
    <div className="space-y-4">
      {onRefresh && (
        <div className="flex justify-end">
          <button
            onClick={onRefresh}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-600 bg-white hover:bg-gray-50 border border-gray-200 rounded-lg shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Stats
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* CARD 1 - TODAY'S SALES */}
        <div 
          className={`border rounded-xl shadow-sm p-4 transition-all duration-300 ${
            isSalesIncrease 
              ? 'bg-emerald-50/60 border-emerald-200/80 hover:shadow-md' 
              : 'bg-red-50/60 border-red-200/80 hover:shadow-md'
          }`}
        >
          <div className="flex justify-between items-start">
            <div>
              <p className={`text-xs font-semibold uppercase tracking-wider ${
                isSalesIncrease ? 'text-emerald-700/80' : 'text-red-700/80'
              }`}>
                Today's Sales
              </p>
              <h3 className={`text-2xl font-bold mt-1.5 ${
                isSalesIncrease ? 'text-emerald-950' : 'text-red-950'
              }`}>
                KES {todaySales.toLocaleString()}
              </h3>
            </div>
            <div className={`p-2 rounded-lg ${
              isSalesIncrease ? 'bg-emerald-100/50' : 'bg-red-100/50'
            }`}>
              <TrendingUp className={`w-5 h-5 ${
                isSalesIncrease ? 'text-emerald-600' : 'text-red-600'
              }`} />
            </div>
          </div>

          <div className="flex items-center gap-1 mt-3.5">
            <span className={`text-sm font-bold flex items-center gap-0.5 px-1.5 py-0.5 rounded ${
              isSalesIncrease 
                ? 'text-emerald-700 bg-emerald-100/40' 
                : 'text-red-700 bg-red-100/40'
            }`}>
              {isSalesIncrease ? (
                <ArrowUpRight className="w-3.5 h-3.5 stroke-[2.5]" />
              ) : (
                <ArrowDownRight className="w-3.5 h-3.5 stroke-[2.5]" />
              )}
              {Math.abs(salesChange).toFixed(1)}%
            </span>
            <span className={`text-xs ${
              isSalesIncrease ? 'text-emerald-700/70' : 'text-red-700/70'
            }`}>
              vs yesterday
            </span>
          </div>
        </div>

        {/* CARD 2 - TODAY'S ORDERS */}
        <div 
          className={`border rounded-xl shadow-sm p-4 transition-all duration-300 ${
            isOrdersIncrease 
              ? 'bg-emerald-50/60 border-emerald-200/80 hover:shadow-md' 
              : 'bg-red-50/60 border-red-200/80 hover:shadow-md'
          }`}
        >
          <div className="flex justify-between items-start">
            <div>
              <p className={`text-xs font-semibold uppercase tracking-wider ${
                isOrdersIncrease ? 'text-emerald-700/80' : 'text-red-700/80'
              }`}>
                Orders Today
              </p>
              <h3 className={`text-2xl font-bold mt-1.5 ${
                isOrdersIncrease ? 'text-emerald-950' : 'text-red-950'
              }`}>
                {todayOrders}
              </h3>
            </div>
            <div className={`p-2 rounded-lg ${
              isOrdersIncrease ? 'bg-emerald-100/50' : 'bg-red-100/50'
            }`}>
              <Package className={`w-5 h-5 ${
                isOrdersIncrease ? 'text-emerald-600' : 'text-red-600'
              }`} />
            </div>
          </div>

          <div className="flex items-center gap-1 mt-3.5">
            <span className={`text-sm font-bold flex items-center gap-0.5 px-1.5 py-0.5 rounded ${
              isOrdersIncrease 
                ? 'text-emerald-700 bg-emerald-100/40' 
                : 'text-red-700 bg-red-100/40'
            }`}>
              {isOrdersIncrease ? (
                <ArrowUpRight className="w-3.5 h-3.5 stroke-[2.5]" />
              ) : (
                <ArrowDownRight className="w-3.5 h-3.5 stroke-[2.5]" />
              )}
              {Math.abs(ordersChange).toFixed(1)}%
            </span>
            <span className={`text-xs ${
              isOrdersIncrease ? 'text-emerald-700/70' : 'text-red-700/70'
            }`}>
              vs yesterday
            </span>
          </div>
        </div>

        {/* CARD 3 - AVERAGE TICKET */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 hover:shadow-md transition-all duration-300 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Avg. Ticket
              </p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1.5">
                KES {averageTicket.toLocaleString()}
              </h3>
            </div>
            <div className="p-2 bg-gray-50 border border-gray-100 rounded-lg">
              <Receipt className="w-5 h-5 text-gray-500" />
            </div>
          </div>

          <div className="mt-3.5">
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500" />
              per order
            </p>
          </div>
        </div>

        {/* CARD 4 - TABLES OCCUPIED */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 hover:shadow-md transition-all duration-300 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Tables Occupied
              </p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1.5">
                {tablesOccupied} / {totalTables}
              </h3>
            </div>
            <div className="p-2 bg-gray-50 border border-gray-100 rounded-lg">
              <LayoutGrid className="w-5 h-5 text-gray-500" />
            </div>
          </div>

          <div className="mt-3.5 space-y-1.5">
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden border border-gray-200">
              <div 
                className="bg-emerald-500 h-full rounded-full transition-all duration-500 ease-out" 
                style={{ width: `${occupancyPercentage}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 flex justify-between items-center">
              <span>{Math.round(occupancyPercentage)}% capacity</span>
              <span>currently occupied</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

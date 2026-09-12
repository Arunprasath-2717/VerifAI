import React from 'react';
import { Filter, Calendar, Cpu, CheckCircle2, Globe, RotateCcw } from 'lucide-react';
import type { ActiveFilters, FilterOptions } from '../types/api';

interface FilterBarProps {
  options: FilterOptions | null;
  filters: ActiveFilters;
  onFilterChange: (newFilters: ActiveFilters) => void;
  onReset: () => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  options,
  filters,
  onFilterChange,
  onReset
}) => {
  const handleChange = (key: keyof ActiveFilters, value: string) => {
    onFilterChange({
      ...filters,
      [key]: value
    });
  };

  const hasActiveFilters = Boolean(
    filters.dateFrom || filters.dateTo || filters.modelId || filters.verdict || filters.domain
  );

  return (
    <div className="bg-slate-900/80 border border-indigo-900/40 rounded-2xl p-5 shadow-xl backdrop-blur-xl mb-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        
        {/* Title */}
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-indigo-950 rounded-xl border border-indigo-800 text-indigo-400">
            <Filter className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100">Compositing Filter Engine</h3>
            <p className="text-[11px] text-slate-400">Date + Model + Verdict + Domain compose seamlessly</p>
          </div>
        </div>

        {/* Filter Inputs Grid */}
        <div className="flex flex-wrap items-center gap-3">
          
          {/* Model Filter */}
          <div className="flex items-center space-x-2 bg-slate-950/90 px-3.5 py-2 rounded-xl border border-slate-800 text-xs font-semibold hover:border-slate-700 transition-colors">
            <Cpu className="h-4 w-4 text-indigo-400" />
            <select
              value={filters.modelId}
              onChange={(e) => handleChange('modelId', e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="" className="bg-slate-900 text-slate-300">All Models</option>
              {options?.models.map((m) => (
                <option key={m} value={m} className="bg-slate-900 text-slate-200">
                  {m}
                </option>
              ))}
            </select>
          </div>

          {/* Verdict Filter */}
          <div className="flex items-center space-x-2 bg-slate-950/90 px-3.5 py-2 rounded-xl border border-slate-800 text-xs font-semibold hover:border-slate-700 transition-colors">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <select
              value={filters.verdict}
              onChange={(e) => handleChange('verdict', e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="" className="bg-slate-900 text-slate-300">All Verdicts</option>
              <option value="SUPPORTED" className="bg-slate-900 text-emerald-400 font-bold">SUPPORTED</option>
              <option value="CONTRADICTED" className="bg-slate-900 text-rose-400 font-bold">CONTRADICTED</option>
              <option value="INCONCLUSIVE" className="bg-slate-900 text-amber-400 font-bold">INCONCLUSIVE</option>
            </select>
          </div>

          {/* Domain Filter */}
          <div className="flex items-center space-x-2 bg-slate-950/90 px-3.5 py-2 rounded-xl border border-slate-800 text-xs font-semibold hover:border-slate-700 transition-colors">
            <Globe className="h-4 w-4 text-sky-400" />
            <select
              value={filters.domain}
              onChange={(e) => handleChange('domain', e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="" className="bg-slate-900 text-slate-300">All Domains</option>
              {options?.domains.map((d) => (
                <option key={d} value={d} className="bg-slate-900 text-slate-200">
                  {d}
                </option>
              ))}
            </select>
          </div>

          {/* Date From */}
          <div className="flex items-center space-x-2 bg-slate-950/90 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-semibold">
            <Calendar className="h-4 w-4 text-purple-400" />
            <span className="text-slate-400">From:</span>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => handleChange('dateFrom', e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            />
          </div>

          {/* Date To */}
          <div className="flex items-center space-x-2 bg-slate-950/90 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-semibold">
            <Calendar className="h-4 w-4 text-purple-400" />
            <span className="text-slate-400">To:</span>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => handleChange('dateTo', e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            />
          </div>

          {/* Reset Filters */}
          {hasActiveFilters && (
            <button
              onClick={onReset}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white shadow-md shadow-rose-600/30 text-xs font-bold transition-all duration-200"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Reset Filters</span>
            </button>
          )}

        </div>

      </div>
    </div>
  );
};

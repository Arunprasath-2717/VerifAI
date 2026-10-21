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
    <div className="bg-white/50 border border-white/70 rounded-2xl p-5 shadow-lg shadow-sky-500/10 backdrop-blur-xl mb-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        
        {/* Title */}
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-sky-100/80 rounded-xl border border-sky-200/50 text-sky-600 shadow-sm">
            <Filter className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">Compositing Filter Engine</h3>
            <p className="text-[11px] text-sky-600/80 font-medium">Date + Model + Verdict + Domain compose seamlessly</p>
          </div>
        </div>

        {/* Filter Inputs Grid */}
        <div className="flex flex-wrap items-center gap-3">
          
          {/* Model Filter */}
          <div className="flex items-center space-x-2 bg-white/70 px-3.5 py-2 rounded-xl border border-white hover:border-sky-300 shadow-sm text-xs font-semibold hover:shadow-md transition-all">
            <Cpu className="h-4 w-4 text-sky-500" />
            <select
              value={filters.modelId}
              onChange={(e) => handleChange('modelId', e.target.value)}
              className="bg-transparent text-slate-700 focus:outline-none cursor-pointer w-full outline-none"
            >
              <option value="">All Models</option>
              {options?.models.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          {/* Verdict Filter */}
          <div className="flex items-center space-x-2 bg-white/70 px-3.5 py-2 rounded-xl border border-white hover:border-sky-300 shadow-sm text-xs font-semibold hover:shadow-md transition-all">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <select
              value={filters.verdict}
              onChange={(e) => handleChange('verdict', e.target.value)}
              className="bg-transparent text-slate-700 focus:outline-none cursor-pointer w-full outline-none"
            >
              <option value="">All Verdicts</option>
              <option value="SUPPORTED" className="text-emerald-600 font-bold">SUPPORTED</option>
              <option value="CONTRADICTED" className="text-rose-600 font-bold">CONTRADICTED</option>
              <option value="INCONCLUSIVE" className="text-amber-600 font-bold">INCONCLUSIVE</option>
            </select>
          </div>

          {/* Domain Filter */}
          <div className="flex items-center space-x-2 bg-white/70 px-3.5 py-2 rounded-xl border border-white hover:border-sky-300 shadow-sm text-xs font-semibold hover:shadow-md transition-all">
            <Globe className="h-4 w-4 text-sky-500" />
            <select
              value={filters.domain}
              onChange={(e) => handleChange('domain', e.target.value)}
              className="bg-transparent text-slate-700 focus:outline-none cursor-pointer w-full outline-none"
            >
              <option value="">All Domains</option>
              {options?.domains.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          {/* Date From */}
          <div className="flex items-center space-x-2 bg-white/70 px-3.5 py-1.5 rounded-xl border border-white hover:border-sky-300 shadow-sm text-xs font-semibold hover:shadow-md transition-all">
            <Calendar className="h-4 w-4 text-blue-500" />
            <span className="text-slate-500">From:</span>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => handleChange('dateFrom', e.target.value)}
              className="bg-transparent text-slate-700 focus:outline-none cursor-pointer outline-none appearance-none"
            />
          </div>

          {/* Date To */}
          <div className="flex items-center space-x-2 bg-white/70 px-3.5 py-1.5 rounded-xl border border-white hover:border-sky-300 shadow-sm text-xs font-semibold hover:shadow-md transition-all">
            <Calendar className="h-4 w-4 text-blue-500" />
            <span className="text-slate-500">To:</span>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => handleChange('dateTo', e.target.value)}
              className="bg-transparent text-slate-700 focus:outline-none cursor-pointer outline-none appearance-none"
            />
          </div>

          {/* Reset Filters */}
          {hasActiveFilters && (
            <button
              onClick={onReset}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-rose-500 to-pink-500 hover:from-rose-400 hover:to-pink-400 text-white shadow-md shadow-rose-500/30 text-xs font-bold transition-all duration-200 hover:-translate-y-0.5"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Reset</span>
            </button>
          )}

        </div>

      </div>
    </div>
  );
};

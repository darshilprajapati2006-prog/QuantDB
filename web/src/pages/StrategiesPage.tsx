import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  FlaskConical,
  Play,
  Settings,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Layers,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Sliders,
  ShieldCheck,
} from 'lucide-react';
import { request } from '../lib/api';
import type { Strategy } from '../types';

export function StrategiesPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');
  const [activeStrategy, setActiveStrategy] = useState<Strategy | null>(null);

  const { data: strategies = [], isLoading, refetch } = useQuery({
    queryKey: ['strategies'],
    queryFn: () => request<Strategy[]>('/strategies'),
  });

  // Unique strategy types
  const types = useMemo(() => {
    const set = new Set<string>();
    strategies.forEach((s) => {
      if (s.strategy_type) set.add(s.strategy_type);
    });
    return Array.from(set);
  }, [strategies]);

  const filteredStrategies = useMemo(() => {
    return strategies.filter((s) => {
      const matchSearch =
        s.strategy_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchType = selectedType === 'ALL' || s.strategy_type === selectedType;
      return matchSearch && matchType;
    });
  }, [strategies, searchTerm, selectedType]);

  const parseParams = (raw: string | Record<string, unknown>): Record<string, unknown> => {
    if (typeof raw === 'object' && raw !== null) return raw;
    try {
      return JSON.parse(raw);
    } catch {
      return { raw_parameters: raw };
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Heading */}
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            QUANTITATIVE MODELING <span className="eyebrow-sep">/</span> STRATEGY CATALOG
          </div>
          <h1>Systematic Strategies & Models</h1>
          <p>
            Algorithmic signal generation rules, indicator parameters, and execution logic.
          </p>
        </div>

        <button
          onClick={() => navigate('/backtesting')}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1b3a2d] hover:bg-[#234c3b] text-[#86d9b2] border border-[#2b5945] rounded-md text-[11px] font-medium transition"
        >
          <Play size={13} fill="currentColor" />
          <span>Launch Backtester</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-b border-[#1f282e] pb-3">
        <div className="relative w-full sm:w-80">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64747a]" />
          <input
            type="text"
            placeholder="Search strategies or models..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-[#10161b] border border-[#222d33] rounded-md text-xs text-[#dbe5e1] placeholder-[#5a6c72] focus:outline-none focus:border-[#487a66]"
          />
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          <button
            onClick={() => setSelectedType('ALL')}
            className={`px-3 py-1 rounded text-xs font-mono transition ${
              selectedType === 'ALL'
                ? 'bg-[#182721] text-[#86d9b2] border border-[#264438]'
                : 'bg-[#10151a] text-[#78878b] border border-[#1d262c] hover:text-[#c7d2cf]'
            }`}
          >
            ALL ({strategies.length})
          </button>
          {types.map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`px-3 py-1 rounded text-xs font-mono uppercase transition ${
                selectedType === type
                  ? 'bg-[#182721] text-[#86d9b2] border border-[#264438]'
                  : 'bg-[#10151a] text-[#78878b] border border-[#1d262c] hover:text-[#c7d2cf]'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Strategies Grid */}
      {isLoading ? (
        <div className="panel py-16 text-center text-[#78888d] text-xs">
          Loading QuantDB strategy models...
        </div>
      ) : filteredStrategies.length === 0 ? (
        <div className="panel py-16 text-center text-[#78888d] text-xs">
          <FlaskConical size={32} className="mx-auto mb-2 opacity-40 text-[#68d1a9]" />
          <p>No strategies found matching your search.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredStrategies.map((strat) => {
            const params = parseParams(strat.parameters);
            const isActive = strat.status?.toUpperCase() === 'ACTIVE';

            return (
              <div
                key={strat.strategy_id}
                className="panel flex flex-col justify-between hover:border-[#2d3c45] transition"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#162128] text-[#82a4bc] border border-[#223542] uppercase tracking-wider">
                      {strat.strategy_type || 'MOMENTUM'}
                    </span>
                    <span
                      className={`text-[9px] font-mono px-2 py-0.5 rounded border uppercase ${
                        isActive
                          ? 'bg-[#15271f] text-[#76d5ab] border-[#254637]'
                          : 'bg-[#1b1c1e] text-[#8d9294] border-[#292c2f]'
                      }`}
                    >
                      {strat.status || 'DRAFT'}
                    </span>
                  </div>

                  <h3 className="text-sm font-semibold text-[#e5ecea] mt-1 mb-1.5 font-sans">
                    {strat.strategy_name}
                  </h3>
                  <p className="text-xs text-[#7e8e92] line-clamp-2 leading-relaxed mb-4">
                    {strat.description || 'Quantitative algorithm designed for systematic market execution.'}
                  </p>

                  {/* Parameter chips */}
                  <div className="border-t border-[#1e272d] pt-3 mb-4">
                    <div className="text-[10px] font-mono text-[#627379] uppercase mb-2 flex items-center gap-1.5">
                      <Sliders size={11} />
                      <span>Model Hyperparameters</span>
                    </div>
                    <div className="grid grid-cols-2 gap-1.5 font-mono text-[11px]">
                      {Object.entries(params).slice(0, 4).map(([k, v]) => (
                        <div key={k} className="bg-[#0e1418] px-2 py-1 rounded border border-[#1b252b] flex justify-between items-center">
                          <span className="text-[#6c7d83] truncate">{k}</span>
                          <span className="text-[#b9d5c9] font-medium">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Card Actions */}
                <div className="border-t border-[#1e272d] pt-3 flex items-center justify-between mt-auto">
                  <span className="text-[10px] font-mono text-[#5b6a70]">
                    ID: #{strat.strategy_id}
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setActiveStrategy(strat)}
                      className="px-2.5 py-1 text-[11px] text-[#839397] hover:text-[#d3ddd9] bg-[#12191e] border border-[#222e35] rounded transition"
                    >
                      Inspect
                    </button>
                    <button
                      onClick={() => navigate('/backtesting')}
                      className="px-2.5 py-1 text-[11px] text-[#86d9b2] hover:bg-[#1a382c] bg-[#162d23] border border-[#274b3b] rounded transition flex items-center gap-1"
                    >
                      <Play size={10} fill="currentColor" /> Backtest
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Inspect Strategy Modal */}
      {activeStrategy && (
        <div className="fixed inset-0 z-50 bg-[#000000a6] backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f161c] border border-[#263740] rounded-xl max-w-lg w-full p-6 shadow-2xl relative">
            <div className="flex items-start justify-between border-b border-[#202c34] pb-3 mb-4">
              <div>
                <span className="text-[10px] font-mono text-[#76d5ab] uppercase">
                  {activeStrategy.strategy_type} STRATEGY
                </span>
                <h2 className="text-base font-semibold text-[#e8f0ec] mt-0.5">
                  {activeStrategy.strategy_name}
                </h2>
              </div>
              <button
                onClick={() => setActiveStrategy(null)}
                className="text-[#6e8086] hover:text-[#dce5e1] text-lg font-mono"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-[#8c9c9f] leading-relaxed mb-4">
              {activeStrategy.description}
            </p>

            <div className="space-y-3 mb-6">
              <div className="text-xs font-mono text-[#728389] uppercase tracking-wider">
                Full Configuration Matrix
              </div>
              <pre className="bg-[#090d10] border border-[#1b262d] rounded-lg p-3 text-[11px] font-mono text-[#a5d7c1] overflow-x-auto max-h-52">
                {JSON.stringify(parseParams(activeStrategy.parameters), null, 2)}
              </pre>
            </div>

            <div className="flex items-center justify-end gap-2 border-t border-[#202c34] pt-4">
              <button
                onClick={() => setActiveStrategy(null)}
                className="px-3 py-1.5 bg-[#141b21] hover:bg-[#1b242c] text-[#899aa0] border border-[#232f37] rounded-md text-xs transition"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setActiveStrategy(null);
                  navigate('/backtesting');
                }}
                className="px-4 py-1.5 bg-[#1b3a2d] hover:bg-[#234c3b] text-[#86d9b2] border border-[#2b5945] rounded-md text-xs font-medium transition flex items-center gap-1.5"
              >
                <Play size={12} fill="currentColor" /> Simulate This Strategy
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="disclaimer">
        <ShieldCheck size={14} /> Strategies run on the QuantDB Backtest Engine and execute in simulation mode. No real capital risk.
      </div>
    </div>
  );
}

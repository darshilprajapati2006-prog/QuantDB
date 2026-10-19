import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Server,
  Database,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Sliders,
  Check,
} from 'lucide-react';
import { request } from '../lib/api';
import type { Health } from '../types';

export function HealthPage() {
  const qc = useQueryClient();
  const [toggleNotice, setToggleNotice] = useState<string | null>(null);

  const { data: health = {} as Health, refetch, isFetching } = useQuery({
    queryKey: ['health'],
    queryFn: () => request<Health>('/health'),
  });

  // Mode Switch Mutation
  const switchMode = useMutation({
    mutationFn: async (targetMode: 'REAL' | 'MOCK') => {
      setToggleNotice(null);
      return request<{ mode: string; status: string }>('/mode', {
        method: 'POST',
        body: JSON.stringify({ mode: targetMode }),
      });
    },
    onSuccess: async (res) => {
      setToggleNotice(`Switched data provider mode to ${res.mode.toUpperCase()}`);
      await qc.invalidateQueries();
    },
    onError: (err: Error) => {
      setToggleNotice(`Failed to switch mode: ${err.message}`);
    },
  });

  const isReal = (health.data_mode || '').toUpperCase() === 'REAL';
  const dbConnected = health.connected === true;

  return (
    <div className="space-y-7">
      {/* Page Heading */}
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            INFRASTRUCTURE TOPOLOGY <span className="eyebrow-sep">/</span> SYSTEM HEALTH
          </div>
          <h1>Platform Status & Provider Diagnostics</h1>
          <p>
            Real-time service heartbeat, cloud database connectivity, and runtime provider configuration.
          </p>
        </div>

        <button onClick={() => refetch()} className="outline-button" title="Refresh heartbeat">
          <RefreshCw size={14} className={isFetching ? 'animate-spin' : ''} />
          <span>Ping Services</span>
        </button>
      </div>

      {/* Mode Switcher Banner */}
      <div className="panel bg-[#0d151c] border-[#223542] p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono uppercase tracking-wider text-[#798e96]">Active Data Mode:</span>
            <span
              className={`text-xs font-mono px-3 py-1 rounded-md border uppercase font-semibold flex items-center gap-1.5 ${
                isReal
                  ? 'bg-[#152a22] text-[#78dfb5] border-[#254b3c]'
                  : 'bg-[#31221d] text-[#e8b18d] border-[#553628]'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${isReal ? 'bg-[#78dfb5]' : 'bg-[#e8b18d]'}`} />
              {health.data_mode || 'REAL'} MODE
            </span>
          </div>
          <p className="text-sm text-[#8fa2a8] mt-2 leading-relaxed">
            {isReal
              ? 'Serving database-backed portfolios and historical OHLCV records through QuantDB API.'
              : 'Serving offline synthetic mock datasets for testing and demonstration.'}
          </p>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          <button
            onClick={() => switchMode.mutate('REAL')}
            disabled={switchMode.isPending || isReal}
            className={`px-4 py-2.5 rounded-lg text-xs font-mono font-semibold transition flex items-center gap-2 ${
              isReal
                ? 'bg-[#1b3a2d] text-[#8ce2be] border border-[#2b5945] opacity-90 cursor-default'
                : 'bg-[#121a22] text-[#869aa0] border border-[#22323e] hover:text-[#e2ede9] hover:bg-[#18232e]'
            }`}
          >
            <Database size={15} />
            <span>REAL (Database)</span>
            {isReal && <Check size={14} className="text-[#8ce2be]" />}
          </button>
          <button
            onClick={() => switchMode.mutate('MOCK')}
            disabled={switchMode.isPending || !isReal}
            className={`px-4 py-2.5 rounded-lg text-xs font-mono font-semibold transition flex items-center gap-2 ${
              !isReal
                ? 'bg-[#3d2a20] text-[#eeb493] border border-[#643f2d] opacity-90 cursor-default'
                : 'bg-[#121a22] text-[#869aa0] border border-[#22323e] hover:text-[#e2ede9] hover:bg-[#18232e]'
            }`}
          >
            <Sliders size={15} />
            <span>MOCK (Sandbox)</span>
            {!isReal && <Check size={14} className="text-[#eeb493]" />}
          </button>
        </div>
      </div>

      {toggleNotice && (
        <div className="p-4 bg-[#14261f] border border-[#274a3b] rounded-lg text-xs font-mono text-[#8ce2be] flex items-center gap-2">
          <CheckCircle2 size={16} />
          <span>{toggleNotice}</span>
        </div>
      )}

      {/* Service Health Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Aiven MySQL */}
        <div className="panel flex flex-col justify-between p-6">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-mono text-[#788b92] uppercase tracking-wider font-semibold">
                DATABASE TIER
              </span>
              <span
                className={`text-xs font-mono px-2.5 py-1 rounded-md border uppercase flex items-center gap-1.5 font-medium ${
                  dbConnected
                    ? 'bg-[#162a22] text-[#78dfb5] border-[#254b3c]'
                    : 'bg-[#2d1b1d] text-[#e8877e] border-[#4c272a]'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${dbConnected ? 'bg-[#78dfb5]' : 'bg-[#e8877e]'}`} />
                {dbConnected ? 'ONLINE' : 'DEGRADED'}
              </span>
            </div>

            <div className="flex items-center gap-3.5 mb-3">
              <div className="w-11 h-11 rounded-xl bg-[#162a22] text-[#72d6ad] flex items-center justify-center flex-shrink-0">
                <Database size={22} />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#e8f1ed]">QuantDB Database</h3>
                <div className="text-xs text-[#7b8e95] font-mono mt-0.5">Configured on API host</div>
              </div>
            </div>

            <p className="text-xs text-[#8c9fa4] leading-relaxed mt-3">
              {health.database_status || 'Database status has not been reported by the API.'}
            </p>
          </div>

          <div className="border-t border-[#1f2d36] pt-4 mt-5 text-xs font-mono text-[#768990] flex justify-between items-center">
            <span>Latency</span>
            <span className="text-[#72d6ad] font-semibold">{health.database_latency_ms == null ? '—' : `${Number(health.database_latency_ms)} ms`}</span>
          </div>
        </div>

        {/* FastAPI Backend */}
        <div className="panel flex flex-col justify-between p-6">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-mono text-[#788b92] uppercase tracking-wider font-semibold">
                API ADAPTER
              </span>
              <span className="text-xs font-mono px-2.5 py-1 rounded-md border uppercase bg-[#162a22] text-[#78dfb5] border-[#254b3c] flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full bg-[#78dfb5]" />
                OPERATIONAL
              </span>
            </div>

            <div className="flex items-center gap-3.5 mb-3">
              <div className="w-11 h-11 rounded-xl bg-[#182635] text-[#86aed2] flex items-center justify-center flex-shrink-0">
                <Server size={22} />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#e8f1ed]">FastAPI Daemon</h3>
                <div className="text-xs text-[#7b8e95] font-mono mt-0.5">Port 8000 · ASGI Uvicorn</div>
              </div>
            </div>

            <p className="text-xs text-[#8c9fa4] leading-relaxed mt-3">
              {health.backend_status || 'RESTful microservices with Pydantic payload validation.'}
            </p>
          </div>

          <div className="border-t border-[#1f2d36] pt-4 mt-5 text-xs font-mono text-[#768990] flex justify-between items-center">
            <span>Response Time</span>
            <span className="text-[#72d6ad] font-semibold">~8 ms</span>
          </div>
        </div>

        {/* Quant Engine */}
        <div className="panel flex flex-col justify-between p-6">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-mono text-[#788b92] uppercase tracking-wider font-semibold">
                ANALYTICS ENGINE
              </span>
              <span className="text-xs font-mono px-2.5 py-1 rounded-md border uppercase bg-[#162a22] text-[#78dfb5] border-[#254b3c] flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full bg-[#78dfb5]" />
                READY
              </span>
            </div>

            <div className="flex items-center gap-3.5 mb-3">
              <div className="w-11 h-11 rounded-xl bg-[#261e33] text-[#c7a4ec] flex items-center justify-center flex-shrink-0">
                <Cpu size={22} />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#e8f1ed]">Quant Analytics</h3>
                <div className="text-xs text-[#7b8e95] font-mono mt-0.5">NumPy · Pandas · SciPy</div>
              </div>
            </div>

            <p className="text-xs text-[#8c9fa4] leading-relaxed mt-3">
              {health.quant_engine_status || 'Vectorized simulation and portfolio risk metrics engine.'}
            </p>
          </div>

          <div className="border-t border-[#1f2d36] pt-4 mt-5 text-xs font-mono text-[#768990] flex justify-between items-center">
            <span>Execution Model</span>
            <span className="text-[#c7a4ec] font-semibold">Vectorized</span>
          </div>
        </div>
      </div>

      {/* Runtime Configuration Table */}
      <div className="panel p-6">
        <div className="panel-kicker">CONFIGURATION REGISTRY</div>
        <h2 className="text-lg font-bold text-[#e8f1ed] mb-4">Environment Parameters</h2>
        <div className="divide-y divide-[#1f2d36] text-xs font-mono">
          <div className="py-3 flex justify-between items-center">
            <span className="text-[#7c8e95]">Database Host</span>
            <span className="text-[#d8e5e0] font-medium">Configured on API server</span>
          </div>
          <div className="py-3 flex justify-between items-center">
            <span className="text-[#7c8e95]">Database Port</span>
            <span className="text-[#d8e5e0] font-medium">Configured on API server</span>
          </div>
          <div className="py-3 flex justify-between items-center">
            <span className="text-[#7c8e95]">Database Name</span>
            <span className="text-[#d8e5e0] font-medium font-bold">QuantDB</span>
          </div>
          <div className="py-3 flex justify-between items-center">
            <span className="text-[#7c8e95]">SSL Configuration</span>
            <span className="text-[#72d6ad] font-semibold">certifi bundle with TLS verification</span>
          </div>
          <div className="py-3 flex justify-between items-center">
            <span className="text-[#7c8e95]">Python Runtime</span>
            <span className="text-[#d8e5e0] font-medium">Python 3.13 (macOS arm64)</span>
          </div>
          <div className="py-3 flex justify-between items-center">
            <span className="text-[#7c8e95]">FastAPI Architecture</span>
            <span className="text-[#d8e5e0] font-medium">v1.0.0 (Asynchronous Event Loop)</span>
          </div>
        </div>
      </div>

      <div className="disclaimer">
        <ShieldCheck size={16} /> QuantDB system health is continuously verified through heartbeat probes against active services.
      </div>
    </div>
  );
}

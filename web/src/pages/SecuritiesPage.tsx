import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  ArrowUpRight,
  BarChart2,
  Activity,
  Globe,
  Layers,
  Sparkles,
} from 'lucide-react';
import { request } from '../lib/api';
import type { Security, Exchange } from '../types';

export function SecuritiesPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedExchange, setSelectedExchange] = useState('ALL');
  const [selectedType, setSelectedType] = useState('ALL');

  const { data: securities = [], isLoading: secLoading } = useQuery({
    queryKey: ['securities'],
    queryFn: () => request<Security[]>('/securities'),
  });

  const { data: exchanges = [] } = useQuery({
    queryKey: ['exchanges'],
    queryFn: () => request<Exchange[]>('/exchanges'),
  });

  // Filter logic
  const filteredSecurities = useMemo(() => {
    return securities.filter((s) => {
      const matchSearch =
        s.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.security_name.toLowerCase().includes(searchTerm.toLowerCase());

      const matchExchange =
        selectedExchange === 'ALL' ||
        String(s.exchange_id) === selectedExchange;

      const matchType =
        selectedType === 'ALL' || s.security_type === selectedType;

      return matchSearch && matchExchange && matchType;
    });
  }, [securities, searchTerm, selectedExchange, selectedType]);

  const exchangeMap = useMemo(() => {
    const map: Record<number, string> = {};
    exchanges.forEach((e) => {
      map[e.exchange_id] = e.exchange_code;
    });
    return map;
  }, [exchanges]);

  return (
    <div className="space-y-7">
      {/* Header */}
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            INSTRUMENT UNIVERSE <span className="eyebrow-sep">/</span> SECURITIES
          </div>
          <h1 className="flex items-center gap-3">
            <span>Securities Master Catalog</span>
            <span className="text-xs px-3 py-1 rounded-md bg-[#192332] text-[#87A6D6] border border-[#25354D] font-mono">
              {filteredSecurities.length} Instruments
            </span>
          </h1>
          <p>
            Tradable equities, ETFs, and market indices returned by the selected data provider.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="panel bg-[#0d151c] border-[#202f3a] p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        {/* Search Input */}
        <div className="relative w-full md:w-96">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#687a81]" />
          <input
            type="text"
            placeholder="Search symbol or company..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#10171e] border border-[#23333e] rounded-lg pl-10 pr-4 py-2.5 text-sm text-[#dce7e3] placeholder-[#5d7077] focus:outline-none focus:border-[#4c8470]"
          />
        </div>

        {/* Filter Selectors */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          {/* Exchange Filter */}
          <select
            value={selectedExchange}
            onChange={(e) => setSelectedExchange(e.target.value)}
            className="bg-[#10171e] border border-[#23333e] rounded-lg px-3 py-2 text-xs text-[#dce7e3] font-mono focus:outline-none focus:border-[#4c8470]"
          >
            <option value="ALL">All Exchanges</option>
            {exchanges.map((e) => (
              <option key={e.exchange_id} value={String(e.exchange_id)}>
                {e.exchange_code} ({e.country})
              </option>
            ))}
          </select>

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-[#0B1015] border border-[#2A353A] rounded-md px-2.5 py-1.5 text-xs text-[#E5ECEA] font-mono focus:outline-none focus:border-[#06B6D4]"
          >
            <option value="ALL">All Asset Classes</option>
            <option value="EQUITY">Equity</option>
            <option value="ETF">ETF</option>
            <option value="INDEX">Index</option>
          </select>
        </div>
      </div>

      {/* Securities Table */}
      <div className="bg-[#11171C] border border-[#202B31] rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-[#1F2937] bg-[#0E1418] text-[10px] text-[#718087] uppercase tracking-wider">
                <th className="py-3 px-4">Instrument</th>
                <th className="py-3 px-4">Exchange</th>
                <th className="py-3 px-4">Asset Class</th>
                <th className="py-3 px-4 text-right">Reference Price</th>
                <th className="py-3 px-4 text-right">Annual Volatility</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#182126] text-[#DCE5E1]">
              {secLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#718087]">
                    Loading instruments from QuantDB API...
                  </td>
                </tr>
              ) : filteredSecurities.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#718087]">
                    No securities match your filter criteria.
                  </td>
                </tr>
              ) : (
                filteredSecurities.map((sec) => (
                  <tr key={sec.security_id} className="hover:bg-[#162026] transition">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-7 h-7 rounded bg-[#162A25] text-[#76D2AE] border border-[#2A4E43] font-bold flex items-center justify-center text-xs">
                          {sec.symbol.slice(0, 2)}
                        </div>
                        <div>
                          <b className="text-[#F0F5F2] block font-mono">{sec.symbol}</b>
                          <small className="text-[#78868B] text-[10px] block font-sans">
                            {sec.security_name}
                          </small>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded bg-[#1E293B] text-[#94A3B8] text-[10px] font-mono border border-[#334155]">
                        {exchangeMap[sec.exchange_id] || `EXCH #${sec.exchange_id}`}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[#A6B5B3] font-sans">{sec.security_type}</span>
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-[#F0F5F2]">
                      ${Number(sec.base_price || 100).toFixed(2)} {sec.currency}
                    </td>
                    <td className="py-3 px-4 text-right text-[#06B6D4]">
                      {(Number(sec.volatility || 0.02) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-[9px] font-mono uppercase ${
                          sec.status === 'ACTIVE'
                            ? 'bg-[#162A25] text-[#34D399] border border-[#2A4E43]'
                            : 'bg-[#291F1D] text-[#FB7185] border border-[#49302B]'
                        }`}
                      >
                        {sec.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => navigate('/market-data')}
                          title="View Chart"
                          className="px-2 py-1 bg-[#1A2522] hover:bg-[#20332D] text-[#76D2AE] rounded text-[10px] font-mono transition flex items-center gap-1"
                        >
                          <BarChart2 size={12} />
                          <span>Chart</span>
                        </button>
                        <button
                          onClick={() => navigate('/trading')}
                          title="Trade"
                          className="px-2 py-1 bg-[#1B3A2D] hover:bg-[#23503E] text-[#A4E1C3] rounded text-[10px] font-mono transition flex items-center gap-1 font-bold"
                        >
                          <Activity size={12} />
                          <span>Trade</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
export default SecuritiesPage;

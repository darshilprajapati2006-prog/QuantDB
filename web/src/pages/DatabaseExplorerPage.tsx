import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Table as TableIcon,
  RefreshCw,
  Server,
  ShieldCheck,
  ChevronRight,
  X,
  Database,
  Layers,
  FileSpreadsheet,
  CheckCircle2,
  Info,
} from 'lucide-react';
import { request } from '../lib/api';
import type { TableMeta } from '../types';

interface TableResponse {
  table?: string;
  count?: number;
  records?: Record<string, unknown>[];
}

export function DatabaseExplorerPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'ALL' | 'BASE TABLE' | 'VIEW'>('ALL');
  const [selectedTable, setSelectedTable] = useState<string | null>(null);

  // Fetch tables metadata
  const { data: tables = [], isLoading, refetch, isFetching, isError } = useQuery({
    queryKey: ['database-tables'],
    queryFn: () => request<TableMeta[]>('/database/tables'),
  });

  // Fetch selected table records safely
  const rawQuery = useQuery({
    queryKey: ['database-table-rows', selectedTable],
    queryFn: () => request<TableResponse | Record<string, unknown>[]>(`/database/tables/${selectedTable}?limit=50`),
    enabled: !!selectedTable,
  });

  const filteredTables = useMemo(() => {
    return tables.filter((t) => {
      const matchSearch = t.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchType = filterType === 'ALL' || t.type === filterType;
      return matchSearch && matchType;
    });
  }, [tables, searchTerm, filterType]);

  const totalRows = useMemo(() => {
    return tables.reduce((acc, t) => acc + (t.row_count || 0), 0);
  }, [tables]);

  // Safely extract table rows as an array
  const { displayRows } = useMemo(() => {
    if (!selectedTable) return { displayRows: [] };

    let fetchedRows: Record<string, unknown>[] = [];
    const data = rawQuery.data;

    if (Array.isArray(data)) {
      fetchedRows = data;
    } else if (data && typeof data === 'object' && Array.isArray((data as TableResponse).records)) {
      fetchedRows = (data as TableResponse).records || [];
    }

    if (fetchedRows.length > 0) {
      return { displayRows: fetchedRows };
    }
    return { displayRows: [] };
  }, [selectedTable, rawQuery.data]);

  const columns = useMemo(() => {
    if (displayRows.length === 0) return [];
    return Object.keys(displayRows[0]);
  }, [displayRows]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            RELATIONAL REPOSITORY <span className="eyebrow-sep">/</span> DATABASE
          </div>
          <h1>Database Schema & Tables Explorer</h1>
          <p>
            Browse the schema and records available to the connected API account.
          </p>
        </div>

        <button onClick={() => refetch()} className="outline-button" title="Sync database metadata">
          <RefreshCw size={14} className={isFetching ? 'animate-spin' : ''} />
          <span>Sync Schema</span>
        </button>
      </div>

      {/* Database Connection Info Card */}
      <div className="panel bg-[#0d1419] border-[#1e2a32] p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
        <div className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-lg bg-[#14231d] border border-[#264536] flex items-center justify-center text-[#70d2a8] flex-shrink-0">
            <Server size={22} />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-[#e5ecea] font-mono">
                QuantDB Database
              </span>
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-[#152720] text-[#71d2aa] border border-[#234737] flex items-center gap-1.5 font-medium">
                <span className={`w-2 h-2 rounded-full ${isError ? 'bg-[#ea837c]' : 'bg-[#71d2aa]'} animate-pulse`} /> {isError ? 'CONNECTION ERROR' : 'API STATUS'}
              </span>
            </div>
            <div className="text-xs text-[#788a91] font-mono mt-1">
              Database access is managed by the server
            </div>
          </div>
        </div>

        <div className="flex items-center gap-8 text-xs font-mono">
          <div>
            <span className="text-[#697c82] block text-[10px] uppercase font-semibold">TOTAL TABLES</span>
            <span className="text-[#e5ecea] font-bold text-base mt-0.5 block">{tables.length}</span>
          </div>
          <div>
            <span className="text-[#697c82] block text-[10px] uppercase font-semibold">TOTAL RECORDS</span>
            <span className="text-[#71d2aa] font-bold text-base mt-0.5 block">
              {totalRows.toLocaleString()}
            </span>
          </div>
          <div>
            <span className="text-[#697c82] block text-[10px] uppercase font-semibold">SSL PROTOCOL</span>
            <span className="text-[#84a9c9] font-bold text-base mt-0.5 block">TLSv1.3</span>
          </div>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-b border-[#1c272e] pb-3">
        <div className="relative w-full sm:w-96">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#65767c]" />
          <input
            type="text"
            placeholder="Search tables or views..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-[#10161b] border border-[#212c33] rounded-md text-xs text-[#dbe5e1] placeholder-[#5c6e75] focus:outline-none focus:border-[#437562]"
          />
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {(['ALL', 'BASE TABLE', 'VIEW'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-3 py-1.5 rounded-md text-xs font-mono transition font-medium ${
                filterType === type
                  ? 'bg-[#172720] text-[#86d9b2] border border-[#27483a]'
                  : 'bg-[#10161b] text-[#7a8c92] border border-[#1d272d] hover:text-[#e0ece8]'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Tables Grid */}
      {isLoading ? (
        <div className="panel py-20 text-center text-[#7e9096] text-xs font-mono">
          Loading database tables through QuantDB API...
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3.5">
          {filteredTables.map((tbl) => {
            const isView = tbl.type.toUpperCase() === 'VIEW';
            const isSelected = selectedTable === tbl.name;

            return (
              <div
                key={tbl.name}
                onClick={() => setSelectedTable(tbl.name)}
                className={`panel p-4 cursor-pointer hover:border-[#33483f] hover:bg-[#121c17] transition flex flex-col justify-between ${
                  isSelected ? 'border-[#427b62] bg-[#14241e]' : ''
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`text-[9px] font-mono px-2 py-0.5 rounded border uppercase font-medium ${
                        isView
                          ? 'bg-[#162029] text-[#79a1bf] border-[#223543]'
                          : 'bg-[#162720] text-[#71d2aa] border-[#244537]'
                      }`}
                    >
                      {tbl.type}
                    </span>
                    <TableIcon size={15} className={isSelected ? 'text-[#71d2aa]' : 'text-[#586b72]'} />
                  </div>

                  <h3 className="text-xs font-bold text-[#e2ede8] font-mono truncate mt-1" title={tbl.name}>
                    {tbl.name}
                  </h3>
                </div>

                <div className="flex items-center justify-between border-t border-[#1b252b] pt-3 mt-3.5 text-xs font-mono">
                  <span className="text-[#72848a]">
                    {tbl.row_count?.toLocaleString() ?? 0} rows
                  </span>
                  <span className="text-[#71d2aa] flex items-center gap-1 font-semibold text-[11px]">
                    Inspect <ChevronRight size={12} />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Selected Table Inspector Drawer / Panel */}
      {selectedTable && (
        <div className="panel mt-6 p-5">
          <div className="flex items-center justify-between border-b border-[#1f2b32] pb-3 mb-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#162720] border border-[#27483a] flex items-center justify-center text-[#71d2aa] flex-shrink-0">
                <FileSpreadsheet size={18} />
              </div>
              <div>
                <div className="flex items-center gap-2.5">
                  <h2 className="text-sm font-bold text-[#e6f0eb] font-mono">
                    `{selectedTable}`
                  </h2>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#10171d] text-[#7a8d94] border border-[#202c34]">
                    {displayRows.length} RECORDS DISPLAYED
                  </span>
                </div>
                <div className="text-xs text-[#73868d] mt-0.5">Rows fetched from the connected database.</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => rawQuery.refetch()}
                className="outline-button"
                title="Refresh rows"
              >
                <RefreshCw size={12} className={rawQuery.isFetching ? 'animate-spin' : ''} />
                <span>Refresh</span>
              </button>
              <button
                onClick={() => setSelectedTable(null)}
                className="icon-button"
                title="Close table preview"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {rawQuery.isLoading ? (
            <div className="py-14 text-center text-[#7e9096] text-xs font-mono">
              Fetching rows from MySQL...
            </div>
          ) : displayRows.length === 0 ? (
            <div className="py-14 text-center text-[#7e9096] text-xs font-mono">
              <Info size={24} className="mx-auto mb-2 opacity-40 text-[#71d2aa]" />
              <p>No records available for `{selectedTable}`.</p>
            </div>
          ) : (
            <div className="overflow-x-auto max-h-96 border border-[#1d2931] rounded-lg">
              <table className="w-full text-left text-xs font-mono divide-y divide-[#182329]">
                <thead className="bg-[#0b1015] sticky top-0">
                  <tr className="divide-x divide-[#182329] text-[#6d7f86] text-[10px] uppercase">
                    {columns.map((col) => (
                      <th key={col} className="py-2.5 px-3 whitespace-nowrap font-semibold">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#182329] bg-[#0d1419]">
                  {displayRows.map((row, idx) => (
                    <tr key={idx} className="divide-x divide-[#182329] hover:bg-[#121c22] transition">
                      {columns.map((col) => {
                        const val = row[col];
                        return (
                          <td
                            key={col}
                            className="py-2 px-3 whitespace-nowrap text-[#c9d7d3] max-w-xs truncate"
                            title={String(val ?? '')}
                          >
                            {val === null || val === undefined ? (
                              <span className="text-[#4e6067] italic">NULL</span>
                            ) : typeof val === 'object' ? (
                              JSON.stringify(val)
                            ) : (
                              String(val)
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div className="disclaimer">
        <ShieldCheck size={14} /> Database records are read by the API; connection credentials stay on the server.
      </div>
    </div>
  );
}

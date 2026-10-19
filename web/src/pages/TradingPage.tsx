import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
  AlertCircle,
  Clock,
  ShieldCheck,
  RefreshCw,
  Wallet,
  Layers,
  ArrowRightLeft,
} from 'lucide-react';
import { request } from '../lib/api';
import type { Portfolio, Security, Order, Trade } from '../types';

export function TradingPage() {
  const qc = useQueryClient();

  // Form states
  const [portfolioId, setPortfolioId] = useState<number>(0);
  const [securityId, setSecurityId] = useState<number>(0);
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [quantity, setQuantity] = useState<number>(10);
  const [price, setPrice] = useState<number>(0);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Queries
  const { data: portfolios = [] } = useQuery({
    queryKey: ['portfolios'],
    queryFn: () => request<Portfolio[]>('/portfolios'),
  });

  const { data: securities = [] } = useQuery({
    queryKey: ['securities'],
    queryFn: () => request<Security[]>('/securities'),
  });

  const rawOrders = useQuery({
    queryKey: ['orders'],
    queryFn: () => request<Order[]>('/orders'),
  });

  const rawTrades = useQuery({
    queryKey: ['trades'],
    queryFn: () => request<Trade[]>('/trades'),
  });

  const orders = rawOrders.data || [];
  const refetchOrders = rawOrders.refetch;
  const ordersFetching = rawOrders.isFetching;

  const trades = rawTrades.data || [];
  const refetchTrades = rawTrades.refetch;
  const tradesFetching = rawTrades.isFetching;

  const activePort = portfolios.find((p) => p.portfolio_id === portfolioId) || portfolios[0];
  const activeSec = securities.find((s) => s.security_id === securityId) || securities[0];
  React.useEffect(() => {
    if (portfolios.length && !portfolios.some((item) => item.portfolio_id === portfolioId)) setPortfolioId(portfolios[0].portfolio_id);
  }, [portfolios, portfolioId]);
  React.useEffect(() => {
    if (securities.length && !securities.some((item) => item.security_id === securityId)) setSecurityId(securities[0].security_id);
  }, [securities, securityId]);

  // Update default price when security changes
  React.useEffect(() => {
    if (activeSec && activeSec.base_price) {
      setPrice(Number(activeSec.base_price));
    }
  }, [activeSec]);

  const estimatedNotional = quantity * price;
  const estimatedFee = estimatedNotional * 0.0005; // 5 bps

  // Submit order mutation
  const submitOrder = useMutation({
    mutationFn: async () => {
      return request<Order>('/orders', {
        method: 'POST',
        body: JSON.stringify({
          portfolio_id: portfolioId,
          security_id: activeSec?.security_id,
          symbol: activeSec?.symbol,
          side,
          order_type: orderType,
          quantity: Number(quantity),
          price: Number(price),
        }),
      });
    },
    onSuccess: (data) => {
      setMessage({
        type: 'success',
        text: `Order #${data.order_id || 'NEW'} accepted by QuantDB. ${quantity} ${activeSec?.symbol} @ $${price.toFixed(2)}.`,
      });
      qc.invalidateQueries({ queryKey: ['orders'] });
      qc.invalidateQueries({ queryKey: ['trades'] });
      qc.invalidateQueries({ queryKey: ['portfolios'] });
      qc.invalidateQueries({ queryKey: ['overview'] });
    },
    onError: (err: Error) => {
      setMessage({
        type: 'error',
        text: err.message || 'Failed to submit order.',
      });
    },
  });

  const [activeTab, setActiveTab] = useState<'orders' | 'trades'>('orders');

  return (
    <div className="space-y-7">
      {/* Header */}
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <span className="pulse" />
            EXECUTION ENGINE <span className="eyebrow-sep">/</span> PAPER TRADING
          </div>
          <h1>Simulated Trading Desk & Order Blotter</h1>
          <p>
            Place simulated market and limit orders using the selected data provider.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              refetchOrders();
              refetchTrades();
            }}
            className="outline-button"
            title="Refresh order blotters"
          >
            <RefreshCw
              size={14}
              className={ordersFetching || tradesFetching ? 'animate-spin' : ''}
            />
            <span>Refresh Blotter</span>
          </button>
        </div>
      </div>

      {/* Two Column Layout: Order Ticket on Left, Blotters on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Order Entry Ticket (5 cols) */}
        <div className="lg:col-span-5 bg-[#11171C] border border-[#202B31] rounded-lg p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#1C252B] mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-[#F0F5F2] font-mono flex items-center gap-2">
                <Activity size={14} className="text-[#06B6D4]" />
                Order Entry Ticket
              </span>
              <span className="text-[10px] text-[#718087] font-mono">No Real Capital</span>
            </div>

            {/* Target Portfolio */}
            <div className="mb-4">
              <label className="text-[10px] font-mono uppercase text-[#718087] block mb-1">
                Target Portfolio
              </label>
              <select
                value={portfolioId}
                onChange={(e) => setPortfolioId(Number(e.target.value))}
                className="w-full bg-[#0B1015] border border-[#2A353A] rounded-md px-3 py-2 text-xs text-[#E5ECEA] font-mono focus:outline-none focus:border-[#06B6D4]"
              >
                {portfolios.map((p) => (
                  <option key={p.portfolio_id} value={p.portfolio_id}>
                    {p.portfolio_name} (Cash: ${Number(p.current_cash || 0).toLocaleString()})
                  </option>
                ))}
              </select>
              <div className="flex justify-between items-center text-[10px] text-[#6B7B81] mt-1 font-mono">
                <span>Available Cash / Power:</span>
                <span className="text-[#34D399] font-bold">
                  ${Number(activePort?.current_cash || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            {/* Instrument Selection */}
            <div className="mb-4">
              <label className="text-[10px] font-mono uppercase text-[#718087] block mb-1">
                Security Instrument
              </label>
              <select
                value={securityId}
                onChange={(e) => setSecurityId(Number(e.target.value))}
                className="w-full bg-[#0B1015] border border-[#2A353A] rounded-md px-3 py-2 text-xs text-[#E5ECEA] font-mono focus:outline-none focus:border-[#06B6D4]"
              >
                {securities.map((s) => (
                  <option key={s.security_id} value={s.security_id}>
                    {s.symbol} — {s.security_name} (${Number(s.base_price || 100).toFixed(2)})
                  </option>
                ))}
              </select>
            </div>

            {/* Side Buttons (BUY / SELL) */}
            <div className="mb-4">
              <label className="text-[10px] font-mono uppercase text-[#718087] block mb-1">
                Order Side
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setSide('BUY')}
                  className={`py-2 text-xs font-mono font-bold rounded-md transition ${
                    side === 'BUY'
                      ? 'bg-[#10B981] text-[#0B1015] shadow-lg shadow-[#10B981]/20'
                      : 'bg-[#17251F] text-[#76D2AE] border border-[#2A4E43]'
                  }`}
                >
                  ▲ BUY
                </button>
                <button
                  type="button"
                  onClick={() => setSide('SELL')}
                  className={`py-2 text-xs font-mono font-bold rounded-md transition ${
                    side === 'SELL'
                      ? 'bg-[#EF4444] text-[#0B1015] shadow-lg shadow-[#EF4444]/20'
                      : 'bg-[#291F1D] text-[#FB7185] border border-[#49302B]'
                  }`}
                >
                  ▼ SELL
                </button>
              </div>
            </div>

            {/* Order Type (MARKET / LIMIT) */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="text-[10px] font-mono uppercase text-[#718087] block mb-1">
                  Type
                </label>
                <select
                  value={orderType}
                  onChange={(e) => setOrderType(e.target.value as 'MARKET' | 'LIMIT')}
                  className="w-full bg-[#0B1015] border border-[#2A353A] rounded-md px-2.5 py-1.5 text-xs text-[#E5ECEA] font-mono focus:outline-none focus:border-[#06B6D4]"
                >
                  <option value="MARKET">MARKET</option>
                  <option value="LIMIT">LIMIT</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] font-mono uppercase text-[#718087] block mb-1">
                  Reference Price
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  disabled={orderType === 'MARKET'}
                  value={price}
                  onChange={(e) => setPrice(Number(e.target.value))}
                  className="w-full bg-[#0B1015] border border-[#2A353A] disabled:opacity-60 rounded-md px-2.5 py-1.5 text-xs text-[#E5ECEA] font-mono focus:outline-none focus:border-[#06B6D4]"
                />
              </div>
            </div>

            {/* Shares Quantity */}
            <div className="mb-4">
              <div className="flex justify-between items-center mb-1">
                <label className="text-[10px] font-mono uppercase text-[#718087]">Quantity (Shares)</label>
                <div className="flex gap-1">
                  {[10, 50, 100, 500].map((q) => (
                    <button
                      key={q}
                      type="button"
                      onClick={() => setQuantity(q)}
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                        quantity === q
                          ? 'bg-[#06B6D4] text-[#0B1015] font-bold'
                          : 'bg-[#1E293B] text-[#94A3B8] hover:text-[#E2E8F0]'
                      }`}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
              <input
                type="number"
                min="1"
                step="1"
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full bg-[#0B1015] border border-[#2A353A] rounded-md px-3 py-2 text-xs text-[#E5ECEA] font-mono focus:outline-none focus:border-[#06B6D4]"
              />
            </div>

            {/* Estimated Value & Summary Box */}
            <div className="bg-[#0B1015] border border-[#1E293B] rounded-md p-3 mb-4 space-y-1.5 font-mono text-xs">
              <div className="flex justify-between text-[#859396]">
                <span>Estimated Notional:</span>
                <span className="text-[#F0F5F2] font-bold">${estimatedNotional.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-[#859396]">
                <span>Simulated Fee (0.05%):</span>
                <span>${estimatedFee.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-[#859396] pt-1.5 border-t border-[#1E293B]">
                <span className="font-bold text-[#E5ECEA]">Total Cash Impact:</span>
                <span className="font-bold text-[#06B6D4]">
                  ${(estimatedNotional + estimatedFee).toFixed(2)}
                </span>
              </div>
            </div>

            {/* Submit Action */}
            <button
              onClick={() => {
                setMessage(null);
                submitOrder.mutate();
              }}
              disabled={submitOrder.isPending || !activePort || !activeSec || quantity <= 0 || price <= 0}
              className={`w-full py-3 rounded-md text-xs font-mono font-bold tracking-wider uppercase transition ${
                side === 'BUY'
                  ? 'bg-gradient-to-r from-[#10B981] to-[#059669] hover:from-[#34D399] hover:to-[#10B981] text-[#0B1015]'
                  : 'bg-gradient-to-r from-[#EF4444] to-[#DC2626] hover:from-[#F87171] hover:to-[#EF4444] text-[#FFFFFF]'
              }`}
            >
              {submitOrder.isPending ? 'Submitting paper order…' : `Submit ${side} Order`}
            </button>

            {message && (
              <div
                className={`mt-3 p-3 rounded-md text-xs font-mono flex items-start gap-2 ${
                  message.type === 'success'
                    ? 'bg-[#162A25] text-[#34D399] border border-[#2A4E43]'
                    : 'bg-[#291F1D] text-[#FB7185] border border-[#49302B]'
                }`}
              >
                {message.type === 'success' ? (
                  <CheckCircle2 size={15} className="flex-none mt-0.5" />
                ) : (
                  <AlertCircle size={15} className="flex-none mt-0.5" />
                )}
                <span>{message.text}</span>
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-[#1C252B] flex items-center gap-2 text-[10px] text-[#6B7B81]">
            <ShieldCheck size={13} className="text-[#38BDF8]" />
            <span>Simulated paper orders only. Triggers & constraints enforced in QuantDB.</span>
          </div>
        </div>

        {/* Right: Blotters & Execution History (7 cols) */}
        <div className="lg:col-span-7 bg-[#11171C] border border-[#202B31] rounded-lg p-5">
          {/* Blotter Tabs */}
          <div className="flex items-center justify-between pb-3 border-b border-[#1C252B] mb-4">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('orders')}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-semibold transition ${
                  activeTab === 'orders'
                    ? 'bg-[#1E293B] text-[#06B6D4] border border-[#334155]'
                    : 'text-[#718087] hover:text-[#E2E8F0]'
                }`}
              >
                Active Order Blotter ({orders.length})
              </button>
              <button
                onClick={() => setActiveTab('trades')}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-semibold transition ${
                  activeTab === 'trades'
                    ? 'bg-[#1E293B] text-[#06B6D4] border border-[#334155]'
                    : 'text-[#718087] hover:text-[#E2E8F0]'
                }`}
              >
                Executed Trade History ({trades.length})
              </button>
            </div>
            <span className="text-[10px] text-[#6B7B81] font-mono">
              Live from <code className="text-[#38BDF8]">{activeTab}</code>
            </span>
          </div>

          {/* Table Container */}
          <div className="overflow-x-auto min-h-[360px]">
            {activeTab === 'orders' ? (
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#1F2937] text-[10px] text-[#718087] uppercase tracking-wider">
                    <th className="py-2.5 px-3">Order ID</th>
                    <th className="py-2.5 px-3">Symbol</th>
                    <th className="py-2.5 px-3">Side</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3 text-right">Qty</th>
                    <th className="py-2.5 px-3 text-right">Price</th>
                    <th className="py-2.5 px-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#182126] text-[#DCE5E1]">
                  {orders.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-[#718087]">
                        No active orders recorded in database.
                      </td>
                    </tr>
                  ) : (
                    orders.slice().reverse().map((o, idx) => (
                      <tr key={o.order_id || idx} className="hover:bg-[#162026] transition">
                        <td className="py-2.5 px-3 text-[#38BDF8]">#{o.order_id}</td>
                        <td className="py-2.5 px-3 font-bold text-[#F0F5F2]">{o.symbol}</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                              o.side === 'BUY'
                                ? 'bg-[#162A25] text-[#34D399]'
                                : 'bg-[#291F1D] text-[#FB7185]'
                            }`}
                          >
                            {o.side}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-[#A6B5B3]">{o.order_type}</td>
                        <td className="py-2.5 px-3 text-right">{o.quantity}</td>
                        <td className="py-2.5 px-3 text-right">${Number(o.price || o.order_price || 0).toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-center">
                          <span className="px-2 py-0.5 rounded-full text-[9px] bg-[#1E293B] text-[#94A3B8]">
                            {o.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            ) : (
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#1F2937] text-[10px] text-[#718087] uppercase tracking-wider">
                    <th className="py-2.5 px-3">Trade ID</th>
                    <th className="py-2.5 px-3">Order Ref</th>
                    <th className="py-2.5 px-3">Symbol</th>
                    <th className="py-2.5 px-3">Side</th>
                    <th className="py-2.5 px-3 text-right">Shares</th>
                    <th className="py-2.5 px-3 text-right">Fill Price</th>
                    <th className="py-2.5 px-3 text-right">Realized P&L</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#182126] text-[#DCE5E1]">
                  {trades.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-[#718087]">
                        No executed trades recorded in database.
                      </td>
                    </tr>
                  ) : (
                    trades.slice().reverse().map((t, idx) => (
                      <tr key={t.trade_id || idx} className="hover:bg-[#162026] transition">
                        <td className="py-2.5 px-3 text-[#A77BBC]">#{t.trade_id}</td>
                        <td className="py-2.5 px-3 text-[#718087]">#{t.order_id}</td>
                        <td className="py-2.5 px-3 font-bold text-[#F0F5F2]">{t.symbol}</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                              t.side === 'BUY'
                                ? 'bg-[#162A25] text-[#34D399]'
                                : 'bg-[#291F1D] text-[#FB7185]'
                            }`}
                          >
                            {t.side}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right">{t.quantity}</td>
                        <td className="py-2.5 px-3 text-right text-[#F0F5F2]">
                          ${Number(t.execution_price).toFixed(2)}
                        </td>
                        <td
                          className={`py-2.5 px-3 text-right font-bold ${
                            Number(t.pnl || 0) >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'
                          }`}
                        >
                          {Number(t.pnl || 0) >= 0 ? '+' : ''}${Number(t.pnl || 0).toFixed(2)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
export default TradingPage;

export type Quote = {
  symbol: string;
  price?: number;
  close_price?: number;
  last_price?: number;
  open_price?: number;
  high_price?: number;
  low_price?: number;
  change_pct?: number;
  change?: number;
  volume?: number;
  bid?: number;
  ask?: number;
  timestamp?: string;
  name?: string;
  [key: string]: unknown;
};

export type Health = {
  data_mode?: string;
  database_latency_ms?: number | null;
  backend_status?: string;
  database_status?: string;
  quant_engine_status?: string;
  version?: string;
  connected?: boolean;
};

export type Security = {
  security_id: number;
  exchange_id: number;
  symbol: string;
  security_name: string;
  security_type: string;
  currency: string;
  status: string;
  base_price?: number;
  volatility?: number;
};

export type Exchange = {
  exchange_id: number;
  exchange_code: string;
  exchange_name: string;
  country: string;
  timezone: string;
};

export type MarketDataPoint = {
  market_data_id?: number;
  timestamp: string;
  security_id: number;
  symbol: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  bid_price?: number;
  ask_price?: number;
  spread?: number;
  mid_price?: number;
  relative_spread_bps?: number;
};

export type Portfolio = {
  portfolio_id: number;
  user_id?: number;
  portfolio_name: string;
  initial_capital: number;
  current_cash: number;
  portfolio_value?: number;
  total_equity?: number;
  total_pnl?: number;
  realized_pnl?: number;
  unrealized_pnl?: number;
  daily_return_pct?: number;
  sharpe_ratio?: number;
  status: string;
  created_at?: string;
};

export type Position = {
  position_id?: number;
  portfolio_id: number;
  security_id: number;
  symbol: string;
  security_name?: string;
  quantity: number;
  average_price: number;
  current_price?: number;
  market_value?: number;
  unrealized_pnl?: number;
  pnl_percentage?: number;
  weight_pct?: number;
};

export type Order = {
  order_id: number;
  portfolio_id?: number;
  security_id: number;
  symbol: string;
  timestamp?: string;
  order_time?: string;
  side: 'BUY' | 'SELL';
  order_type: 'MARKET' | 'LIMIT';
  quantity: number;
  price?: number;
  order_price?: number;
  status: string;
};

export type Trade = {
  trade_id: number;
  order_id: number;
  security_id: number;
  symbol: string;
  timestamp: string;
  trade_time?: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  execution_price: number;
  pnl?: number;
  transaction_cost?: number;
};

export type Strategy = {
  strategy_id: number;
  user_id: number;
  strategy_name: string;
  description: string;
  strategy_type: string;
  parameters: string | Record<string, unknown>;
  status: string;
  created_at: string;
};

export type RiskMetrics = {
  portfolio_id: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  annualized_volatility: number;
  beta_vs_sp500: number;
  var_95_daily: number;
  cvar_95_daily: number;
};

export type BacktestSummary = {
  backtest_id?: number;
  strategy_name?: string;
  symbol?: string;
  total_return_pct?: number;
  sharpe_ratio?: number;
  max_drawdown_pct?: number;
  win_rate_pct?: number;
  total_trades?: number;
  initial_capital?: number;
  final_capital?: number;
  profit_factor?: number;
  [key: string]: unknown;
};

export type TableMeta = {
  name: string;
  type: string;
  row_count: number;
};

export type OverviewData = {
  market: Quote[];
  portfolios: Portfolio[];
  health: Health;
  risk: Record<string, number>;
  backtest: BacktestSummary;
};

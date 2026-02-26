export interface AssetOut {
  id: string;
  symbol: string;
  name: string | null;
  asset_type: "stock" | "crypto" | "index";
  currency: string;
  last_updated: string | null;
  created_at: string | null;
}

export interface PriceOut {
  id: string;
  asset_id: string;
  timestamp: string;
  open_price: number | null;
  high_price: number | null;
  low_price: number | null;
  close_price: number;
  volume: number | null;
}

export interface SyncResponse {
  status: "success";
  message: string;
  symbol: string;
  rows_synced: number;
}

export interface ForecastRequest {
  symbol: string;
  interval?: "1wk" | "1mo";
  periods?: number;
  lookback_window?: number;
  epochs?: number;
  confidence_level?: number;
}

export interface ForecastResponse {
  symbol: string;
  interval: string;
  model: string;
  periods_ahead: number;
  forecast_horizon_label: string;
  data_points_used: number;
  dates: string[];
  point_forecast: number[];
  lower_bound: number[];
  upper_bound: number[];
  confidence_level: number;
  model_info: Record<string, any>;
}

export interface AnalyzeRequest {
  interval?: "1wk" | "1mo";
  periods?: number;
  model?: "base" | "lstm" | "prophet" | "chronos2" | "prophet_xgb";
  asset_type?: "stock" | "crypto" | "index";
  lookback_window?: number;
  epochs?: number;
  confidence_level?: number;
}

/** Forecast horizon: 1w, 2w, 3w, 4w ahead (used when interval is 1wk). */
export type ForecastHorizonWeeks = 1 | 2 | 3 | 4;

/** Error metrics from walk-forward 1-step backtest (last 20 weeks). */
export interface ModelMetricRow {
  model: string;
  mae: number;
  rmse: number;
  mape: number;
}

/** Forecast bounds (lower, point, upper) per model for the horizon. */
export interface ModelBoundsRow {
  model: string;
  lower: number[];
  forecast: number[];
  upper: number[];
}

export interface ForecastMetricsRequest {
  symbol: string;
  interval?: "1wk" | "1mo";
  last_n_weeks?: number;
  lookback_window?: number;
  epochs?: number;
  confidence_level?: number;
  /** Horizon for forecast bounds (same as chart selection, e.g. 1–4). */
  bounds_horizon_periods?: number;
  /** Models to run. Omit for fast default (base+prophet). Use all four for full comparison (slower). */
  models?: ("base" | "prophet" | "lstm" | "chronos2" | "prophet_xgb")[];
}

export interface ForecastMetricsResponse {
  symbol: string;
  interval: string;
  last_n_weeks: number;
  bounds_horizon_weeks: number;
  metrics: ModelMetricRow[];
  bounds: ModelBoundsRow[];
  error?: string | null;
}

export interface AnalyzeResponse extends ForecastResponse {
  sync: {
    performed: boolean;
    rows_synced: number;
    message: string;
  };
}

export interface PortfolioBaseRequest {
  symbols: string[];
  interval?: "1wk" | "1mo";
  risk_free_rate?: number;
  from_date?: string | null;
  to_date?: string | null;
}

export interface StatsRequest extends PortfolioBaseRequest {}

export interface OptimizeRequest extends PortfolioBaseRequest {
  target?: "max_sharpe" | "min_volatility" | "efficient_return" | "efficient_risk";
  target_return?: number | null;
  target_volatility?: number | null;
  n_frontier_points?: number;
}

export interface StatsResponse {
  symbols: string[];
  // Add specific fields based on backend response if needed
  [key: string]: any;
}

export interface OptimizeResponse {
  symbols: string[];
  weights: Record<string, number>;
  performance: {
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
  };
  efficient_frontier: Array<{
    volatility: number;
    expected_return: number;
    sharpe_ratio: number;
  }>;
  risk_metrics: {
    var_95: number;
    cvar_95: number;
    max_drawdown: number;
  };
  data_points_used: Record<string, number>;
  shared_data_points: number;
}

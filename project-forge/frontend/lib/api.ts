/** API client for Project Forge backend. */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'dev-key-change-in-production';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'X-API-KEY': API_KEY,
    'Content-Type': 'application/json',
  },
});

// Types
export interface ScenarioParams {
  entry_time_start: string;  // Start of entry time window
  entry_time_end: string;    // End of entry time window
  trade_end_time?: string;    // Trade window end time (defaults to 16:00:00)
  target_pts: number;
  stop_pts: number;
  direction?: 'bullish' | 'bearish' | null;
  year_start: number;
  year_end: number;
  // Trend filter parameters
  trend_enabled?: boolean;
  trend_timeframe?: string;
  trend_period?: number;
  trend_type?: 'sma' | 'ema';
  trend_strict?: boolean;
}

export interface BacktestRequest {
  scenarios: ScenarioParams[];
  strategy_text?: string;
  mode?: string;
}

export interface BacktestRunResponse {
  run_id: string;
  status: string;
  total_scenarios: number;
  created_at: string;
}

export interface BacktestRunStatus {
  run_id: string;
  status: string;
  total_scenarios: number;
  completed_scenarios: number;
  started_at?: string;
  finished_at?: string;
  created_at: string;
  strategy_text?: string;
  mode?: string;
  strategy_type?: string;
  scenario_params?: Record<string, any>;
  overall_win_rate?: number;  // Overall win rate percentage across all results
}

export interface BacktestResult {
  id: string;
  scenario_id: string;
  grouping: Record<string, any>;
  totals: {
    total_trades: number;
    wins: number;
    losses: number;
    timeouts: number;
  };
  kpis: {
    win_rate_percent: number;
    total_trades: number;
    wins: number;
    losses: number;
    timeouts: number;
    expectancy_r?: number;
    profit_factor?: number;
    avg_fvg_size?: number;
    avg_tp_pts?: number;
    avg_sl_pts?: number;
  };
}

export interface BacktestResultsResponse {
  run_id: string;
  results: BacktestResult[];
  total: number;
  page: number;
  page_size: number;
}

// API functions
export const backtestApi = {
  create: async (request: BacktestRequest): Promise<BacktestRunResponse> => {
    const response = await apiClient.post<BacktestRunResponse>('/backtests', request);
    return response.data;
  },
  
  list: async (limit: number = 50): Promise<BacktestRunStatus[]> => {
    const response = await apiClient.get<BacktestRunStatus[]>('/backtests', {
      params: { limit }
    });
    return response.data;
  },
  
  getStatus: async (runId: string): Promise<BacktestRunStatus> => {
    const response = await apiClient.get<BacktestRunStatus>(`/backtests/${runId}`);
    return response.data;
  },
  
  getResults: async (runId: string, page = 1, pageSize = 100): Promise<BacktestResultsResponse> => {
    const response = await apiClient.get<BacktestResultsResponse>(
      `/backtests/${runId}/results`,
      { params: { page, page_size: pageSize } }
    );
    return response.data;
  },
  
  getTrades: async (resultId: string): Promise<{ trades: any[], count: number }> => {
    const response = await apiClient.get(`/backtests/results/${resultId}/trades`);
    return response.data;
  },
  
  getRunningStatus: async (): Promise<{
    running_runs: Array<{
      run_id: string;
      status: string;
      progress: string;
      completed_scenarios: number;
      total_scenarios: number;
      created_at: string | null;
      started_at: string | null;
    }>;
    active_queries: Array<{
      pid: number;
      duration_seconds: number;
      query_preview: string;
      state: string;
    }>;
    total_running: number;
    total_queries: number;
  }> => {
    const response = await apiClient.get('/backtests/running/status');
    return response.data;
  },
  
  cancelRun: async (runId: string): Promise<{
    run_id: string;
    status: string;
    cancelled_scenarios: number;
    message: string;
  }> => {
    const response = await apiClient.post(`/backtests/${runId}/cancel`);
    return response.data;
  },
  
  cancelAllRunning: async (): Promise<{
    cancelled_runs: number;
    cancelled_scenarios: number;
    run_ids: string[];
    message: string;
  }> => {
    const response = await apiClient.post('/backtests/running/cancel-all');
    return response.data;
  },
  
  killAllQueries: async (): Promise<{
    killed_queries: number;
    pids: number[];
    message: string;
  }> => {
    const response = await apiClient.post('/backtests/queries/kill-all');
    return response.data;
  },
};

export interface GridSearchRequest {
  entry_time_starts: string[];
  entry_time_ends: string[];
  trade_end_times?: string[];
  target_pts_list: number[];
  stop_pts_list: number[];
  directions?: (string | null)[];
  year_start: number;
  year_end: number;
  // Trend filter parameters (optional, applied to all scenarios if enabled)
  trend_enabled?: boolean;
  trend_timeframe?: string;
  trend_period?: number;
  trend_type?: 'sma' | 'ema';
  trend_strict?: boolean;
}

export interface GridSearchResponse {
  scenarios: ScenarioParams[];
  total_combinations: number;
  valid_scenarios: number;
}

export const aiApi = {
  suggest: async (recentResults?: any[], context?: string, numScenarios: number = 10) => {
    const response = await apiClient.post('/ai/suggest', {
      recent_results: recentResults,
      context,
      num_scenarios: numScenarios,
    });
    return response.data;
  },
  
  explain: async (results: BacktestResult[], context?: string) => {
    const response = await apiClient.post('/ai/explain', {
      results,
      context,
    });
    return response.data;
  },
  
  grid: async (request: GridSearchRequest): Promise<GridSearchResponse> => {
    const response = await apiClient.post<GridSearchResponse>('/ai/grid', request);
    return response.data;
  },
  
  analyze: async (results: BacktestResult[], context?: string) => {
    const response = await apiClient.post('/ai/analyze', {
      results,
      context,
    });
    return response.data;
  },
};

// iFVG Strategy Types
export interface IFVGScenarioParams {
  fvg_timeframe: string;  // e.g., '5m', '15m', '30m', '1h'
  entry_timeframe: string;  // e.g., '1m', '5m'
  wait_candles: number;  // Number of FVG timeframe candles to wait for inversion
  use_adaptive_rr: boolean;  // Use adaptive RR (true) or fixed RR (false)
  target_pts?: number;  // Fixed target points (if use_adaptive_rr=false)
  stop_pts?: number;  // Fixed stop loss points (if use_adaptive_rr=false)
  extra_margin_pts: number;  // Extra margin beyond FVG boundary for adaptive SL
  rr_multiple: number;  // Risk-reward multiple for adaptive TP
  cutoff_time: string;  // Session cutoff time (HH:MM:SS)
  // Date range parameters (optional - date_start/date_end take precedence over year_start/year_end)
  year_start?: number;  // Start year (required if date_start not provided)
  year_end?: number;  // End year (required if date_end not provided)
  date_start?: string;  // Start date (YYYY-MM-DD) - optional, overrides year_start if provided
  date_end?: string;  // End date (YYYY-MM-DD) - optional, overrides year_end if provided
  // Time filter parameters (optional - if not provided, allow all times)
  time_start?: string;  // Start time filter (HH:MM:SS) in NY timezone - optional
  time_end?: string;  // End time filter (HH:MM:SS) in NY timezone - optional
  // Liquidity filter parameters
  liquidity_enabled?: boolean;  // Enable liquidity filter (only trade FVGs at swing highs/lows)
  liquidity_timeframe?: string;  // Timeframe for swing high/low detection (15m, 30m, 1h, 4h, 1d)
  swing_lookback?: number;  // Number of candles to look back/forward for swing detection
  tolerance_pts?: number;  // Price tolerance in points for matching FVG to swing level
}

export interface IFVGBacktestRequest {
  scenarios: IFVGScenarioParams[];
  strategy_text?: string;
  mode?: string;
}

export interface IFVGResultKPIs {
  total_trades: number;
  wins: number;
  losses: number;
  timeouts: number;
  win_rate_percent: number;
  avg_fvg_size?: number;
  avg_tp_pts?: number;
  avg_sl_pts?: number;
  expectancy_r?: number;
  profit_factor?: number;
}

export interface IFVGResult {
  id: string;
  scenario_id: string;
  grouping?: Record<string, any>;
  totals?: Record<string, any>;
  kpis: IFVGResultKPIs;
  created_at: string;
}

export interface IFVGResultsResponse {
  run_id: string;
  results: IFVGResult[];
  total_results: number;
}

// iFVG API
export const ifvgApi = {
  createBacktest: async (request: IFVGBacktestRequest): Promise<BacktestRunResponse> => {
    const response = await apiClient.post<BacktestRunResponse>('/ifvg/backtests', request);
    return response.data;
  },
  
  getStatus: async (runId: string): Promise<BacktestRunStatus> => {
    const response = await apiClient.get<BacktestRunStatus>(`/ifvg/backtests/${runId}/status`);
    return response.data;
  },
  
  getResults: async (runId: string): Promise<IFVGResultsResponse> => {
    const response = await apiClient.get<IFVGResultsResponse>(`/ifvg/backtests/${runId}/results`);
    return response.data;
  },
  
  getTradesForGroup: async (
    runId: string,
    filters: {
      fvg_timeframe?: string;
      entry_timeframe?: string;
      year?: number;
      month?: number;
      day_of_week?: number;
      direction?: string;
      use_adaptive_rr?: boolean;
    }
  ): Promise<{ trades: any[], count: number }> => {
    const params = new URLSearchParams();
    if (filters.fvg_timeframe) params.append('fvg_timeframe', filters.fvg_timeframe);
    if (filters.entry_timeframe) params.append('entry_timeframe', filters.entry_timeframe);
    if (filters.year !== undefined) params.append('year', filters.year.toString());
    if (filters.month !== undefined) params.append('month', filters.month.toString());
    if (filters.day_of_week !== undefined) params.append('day_of_week', filters.day_of_week.toString());
    if (filters.direction) params.append('direction', filters.direction);
    if (filters.use_adaptive_rr !== undefined) params.append('use_adaptive_rr', filters.use_adaptive_rr.toString());
    
    const response = await apiClient.get(`/ifvg/backtests/${runId}/trades?${params.toString()}`);
    return response.data;
  },
};

// Daily Scorecard Strategy Types
export interface DailyScorecardScenarioParams {
  year_start: number;  // Start year (default: 2020)
  year_end: number;  // End year (default: 2025)
  calendar_week?: number;  // Calendar week number (1-53). If not provided, uses current week.
}

export interface DailyScorecardBacktestRequest {
  scenarios: DailyScorecardScenarioParams[];
  strategy_text?: string;
  mode?: string;
}

export interface DailyScorecardWeeklyStats {
  total_weeks: number;
  bullish_count: number;
  bearish_count: number;
  bullish_percent: number;
  bearish_percent: number;
  total_weekly_change: number;
}

export interface DailyScorecardDailyStats {
  day_of_week: number;  // 0=Sunday, 1=Monday, ..., 6=Saturday
  day_name: string;
  total_days: number;
  bullish_count: number;
  bearish_count: number;
  bullish_percent: number;
  bearish_percent: number;
  avg_price_range: number;
  avg_bullish_high_time?: string;  // HH:MM:SS format
  avg_bullish_low_time?: string;  // HH:MM:SS format
  avg_bearish_high_time?: string;  // HH:MM:SS format
  avg_bearish_low_time?: string;  // HH:MM:SS format
}

export interface DailyScorecardResult {
  id: string;
  scenario_id: string;
  calendar_week: number;
  year_start: number;
  year_end: number;
  weekly_stats: DailyScorecardWeeklyStats;
  daily_stats: DailyScorecardDailyStats[];
  created_at: string;
}

export interface DailyScorecardResultsResponse {
  run_id: string;
  results: DailyScorecardResult[];
  total_results: number;
}

// Daily Scorecard API
export const dailyScorecardApi = {
  createBacktest: async (request: DailyScorecardBacktestRequest): Promise<BacktestRunResponse> => {
    const response = await apiClient.post<BacktestRunResponse>('/daily-scorecard/backtests', request);
    return response.data;
  },
  
  getStatus: async (runId: string): Promise<BacktestRunStatus> => {
    const response = await apiClient.get<BacktestRunStatus>(`/daily-scorecard/backtests/${runId}/status`);
    return response.data;
  },
  
  getResults: async (runId: string): Promise<DailyScorecardResultsResponse> => {
    const response = await apiClient.get<DailyScorecardResultsResponse>(`/daily-scorecard/backtests/${runId}/results`);
    return response.data;
  },
};


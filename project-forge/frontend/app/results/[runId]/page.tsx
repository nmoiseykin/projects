'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { backtestApi, aiApi, ifvgApi, dailyScorecardApi, type DailyScorecardResult } from '@/lib/api';

interface BacktestResult {
  id: string;
  grouping: Record<string, any>;
  totals: {
    total_trades: number;
    wins: number;
    losses: number;
    timeouts: number;
  };
  kpis: {
    win_rate_percent: number;
    expectancy_r?: number;
    profit_factor?: number;
    avg_fvg_size?: number;
    avg_tp_pts?: number;
    avg_sl_pts?: number;
  };
}

interface Trade {
  year: number;
  trading_date: string;
  day_of_week: number;
  day_name: string;
  entry_time: string;
  entry_price: number;
  target_price: number;
  stop_price: number;
  direction: string;
  outcome: string;
  trade_end_time: string;
  exit_time: string;
  exit_price: number | null;
  result_id?: string; // Store which result this trade came from
  // FVG details (for iFVG trades)
  fvg_timestamp?: string;
  fvg_direction?: string;
  gap_low?: number;
  gap_high?: number;
  fvg_size?: number;
  inversion_timestamp?: string;
  inversion_open_price?: number;
  inversion_close_price?: number;
  use_adaptive_rr?: boolean;
}

interface RunStatus {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_scenarios: number;
  completed_scenarios: number;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  strategy_text?: string;
  mode?: string;
  strategy_type?: string;
  scenario_params?: Record<string, any>;
}

interface GroupedResult {
  key: string;
  entry_time_start: string;
  entry_time_end: string;
  direction: string;
  target_pts: number;
  stop_pts: number;
  total_trades: number;
  wins: number;
  losses: number;
  timeouts: number;
  win_rate_percent: number;
  grouping?: Record<string, any>;
  kpis?: Record<string, any>;
}

// Helper function to get day of week from date string
function getDayOfWeek(dateStr: string | undefined): number | null {
  if (!dateStr) return null;
  try {
    const date = new Date(dateStr);
    // JavaScript: 0=Sunday, 6=Saturday. PostgreSQL DOW: 0=Sunday, 6=Saturday
    return date.getDay();
  } catch {
    return null;
  }
}

// Helper function to get day name from DOW number
function getDayName(dow: number): string {
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  return days[dow] || `Day ${dow}`;
}

function buildSimpleGroups(
  results: BacktestResult[], 
  strategyType?: string,
  groupByYear: boolean = true,
  groupByMonth: boolean = false,
  groupByDayOfWeek: boolean = false
): GroupedResult[] {
  const groups = new Map<string, {
    entry_time_start: string;
    entry_time_end: string;
    direction: string;
    target_pts: number;
    stop_pts: number;
    total_trades: number;
    wins: number;
    losses: number;
    timeouts: number;
    grouping?: Record<string, any>;
    kpis?: Record<string, any>;
  }>();

  // Filter results based on grouping options
  // For standard strategies, we need to filter by level and aggregate based on selected grouping
  let filteredResults = results;
  
  if (strategyType === 'ifvg') {
    // For iFVG, filter results based on grouping options
    if (groupByYear && groupByDayOfWeek) {
      // Need year_dow level (day of week grouped by year)
      filteredResults = results.filter(r => r.grouping?.level === 'year_dow' || r.grouping?.level === 'year_direction');
    } else if (groupByYear && groupByMonth) {
      // Need year_month level
      filteredResults = results.filter(r => r.grouping?.level === 'year_month');
    } else if (groupByYear) {
      // Need year level or any level with year
      filteredResults = results.filter(r => {
        const level = r.grouping?.level;
        return level === 'year' || level === 'year_direction' || level === 'year_dow' || level === 'year_month';
      });
    } else {
      // No year grouping - use all results
      filteredResults = results;
    }
  } else if (strategyType !== 'ifvg') {
    // Determine which level to use based on grouping options
    // YEAR is highest hierarchy, so we need the most granular level that includes all selected dimensions
    if (groupByYear && groupByMonth && groupByDayOfWeek) {
      // Need year_month_day level
      filteredResults = results.filter(r => r.grouping?.level === 'year_month_day');
    } else if (groupByYear && groupByMonth) {
      // Need year_month level
      filteredResults = results.filter(r => r.grouping?.level === 'year_month' || r.grouping?.level === 'year_month_day');
    } else if (groupByYear) {
      // Need year level or any level with year
      filteredResults = results.filter(r => {
        const level = r.grouping?.level;
        return level === 'year' || level === 'year_month' || level === 'year_month_day';
      });
    } else {
      // No year grouping - use most granular available
      filteredResults = results.filter(r => {
        const level = r.grouping?.level;
        return level === 'year_month_day' || !level;
      });
    }
  }

  console.log(`Filtering: ${results.length} total results -> ${filteredResults.length} filtered results`);

  // Aggregate results based on selected grouping options
  for (const result of filteredResults) {
    const grouping = result.grouping || {};
    
    if (strategyType === 'ifvg') {
      // For iFVG, group by fvg_timeframe, entry_timeframe, year, direction, use_adaptive_rr
      // Apply grouping filters
      const fvg_timeframe = grouping.fvg_timeframe || '';
      const entry_timeframe = grouping.entry_timeframe || '';
      const year = groupByYear ? (grouping.year || '') : '';
      const month = groupByMonth ? (grouping.month || '') : '';
      // For iFVG, day_of_week comes from the grouping if level is 'year_dow', otherwise try to get from trading_date
      const dow = groupByDayOfWeek ? (grouping.day_of_week !== undefined ? grouping.day_of_week : (getDayOfWeek(grouping.trading_date) ?? null)) : null;
      const direction = grouping.direction || '';
      const use_adaptive_rr = grouping.use_adaptive_rr ? 'adaptive' : 'fixed';
      
      // Build group key with selected dimensions (YEAR is highest hierarchy)
      const groupKeyParts = [fvg_timeframe, entry_timeframe];
      if (groupByYear) groupKeyParts.push(`Y${year}`);
      if (groupByMonth) groupKeyParts.push(`M${month}`);
      if (groupByDayOfWeek && dow !== null && dow !== undefined) groupKeyParts.push(`DOW${dow}`);
      groupKeyParts.push(direction, use_adaptive_rr);
      const groupKey = groupKeyParts.join('_');
      
      if (!groups.has(groupKey)) {
        groups.set(groupKey, {
          entry_time_start: '',
          entry_time_end: '',
          direction: direction,
          target_pts: 0,
          stop_pts: 0,
          total_trades: 0,
          wins: 0,
          losses: 0,
          timeouts: 0,
          grouping: { 
            ...grouping, 
            year: groupByYear ? grouping.year : undefined,
            month: groupByMonth ? grouping.month : undefined,
            day_of_week: groupByDayOfWeek && dow !== null && dow !== undefined ? dow : undefined,
          },
          kpis: result.kpis || {}
        });
      }
      
      const group = groups.get(groupKey)!;
      group.total_trades += result.totals?.total_trades || 0;
      group.wins += result.totals?.wins || 0;
      group.losses += result.totals?.losses || 0;
      group.timeouts += result.totals?.timeouts || 0;
      if (result.kpis) {
        group.kpis = result.kpis;
      }
    } else {
      // Standard strategy grouping
      const entry_time_start = grouping.entry_time_start || '';
      const entry_time_end = grouping.entry_time_end || '';
      const direction = grouping.direction || 'auto';
      const target_pts = grouping.target_pts || 0;
      const stop_pts = grouping.stop_pts || 0;
      
      // Build group key with selected dimensions (YEAR is highest hierarchy)
      const groupKeyParts = [entry_time_start, entry_time_end, direction, `TP${target_pts}`, `SL${stop_pts}`];
      
      if (groupByYear) {
        const year = grouping.year || '';
        groupKeyParts.push(`Y${year}`);
      }
      if (groupByMonth) {
        const month = grouping.month || '';
        groupKeyParts.push(`M${month}`);
      }
      if (groupByDayOfWeek) {
        const dow = getDayOfWeek(grouping.trading_date);
        if (dow !== null) {
          groupKeyParts.push(`DOW${dow}`);
        }
      }
      
      const groupKey = groupKeyParts.join('_');
      
      if (!groups.has(groupKey)) {
        groups.set(groupKey, {
          entry_time_start,
          entry_time_end,
          direction,
          target_pts,
          stop_pts,
          total_trades: 0,
          wins: 0,
          losses: 0,
          timeouts: 0,
          grouping: {
            ...grouping,
            year: groupByYear ? grouping.year : undefined,
            month: groupByMonth ? grouping.month : undefined,
            day_of_week: groupByDayOfWeek ? getDayOfWeek(grouping.trading_date) : undefined,
          },
        });
      }
      
      const group = groups.get(groupKey)!;
      const totals = result.totals || {};
      group.total_trades += totals.total_trades || 0;
      group.wins += totals.wins || 0;
      group.losses += totals.losses || 0;
      group.timeouts += totals.timeouts || 0;
    }
  }

  // Convert to array and calculate win rate, then sort by hierarchy (YEAR first, then MONTH, then DOW)
  return Array.from(groups.values())
    .map(group => ({
    key: strategyType === 'ifvg' 
        ? `${group.grouping?.fvg_timeframe}_${group.grouping?.entry_timeframe}_${group.grouping?.year || ''}_${group.direction}_${group.grouping?.use_adaptive_rr ? 'adaptive' : 'fixed'}`
      : `${group.entry_time_start}_${group.entry_time_end}_${group.direction}_${group.target_pts}_${group.stop_pts}`,
    entry_time_start: group.entry_time_start,
    entry_time_end: group.entry_time_end,
    direction: group.direction,
    target_pts: group.target_pts,
    stop_pts: group.stop_pts,
    total_trades: group.total_trades,
    wins: group.wins,
    losses: group.losses,
    timeouts: group.timeouts,
    win_rate_percent: group.total_trades > 0 ? (group.wins / group.total_trades) * 100 : 0,
    grouping: group.grouping,
    kpis: group.kpis,
    }))
    .sort((a, b) => {
      // Sort by hierarchy: YEAR (highest) -> MONTH -> DAY OF WEEK
      const aGroup = a.grouping || {};
      const bGroup = b.grouping || {};
      
      // Year comparison (if grouping by year) - applies to both standard and iFVG
      if (groupByYear) {
        const aYear = aGroup.year ?? 0;
        const bYear = bGroup.year ?? 0;
        if (aYear !== bYear) return aYear - bYear;
      }
      
      // Month comparison (if grouping by month)
      if (groupByMonth) {
        const aMonth = aGroup.month ?? 0;
        const bMonth = bGroup.month ?? 0;
        if (aMonth !== bMonth) return aMonth - bMonth;
      }
      
      // Day of week comparison (if grouping by DOW)
      if (groupByDayOfWeek) {
        const aDOW = aGroup.day_of_week ?? 0;
        const bDOW = bGroup.day_of_week ?? 0;
        if (aDOW !== bDOW) return aDOW - bDOW;
      }
      
      // For iFVG, also sort by direction and RR mode for consistency
      if (strategyType === 'ifvg') {
        const aDir = a.direction || '';
        const bDir = b.direction || '';
        if (aDir !== bDir) return aDir.localeCompare(bDir);
      }
      
      return 0;
    });
}

// HierarchicalResultRow removed - using simple grouping instead

// Helper function to format scenario parameters for display
function formatScenarioParams(params: Record<string, any> | undefined, strategyType?: string): string[] {
  if (!params) return [];
  
  const lines: string[] = [];
  
  if (strategyType === 'ifvg') {
    // iFVG parameters
    if (params.fvg_timeframe) lines.push(`FVG: ${params.fvg_timeframe}`);
    if (params.entry_timeframe) lines.push(`Entry: ${params.entry_timeframe}`);
    if (params.wait_candles) lines.push(`Wait Candles: ${params.wait_candles}`);
    if (params.use_adaptive_rr !== undefined) {
      lines.push(`RR: ${params.use_adaptive_rr ? 'Adaptive' : 'Fixed'}`);
      if (params.use_adaptive_rr) {
        if (params.extra_margin_pts) lines.push(`Margin: ${params.extra_margin_pts}pts`);
        if (params.rr_multiple) lines.push(`RR Multiple: ${params.rr_multiple}x`);
      } else {
        if (params.target_pts) lines.push(`TP: ${params.target_pts}pts`);
        if (params.stop_pts) lines.push(`SL: ${params.stop_pts}pts`);
      }
    }
    // Date range
    if (params.year_start && params.year_end) {
      lines.push(`Date Range: ${params.year_start}-${params.year_end}`);
    } else if (params.date_start && params.date_end) {
      lines.push(`Date Range: ${params.date_start} to ${params.date_end}`);
    }
    // Time range (when trades can be executed)
    if (params.time_start && params.time_end) {
      lines.push(`Time Range: ${params.time_start} - ${params.time_end}`);
    } else if (params.time_start) {
      lines.push(`Time Start: ${params.time_start}`);
    } else if (params.time_end) {
      lines.push(`Time End: ${params.time_end}`);
    }
    if (params.cutoff_time) lines.push(`Cutoff: ${params.cutoff_time}`);
    // Liquidity filter status (always show)
    if (params.liquidity_enabled) {
      lines.push(`Liquidity: ON`);
      if (params.liquidity_timeframe) lines.push(`Liquidity TF: ${params.liquidity_timeframe}`);
      if (params.swing_lookback) lines.push(`Swing Lookback: ${params.swing_lookback}`);
    } else {
      lines.push(`Liquidity: OFF`);
    }
  } else if (strategyType === 'daily_scorecard') {
    // Daily Scorecard parameters
    if (params.calendar_week) lines.push(`Calendar Week: ${params.calendar_week}`);
    if (params.year_start && params.year_end) {
      lines.push(`Date Range: ${params.year_start}-${params.year_end}`);
    }
  } else {
    // Standard strategy parameters
    // Date range
    if (params.year_start && params.year_end) {
      lines.push(`Date Range: ${params.year_start}-${params.year_end}`);
    } else if (params.date_start && params.date_end) {
      lines.push(`Date Range: ${params.date_start} to ${params.date_end}`);
    }
    // Entry time range
    if (params.entry_time_start && params.entry_time_end) {
      lines.push(`Entry Time: ${params.entry_time_start}-${params.entry_time_end}`);
    }
    if (params.trade_end_time) lines.push(`Trade End: ${params.trade_end_time}`);
    if (params.target_pts) lines.push(`TP: ${params.target_pts}pts`);
    if (params.stop_pts) lines.push(`SL: ${params.stop_pts}pts`);
    if (params.direction) lines.push(`Direction: ${params.direction}`);
  }
  
  return lines;
}

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const runId = params.runId as string;
  const isGrouped = (searchParams.get('group') ?? '1') !== '0';
  
  // Debug logging
  console.log('Results page - isGrouped:', isGrouped, 'group param:', searchParams.get('group'));
  
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null);
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const [groupedResults, setGroupedResults] = useState<GroupedResult[]>([]);
  
  // GROUP BY options state
  const [groupByYear, setGroupByYear] = useState(true); // YEAR is default and highest hierarchy
  const [groupByMonth, setGroupByMonth] = useState(false);
  const [groupByDayOfWeek, setGroupByDayOfWeek] = useState(false);
  const [tradesByResultId, setTradesByResultId] = useState<Map<string, Trade[]>>(new Map());
  const [tradesLoadingByResultId, setTradesLoadingByResultId] = useState<Map<string, boolean>>(new Map());
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  // Flat trades view state (when isGrouped === false)
  const [flatTrades, setFlatTrades] = useState<Trade[]>([]);
  const [flatLoading, setFlatLoading] = useState(false);
  const [flatLoadedCount, setFlatLoadedCount] = useState(0);
  const [flatNextIndex, setFlatNextIndex] = useState(0);
  const [flatLimit, setFlatLimit] = useState<number>(10); // Default limit: 10 trades
  const [dailyScorecardResults, setDailyScorecardResults] = useState<DailyScorecardResult[]>([]);
  const [flatSortKey, setFlatSortKey] = useState<'trading_date' | 'entry_time' | 'entry_price' | 'target_price' | 'stop_price' | 'exit_time' | 'exit_price' | 'outcome' | 'direction' | 'r_multiple'>('trading_date');
  const [flatSortDir, setFlatSortDir] = useState<'asc' | 'desc'>('asc');
  const toggleFlatSort = (key: typeof flatSortKey) => {
    if (flatSortKey === key) {
      setFlatSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setFlatSortKey(key);
      setFlatSortDir('asc');
    }
  };
  
  // Running status state
  const [runningStatus, setRunningStatus] = useState<{
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
  } | null>(null);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [exportingRow, setExportingRow] = useState<number | null>(null);
  
  // Export iFVG trades for a specific group row
  const exportIFVGTradesForGroup = async (grouping: Record<string, any>, rowIndex: number, result?: GroupedResult) => {
    if (!runId || runStatus?.strategy_type !== 'ifvg') return;
    
    setExportingRow(rowIndex);
    try {
      // Build filters from grouping
      const filters: {
        fvg_timeframe?: string;
        entry_timeframe?: string;
        year?: number;
        month?: number;
        day_of_week?: number;
        direction?: string;
        use_adaptive_rr?: boolean;
      } = {};
      
      if (grouping.fvg_timeframe) filters.fvg_timeframe = grouping.fvg_timeframe;
      if (grouping.entry_timeframe) filters.entry_timeframe = grouping.entry_timeframe;
      if (groupByYear && grouping.year !== undefined && grouping.year !== null) {
        filters.year = typeof grouping.year === 'number' ? grouping.year : parseInt(grouping.year);
      }
      if (groupByMonth && grouping.month !== undefined && grouping.month !== null) {
        filters.month = typeof grouping.month === 'number' ? grouping.month : parseInt(grouping.month);
      }
      if (groupByDayOfWeek && grouping.day_of_week !== undefined && grouping.day_of_week !== null) {
        filters.day_of_week = typeof grouping.day_of_week === 'number' ? grouping.day_of_week : parseInt(grouping.day_of_week);
      }
      // Direction can come from result or grouping
      if (result?.direction) {
        filters.direction = result.direction;
      } else if (grouping.direction && grouping.direction !== 'auto' && grouping.direction !== '-') {
        filters.direction = grouping.direction;
      }
      if (grouping.use_adaptive_rr !== undefined) {
        filters.use_adaptive_rr = grouping.use_adaptive_rr;
      }
      
      console.log('Export filters:', filters);
      console.log('Grouping data:', grouping);
      console.log('Result data:', result);
      
      const data = await ifvgApi.getTradesForGroup(runId, filters);
      const trades = data.trades || [];
      
      if (trades.length === 0) {
        alert(`No trades found for this group.\n\nFilters applied:\n${JSON.stringify(filters, null, 2)}\n\nPlease check that the grouping criteria match the data.`);
        return;
      }
      
      // Generate CSV
      const headers = [
        'Trading Date',
        'Entry Time',
        'Entry Price',
        'Target Price',
        'Stop Price',
        'Exit Time',
        'Exit Price',
        'Direction',
        'Outcome',
        'FVG Timestamp',
        'FVG Direction',
        'Gap Low',
        'Gap High',
        'FVG Size',
        'Inversion Timestamp',
        'Inversion Open Price',
        'Inversion Close Price',
        'Use Adaptive RR'
      ];
      
      const csvRows = [
        headers.join(','),
        ...trades.map((t: any) => {
          const formatPrice = (price: any) => {
            if (price === null || price === undefined) return 'N/A';
            return Number(price).toFixed(2);
          };
          
          const formatTime = (time: any) => {
            if (!time) return 'N/A';
            try {
              if (typeof time === 'string' && time.includes('T')) {
                return new Date(time).toLocaleString();
              }
              return String(time);
            } catch {
              return String(time);
            }
          };
          
          return [
            t.trading_date || 'N/A',
            t.entry_time || 'N/A',
            formatPrice(t.entry_price),
            formatPrice(t.target_price),
            formatPrice(t.stop_price),
            formatTime(t.exit_time),
            formatPrice(t.exit_price),
            t.direction || 'N/A',
            t.outcome || 'N/A',
            formatTime(t.fvg_timestamp),
            t.fvg_direction || 'N/A',
            formatPrice(t.gap_low),
            formatPrice(t.gap_high),
            formatPrice(t.fvg_size),
            formatTime(t.inversion_timestamp),
            formatPrice(t.inversion_open_price),
            formatPrice(t.inversion_close_price),
            t.use_adaptive_rr ? 'Yes' : 'No'
          ].map(field => {
            const str = String(field);
            if (str.includes(',') || str.includes('"') || str.includes('\n')) {
              return `"${str.replace(/"/g, '""')}"`;
            }
            return str;
          }).join(',');
        })
      ];
      
      const csvContent = csvRows.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      
      // Create filename with grouping info
      const filenameParts = [`ifvg_trades_${runId}`];
      if (filters.fvg_timeframe) filenameParts.push(`fvg${filters.fvg_timeframe}`);
      if (filters.entry_timeframe) filenameParts.push(`entry${filters.entry_timeframe}`);
      if (filters.year) filenameParts.push(`y${filters.year}`);
      if (filters.month) filenameParts.push(`m${filters.month}`);
      if (filters.day_of_week !== undefined) filenameParts.push(`dow${filters.day_of_week}`);
      if (filters.direction) filenameParts.push(filters.direction);
      
      link.setAttribute('download', `${filenameParts.join('_')}_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log(`Exported ${trades.length} iFVG trades to CSV`);
    } catch (error) {
      console.error('Error exporting iFVG trades:', error);
      alert('Failed to export trades. Please try again.');
    } finally {
      setExportingRow(null);
    }
  };
  
  // Export all loaded trades to CSV
  const exportToCSV = () => {
    if (flatTrades.length === 0) {
      alert('No trades to export. Please load trades first.');
      return;
    }
    
    // Get current run's result IDs to filter trades
    const currentRunResultIds = new Set(results.map(r => r.id));
    console.log('exportToCSV: current run has', currentRunResultIds.size, 'results');
    console.log('exportToCSV: total flatTrades before filtering:', flatTrades.length);
    
    // Filter trades to only include those from current run's results
    const currentRunTrades = flatTrades.filter((t: any) => {
      const belongsToCurrentRun = t.result_id && currentRunResultIds.has(t.result_id);
      if (!belongsToCurrentRun) {
        console.log('exportToCSV: filtering out trade from different run (result_id:', t.result_id, ')');
      }
      return belongsToCurrentRun;
    });
    
    console.log('exportToCSV: trades after filtering:', currentRunTrades.length);
    
    if (currentRunTrades.length === 0) {
      alert('No trades found for the current run. Please ensure trades are loaded.');
      return;
    }
    
    // Sort trades by current sort settings
    const sortedTrades = [...currentRunTrades].sort((a: any, b: any) => {
      const dir = flatSortDir === 'asc' ? 1 : -1;
      let av = (a as any)[flatSortKey];
      let bv = (b as any)[flatSortKey];
      if (flatSortKey.endsWith('time') || flatSortKey === 'trading_date') {
        const ad = av ? new Date(av).getTime() : 0;
        const bd = bv ? new Date(bv).getTime() : 0;
        return (ad - bd) * dir;
      }
      if (typeof av === 'number' && typeof bv === 'number') {
        return (av - bv) * dir;
      }
      return String(av ?? '').localeCompare(String(bv ?? '')) * dir;
    });
    
    // CSV headers
    const headers = [
      'Date',
      'Time',
      'Entry Price',
      'TP Price',
      'SL Price',
      'Exit Price',
      'Exit Time',
      'Direction',
      'Outcome',
      'R Multiple'
    ];
    
    // Convert trades to CSV rows
    const csvRows = [
      headers.join(','),
      ...sortedTrades.map(t => {
        const formatPrice = (price: any) => {
          if (price === null || price === undefined) return 'N/A';
          return Number(price).toFixed(2);
        };
        
        const formatTime = (time: any) => {
          if (!time) return 'N/A';
          try {
            return new Date(time).toLocaleTimeString();
          } catch {
            return String(time);
          }
        };
        
        const direction = t.direction === 'bullish' ? 'Bullish' : 
                         t.direction === 'bearish' ? 'Bearish' : 
                         t.direction || 'N/A';
        
        return [
          t.trading_date || 'N/A',
          t.entry_time || 'N/A',
          formatPrice(t.entry_price),
          formatPrice(t.target_price),
          formatPrice(t.stop_price),
          formatPrice(t.exit_price),
          formatTime(t.exit_time),
          direction,
          t.outcome || 'N/A',
          computeRMultiple(t).toFixed(2)
        ].map(field => {
          // Escape commas and quotes in CSV
          const str = String(field);
          if (str.includes(',') || str.includes('"') || str.includes('\n')) {
            return `"${str.replace(/"/g, '""')}"`;
          }
          return str;
        }).join(',');
      })
    ];
    
    // Create CSV content
    const csvContent = csvRows.join('\n');
    
    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `backtest_trades_${runId}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log(`Exported ${sortedTrades.length} trades to CSV`);
  };
  // Sorting for grouped results
  const [groupSortKey, setGroupSortKey] = useState<'entry_time_start' | 'direction' | 'target_pts' | 'stop_pts' | 'total_trades' | 'wins' | 'losses' | 'timeouts' | 'win_rate_percent'>('win_rate_percent');
  const [groupSortDir, setGroupSortDir] = useState<'asc' | 'desc'>('desc');
  
  const toggleGroupSort = (key: typeof groupSortKey) => {
    if (groupSortKey === key) {
      setGroupSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setGroupSortKey(key);
      setGroupSortDir('desc');
    }
  };
  
  // Export grouped results to CSV
  const exportGroupedToCSV = () => {
    if (groupedResults.length === 0) {
      alert('No grouped results to export.');
      return;
    }
    
    // Sort grouped results by current sort settings
    const sortedGroups = [...groupedResults].sort((a, b) => {
      const dir = groupSortDir === 'asc' ? 1 : -1;
      let av: any = a[groupSortKey];
      let bv: any = b[groupSortKey];
      
      if (typeof av === 'number' && typeof bv === 'number') {
        return (av - bv) * dir;
      }
      return String(av ?? '').localeCompare(String(bv ?? '')) * dir;
    });
    
    // CSV headers
    const headers = [
      'Entry Time Start',
      'Entry Time End',
      'Direction',
      'Take Profit',
      'Stop Loss',
      'Total Trades',
      'Wins',
      'Losses',
      'Timeouts',
      'Win %'
    ];
    
    // Convert groups to CSV rows
    const csvRows = [
      headers.join(','),
      ...sortedGroups.map(g => {
        const direction = g.direction === 'bullish' ? 'Bullish' : 
                         g.direction === 'bearish' ? 'Bearish' : 
                         g.direction || 'Auto';
        
        return [
          g.entry_time_start || 'N/A',
          g.entry_time_end || 'N/A',
          direction,
          g.target_pts.toFixed(2),
          g.stop_pts.toFixed(2),
          g.total_trades.toString(),
          g.wins.toString(),
          g.losses.toString(),
          g.timeouts.toString(),
          g.win_rate_percent.toFixed(2)
        ].map(field => {
          // Escape commas and quotes in CSV
          const str = String(field);
          if (str.includes(',') || str.includes('"') || str.includes('\n')) {
            return `"${str.replace(/"/g, '""')}"`;
          }
          return str;
        }).join(',');
      })
    ];
    
    // Create CSV content
    const csvContent = csvRows.join('\n');
    
    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `backtest_groups_${runId}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log(`Exported ${sortedGroups.length} grouped results to CSV`);
  };

  const handleAnalyzeWithAI = async () => {
    if (results.length === 0) {
      alert('No results available to analyze. Please wait for the backtest to complete.');
      return;
    }

    setAnalysisLoading(true);
    setShowAnalysis(true);
    try {
      const response = await aiApi.analyze(results, runStatus?.strategy_text || undefined);
      setAnalysis(response.analysis);
    } catch (err: any) {
      console.error('Error analyzing strategy:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || 'Unknown error';
      setAnalysis(`# Error\n\nFailed to analyze strategy: ${errorMessage}\n\nPlease check:\n1. OpenAI API key is set in .env\n2. Backend API is running\n3. Check browser console for details`);
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Fetch all paginated results to build a complete hierarchy
  async function fetchAllRunResults(runId: string): Promise<BacktestResult[]> {
    const pageSize = 5000; // large pages to minimize requests
    let page = 1;
    let all: BacktestResult[] = [];
    // Initial page to learn total
    const first = await backtestApi.getResults(runId, page, pageSize);
    all = first.results || [];
    const total = first.total || all.length;
    console.log(`Fetched page ${page} of results: ${all.length}/${total}`);
    while (all.length < total) {
      page += 1;
      const res = await backtestApi.getResults(runId, page, pageSize);
      all = all.concat(res.results || []);
      console.log(`Fetched page ${page}: ${all.length}/${total}`);
      // Safety: prevent runaway loops if server misreports
      if (page > 100) break;
    }
    return all;
  }

  useEffect(() => {
    if (results.length > 0) {
      try {
        if (isGrouped) {
          const groups = buildSimpleGroups(
            results, 
            runStatus?.strategy_type,
            groupByYear,
            groupByMonth,
            groupByDayOfWeek
          );
          setGroupedResults(groups);
          console.log(`Built ${groups.length} groups from ${results.length} results (Year: ${groupByYear}, Month: ${groupByMonth}, DOW: ${groupByDayOfWeek})`);
        } else {
          setGroupedResults([]);
        }
      } catch (error) {
        console.error('Error building groups:', error);
        setError(`Failed to build results groups: ${error}`);
      }
    } else {
      setGroupedResults([]);
    }
  }, [results, isGrouped, groupByYear, groupByMonth, groupByDayOfWeek, runStatus?.strategy_type]);
  
  // Track if we've already triggered initial load to prevent infinite loops
  const [flatTradesInitialized, setFlatTradesInitialized] = useState(false);
  
  // Separate effect to trigger flat trades loading when isGrouped changes to false
  useEffect(() => {
    if (!isGrouped && results.length > 0 && runStatus?.status === 'completed' && !flatTradesInitialized) {
      const dayResults = results.filter(r => r.grouping?.level === 'year_month_day');
      if (dayResults.length > 0) {
        setFlatTradesInitialized(true);
        setFlatTrades([]);
        setFlatLoadedCount(0);
        setFlatNextIndex(0);
        // Load initial batch immediately with higher batch size
        setTimeout(() => { 
          const batchSize = Math.min(flatLimit, 1000);
          loadMoreFlatTrades(batchSize); 
        }, 100);
      }
    }
    // Reset initialization flag if grouping changes back to true
    if (isGrouped && flatTradesInitialized) {
      setFlatTradesInitialized(false);
    }
  }, [isGrouped, results.length, runStatus?.status, flatTradesInitialized]);

  // Helper to compute R multiple for a trade (positive for win = TP/SL, -1 for loss, 0 for timeout)
  const computeRMultiple = (t: Trade): number => {
    const tpDist = Math.abs((t.target_price ?? 0) - t.entry_price);
    const slDist = Math.abs(t.entry_price - (t.stop_price ?? 0));
    const rr = slDist > 0 ? tpDist / slDist : 0;
    if (t.outcome === 'win') return rr;
    if (t.outcome === 'loss') return -1;
    return 0;
  };

  // Load flat trades from day-level result IDs, in batches to avoid blocking the UI
  const loadMoreFlatTrades = async (batchSize: number = 500, concurrency: number = 30) => {
    if (flatLoading) {
      return;
    }
    setFlatLoading(true);
    try {
      // Collect day-level result IDs - only from current run's results
      const dayResults = results.filter(r => r.grouping?.level === 'year_month_day');
      const slice = dayResults.slice(flatNextIndex, flatNextIndex + batchSize);
      if (slice.length === 0) {
        return;
      }
      
      let successCount = 0;
      let errorCount = 0;
      
      // Process in batches with higher concurrency for faster loading
      for (let i = 0; i < slice.length; i += concurrency) {
        const batch = slice.slice(i, i + concurrency);
        
        const batchPromises = batch.map(async (r) => {
          try {
            const data = await backtestApi.getTrades(r.id);
            const trades = (data.trades || []).map((t: Trade) => ({
              ...t,
              result_id: r.id,
              r_multiple: computeRMultiple(t),
            } as any));
            successCount++;
            return trades;
          } catch (e) {
            errorCount++;
            return [];
          }
        });
        
        try {
          const batchResults = await Promise.all(batchPromises);
          const batchTrades = batchResults.flat();
          
          // Update UI incrementally for better perceived performance (every batch)
          if (batchTrades.length > 0) {
            setFlatTrades(prev => {
              // Build existing keys from current state
              const existingKeys = new Set(prev.map(t => 
                `${t.trading_date || ''}_${t.entry_time || ''}_${t.entry_price || ''}_${t.direction || ''}`
              ));
              // Filter out duplicates
              const newTrades = batchTrades.filter(t => {
                const key = `${t.trading_date || ''}_${t.entry_time || ''}_${t.entry_price || ''}_${t.direction || ''}`;
                return !existingKeys.has(key);
              });
              return prev.concat(newTrades);
            });
          }
        } catch (e) {
          errorCount += batch.length;
        }
      }
      
      setFlatLoadedCount(prev => prev + slice.length);
      setFlatNextIndex(prev => prev + slice.length);
    } catch (error) {
      console.error('loadMoreFlatTrades: error', error);
    } finally {
      setFlatLoading(false);
    }
  };

  // Clear flat trades when runId changes
  useEffect(() => {
    if (runId) {
      setFlatTrades([]);
      setFlatLoadedCount(0);
      setFlatNextIndex(0);
      setFlatTradesInitialized(false);
    }
  }, [runId]);

  // Check running status periodically
  useEffect(() => {
    const checkRunningStatus = async () => {
      try {
        const status = await backtestApi.getRunningStatus();
        setRunningStatus(status);
      } catch (error) {
        console.error('Error checking running status:', error);
      }
    };

    // Check immediately
    checkRunningStatus();

    // Check every 5 seconds if there are running items
    const interval = setInterval(() => {
      checkRunningStatus();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Functions to handle killing/canceling
  const handleKillAllQueries = async () => {
    if (!confirm('Kill all active database queries? This may interrupt running backtests.')) {
      return;
    }
    
    setCheckingStatus(true);
    try {
      const result = await backtestApi.killAllQueries();
      alert(`✅ ${result.message}`);
      // Refresh status
      const status = await backtestApi.getRunningStatus();
      setRunningStatus(status);
    } catch (error: any) {
      alert(`Error: ${error?.response?.data?.detail || error?.message || 'Unknown error'}`);
    } finally {
      setCheckingStatus(false);
    }
  };

  const handleCancelAllRuns = async () => {
    if (!confirm('Cancel all running backtest runs? This cannot be undone.')) {
      return;
    }
    
    setCheckingStatus(true);
    try {
      const result = await backtestApi.cancelAllRunning();
      alert(`✅ ${result.message}`);
      // Refresh status
      const status = await backtestApi.getRunningStatus();
      setRunningStatus(status);
      // Refresh current run status if it was cancelled
      if (runId) {
        const updatedStatus = await backtestApi.getStatus(runId);
        setRunStatus(updatedStatus);
      }
    } catch (error: any) {
      alert(`Error: ${error?.response?.data?.detail || error?.message || 'Unknown error'}`);
    } finally {
      setCheckingStatus(false);
    }
  };

  const handleCancelRun = async (runIdToCancel: string) => {
    if (!confirm(`Cancel backtest run ${runIdToCancel.substring(0, 8)}...?`)) {
      return;
    }
    
    setCheckingStatus(true);
    try {
      const result = await backtestApi.cancelRun(runIdToCancel);
      alert(`✅ ${result.message}`);
      // Refresh status
      const status = await backtestApi.getRunningStatus();
      setRunningStatus(status);
      // Refresh current run status if it was cancelled
      if (runId === runIdToCancel) {
        const updatedStatus = await backtestApi.getStatus(runId);
        setRunStatus(updatedStatus);
      }
    } catch (error: any) {
      alert(`Error: ${error?.response?.data?.detail || error?.message || 'Unknown error'}`);
    } finally {
      setCheckingStatus(false);
    }
  };

  useEffect(() => {
    if (!runId) return;

    const fetchData = async () => {
      try {
        const status = await backtestApi.getStatus(runId);
        setRunStatus(status);

        if (status.status === 'completed') {
          try {
            // Load Daily Scorecard results if strategy type is daily_scorecard
            if (status.strategy_type === 'daily_scorecard') {
              const scorecardResults = await dailyScorecardApi.getResults(runId);
              setDailyScorecardResults(scorecardResults.results || []);
              console.log(`Fetched ${scorecardResults.results?.length || 0} Daily Scorecard results for run ${runId}`);
            } else {
              // Load standard/iFVG results
            const fetchedAll = await fetchAllRunResults(runId);
            setResults(fetchedAll);
            console.log(`Fetched ALL ${fetchedAll.length} results for run ${runId}`);
            if (fetchedAll.length === 0) {
              console.warn('No results found for completed run. This may indicate that SQL queries returned empty results for all scenarios.');
            }
            // Note: Flat trades loading is handled by the separate useEffect that watches isGrouped
            if (!isGrouped) {
              console.log('Grouping is OFF - flat trades will be loaded by useEffect. Day-level results:', fetchedAll.filter(r => r.grouping?.level === 'year_month_day').length);
            } else {
              console.log('Grouping is ON - will use hierarchical view');
              }
            }
          } catch (err: any) {
            console.error('Error fetching results:', err);
            setError(`Failed to fetch results: ${err?.response?.data?.detail || err?.message || 'Unknown error'}`);
          }
        }
        
        setError(null);
      } catch (err: any) {
        console.error('Error fetching data:', err);
        setError(err?.response?.data?.detail || err?.message || 'Failed to load results');
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    if (autoRefresh) {
      intervalRef.current = setInterval(async () => {
        try {
          const status = await backtestApi.getStatus(runId);
          const currentStatus = status.status;
          
          if (currentStatus === 'pending' || currentStatus === 'running') {
            setRunStatus(status);
            // Only fetch results if still running
            if (currentStatus === 'running') {
              const resultsData = await backtestApi.getResults(runId, 1, 1000);
              const fetchedResults = resultsData.results || [];
              setResults(prev => {
                // Only update if we got new results or if we had none before
                if (fetchedResults.length > 0 || prev.length === 0) {
                  return fetchedResults;
                }
                return prev; // Keep existing results
              });
            }
          } else {
            // Completed or failed - stop auto-refresh and ensure final results are loaded
            setRunStatus(status);
            setAutoRefresh(false); // Stop polling
            if (currentStatus === 'completed') {
              // Fetch ALL final results only once - use functional update to avoid stale closure
              const allResults = await fetchAllRunResults(runId);
              setResults(prev => {
                if (allResults.length > 0) {
                  return allResults;
                }
                return prev.length > 0 ? prev : allResults;
              });
            }
            // Clear interval immediately to stop further polling
            if (intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
          }
        } catch (err: any) {
          console.error('Error in auto-refresh:', err);
        }
      }, 3000);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      };
    }
  }, [runId, autoRefresh]);

  if (loading && !runStatus) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-7xl mx-auto">
          <div className="card-matrix p-8 text-center">
            <p className="text-matrix-green">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-7xl mx-auto">
          <div className="card-matrix p-8">
            <h1 className="text-2xl font-bold text-red-400 mb-4">Error</h1>
            <p className="text-neutral-400">{error}</p>
            <button
              onClick={() => router.push('/chat')}
              className="btn-matrix mt-4"
            >
              Back to Chat
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!runStatus) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-7xl mx-auto">
          <div className="card-matrix p-8">
            <h1 className="text-2xl font-bold text-red-400 mb-4">Run Not Found</h1>
            <p className="text-neutral-400">Backtest run {runId} not found.</p>
            <button
              onClick={() => router.push('/chat')}
              className="btn-matrix mt-4"
            >
              Back to Chat
            </button>
          </div>
        </div>
      </div>
    );
  }

  const isRunning = runStatus.status === 'pending' || runStatus.status === 'running';
  const progress = runStatus.total_scenarios > 0 
    ? (runStatus.completed_scenarios / runStatus.total_scenarios) * 100 
    : 0;

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-matrix-green">Backtest Results</h1>
          <div className="flex gap-4">
            {runStatus?.status === 'completed' && results.length > 0 && (
              <button
                onClick={handleAnalyzeWithAI}
                disabled={analysisLoading}
                className="px-4 py-2 bg-matrix-green/20 border border-matrix-green/50 text-matrix-green rounded hover:bg-matrix-green/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {analysisLoading ? '🤖 Analyzing...' : '🤖 Analyze with AI'}
              </button>
            )}
            {runStatus.strategy_type === 'ifvg' && (
              <button
                onClick={() => router.push('/strategies/ifvg')}
                className="px-4 py-2 bg-matrix-green/20 border border-matrix-green/50 text-matrix-green rounded hover:bg-matrix-green/30 transition-colors"
              >
                ⚙️ Back to iFVG Config
              </button>
            )}
            {runStatus.strategy_type === 'daily_scorecard' && (
              <button
                onClick={() => router.push('/strategies/daily-scorecard')}
                className="px-4 py-2 bg-matrix-green/20 border border-matrix-green/50 text-matrix-green rounded hover:bg-matrix-green/30 transition-colors"
              >
                ⚙️ Back to Daily Scorecard Config
              </button>
            )}
            <button
              onClick={() => router.push('/history')}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 text-neutral-200 rounded hover:bg-zinc-700 transition-colors"
            >
              📊 History
            </button>
            <button
              onClick={() => router.push('/chat')}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 text-neutral-200 rounded hover:bg-zinc-700 transition-colors"
            >
              ← Back to Chat
            </button>
          </div>
        </div>

        {/* Running Status Indicator */}
        {runningStatus && (runningStatus.total_running > 0 || runningStatus.total_queries > 0) && (
          <div className="card-matrix p-4 mb-6 border-2 border-yellow-500/50 bg-yellow-500/10">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-yellow-400 text-lg">⚠️</span>
                  <h3 className="text-lg font-semibold text-yellow-400">
                    Active Processes Running
                  </h3>
                </div>
                
                {runningStatus.total_running > 0 && (
                  <div className="mb-3">
                    <div className="text-sm text-neutral-300 mb-2">
                      <strong>{runningStatus.total_running}</strong> backtest run{runningStatus.total_running !== 1 ? 's' : ''} running:
                    </div>
                    <div className="space-y-2 ml-4">
                      {runningStatus.running_runs.map((run) => (
                        <div key={run.run_id} className="flex items-center justify-between p-2 bg-black/30 rounded">
                          <div className="flex-1">
                            <div className="text-xs text-neutral-400 font-mono">
                              {run.run_id.substring(0, 8)}...
                            </div>
                            <div className="text-sm text-neutral-200">
                              {run.progress} scenarios ({run.status})
                            </div>
                          </div>
                          <button
                            onClick={() => handleCancelRun(run.run_id)}
                            disabled={checkingStatus}
                            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors disabled:opacity-50"
                          >
                            Cancel
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {runningStatus.total_queries > 0 && (
                  <div className="mb-3">
                    <div className="text-sm text-neutral-300 mb-2">
                      <strong>{runningStatus.total_queries}</strong> active database quer{runningStatus.total_queries !== 1 ? 'ies' : 'y'}:
                    </div>
                    <div className="space-y-1 ml-4">
                      {runningStatus.active_queries.slice(0, 3).map((query) => {
                        const durationMin = Math.floor(query.duration_seconds / 60);
                        const durationSec = Math.floor(query.duration_seconds % 60);
                        return (
                          <div key={query.pid} className="text-xs text-neutral-400 p-2 bg-black/30 rounded">
                            PID {query.pid}: {durationMin}m {durationSec}s - {query.query_preview.substring(0, 80)}...
                          </div>
                        );
                      })}
                      {runningStatus.total_queries > 3 && (
                        <div className="text-xs text-neutral-500">
                          ... and {runningStatus.total_queries - 3} more
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
              
              <div className="flex flex-col gap-2 ml-4">
                {runningStatus.total_queries > 0 && (
                  <button
                    onClick={handleKillAllQueries}
                    disabled={checkingStatus}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors disabled:opacity-50 whitespace-nowrap"
                  >
                    🔪 Kill All Queries
                  </button>
                )}
                {runningStatus.total_running > 0 && (
                  <button
                    onClick={handleCancelAllRuns}
                    disabled={checkingStatus}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors disabled:opacity-50 whitespace-nowrap"
                  >
                    ❌ Cancel All Runs
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Run Status Card */}
        <div className="card-matrix p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-matrix-green mb-2">
                Run ID: {runId}
              </h2>
              {runStatus.strategy_text && (
                <div className="mb-4 p-4 bg-black/40 border border-matrix-green/30 rounded-lg">
                  <div className="text-xs text-matrix-green font-semibold mb-2 uppercase tracking-wide">Strategy Description</div>
                  <div className="text-sm text-neutral-200 leading-relaxed whitespace-pre-wrap">
                    {runStatus.strategy_text}
                  </div>
                </div>
              )}
              {runStatus.scenario_params && (
                <div className="mb-4 p-4 bg-black/30 border border-zinc-800 rounded-lg">
                  <div className="text-xs text-matrix-green font-semibold mb-2 uppercase tracking-wide">Strategy Parameters</div>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs text-neutral-300">
                    {formatScenarioParams(runStatus.scenario_params, runStatus.strategy_type).map((line, idx) => (
                      <div key={idx} className="font-mono">{line}</div>
                    ))}
                  </div>
                </div>
              )}
              <div className="text-sm text-neutral-400 space-y-1">
                <div>Status: <span className={`font-semibold ${
                  runStatus.status === 'completed' ? 'text-matrix-green' :
                  runStatus.status === 'failed' ? 'text-red-400' :
                  'text-yellow-400'
                }`}>{runStatus.status.toUpperCase()}</span></div>
                {runStatus.mode && (
                  <div>Mode: <span className="text-neutral-300">{runStatus.mode.toUpperCase()}</span></div>
                )}
                <div>Created: {new Date(runStatus.created_at).toLocaleString()}</div>
                {runStatus.started_at && (
                  <div>Started: {new Date(runStatus.started_at).toLocaleString()}</div>
                )}
                {runStatus.finished_at && (
                  <div>Finished: {new Date(runStatus.finished_at).toLocaleString()}</div>
                )}
              </div>
            </div>
            {isRunning && (
              <div className="text-right">
                <div className="text-sm text-neutral-400 mb-2">
                  {runStatus.completed_scenarios} / {runStatus.total_scenarios} scenarios
                </div>
                <div className="w-48 h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-matrix-green transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <div className="text-xs text-neutral-500 mt-1">
                  {autoRefresh ? 'Auto-refreshing...' : 'Paused'}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* GROUP BY Section - Show for all completed runs in grouped view, but not for Daily Scorecard */}
        {runStatus.status === 'completed' && isGrouped && runStatus.strategy_type !== 'daily_scorecard' && (
          <div className="card-matrix p-6 mb-6">
            <div className="text-sm font-semibold text-matrix-green mb-3">GROUP BY</div>
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={groupByYear}
                  onChange={(e) => {
                    const checked = e.target.checked;
                    setGroupByYear(checked);
                    if (!checked) {
                      // YEAR is highest hierarchy - uncheck MONTH and DOW if YEAR is unchecked
                      setGroupByMonth(false);
                      setGroupByDayOfWeek(false);
                    }
                  }}
                  className="w-4 h-4 text-matrix-green bg-black border-zinc-700 rounded focus:ring-matrix-green focus:ring-2"
                />
                <span className="text-sm text-neutral-300">YEAR</span>
                {groupByYear && <span className="text-xs text-matrix-green">(Highest)</span>}
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={groupByMonth}
                  onChange={(e) => setGroupByMonth(e.target.checked)}
                  disabled={!groupByYear}
                  className="w-4 h-4 text-matrix-green bg-black border-zinc-700 rounded focus:ring-matrix-green focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <span className={`text-sm ${groupByYear ? 'text-neutral-300' : 'text-neutral-500'}`}>MONTH</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={groupByDayOfWeek}
                  onChange={(e) => setGroupByDayOfWeek(e.target.checked)}
                  disabled={!groupByYear}
                  className="w-4 h-4 text-matrix-green bg-black border-zinc-700 rounded focus:ring-matrix-green focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <span className={`text-sm ${groupByYear ? 'text-neutral-300' : 'text-neutral-500'}`}>DAY OF WEEK</span>
              </label>
            </div>
            {!groupByYear && (
              <div className="mt-2 text-xs text-yellow-400">
                ⚠️ YEAR must be selected (highest hierarchy). MONTH and DAY OF WEEK require YEAR.
              </div>
            )}
            {runStatus.strategy_type === 'ifvg' && groupByDayOfWeek && (
              <div className="mt-2 text-xs text-blue-400">
                ℹ️ Day of week grouping for iFVG requires results with day_of_week data. If you see nulls, the backtest may need to be re-run to include day of week aggregation.
              </div>
            )}
          </div>
        )}

        {/* Results view - Simple Grouping */}
        {runStatus.status === 'completed' && isGrouped && runStatus.strategy_type !== 'ifvg' && runStatus.strategy_type !== 'daily_scorecard' && (
          <div className="card-matrix p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-matrix-green">
                Grouped Results
              </h2>
              <button
                onClick={exportGroupedToCSV}
                disabled={groupedResults.length === 0}
                className="px-3 py-1 text-sm bg-matrix-green/20 border border-matrix-green/50 text-matrix-green rounded hover:bg-matrix-green/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                📥 Export CSV ({groupedResults.length.toLocaleString()} groups)
              </button>
            </div>
            
            {groupedResults.length === 0 ? (
              <p className="text-neutral-400">No results available yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm font-mono">
                  <thead>
                    <tr className="border-b border-zinc-700 text-matrix-green">
                      {groupByYear && (
                        <th className="text-left p-3 cursor-pointer hover:text-matrix-cyan">
                          Year
                        </th>
                      )}
                      {groupByMonth && (
                        <th className="text-left p-3 cursor-pointer hover:text-matrix-cyan">
                          Month
                        </th>
                      )}
                      {groupByDayOfWeek && (
                        <th className="text-left p-3 cursor-pointer hover:text-matrix-cyan">
                          Day of Week
                        </th>
                      )}
                      <th className="text-left p-3 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleGroupSort('entry_time_start')}>
                        Entry Time {groupSortKey === 'entry_time_start' ? (groupSortDir === 'asc' ? '▲' : '▼') : ''}
                      </th>
                      <th className="text-left p-3 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleGroupSort('direction')}>
                        Direction {groupSortKey === 'direction' ? (groupSortDir === 'asc' ? '▲' : '▼') : ''}
                      </th>
                      <th className="text-right p-3 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleGroupSort('target_pts')}>
                        Take Profit {groupSortKey === 'target_pts' ? (groupSortDir === 'asc' ? '▲' : '▼') : ''}
                      </th>
                      <th className="text-right p-3 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleGroupSort('stop_pts')}>
                        Stop Loss {groupSortKey === 'stop_pts' ? (groupSortDir === 'asc' ? '▲' : '▼') : ''}
                      </th>
                      <th className="text-right p-3 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleGroupSort('total_trades')}>
                        Total Trades {groupSortKey === 'total_trades' ? (groupSortDir === 'asc' ? '▲' : '▼') : ''}
                      </th>
                      <th className="text-right p-3 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleGroupSort('wins')}>
                        Wins {groupSortKey === 'wins' ? (groupSortDir === 'asc' ? '▲' : '▼') : ''}
                      </th>
                      <th className="text-right p-3 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleGroupSort('losses')}>
                        Losses {groupSortKey === 'losses' ? (groupSortDir === 'asc' ? '▲' : '▼') : ''}
                      </th>
                      <th className="text-right p-3 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleGroupSort('timeouts')}>
                        Timeouts {groupSortKey === 'timeouts' ? (groupSortDir === 'asc' ? '▲' : '▼') : ''}
                      </th>
                      <th className="text-right p-3 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleGroupSort('win_rate_percent')}>
                        Win % {groupSortKey === 'win_rate_percent' ? (groupSortDir === 'asc' ? '▲' : '▼') : ''}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...groupedResults].sort((a, b) => {
                      const dir = groupSortDir === 'asc' ? 1 : -1;
                      let av: any = a[groupSortKey];
                      let bv: any = b[groupSortKey];
                      
                      if (typeof av === 'number' && typeof bv === 'number') {
                        return (av - bv) * dir;
                      }
                      return String(av ?? '').localeCompare(String(bv ?? '')) * dir;
                    }).map((group) => {
                      const grouping = group.grouping || {};
                      const monthNames = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                      
                      return (
                      <tr key={group.key} className="border-b border-zinc-800 hover:bg-zinc-900/50">
                          {groupByYear && (
                            <td className="p-3 text-neutral-300 font-semibold">
                              {grouping.year || '-'}
                            </td>
                          )}
                          {groupByMonth && (
                            <td className="p-3 text-neutral-300">
                              {grouping.month ? monthNames[grouping.month] || grouping.month : '-'}
                            </td>
                          )}
                          {groupByDayOfWeek && (
                            <td className="p-3 text-neutral-300">
                              {grouping.day_of_week !== undefined ? getDayName(grouping.day_of_week) : '-'}
                            </td>
                          )}
                        <td className="p-3 text-neutral-300">
                          {group.entry_time_start} - {group.entry_time_end}
                        </td>
                        <td className={`p-3 capitalize font-semibold ${
                          group.direction === 'bullish' ? 'text-matrix-green' : 
                          group.direction === 'bearish' ? 'text-red-400' : 
                          'text-neutral-300'
                        }`}>
                          {group.direction === 'bullish' ? 'Bullish' : 
                           group.direction === 'bearish' ? 'Bearish' : 
                           group.direction || 'Auto'}
                        </td>
                        <td className="p-3 text-right text-matrix-green">{group.target_pts.toFixed(2)}</td>
                        <td className="p-3 text-right text-red-400">{group.stop_pts.toFixed(2)}</td>
                        <td className="p-3 text-right text-neutral-300">{group.total_trades.toLocaleString()}</td>
                        <td className="p-3 text-right text-matrix-green">{group.wins.toLocaleString()}</td>
                        <td className="p-3 text-right text-red-400">{group.losses.toLocaleString()}</td>
                        <td className="p-3 text-right text-yellow-400">{group.timeouts.toLocaleString()}</td>
                        <td className={`p-3 text-right font-semibold ${
                          group.win_rate_percent >= 50 ? 'text-matrix-green' : 
                          group.win_rate_percent >= 40 ? 'text-yellow-400' : 
                          'text-red-400'
                        }`}>
                          {group.win_rate_percent.toFixed(2)}%
                        </td>
                      </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Flat Trades (ungrouped) */}
        {/* iFVG Results Display */}
        {runStatus.status === 'completed' && isGrouped && runStatus.strategy_type === 'ifvg' && (
          <div className="card-matrix p-6">
            <h2 className="text-xl font-semibold text-matrix-green mb-4">iFVG Results</h2>
            {groupedResults.length === 0 ? (
              <p className="text-neutral-500">No results available yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-700">
                      <th className="text-left p-2 text-sm text-neutral-400">FVG TF</th>
                      <th className="text-left p-2 text-sm text-neutral-400">Entry TF</th>
                      <th className="text-left p-2 text-sm text-neutral-400">RR Mode</th>
                      {groupByYear && (
                      <th className="text-left p-2 text-sm text-neutral-400">Year</th>
                      )}
                      {groupByMonth && (
                        <th className="text-left p-2 text-sm text-neutral-400">Month</th>
                      )}
                      {groupByDayOfWeek && (
                        <th className="text-left p-2 text-sm text-neutral-400">Day of Week</th>
                      )}
                      <th className="text-left p-2 text-sm text-neutral-400">Direction</th>
                      <th className="text-right p-2 text-sm text-neutral-400">Trades</th>
                      <th className="text-right p-2 text-sm text-neutral-400">Wins</th>
                      <th className="text-right p-2 text-sm text-neutral-400">Losses</th>
                      <th className="text-right p-2 text-sm text-neutral-400">Win %</th>
                      <th className="text-right p-2 text-sm text-neutral-400">Avg FVG Size</th>
                      <th className="text-right p-2 text-sm text-neutral-400">Avg TP</th>
                      <th className="text-right p-2 text-sm text-neutral-400">Avg SL</th>
                      <th className="text-right p-2 text-sm text-neutral-400">Expectancy R</th>
                      <th className="text-center p-2 text-sm text-neutral-400">Export</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groupedResults.map((result, idx) => {
                      const grouping = result.grouping || {};
                      const monthNames = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                      
                      return (
                      <tr key={idx} className="border-b border-zinc-800 hover:bg-zinc-900/50">
                          <td className="p-2 text-sm text-neutral-300">{grouping.fvg_timeframe || '-'}</td>
                          <td className="p-2 text-sm text-neutral-300">{grouping.entry_timeframe || '-'}</td>
                        <td className="p-2 text-sm text-neutral-300">
                            {grouping.use_adaptive_rr ? 'Adaptive' : 'Fixed'}
                        </td>
                          {groupByYear && (
                            <td className="p-2 text-sm text-neutral-300 font-semibold">
                              {grouping.year || '-'}
                            </td>
                          )}
                          {groupByMonth && (
                            <td className="p-2 text-sm text-neutral-300">
                              {grouping.month ? monthNames[grouping.month] || grouping.month : '-'}
                            </td>
                          )}
                          {groupByDayOfWeek && (
                            <td className="p-2 text-sm text-neutral-300">
                              {grouping.day_of_week !== undefined && grouping.day_of_week !== null 
                                ? getDayName(grouping.day_of_week) 
                                : '-'}
                            </td>
                          )}
                        <td className="p-2 text-sm text-neutral-300">{result.direction || '-'}</td>
                        <td className="p-2 text-sm text-neutral-300 text-right">{result.total_trades}</td>
                        <td className="p-2 text-sm text-neutral-300 text-right">{result.wins}</td>
                        <td className="p-2 text-sm text-neutral-300 text-right">{result.losses}</td>
                        <td className="p-2 text-sm text-neutral-300 text-right">
                          {result.win_rate_percent.toFixed(2)}%
                        </td>
                        <td className="p-2 text-sm text-neutral-300 text-right">
                          {result.kpis?.avg_fvg_size?.toFixed(2) || '-'}
                        </td>
                        <td className="p-2 text-sm text-neutral-300 text-right">
                          {result.kpis?.avg_tp_pts?.toFixed(2) || '-'}
                        </td>
                        <td className="p-2 text-sm text-neutral-300 text-right">
                          {result.kpis?.avg_sl_pts?.toFixed(2) || '-'}
                        </td>
                        <td className="p-2 text-sm text-neutral-300 text-right">
                          {result.kpis?.expectancy_r?.toFixed(4) || '-'}
                        </td>
                          <td className="p-2 text-center">
                            <button
                              onClick={() => exportIFVGTradesForGroup(grouping, idx, result)}
                              disabled={exportingRow === idx}
                              className="px-2 py-1 text-xs bg-matrix-green/20 border border-matrix-green/50 text-matrix-green rounded hover:bg-matrix-green/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                              title="Export trades for this group to CSV"
                            >
                              {exportingRow === idx ? '...' : '📥'}
                            </button>
                          </td>
                      </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Daily Scorecard Results Display */}
        {runStatus.status === 'completed' && runStatus.strategy_type === 'daily_scorecard' && dailyScorecardResults.length > 0 && (
          <div className="card-matrix p-6">
            <h2 className="text-xl font-semibold text-matrix-green mb-4">Daily Scorecard Results</h2>
            {dailyScorecardResults.map((result, idx) => (
              <div key={idx} className="mb-8">
                <div className="mb-4 p-4 bg-zinc-900 rounded border border-zinc-700">
                  <h3 className="text-lg font-semibold text-matrix-green mb-2">
                    Calendar Week {result.calendar_week} ({result.year_start}-{result.year_end})
                  </h3>
                  
                  {/* Weekly Stats */}
                  <div className="mb-6">
                    <h4 className="text-md font-semibold text-neutral-300 mb-3">Weekly Statistics</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      <div className="p-3 bg-zinc-800 rounded">
                        <div className="text-xs text-neutral-500">Total Weeks</div>
                        <div className="text-lg font-semibold text-neutral-200">{result.weekly_stats.total_weeks}</div>
                      </div>
                      <div className="p-3 bg-green-900/30 rounded border border-green-700/50">
                        <div className="text-xs text-green-400">Bullish %</div>
                        <div className="text-lg font-semibold text-green-300">{result.weekly_stats.bullish_percent.toFixed(2)}%</div>
                        <div className="text-xs text-neutral-500">({result.weekly_stats.bullish_count} weeks)</div>
                      </div>
                      <div className="p-3 bg-red-900/30 rounded border border-red-700/50">
                        <div className="text-xs text-red-400">Bearish %</div>
                        <div className="text-lg font-semibold text-red-300">{result.weekly_stats.bearish_percent.toFixed(2)}%</div>
                        <div className="text-xs text-neutral-500">({result.weekly_stats.bearish_count} weeks)</div>
                      </div>
                    </div>
                  </div>

                  {/* Daily Stats */}
                  <div>
                    <h4 className="text-md font-semibold text-neutral-300 mb-3">Daily Statistics by Day of Week</h4>
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse">
                        <thead>
                          <tr className="border-b border-zinc-700">
                            <th className="text-left p-2 text-sm text-neutral-400">Day</th>
                            <th className="text-right p-2 text-sm text-neutral-400">Total Days</th>
                            <th className="text-right p-2 text-sm text-neutral-400">Bullish %</th>
                            <th className="text-right p-2 text-sm text-neutral-400">Bearish %</th>
                            <th className="text-right p-2 text-sm text-neutral-400">Avg Range</th>
                            <th className="text-right p-2 text-sm text-neutral-400">Avg Bullish High Time</th>
                            <th className="text-right p-2 text-sm text-neutral-400">Avg Bullish Low Time</th>
                            <th className="text-right p-2 text-sm text-neutral-400">Avg Bearish High Time</th>
                            <th className="text-right p-2 text-sm text-neutral-400">Avg Bearish Low Time</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.daily_stats.map((daily, dayIdx) => (
                            <tr key={dayIdx} className="border-b border-zinc-800 hover:bg-zinc-900/50">
                              <td className="p-2 text-sm text-neutral-300 font-semibold">{daily.day_name}</td>
                              <td className="p-2 text-sm text-neutral-300 text-right">{daily.total_days}</td>
                              <td className="p-2 text-sm text-green-300 text-right">
                                {daily.bullish_percent.toFixed(2)}% ({daily.bullish_count})
                              </td>
                              <td className="p-2 text-sm text-red-300 text-right">
                                {daily.bearish_percent.toFixed(2)}% ({daily.bearish_count})
                              </td>
                              <td className="p-2 text-sm text-neutral-300 text-right">{daily.avg_price_range.toFixed(2)}</td>
                              <td className="p-2 text-sm text-neutral-300 text-right font-mono">
                                {daily.avg_bullish_high_time || '-'}
                              </td>
                              <td className="p-2 text-sm text-neutral-300 text-right font-mono">
                                {daily.avg_bullish_low_time || '-'}
                              </td>
                              <td className="p-2 text-sm text-neutral-300 text-right font-mono">
                                {daily.avg_bearish_high_time || '-'}
                              </td>
                              <td className="p-2 text-sm text-neutral-300 text-right font-mono">
                                {daily.avg_bearish_low_time || '-'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {runStatus.status === 'completed' && !isGrouped && (
          <div className="card-matrix p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-matrix-green">
                Flat Trades
              </h2>
              <div className="flex items-center gap-3">
                <label className="text-xs text-neutral-400 flex items-center gap-2">
                  Limit:
                  <select
                    value={flatLimit}
                    onChange={(e) => {
                      const newLimit = parseInt(e.target.value, 10);
                      setFlatLimit(newLimit);
                      // Reset and reload with new limit
                      setFlatTrades([]);
                      setFlatLoadedCount(0);
                      setFlatNextIndex(0);
                      setTimeout(() => {
                        const batchSize = Math.min(newLimit, 500);
                        loadMoreFlatTrades(batchSize);
                      }, 100);
                    }}
                    className="px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-xs focus:border-matrix-green focus:outline-none"
                    disabled={flatLoading}
                  >
                    <option value="100">100</option>
                    <option value="500">500</option>
                    <option value="1000">1,000</option>
                    <option value="2500">2,500</option>
                    <option value="5000">5,000</option>
                    <option value="10000">10,000</option>
                    <option value="999999">All</option>
                  </select>
                </label>
              </div>
            </div>
            {results.length === 0 ? (
              <p className="text-neutral-400">No results available yet.</p>
            ) : (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="text-xs text-neutral-500">
                    Showing: {Math.min(flatTrades.length, flatLimit)} / {flatTrades.length} loaded trades
                    {flatLimit < 999999 && ` (limit: ${flatLimit.toLocaleString()})`}
                    <span className="ml-3">
                      Day results loaded: {flatLoadedCount} / {results.filter(r => r.grouping?.level === 'year_month_day').length}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {flatTrades.length < flatLimit && flatLoadedCount < results.filter(r => r.grouping?.level === 'year_month_day').length && (
                      <button
                        onClick={() => {
                          const remaining = flatLimit - flatTrades.length;
                          const batchSize = Math.min(remaining, 500);
                          loadMoreFlatTrades(batchSize);
                        }}
                        disabled={flatLoading}
                        className="px-3 py-1 text-sm bg-zinc-800 border border-zinc-700 text-neutral-200 rounded hover:bg-zinc-700 transition-colors disabled:opacity-50"
                      >
                        {flatLoading ? 'Loading…' : `Load more (up to ${flatLimit.toLocaleString()})`}
                      </button>
                    )}
                    <button
                      onClick={() => { 
                        setFlatTrades([]); 
                        setFlatLoadedCount(0); 
                        setFlatNextIndex(0); 
                        const batchSize = Math.min(flatLimit, 500);
                        loadMoreFlatTrades(batchSize); 
                      }}
                      disabled={flatLoading}
                      className="px-3 py-1 text-sm bg-zinc-800 border border-zinc-700 text-neutral-200 rounded hover:bg-zinc-700 transition-colors disabled:opacity-50"
                    >
                      Reload
                    </button>
                    {runStatus.strategy_type !== 'daily_scorecard' && (
                      <button
                        onClick={exportToCSV}
                        disabled={flatTrades.length === 0}
                        className="px-3 py-1 text-sm bg-matrix-green/20 border border-matrix-green/50 text-matrix-green rounded hover:bg-matrix-green/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        📥 Export CSV ({flatTrades.length.toLocaleString()} trades)
                      </button>
                    )}
                  </div>
                </div>
                {flatTrades.length > 0 && (
                  <div className="mb-2 text-xs text-matrix-green">
                    Debug: Rendering {Math.min(flatTrades.length, flatLimit)} trades (flatTrades.length={flatTrades.length}, flatLimit={flatLimit})
                  </div>
                )}
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono">
                    <thead>
                      <tr className="border-b border-zinc-700 text-matrix-green">
                        <th className="text-left p-2 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleFlatSort('trading_date')}>Date {flatSortKey==='trading_date' ? (flatSortDir==='asc'?'▲':'▼') : ''}</th>
                        <th className="text-left p-2 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleFlatSort('entry_time')}>Time {flatSortKey==='entry_time' ? (flatSortDir==='asc'?'▲':'▼') : ''}</th>
                        <th className="text-right p-2 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleFlatSort('entry_price')}>Entry</th>
                        <th className="text-right p-2 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleFlatSort('target_price')}>TP Price</th>
                        <th className="text-right p-2 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleFlatSort('stop_price')}>SL Price</th>
                        <th className="text-right p-2 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleFlatSort('exit_price')}>Exit Price</th>
                        <th className="text-left p-2 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleFlatSort('exit_time')}>Exit Time</th>
                        <th className="text-left p-2 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleFlatSort('direction')}>Direction {flatSortKey==='direction' ? (flatSortDir==='asc'?'▲':'▼') : ''}</th>
                        <th className="text-left p-2 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleFlatSort('outcome')}>Outcome</th>
                        <th className="text-right p-2 cursor-pointer hover:text-matrix-cyan" onClick={() => toggleFlatSort('r_multiple')}>R</th>
                      </tr>
                    </thead>
                    <tbody>
                      {flatTrades.length === 0 ? (
                        <tr>
                          <td colSpan={10} className="p-4 text-center text-neutral-500 text-sm">
                            {flatLoading ? 'Loading trades...' : 'No trades loaded. Click "Load more" to fetch trades.'}
                          </td>
                        </tr>
                      ) : (
                        [...flatTrades]
                          .slice(0, flatLimit) // Apply limit to displayed trades
                          .sort((a: any, b: any) => {
                        const dir = flatSortDir === 'asc' ? 1 : -1;
                        let av = (a as any)[flatSortKey];
                        let bv = (b as any)[flatSortKey];
                        if (flatSortKey.endsWith('time') || flatSortKey === 'trading_date') {
                          const ad = av ? new Date(av).getTime() : 0;
                          const bd = bv ? new Date(bv).getTime() : 0;
                          return (ad - bd) * dir;
                        }
                        if (typeof av === 'number' && typeof bv === 'number') {
                          return (av - bv) * dir;
                        }
                        return String(av ?? '').localeCompare(String(bv ?? '')) * dir;
                      }).map((t, i) => {
                        try {
                          return (
                            <tr key={i} className="border-b border-zinc-800 hover:bg-zinc-900/50">
                              <td className="p-2 text-neutral-300">{t.trading_date || 'N/A'}</td>
                              <td className="p-2 text-neutral-300">{t.entry_time || 'N/A'}</td>
                              <td className="p-2 text-right text-neutral-300">
                                {t.entry_price !== null && t.entry_price !== undefined ? Number(t.entry_price).toFixed(2) : 'N/A'}
                              </td>
                              <td className="p-2 text-right text-matrix-green">
                                {t.target_price !== null && t.target_price !== undefined ? Number(t.target_price).toFixed(2) : 'N/A'}
                              </td>
                              <td className="p-2 text-right text-red-400">
                                {t.stop_price !== null && t.stop_price !== undefined ? Number(t.stop_price).toFixed(2) : 'N/A'}
                              </td>
                              <td className={`p-2 text-right ${t.exit_price !== null && t.exit_price !== undefined ? (t.outcome === 'win' ? 'text-matrix-green' : t.outcome === 'loss' ? 'text-red-400' : 'text-neutral-300') : 'text-neutral-500'}`}>
                                {t.exit_price !== null && t.exit_price !== undefined ? Number(t.exit_price).toFixed(2) : 'N/A'}
                              </td>
                              <td className="p-2 text-neutral-300">{t.exit_time ? new Date(t.exit_time).toLocaleTimeString() : 'N/A'}</td>
                              <td className={`p-2 capitalize font-semibold ${
                                t.direction === 'bullish' ? 'text-matrix-green' : 
                                t.direction === 'bearish' ? 'text-red-400' : 
                                'text-neutral-300'
                              }`}>
                                {t.direction === 'bullish' ? 'Bullish' : 
                                 t.direction === 'bearish' ? 'Bearish' : 
                                 t.direction || 'N/A'}
                              </td>
                              <td className={`p-2 capitalize ${t.outcome === 'win' ? 'text-matrix-green' : t.outcome === 'loss' ? 'text-red-400' : 'text-yellow-400'}`}>{t.outcome || 'N/A'}</td>
                              <td className={`p-2 text-right ${computeRMultiple(t) >= 0 ? 'text-matrix-green' : 'text-red-400'}`}>
                                {computeRMultiple(t).toFixed(2)}
                              </td>
                            </tr>
                          );
                        } catch (err) {
                          console.error('Error rendering trade row:', err, t);
                          return (
                            <tr key={i} className="border-b border-zinc-800">
                              <td colSpan={10} className="p-2 text-red-400 text-xs">
                                Error rendering trade: {err instanceof Error ? err.message : String(err)}
                              </td>
                            </tr>
                          );
                        }
                      })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {runStatus.status === 'failed' && (
          <div className="card-matrix p-6">
            <h2 className="text-xl font-semibold text-red-400 mb-4">Backtest Failed</h2>
            <p className="text-neutral-400">
              The backtest run encountered an error. Please check the logs or try again.
            </p>
          </div>
        )}

        {/* AI Analysis Modal */}
        {showAnalysis && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setShowAnalysis(false)}>
            <div className="card-matrix p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-matrix-green">AI Strategy Analysis</h2>
                <button
                  onClick={() => setShowAnalysis(false)}
                  className="px-3 py-1 bg-zinc-800 border border-zinc-700 text-neutral-200 rounded hover:bg-zinc-700 transition-colors"
                >
                  ✕ Close
                </button>
              </div>
              
              {analysisLoading ? (
                <div className="text-center py-8">
                  <p className="text-matrix-green">Analyzing strategy with AI...</p>
                  <p className="text-neutral-400 text-sm mt-2">This may take a moment</p>
                </div>
              ) : analysis ? (
                <div className="prose prose-invert max-w-none">
                  <div 
                    className="text-neutral-300 whitespace-pre-wrap"
                    dangerouslySetInnerHTML={{ 
                      __html: analysis
                        .replace(/\n/g, '<br>')
                        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-matrix-green">$1</strong>')
                        .replace(/\*(.*?)\*/g, '<em>$1</em>')
                        .replace(/^### (.*$)/gm, '<h3 class="text-xl font-bold text-matrix-green mt-4 mb-2">$1</h3>')
                        .replace(/^## (.*$)/gm, '<h2 class="text-2xl font-bold text-matrix-green mt-6 mb-3">$1</h2>')
                        .replace(/^# (.*$)/gm, '<h1 class="text-3xl font-bold text-matrix-green mt-8 mb-4">$1</h1>')
                        .replace(/^- (.*$)/gm, '<li class="ml-4">$1</li>')
                        .replace(/(<li.*<\/li>)/g, '<ul class="list-disc list-inside mb-2">$1</ul>')
                    }}
                  />
                </div>
              ) : (
                <div className="text-neutral-400">No analysis available</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


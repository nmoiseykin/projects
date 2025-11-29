'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ifvgApi, type IFVGScenarioParams, type BacktestRunStatus } from '@/lib/api';

export default function IFVGPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [history, setHistory] = useState<BacktestRunStatus[]>([]);
  
  // iFVG parameters
  const [params, setParams] = useState<IFVGScenarioParams>({
    fvg_timeframe: '5m',
    entry_timeframe: '1m',
    wait_candles: 24,
    use_adaptive_rr: true,
    target_pts: 60,
    stop_pts: 30,
    extra_margin_pts: 5.0,
    rr_multiple: 2.0,
    cutoff_time: '16:00:00',
    year_start: 2020,
    year_end: 2025,
    date_start: undefined,
    date_end: undefined,
    time_start: undefined,
    time_end: undefined,
    liquidity_enabled: false,
    liquidity_timeframe: '15m',
    swing_lookback: 5,
    tolerance_pts: 5.0,
  });

  // Load history
  useEffect(() => {
    const loadHistory = async () => {
      try {
        console.log('Loading iFVG history...');
        // For now, use backtestApi.list and filter by strategy_type
        const { backtestApi } = await import('@/lib/api');
        console.log('Calling backtestApi.list(100)...');
        const allRuns = await backtestApi.list(100);
        console.log('Received runs:', allRuns.length, allRuns);
        const ifvgRuns = allRuns.filter(r => r.strategy_type === 'ifvg');
        console.log('Filtered iFVG runs:', ifvgRuns.length, ifvgRuns);
        setHistory(ifvgRuns as any);
      } catch (error: any) {
        console.error('Error loading history:', error);
        console.error('Error details:', error?.response?.data || error?.message);
        // Set empty array on error so UI doesn't show "No runs" incorrectly
        setHistory([]);
      }
    };
    loadHistory();
  }, []);

  const handleRunBacktest = async () => {
    setLoading(true);
    try {
      const response = await ifvgApi.createBacktest({
        scenarios: [params]
      });
      
      if (!response || !response.run_id) {
        throw new Error('Invalid response from server: missing run_id');
      }
      
      setRunId(response.run_id);
      
      // Redirect immediately - use router.push with replace to avoid back button issues
      router.push(`/results/${response.run_id}`);
      router.refresh(); // Force refresh to ensure navigation happens
    } catch (error: any) {
      console.error('Error creating iFVG backtest:', error);
      setLoading(false);
      alert(`Error: ${error?.response?.data?.detail || error?.message || 'Unknown error'}`);
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-matrix-green">iFVG Reversal Strategy</h1>
          <button
            onClick={() => router.push('/strategies')}
            className="px-4 py-2 bg-zinc-800 border border-zinc-700 text-neutral-200 rounded hover:bg-zinc-700 transition-colors"
          >
            ← Back to Strategies
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Configuration Form */}
          <div className="card-matrix p-6 space-y-6">
            <h2 className="text-xl font-semibold text-matrix-green mb-4">Configuration</h2>
            
            {/* FVG Timeframe */}
            <div>
              <label className="block text-sm text-neutral-300 mb-2">FVG Timeframe</label>
              <select
                value={params.fvg_timeframe}
                onChange={(e) => setParams({ ...params, fvg_timeframe: e.target.value })}
                className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
              >
                <option value="5m">5m</option>
                <option value="15m">15m</option>
                <option value="30m">30m</option>
                <option value="1h">1h</option>
              </select>
            </div>

            {/* Entry Timeframe */}
            <div>
              <label className="block text-sm text-neutral-300 mb-2">Entry Timeframe</label>
              <select
                value={params.entry_timeframe}
                onChange={(e) => setParams({ ...params, entry_timeframe: e.target.value })}
                className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
              >
                <option value="1m">1m</option>
                <option value="5m">5m</option>
              </select>
            </div>

            {/* Wait Candles */}
            <div>
              <label className="block text-sm text-neutral-300 mb-2">Wait Candles</label>
              <input
                type="number"
                value={params.wait_candles}
                onChange={(e) => setParams({ ...params, wait_candles: parseInt(e.target.value) || 24 })}
                className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                min="1"
              />
              <p className="text-xs text-neutral-500 mt-1">Number of FVG timeframe candles to wait for inversion</p>
            </div>

            {/* RR Mode Toggle */}
            <div>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={params.use_adaptive_rr}
                  onChange={(e) => setParams({ ...params, use_adaptive_rr: e.target.checked })}
                  className="w-5 h-5 text-matrix-green bg-black border-zinc-700 rounded focus:ring-matrix-green focus:ring-2"
                />
                <span className="text-sm text-neutral-300 font-medium">
                  Use Adaptive RR (based on FVG size)
                </span>
              </label>
            </div>

            {/* Fixed Mode Parameters */}
            {!params.use_adaptive_rr && (
              <div className="space-y-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded">
                <h3 className="text-sm font-semibold text-neutral-300">Fixed RR Mode</h3>
                
                <div>
                  <label className="block text-sm text-neutral-300 mb-2">Target Points</label>
                  <input
                    type="number"
                    value={params.target_pts || ''}
                    onChange={(e) => setParams({ ...params, target_pts: parseFloat(e.target.value) || undefined })}
                    className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                    step="0.1"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm text-neutral-300 mb-2">Stop Loss Points</label>
                  <input
                    type="number"
                    value={params.stop_pts || ''}
                    onChange={(e) => setParams({ ...params, stop_pts: parseFloat(e.target.value) || undefined })}
                    className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                    step="0.1"
                    min="0"
                  />
                </div>
              </div>
            )}

            {/* Adaptive Mode Parameters */}
            {params.use_adaptive_rr && (
              <div className="space-y-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded">
                <h3 className="text-sm font-semibold text-neutral-300">Adaptive RR Mode</h3>
                
                <div>
                  <label className="block text-sm text-neutral-300 mb-2">Extra Margin Points</label>
                  <input
                    type="number"
                    value={params.extra_margin_pts}
                    onChange={(e) => setParams({ ...params, extra_margin_pts: parseFloat(e.target.value) || 5.0 })}
                    className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                    step="0.1"
                    min="0"
                  />
                  <p className="text-xs text-neutral-500 mt-1">Buffer beyond FVG boundary for SL</p>
                </div>

                <div>
                  <label className="block text-sm text-neutral-300 mb-2">RR Multiple</label>
                  <input
                    type="number"
                    value={params.rr_multiple}
                    onChange={(e) => setParams({ ...params, rr_multiple: parseFloat(e.target.value) || 2.0 })}
                    className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                    step="0.1"
                    min="0.1"
                  />
                  <p className="text-xs text-neutral-500 mt-1">TP:SL ratio (e.g., 2.0 = 2:1)</p>
                </div>
              </div>
            )}

            {/* Cutoff Time */}
            <div>
              <label className="block text-sm text-neutral-300 mb-2">Cutoff Time (NY)</label>
              <input
                type="time"
                value={params.cutoff_time}
                onChange={(e) => setParams({ ...params, cutoff_time: e.target.value + ':00' })}
                className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
              />
              <p className="text-xs text-neutral-500 mt-1">Session end time (default: 16:00)</p>
            </div>

            {/* Liquidity Filter */}
            <div className="space-y-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={params.liquidity_enabled || false}
                  onChange={(e) => setParams({ ...params, liquidity_enabled: e.target.checked })}
                  className="w-5 h-5 text-matrix-green bg-black border-zinc-700 rounded focus:ring-matrix-green focus:ring-2"
                />
                <span className="text-sm text-neutral-300 font-medium">
                  Enable Liquidity Filter (Only trade FVGs at swing highs/lows)
                </span>
              </label>
              <p className="text-xs text-neutral-500">
                Only consider FVGs that form when price takes out swing highs/lows (liquidity levels)
              </p>

              {params.liquidity_enabled && (
                <div className="space-y-4 mt-4 pt-4 border-t border-zinc-800">
                  <div>
                    <label className="block text-sm text-neutral-300 mb-2">Liquidity Timeframe</label>
                    <select
                      value={params.liquidity_timeframe || '15m'}
                      onChange={(e) => setParams({ ...params, liquidity_timeframe: e.target.value })}
                      className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                    >
                      <option value="15m">15m</option>
                      <option value="30m">30m</option>
                      <option value="1h">1h</option>
                      <option value="4h">4h</option>
                      <option value="1d">1d</option>
                    </select>
                    <p className="text-xs text-neutral-500 mt-1">Timeframe for swing high/low detection</p>
                  </div>

                  <div>
                    <label className="block text-sm text-neutral-300 mb-2">Swing Lookback</label>
                    <input
                      type="number"
                      value={params.swing_lookback || 5}
                      onChange={(e) => setParams({ ...params, swing_lookback: parseInt(e.target.value) || 5 })}
                      className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                      min="1"
                      max="50"
                    />
                    <p className="text-xs text-neutral-500 mt-1">Number of candles to look back/forward for swing detection</p>
                  </div>

                  <div>
                    <label className="block text-sm text-neutral-300 mb-2">Tolerance Points</label>
                    <input
                      type="number"
                      value={params.tolerance_pts || 5.0}
                      onChange={(e) => setParams({ ...params, tolerance_pts: parseFloat(e.target.value) || 5.0 })}
                      className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                      step="0.1"
                      min="0"
                    />
                    <p className="text-xs text-neutral-500 mt-1">Price tolerance in points for matching FVG to swing level</p>
                  </div>
                </div>
              )}
            </div>

            {/* Date Range (Optional - overrides Year Range if provided) */}
            <div className="space-y-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded">
              <h3 className="text-sm font-semibold text-neutral-300">Date Range (Optional)</h3>
              <p className="text-xs text-neutral-500">
                If not specified, Year Range below will be used. Date range takes precedence over year range.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-neutral-300 mb-2">Start Date</label>
                  <input
                    type="date"
                    value={params.date_start || ''}
                    onChange={(e) => setParams({ ...params, date_start: e.target.value || undefined })}
                    className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                  />
                </div>
                <div>
                  <label className="block text-sm text-neutral-300 mb-2">End Date</label>
                  <input
                    type="date"
                    value={params.date_end || ''}
                    onChange={(e) => setParams({ ...params, date_end: e.target.value || undefined })}
                    className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                  />
                </div>
              </div>
            </div>

            {/* Year Range (Used if Date Range not provided) */}
            <div className="space-y-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded">
              <h3 className="text-sm font-semibold text-neutral-300">Year Range</h3>
              <p className="text-xs text-neutral-500">
                Used if Date Range above is not specified.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-neutral-300 mb-2">Year Start</label>
                  <input
                    type="number"
                    value={params.year_start || ''}
                    onChange={(e) => setParams({ ...params, year_start: e.target.value ? parseInt(e.target.value) : undefined })}
                    className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                    min="2000"
                    max="2100"
                    disabled={!!params.date_start}
                  />
                </div>
                <div>
                  <label className="block text-sm text-neutral-300 mb-2">Year End</label>
                  <input
                    type="number"
                    value={params.year_end || ''}
                    onChange={(e) => setParams({ ...params, year_end: e.target.value ? parseInt(e.target.value) : undefined })}
                    className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                    min="2000"
                    max="2100"
                    disabled={!!params.date_end}
                  />
                </div>
              </div>
            </div>

            {/* Time Filter (Optional) */}
            <div className="space-y-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded">
              <h3 className="text-sm font-semibold text-neutral-300">Time Filter (Optional)</h3>
              <p className="text-xs text-neutral-500">
                Filter trades by entry time. If not specified, all times are allowed.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-neutral-300 mb-2">Start Time (NY)</label>
                  <input
                    type="time"
                    value={params.time_start ? params.time_start.substring(0, 5) : ''}
                    onChange={(e) => setParams({ ...params, time_start: e.target.value ? e.target.value + ':00' : undefined })}
                    className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                  />
                </div>
                <div>
                  <label className="block text-sm text-neutral-300 mb-2">End Time (NY)</label>
                  <input
                    type="time"
                    value={params.time_end ? params.time_end.substring(0, 5) : ''}
                    onChange={(e) => setParams({ ...params, time_end: e.target.value ? e.target.value + ':00' : undefined })}
                    className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                  />
                </div>
              </div>
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunBacktest}
              disabled={loading}
              className="w-full px-6 py-3 bg-matrix-green text-black font-semibold rounded hover:bg-matrix-green/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Running...' : 'Run iFVG Backtest'}
            </button>
          </div>

          {/* History */}
          <div className="card-matrix p-6">
            <h2 className="text-xl font-semibold text-matrix-green mb-4">Past Runs</h2>
            {history.length === 0 ? (
              <p className="text-neutral-500 text-sm">No iFVG runs yet. Run your first backtest above.</p>
            ) : (
              <div className="space-y-3">
                {history.slice(0, 10).map((run) => {
                  const createdDate = new Date(run.created_at);
                  const dateStr = createdDate.toLocaleDateString();
                  const timeStr = createdDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                  const statusColor = run.status === 'completed' ? 'text-matrix-green' : 
                                     run.status === 'failed' ? 'text-red-400' : 
                                     run.status === 'running' ? 'text-yellow-400' : 'text-neutral-400';
                  
                  return (
                    <div
                      key={run.run_id}
                      className="p-4 bg-zinc-900/50 border border-zinc-800 rounded cursor-pointer hover:border-matrix-green/50 transition-colors"
                      onClick={() => router.push(`/results/${run.run_id}`)}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`text-sm font-semibold ${statusColor} capitalize`}>
                              {run.status}
                            </span>
                            {run.completed_scenarios > 0 && run.total_scenarios > 0 && (
                              <span className="text-xs text-neutral-500">
                                ({Math.round((run.completed_scenarios / run.total_scenarios) * 100)}%)
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-neutral-400 mb-1">
                            {dateStr} at {timeStr}
                          </div>
                          <div className="text-xs text-neutral-500 font-mono">
                            ID: {run.run_id.substring(0, 8)}...
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/results/${run.run_id}`);
                          }}
                          className="px-3 py-1 text-xs bg-matrix-green/20 border border-matrix-green/50 text-matrix-green rounded hover:bg-matrix-green/30 whitespace-nowrap"
                        >
                          View →
                        </button>
                      </div>
                      <div className="mt-2 pt-2 border-t border-zinc-800 space-y-2">
                        <div className="text-xs text-neutral-500">
                          Scenarios: <span className="text-neutral-300">{run.completed_scenarios}/{run.total_scenarios}</span>
                        </div>
                        {/* WIN RATE DISPLAY - COMMENTED OUT */}
                        {/* {run.overall_win_rate !== undefined && run.overall_win_rate !== null && (
                          <div className="text-xs text-neutral-500">
                            Win Rate: <span className={`font-semibold ${
                              run.overall_win_rate >= 50 ? 'text-matrix-green' : 
                              run.overall_win_rate >= 40 ? 'text-yellow-400' : 
                              'text-red-400'
                            }`}>{run.overall_win_rate.toFixed(2)}%</span>
                          </div>
                        )} */}
                        {run.strategy_text && (
                          <div className="mt-2">
                            <div className="text-xs text-neutral-500 mb-1">Strategy:</div>
                            <div className="text-xs text-neutral-300 leading-relaxed line-clamp-2">
                              {run.strategy_text}
                            </div>
                          </div>
                        )}
                        {!run.strategy_text && run.strategy_type && (
                          <div className="mt-2">
                            <div className="text-xs text-neutral-500 mb-1">Strategy:</div>
                            <div className="text-xs text-neutral-300">
                              {run.strategy_type === 'ifvg' ? 'iFVG Reversal Strategy' : run.strategy_type}
                            </div>
                          </div>
                        )}
                        {run.scenario_params && (
                          <div className="mt-2">
                            <div className="text-xs text-neutral-500 mb-1">Parameters:</div>
                            <div className="text-xs text-neutral-300 space-y-0.5">
                              {run.scenario_params.fvg_timeframe && (
                                <div>FVG: {run.scenario_params.fvg_timeframe} • Entry: {run.scenario_params.entry_timeframe || 'N/A'}</div>
                              )}
                              {run.scenario_params.wait_candles && (
                                <div>Wait Candles: {run.scenario_params.wait_candles}</div>
                              )}
                              {run.scenario_params.use_adaptive_rr !== undefined && (
                                <div>RR: {run.scenario_params.use_adaptive_rr ? 'Adaptive' : 'Fixed'}</div>
                              )}
                              {(run.scenario_params.year_start && run.scenario_params.year_end) ? (
                                <div>Date Range: {run.scenario_params.year_start}-{run.scenario_params.year_end}</div>
                              ) : (run.scenario_params.date_start && run.scenario_params.date_end) ? (
                                <div>Date Range: {run.scenario_params.date_start} to {run.scenario_params.date_end}</div>
                              ) : null}
                              {(run.scenario_params.time_start || run.scenario_params.time_end) && (
                                <div>Time Range: {run.scenario_params.time_start || 'Any'} - {run.scenario_params.time_end || 'Any'}</div>
                              )}
                              <div>Liquidity: {run.scenario_params.liquidity_enabled ? 'ON' : 'OFF'}</div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


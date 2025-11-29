'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { aiApi, backtestApi, type ScenarioParams, type GridSearchRequest } from '@/lib/api';

type GenerationMode = 'ai' | 'grid';

export default function ChatPage() {
  const router = useRouter();
  const [mode, setMode] = useState<GenerationMode>('ai');
  const [message, setMessage] = useState('');
  const [scenarios, setScenarios] = useState<ScenarioParams[]>([]);
  const [loading, setLoading] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [numScenarios, setNumScenarios] = useState(10);
  const [groupResults, setGroupResults] = useState(true);
  
  // Grid search parameters
  const [gridParams, setGridParams] = useState({
    entry_time_from: '09:00:00',  // Start of entry time window
    entry_time_to: '10:00:00',     // End of entry time window
    entry_time_increment: 20,      // Increment in minutes
    trade_end_times: ['16:00:00'],
    target_pts_list: [20, 30, 40, 50, 60, 80, 100],
    stop_pts_list: [10, 15, 20, 30, 40, 50],
    rr_factor: null as number | null,  // Risk-Reward factor (null = no constraint)
    direction: 'both' as 'auto' | 'bullish' | 'bearish' | 'both',  // Single direction selection
    year_start: 2020,
    year_end: 2025,
    // Trend filter parameters
    trendEnabled: false,  // Default: OFF
    trendTimeframe: '15m',
    trendPeriod: 20,
    trendType: 'sma' as 'sma' | 'ema',
    trendStrict: true,
  });
  
  // Raw input values for comma-separated fields (to preserve commas while typing)
  const [rawInputs, setRawInputs] = useState({
    stop_pts: '10, 15, 20, 30, 40, 50',
    target_pts: '20, 30, 40, 50, 60, 80, 100',
    trade_end_times: '16:00:00',
  });

  const handleSendMessage = async () => {
    if (mode === 'ai') {
      if (!message.trim()) return;
      
      setLoading(true);
      try {
        const response = await aiApi.suggest(undefined, message, numScenarios);
        if (response.scenarios && response.scenarios.length > 0) {
          setScenarios(response.scenarios);
        } else {
          alert('No scenarios generated. Please check:\n1. OpenAI API key is set in .env\n2. API key is valid\n3. Check browser console for details');
        }
      } catch (error: any) {
        console.error('Error generating scenarios:', error);
        const errorMessage = error?.response?.data?.detail || error?.message || 'Unknown error';
        alert(`Error generating scenarios: ${errorMessage}\n\nPlease check:\n1. OpenAI API key is set in .env file\n2. Backend API is running (http://localhost:8000)\n3. Check browser console for details`);
      } finally {
        setLoading(false);
      }
    } else {
      // Grid search mode
      setLoading(true);
      try {
        // Generate entry times from from/to/increment
        const entry_time_starts = generateEntryTimes(
          gridParams.entry_time_from,
          gridParams.entry_time_to,
          gridParams.entry_time_increment
        );
        // For entry_time_ends, use the same generated times (each entry time is both start and end of that specific entry)
        const entry_time_ends = entry_time_starts;
        
        // Convert direction to directions array format
        let directions: (string | null)[] = [];
        if (gridParams.direction === 'both') {
          directions = ['bullish', 'bearish'];
        } else if (gridParams.direction === 'auto') {
          directions = [null];
        } else {
          directions = [gridParams.direction];
        }
        
        // If RR factor is set, ensure TP/SL pairs match the ratio
        let target_pts_list = gridParams.target_pts_list;
        let stop_pts_list = gridParams.stop_pts_list;
        
        if (gridParams.rr_factor && !isNaN(gridParams.rr_factor)) {
          // Calculate SL from TP to maintain RR ratio
          stop_pts_list = target_pts_list.map(tp => tp / gridParams.rr_factor!);
          // Round to 2 decimal places for cleaner values
          stop_pts_list = stop_pts_list.map(sl => Math.round(sl * 100) / 100);
        }
        
        // Create grid request with generated entry times
        // Exclude UI-only params and trend params (we'll add trend params explicitly)
        const { direction, entry_time_from, entry_time_to, entry_time_increment, rr_factor, trendEnabled, trendTimeframe, trendPeriod, trendType, trendStrict, ...restParams } = gridParams;
        const gridRequest: GridSearchRequest = {
          ...restParams,
          entry_time_starts: entry_time_starts,
          entry_time_ends: entry_time_ends,
          target_pts_list: target_pts_list,
          stop_pts_list: stop_pts_list,
          directions: directions,
          // Add trend params if enabled
          trend_enabled: gridParams.trendEnabled,
          trend_timeframe: gridParams.trendEnabled ? gridParams.trendTimeframe : undefined,
          trend_period: gridParams.trendEnabled ? gridParams.trendPeriod : undefined,
          trend_type: gridParams.trendEnabled ? gridParams.trendType : undefined,
          trend_strict: gridParams.trendEnabled ? gridParams.trendStrict : undefined,
        };
        
        const response = await aiApi.grid(gridRequest);
        if (response.scenarios && response.scenarios.length > 0) {
          setScenarios(response.scenarios);
          alert(`Generated ${response.valid_scenarios} valid scenarios from ${response.total_combinations} possible combinations!`);
        } else {
          alert('No scenarios generated. Please check your grid parameters.');
        }
      } catch (error: any) {
        console.error('Error generating grid scenarios:', error);
        const errorMessage = error?.response?.data?.detail || error?.message || 'Unknown error';
        alert(`Error generating grid scenarios: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleClearScenarios = () => {
    setScenarios([]);
    setMessage('');
    setRunId(null);
  };

  const handleExecute = async () => {
    if (scenarios.length === 0) return;
    
    setLoading(true);
    try {
      const response = await backtestApi.create({ 
        scenarios,
        strategy_text: mode === 'ai' ? message : `Grid search with ${scenarios.length} scenarios`,
        mode: mode
      });
      setRunId(response.run_id);
      // Optionally redirect to results page after a short delay
      setTimeout(() => {
        router.push(`/results/${response.run_id}?group=${groupResults ? '1' : '0'}`);
      }, 2000);
    } catch (error: any) {
      console.error('Error executing backtest:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || 'Unknown error';
      alert(`Error executing backtest: ${errorMessage}\n\nPlease check:\n1. Database tables exist (run init_db.py)\n2. Database connection is working\n3. Check browser console for details`);
    } finally {
      setLoading(false);
    }
  };

  const updateGridParam = (key: string, value: any) => {
    setGridParams(prev => ({ ...prev, [key]: value }));
  };

  const parseListInput = (input: string, type: 'string' | 'number' = 'string'): any[] => {
    return input.split(',').map(s => {
      const trimmed = s.trim();
      if (type === 'number') {
        const num = parseFloat(trimmed);
        return isNaN(num) ? null : num;
      }
      return trimmed;
    }).filter(v => v !== '' && v !== null && v !== undefined && !isNaN(v));
  };

  // Generate entry times based on from, to, and increment
  const generateEntryTimes = (from: string, to: string, incrementMinutes: number): string[] => {
    const times: string[] = [];
    
    // Safety check: if increment is invalid, return empty array
    if (!from || !to || isNaN(incrementMinutes) || incrementMinutes <= 0) {
      return times;
    }
    
    // Parse time strings (HH:MM:SS or HH:MM)
    const parseTime = (timeStr: string): number => {
      if (!timeStr) return 0;
      const parts = timeStr.split(':');
      const hours = parseInt(parts[0], 10) || 0;
      const minutes = parseInt(parts[1] || '0', 10) || 0;
      return hours * 60 + minutes; // Convert to minutes since midnight
    };
    
    // Format minutes to HH:MM:SS
    const formatTime = (minutes: number): string => {
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:00`;
    };
    
    const fromMinutes = parseTime(from);
    const toMinutes = parseTime(to);
    
    // Safety check: if times are invalid, return empty array
    if (isNaN(fromMinutes) || isNaN(toMinutes) || fromMinutes > toMinutes) {
      return times;
    }
    
    // Generate times at increments
    for (let current = fromMinutes; current <= toMinutes; current += incrementMinutes) {
      times.push(formatTime(current));
    }
    
    return times;
  };

  return (
      <div className="min-h-screen p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-matrix-green">Chat</h1>
            <button
              onClick={() => router.push('/history')}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 text-neutral-200 rounded hover:bg-zinc-700 transition-colors"
            >
              📊 View History
            </button>
            <button
              onClick={async () => {
                try {
                  const status = await backtestApi.getRunningStatus();
                  if (status.total_running === 0 && status.total_queries === 0) {
                    alert('✅ No running backtests or active queries');
                  } else {
                    const message = `Running Backtests: ${status.total_running}\nActive Queries: ${status.total_queries}\n\n${status.running_runs.map(r => `- ${r.run_id.substring(0, 8)}... (${r.progress})`).join('\n')}`;
                    const shouldCancel = confirm(`${message}\n\nCancel all running backtests?`);
                    if (shouldCancel) {
                      const result = await backtestApi.cancelAllRunning();
                      alert(`✅ ${result.message}`);
                    }
                  }
                } catch (error: any) {
                  alert(`Error: ${error?.response?.data?.detail || error?.message || 'Unknown error'}`);
                }
              }}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors ml-2"
            >
              ⚠️ Check & Cancel Running
            </button>
          </div>
        
        {/* Mode Toggle */}
        <div className="mb-6 card-matrix p-4">
          <div className="flex items-center gap-4">
            <span className="text-neutral-400">Generation Mode:</span>
            <button
              onClick={() => setMode('ai')}
              className={`px-4 py-2 rounded transition-colors ${
                mode === 'ai'
                  ? 'bg-matrix-green text-black font-semibold'
                  : 'bg-zinc-800 text-neutral-300 hover:bg-zinc-700'
              }`}
            >
              AI Suggestions
            </button>
            <button
              onClick={() => setMode('grid')}
              className={`px-4 py-2 rounded transition-colors ${
                mode === 'grid'
                  ? 'bg-matrix-green text-black font-semibold'
                  : 'bg-zinc-800 text-neutral-300 hover:bg-zinc-700'
              }`}
            >
              Grid Search (All Combinations)
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Input */}
          <div className="card-matrix p-6">
            {mode === 'ai' ? (
              <>
                <h2 className="text-xl font-semibold text-matrix-green mb-4">Describe Your Strategy</h2>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="e.g., for every 15 minute candle from 9am to 11am take a trade for difference stop loss and take profit but achieving 2R on the trade, compare 2020 to 2025"
                  className="w-full h-32 p-3 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-sm focus:border-matrix-green focus:outline-none"
                  disabled={loading}
                />
                <div className="mt-4 flex items-center gap-4">
                  <label className="text-sm text-neutral-400">
                    Number of scenarios:
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={isNaN(numScenarios) ? '' : numScenarios}
                      onChange={(e) => {
                        const value = e.target.value;
                        const num = value === '' ? 10 : parseInt(value, 10);
                        setNumScenarios(Math.max(1, Math.min(50, isNaN(num) ? 10 : num)));
                      }}
                      className="ml-2 w-20 px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-sm focus:border-matrix-green focus:outline-none"
                      disabled={loading}
                    />
                  </label>
                  <label className="text-sm text-neutral-400 flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={groupResults}
                      onChange={(e) => setGroupResults(e.target.checked)}
                    />
                    Group results (Strategy → Year → Month → Day)
                  </label>
                </div>
                <button
                  onClick={handleSendMessage}
                  disabled={loading || !message.trim()}
                  className="btn-matrix mt-4 w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Generating...' : `Generate ${numScenarios} Scenarios`}
                </button>
              </>
            ) : (
              <>
                <h2 className="text-xl font-semibold text-matrix-green mb-4">Grid Search Parameters</h2>
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                  <div>
                    <label className="text-xs text-neutral-400 block mb-1">Entry Time Window</label>
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <label className="text-xs text-neutral-500 block mb-1">From (HH:MM:SS)</label>
                    <input
                      type="text"
                          value={gridParams.entry_time_from}
                          onChange={(e) => updateGridParam('entry_time_from', e.target.value)}
                      className="w-full px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-xs"
                          placeholder="09:00:00"
                    />
                  </div>
                  <div>
                        <label className="text-xs text-neutral-500 block mb-1">To (HH:MM:SS)</label>
                    <input
                      type="text"
                          value={gridParams.entry_time_to}
                          onChange={(e) => updateGridParam('entry_time_to', e.target.value)}
                      className="w-full px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-xs"
                          placeholder="10:00:00"
                    />
                  </div>
                  <div>
                        <label className="text-xs text-neutral-500 block mb-1">Increment (minutes)</label>
                    <input
                          type="number"
                          value={isNaN(gridParams.entry_time_increment) ? '' : gridParams.entry_time_increment}
                          onChange={(e) => {
                            const value = e.target.value;
                            const num = value === '' ? 20 : parseInt(value, 10);
                            updateGridParam('entry_time_increment', isNaN(num) ? 20 : num);
                          }}
                      className="w-full px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-xs"
                          placeholder="20"
                          min="1"
                    />
                      </div>
                    </div>
                    <div className="mt-1 text-xs text-neutral-500">
                      Will generate: {generateEntryTimes(gridParams.entry_time_from, gridParams.entry_time_to, gridParams.entry_time_increment).join(', ')}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-neutral-400 block mb-1">Trade End Times (comma-separated, HH:MM:SS)</label>
                    <input
                      type="text"
                      value={gridParams.trade_end_times.join(', ')}
                      onChange={(e) => {
                        const value = e.target.value;
                        // Allow typing freely - parse but keep empty strings for trailing commas
                        const parsed = value.split(',').map(s => s.trim()).filter(v => v !== '');
                        updateGridParam('trade_end_times', parsed);
                      }}
                      className="w-full px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-xs"
                      placeholder="16:00:00"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-neutral-400 block mb-1">Target Points (comma-separated numbers)</label>
                    <input
                      type="text"
                      value={rawInputs.target_pts}
                      onChange={(e) => {
                        const value = e.target.value;
                        // Update raw input to preserve commas during typing
                        setRawInputs(prev => ({ ...prev, target_pts: value }));
                        
                        // Parse and update the actual list
                        const parsed = value.split(',')
                          .map(s => s.trim())
                          .filter(v => v !== '')
                          .map(v => {
                            const num = parseFloat(v);
                            return isNaN(num) ? null : num;
                          })
                          .filter(v => v !== null) as number[];
                        updateGridParam('target_pts_list', parsed);
                        
                        // If RR factor is set, automatically calculate SL from TP
                        if (gridParams.rr_factor && !isNaN(gridParams.rr_factor) && parsed.length > 0) {
                          const calculatedSL = parsed.map(tp => tp / gridParams.rr_factor!);
                          updateGridParam('stop_pts_list', calculatedSL);
                          setRawInputs(prev => ({ ...prev, stop_pts: calculatedSL.map(sl => Math.round(sl * 100) / 100).join(', ') }));
                        }
                      }}
                      onBlur={(e) => {
                        // On blur, clean up and sync raw input with parsed values
                        const value = e.target.value;
                        const parsed = value.split(',')
                          .map(s => s.trim())
                          .filter(v => v !== '')
                          .map(v => {
                            const num = parseFloat(v);
                            return isNaN(num) ? null : num;
                          })
                          .filter(v => v !== null) as number[];
                        
                        // Update raw input with cleaned version
                        if (parsed.length > 0) {
                          setRawInputs(prev => ({ ...prev, target_pts: parsed.join(', ') }));
                        } else {
                          setRawInputs(prev => ({ ...prev, target_pts: '' }));
                        }
                      }}
                      className="w-full px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-xs"
                      placeholder="20, 30, 40, 50, 60, 80, 100"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-neutral-400 block mb-1">Risk-Reward Factor (optional)</label>
                    <select
                      value={gridParams.rr_factor || ''}
                      onChange={(e) => {
                        const value = e.target.value;
                        const rr = value === '' ? null : parseFloat(value);
                        updateGridParam('rr_factor', rr);
                        
                        // If RR factor is set, calculate SL from TP
                        if (rr !== null && !isNaN(rr) && gridParams.target_pts_list.length > 0) {
                          const calculatedSL = gridParams.target_pts_list.map(tp => tp / rr);
                          updateGridParam('stop_pts_list', calculatedSL);
                          setRawInputs(prev => ({ ...prev, stop_pts: calculatedSL.join(', ') }));
                        }
                      }}
                      className="w-full px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-xs"
                    >
                      <option value="">None (use manual TP/SL)</option>
                      <option value="1">1:1</option>
                      <option value="1.5">1.5:1</option>
                      <option value="2">2:1</option>
                      <option value="2.5">2.5:1</option>
                      <option value="3">3:1</option>
                      <option value="4">4:1</option>
                      <option value="5">5:1</option>
                      <option value="6">6:1</option>
                    </select>
                    {gridParams.rr_factor && (
                      <div className="mt-1 text-xs text-neutral-500">
                        SL will be calculated as TP / {gridParams.rr_factor} (e.g., TP=50 → SL={50 / gridParams.rr_factor})
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="text-xs text-neutral-400 block mb-1">Stop Loss Points (comma-separated numbers){gridParams.rr_factor ? ' (auto-calculated from TP)' : ''}</label>
                    <input
                      type="text"
                      value={rawInputs.stop_pts}
                      onChange={(e) => {
                        if (gridParams.rr_factor) {
                          // If RR factor is set, don't allow manual editing
                          return;
                        }
                        const value = e.target.value;
                        // Update raw input to preserve commas
                        setRawInputs(prev => ({ ...prev, stop_pts: value }));
                        
                        // Parse and update the actual array
                        const parsed = value.split(',')
                          .map(s => s.trim())
                          .filter(v => v !== '')
                          .map(v => {
                            const num = parseFloat(v);
                            return isNaN(num) ? null : num;
                          })
                          .filter(v => v !== null) as number[];
                        updateGridParam('stop_pts_list', parsed);
                      }}
                      onBlur={(e) => {
                        if (gridParams.rr_factor) {
                          return;
                        }
                        // On blur, sync raw input with parsed values
                        const value = e.target.value;
                        const parsed = value.split(',')
                          .map(s => s.trim())
                          .filter(v => v !== '')
                          .map(v => {
                            const num = parseFloat(v);
                            return isNaN(num) ? null : num;
                          })
                          .filter(v => v !== null) as number[];
                        // Update raw input to match parsed values (removes trailing commas)
                        setRawInputs(prev => ({ ...prev, stop_pts: parsed.join(', ') }));
                        updateGridParam('stop_pts_list', parsed);
                      }}
                      disabled={!!gridParams.rr_factor}
                      className="w-full px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                      placeholder="10, 15, 20, 30, 40, 50"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-neutral-400 block mb-1">Direction</label>
                    <select
                      value={gridParams.direction}
                      onChange={(e) => updateGridParam('direction', e.target.value as 'auto' | 'bullish' | 'bearish' | 'both')}
                      className="w-full px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-xs"
                    >
                      <option value="auto">Auto (detect from market)</option>
                      <option value="bullish">Bullish</option>
                      <option value="bearish">Bearish</option>
                      <option value="both">Both (run in both directions)</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-neutral-400 block mb-1">Year Start</label>
                      <input
                        type="number"
                        value={isNaN(gridParams.year_start) ? '' : gridParams.year_start}
                        onChange={(e) => {
                          const value = e.target.value;
                          const num = value === '' ? 2020 : parseInt(value, 10);
                          updateGridParam('year_start', isNaN(num) ? 2020 : num);
                        }}
                        className="w-full px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-xs"
                        min="2000"
                        max="2100"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-neutral-400 block mb-1">Year End</label>
                      <input
                        type="number"
                        value={isNaN(gridParams.year_end) ? '' : gridParams.year_end}
                        onChange={(e) => {
                          const value = e.target.value;
                          const num = value === '' ? 2025 : parseInt(value, 10);
                          updateGridParam('year_end', isNaN(num) ? 2025 : num);
                        }}
                        className="w-full px-2 py-1 bg-black border border-zinc-700 rounded text-neutral-200 font-mono text-xs"
                        min="2000"
                        max="2100"
                      />
                    </div>
                  </div>
                  
                  {/* Trend Filter Section */}
                  <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-lg space-y-3">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={gridParams.trendEnabled}
                        onChange={(e) => {
                          setGridParams({
                            ...gridParams,
                            trendEnabled: e.target.checked
                          });
                        }}
                        className="w-5 h-5 text-matrix-green bg-black border-zinc-700 rounded focus:ring-matrix-green focus:ring-2"
                      />
                      <span className="text-sm text-neutral-300 font-medium">
                        ☑ Enable Trend Filtering
                      </span>
                    </label>
                    
                    {gridParams.trendEnabled && (
                      <div className="ml-8 space-y-3 p-3 bg-black/30 border border-zinc-800 rounded">
                        <div>
                          <label className="block text-xs text-neutral-400 mb-1">
                            Trend Timeframe
                          </label>
                          <select
                            value={gridParams.trendTimeframe}
                            onChange={(e) => setGridParams({
                              ...gridParams,
                              trendTimeframe: e.target.value
                            })}
                            className="w-full px-3 py-2 bg-black border border-zinc-700 rounded text-neutral-200 text-sm focus:border-matrix-green focus:outline-none"
                          >
                            <option value="5m">5 minutes</option>
                            <option value="15m">15 minutes</option>
                            <option value="30m">30 minutes</option>
                            <option value="1h">1 hour</option>
                          </select>
                        </div>
                        
                        <div>
                          <label className="block text-xs text-neutral-400 mb-1">
                            Moving Average Period
                          </label>
                          <input
                            type="number"
                            value={gridParams.trendPeriod}
                            onChange={(e) => setGridParams({
                              ...gridParams,
                              trendPeriod: parseInt(e.target.value) || 20
                            })}
                            className="w-full px-3 py-2 bg-black border border-zinc-700 rounded text-neutral-200 text-sm focus:border-matrix-green focus:outline-none"
                            min="5"
                            max="200"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-xs text-neutral-400 mb-1">
                            MA Type
                          </label>
                          <select
                            value={gridParams.trendType}
                            onChange={(e) => setGridParams({
                              ...gridParams,
                              trendType: e.target.value as 'sma' | 'ema'
                            })}
                            className="w-full px-3 py-2 bg-black border border-zinc-700 rounded text-neutral-200 text-sm focus:border-matrix-green focus:outline-none"
                          >
                            <option value="sma">SMA (Simple Moving Average)</option>
                            <option value="ema">EMA (Exponential Moving Average)</option>
                          </select>
                        </div>
                        
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={gridParams.trendStrict}
                            onChange={(e) => setGridParams({
                              ...gridParams,
                              trendStrict: e.target.checked
                            })}
                            className="w-4 h-4 text-matrix-green bg-black border-zinc-700 rounded focus:ring-matrix-green"
                          />
                          <span className="text-xs text-neutral-300">
                            Strict Mode (only trade in trend direction)
                          </span>
                        </label>
                      </div>
                    )}
                  </div>
                  
                  <div>
                    <label className="text-sm text-neutral-400 flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={groupResults}
                        onChange={(e) => setGroupResults(e.target.checked)}
                      />
                      Group results (Strategy → Year → Month → Day)
                    </label>
                  </div>
                </div>
                <button
                  onClick={handleSendMessage}
                  disabled={loading}
                  className="btn-matrix mt-4 w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Generating All Combinations...' : 'Generate All Combinations'}
                </button>
                <p className="text-xs text-neutral-500 mt-2">
                  This will generate ALL possible combinations. Large grids may take time!
                </p>
              </>
            )}
          </div>

          {/* Right: Generated Scenarios */}
          <div className="card-matrix p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-matrix-green">
                Generated Scenarios ({scenarios.length})
              </h2>
              {scenarios.length > 0 && (
                <button
                  onClick={handleClearScenarios}
                  className="px-3 py-1 text-sm bg-red-900/30 border border-red-700 text-red-400 rounded hover:bg-red-900/50 transition-colors"
                >
                  Clear All
                </button>
              )}
            </div>

            {scenarios.length === 0 ? (
              <p className="text-neutral-500 text-sm">
                {mode === 'ai' 
                  ? 'No scenarios yet. Describe your strategy and click "Generate Scenarios".'
                  : 'No scenarios yet. Configure grid parameters and click "Generate All Combinations".'}
              </p>
            ) : (
              <div className="space-y-4">
                <div className="max-h-96 overflow-y-auto space-y-2">
                  {scenarios.map((scenario, idx) => {
                    const rRatio = scenario.target_pts / scenario.stop_pts;
                    return (
                      <div key={idx} className="p-3 bg-black/50 border border-zinc-800 rounded text-xs font-mono">
                        <div className="text-matrix-green font-semibold mb-1">Scenario {idx + 1}</div>
                        <div className="space-y-1 text-neutral-300">
                          <div>Entry: {scenario.entry_time_start}-{scenario.entry_time_end} | End: {scenario.trade_end_time}</div>
                          <div>TP: {scenario.target_pts} | SL: {scenario.stop_pts} | R: {rRatio.toFixed(1)}</div>
                          <div>Direction: {scenario.direction || 'auto'} | Years: {scenario.year_start}-{scenario.year_end}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <button
                  onClick={handleExecute}
                  disabled={loading || scenarios.length === 0}
                  className="btn-matrix w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Executing...' : `Execute ${scenarios.length} Scenarios`}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

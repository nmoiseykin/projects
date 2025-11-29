'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { dailyScorecardApi, type DailyScorecardScenarioParams, type BacktestRunStatus } from '@/lib/api';

export default function DailyScorecardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [history, setHistory] = useState<BacktestRunStatus[]>([]);
  
  // Get current calendar week
  const getCurrentWeek = () => {
    const now = new Date();
    const start = new Date(now.getFullYear(), 0, 1);
    const days = Math.floor((now.getTime() - start.getTime()) / (24 * 60 * 60 * 1000));
    const weekNumber = Math.ceil((days + start.getDay() + 1) / 7);
    return weekNumber;
  };
  
  // Daily Scorecard parameters
  const [params, setParams] = useState<DailyScorecardScenarioParams>({
    year_start: 2020,
    year_end: 2025,
    calendar_week: getCurrentWeek(),
  });

  // Load history
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const { backtestApi } = await import('@/lib/api');
        const allRuns = await backtestApi.list(100);
        const scorecardRuns = allRuns.filter(r => r.strategy_type === 'daily_scorecard');
        setHistory(scorecardRuns as any);
      } catch (error: any) {
        console.error('Error loading history:', error);
        setHistory([]);
      }
    };
    loadHistory();
  }, []);

  const handleRunBacktest = async () => {
    setLoading(true);
    try {
      const response = await dailyScorecardApi.createBacktest({
        scenarios: [params]
      });
      
      if (!response || !response.run_id) {
        throw new Error('Invalid response from server: missing run_id');
      }
      
      setRunId(response.run_id);
      router.push(`/results/${response.run_id}`);
      router.refresh();
    } catch (error: any) {
      console.error('Error creating Daily Scorecard backtest:', error);
      setLoading(false);
      alert(`Error: ${error?.response?.data?.detail || error?.message || 'Unknown error'}`);
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-matrix-green">Daily Scorecard</h1>
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
            
            {/* Year Start */}
            <div>
              <label className="block text-sm text-neutral-300 mb-2">Start Year</label>
              <input
                type="number"
                value={params.year_start}
                onChange={(e) => setParams({ ...params, year_start: parseInt(e.target.value) || 2020 })}
                className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                min="2000"
                max="2100"
              />
            </div>

            {/* Year End */}
            <div>
              <label className="block text-sm text-neutral-300 mb-2">End Year</label>
              <input
                type="number"
                value={params.year_end}
                onChange={(e) => setParams({ ...params, year_end: parseInt(e.target.value) || 2025 })}
                className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                min="2000"
                max="2100"
              />
            </div>

            {/* Calendar Week */}
            <div>
              <label className="block text-sm text-neutral-300 mb-2">Calendar Week</label>
              <input
                type="number"
                value={params.calendar_week || ''}
                onChange={(e) => setParams({ ...params, calendar_week: e.target.value ? parseInt(e.target.value) : undefined })}
                className="w-full px-3 py-2 bg-black border border-zinc-700 text-neutral-200 rounded focus:border-matrix-green focus:ring-1 focus:ring-matrix-green"
                min="1"
                max="53"
                placeholder="Current week (auto)"
              />
              <p className="text-xs text-neutral-500 mt-1">Leave empty to use current week ({getCurrentWeek()})</p>
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunBacktest}
              disabled={loading}
              className="w-full px-6 py-3 bg-matrix-green text-black font-semibold rounded hover:bg-matrix-green/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Running...' : 'Run Daily Scorecard'}
            </button>
          </div>

          {/* Past Runs */}
          <div className="card-matrix p-6">
            <h2 className="text-xl font-semibold text-matrix-green mb-4">Past Runs</h2>
            {history.length === 0 ? (
              <p className="text-neutral-400">No past runs</p>
            ) : (
              <div className="space-y-3">
                {history.map((run) => (
                  <div
                    key={run.run_id}
                    className="p-4 bg-zinc-900 border border-zinc-700 rounded cursor-pointer hover:border-matrix-green transition-colors"
                    onClick={() => router.push(`/results/${run.run_id}`)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-mono text-neutral-400">
                        {run.run_id.substring(0, 8)}...
                      </span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        run.status === 'completed' ? 'bg-green-900 text-green-300' :
                        run.status === 'running' ? 'bg-yellow-900 text-yellow-300' :
                        'bg-zinc-800 text-neutral-400'
                      }`}>
                        {run.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-xs text-neutral-500">
                      {new Date(run.created_at).toLocaleString()}
                    </div>
                    {run.scenario_params && (
                      <div className="text-xs text-neutral-400 mt-2">
                        Years: {run.scenario_params.year_start}-{run.scenario_params.year_end}
                        {run.scenario_params.calendar_week && `, Week: ${run.scenario_params.calendar_week}`}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Strategy Description */}
        <div className="card-matrix p-6 mt-6">
          <h2 className="text-xl font-semibold text-matrix-green mb-4">About Daily Scorecard</h2>
          <p className="text-neutral-300 mb-4">
            Daily Scorecard provides statistical analysis for a specific calendar week across multiple years.
            It calculates weekly and daily statistics including bullish/bearish percentages and price ranges.
          </p>
          <div className="text-sm text-neutral-400 space-y-2">
            <p><strong className="text-matrix-green">Weekly Stats:</strong> % bullish (Friday close &gt; Sunday open), % bearish, average weekly price range</p>
            <p><strong className="text-matrix-green">Daily Stats:</strong> For each day of the week: % bullish/bearish, average price range, and average high/low for bullish and bearish days</p>
          </div>
        </div>
      </div>
    </div>
  );
}


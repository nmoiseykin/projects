'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { backtestApi } from '@/lib/api';

interface BacktestRunStatus {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  total_scenarios: number;
  completed_scenarios: number;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  strategy_type?: string;
  mode?: string;
  strategy_text?: string;
}

export default function HistoryPage() {
  const router = useRouter();
  const [runs, setRuns] = useState<BacktestRunStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStrategy, setFilterStrategy] = useState<'all' | 'standard' | 'ifvg'>('all');

  useEffect(() => {
    const fetchRuns = async () => {
      try {
        const data = await backtestApi.list(100);
        setRuns(data);
        setError(null);
      } catch (err: any) {
        console.error('Error fetching runs:', err);
        setError(err?.response?.data?.detail || err?.message || 'Failed to load history');
      } finally {
        setLoading(false);
      }
    };

    fetchRuns();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-matrix-green';
      case 'failed':
        return 'text-red-400';
      case 'running':
        return 'text-yellow-400';
      case 'cancelled':
        return 'text-orange-400';
      default:
        return 'text-neutral-400';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-matrix-green/10 border-matrix-green/30';
      case 'failed':
        return 'bg-red-900/10 border-red-700/30';
      case 'running':
        return 'bg-yellow-900/10 border-yellow-700/30';
      case 'cancelled':
        return 'bg-orange-900/10 border-orange-700/30';
      default:
        return 'bg-zinc-900/50 border-zinc-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-7xl mx-auto">
          <div className="card-matrix p-8 text-center">
            <p className="text-matrix-green">Loading history...</p>
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

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-matrix-green">Test History</h1>
          <div className="flex gap-4">
            <div className="flex gap-2 bg-zinc-900 p-1 rounded border border-zinc-700">
              <button
                onClick={() => setFilterStrategy('all')}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  filterStrategy === 'all' 
                    ? 'bg-matrix-green text-black font-semibold' 
                    : 'text-neutral-400 hover:text-neutral-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilterStrategy('standard')}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  filterStrategy === 'standard' 
                    ? 'bg-matrix-green text-black font-semibold' 
                    : 'text-neutral-400 hover:text-neutral-200'
                }`}
              >
                Standard
              </button>
              <button
                onClick={() => setFilterStrategy('ifvg')}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  filterStrategy === 'ifvg' 
                    ? 'bg-matrix-green text-black font-semibold' 
                    : 'text-neutral-400 hover:text-neutral-200'
                }`}
              >
                iFVG
              </button>
            </div>
            <button
              onClick={() => router.push('/chat')}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 text-neutral-200 rounded hover:bg-zinc-700 transition-colors"
            >
              ← Back to Chat
            </button>
          </div>
        </div>

        {(() => {
          const filteredRuns = filterStrategy === 'all' 
            ? runs 
            : runs.filter(r => {
                if (filterStrategy === 'ifvg') {
                  return r.strategy_type === 'ifvg';
                } else if (filterStrategy === 'standard') {
                  return !r.strategy_type || r.strategy_type === 'standard';
                }
                return true;
              });

          if (filteredRuns.length === 0) {
            return (
              <div className="card-matrix p-8 text-center">
                <p className="text-neutral-400">
                  {runs.length === 0 
                    ? 'No test runs found. Create your first backtest from the Chat page.'
                    : `No ${filterStrategy === 'ifvg' ? 'iFVG' : filterStrategy === 'standard' ? 'standard' : ''} runs found.`
                  }
                </p>
                {filterStrategy === 'ifvg' && runs.length > 0 && (
                  <button
                    onClick={() => router.push('/strategies/ifvg')}
                    className="btn-matrix mt-4"
                  >
                    Go to iFVG Strategy
                  </button>
                )}
                {runs.length === 0 && (
                  <button
                    onClick={() => router.push('/chat')}
                    className="btn-matrix mt-4"
                  >
                    Go to Chat
                  </button>
                )}
              </div>
            );
          }

          return (
            <div className="space-y-4">
              {filteredRuns.map((run) => {
              const progress = run.total_scenarios > 0 
                ? (run.completed_scenarios / run.total_scenarios) * 100 
                : 0;
              
              return (
                <div
                  key={run.run_id}
                  className={`card-matrix p-6 cursor-pointer hover:border-matrix-green/50 transition-all ${getStatusBg(run.status)}`}
                  onClick={() => router.push(`/results/${run.run_id}`)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <h2 className="text-lg font-semibold text-matrix-green font-mono">
                          {run.run_id.substring(0, 8)}...
                        </h2>
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(run.status)} bg-zinc-900/50`}>
                          {run.status.toUpperCase()}
                        </span>
                        {run.strategy_type && (
                          <span className="px-2 py-1 rounded text-xs font-semibold text-blue-400 bg-blue-900/30">
                            {run.strategy_type.toUpperCase()}
                          </span>
                        )}
                        {run.mode && (
                          <span className="px-2 py-1 rounded text-xs font-semibold text-neutral-400 bg-zinc-900/50">
                            {run.mode.toUpperCase()}
                          </span>
                        )}
                      </div>
                      
                      {run.strategy_text && (
                        <div className="mb-3 p-3 bg-black/30 border border-zinc-800 rounded">
                          <div className="text-xs text-neutral-500 mb-1">Strategy Request:</div>
                          <div className="text-sm text-neutral-300 font-mono line-clamp-2">
                            {run.strategy_text}
                          </div>
                        </div>
                      )}
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <div className="text-neutral-500 text-xs mb-1">Created</div>
                          <div className="text-neutral-300">
                            {new Date(run.created_at).toLocaleString()}
                          </div>
                        </div>
                        
                        {run.started_at && (
                          <div>
                            <div className="text-neutral-500 text-xs mb-1">Started</div>
                            <div className="text-neutral-300">
                              {new Date(run.started_at).toLocaleString()}
                            </div>
                          </div>
                        )}
                        
                        {run.finished_at && (
                          <div>
                            <div className="text-neutral-500 text-xs mb-1">Finished</div>
                            <div className="text-neutral-300">
                              {new Date(run.finished_at).toLocaleString()}
                            </div>
                          </div>
                        )}
                        
                        {run.finished_at && run.started_at && (
                          <div>
                            <div className="text-neutral-500 text-xs mb-1">Duration</div>
                            <div className="text-neutral-300">
                              {Math.round((new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()) / 1000 / 60)} min
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className="mt-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-neutral-400">
                            Scenarios: {run.completed_scenarios} / {run.total_scenarios}
                          </span>
                          {run.status === 'completed' && (
                            <span className="text-xs text-matrix-green">
                              ✓ Complete
                            </span>
                          )}
                        </div>
                        <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all duration-300 ${
                              run.status === 'completed' ? 'bg-matrix-green' :
                              run.status === 'failed' ? 'bg-red-400' :
                              'bg-yellow-400'
                            }`}
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                      </div>
                    </div>
                    
                    <div className="ml-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/results/${run.run_id}`);
                        }}
                        className="px-4 py-2 bg-matrix-green/20 border border-matrix-green/50 text-matrix-green rounded hover:bg-matrix-green/30 transition-colors"
                      >
                        View Results →
                      </button>
                    </div>
                  </div>
                </div>
              );
              })}
            </div>
          );
        })()}
      </div>
    </div>
  );
}



'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function StrategiesPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'standard' | 'ifvg' | 'daily-scorecard'>('ifvg');

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-matrix-green">Strategies</h1>
          <Link
            href="/"
            className="px-4 py-2 bg-zinc-800 border border-zinc-700 text-neutral-200 rounded hover:bg-zinc-700 transition-colors"
          >
            ← Home
          </Link>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6 card-matrix p-1 flex gap-2">
          <button
            onClick={() => router.push('/chat')}
            className={`px-6 py-2 rounded transition-colors ${
              activeTab === 'standard'
                ? 'bg-matrix-green text-black font-semibold'
                : 'bg-zinc-800 text-neutral-300 hover:bg-zinc-700'
            }`}
          >
            Standard
          </button>
          <button
            onClick={() => setActiveTab('ifvg')}
            className={`px-6 py-2 rounded transition-colors ${
              activeTab === 'ifvg'
                ? 'bg-matrix-green text-black font-semibold'
                : 'bg-zinc-800 text-neutral-300 hover:bg-zinc-700'
            }`}
          >
            iFVG Reversal
          </button>
          <button
            onClick={() => setActiveTab('daily-scorecard')}
            className={`px-6 py-2 rounded transition-colors ${
              activeTab === 'daily-scorecard'
                ? 'bg-matrix-green text-black font-semibold'
                : 'bg-zinc-800 text-neutral-300 hover:bg-zinc-700'
            }`}
          >
            Daily Scorecard
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'ifvg' && (
          <div className="card-matrix p-6">
            <p className="text-neutral-400 mb-4">
              iFVG Reversal strategy trades inversions of Fair Value Gaps (FVGs) when completely closed by opposing candles.
            </p>
            <Link
              href="/strategies/ifvg"
              className="inline-block px-6 py-3 bg-matrix-green text-black font-semibold rounded hover:bg-matrix-green/80 transition-colors"
            >
              Configure & Run iFVG Strategy →
            </Link>
          </div>
        )}

        {activeTab === 'daily-scorecard' && (
          <div className="card-matrix p-6">
            <p className="text-neutral-400 mb-4">
              Daily Scorecard provides statistical analysis for a specific calendar week across multiple years.
              Calculates weekly and daily statistics including bullish/bearish percentages and price ranges.
            </p>
            <Link
              href="/strategies/daily-scorecard"
              className="inline-block px-6 py-3 bg-matrix-green text-black font-semibold rounded hover:bg-matrix-green/80 transition-colors"
            >
              Configure & Run Daily Scorecard →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}


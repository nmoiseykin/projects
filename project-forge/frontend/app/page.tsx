'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-12">
          <h1 className="text-4xl font-bold text-matrix-green mb-2">
            PROJECT FORGE
          </h1>
          <p className="text-neutral-400 text-sm">Кузница — Self-Testing Mechanical Trading Lab</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link href="/chat" className="card-matrix p-6 hover:shadow-matrix-glow transition-all">
            <h2 className="text-xl font-semibold text-matrix-green mb-2">Chat</h2>
            <p className="text-neutral-400 text-sm">
              Describe your trading idea in plain English. AI generates backtest scenarios.
            </p>
          </Link>

          <Link href="/scenarios" className="card-matrix p-6 hover:shadow-matrix-glow transition-all">
            <h2 className="text-xl font-semibold text-matrix-green mb-2">Scenarios</h2>
            <p className="text-neutral-400 text-sm">
              Create and manage backtest scenarios. Run grid searches or AI-generated tests.
            </p>
          </Link>

          <Link href="/strategies" className="card-matrix p-6 hover:shadow-matrix-glow transition-all">
            <h2 className="text-xl font-semibold text-matrix-green mb-2">Strategies</h2>
            <p className="text-neutral-400 text-sm">
              Multiple trading strategies including iFVG Reversal.
            </p>
          </Link>

          <Link href="/logs" className="card-matrix p-6 hover:shadow-matrix-glow transition-all">
            <h2 className="text-xl font-semibold text-matrix-green mb-2">Logs</h2>
            <p className="text-neutral-400 text-sm">
              Live log tail. Watch backtest execution in real-time.
            </p>
          </Link>
        </div>

        <div className="mt-12 card-matrix p-6">
          <h2 className="text-xl font-semibold text-matrix-green mb-4">Recent Runs</h2>
          <p className="text-neutral-500 text-sm">No runs yet. Start by creating a scenario.</p>
        </div>
      </div>
    </div>
  );
}



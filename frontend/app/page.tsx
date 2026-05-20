'use client';

import { useState } from 'react';
import { useTheme } from '@/hooks/useTheme';
import { useResearch } from '@/hooks/useResearch';
import { ResearchForm } from '@/components/ResearchForm';
import { AgentStatus } from '@/components/AgentStatus';
import { ReportDisplay } from '@/components/ReportDisplay';
import { AnalyticsView } from '@/components/AnalyticsView';
import { GatewayControls } from '@/components/GatewayControls';

type Tab = 'research' | 'analytics' | 'gateway';

export default function Home() {
  const { theme, toggleTheme } = useTheme();
  const { agents, reportTokens, isLoading, error, run, reset } = useResearch();
  const [activeTab, setActiveTab] = useState<Tab>('research');

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-[#050814] text-slate-100 transition-colors">
      {/* ── SIDEBAR NAV ── */}
      <aside className="w-full md:w-64 flex flex-col justify-between p-5 border-b md:border-b-0 md:border-r border-[rgba(99,120,180,0.12)] bg-[#0d1117] backdrop-blur-md">
        <div className="space-y-7">
          {/* Brand/Logo */}
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent flex items-center gap-1.5">
                <span>🔍</span> Detective-L
              </span>
              <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-[rgba(6,182,212,0.1)] text-[#06b6d4] border border-[rgba(6,182,212,0.15)]">
                v1.1
              </span>
            </div>
            <p className="text-[11px] mt-1" style={{ color: 'var(--text-secondary)' }}>
              Parallel Agentic Intelligence
            </p>
          </div>

          {/* Navigation Items */}
          <nav className="space-y-1.5">
            <button
              onClick={() => setActiveTab('research')}
              className={`w-full sidebar-item ${activeTab === 'research' ? 'active' : ''}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              Research Workspace
            </button>

            <button
              onClick={() => setActiveTab('analytics')}
              className={`w-full sidebar-item ${activeTab === 'analytics' ? 'active' : ''}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Telemetry Analytics
            </button>

            <button
              onClick={() => setActiveTab('gateway')}
              className={`w-full sidebar-item ${activeTab === 'gateway' ? 'active' : ''}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
              Gateway Controls
            </button>
          </nav>
        </div>

        {/* Footer info & Connection Status */}
        <div className="space-y-4 pt-5 border-t border-[rgba(99,120,180,0.12)]">
          <div className="flex items-center justify-between text-xs">
            <span style={{ color: 'var(--text-secondary)' }}>Status:</span>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-semibold text-emerald-400">Connected</span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            {/* Theme Toggle Button */}
            <button
              onClick={toggleTheme}
              className="p-1.5 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-xs flex items-center justify-center gap-1 transition-colors"
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
            >
              <span>{theme === 'dark' ? '☀️' : '🌙'}</span>
              <span className="text-[10px] font-medium" style={{ color: 'var(--text-secondary)' }}>
                {theme === 'dark' ? 'Light' : 'Dark'}
              </span>
            </button>
            <span className="text-[10px] text-slate-500 font-mono">
              Build v1.1.2
            </span>
          </div>
        </div>
      </aside>

      {/* ── MAIN CONTENT AREA ── */}
      <main className="flex-1 p-6 overflow-y-auto max-h-screen">
        {activeTab === 'research' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in-up">
            {/* Left Workspace Panel */}
            <div className="lg:col-span-1 space-y-6">
              {/* Form Card */}
              <div className="glass-card p-5">
                <ResearchForm onSubmit={run} isLoading={isLoading} />
              </div>

              {/* Connected SVG Pipeline Status */}
              {(isLoading || reportTokens) && (
                <div className="glass-card p-5">
                  <AgentStatus agents={agents} />
                </div>
              )}

              {/* Error Display */}
              {error && (
                <div className="glass-card p-5 border-rose-500/25 bg-rose-950/10">
                  <p className="text-rose-400 text-xs leading-relaxed">
                    <span className="font-bold">❌ Pipeline Error:</span> {error}
                  </p>
                  <button
                    onClick={reset}
                    className="mt-3 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded transition-colors"
                  >
                    Reset &amp; Try Again
                  </button>
                </div>
              )}

              {/* Reset Button (when complete) */}
              {!isLoading && reportTokens && !error && (
                <button
                  onClick={reset}
                  className="w-full btn-secondary py-2.5 flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  New Investigation
                </button>
              )}
            </div>

            {/* Right Report Viewing Panel */}
            <div className="lg:col-span-2">
              <div className="glass-card p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-[rgba(99,120,180,0.12)] pb-3">
                  <h2 className="text-sm font-semibold flex items-center gap-2">
                    {isLoading ? (
                      <>
                        <div className="w-3.5 h-3.5 rounded-full border border-t-transparent animate-spin" style={{ borderColor: 'var(--accent-cyan) transparent transparent transparent' }} />
                        <span className="text-cyan-400">Synthesizing findings…</span>
                      </>
                    ) : reportTokens ? (
                      <>
                        <span className="text-emerald-400">✓</span>
                        <span className="text-emerald-400">Intelligence Dossier Compiled</span>
                      </>
                    ) : (
                      <>
                        <span>📄</span>
                        <span style={{ color: 'var(--text-secondary)' }}>Research Dossier</span>
                      </>
                    )}
                  </h2>
                </div>

                <ReportDisplay reportContent={reportTokens} isGenerating={isLoading} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && <AnalyticsView />}

        {activeTab === 'gateway' && <GatewayControls />}
      </main>
    </div>
  );
}

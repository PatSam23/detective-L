'use client';

import { useState } from 'react';
import { useTheme } from '@/hooks/useTheme';
import { useResearch } from '@/hooks/useResearch';
import { ResearchForm } from '@/components/ResearchForm';
import { AgentStatus } from '@/components/AgentStatus';
import { ReportDisplay } from '@/components/ReportDisplay';

export default function Home() {
  const { theme, toggleTheme } = useTheme();
  const { agents, reportTokens, isLoading, error, run, reset } = useResearch();

  const handleReset = () => {
    reset();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-200 bg-slate-50/50 dark:border-slate-700 dark:bg-slate-900/50 backdrop-blur-sm transition-colors">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 dark:from-blue-400 dark:to-cyan-400 bg-clip-text text-transparent">
                🔍 Detective-L
              </h1>
              <p className="text-slate-600 dark:text-gray-400 text-sm mt-1">
                Multi-agent AI research intelligence system
              </p>
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                <span className="text-slate-600 dark:text-gray-400">Backend Connected</span>
              </div>
              {/* Theme Toggle Button */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-900 dark:text-white transition-colors"
                title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
              >
                {theme === 'dark' ? '☀️' : '🌙'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Form & Agents */}
          <div className="lg:col-span-1 space-y-6">
            {/* Research Form */}
            <section className="p-6 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 transition-colors">
              <ResearchForm onSubmit={run} isLoading={isLoading} />
            </section>

            {/* Agent Status */}
            {isLoading && (
              <section className="p-6 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <AgentStatus agents={agents} />
              </section>
            )}

            {/* Error Display */}
            {error && (
              <section className="p-4 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-600 rounded-lg">
                <p className="text-red-700 dark:text-red-300 text-sm">
                  <span className="font-semibold">❌ Error:</span> {error}
                </p>
                <button
                  onClick={handleReset}
                  className="mt-3 px-4 py-2 bg-red-500 dark:bg-red-600 hover:bg-red-600 dark:hover:bg-red-700 text-white text-sm rounded-lg transition-colors"
                >
                  Try Again
                </button>
              </section>
            )}

            {/* Reset Button (when complete) */}
            {!isLoading && reportTokens && !error && (
              <button
                onClick={handleReset}
                className="w-full px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-900 dark:text-gray-200 text-sm rounded-lg transition-colors border border-slate-300 dark:border-slate-600"
              >
                New Research
              </button>
            )}
          </div>

          {/* Right Column: Report */}
          <div className="lg:col-span-2">
            <section className="p-6 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  {isLoading ? (
                    <>
                      <span className="animate-spin">⚙️</span>
                      <span>Generating Report...</span>
                    </>
                  ) : reportTokens ? (
                    <>
                      <span>✅</span>
                      <span>Research Complete</span>
                    </>
                  ) : (
                    <>
                      <span>📄</span>
                      <span>Report</span>
                    </>
                  )}
                </h2>
              </div>

              <ReportDisplay reportContent={reportTokens} isGenerating={isLoading} />
            </section>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 pt-6 border-t border-slate-200 dark:border-slate-700 text-center text-sm text-slate-600 dark:text-gray-400">
          <p>
            Detective-L v1.0 • Built with Next.js, LangGraph & Tailwind CSS
          </p>
          <p className="mt-2">
            Backend API: <code className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">{process.env.NEXT_PUBLIC_API_URL}</code>
          </p>
        </footer>
      </main>
    </div>
  );
}

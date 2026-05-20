'use client';

import { useState, useEffect, useCallback } from 'react';

interface AnalyticsEntry {
  provider: string;
  model: string;
  tokens: number;
  latency: string;
  cache_hit: boolean;
  time: string;
}

interface AnalyticsSummary {
  total_requests: number;
  cache_hits: number;
  cache_hit_rate: string;
  total_tokens: number;
  avg_latency_ms: string;
}

interface AnalyticsData {
  summary: AnalyticsSummary;
  recent_activity: AnalyticsEntry[];
}

interface CacheStats {
  hits: number;
  misses: number;
  errors: number;
  total: number;
  hit_rate_percent: number;
  connected: boolean;
  enabled: boolean;
}

// ── Simple SVG donut gauge ──────────────────────────────────────────
function GaugeRing({ pct, color, label }: { pct: number; color: string; label: string }) {
  const R = 40;
  const CIRC = 2 * Math.PI * R;
  const offset = CIRC * (1 - Math.min(pct, 1));
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={R} fill="none" stroke="rgba(99,120,180,0.12)" strokeWidth="8" />
        <circle
          cx="50" cy="50" r={R}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={CIRC}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
        <text x="50" y="54" textAnchor="middle" fontSize="14" fontWeight="700" fill={color} fontFamily="Inter,sans-serif">
          {Math.round(pct * 100)}%
        </text>
      </svg>
      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{label}</span>
    </div>
  );
}

// ── Latency bar chart ───────────────────────────────────────────────
function LatencyBars({ entries }: { entries: AnalyticsEntry[] }) {
  if (!entries.length) return null;
  const maxMs = Math.max(...entries.map(e => parseFloat(e.latency)));
  return (
    <div className="w-full">
      <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
        Latency per Call (ms)
      </p>
      <div className="flex items-end gap-1.5" style={{ height: 80 }}>
        {entries.slice(0, 10).map((e, i) => {
          const ms = parseFloat(e.latency);
          const heightPct = maxMs > 0 ? ms / maxMs : 0;
          const h = Math.max(4, Math.round(heightPct * 72));
          const color = e.cache_hit ? '#10b981' : ms > 15000 ? '#f59e0b' : '#06b6d4';
          return (
            <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
              <div
                title={`${ms.toFixed(0)} ms`}
                style={{
                  height: h,
                  background: color,
                  borderRadius: '3px 3px 0 0',
                  opacity: 0.85,
                  width: '100%',
                  transition: 'height 0.6s ease',
                }}
              />
            </div>
          );
        })}
      </div>
      <div className="flex gap-3 mt-2">
        <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-muted)' }}>
          <span className="w-2 h-2 rounded-full inline-block" style={{ background: '#10b981' }} /> Cached
        </span>
        <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-muted)' }}>
          <span className="w-2 h-2 rounded-full inline-block" style={{ background: '#06b6d4' }} /> Fast
        </span>
        <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-muted)' }}>
          <span className="w-2 h-2 rounded-full inline-block" style={{ background: '#f59e0b' }} /> Slow
        </span>
      </div>
    </div>
  );
}

// ── KPI card ───────────────────────────────────────────────────────
function KpiCard({ label, value, sub, glowClass }: { label: string; value: string | number; sub?: string; glowClass: string }) {
  return (
    <div className={`glass-card p-5 ${glowClass}`}>
      <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: 'var(--text-muted)' }}>{label}</p>
      <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{value}</p>
      {sub && <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{sub}</p>}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────
export function AnalyticsView() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [cache, setCache] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const apiUrl = typeof window !== 'undefined'
    ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
    : 'http://localhost:8000';

  const fetchAll = useCallback(async () => {
    try {
      const [analyticsRes, cacheRes] = await Promise.all([
        fetch(`${apiUrl}/analytics/usage`),
        fetch(`${apiUrl}/cache/stats`),
      ]);
      if (analyticsRes.ok) setData(await analyticsRes.json());
      if (cacheRes.ok) setCache(await cacheRes.json());
      setError(null);
    } catch {
      setError('Could not connect to backend. Is the server running?');
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  }, [apiUrl]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // ── Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height: 300 }}>
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: 'var(--accent-cyan) transparent transparent transparent' }} />
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Loading telemetry…</p>
        </div>
      </div>
    );
  }

  // ── Error state
  if (error) {
    return (
      <div className="glass-card p-6 text-center" style={{ borderColor: 'rgba(244,63,94,0.25)' }}>
        <p className="text-sm" style={{ color: 'var(--accent-rose)' }}>⚠ {error}</p>
        <button onClick={fetchAll} className="btn-secondary mt-4 px-5 py-2">Retry</button>
      </div>
    );
  }

  const summary = data?.summary;
  const activity = data?.recent_activity ?? [];
  const cacheHitPct = cache ? cache.hit_rate_percent / 100 : 0;
  const avgMs = summary ? parseFloat(summary.avg_latency_ms) : 0;

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Cost &amp; Performance Telemetry</h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            Last updated {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={fetchAll}
          className="btn-secondary px-4 py-2 flex items-center gap-2"
          style={{ fontSize: '0.8rem' }}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Total Requests"
          value={summary?.total_requests ?? 0}
          sub="via LLM Gateway"
          glowClass="kpi-card-cyan"
        />
        <KpiCard
          label="Avg Latency"
          value={avgMs > 0 ? `${(avgMs / 1000).toFixed(1)}s` : '—'}
          sub={avgMs > 15000 ? '⚠ High latency' : 'Per LLM call'}
          glowClass="kpi-card-blue"
        />
        <KpiCard
          label="Cache Hits"
          value={cache?.hits ?? 0}
          sub={`${cache?.total ?? 0} total calls`}
          glowClass="kpi-card-emerald"
        />
        <KpiCard
          label="Tokens Used"
          value={summary?.total_tokens ?? 0}
          sub="Prompt + completion"
          glowClass="kpi-card-violet"
        />
      </div>

      {/* Gauges + Bar Chart row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Gauges */}
        <div className="glass-card p-5">
          <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>
            Cache Performance
          </p>
          <div className="flex items-center justify-around">
            <GaugeRing
              pct={cacheHitPct}
              color="#10b981"
              label="Hit Rate"
            />
            <div className="text-center">
              <div
                className="w-3 h-3 rounded-full inline-block mb-2"
                style={{ background: cache?.connected ? '#10b981' : '#f43f5e' }}
              />
              <p className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                Redis {cache?.connected ? 'Online' : 'Offline'}
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                {cache?.enabled ? 'Enabled' : 'Disabled'}
              </p>
            </div>
            <div className="text-center space-y-1">
              <p className="text-xl font-bold" style={{ color: 'var(--accent-cyan)' }}>{cache?.hits ?? 0}</p>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Hits</p>
              <p className="text-xl font-bold" style={{ color: 'var(--text-secondary)' }}>{cache?.misses ?? 0}</p>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Misses</p>
            </div>
          </div>
        </div>

        {/* Latency bars */}
        <div className="glass-card p-5">
          <LatencyBars entries={activity} />
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="glass-card overflow-hidden">
        <div className="flex items-center justify-between p-5 pb-3">
          <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
            Recent Gateway Activity
          </p>
          <span className="badge badge-pending">{activity.length} entries</span>
        </div>
        {activity.length === 0 ? (
          <div className="p-8 text-center" style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            No gateway calls recorded yet. Run a research query first.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Model</th>
                  <th>Latency</th>
                  <th>Tokens</th>
                  <th>Cache</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {activity.map((entry, i) => (
                  <tr key={i}>
                    <td>
                      <span className="mono text-xs" style={{ color: 'var(--accent-cyan)' }}>
                        {entry.provider}
                      </span>
                    </td>
                    <td>
                      <span className="mono text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {entry.model}
                      </span>
                    </td>
                    <td>
                      <span
                        className="mono text-xs font-medium"
                        style={{ color: parseFloat(entry.latency) > 15000 ? 'var(--accent-amber)' : 'var(--text-primary)' }}
                      >
                        {(parseFloat(entry.latency) / 1000).toFixed(2)}s
                      </span>
                    </td>
                    <td>
                      <span className="mono text-xs" style={{ color: 'var(--text-muted)' }}>
                        {entry.tokens ?? '—'}
                      </span>
                    </td>
                    <td>
                      {entry.cache_hit
                        ? <span className="badge badge-complete">⚡ Hit</span>
                        : <span className="badge badge-pending">💾 API</span>}
                    </td>
                    <td>
                      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        {new Date(entry.time).toLocaleTimeString()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

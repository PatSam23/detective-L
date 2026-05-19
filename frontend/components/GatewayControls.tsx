'use client';

import { useState, useEffect } from 'react';

const PROVIDER_MODELS: Record<string, string[]> = {
  gemini: ['gemini-2.5-flash', 'gemini-2.5-pro'],
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
  anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'],
};

interface GatewayConfig {
  provider: string;
  model: string;
  max_tokens: number;
  cache_enabled: boolean;
}

export function GatewayControls() {
  const [config, setConfig] = useState<GatewayConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const apiUrl = typeof window !== 'undefined'
    ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
    : 'http://localhost:8000';

  useEffect(() => {
    async function fetchConfig() {
      try {
        const res = await fetch(`${apiUrl}/gateway/config`);
        if (res.ok) {
          setConfig(await res.json());
        }
      } catch {
        setMessage({ text: 'Failed to fetch gateway configuration.', type: 'error' });
      } finally {
        setLoading(false);
      }
    }
    fetchConfig();
  }, [apiUrl]);

  const handleSave = async (updatedConfig: Partial<GatewayConfig>) => {
    if (!config) return;
    setSaving(true);
    setMessage(null);
    const newConfig = { ...config, ...updatedConfig };
    
    // Automatically adjust model if provider changed
    if (updatedConfig.provider) {
      newConfig.model = PROVIDER_MODELS[updatedConfig.provider][0];
    }

    try {
      const res = await fetch(`${apiUrl}/gateway/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig),
      });

      if (res.ok) {
        const result = await res.json();
        setConfig(result.config);
        setMessage({ text: 'Gateway configuration updated successfully.', type: 'success' });
      } else {
        setMessage({ text: 'Failed to update configuration.', type: 'error' });
      }
    } catch {
      setMessage({ text: 'Failed to connect to backend.', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleClearCache = async () => {
    setClearing(true);
    setMessage(null);
    try {
      const res = await fetch(`${apiUrl}/cache/clear`, { method: 'POST' });
      if (res.ok) {
        setMessage({ text: 'Redis cache and statistics cleared successfully.', type: 'success' });
      } else {
        setMessage({ text: 'Failed to clear Redis cache.', type: 'error' });
      }
    } catch {
      setMessage({ text: 'Failed to connect to cache endpoint.', type: 'error' });
    } finally {
      setClearing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height: 250 }}>
        <div className="w-6 h-6 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: 'var(--accent-cyan) transparent transparent transparent' }} />
      </div>
    );
  }

  if (!config) return null;

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Gateway Routing Control</h2>
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
          Manage LLM providers, active routing configurations, caching rules, and API limits.
        </p>
      </div>

      {/* Alert Banner */}
      {message && (
        <div
          className="p-3.5 rounded-lg border text-xs"
          style={{
            background: message.type === 'success' ? 'rgba(16, 185, 129, 0.08)' : 'rgba(244, 63, 94, 0.08)',
            borderColor: message.type === 'success' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(244, 63, 94, 0.25)',
            color: message.type === 'success' ? '#10b981' : '#f43f5e',
          }}
        >
          {message.text}
        </div>
      )}

      {/* Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* LLM Settings */}
        <div className="glass-card p-5 space-y-4">
          <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
            Active LLM Routing
          </p>

          {/* Provider Select */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>LLM Provider</label>
            <select
              value={config.provider}
              onChange={(e) => handleSave({ provider: e.target.value })}
              disabled={saving}
              className="w-full px-3 py-2 text-xs premium-input bg-slate-900 border border-slate-700 rounded-md"
            >
              <option value="gemini">Google Gemini</option>
              <option value="openai">OpenAI (GPT)</option>
              <option value="anthropic">Anthropic Claude</option>
            </select>
          </div>

          {/* Model Select */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Active Model</label>
            <select
              value={config.model}
              onChange={(e) => handleSave({ model: e.target.value })}
              disabled={saving}
              className="w-full px-3 py-2 text-xs premium-input bg-slate-900 border border-slate-700 rounded-md"
            >
              {(PROVIDER_MODELS[config.provider] || []).map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          {/* Max Tokens */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Max Output Limit (Tokens)</label>
            <input
              type="number"
              value={config.max_tokens}
              onChange={(e) => handleSave({ max_tokens: parseInt(e.target.value) || 2048 })}
              disabled={saving}
              min="512"
              max="16384"
              className="w-full px-3 py-2 text-xs premium-input bg-slate-900 border border-slate-700 rounded-md"
            />
          </div>
        </div>

        {/* Cache Settings */}
        <div className="glass-card p-5 space-y-5">
          <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
            Redis Cache Policy
          </p>

          {/* Toggle Cache */}
          <div className="flex items-start gap-3">
            <input
              id="cache-toggle"
              type="checkbox"
              checked={config.cache_enabled}
              onChange={(e) => handleSave({ cache_enabled: e.target.checked })}
              disabled={saving}
              className="mt-0.5 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500"
              style={{ width: 15, height: 15 }}
            />
            <div>
              <label htmlFor="cache-toggle" className="text-xs font-semibold select-none cursor-pointer" style={{ color: 'var(--text-primary)' }}>
                Enable Caching Layer
              </label>
              <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
                Store prompt completions in Redis cache to instantly resolve identical agent queries, dramatically cutting down latencies and token usage.
              </p>
            </div>
          </div>

          <hr className="divider" />

          {/* Clear Cache */}
          <div>
            <p className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>Clear Caching Database</p>
            <p className="text-[11px] mt-0.5 mb-3.5" style={{ color: 'var(--text-muted)' }}>
              Force invalidate all prompt entries cached inside Redis, purging statistics counters completely.
            </p>
            <button
              onClick={handleClearCache}
              disabled={clearing}
              className="px-4 py-2 text-xs bg-rose-600 hover:bg-rose-700 text-white font-medium rounded-md transition-colors flex items-center justify-center gap-1.5"
            >
              {clearing ? (
                <>
                  <div className="w-3 h-3 rounded-full border border-t-transparent animate-spin border-white" />
                  Purging…
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Clear Redis Cache
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

'use client';

import { FormEvent, useState } from 'react';

interface ResearchFormProps {
  onSubmit: (query: string) => Promise<void>;
  isLoading: boolean;
}

/**
 * Form component for submitting research queries
 */
export function ResearchForm({ onSubmit, isLoading }: ResearchFormProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (query.trim()) {
      await onSubmit(query);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="query" className="block text-sm font-medium text-gray-300 mb-2">
          Research Query
        </label>
        <textarea
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your research topic (e.g., 'Competitive landscape of EV battery technology in India')"
          disabled={isLoading}
          className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          rows={4}
        />
      </div>

      <button
        type="submit"
        disabled={isLoading || !query.trim()}
        className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 disabled:scale-100"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="animate-spin">⚙️</span>
            Researching...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            <span>🔍</span>
            Start Research
          </span>
        )}
      </button>
    </form>
  );
}

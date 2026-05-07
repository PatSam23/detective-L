'use client';

import { FinalReport } from '@/types';

interface ReportDisplayProps {
  reportContent: string;
  isGenerating: boolean;
}

/**
 * Component to display the research report as it's being generated
 */
export function ReportDisplay({ reportContent, isGenerating }: ReportDisplayProps) {
  // Try to parse JSON if it looks like structured report
  let parsedReport: FinalReport | null = null;
  
  try {
    if (reportContent.startsWith('{')) {
      parsedReport = JSON.parse(reportContent) as FinalReport;
    }
  } catch (err) {
    // Not valid JSON, treat as plain text
  }

  if (!reportContent && !isGenerating) {
    return (
      <div className="p-6 bg-slate-100 dark:bg-slate-700 rounded-lg border border-slate-300 dark:border-slate-600 text-center text-slate-600 dark:text-gray-400">
        <p>📄 Report will appear here as agents complete their work</p>
      </div>
    );
  }

  if (parsedReport) {
    return (
      <div className="space-y-6 max-h-[600px] overflow-y-auto">
        {/* Title */}
        {parsedReport.title && (
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
              {parsedReport.title}
            </h2>
          </div>
        )}

        {/* Executive Summary */}
        {parsedReport.executive_summary && (
          <div>
            <h3 className="text-lg font-semibold text-blue-600 dark:text-blue-400 mb-2">Executive Summary</h3>
            <p className="text-slate-700 dark:text-gray-300 leading-relaxed">
              {parsedReport.executive_summary}
            </p>
          </div>
        )}

        {/* Sections */}
        {parsedReport.sections && parsedReport.sections.length > 0 && (
          <div className="space-y-4">
            {parsedReport.sections.map((section, idx) => (
              <div key={idx}>
                <h3 className="text-lg font-semibold text-blue-600 dark:text-blue-400 mb-2">{section.title}</h3>
                <p className="text-slate-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{section.content}</p>
              </div>
            ))}
          </div>
        )}

        {/* Sources */}
        {parsedReport.sources && parsedReport.sources.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-blue-600 dark:text-blue-400 mb-2">Sources</h3>
            <ul className="space-y-1">
              {parsedReport.sources.map((source, idx) => (
                <li key={idx} className="text-sm text-blue-500 dark:text-blue-300 truncate">
                  {idx + 1}. {source}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Confidence Score */}
        {parsedReport.confidence_score !== undefined && (
          <div className="p-4 bg-slate-100 dark:bg-slate-700 rounded-lg border border-slate-300 dark:border-slate-600">
            <div className="flex items-center justify-between">
              <span className="text-slate-700 dark:text-gray-300">Overall Confidence</span>
              <span
                className={`text-lg font-bold ${
                  parsedReport.confidence_score > 0.8
                    ? "text-green-600 dark:text-green-400"
                    : parsedReport.confidence_score > 0.6
                    ? "text-yellow-600 dark:text-yellow-400"
                    : "text-red-600 dark:text-red-400"
                }`}
              >
                {(parsedReport.confidence_score * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Plain text report (streaming)
  return (
    <div className="p-6 bg-slate-100 dark:bg-slate-700 rounded-lg border border-slate-300 dark:border-slate-600 max-h-[600px] overflow-y-auto">
      <p className="text-slate-700 dark:text-gray-300 whitespace-pre-wrap font-mono text-sm leading-relaxed">
        {reportContent}
        {isGenerating && <span className="animate-pulse">▊</span>}
      </p>
    </div>
  );
}

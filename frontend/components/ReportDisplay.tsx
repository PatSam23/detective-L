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
      <div className="p-6 bg-slate-700 rounded-lg border border-slate-600 text-center text-gray-400">
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
            <h2 className="text-2xl font-bold text-white mb-2">
              {parsedReport.title}
            </h2>
          </div>
        )}

        {/* Summary */}
        {parsedReport.summary && (
          <div>
            <h3 className="text-lg font-semibold text-blue-400 mb-2">Summary</h3>
            <p className="text-gray-300 leading-relaxed">
              {parsedReport.summary}
            </p>
          </div>
        )}

        {/* Key Findings */}
        {parsedReport.key_findings && parsedReport.key_findings.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-blue-400 mb-2">Key Findings</h3>
            <ul className="space-y-2">
              {parsedReport.key_findings.map((finding, idx) => (
                <li key={idx} className="flex gap-3">
                  <span className="text-green-400 font-bold">✓</span>
                  <span className="text-gray-300">{finding}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Analysis */}
        {parsedReport.analysis && (
          <div>
            <h3 className="text-lg font-semibold text-blue-400 mb-2">Analysis</h3>
            <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
              {parsedReport.analysis}
            </p>
          </div>
        )}

        {/* Claims with Confidence */}
        {parsedReport.claims && parsedReport.claims.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-blue-400 mb-2">Verified Claims</h3>
            <div className="space-y-2">
              {parsedReport.claims.map((claim, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border ${
                    claim.flagged
                      ? "bg-red-900/20 border-red-600"
                      : "bg-green-900/20 border-green-600"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-gray-300 flex-1">{claim.text}</p>
                    <div className="ml-4 text-right">
                      <span
                        className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                          claim.confidence > 0.8
                            ? "bg-green-600 text-white"
                            : claim.confidence > 0.6
                            ? "bg-yellow-600 text-white"
                            : "bg-red-600 text-white"
                        }`}
                      >
                        {(claim.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  {claim.flagged && (
                    <p className="text-xs text-red-300 mt-1">⚠️ Requires further verification</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Sources */}
        {parsedReport.sources && parsedReport.sources.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-blue-400 mb-2">Sources</h3>
            <ul className="space-y-1">
              {parsedReport.sources.map((source, idx) => (
                <li key={idx} className="text-sm text-blue-300 truncate">
                  {idx + 1}. {source}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Confidence Score */}
        {parsedReport.confidence_score !== undefined && (
          <div className="p-4 bg-slate-700 rounded-lg border border-slate-600">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Overall Confidence</span>
              <span
                className={`text-lg font-bold ${
                  parsedReport.confidence_score > 0.8
                    ? "text-green-400"
                    : parsedReport.confidence_score > 0.6
                    ? "text-yellow-400"
                    : "text-red-400"
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
    <div className="p-6 bg-slate-700 rounded-lg border border-slate-600 max-h-[600px] overflow-y-auto">
      <p className="text-gray-300 whitespace-pre-wrap font-mono text-sm leading-relaxed">
        {reportContent}
        {isGenerating && <span className="animate-pulse">▊</span>}
      </p>
    </div>
  );
}

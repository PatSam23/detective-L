'use client';

import { AgentStatus as AgentStatusType } from '@/types';

interface AgentStatusProps {
  agents: AgentStatusType[];
}

const AGENT_DISPLAY_NAMES: Record<string, string> = {
  planner: "📋 Planner",
  web_research_agent: "🌐 Web Research",
  synthesis: "📝 Synthesis",
  critic: "🔍 Critic",
  revisor: "✏️ Revisor",
  format_report: "📊 Formatter",
};

const AGENT_DESCRIPTIONS: Record<string, string> = {
  planner: "Breaking down query into research topics",
  web_research_agent: "Searching and gathering information",
  synthesis: "Merging findings into draft report",
  critic: "Fact-checking claims",
  revisor: "Refining report based on feedback",
  format_report: "Creating final structured report",
};

/**
 * Component to display real-time agent status
 */
export function AgentStatus({ agents }: AgentStatusProps) {
  const getStatusIcon = (status: AgentStatusType["status"]) => {
    switch (status) {
      case "pending":
        return "⭕";
      case "running":
        return "🔄";
      case "complete":
        return "✅";
      case "error":
        return "❌";
      default:
        return "❓";
    }
  };

  const getStatusColor = (status: AgentStatusType["status"]) => {
    switch (status) {
      case "pending":
        return "text-slate-600 dark:text-gray-400";
      case "running":
        return "text-yellow-500 dark:text-yellow-400 animate-pulse";
      case "complete":
        return "text-green-500 dark:text-green-400";
      case "error":
        return "text-red-500 dark:text-red-400";
      default:
        return "text-slate-600 dark:text-gray-400";
    }
  };

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Agent Progress</h3>
      <div className="space-y-2">
        {agents.map((agent) => (
          <div
            key={agent.name}
            className="flex items-center gap-3 p-3 bg-slate-100 dark:bg-slate-700 rounded-lg border border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500 transition-colors"
          >
            <span className={`text-xl ${getStatusColor(agent.status)}`}>
              {getStatusIcon(agent.status)}
            </span>
            
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-900 dark:text-white">
                  {AGENT_DISPLAY_NAMES[agent.name] || agent.name}
                </span>
                <span className="text-xs text-slate-600 dark:text-gray-400">
                  {agent.status === "complete" ? "100%" : agent.status === "running" ? "In progress..." : "Waiting"}
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-gray-400 mt-1">
                {AGENT_DESCRIPTIONS[agent.name]}
              </p>
            </div>

            {/* Progress bar */}
            <div className="w-24 h-1.5 bg-slate-300 dark:bg-slate-600 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  agent.status === "complete"
                    ? "bg-green-500"
                    : agent.status === "running"
                    ? "bg-yellow-500"
                    : "bg-slate-400 dark:bg-slate-500"
                }`}
                style={{
                  width: `${agent.progress || 0}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

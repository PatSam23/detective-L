'use client';

import { AgentStatus as AgentStatusType } from '@/types';

interface AgentPipelineProps {
  agents: AgentStatusType[];
}

const AGENT_CONFIG = [
  { key: 'planner',          label: 'Planner',    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
  { key: 'web_research_agent', label: 'Research',  icon: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9' },
  { key: 'synthesis',         label: 'Synthesis', icon: 'M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
  { key: 'critic',            label: 'Critic',    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
  { key: 'format_report',     label: 'Formatter', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
];

const NODE_COLORS = {
  pending:  { stroke: '#334155', fill: '#1c2333', text: '#475569', glow: 'none' },
  running:  { stroke: '#06b6d4', fill: '#082028', text: '#06b6d4', glow: 'drop-shadow(0 0 10px rgba(6,182,212,0.9))' },
  complete: { stroke: '#10b981', fill: '#05150f', text: '#10b981', glow: 'drop-shadow(0 0 8px rgba(16,185,129,0.7))' },
  error:    { stroke: '#f43f5e', fill: '#1a0510', text: '#f43f5e', glow: 'drop-shadow(0 0 8px rgba(244,63,94,0.7))' },
};

export function AgentStatus({ agents }: AgentPipelineProps) {
  // Map agent name → status
  const statusMap = Object.fromEntries(agents.map(a => [a.key ?? a.name, a.status ?? 'pending']));

  const NODE_R = 26;
  const ICON_SIZE = 14;
  const SVG_H = 130;

  // Responsive: nodes spread evenly across a fixed viewBox width
  const VB_W = 700;
  const nodeCount = AGENT_CONFIG.length;
  const nodeSpacingX = VB_W / nodeCount;
  const nodeXs = AGENT_CONFIG.map((_, i) => nodeSpacingX * i + nodeSpacingX / 2);
  const nodeY = SVG_H / 2 - 8;

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
          Agent Pipeline
        </span>
        {agents.some(a => a.status === 'running') && (
          <span className="badge badge-running">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse inline-block" />
            Live
          </span>
        )}
        {agents.every(a => a.status === 'complete') && agents.length > 0 && (
          <span className="badge badge-complete">✓ Complete</span>
        )}
      </div>

      <svg
        viewBox={`0 0 ${VB_W} ${SVG_H}`}
        className="w-full"
        style={{ height: 130 }}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="pipe-grad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%"   stopColor="#06b6d4" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.8" />
          </linearGradient>
        </defs>

        {/* Connector lines */}
        {AGENT_CONFIG.slice(0, -1).map((agent, i) => {
          const x1 = nodeXs[i] + NODE_R;
          const x2 = nodeXs[i + 1] - NODE_R;
          const y  = nodeY;
          const nextKey = AGENT_CONFIG[i + 1].key;
          const prevStatus = statusMap[agent.key] ?? 'pending';
          const nextStatus = statusMap[nextKey] ?? 'pending';
          const isActive   = prevStatus === 'running' || (prevStatus === 'complete' && nextStatus === 'running');
          const isDone     = prevStatus === 'complete' && nextStatus === 'complete';

          return (
            <g key={`line-${i}`}>
              {/* Base line */}
              <line
                x1={x1} y1={y} x2={x2} y2={y}
                stroke={isDone ? '#10b981' : isActive ? 'url(#pipe-grad)' : '#1e293b'}
                strokeWidth={isDone ? 2 : isActive ? 2 : 1.5}
                strokeDasharray={isDone ? 'none' : ''}
              />
              {/* Animated flow dots */}
              {isActive && (
                <line
                  x1={x1} y1={y} x2={x2} y2={y}
                  stroke="url(#pipe-grad)"
                  strokeWidth={2}
                  strokeDasharray="6 6"
                  className="pipeline-flow-line"
                />
              )}
            </g>
          );
        })}

        {/* Nodes */}
        {AGENT_CONFIG.map((agent, i) => {
          const status = (statusMap[agent.key] ?? 'pending') as keyof typeof NODE_COLORS;
          const colors = NODE_COLORS[status];
          const cx = nodeXs[i];
          const cy = nodeY;
          const isRunning = status === 'running';

          return (
            <g key={agent.key} style={{ filter: colors.glow }}>
              {/* Pulse ring for running */}
              {isRunning && (
                <circle
                  cx={cx} cy={cy} r={NODE_R + 6}
                  fill="none"
                  stroke="#06b6d4"
                  strokeWidth={1.5}
                  strokeOpacity={0.4}
                  className="agent-node-active"
                />
              )}

              {/* Main circle */}
              <circle
                cx={cx} cy={cy} r={NODE_R}
                fill={colors.fill}
                stroke={colors.stroke}
                strokeWidth={isRunning ? 2 : 1.5}
              />

              {/* Icon */}
              <g transform={`translate(${cx - ICON_SIZE / 2}, ${cy - ICON_SIZE / 2})`}>
                <svg
                  width={ICON_SIZE} height={ICON_SIZE}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke={status === 'pending' ? '#334155' : colors.text}
                  strokeWidth={1.8}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d={agent.icon} />
                </svg>
              </g>

              {/* Label below */}
              <text
                x={cx} y={cy + NODE_R + 14}
                textAnchor="middle"
                fontSize={10}
                fontWeight={status === 'running' ? '600' : '400'}
                fill={colors.text}
                style={{ fontFamily: 'Inter, sans-serif' }}
              >
                {agent.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

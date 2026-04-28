/**
 * Type definitions for the Detective-L frontend
 */

export interface ResearchRequest {
  query: string;
}

export interface Claim {
  text: string;
  confidence: number;
  flagged: boolean;
}

export interface FinalReport {
  title: string;
  summary: string;
  key_findings: string[];
  analysis: string;
  sources: string[];
  confidence_score: number;
  claims: Claim[];
}

export interface ResearchResponse {
  status: string;
  final_report: FinalReport;
  sources: string[];
  revision_count: number;
}

export interface AgentStatus {
  name: string;
  status: "pending" | "running" | "complete" | "error";
  progress?: number;
}

export interface StreamEvent {
  type: "agent_update" | "agent_start" | "agent_complete" | "research_complete" | "error" | "token";
  name?: string;
  data?: Record<string, unknown>;
  message?: string;
  text?: string;
}

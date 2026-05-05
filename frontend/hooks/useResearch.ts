'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { AgentStatus, StreamEvent, FinalReport } from '@/types';

const AGENT_NAMES = [
  "planner",
  "web_research_agent",
  "synthesis",
  "critic",
  "revisor",
  "format_report",
];

interface UseResearchReturn {
  agents: AgentStatus[];
  reportTokens: string;
  isLoading: boolean;
  error: string | null;
  finalReport: FinalReport | null;
  run: (query: string) => Promise<void>;
  reset: () => void;
}

/**
 * Hook to manage research queries and SSE streaming from backend
 */
export function useResearch(): UseResearchReturn {
  const [agents, setAgents] = useState<AgentStatus[]>(
    AGENT_NAMES.map((name) => ({
      name,
      status: "pending",
      progress: 0,
    }))
  );
  
  const [reportTokens, setReportTokens] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [finalReport, setFinalReport] = useState<FinalReport | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const reset = useCallback(() => {
    setAgents(
      AGENT_NAMES.map((name) => ({
        name,
        status: "pending",
        progress: 0,
      }))
    );
    setReportTokens("");
    setError(null);
    setFinalReport(null);
    setIsLoading(false);
  }, []);

  const run = useCallback(async (query: string) => {
    reset();
    setIsLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const streamUrl = `${apiUrl}/research/stream`;

      const response = await fetch(streamUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error("No response body from stream");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");

        // Process complete lines, keep incomplete line in buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;

          try {
            const eventData = JSON.parse(line.slice(6)) as StreamEvent;
            handleStreamEvent(eventData);
          } catch (err) {
            console.error("Failed to parse event:", err);
          }
        }
      }

      setIsLoading(false);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error occurred";
      setError(errorMsg);
      setIsLoading(false);
      console.error("Research error:", err);
    }
  }, [reset]);

  const handleStreamEvent = useCallback((event: StreamEvent) => {
    switch (event.type) {
      case "agent_start":
        // Agent starting - mark as running
        if (event.name) {
          setAgents((prev) =>
            prev.map((a) =>
              a.name === event.name ? { ...a, status: "running", progress: 25 } : a
            )
          );
          console.debug(`[SSE] Agent started: ${event.name}`);
        }
        break;

      case "agent_update":
        // Agent is processing - update progress
        if (event.name) {
          setAgents((prev) =>
            prev.map((a) =>
              a.name === event.name ? { ...a, status: "running", progress: 75 } : a
            )
          );
          
          // If the update contains report data, display it
          if (event.data) {
            const data = event.data as Record<string, unknown>;
            
            // Extract and display final_report if available
            if (data.final_report && typeof data.final_report === 'object') {
              const report = data.final_report as FinalReport;
              setReportTokens(JSON.stringify(report, null, 2));
              setFinalReport(report);
            }
          }
        }
        break;

      case "agent_complete":
      case "agent_done":
        // Agent finished - mark as complete
        if (event.name) {
          setAgents((prev) =>
            prev.map((a) =>
              a.name === event.name ? { ...a, status: "complete", progress: 100 } : a
            )
          );
          console.debug(`[SSE] Agent completed: ${event.name}`);
        }
        break;

      case "token":
        // Append token to report (for streaming text)
        if (event.text) {
          setReportTokens((prev) => prev + event.text);
        }
        break;

      case "research_complete":
        // All agents done - mark any remaining as complete
        setAgents((prev) =>
          prev.map((a) =>
            a.status === "pending" ? { ...a, status: "complete", progress: 100 } : a
          )
        );
        console.debug("[SSE] Research completed");
        break;

      case "error":
        if (event.message) {
          setError(event.message);
          console.error(`[SSE] Stream error: ${event.message}`);
        }
        break;

      default:
        console.debug(`[SSE] Unknown event type: ${event.type}`);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return {
    agents,
    reportTokens,
    isLoading,
    error,
    finalReport,
    run,
    reset,
  };
}

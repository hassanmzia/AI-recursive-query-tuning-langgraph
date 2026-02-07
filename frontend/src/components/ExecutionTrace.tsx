import React from 'react';
import type { TraceItem } from '../types';

interface Props {
  trace: TraceItem[];
  title?: string;
}

const nodeColors: Record<string, string> = {
  generate_query_or_respond: '#3b82f6',
  retrieve: '#f59e0b',
  grade_documents: '#a855f7',
  rewrite_question: '#ef4444',
  generate_answer: '#06b6d4',
  research_agent: '#3b82f6',
  qa_specialist: '#f59e0b',
  critique_agent: '#a855f7',
  revision_agent: '#ef4444',
  summarizer: '#06b6d4',
};

export default function ExecutionTrace({ trace, title = 'Execution Trace' }: Props) {
  if (!trace || trace.length === 0) return null;

  return (
    <div className="trace-panel">
      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: '#9da2c2' }}>
        {title}
      </div>
      {trace.map((item, i) => {
        const nodeName = item.node || item.agent || 'unknown';
        const color = nodeColors[nodeName] || '#6366f1';
        return (
          <div key={i} className="trace-item">
            <span
              className="trace-node"
              style={{ background: `${color}22`, color }}
            >
              {nodeName}
            </span>
            <span className="trace-detail">{item.detail || item.action || ''}</span>
            {item.score !== undefined && (
              <span className="badge badge-info" style={{ marginLeft: 'auto' }}>
                Score: {item.score}/10
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

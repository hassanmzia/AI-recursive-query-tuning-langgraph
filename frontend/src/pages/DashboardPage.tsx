import React, { useEffect, useState } from 'react';
import { useAppStore } from '../store';
import { getDashboard } from '../services/api';
import type { DashboardData } from '../types';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((e) => setError(e.message || 'Failed to load dashboard'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <>
        <div className="page-header"><div className="page-title">Dashboard</div></div>
        <div className="page-body">
          <div className="loading-indicator"><div className="spinner" /><span>Loading dashboard...</span></div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <div className="page-header"><div className="page-title">Dashboard</div></div>
        <div className="page-body">
          <div className="card" style={{ color: 'var(--color-error)' }}>
            Failed to load dashboard data. Make sure the backend is running.
            <div style={{ fontSize: 12, marginTop: 4, color: 'var(--color-text-muted)' }}>{error}</div>
          </div>
        </div>
      </>
    );
  }

  const o = data?.overview;

  return (
    <>
      <div className="page-header">
        <div className="page-title">Dashboard</div>
        <button className="btn btn-secondary btn-sm" onClick={() => {
          setLoading(true);
          getDashboard().then(setData).finally(() => setLoading(false));
        }}>
          Refresh
        </button>
      </div>

      <div className="page-body">
        <div className="stats-grid">
          <StatCard label="Total Queries" value={o?.total_executions || 0} color="var(--color-primary)" />
          <StatCard label="Success Rate" value={`${o?.success_rate || 0}%`} color="var(--color-success)" />
          <StatCard label="Avg Duration" value={`${o?.average_duration_ms || 0}ms`} color="var(--color-info)" />
          <StatCard label="Active Sessions" value={o?.active_sessions || 0} color="var(--color-warning)" />
          <StatCard label="Documents Indexed" value={o?.indexed_documents || 0} color="var(--color-agent-summarizer)" />
          <StatCard label="Avg Quality" value={o?.average_quality_score ? `${o.average_quality_score}/10` : 'N/A'} color="var(--color-agent-critique)" />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="card">
            <div className="card-header">Workflow Distribution</div>
            {data?.workflow_distribution?.map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--color-border)' }}>
                <span style={{ fontSize: 13 }}>{item.workflow_type === 'recursive_qa' ? 'Recursive ReAct QA' : 'Multi-Agent'}</span>
                <span className="badge badge-primary">{item.count}</span>
              </div>
            )) || <div style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>No data yet</div>}
          </div>

          <div className="card">
            <div className="card-header">Status Distribution</div>
            {data?.status_distribution?.map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--color-border)' }}>
                <span style={{ fontSize: 13, textTransform: 'capitalize' }}>{item.status}</span>
                <span className={`badge ${item.status === 'completed' ? 'badge-success' : item.status === 'failed' ? 'badge-error' : 'badge-warning'}`}>
                  {item.count}
                </span>
              </div>
            )) || <div style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>No data yet</div>}
          </div>
        </div>

        <div className="card" style={{ marginTop: 16 }}>
          <div className="card-header">Recent Executions</div>
          {data?.recent_executions && data.recent_executions.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Query</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_executions.map((exec: any, i) => (
                  <tr key={i}>
                    <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {exec.input_query}
                    </td>
                    <td>{exec.workflow_type === 'recursive_qa' ? 'ReAct QA' : 'Multi-Agent'}</td>
                    <td>
                      <span className={`badge ${exec.status === 'completed' ? 'badge-success' : exec.status === 'failed' ? 'badge-error' : 'badge-warning'}`}>
                        {exec.status}
                      </span>
                    </td>
                    <td>{exec.duration_ms ? `${exec.duration_ms}ms` : '-'}</td>
                    <td>{new Date(exec.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ color: 'var(--color-text-muted)', fontSize: 13, padding: 12 }}>
              No executions yet. Start asking questions!
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color }}>{value}</div>
    </div>
  );
}

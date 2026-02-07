import React, { useEffect, useState } from 'react';
import { getExecutions, getSessions } from '../services/api';
import ExecutionTrace from '../components/ExecutionTrace';
import type { WorkflowExecution, Session } from '../types';

export default function HistoryPage() {
  const [activeTab, setActiveTab] = useState<'executions' | 'sessions'>('executions');
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedExec, setSelectedExec] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getExecutions().catch(() => []),
      getSessions().catch(() => []),
    ]).then(([execs, sess]) => {
      setExecutions(execs);
      setSessions(sess);
      setLoading(false);
    });
  }, []);

  return (
    <>
      <div className="page-header">
        <div className="page-title">History</div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => {
            setLoading(true);
            Promise.all([getExecutions().catch(() => []), getSessions().catch(() => [])])
              .then(([e, s]) => { setExecutions(e); setSessions(s); })
              .finally(() => setLoading(false));
          }}
        >
          Refresh
        </button>
      </div>

      <div className="page-body">
        <div className="tabs">
          <button className={`tab ${activeTab === 'executions' ? 'active' : ''}`} onClick={() => setActiveTab('executions')}>
            Workflow Executions
          </button>
          <button className={`tab ${activeTab === 'sessions' ? 'active' : ''}`} onClick={() => setActiveTab('sessions')}>
            Conversation Sessions
          </button>
        </div>

        {loading ? (
          <div className="loading-indicator"><div className="spinner" /><span>Loading history...</span></div>
        ) : (
          <>
            {activeTab === 'executions' && (
              <div style={{ display: 'grid', gridTemplateColumns: selectedExec ? '1fr 1fr' : '1fr', gap: 16 }}>
                <div>
                  {executions.length === 0 ? (
                    <div className="card" style={{ textAlign: 'center', color: 'var(--color-text-muted)' }}>
                      No workflow executions yet
                    </div>
                  ) : (
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
                        {executions.map((exec) => (
                          <tr
                            key={exec.id}
                            onClick={() => setSelectedExec(exec)}
                            style={{ cursor: 'pointer', background: selectedExec?.id === exec.id ? 'var(--color-surface)' : undefined }}
                          >
                            <td style={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {exec.input_query}
                            </td>
                            <td style={{ fontSize: 12 }}>
                              {exec.workflow_type === 'recursive_qa' ? 'ReAct' : 'Multi'}
                            </td>
                            <td>
                              <span className={`badge ${exec.status === 'completed' ? 'badge-success' : exec.status === 'failed' ? 'badge-error' : 'badge-warning'}`}>
                                {exec.status}
                              </span>
                            </td>
                            <td>{exec.duration_ms ? `${exec.duration_ms}ms` : '-'}</td>
                            <td style={{ fontSize: 11 }}>{new Date(exec.created_at).toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                {selectedExec && (
                  <div className="card">
                    <div className="card-header">
                      Execution Detail
                      <button className="btn btn-ghost btn-sm" style={{ marginLeft: 'auto' }} onClick={() => setSelectedExec(null)}>
                        Close
                      </button>
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                      <div style={{ marginBottom: 8 }}>
                        <strong>Query:</strong> {selectedExec.input_query}
                      </div>
                      {selectedExec.final_answer && (
                        <div style={{ marginBottom: 8 }}>
                          <strong>Answer:</strong> {selectedExec.final_answer}
                        </div>
                      )}
                      <div style={{ display: 'flex', gap: 16, marginBottom: 8, fontSize: 12 }}>
                        <span>Type: {selectedExec.workflow_type}</span>
                        <span>Duration: {selectedExec.duration_ms}ms</span>
                        <span>Iterations: {selectedExec.total_iterations}</span>
                      </div>
                    </div>
                    {selectedExec.execution_trace && selectedExec.execution_trace.length > 0 && (
                      <ExecutionTrace trace={selectedExec.execution_trace} />
                    )}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'sessions' && (
              <div>
                {sessions.length === 0 ? (
                  <div className="card" style={{ textAlign: 'center', color: 'var(--color-text-muted)' }}>
                    No conversation sessions yet
                  </div>
                ) : (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>Messages</th>
                        <th>Status</th>
                        <th>Last Activity</th>
                        <th>Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sessions.map((session) => (
                        <tr key={session.id}>
                          <td>{session.title || 'Untitled Session'}</td>
                          <td>{session.message_count}</td>
                          <td>
                            <span className={`badge ${session.is_active ? 'badge-success' : 'badge-info'}`}>
                              {session.is_active ? 'Active' : 'Closed'}
                            </span>
                          </td>
                          <td style={{ fontSize: 11 }}>
                            {session.last_message
                              ? `${session.last_message.role}: ${session.last_message.content}`
                              : '-'
                            }
                          </td>
                          <td style={{ fontSize: 11 }}>{new Date(session.created_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}

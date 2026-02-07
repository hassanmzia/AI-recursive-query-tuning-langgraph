import React, { useEffect, useState } from 'react';
import { getA2AAgents, getA2AProtocolInfo, getMCPTools, getMCPServerInfo } from '../services/api';
import type { A2AAgent, MCPTool } from '../types';

export default function AgentsPage() {
  const [activeTab, setActiveTab] = useState<'agents' | 'mcp' | 'a2a'>('agents');
  const [agents, setAgents] = useState<A2AAgent[]>([]);
  const [mcpTools, setMcpTools] = useState<MCPTool[]>([]);
  const [mcpInfo, setMcpInfo] = useState<any>(null);
  const [a2aInfo, setA2aInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getA2AAgents().catch(() => []),
      getMCPTools().catch(() => []),
      getMCPServerInfo().catch(() => null),
      getA2AProtocolInfo().catch(() => null),
    ]).then(([agts, tools, mInfo, aInfo]) => {
      setAgents(agts);
      setMcpTools(tools);
      setMcpInfo(mInfo);
      setA2aInfo(aInfo);
      setLoading(false);
    });
  }, []);

  return (
    <>
      <div className="page-header">
        <div className="page-title">Agents, MCP & A2A</div>
      </div>

      <div className="page-body">
        <div className="tabs">
          <button className={`tab ${activeTab === 'agents' ? 'active' : ''}`} onClick={() => setActiveTab('agents')}>
            Agent Registry
          </button>
          <button className={`tab ${activeTab === 'mcp' ? 'active' : ''}`} onClick={() => setActiveTab('mcp')}>
            MCP Tools
          </button>
          <button className={`tab ${activeTab === 'a2a' ? 'active' : ''}`} onClick={() => setActiveTab('a2a')}>
            A2A Protocol
          </button>
        </div>

        {loading ? (
          <div className="loading-indicator"><div className="spinner" /><span>Loading agent data...</span></div>
        ) : (
          <>
            {activeTab === 'agents' && (
              <div>
                <div style={{ marginBottom: 16, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  {agents.length} agents registered in the multi-agent system
                </div>
                <div className="agents-grid">
                  {agents.map((agent) => (
                    <div key={agent.id} className="agent-card" data-type={agent.agentType}>
                      <div className="agent-name">{agent.name}</div>
                      <div className="agent-desc">{agent.description}</div>
                      <div className="agent-caps">
                        {agent.capabilities.map((cap, i) => (
                          <span key={i} className="agent-cap">{cap}</span>
                        ))}
                      </div>
                      <div style={{ marginTop: 10, fontSize: 11, color: 'var(--color-text-muted)' }}>
                        Endpoint: <code style={{ fontFamily: 'var(--font-mono)' }}>{agent.endpoint}</code>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'mcp' && (
              <div>
                {mcpInfo && (
                  <div className="card" style={{ marginBottom: 16 }}>
                    <div className="card-header">MCP Server Info</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                      <div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Server Name</div>
                        <div style={{ fontSize: 14, fontWeight: 500 }}>{mcpInfo.serverInfo?.name || mcpInfo.name || 'N/A'}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Version</div>
                        <div style={{ fontSize: 14, fontWeight: 500 }}>{mcpInfo.version || 'N/A'}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Protocol Version</div>
                        <div style={{ fontSize: 14, fontWeight: 500 }}>{mcpInfo.protocolVersion || 'N/A'}</div>
                      </div>
                    </div>
                  </div>
                )}

                <div style={{ marginBottom: 16, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  {mcpTools.length} tools available via Model Context Protocol
                </div>
                <div className="agents-grid">
                  {mcpTools.map((tool, i) => (
                    <div key={i} className="card">
                      <div className="card-header">
                        <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-primary)' }}>{tool.name}</code>
                      </div>
                      <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
                        {tool.description}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Input Schema:</div>
                      <pre style={{
                        background: 'var(--color-bg)',
                        padding: 10,
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 11,
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--color-text-secondary)',
                        overflow: 'auto',
                        maxHeight: 150,
                        marginTop: 4,
                      }}>
                        {JSON.stringify(tool.inputSchema, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'a2a' && (
              <div>
                {a2aInfo && (
                  <div className="card" style={{ marginBottom: 16 }}>
                    <div className="card-header">A2A Protocol Status</div>
                    <div className="stats-grid">
                      <div className="stat-card">
                        <div className="stat-label">Registered Agents</div>
                        <div className="stat-value" style={{ color: 'var(--color-primary)' }}>{a2aInfo.agents}</div>
                      </div>
                      <div className="stat-card">
                        <div className="stat-label">Pending Tasks</div>
                        <div className="stat-value" style={{ color: 'var(--color-warning)' }}>{a2aInfo.pendingTasks}</div>
                      </div>
                      <div className="stat-card">
                        <div className="stat-label">Completed Tasks</div>
                        <div className="stat-value" style={{ color: 'var(--color-success)' }}>{a2aInfo.completedTasks}</div>
                      </div>
                      <div className="stat-card">
                        <div className="stat-label">Total Messages</div>
                        <div className="stat-value" style={{ color: 'var(--color-info)' }}>{a2aInfo.totalMessages}</div>
                      </div>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 8 }}>
                      Protocol Version: {a2aInfo.protocolVersion}
                    </div>
                  </div>
                )}

                <div className="card">
                  <div className="card-header">A2A Communication Model</div>
                  <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.8 }}>
                    <p>The Agent-to-Agent (A2A) protocol enables inter-agent communication:</p>
                    <ul style={{ paddingLeft: 20, marginTop: 8 }}>
                      <li><strong>Agent Discovery</strong> — Agents publish their capabilities via Agent Cards</li>
                      <li><strong>Task Delegation</strong> — Agents can send tasks to other agents based on capabilities</li>
                      <li><strong>Feedback Loop</strong> — Agents provide feedback on task results for quality improvement</li>
                      <li><strong>Status Updates</strong> — Real-time status tracking of inter-agent communications</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}

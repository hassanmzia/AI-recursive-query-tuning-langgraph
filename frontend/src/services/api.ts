import axios from 'axios';
import type {
  ExecutionResult,
  Session,
  ConversationMessage,
  Document,
  DashboardData,
  AgentConfig,
  MCPTool,
  A2AAgent,
  SearchResult,
  WorkflowExecution,
} from '../types';

const GATEWAY_URL = process.env.REACT_APP_GATEWAY_URL || 'http://172.168.1.95:3083';

const api = axios.create({
  baseURL: `${GATEWAY_URL}/api`,
  timeout: 300000,
  headers: { 'Content-Type': 'application/json' },
});

// --- Agents / Workflow ---

export async function executeQuery(
  query: string,
  workflowType: string = 'recursive_qa',
  maxIterations: number = 5,
  sessionId?: string,
): Promise<ExecutionResult> {
  const { data } = await api.post('/agents/execute/', {
    query,
    workflow_type: workflowType,
    max_iterations: maxIterations,
    session_id: sessionId,
  });
  return data;
}

export async function getExecutions(): Promise<WorkflowExecution[]> {
  const { data } = await api.get('/agents/executions/');
  return data.results || data;
}

export async function getExecution(id: string): Promise<WorkflowExecution> {
  const { data } = await api.get(`/agents/executions/${id}/`);
  return data;
}

export async function getWorkflowVisualization(type: string = 'recursive_qa'): Promise<{ mermaid_diagram: string }> {
  const { data } = await api.get(`/agents/visualize/?type=${type}`);
  return data;
}

export async function getAgentConfigs(): Promise<AgentConfig[]> {
  const { data } = await api.get('/agents/configs/');
  return data.results || data;
}

// --- Documents ---

export async function getDocuments(): Promise<Document[]> {
  const { data } = await api.get('/documents/');
  return data.results || data;
}

export async function uploadDocument(file: File, title?: string, description?: string): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);
  if (title) formData.append('title', title);
  if (description) formData.append('description', description);
  const { data } = await api.post('/documents/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function searchDocuments(query: string, topK: number = 5): Promise<SearchResult[]> {
  const { data } = await api.post('/documents/search/', { query, top_k: topK });
  return data.results || [];
}

// --- Conversations ---

export async function getSessions(): Promise<Session[]> {
  const { data } = await api.get('/conversations/sessions/');
  return data.results || data;
}

export async function getSession(id: string): Promise<Session> {
  const { data } = await api.get(`/conversations/sessions/${id}/`);
  return data;
}

export async function createSession(title?: string): Promise<Session> {
  const { data } = await api.post('/conversations/sessions/', { title: title || '' });
  return data;
}

export async function getSessionMessages(sessionId: string): Promise<ConversationMessage[]> {
  const { data } = await api.get(`/conversations/sessions/${sessionId}/messages/`);
  return data;
}

export async function addMessage(sessionId: string, role: string, content: string): Promise<ConversationMessage> {
  const { data } = await api.post(`/conversations/sessions/${sessionId}/add_message/`, {
    role,
    content,
  });
  return data;
}

// --- Analytics ---

export async function getDashboard(): Promise<DashboardData> {
  const { data } = await api.get('/analytics/dashboard/');
  return data;
}

export async function submitFeedback(
  executionId: string,
  score: number,
  scoreType: string = 'user_satisfaction',
  feedback?: string,
): Promise<void> {
  await api.post('/analytics/feedback/', {
    execution_id: executionId,
    score,
    score_type: scoreType,
    feedback: feedback || '',
  });
}

// --- MCP ---

export async function getMCPTools(): Promise<MCPTool[]> {
  const { data } = await api.get('/agents/mcp/?action=tools');
  return data.tools || [];
}

export async function getMCPServerInfo(): Promise<any> {
  const { data } = await api.get('/agents/mcp/');
  return data;
}

export async function callMCPTool(toolName: string, args: Record<string, any>): Promise<any> {
  const { data } = await api.post('/agents/mcp/', {
    tool_name: toolName,
    arguments: args,
  });
  return data;
}

// --- A2A ---

export async function getA2AAgents(): Promise<A2AAgent[]> {
  const { data } = await api.get('/agents/a2a/?action=discover');
  return data.agents || [];
}

export async function getA2AProtocolInfo(): Promise<any> {
  const { data } = await api.get('/agents/a2a/');
  return data;
}

// --- Health ---

export async function healthCheck(): Promise<any> {
  const { data } = await api.get('/health/');
  return data;
}

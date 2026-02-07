// ============================================================================
// Core Application Types
// ============================================================================

export interface WorkflowExecution {
  id: string;
  workflow_type: 'recursive_qa' | 'multi_agent';
  status: 'pending' | 'running' | 'completed' | 'failed';
  input_query: string;
  final_answer: string;
  total_iterations: number;
  duration_ms: number | null;
  execution_trace: TraceItem[];
  mermaid_diagram: string;
  nodes_visited: string[];
  created_at: string;
}

export interface TraceItem {
  node: string;
  detail: string;
  timestamp: number;
  agent?: string;
  action?: string;
  score?: number;
  iteration?: number;
}

export interface ExecutionResult {
  execution_id: string;
  status: string;
  answer: string;
  workflow_type: string;
  duration_ms: number;
  trace: TraceItem[];
  mermaid_diagram: string;
  messages: MessageItem[];
  summary?: string;
  critique_score?: number;
}

export interface MessageItem {
  role: 'ai' | 'human' | 'tool' | 'unknown';
  content: string;
  tool_calls?: any[];
}

export interface Session {
  id: string;
  title: string;
  is_active: boolean;
  message_count: number;
  last_message?: {
    role: string;
    content: string;
    created_at: string;
  };
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: string;
  session: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  workflow_execution_id?: string;
  created_at: string;
}

export interface Document {
  id: string;
  title: string;
  description: string;
  document_type: 'pdf' | 'docx' | 'txt';
  file_size: number;
  page_count: number;
  chunk_count: number;
  status: 'uploaded' | 'processing' | 'indexed' | 'failed';
  uploaded_at: string;
}

export interface AgentConfig {
  id: string;
  name: string;
  agent_type: string;
  agent_type_display: string;
  description: string;
  model_name: string;
  temperature: number;
  is_active: boolean;
}

export interface DashboardData {
  overview: {
    total_executions: number;
    completed_executions: number;
    failed_executions: number;
    success_rate: number;
    average_duration_ms: number;
    total_sessions: number;
    active_sessions: number;
    total_documents: number;
    indexed_documents: number;
    average_quality_score: number | null;
  };
  recent_executions: WorkflowExecution[];
  workflow_distribution: Array<{ workflow_type: string; count: number }>;
  status_distribution: Array<{ status: string; count: number }>;
}

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: Record<string, any>;
}

export interface A2AAgent {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  endpoint: string;
  agentType: string;
}

export interface SearchResult {
  content: string;
  metadata: Record<string, any>;
  score: number;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

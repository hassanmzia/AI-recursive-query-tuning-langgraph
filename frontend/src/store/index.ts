import { create } from 'zustand';
import type {
  Session,
  ConversationMessage,
  ExecutionResult,
  DashboardData,
  Document,
  TraceItem,
} from '../types';

interface AppState {
  // Active session
  currentSessionId: string | null;
  sessions: Session[];
  messages: ConversationMessage[];

  // Query execution
  isExecuting: boolean;
  currentResult: ExecutionResult | null;
  executionHistory: ExecutionResult[];

  // UI state
  activeTab: string;
  sidebarOpen: boolean;
  workflowType: 'recursive_qa' | 'multi_agent';

  // Dashboard
  dashboardData: DashboardData | null;

  // Documents
  documents: Document[];

  // WebSocket
  wsConnected: boolean;
  streamingTrace: TraceItem[];

  // Actions
  setCurrentSession: (id: string | null) => void;
  setSessions: (sessions: Session[]) => void;
  setMessages: (messages: ConversationMessage[]) => void;
  addMessage: (message: ConversationMessage) => void;
  setIsExecuting: (val: boolean) => void;
  setCurrentResult: (result: ExecutionResult | null) => void;
  addExecutionToHistory: (result: ExecutionResult) => void;
  setActiveTab: (tab: string) => void;
  setSidebarOpen: (open: boolean) => void;
  setWorkflowType: (type: 'recursive_qa' | 'multi_agent') => void;
  setDashboardData: (data: DashboardData | null) => void;
  setDocuments: (docs: Document[]) => void;
  setWsConnected: (connected: boolean) => void;
  addStreamingTrace: (trace: TraceItem) => void;
  clearStreamingTrace: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentSessionId: null,
  sessions: [],
  messages: [],

  isExecuting: false,
  currentResult: null,
  executionHistory: [],

  activeTab: 'chat',
  sidebarOpen: true,
  workflowType: 'recursive_qa',

  dashboardData: null,
  documents: [],

  wsConnected: false,
  streamingTrace: [],

  setCurrentSession: (id) => set({ currentSessionId: id }),
  setSessions: (sessions) => set({ sessions }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((s) => ({ messages: [...s.messages, message] })),
  setIsExecuting: (val) => set({ isExecuting: val }),
  setCurrentResult: (result) => set({ currentResult: result }),
  addExecutionToHistory: (result) =>
    set((s) => ({ executionHistory: [result, ...s.executionHistory].slice(0, 50) })),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setWorkflowType: (type) => set({ workflowType: type }),
  setDashboardData: (data) => set({ dashboardData: data }),
  setDocuments: (docs) => set({ documents: docs }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  addStreamingTrace: (trace) => set((s) => ({ streamingTrace: [...s.streamingTrace, trace] })),
  clearStreamingTrace: () => set({ streamingTrace: [] }),
}));

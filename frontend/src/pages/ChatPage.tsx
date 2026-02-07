import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAppStore } from '../store';
import { executeQuery, createSession, addMessage as apiAddMessage } from '../services/api';
import ExecutionTrace from '../components/ExecutionTrace';
import type { ExecutionResult, ConversationMessage } from '../types';

export default function ChatPage() {
  const [input, setInput] = useState('');
  const [localMessages, setLocalMessages] = useState<Array<{
    role: string;
    content: string;
    result?: ExecutionResult;
  }>>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const isExecuting = useAppStore((s) => s.isExecuting);
  const setIsExecuting = useAppStore((s) => s.setIsExecuting);
  const workflowType = useAppStore((s) => s.workflowType);
  const setWorkflowType = useAppStore((s) => s.setWorkflowType);
  const addExecutionToHistory = useAppStore((s) => s.addExecutionToHistory);
  const currentSessionId = useAppStore((s) => s.currentSessionId);
  const setCurrentSession = useAppStore((s) => s.setCurrentSession);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [localMessages, isExecuting, scrollToBottom]);

  const handleSubmit = async () => {
    const query = input.trim();
    if (!query || isExecuting) return;

    setInput('');
    setLocalMessages((prev) => [...prev, { role: 'user', content: query }]);
    setIsExecuting(true);

    try {
      // Ensure we have a session
      let sessionId = currentSessionId;
      if (!sessionId) {
        const session = await createSession(query.slice(0, 80));
        sessionId = session.id;
        setCurrentSession(sessionId);
      }

      // Save user message
      await apiAddMessage(sessionId!, 'user', query).catch(() => {});

      // Execute query
      const result = await executeQuery(query, workflowType, 5, sessionId!);

      setLocalMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.answer,
          result,
        },
      ]);
      addExecutionToHistory(result);

      // Save assistant message
      await apiAddMessage(sessionId!, 'assistant', result.answer).catch(() => {});
    } catch (err: any) {
      setLocalMessages((prev) => [
        ...prev,
        {
          role: 'system',
          content: `Error: ${err.response?.data?.error || err.message || 'Failed to execute query'}`,
        },
      ]);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <>
      <div className="page-header">
        <div className="page-title">Recursive Query & Answer</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Engine:</span>
          <div className="workflow-selector">
            <button
              className={`workflow-option ${workflowType === 'recursive_qa' ? 'active' : ''}`}
              onClick={() => setWorkflowType('recursive_qa')}
            >
              Recursive ReAct QA
            </button>
            <button
              className={`workflow-option ${workflowType === 'multi_agent' ? 'active' : ''}`}
              onClick={() => setWorkflowType('multi_agent')}
            >
              Multi-Agent
            </button>
          </div>
        </div>
      </div>

      <div className="chat-container" style={{ flex: 1 }}>
        <div className="chat-messages">
          {localMessages.length === 0 && (
            <div style={{ textAlign: 'center', marginTop: 80 }}>
              <h2 style={{ fontSize: 22, fontWeight: 600, marginBottom: 8 }}>
                AI Recursive Query Tuning
              </h2>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 14, maxWidth: 500, margin: '0 auto', lineHeight: 1.7 }}>
                Ask questions about the indexed research papers. The system uses LangGraph
                with adaptive ReAct patterns to retrieve, grade, rewrite, and generate answers recursively.
              </p>
              <div style={{ marginTop: 24, display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
                {[
                  'What are the key aspects of Agentic AI systems?',
                  'Give me the abstract for the Agentic AI for Scientific Discovery paper',
                  'How do multi-agent systems contribute to AGI?',
                ].map((q, i) => (
                  <button
                    key={i}
                    className="btn btn-secondary btn-sm"
                    onClick={() => { setInput(q); }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {localMessages.map((msg, i) => (
            <div key={i}>
              <div className={`chat-message ${msg.role}`}>
                <div>{msg.content}</div>
                {msg.result && (
                  <div className="message-meta">
                    {msg.result.workflow_type === 'multi_agent' ? 'Multi-Agent' : 'Recursive ReAct'} |{' '}
                    {msg.result.duration_ms}ms
                    {msg.result.critique_score && ` | Quality: ${msg.result.critique_score}/10`}
                  </div>
                )}
              </div>
              {msg.result?.trace && msg.result.trace.length > 0 && (
                <div style={{ maxWidth: '80%' }}>
                  <ExecutionTrace trace={msg.result.trace} />
                </div>
              )}
              {msg.result?.summary && (
                <div style={{ maxWidth: '80%', marginTop: 8 }}>
                  <div className="trace-panel">
                    <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4, color: '#9da2c2' }}>
                      Summary
                    </div>
                    <div style={{ fontSize: 13, color: '#e4e6f0' }}>{msg.result.summary}</div>
                  </div>
                </div>
              )}
            </div>
          ))}

          {isExecuting && (
            <div className="loading-indicator">
              <div className="spinner" />
              <span>Processing with {workflowType === 'multi_agent' ? 'Multi-Agent' : 'Recursive ReAct'} workflow...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <div className="chat-input-row">
            <textarea
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about the research papers..."
              rows={1}
              disabled={isExecuting}
            />
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={isExecuting || !input.trim()}
            >
              {isExecuting ? <div className="spinner" /> : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

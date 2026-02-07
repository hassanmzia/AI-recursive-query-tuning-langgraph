import React, { useEffect, useState } from 'react';
import { getWorkflowVisualization } from '../services/api';
import MermaidDiagram from '../components/MermaidDiagram';

export default function WorkflowPage() {
  const [activeTab, setActiveTab] = useState<'recursive_qa' | 'multi_agent'>('recursive_qa');
  const [mermaidChart, setMermaidChart] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getWorkflowVisualization(activeTab)
      .then((data) => setMermaidChart(data.mermaid_diagram))
      .catch(() => setMermaidChart(getDefaultDiagram(activeTab)))
      .finally(() => setLoading(false));
  }, [activeTab]);

  return (
    <>
      <div className="page-header">
        <div className="page-title">Workflow Visualization</div>
      </div>

      <div className="page-body">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'recursive_qa' ? 'active' : ''}`}
            onClick={() => setActiveTab('recursive_qa')}
          >
            Recursive ReAct QA
          </button>
          <button
            className={`tab ${activeTab === 'multi_agent' ? 'active' : ''}`}
            onClick={() => setActiveTab('multi_agent')}
          >
            Multi-Agent Orchestration
          </button>
        </div>

        <div className="card">
          <div className="card-header">
            {activeTab === 'recursive_qa'
              ? 'Adaptive ReAct QA Workflow (LangGraph)'
              : 'Multi-Agent Orchestration Workflow'}
          </div>

          {loading ? (
            <div className="loading-indicator"><div className="spinner" /><span>Loading visualization...</span></div>
          ) : (
            <MermaidDiagram
              chart={mermaidChart}
              id={`workflow-${activeTab}`}
            />
          )}
        </div>

        <div className="card">
          <div className="card-header">Workflow Description</div>
          {activeTab === 'recursive_qa' ? (
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.8 }}>
              <p><strong>Adaptive ReAct QA Workflow</strong> — Based on the LangGraph framework</p>
              <ul style={{ paddingLeft: 20, marginTop: 8 }}>
                <li><strong>generate_query_or_respond</strong> — Entry point: decides whether to answer directly or use RAG retrieval</li>
                <li><strong>retrieve (ToolNode)</strong> — Fetches relevant research paper chunks from the ChromaDB vector store</li>
                <li><strong>grade_documents</strong> — Evaluates document relevance with a binary yes/no score</li>
                <li><strong>rewrite_question</strong> — Refines unclear or off-topic queries for better retrieval</li>
                <li><strong>generate_answer</strong> — Produces the final answer from retrieved context (max 3 sentences)</li>
              </ul>
              <p style={{ marginTop: 8 }}>The workflow loops recursively: if retrieved documents are not relevant, the question is rewritten and retrieval is attempted again.</p>
            </div>
          ) : (
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.8 }}>
              <p><strong>Multi-Agent Orchestration Workflow</strong> — Coordinated agent team</p>
              <ul style={{ paddingLeft: 20, marginTop: 8 }}>
                <li><strong>Research Agent</strong> — Searches and analyzes relevant research paper content</li>
                <li><strong>QA Specialist</strong> — Synthesizes research findings into clear answers</li>
                <li><strong>Critique Agent</strong> — Evaluates answer quality (1-10 score) and provides feedback</li>
                <li><strong>Revision Agent</strong> — Improves the answer based on critique feedback</li>
                <li><strong>Summarizer</strong> — Creates a concise final summary</li>
              </ul>
              <p style={{ marginTop: 8 }}>The critique-revision loop continues until the answer quality meets the threshold or max iterations are reached.</p>
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">Mermaid Source</div>
          <pre style={{
            background: 'var(--color-bg)',
            padding: 16,
            borderRadius: 'var(--radius-md)',
            fontSize: 12,
            fontFamily: 'var(--font-mono)',
            color: 'var(--color-text-secondary)',
            overflow: 'auto',
            maxHeight: 300,
          }}>
            {mermaidChart}
          </pre>
        </div>
      </div>
    </>
  );
}

function getDefaultDiagram(type: string): string {
  if (type === 'recursive_qa') {
    return `graph TD
    __start__([Start]) --> generate_query_or_respond
    generate_query_or_respond -->|uses tools| retrieve
    generate_query_or_respond -->|direct answer| __end__([End])
    retrieve --> grade_documents{Grade Documents}
    grade_documents -->|relevant| generate_answer
    grade_documents -->|not relevant| rewrite_question
    rewrite_question --> generate_query_or_respond
    generate_answer --> __end__([End])

    style __start__ fill:#4CAF50,color:#fff
    style __end__ fill:#f44336,color:#fff
    style generate_query_or_respond fill:#2196F3,color:#fff
    style retrieve fill:#FF9800,color:#fff
    style grade_documents fill:#9C27B0,color:#fff
    style rewrite_question fill:#FF5722,color:#fff
    style generate_answer fill:#00BCD4,color:#fff`;
  }
  return `graph TD
    __start__([Start]) --> research_agent[Research Agent]
    research_agent --> qa_specialist[QA Specialist]
    qa_specialist --> critique_agent[Critique Agent]
    critique_agent -->|needs revision| revision_agent[Revision Agent]
    critique_agent -->|accepted| summarizer[Summarizer]
    revision_agent --> critique_agent
    summarizer --> __end__([End])

    style __start__ fill:#4CAF50,color:#fff
    style __end__ fill:#f44336,color:#fff
    style research_agent fill:#2196F3,color:#fff
    style qa_specialist fill:#FF9800,color:#fff
    style critique_agent fill:#9C27B0,color:#fff
    style revision_agent fill:#FF5722,color:#fff
    style summarizer fill:#00BCD4,color:#fff`;
}

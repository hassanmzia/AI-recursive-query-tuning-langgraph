import React, { useEffect, useState, useRef } from 'react';
import { getDocuments, uploadDocument, searchDocuments } from '../services/api';
import type { Document, SearchResult } from '../types';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getDocuments()
      .then(setDocuments)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const doc = await uploadDocument(file);
      setDocuments((prev) => [doc, ...prev]);
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const results = await searchDocuments(searchQuery);
      setSearchResults(results);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const statusBadge = (status: string) => {
    const cls = status === 'indexed' ? 'badge-success'
      : status === 'processing' ? 'badge-warning'
      : status === 'failed' ? 'badge-error'
      : 'badge-info';
    return <span className={`badge ${cls}`}>{status}</span>;
  };

  return (
    <>
      <div className="page-header">
        <div className="page-title">Document Management</div>
        <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
          {uploading ? 'Uploading...' : 'Upload Document'}
        </button>
        <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt" style={{ display: 'none' }} onChange={handleUpload} />
      </div>

      <div className="page-body">
        {/* Search Section */}
        <div className="card">
          <div className="card-header">Vector Store Search</div>
          <div style={{ display: 'flex', gap: 10 }}>
            <input
              type="text"
              className="chat-input"
              style={{ flex: 1, minHeight: 40 }}
              placeholder="Search indexed documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button className="btn btn-primary" onClick={handleSearch} disabled={searching}>
              {searching ? <div className="spinner" /> : 'Search'}
            </button>
          </div>

          {searchResults.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 8 }}>
                {searchResults.length} results found
              </div>
              {searchResults.map((result, i) => (
                <div key={i} style={{
                  padding: 12,
                  background: 'var(--color-bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: 8,
                }}>
                  <div style={{ fontSize: 13, color: 'var(--color-text)', lineHeight: 1.6 }}>
                    {result.content.slice(0, 300)}
                    {result.content.length > 300 && '...'}
                  </div>
                  <div style={{ display: 'flex', gap: 12, marginTop: 6, fontSize: 11, color: 'var(--color-text-muted)' }}>
                    <span>Score: {result.score.toFixed(4)}</span>
                    {result.metadata?.source && <span>Source: {result.metadata.source.split('/').pop()}</span>}
                    {result.metadata?.page !== undefined && <span>Page: {result.metadata.page + 1}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upload Zone */}
        <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
          <h3>Drop files here or click to upload</h3>
          <p>Supports PDF, DOCX, and TXT files. Documents will be indexed into the vector store.</p>
        </div>

        {/* Documents Grid */}
        <div style={{ marginTop: 24 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>
            Indexed Documents ({documents.length})
          </h3>
          {loading ? (
            <div className="loading-indicator"><div className="spinner" /><span>Loading documents...</span></div>
          ) : documents.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', color: 'var(--color-text-muted)' }}>
              No documents indexed yet. Upload research papers to get started.
            </div>
          ) : (
            <div className="doc-grid">
              {documents.map((doc) => (
                <div key={doc.id} className="doc-card">
                  <div className="doc-title">{doc.title}</div>
                  {doc.description && (
                    <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
                      {doc.description}
                    </div>
                  )}
                  <div className="doc-meta">
                    {statusBadge(doc.status)}
                    <span>{doc.document_type.toUpperCase()}</span>
                    <span>{doc.chunk_count} chunks</span>
                    {doc.page_count > 0 && <span>{doc.page_count} pages</span>}
                    {doc.file_size > 0 && <span>{(doc.file_size / 1024).toFixed(0)} KB</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

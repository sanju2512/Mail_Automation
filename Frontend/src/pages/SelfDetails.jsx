import React, { useState, useRef } from "react";
import { 
  Upload, 
  Search, 
  Database, 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  Cpu, 
  Layers, 
  Sparkles,
  ArrowRight
} from "lucide-react";
import { ingestRAGKnowledge, searchRAGKnowledge } from "../api";

export default function SelfDetails({ setCurrentRoute }) {
  const [docType, setDocType] = useState("policy");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  // Semantic Search State
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [searchTopK, setSearchTopK] = useState(3);

  const fileInputRef = useRef(null);

  const handleUploadKnowledge = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setErrorMessage("Only PDF documents (.pdf) can be ingested into the RAG knowledge base.");
      return;
    }

    setIsUploading(true);
    setErrorMessage("");
    setUploadResult(null);

    try {
      const res = await ingestRAGKnowledge(file, docType);
      setUploadResult({
        filename: res.filename,
        chunks: res.chunks_indexed,
        status: res.status
      });
    } catch (err) {
      setErrorMessage(`Knowledge ingestion failed: ${err.message}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleSearchKnowledge = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setErrorMessage("");
    try {
      const res = await searchRAGKnowledge(searchQuery, searchTopK);
      setSearchResults(res.results || []);
    } catch (err) {
      setErrorMessage(`RAG search failed: ${err.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "20px" }}>
      {/* Page Header */}
      <div style={{ marginBottom: "20px" }}>
        <div className="card-label">RAG Knowledge Management</div>
        <h1 style={{ fontSize: "18px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
          Self Details & Knowledge Base Ingestion
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "12.5px", marginTop: "4px" }}>
          Upload personal profile documents, company policies, and domain specifications to feed ChromaDB vector storage for agent retrieval.
        </p>
      </div>

      {errorMessage && (
        <div className="notification-banner error">
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <AlertCircle size={15} />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage("")} style={{ background: "none", border: "none", color: "inherit", cursor: "pointer" }}>✕</button>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* Left Column: Knowledge Document Ingestion */}
        <div className="card">
          <div className="card-header">
            <div>
              <span className="card-label">RAG Document Ingestion</span>
              <h3 className="card-title" style={{ fontSize: "14px" }}>Upload Knowledge Reference PDF</h3>
            </div>
            <Database size={16} color="var(--accent-blue)" />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {/* Document Type Selector */}
            <div>
              <label 
                style={{ 
                  display: "block", 
                  fontSize: "11px", 
                  fontFamily: "var(--font-mono)", 
                  textTransform: "uppercase", 
                  color: "var(--text-secondary)",
                  marginBottom: "6px",
                  fontWeight: 600
                }}
              >
                Document Classification / Category
              </label>
              <select 
                value={docType} 
                onChange={(e) => setDocType(e.target.value)}
                style={{ cursor: "pointer" }}
              >
                <option value="policy">Company Policy & Regulations</option>
                <option value="self_details">Personal Profile & Credentials (Self Details)</option>
                <option value="handbook">Employee Handbook & Operational Guide</option>
                <option value="template_specs">Document Template Guidelines & Rules</option>
                <option value="financial_rules">Financial & Invoice Verification Specs</option>
              </select>
            </div>

            {/* Drag & Drop / File Upload Card */}
            <div
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: "1px dashed var(--border-default)",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--bg-input)",
                padding: "32px 20px",
                textAlign: "center",
                cursor: "pointer",
                transition: "all 0.15s ease"
              }}
              onMouseEnter={(e) => e.currentTarget.style.borderColor = "var(--border-focus)"}
              onMouseLeave={(e) => e.currentTarget.style.borderColor = "var(--border-default)"}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleUploadKnowledge}
                accept=".pdf"
                style={{ display: "none" }}
              />

              <Upload size={28} style={{ margin: "0 auto 10px", color: "var(--accent-blue)", opacity: 0.9 }} />
              <div style={{ fontWeight: 600, fontSize: "13px", color: "var(--text-primary)" }}>
                {isUploading ? "Chunking & Vectorizing Document..." : "Click to select or drop Knowledge PDF"}
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px", fontFamily: "var(--font-mono)" }}>
                Supports PDF up to 20MB • Automated PyMuPDF chunking & all-MiniLM-L6-v2 embeddings
              </div>
            </div>

            {/* Ingestion Success Feedback */}
            {uploadResult && (
              <div 
                style={{
                  padding: "12px",
                  backgroundColor: "rgba(16, 185, 129, 0.08)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "4px"
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#34d399", fontWeight: 600 }}>
                  <CheckCircle2 size={14} />
                  <span>Document Successfully Vectorized in ChromaDB!</span>
                </div>
                <div className="font-mono" style={{ color: "var(--text-secondary)", fontSize: "11.5px" }}>
                  File: <span style={{ color: "var(--text-primary)" }}>{uploadResult.filename}</span>
                </div>
                <div className="font-mono" style={{ color: "var(--text-secondary)", fontSize: "11.5px" }}>
                  Chunks Indexed: <span style={{ color: "var(--accent-blue)" }}>{uploadResult.chunks} text segments</span>
                </div>
              </div>
            )}

            {/* Shortcut to Show Downloads */}
            <div style={{ paddingTop: "6px", borderTop: "1px solid var(--border-subtle)" }}>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => setCurrentRoute("showdownloads")}
                style={{ width: "100%", justifyContent: "space-between" }}
              >
                <span>View all indexed documents in Show Downloads</span>
                <ArrowRight size={13} />
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: RAG Semantic Search Inspector */}
        <div className="card">
          <div className="card-header">
            <div>
              <span className="card-label">Vector Retrieval Tester</span>
              <h3 className="card-title" style={{ fontSize: "14px" }}>Test RAG Semantic Search</h3>
            </div>
            <Sparkles size={16} color="var(--accent-amber-light)" />
          </div>

          <form onSubmit={handleSearchKnowledge} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", gap: "8px" }}>
              <div style={{ position: "relative", flex: 1 }}>
                <input
                  type="text"
                  placeholder="Enter a test query (e.g. 'verification rules', 'employee policy')..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ paddingLeft: "30px" }}
                />
                <Search size={14} style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
              </div>

              <select
                value={searchTopK}
                onChange={(e) => setSearchTopK(Number(e.target.value))}
                style={{ width: "90px" }}
              >
                <option value={2}>Top 2</option>
                <option value={3}>Top 3</option>
                <option value={5}>Top 5</option>
              </select>

              <button type="submit" className="btn btn-primary" disabled={isSearching || !searchQuery.trim()}>
                {isSearching ? "Searching..." : "Search"}
              </button>
            </div>
          </form>

          {/* Results List */}
          <div style={{ marginTop: "14px" }}>
            <div style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "8px" }}>
              Retrieved Context Chunks {searchResults ? `(${searchResults.length})` : ""}
            </div>

            {searchResults === null ? (
              <div style={{ padding: "30px 10px", textAlign: "center", color: "var(--text-muted)", fontSize: "12px" }}>
                Enter a query above to inspect what context chunks will be retrieved by the Qwen LLM orchestrator.
              </div>
            ) : searchResults.length === 0 ? (
              <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontSize: "12px" }}>
                No matching semantic chunks found in ChromaDB collection.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "340px", overflowY: "auto" }}>
                {searchResults.map((r, idx) => (
                  <div
                    key={idx}
                    style={{
                      backgroundColor: "var(--bg-input)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-sm)",
                      padding: "10px",
                      fontSize: "12px"
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                      <span className="badge badge-mono">
                        {r.source} {r.page ? `• p.${r.page}` : ""}
                      </span>
                      <span className="badge badge-emerald font-mono">
                        Score: {r.score}
                      </span>
                    </div>
                    <div style={{ color: "var(--text-primary)", whiteSpace: "pre-wrap", lineHeight: 1.4, fontSize: "11.5px" }}>
                      {r.text}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

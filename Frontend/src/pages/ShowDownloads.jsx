import React, { useState, useEffect } from "react";
import { 
  FileText, 
  Database, 
  Download, 
  Eye, 
  Trash2, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Layers, 
  BookOpen,
  ArrowUpRight,
  HardDrive
} from "lucide-react";
import { 
  listDocuments, 
  deleteDocument, 
  listRAGDocuments, 
  deleteRAGDocument,
  getDocumentDownloadUrl,
  getDocumentViewUrl,
  getRAGDocumentViewUrl
} from "../api";

export default function ShowDownloads({ onOpenPdfViewer }) {
  const [pipelineDocs, setPipelineDocs] = useState([]);
  const [ragDocs, setRagDocs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [bannerMessage, setBannerMessage] = useState(null);

  const fetchAllData = async () => {
    setIsLoading(true);
    try {
      const [docsRes, ragRes] = await Promise.all([
        listDocuments(),
        listRAGDocuments()
      ]);
      setPipelineDocs(docsRes || []);
      setRagDocs(ragRes || []);
    } catch (err) {
      console.error("Error loading documents:", err);
      setBannerMessage({
        type: "error",
        text: `Failed to load document records: ${err.message}`
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  // Delete Processed / Ingested Document
  const handleDeletePipelineDoc = async (id, name) => {
    if (!window.confirm(`Are you sure you want to permanently delete document "${id} (${name})"?`)) return;

    try {
      await deleteDocument(id);
      setBannerMessage({
        type: "success",
        text: `Document ${id} successfully deleted.`
      });
      await fetchAllData();
    } catch (err) {
      setBannerMessage({
        type: "error",
        text: `Failed to delete document: ${err.message}`
      });
    }
  };

  // Delete RAG Knowledge Document
  const handleDeleteRAGDoc = async (filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}" and its vector embeddings from ChromaDB?`)) return;

    try {
      await deleteRAGDocument(filename);
      setBannerMessage({
        type: "success",
        text: `Knowledge document "${filename}" and ChromaDB vectors successfully deleted.`
      });
      await fetchAllData();
    } catch (err) {
      setBannerMessage({
        type: "error",
        text: `Failed to delete RAG document: ${err.message}`
      });
    }
  };

  return (
    <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "20px" }}>
      {/* Top Header & Refresh */}
      <div 
        style={{ 
          display: "flex", 
          alignItems: "center", 
          justifyContent: "space-between", 
          marginBottom: "16px",
          flexWrap: "wrap",
          gap: "12px"
        }}
      >
        <div>
          <div className="card-label">Storage & Repository Inspector</div>
          <h1 style={{ fontSize: "18px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
            Show Downloads & Document Split View
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "12px", marginTop: "2px" }}>
            Dual-pane view of all active pipeline PDFs and vectorized RAG knowledge documents.
          </p>
        </div>

        <button
          className="btn btn-secondary"
          onClick={fetchAllData}
          disabled={isLoading}
        >
          <RefreshCw size={13} className={isLoading ? "animate-spin" : ""} />
          <span>Refresh Files</span>
        </button>
      </div>

      {/* Banner Feedback */}
      {bannerMessage && (
        <div className={`notification-banner ${bannerMessage.type}`}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {bannerMessage.type === "success" && <CheckCircle2 size={15} />}
            {bannerMessage.type === "error" && <AlertCircle size={15} />}
            <span>{bannerMessage.text}</span>
          </div>
          <button 
            onClick={() => setBannerMessage(null)}
            style={{ background: "none", border: "none", color: "inherit", cursor: "pointer" }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Split Page: 2 Columns */}
      <div className="split-view-container">
        {/* Left Column: Downloaded & Processed Pipeline PDFs */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <FileText size={16} color="var(--accent-blue)" />
              <div>
                <span className="card-label">Processed & Pipeline Files</span>
                <h3 className="card-title" style={{ fontSize: "14px" }}>
                  Active PDFs ({pipelineDocs.length})
                </h3>
              </div>
            </div>
            <span className="badge badge-mono">data/input & data/output</span>
          </div>

          {pipelineDocs.length === 0 ? (
            <div style={{ padding: "40px 20px", textAlign: "center", color: "var(--text-muted)", fontSize: "12px" }}>
              <FileText size={28} style={{ margin: "0 auto 8px", opacity: 0.3 }} />
              No pipeline documents found.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {pipelineDocs.map((doc) => (
                <div
                  key={doc.id}
                  style={{
                    backgroundColor: "var(--bg-input)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-sm)",
                    padding: "12px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                        <span className="badge badge-mono font-mono" style={{ color: "var(--accent-blue)", fontWeight: 600 }}>
                          {doc.id}
                        </span>
                        <span className={`badge ${doc.status === "COMPLETED" ? "badge-emerald" : "badge-blue"}`}>
                          {doc.status}
                        </span>
                      </div>
                      <div style={{ fontWeight: 600, fontSize: "13px", color: "var(--text-primary)", wordBreak: "break-all" }}>
                        {doc.filename}
                      </div>
                      {doc.output_filename && (
                        <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: "2px" }}>
                          Output: {doc.output_filename}
                        </div>
                      )}
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "6px", flexShrink: 0 }}>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => onOpenPdfViewer({
                          title: doc.filename,
                          url: getDocumentViewUrl(doc.id, "auto"),
                          downloadUrl: doc.output_filename ? getDocumentDownloadUrl(doc.id) : null
                        })}
                        title="View Document inline"
                      >
                        <Eye size={12} />
                        <span>View</span>
                      </button>

                      {doc.output_filename && (
                        <a
                          href={getDocumentDownloadUrl(doc.id)}
                          download
                          className="btn btn-secondary btn-sm"
                          title="Download Generated Output PDF"
                          target="_blank"
                          rel="noreferrer"
                        >
                          <Download size={12} />
                        </a>
                      )}

                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDeletePipelineDoc(doc.id, doc.filename)}
                        title="Delete Document"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: RAG Feeded Documents */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Database size={16} color="var(--accent-amber-light)" />
              <div>
                <span className="card-label">Vector Knowledge Base</span>
                <h3 className="card-title" style={{ fontSize: "14px" }}>
                  RAG Feeded Documents ({ragDocs.length})
                </h3>
              </div>
            </div>
            <span className="badge badge-mono">ChromaDB + data/knowledge_base</span>
          </div>

          {ragDocs.length === 0 ? (
            <div style={{ padding: "40px 20px", textAlign: "center", color: "var(--text-muted)", fontSize: "12px" }}>
              <BookOpen size={28} style={{ margin: "0 auto 8px", opacity: 0.3 }} />
              No RAG knowledge documents ingested yet. Go to Self Details to upload.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {ragDocs.map((rDoc) => (
                <div
                  key={rDoc.filename}
                  style={{
                    backgroundColor: "var(--bg-input)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-sm)",
                    padding: "12px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                        <span className="badge badge-amber font-mono">
                          {rDoc.chunks_indexed} CHUNKS INDEXED
                        </span>
                        <span className="badge badge-mono">
                          {rDoc.file_size_mb} MB
                        </span>
                      </div>
                      <div style={{ fontWeight: 600, fontSize: "13px", color: "var(--text-primary)", wordBreak: "break-all" }}>
                        {rDoc.filename}
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "6px", flexShrink: 0 }}>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => onOpenPdfViewer({
                          title: rDoc.filename,
                          url: getRAGDocumentViewUrl(rDoc.filename),
                          downloadUrl: getRAGDocumentViewUrl(rDoc.filename)
                        })}
                        title="View Knowledge Document"
                      >
                        <Eye size={12} />
                        <span>View</span>
                      </button>

                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDeleteRAGDoc(rDoc.filename)}
                        title="Delete from knowledge base & ChromaDB"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

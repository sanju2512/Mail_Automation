import React, { useState, useEffect, useRef } from "react";
import { 
  Mail, 
  Upload, 
  RefreshCw, 
  Play, 
  Download, 
  Eye, 
  Trash2, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  FileText, 
  FileCheck, 
  Layers, 
  ShieldCheck, 
  ArrowRight,
  Database,
  ExternalLink,
  ChevronRight
} from "lucide-react";
import { 
  listDocuments, 
  getDocumentDetails, 
  uploadDocument, 
  checkEmailInbox, 
  processDocument, 
  deleteDocument,
  getDocumentDownloadUrl,
  getDocumentViewUrl
} from "../api";

const PIPELINE_STAGES = [
  { key: "RECEIVED", num: 1, label: "Received", desc: "PDF Ingested" },
  { key: "TEXT_EXTRACTED", num: 2, label: "PDF Text", desc: "PyMuPDF Parse" },
  { key: "UNDERSTANDING", num: 3, label: "Understand", desc: "Type Classification" },
  { key: "RETRIEVING", num: 4, label: "RAG Context", desc: "ChromaDB Retrieval" },
  { key: "EXTRACTING", num: 5, label: "Qwen LLM", desc: "Field Extraction" },
  { key: "VALIDATING", num: 6, label: "Validate", desc: "Schema & Logic Checks" },
  { key: "COMPLETED", num: 7, label: "Completed", desc: "Output PDF Ready" }
];

export default function Dashboard({ setCurrentRoute, onOpenPdfViewer }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [activeDoc, setActiveDoc] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingEmail, setIsCheckingEmail] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState(null);
  const [bannerMessage, setBannerMessage] = useState(null);
  const fileInputRef = useRef(null);

  // Load document list
  const fetchDocuments = async (autoSelectLatest = false) => {
    setIsLoading(true);
    try {
      const data = await listDocuments();
      setDocuments(data || []);
      if (data && data.length > 0) {
        if (!selectedDocId || autoSelectLatest) {
          selectDocument(data[0].id);
        }
      } else {
        setActiveDoc(null);
        setSelectedDocId(null);
      }
    } catch (err) {
      console.error("Failed to fetch documents:", err);
      setBannerMessage({
        type: "error",
        text: `Failed to load document records: ${err.message}`
      });
    } finally {
      setIsLoading(false);
    }
  };

  const selectDocument = async (id) => {
    setSelectedDocId(id);
    try {
      const details = await getDocumentDetails(id);
      setActiveDoc(details);
    } catch (err) {
      console.error("Failed to load document details:", err);
    }
  };

  useEffect(() => {
    fetchDocuments(true);
  }, []);

  // Check Email Action
  const handleCheckEmail = async () => {
    setIsCheckingEmail(true);
    setBannerMessage({
      type: "info",
      text: "Checking configured IMAP mailbox for new incoming PDF attachments..."
    });
    try {
      const res = await checkEmailInbox();
      setBannerMessage({
        type: "success",
        text: `Mail check completed: ${res.emails_processed} emails scanned, ${res.documents_detected} new documents ingested.`
      });
      await fetchDocuments(true);
    } catch (err) {
      setBannerMessage({
        type: "error",
        text: `Email check failed: ${err.message}`
      });
    } finally {
      setIsCheckingEmail(false);
    }
  };

  // Upload Document Action
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setBannerMessage({
        type: "error",
        text: "Please select a valid PDF document (.pdf)."
      });
      return;
    }

    setIsLoading(true);
    setBannerMessage({
      type: "info",
      text: `Uploading and parsing ${file.name}...`
    });

    try {
      const res = await uploadDocument(file);
      setBannerMessage({
        type: "success",
        text: `Document uploaded: ID ${res.document_id} (${res.pages} pages extracted).`
      });
      await fetchDocuments();
      await selectDocument(res.document_id);
    } catch (err) {
      setBannerMessage({
        type: "error",
        text: `Upload failed: ${err.message}`
      });
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Execute Agentic Pipeline Action
  const handleExecutePipeline = async () => {
    if (!selectedDocId) return;
    setIsProcessing(true);
    setProcessingStage("UNDERSTANDING");
    setBannerMessage({
      type: "info",
      text: `Executing multi-agent orchestration for document ${selectedDocId}...`
    });

    // Simulate animated step progression for great UX while waiting for backend
    const timer1 = setTimeout(() => setProcessingStage("RETRIEVING"), 1200);
    const timer2 = setTimeout(() => setProcessingStage("EXTRACTING"), 2600);
    const timer3 = setTimeout(() => setProcessingStage("VALIDATING"), 4800);

    try {
      const res = await processDocument(selectedDocId);
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      setProcessingStage("COMPLETED");

      setBannerMessage({
        type: "success",
        text: `Pipeline executed successfully! Output generated: ${res.output_filename || 'completed.pdf'}`
      });
      await selectDocument(selectedDocId);
      await fetchDocuments();
    } catch (err) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      setProcessingStage(null);
      setBannerMessage({
        type: "error",
        text: `Pipeline execution failed: ${err.message}`
      });
    } finally {
      setIsProcessing(false);
      setTimeout(() => setProcessingStage(null), 3000);
    }
  };

  // Delete Document Action
  const handleDeleteDoc = async (id, e) => {
    if (e) e.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete document ${id}?`)) return;

    try {
      await deleteDocument(id);
      setBannerMessage({
        type: "success",
        text: `Document ${id} successfully deleted.`
      });
      if (selectedDocId === id) {
        setSelectedDocId(null);
        setActiveDoc(null);
      }
      await fetchDocuments(true);
    } catch (err) {
      setBannerMessage({
        type: "error",
        text: `Failed to delete document: ${err.message}`
      });
    }
  };

  // Compute Active Step Status
  const getStageStatus = (stageKey, index) => {
    const stageOrder = [
      "RECEIVED",
      "TEXT_EXTRACTED",
      "UNDERSTANDING",
      "RETRIEVING",
      "EXTRACTING",
      "VALIDATING",
      "COMPLETED"
    ];

    const currentDocStatus = isProcessing && processingStage 
      ? processingStage 
      : activeDoc?.status || "RECEIVED";

    const currentIdx = stageOrder.indexOf(currentDocStatus);
    const thisIdx = stageOrder.indexOf(stageKey);

    if (currentDocStatus === "FAILED" || currentDocStatus === "EXTRACTION_FAILED") {
      if (thisIdx === 0) return "completed";
      return "error";
    }

    if (thisIdx < currentIdx || (currentDocStatus === "COMPLETED" && thisIdx <= currentIdx)) {
      return "completed";
    }
    if (thisIdx === currentIdx) {
      return isProcessing ? "active" : (currentDocStatus === "COMPLETED" ? "completed" : "active");
    }
    return "pending";
  };

  const confidenceScore = activeDoc?.confidence_score 
    ? Math.round(activeDoc.confidence_score * 100) 
    : 0;

  return (
    <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "20px" }}>
      {/* Top Banner Message */}
      {bannerMessage && (
        <div className={`notification-banner ${bannerMessage.type}`}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {bannerMessage.type === "success" && <CheckCircle2 size={15} />}
            {bannerMessage.type === "error" && <AlertCircle size={15} />}
            {bannerMessage.type === "info" && <Clock size={15} />}
            <span>{bannerMessage.text}</span>
          </div>
          <button 
            onClick={() => setBannerMessage(null)}
            style={{ background: "none", border: "none", color: "inherit", cursor: "pointer", fontSize: "12px" }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Action Toolbar & Navigation Shortcuts */}
      <div 
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "16px",
          gap: "12px",
          flexWrap: "wrap"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {/* Check Mail Button */}
          <button
            id="btnCheckMail"
            className="btn btn-primary"
            onClick={handleCheckEmail}
            disabled={isCheckingEmail}
          >
            <Mail size={14} className={isCheckingEmail ? "animate-spin" : ""} />
            <span>{isCheckingEmail ? "Checking Mailbox..." : "Check Mail"}</span>
          </button>

          {/* Upload PDF */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf"
            style={{ display: "none" }}
          />
          <button
            id="btnUploadDoc"
            className="btn btn-secondary"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
          >
            <Upload size={14} />
            <span>Upload PDF</span>
          </button>

          <button
            className="btn btn-outline"
            onClick={() => fetchDocuments()}
            disabled={isLoading}
            title="Refresh documents list"
          >
            <RefreshCw size={13} className={isLoading ? "animate-spin" : ""} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Route Navigation Shortcuts */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button
            id="btnNavDownloads"
            className="btn btn-outline btn-sm"
            onClick={() => setCurrentRoute("showdownloads")}
          >
            <Download size={13} />
            <span>Show Downloads</span>
            <ChevronRight size={12} color="var(--text-muted)" />
          </button>

          <button
            id="btnNavSelfDetails"
            className="btn btn-outline btn-sm"
            onClick={() => setCurrentRoute("selfdetails")}
          >
            <Database size={13} />
            <span>Self Details</span>
            <ChevronRight size={12} color="var(--text-muted)" />
          </button>
        </div>
      </div>

      {/* Main Inspector Panel: Active Workflow State Machine */}
      <section className="main-inspector-panel">
        <div className="card stepper-card">
          <div className="card-header flex-between">
            <div>
              <span className="card-label">Active Workflow State Machine</span>
              <h2 className="card-title" id="activeDocTitle">
                {activeDoc ? `${activeDoc.id} — ${activeDoc.filename}` : "Select a document to begin"}
              </h2>
            </div>
            <div className="action-buttons" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              {activeDoc?.output_filename && (
                <a
                  href={getDocumentDownloadUrl(activeDoc.id)}
                  download
                  className="btn btn-secondary"
                  target="_blank"
                  rel="noreferrer"
                >
                  <Download size={14} />
                  <span>Download Output PDF</span>
                </a>
              )}

              <button 
                className="btn btn-primary" 
                id="btnProcessDoc" 
                disabled={!activeDoc || isProcessing || activeDoc.status === "COMPLETED"}
                onClick={handleExecutePipeline}
              >
                <Play size={14} />
                <span>{isProcessing ? "Executing Orchestration..." : "🚀 Execute Agentic Pipeline"}</span>
              </button>
            </div>
          </div>

          {/* Visual Workflow Stages (7 Stages) */}
          <div className="pipeline-stepper" id="pipelineStepper">
            {PIPELINE_STAGES.map((st, idx) => {
              const statusClass = getStageStatus(st.key, idx);
              const isLast = idx === PIPELINE_STAGES.length - 1;
              const lineCompleted = statusClass === "completed";

              return (
                <React.Fragment key={st.key}>
                  <div className={`step ${statusClass}`} data-step={st.key}>
                    <div className="step-circle">
                      {statusClass === "completed" ? "✓" : st.num}
                    </div>
                    <span className="step-label">{st.label}</span>
                  </div>
                  {!isLast && <div className={`step-line ${lineCompleted ? "completed" : ""}`} />}
                </React.Fragment>
              );
            })}
          </div>

          {/* Active Document Details & Metadata Inspector */}
          {activeDoc && (
            <div 
              style={{
                marginTop: "16px",
                paddingTop: "14px",
                borderTop: "1px solid var(--border-subtle)",
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                gap: "14px"
              }}
            >
              {/* Telemetry Column */}
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Execution Telemetry
                </div>
                <div className="kv-grid">
                  <div className="kv-key">Document ID</div>
                  <div className="kv-value">{activeDoc.id}</div>

                  <div className="kv-key">Type</div>
                  <div className="kv-value">{activeDoc.document_type || "Pending Classification"}</div>

                  <div className="kv-key">Status</div>
                  <div className="kv-value">
                    <span className={`badge ${activeDoc.status === "COMPLETED" ? "badge-emerald" : "badge-blue"}`}>
                      {activeDoc.status}
                    </span>
                  </div>

                  <div className="kv-key">Pages</div>
                  <div className="kv-value">{activeDoc.page_count || 1}</div>

                  <div className="kv-key">Validation</div>
                  <div className="kv-value">
                    <span className={`badge ${activeDoc.validation_status === "VALID" ? "badge-emerald" : "badge-amber"}`}>
                      {activeDoc.validation_status || "PENDING"}
                    </span>
                  </div>
                </div>

                {/* Confidence Score Monospace Progress Bar */}
                <div style={{ marginTop: "4px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                    <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      AI CONFIDENCE
                    </span>
                    <span className="progress-text">{confidenceScore}%</span>
                  </div>
                  <div className="progress-container">
                    <div className="progress-bar-bg">
                      <div 
                        className="progress-bar-fill" 
                        style={{ 
                          width: `${confidenceScore}%`,
                          backgroundColor: confidenceScore > 80 ? "var(--accent-emerald)" : "var(--accent-blue)" 
                        }} 
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Extracted Fields & RAG Context Summary */}
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)", textTransform: "uppercase" }}>
                    Extracted Fields (Qwen LLM)
                  </span>
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => onOpenPdfViewer({
                      title: activeDoc.filename,
                      url: getDocumentViewUrl(activeDoc.id, "auto"),
                      downloadUrl: getDocumentDownloadUrl(activeDoc.id)
                    })}
                  >
                    <Eye size={12} />
                    <span>View PDF</span>
                  </button>
                </div>

                <div 
                  style={{
                    backgroundColor: "var(--bg-input)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-sm)",
                    padding: "10px",
                    maxHeight: "180px",
                    overflowY: "auto",
                    fontFamily: "var(--font-mono)",
                    fontSize: "11.5px"
                  }}
                >
                  {activeDoc.extracted_data && Object.keys(activeDoc.extracted_data).length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                      {Object.entries(activeDoc.extracted_data).map(([k, v]) => (
                        <div key={k} style={{ display: "flex", justifyContent: "space-between", gap: "10px" }}>
                          <span style={{ color: "var(--text-muted)" }}>{k}:</span>
                          <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>
                            {typeof v === "object" ? JSON.stringify(v) : String(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ color: "var(--text-muted)", fontStyle: "italic", textAlign: "center", padding: "12px 0" }}>
                      No fields extracted yet. Click "Execute Agentic Pipeline".
                    </div>
                  )}
                </div>

                {/* Validation Warnings / Missing Fields */}
                {activeDoc.validation_warnings && activeDoc.validation_warnings.length > 0 && (
                  <div style={{ fontSize: "11px", color: "var(--accent-amber-light)", display: "flex", alignItems: "center", gap: "6px" }}>
                    <AlertCircle size={13} />
                    <span>Warnings: {activeDoc.validation_warnings.join(", ")}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Down: Download Processed File & Document Queue Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <span className="card-label">Document Execution Queue</span>
            <h3 className="card-title" style={{ fontSize: "14px" }}>
              Tracked Pipeline Documents ({documents.length})
            </h3>
          </div>
          <span style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
            Select row to inspect state machine
          </span>
        </div>

        {documents.length === 0 ? (
          <div style={{ padding: "40px 20px", textAlign: "center", color: "var(--text-muted)" }}>
            <FileText size={32} style={{ margin: "0 auto 10px", opacity: 0.4 }} />
            <div style={{ fontWeight: 500, color: "var(--text-secondary)" }}>No documents in pipeline</div>
            <div style={{ fontSize: "12px", marginTop: "4px" }}>
              Click "Check Mail" to fetch attachments or "Upload PDF" to start.
            </div>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: "120px" }}>Document ID</th>
                  <th>Filename</th>
                  <th style={{ width: "130px" }}>Type</th>
                  <th style={{ width: "120px" }}>Status</th>
                  <th style={{ width: "110px" }}>Confidence</th>
                  <th style={{ width: "140px" }}>Created</th>
                  <th style={{ width: "170px", textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => {
                  const isSelected = selectedDocId === doc.id;
                  const conf = doc.confidence_score ? Math.round(doc.confidence_score * 100) : 0;
                  const formattedDate = doc.created_at 
                    ? new Date(doc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) 
                    : "—";

                  return (
                    <tr 
                      key={doc.id}
                      className={isSelected ? "selected" : ""}
                      onClick={() => selectDocument(doc.id)}
                      style={{ cursor: "pointer" }}
                    >
                      <td className="font-mono" style={{ color: isSelected ? "var(--accent-blue)" : "inherit", fontWeight: 600 }}>
                        {doc.id}
                      </td>
                      <td style={{ fontWeight: 500, maxWidth: "260px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {doc.filename}
                      </td>
                      <td>
                        <span className="badge">
                          {doc.document_type || "general"}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${doc.status === "COMPLETED" ? "badge-emerald" : doc.status === "EXTRACTION_FAILED" ? "badge-rose" : "badge-blue"}`}>
                          {doc.status}
                        </span>
                      </td>
                      <td className="font-mono">
                        {conf > 0 ? `${conf}%` : "—"}
                      </td>
                      <td className="font-mono" style={{ color: "var(--text-muted)", fontSize: "11px" }}>
                        {formattedDate}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <div style={{ display: "inline-flex", alignItems: "center", gap: "6px" }} onClick={(e) => e.stopPropagation()}>
                          {/* Option to download processed file */}
                          {doc.output_filename ? (
                            <a
                              href={getDocumentDownloadUrl(doc.id)}
                              download
                              className="btn btn-secondary btn-sm"
                              title="Download processed document"
                              target="_blank"
                              rel="noreferrer"
                            >
                              <Download size={12} />
                              <span>Download</span>
                            </a>
                          ) : (
                            <button
                              className="btn btn-outline btn-sm"
                              onClick={() => {
                                selectDocument(doc.id);
                                handleExecutePipeline();
                              }}
                              title="Process document"
                            >
                              <Play size={12} />
                              <span>Run</span>
                            </button>
                          )}

                          <button
                            className="btn btn-outline btn-sm"
                            onClick={() => onOpenPdfViewer({
                              title: doc.filename,
                              url: getDocumentViewUrl(doc.id, "auto"),
                              downloadUrl: doc.output_filename ? getDocumentDownloadUrl(doc.id) : null
                            })}
                            title="Preview PDF"
                          >
                            <Eye size={12} />
                          </button>

                          <button
                            className="btn btn-danger btn-sm"
                            onClick={(e) => handleDeleteDoc(doc.id, e)}
                            title="Delete document"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

import React from "react";
import { X, Download, ExternalLink, FileText } from "lucide-react";

export default function PdfViewerModal({ isOpen, onClose, title, url, downloadUrl }) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div 
        className="modal-dialog" 
        style={{ width: "95vw", maxWidth: "1100px", height: "88vh" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <FileText size={16} color="var(--accent-blue)" />
            <span style={{ fontWeight: 600, fontSize: "13.5px" }}>{title || "PDF Document Viewer"}</span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {downloadUrl && (
              <a 
                href={downloadUrl} 
                download
                className="btn btn-secondary btn-sm"
                target="_blank"
                rel="noreferrer"
              >
                <Download size={13} />
                <span>Download</span>
              </a>
            )}
            <a 
              href={url} 
              target="_blank" 
              rel="noreferrer" 
              className="btn btn-outline btn-sm"
              title="Open in new browser tab"
            >
              <ExternalLink size={13} />
              <span>New Tab</span>
            </a>
            <button 
              className="btn btn-outline btn-sm" 
              onClick={onClose}
              style={{ padding: "4px 8px" }}
            >
              <X size={15} />
            </button>
          </div>
        </div>

        <div className="modal-body" style={{ padding: 0, backgroundColor: "#06070a", height: "calc(100% - 50px)" }}>
          <iframe
            src={url}
            title={title}
            width="100%"
            height="100%"
            style={{ border: "none", display: "block" }}
          />
        </div>
      </div>
    </div>
  );
}

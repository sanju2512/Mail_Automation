// API client for Mail Automation Backend
const API_BASE = "https://mail-automation-ln3d.onrender.com";

export async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === "string"
            ? errorData.detail
            : JSON.stringify(errorData.detail);
        }
      } catch (e) {
        // ignore json parse error
      }
      throw new Error(errorMessage);
    }
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return await response.json();
    }
    return response;
  } catch (err) {
    console.error(`API error at ${endpoint}:`, err);
    throw err;
  }
}

// Health API
export async function getHealth() {
  return request("/health");
}

// Email Automation APIs
export async function checkEmailInbox() {
  return request("/email/check", { method: "POST" });
}

export async function testEmailConnection() {
  return request("/email/test", { method: "GET" });
}

// Document APIs
export async function listDocuments() {
  return request("/documents/");
}

export async function getDocumentDetails(documentId) {
  return request(`/documents/${documentId}`);
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/documents/upload", {
    method: "POST",
    body: formData,
  });
}

export async function extractDocument(documentId) {
  return request(`/documents/${documentId}/extract`, { method: "POST" });
}

export async function processDocument(documentId) {
  return request(`/documents/${documentId}/process`, { method: "POST" });
}

export async function deleteDocument(documentId) {
  return request(`/documents/${documentId}`, { method: "DELETE" });
}

export function getDocumentDownloadUrl(documentId) {
  return `${API_BASE}/documents/${documentId}/download`;
}

export function getDocumentViewUrl(documentId, fileType = "auto") {
  return `${API_BASE}/documents/${documentId}/view?file_type=${fileType}`;
}

// RAG / Knowledge Base APIs
export async function listRAGDocuments() {
  return request("/rag/documents");
}

export async function ingestRAGKnowledge(file, documentType = "policy") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_type", documentType);
  return request("/rag/ingest", {
    method: "POST",
    body: formData,
  });
}

export async function searchRAGKnowledge(query, topK = 4, documentType = "") {
  let url = `/rag/search?query=${encodeURIComponent(query)}&top_k=${topK}`;
  if (documentType) {
    url += `&document_type=${encodeURIComponent(documentType)}`;
  }
  return request(url);
}

export async function deleteRAGDocument(filename) {
  return request(`/rag/documents/${encodeURIComponent(filename)}`, {
    method: "DELETE",
  });
}

export function getRAGDocumentViewUrl(filename) {
  return `${API_BASE}/rag/documents/${encodeURIComponent(filename)}/view`;
}

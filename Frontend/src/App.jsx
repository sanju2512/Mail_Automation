import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import SelfDetails from "./pages/SelfDetails";
import ShowDownloads from "./pages/ShowDownloads";
import PdfViewerModal from "./components/PdfViewerModal";

export default function App() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("mailauto_user");
    return saved ? JSON.parse(saved) : null;
  });

  // Current route state: 'dashboard' | 'selfdetails' | 'showdownloads'
  const [currentRoute, setCurrentRoute] = useState("dashboard");

  // PDF Viewer Modal state
  const [pdfModal, setPdfModal] = useState({
    isOpen: false,
    title: "",
    url: "",
    downloadUrl: ""
  });

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    localStorage.setItem("mailauto_user", JSON.stringify(userData));
    setCurrentRoute("dashboard");
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("mailauto_user");
  };

  const openPdfViewer = ({ title, url, downloadUrl }) => {
    setPdfModal({
      isOpen: true,
      title,
      url,
      downloadUrl
    });
  };

  const closePdfViewer = () => {
    setPdfModal({
      isOpen: false,
      title: "",
      url: "",
      downloadUrl: ""
    });
  };

  // If not authenticated, render Login Page
  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", backgroundColor: "var(--bg-app)" }}>
      {/* Top App Header */}
      <Header
        currentRoute={currentRoute}
        setCurrentRoute={setCurrentRoute}
        user={user}
        onLogout={handleLogout}
      />

      {/* Main Routed Page Content */}
      <main style={{ flex: 1 }}>
        {currentRoute === "dashboard" && (
          <Dashboard
            setCurrentRoute={setCurrentRoute}
            onOpenPdfViewer={openPdfViewer}
          />
        )}

        {currentRoute === "selfdetails" && (
          <SelfDetails
            setCurrentRoute={setCurrentRoute}
          />
        )}

        {currentRoute === "showdownloads" && (
          <ShowDownloads
            onOpenPdfViewer={openPdfViewer}
          />
        )}
      </main>

      {/* Global PDF Viewer Modal */}
      <PdfViewerModal
        isOpen={pdfModal.isOpen}
        onClose={closePdfViewer}
        title={pdfModal.title}
        url={pdfModal.url}
        downloadUrl={pdfModal.downloadUrl}
      />
    </div>
  );
}

import React, { useEffect, useState } from "react";
import { 
  FileText, 
  Layers, 
  Download, 
  UserCheck, 
  LogOut, 
  Activity, 
  Terminal 
} from "lucide-react";
import { getHealth } from "../api";

export default function Header({ currentRoute, setCurrentRoute, user, onLogout }) {
  const [systemHealthy, setSystemHealthy] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const checkStatus = async () => {
      try {
        const res = await getHealth();
        if (isMounted) {
          setSystemHealthy(res.status === "healthy");
        }
      } catch (err) {
        if (isMounted) setSystemHealthy(false);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="app-header">
      {/* Brand & System */}
      <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
        <div className="header-brand">
          <div className="brand-icon">
            <Terminal size={15} />
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontWeight: 600, letterSpacing: "-0.01em" }}>MailAuto::Pipeline</span>
            <span style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              v1.0.0-qwen-agentic
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="header-nav">
          <button
            id="nav-dashboard"
            className={`nav-link ${currentRoute === "dashboard" ? "active" : ""}`}
            onClick={() => setCurrentRoute("dashboard")}
          >
            <Layers size={14} />
            <span>Dashboard</span>
          </button>

          <button
            id="nav-showdownloads"
            className={`nav-link ${currentRoute === "showdownloads" ? "active" : ""}`}
            onClick={() => setCurrentRoute("showdownloads")}
          >
            <Download size={14} />
            <span>Show Downloads</span>
          </button>

          <button
            id="nav-selfdetails"
            className={`nav-link ${currentRoute === "selfdetails" ? "active" : ""}`}
            onClick={() => setCurrentRoute("selfdetails")}
          >
            <UserCheck size={14} />
            <span>Self Details</span>
          </button>
        </nav>
      </div>

      {/* Right Controls: Health & User */}
      <div className="header-user">
        <div 
          className="badge badge-mono"
          style={{ 
            display: "flex", 
            alignItems: "center", 
            gap: "5px",
            color: systemHealthy ? "#34d399" : "#f87171",
            borderColor: systemHealthy ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"
          }}
          title={systemHealthy ? "FastAPI & ChromaDB Connected" : "Backend Offline"}
        >
          <Activity size={12} />
          <span>{systemHealthy ? "CORE ONLINE" : "OFFLINE"}</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div 
            style={{ 
              padding: "4px 8px", 
              borderRadius: "var(--radius-xs)", 
              backgroundColor: "var(--bg-surface-elevated)", 
              border: "1px solid var(--border-default)",
              fontSize: "12px",
              fontFamily: "var(--font-mono)",
              display: "flex",
              alignItems: "center",
              gap: "6px"
            }}
          >
            <span style={{ color: "var(--text-muted)" }}>USER:</span>
            <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{user?.username || "Sanjay"}</span>
          </div>

          <button
            id="btn-logout"
            className="btn btn-outline btn-sm"
            onClick={onLogout}
            title="Sign out session"
          >
            <LogOut size={13} />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
}

import React, { useState } from "react";
import { Lock, User, Terminal, AlertCircle, Eye, EyeOff, ShieldCheck } from "lucide-react";

export default function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");

    if (!username.trim()) {
      setError("Username is required.");
      return;
    }
    if (!password) {
      setError("Password is required.");
      return;
    }

    setIsSubmitting(true);

    // Hardcoded credentials check as requested: "Sanjay" / "Sanjay@123"
    setTimeout(() => {
      if (username.trim() === "Sanjay" && password === "Sanjay@123") {
        onLoginSuccess({ username: "Sanjay", role: "Developer/Admin" });
      } else {
        setError("Invalid credentials. Please verify your username and password.");
        setIsSubmitting(false);
      }
    }, 200);
  };

  const handleFillDemo = () => {
    setUsername("Sanjay");
    setPassword("Sanjay@123");
    setError("");
  };

  return (
    <div 
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "var(--bg-app)",
        padding: "20px"
      }}
    >
      <div 
        style={{
          width: "100%",
          maxWidth: "380px",
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-default)",
          borderRadius: "var(--radius-md)",
          overflow: "hidden"
        }}
      >
        {/* Terminal / Tool Header */}
        <div 
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid var(--border-default)",
            backgroundColor: "#0d0f16",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between"
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div className="brand-icon" style={{ width: "24px", height: "24px" }}>
              <Terminal size={14} />
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: "13px", color: "var(--text-primary)" }}>
                Mail Automation Console
              </div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                AUTHENTICATION GATEWAY
              </div>
            </div>
          </div>
          <ShieldCheck size={16} color="var(--text-muted)" />
        </div>

        {/* Login Form Body */}
        <div style={{ padding: "24px 20px" }}>
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {error && (
              <div 
                className="notification-banner error" 
                style={{ padding: "8px 10px", fontSize: "12px", gap: "8px", margin: 0 }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <AlertCircle size={14} style={{ flexShrink: 0 }} />
                  <span>{error}</span>
                </div>
              </div>
            )}

            <div>
              <label 
                htmlFor="username"
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
                Username <span style={{ color: "var(--accent-rose)" }}>*</span>
              </label>
              <div style={{ position: "relative" }}>
                <input
                  id="username"
                  type="text"
                  required
                  placeholder="Enter username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  style={{ paddingLeft: "32px" }}
                  autoComplete="username"
                  autoFocus
                />
                <User 
                  size={14} 
                  style={{ 
                    position: "absolute", 
                    left: "10px", 
                    top: "50%", 
                    transform: "translateY(-50%)", 
                    color: "var(--text-muted)" 
                  }} 
                />
              </div>
            </div>

            <div>
              <label 
                htmlFor="password"
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
                Password <span style={{ color: "var(--accent-rose)" }}>*</span>
              </label>
              <div style={{ position: "relative" }}>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{ paddingLeft: "32px", paddingRight: "36px" }}
                  autoComplete="current-password"
                />
                <Lock 
                  size={14} 
                  style={{ 
                    position: "absolute", 
                    left: "10px", 
                    top: "50%", 
                    transform: "translateY(-50%)", 
                    color: "var(--text-muted)" 
                  }} 
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: "absolute",
                    right: "8px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    background: "none",
                    border: "none",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    padding: "4px"
                  }}
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            <button
              id="btn-login"
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
              style={{ width: "100%", padding: "8px 14px", marginTop: "6px" }}
            >
              {isSubmitting ? "Authenticating..." : "Sign In to Dashboard"}
            </button>
          </form>

          {/* Quick Credential Hint */}
          <div 
            style={{
              marginTop: "20px",
              padding: "10px 12px",
              backgroundColor: "var(--bg-input)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-sm)",
              fontSize: "11px",
              fontFamily: "var(--font-mono)",
              color: "var(--text-muted)",
              display: "flex",
              flexDirection: "column",
              gap: "4px"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: "var(--text-secondary)", fontWeight: 600 }}>Default Access:</span>
              <button 
                type="button" 
                onClick={handleFillDemo}
                style={{ 
                  background: "none", 
                  border: "none", 
                  color: "var(--accent-blue)", 
                  cursor: "pointer",
                  fontSize: "11px",
                  textDecoration: "underline",
                  fontFamily: "inherit"
                }}
              >
                Auto-fill
              </button>
            </div>
            <div>USER: <span style={{ color: "var(--text-primary)" }}>Sanjay</span></div>
            <div>PASS: <span style={{ color: "var(--text-primary)" }}>Sanjay@123</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}

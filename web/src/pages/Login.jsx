import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const result = await signIn({ email, password });
      navigate(result.profile?.user_type === "organiser" ? "/partner" : "/");
    } catch (err) {
      setError(err?.message || "Couldn't sign you in. Check your details.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--color-paper)",
        color: "var(--color-ink)",
        padding: "20px",
      }}
    >
      {/* Brand */}
      <h1
        className="font-display font-extrabold tracking-tight"
        style={{ fontSize: "clamp(32px, 6vw, 60px)", lineHeight: 1, marginBottom: "5px" }}
      >
        FROMO
      </h1>
      <p className="text-muted" style={{ fontSize: "clamp(13px, 1.6vw, 16px)", marginBottom: "30px" }}>
        Discover last-minute activities in Manhattan
      </p>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        style={{
          width: "100%",
          maxWidth: "440px",
          display: "flex",
          flexDirection: "column",
          gap: "20px",
        }}
      >
        <UnderlineField
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          autoComplete="email"
          placeholder="Email"
        />
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <UnderlineField
            label="Password"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={setPassword}
            autoComplete="current-password"
            placeholder="Password"
            rightSlot={
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                style={{ background: "none", border: "none", cursor: "pointer", color: "#999", padding: "0 2px", lineHeight: 1 }}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
              </button>
            }
          />
          <div style={{ textAlign: "right" }}>
            <span
              className="text-muted"
              style={{ fontSize: "13px", cursor: "pointer" }}
            >
              Forgot password?
            </span>
          </div>
        </div>

        {error && (
          <p style={{ color: "#E5533C", fontSize: "13px", margin: 0 }}>{error}</p>
        )}

        <button
          disabled={busy}
          style={{
            background: "#14110E",
            color: "#fff",
            fontWeight: 700,
            fontSize: "clamp(14px, 1.8vw, 18px)",
            padding: "12px",
            borderRadius: "14px",
            border: "none",
            cursor: busy ? "not-allowed" : "pointer",
            opacity: busy ? 0.6 : 1,
            marginTop: "5px",
          }}
        >
          {busy ? "Signing in…" : "Sign In"}
        </button>
      </form>

      <p className="text-muted" style={{ fontSize: "clamp(13px, 1.5vw, 15px)", marginTop: "20px" }}>
        No account yet?{" "}
        <Link to="/signup" className="font-semibold text-ink" style={{ textDecoration: "none", fontWeight: 700, color: "var(--color-ink)" }}>
          Sign up
        </Link>
      </p>
    </div>
  );
}

function UnderlineField({ label, type = "text", value, onChange, placeholder, rightSlot, ...rest }) {
  return (
    <div style={{ position: "relative", display: "flex", flexDirection: "column" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          borderBottom: "1.5px solid #D4C9B8",
          paddingBottom: "8px",
        }}
      >
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder || label}
          required
          style={{
            flex: 1,
            border: "none",
            outline: "none",
            background: "transparent",
            fontSize: "clamp(14px, 1.6vw, 16px)",
            color: "var(--color-ink)",
          }}
          {...rest}
        />
        {rightSlot}
      </div>
    </div>
  );
}

function EyeIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function EyeOffIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}

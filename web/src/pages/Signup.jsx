import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { USER_TYPE } from "../lib/config.js";

export default function Signup() {
  const { signUp } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [userType, setUserType] = useState(USER_TYPE.STUDENT);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setBusy(true);
    try {
      const data = await signUp({ email, password, fullName, userType });
      if (data.session) {
        navigate("/");
      } else {
        setNotice("Check your email to confirm your account, then log in.");
      }
    } catch (err) {
      setError(err?.message || "Couldn't create your account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ maxWidth: "520px", margin: "0 auto", padding: "4rem 2.4rem", display: "flex", flexDirection: "column", justifyContent: "center", flex: 1 }}>
      <h1 className="font-display font-extrabold tracking-tight" style={{ fontSize: "clamp(2.4rem, 4vw, 4.5rem)", lineHeight: 1.02 }}>
        Join FROMO
      </h1>
      <p className="text-muted" style={{ fontSize: "clamp(1.4rem, 1.8vw, 1.8rem)", marginTop: "0.75rem" }}>
        Never miss what's happening on your block.
      </p>

      <div style={{ marginTop: "2rem", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", border: "1px solid #EAE4D9", borderRadius: "16px", padding: "0.5rem", background: "#fff" }}>
        <RoleTab
          label="I'm a student"
          active={userType === USER_TYPE.STUDENT}
          onClick={() => setUserType(USER_TYPE.STUDENT)}
        />
        <RoleTab
          label="I run events"
          active={userType === USER_TYPE.ORGANISER}
          onClick={() => setUserType(USER_TYPE.ORGANISER)}
        />
      </div>

      <form onSubmit={handleSubmit} style={{ marginTop: "1.5rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        <Field label="Full name" value={fullName} onChange={setFullName} autoComplete="name" />
        <Field label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" />
        <PasswordField value={password} onChange={setPassword} show={showPassword} onToggle={() => setShowPassword((v) => !v)} />
        {error && <p style={{ color: "#E5533C", fontSize: "clamp(1.2rem, 1.4vw, 1.4rem)" }}>{error}</p>}
        {notice && <p style={{ color: "#2E9E6B", fontSize: "clamp(1.2rem, 1.4vw, 1.4rem)" }}>{notice}</p>}
        <button
          disabled={busy}
          className="bg-amber font-semibold text-[#231a09] hover:bg-amber-press disabled:opacity-60"
          style={{ fontSize: "clamp(1.4rem, 1.8vw, 1.8rem)", padding: "1.1rem", borderRadius: "14px", marginTop: "0.5rem" }}
        >
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p style={{ fontSize: "clamp(1.3rem, 1.5vw, 1.5rem)", marginTop: "1.5rem" }} className="text-muted">
        Already have an account?{" "}
        <Link to="/login" className="font-semibold text-ink underline">
          Log in
        </Link>
      </p>
    </main>
  );
}

function RoleTab({ label, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{ fontSize: "clamp(1.3rem, 1.5vw, 1.6rem)", padding: "1rem 1.2rem", borderRadius: "10px", fontWeight: 600, transition: "all 0.15s" }}
      className={active ? "bg-amber text-[#231a09]" : "text-muted hover:text-ink"}
    >
      {label}
    </button>
  );
}

function Field({ label, type = "text", value, onChange, ...rest }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      <span style={{ fontSize: "clamp(1.3rem, 1.5vw, 1.6rem)", fontWeight: 500 }}>{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
        className="border border-line bg-surface outline-none focus:border-ink"
        style={{ fontSize: "1.6rem", padding: "1.1rem 1.3rem", borderRadius: "12px" }}
        {...rest}
      />
    </label>
  );
}

function PasswordField({ value, onChange, show, onToggle }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      <span style={{ fontSize: "clamp(1.3rem, 1.5vw, 1.6rem)", fontWeight: 500 }}>Password</span>
      <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
        <input
          type={show ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required
          minLength={6}
          autoComplete="new-password"
          className="border border-line bg-surface outline-none focus:border-ink"
          style={{ fontSize: "1.6rem", padding: "1.1rem 4rem 1.1rem 1.3rem", borderRadius: "12px", width: "100%" }}
        />
        <button
          type="button"
          onClick={onToggle}
          style={{
            position: "absolute",
            right: "1.2rem",
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "#999",
            padding: 0,
            lineHeight: 1,
            display: "flex",
            alignItems: "center",
          }}
          aria-label={show ? "Hide password" : "Show password"}
        >
          {show ? <EyeOffIcon /> : <EyeIcon />}
        </button>
      </div>
    </label>
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

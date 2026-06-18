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
    <main style={{ maxWidth: "820px", margin: "0 auto", padding: "4rem 2rem", display: "flex", flexDirection: "column", justifyContent: "center", flex: 1 }}>
      <h1 className="font-display font-extrabold tracking-tight" style={{ fontSize: "4.5rem", lineHeight: 1.02 }}>
        Join FROMO
      </h1>
      <p className="text-muted" style={{ fontSize: "1.8rem", marginTop: "0.75rem" }}>
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
        <Field label="Password" type="password" value={password} onChange={setPassword} autoComplete="new-password" minLength={6} />
        {error && <p style={{ color: "#E5533C", fontSize: "1.4rem" }}>{error}</p>}
        {notice && <p style={{ color: "#2E9E6B", fontSize: "1.4rem" }}>{notice}</p>}
        <button
          disabled={busy}
          className="bg-amber font-semibold text-[#231a09] hover:bg-amber-press disabled:opacity-60"
          style={{ fontSize: "2rem", padding: "1.3rem", borderRadius: "14px", marginTop: "0.5rem" }}
        >
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p style={{ fontSize: "1.5rem", marginTop: "1.5rem" }} className="text-muted">
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
      style={{ fontSize: "1.6rem", padding: "1rem 1.2rem", borderRadius: "10px", fontWeight: 600, transition: "all 0.15s" }}
      className={active ? "bg-amber text-[#231a09]" : "text-muted hover:text-ink"}
    >
      {label}
    </button>
  );
}

function Field({ label, type = "text", value, onChange, ...rest }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      <span style={{ fontSize: "1.6rem", fontWeight: 500 }}>{label}</span>
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

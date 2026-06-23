import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await signIn({ email, password });
      navigate("/");
    } catch (err) {
      setError(err?.message || "Couldn't sign you in. Check your details.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ maxWidth: "820px", margin: "0 auto", padding: "4rem 2rem", display: "flex", flexDirection: "column", justifyContent: "center", flex: 1 }}>
      <h1 className="font-display font-extrabold tracking-tight" style={{ fontSize: "4.5rem", lineHeight: 1.02 }}>
        Welcome back
      </h1>
      <p className="text-muted" style={{ fontSize: "1.8rem", marginTop: "0.75rem" }}>
        Log in to see what's happening near you.
      </p>

      <form onSubmit={handleSubmit} style={{ marginTop: "2.5rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        <Field label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" />
        <Field label="Password" type="password" value={password} onChange={setPassword} autoComplete="current-password" />
        {error && <p style={{ color: "#E5533C", fontSize: "1.4rem" }}>{error}</p>}
        <button
          disabled={busy}
          className="bg-amber font-semibold text-[#231a09] hover:bg-amber-press disabled:opacity-60"
          style={{ fontSize: "2rem", padding: "1.3rem", borderRadius: "14px", marginTop: "0.5rem" }}
        >
          {busy ? "Logging in…" : "Log in"}
        </button>
      </form>

      <p style={{ fontSize: "1.5rem", marginTop: "1.5rem" }} className="text-muted">
        New to FROMO?{" "}
        <Link to="/signup" className="font-semibold text-ink underline">
          Create an account
        </Link>
      </p>
    </main>
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

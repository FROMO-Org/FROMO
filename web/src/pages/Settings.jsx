import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

export default function Settings() {
  const { user, profile, signOut } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const personalName = profile?.full_name || user?.user_metadata?.full_name || user?.email || "";
  const initials = personalName
    .split(" ")
    .filter(Boolean)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase() || "?";

  async function handleSignOut() {
    await signOut();
    navigate("/");
  }

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 28, fontWeight: 800, fontFamily: '"Bricolage Grotesque", Inter, system-ui', letterSpacing: "-0.02em", margin: "0 0 32px", color: "var(--color-ink)" }}>
        Settings
      </h1>

      {/* Profile */}
      <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 36, paddingBottom: 32, borderBottom: "1px solid var(--color-line)" }}>
        <div style={{ width: 64, height: 64, borderRadius: "50%", background: "#F5A623", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: "#231a09", fontFamily: '"Bricolage Grotesque", Inter, system-ui' }}>
            {initials}
          </span>
        </div>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "var(--color-ink)" }}>{personalName}</div>
          <div style={{ fontSize: 13, color: "var(--color-muted)", marginTop: 2 }}>Student Account</div>
        </div>
      </div>

      {/* Appearance */}
      <Section label="Appearance">
        <ToggleRow label="Dark mode" on={isDark} onToggle={toggleTheme} />
      </Section>

      <Divider />

      {/* Account */}
      <Section label="Account">
        <div style={{ display: "flex", flexDirection: "column", gap: 20, paddingTop: 4 }}>
          <div style={{ fontSize: 14, color: "var(--color-ink)" }}>
            <span style={{ color: "var(--color-muted)", fontSize: 12, display: "block", marginBottom: 2 }}>Email</span>
            {user?.email}
          </div>
          <span style={{ fontSize: 15, color: "var(--color-muted)", cursor: "pointer" }}>Change Password</span>
          <span onClick={handleSignOut} style={{ fontSize: 15, color: "#E53935", cursor: "pointer", fontWeight: 500 }}>
            Log Out
          </span>
        </div>
      </Section>
    </main>
  );
}

function Section({ label, children }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-muted)", marginBottom: 20 }}>
        {label}
      </div>
      {children}
    </div>
  );
}

function Divider() {
  return <div style={{ borderTop: "1px solid var(--color-line)", margin: "32px 0" }} />;
}

function ToggleRow({ label, on, onToggle }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 0", borderBottom: "1px solid var(--color-line)" }}>
      <div style={{ fontSize: 15, fontWeight: 600, color: "var(--color-ink)" }}>{label}</div>
      <button
        onClick={onToggle}
        role="switch"
        aria-checked={on}
        style={{ width: 46, height: 26, borderRadius: 13, background: on ? "#F5A623" : "var(--color-line)", border: "none", cursor: "pointer", padding: 0, position: "relative", transition: "background 0.2s" }}
      >
        <span style={{ position: "absolute", top: 3, left: on ? 23 : 3, width: 20, height: 20, borderRadius: "50%", background: "#fff", transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)" }} />
      </button>
    </div>
  );
}

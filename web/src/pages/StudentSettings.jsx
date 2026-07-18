import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { updateMyProfile } from "../lib/api";

const LS_KEY = "fromo_student_notifs";

function loadNotifs() {
  try {
    return JSON.parse(localStorage.getItem(LS_KEY)) ?? {
      nearbyEvents: true,
      eventReminders: true,
      weeklyPicks: false,
      promoEmails: false,
    };
  } catch {
    return { nearbyEvents: true, eventReminders: true, weeklyPicks: false, promoEmails: false };
  }
}

export default function StudentSettings() {
  const { user, profile, signOut, reloadProfile } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const [form, setForm] = useState({ name: "" });
  const [notifs, setNotifs] = useState(loadNotifs);
  const [saveState, setSaveState] = useState("idle");

  useEffect(() => {
    setForm({
      name: profile?.full_name || user?.user_metadata?.full_name || "",
    });
  }, [profile, user]);

  function handleToggle(key) {
    setNotifs((n) => {
      const next = { ...n, [key]: !n[key] };
      localStorage.setItem(LS_KEY, JSON.stringify(next));
      return next;
    });
  }

  async function handleSave(e) {
    e.preventDefault();
    setSaveState("saving");
    try {
      await updateMyProfile({ full_name: form.name });
      await reloadProfile();
      setSaveState("saved");
      setTimeout(() => setSaveState("idle"), 2500);
    } catch {
      setSaveState("error");
      setTimeout(() => setSaveState("idle"), 2500);
    }
  }

  async function handleSignOut() {
    await signOut();
    navigate("/");
  }

  const initials = (form.name || user?.email || "?")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div style={{ minHeight: "100vh", background: "var(--color-paper)", color: "var(--color-ink)" }}>
      <div style={{ maxWidth: 680, margin: "0 auto", padding: "48px 24px" }}>
        {/* Header */}
        <div style={{ marginBottom: 36, paddingBottom: 24, borderBottom: "1px solid var(--color-line)" }}>
          <h1 style={{ fontSize: 30, fontWeight: 800, fontFamily: '"Bricolage Grotesque", Inter, system-ui', margin: 0, letterSpacing: "-0.02em", color: "var(--color-ink)" }}>
            Settings
          </h1>
        </div>

        {/* Profile */}
        <form onSubmit={handleSave}>
          <SectionLabel>Your Profile</SectionLabel>

          {/* Avatar */}
          <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 28 }}>
            <div style={{
              width: 64, height: 64, borderRadius: "50%",
              background: "#F5A623", display: "flex", alignItems: "center",
              justifyContent: "center", flexShrink: 0,
            }}>
              <span style={{ fontSize: 22, fontWeight: 700, color: "#231a09", fontFamily: '"Bricolage Grotesque", Inter, system-ui' }}>
                {initials}
              </span>
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, color: "var(--color-ink)" }}>
                {form.name || user?.email}
              </div>
              <div style={{ fontSize: 13, color: "var(--color-muted)", marginTop: 2 }}>Student Account</div>
            </div>
          </div>

          <UnderlineField
            label="Full name"
            value={form.name}
            onChange={(v) => setForm((f) => ({ ...f, name: v }))}
          />
          <UnderlineField
            label="Email"
            value={user?.email ?? ""}
            onChange={() => {}}
            type="email"
            readOnly
            hint="Email can't be changed here"
          />

          <button
            type="submit"
            disabled={saveState === "saving"}
            style={{
              background: "var(--color-ink)", color: "var(--color-paper)", border: "none",
              padding: "14px 32px", borderRadius: 8, fontSize: 14,
              fontWeight: 600, cursor: saveState === "saving" ? "wait" : "pointer",
              marginTop: 8, minWidth: 160,
            }}
          >
            {saveState === "saving" ? "Saving…" : saveState === "saved" ? "Saved ✓" : saveState === "error" ? "Error — retry" : "Save Changes"}
          </button>
        </form>

        <Divider />

        {/* Appearance */}
        <SectionLabel>Appearance</SectionLabel>
        <NotifRow
          label="Dark mode"
          on={isDark}
          onToggle={toggleTheme}
        />

        <Divider />

        {/* Preferences */}
        <SectionLabel>Notifications</SectionLabel>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          <NotifRow
            label="Events near me"
            sub="Get notified when new events pop up in your area"
            on={notifs.nearbyEvents}
            onToggle={() => handleToggle("nearbyEvents")}
          />
          <NotifRow
            label="Event reminders"
            sub="Reminder before events you've saved start"
            on={notifs.eventReminders}
            onToggle={() => handleToggle("eventReminders")}
          />
          <NotifRow
            label="Weekly picks"
            sub="A curated list of top events every week"
            on={notifs.weeklyPicks}
            onToggle={() => handleToggle("weeklyPicks")}
          />
          <NotifRow
            label="Promotional emails"
            sub="Updates about new features and FROMO news"
            on={notifs.promoEmails}
            onToggle={() => handleToggle("promoEmails")}
          />
        </div>

        <Divider />

        {/* Account */}
        <SectionLabel>Account</SectionLabel>
        <div style={{ display: "flex", flexDirection: "column", gap: 18, paddingTop: 4 }}>
          <span style={{ fontSize: 15, color: "var(--color-muted)", cursor: "pointer" }}>Change Password</span>
          <span
            onClick={handleSignOut}
            style={{ fontSize: 15, color: "#E53935", cursor: "pointer", fontWeight: 500 }}
          >
            Log Out
          </span>
        </div>
      </div>
    </div>
  );
}

function SectionLabel({ children }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-ink)", marginBottom: 20 }}>
      {children}
    </div>
  );
}

function Divider() {
  return <div style={{ borderTop: "1px solid var(--color-line)", margin: "36px 0" }} />;
}

function UnderlineField({ label, value, onChange, type = "text", readOnly, hint }) {
  return (
    <div style={{ marginBottom: 0 }}>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={label}
        readOnly={readOnly}
        style={{
          width: "100%", background: "none", border: "none",
          borderBottom: "1px solid var(--color-line)", padding: "14px 0",
          fontSize: 15, color: readOnly ? "var(--color-muted)" : "var(--color-ink)",
          outline: "none", boxSizing: "border-box",
          cursor: readOnly ? "default" : "text",
        }}
        onFocus={(e) => { if (!readOnly) e.target.style.borderBottomColor = "var(--color-ink)"; }}
        onBlur={(e) => { e.target.style.borderBottomColor = "var(--color-line)"; }}
      />
      {hint && <div style={{ fontSize: 11, color: "var(--color-muted)", marginTop: 4 }}>{hint}</div>}
    </div>
  );
}

function NotifRow({ label, sub, on, onToggle }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "18px 0", borderBottom: "1px solid var(--color-line-soft)",
    }}>
      <div>
        <div style={{ fontSize: 15, fontWeight: 600, color: "var(--color-ink)" }}>{label}</div>
        {sub && <div style={{ fontSize: 12.5, color: "var(--color-muted)", marginTop: 3 }}>{sub}</div>}
      </div>
      <button
        onClick={onToggle}
        aria-checked={on}
        role="switch"
        style={{
          width: 46, height: 26, borderRadius: 13,
          background: on ? "#F5A623" : "var(--color-line)",
          border: "none", cursor: "pointer", padding: 0,
          position: "relative", flexShrink: 0, transition: "background 0.2s",
        }}
      >
        <span style={{
          position: "absolute", top: 3, left: on ? 23 : 3,
          width: 20, height: 20, borderRadius: "50%", background: "#fff",
          transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
        }} />
      </button>
    </div>
  );
}

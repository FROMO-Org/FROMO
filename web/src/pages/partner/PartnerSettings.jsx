import { useEffect, useState } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";
import { updateMyProfile } from "../../lib/api";

const LS_KEY = "fromo_partner_notifs";

function loadNotifs() {
  try {
    return JSON.parse(localStorage.getItem(LS_KEY)) ?? {
      newBookings: true,
      listingExpiring: true,
      weeklyReport: false,
      promoEmails: false,
    };
  } catch {
    return { newBookings: true, listingExpiring: true, weeklyReport: false, promoEmails: false };
  }
}

export default function PartnerSettings() {
  const { orgData } = useOutletContext();
  const { user, profile, signOut, reloadProfile } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const orgName = orgData?.dashboard?.organisation?.name ?? orgData?.org?.name ?? "";
  const firstVenue = orgData?.dashboard?.listings?.[0]?.venue;

  const personalName = profile?.full_name || user?.user_metadata?.full_name || user?.email || "";
  const initials = personalName
    .split(" ")
    .filter(Boolean)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase() || "?";

  const [form, setForm] = useState({
    name: "",
    address: "",
    email: "",
    phone: "",
  });
  const [notifs, setNotifs] = useState(loadNotifs);
  const [saveState, setSaveState] = useState("idle");

  useEffect(() => {
    setForm({
      name: orgName,
      address: firstVenue?.address ?? "",
      email: user?.email ?? "",
      phone: "",
    });
  }, [orgName, firstVenue, user]);

  function handleField(key, val) {
    setForm((f) => ({ ...f, [key]: val }));
  }

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

  return (
    <div style={{ background: "var(--color-surface)", color: "var(--color-ink)", minHeight: "100%", padding: "40px 48px" }}>
      {/* Header */}
      <div style={{ marginBottom: 32, paddingBottom: 24, borderBottom: "1px solid var(--color-line)" }}>
        <h1
          style={{
            fontSize: 30,
            fontWeight: 800,
            fontFamily: '"Bricolage Grotesque", Inter, system-ui',
            margin: 0,
            letterSpacing: "-0.02em",
            color: "var(--color-ink)",
          }}
        >
          Settings
        </h1>
      </div>

      <div style={{ maxWidth: 680 }}>

        {/* Personal profile row — mirrors Student Settings */}
        <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 36, paddingBottom: 32, borderBottom: "1px solid var(--color-line)" }}>
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
              {personalName}
            </div>
            <div style={{ fontSize: 13, color: "var(--color-muted)", marginTop: 2 }}>Partner Account</div>
          </div>
        </div>

        {/* Venue Profile */}
        <form onSubmit={handleSave}>
          <SectionLabel>Venue Profile</SectionLabel>

          {/* Avatar row */}
          <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 28 }}>
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: "50%",
                background: "var(--color-line)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="3" width="20" height="18" rx="2" />
                <line x1="8" y1="3" x2="8" y2="21" />
                <line x1="16" y1="3" x2="16" y2="21" />
                <line x1="2" y1="9" x2="8" y2="9" />
                <line x1="2" y1="15" x2="8" y2="15" />
                <line x1="16" y1="9" x2="22" y2="9" />
                <line x1="16" y1="15" x2="22" y2="15" />
              </svg>
            </div>
            <span style={{ fontSize: 13, color: "#F5A623", fontWeight: 600, cursor: "pointer" }} >Edit</span>
          </div>

          <UnderlineField label="Venue name" value={form.name} onChange={(v) => handleField("name", v)} />
          <UnderlineField label="Address" value={form.address} onChange={(v) => handleField("address", v)} />
          <UnderlineField label="Contact email" value={form.email} onChange={(v) => handleField("email", v)} type="email" />
          <UnderlineField label="Phone" value={form.phone} onChange={(v) => handleField("phone", v)} type="tel" />

          <button
            type="submit"
            disabled={saveState === "saving"}
            style={{
              background: "var(--color-ink)",
              color: "var(--color-paper)",
              border: "none",
              padding: "14px 32px",
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              cursor: saveState === "saving" ? "wait" : "pointer",
              marginTop: 8,
              minWidth: 160,
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

        {/* Notifications */}
        <SectionLabel>Notifications</SectionLabel>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          <NotifRow
            label="New Bookings"
            sub="Get notified when someone books your event"
            on={notifs.newBookings}
            onToggle={() => handleToggle("newBookings")}
          />
          <NotifRow
            label="Listing Expiring"
            sub="Reminder when your listing is about to expire"
            on={notifs.listingExpiring}
            onToggle={() => handleToggle("listingExpiring")}
          />
          <NotifRow
            label="Weekly Report"
            sub="Receive weekly analytics and performance summary"
            on={notifs.weeklyReport}
            onToggle={() => handleToggle("weeklyReport")}
          />
          <NotifRow
            label="Promotional Emails"
            sub="Updates about new features and partner benefits"
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

function UnderlineField({ label, value, onChange, type = "text" }) {
  return (
    <div style={{ marginBottom: 0 }}>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={label}
        style={{
          width: "100%",
          background: "none",
          border: "none",
          borderBottom: "1px solid var(--color-line)",
          padding: "14px 0",
          fontSize: 15,
          color: "var(--color-ink)",
          outline: "none",
          boxSizing: "border-box",
        }}
        onFocus={(e) => { e.target.style.borderBottomColor = "var(--color-ink)"; }}
        onBlur={(e) => { e.target.style.borderBottomColor = "var(--color-line)"; }}
      />
    </div>
  );
}

function NotifRow({ label, sub, on, onToggle }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "18px 0",
        borderBottom: "1px solid var(--color-line-soft)",
      }}
    >
      <div>
        <div style={{ fontSize: 15, fontWeight: 600, color: "var(--color-ink)" }}>{label}</div>
        {sub && <div style={{ fontSize: 12.5, color: "var(--color-muted)", marginTop: 3 }}>{sub}</div>}
      </div>
      <button
        onClick={onToggle}
        aria-checked={on}
        role="switch"
        style={{
          width: 46,
          height: 26,
          borderRadius: 13,
          background: on ? "#F5A623" : "var(--color-line)",
          border: "none",
          cursor: "pointer",
          padding: 0,
          position: "relative",
          flexShrink: 0,
          transition: "background 0.2s",
        }}
      >
        <span
          style={{
            position: "absolute",
            top: 3,
            left: on ? 23 : 3,
            width: 20,
            height: 20,
            borderRadius: "50%",
            background: "#fff",
            transition: "left 0.2s",
            boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
          }}
        />
      </button>
    </div>
  );
}

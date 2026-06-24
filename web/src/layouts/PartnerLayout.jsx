import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getMyOrganisations, getOrganisationDashboard } from "../lib/api";

export default function PartnerLayout() {
  const { signOut, user, profile } = useAuth();
  const navigate = useNavigate();
  const [orgData, setOrgData] = useState(null);
  const [loadState, setLoadState] = useState("loading");

  useEffect(() => {
    let alive = true;
    getMyOrganisations()
      .then((orgs) => {
        if (!alive) return;
        if (!orgs.length) { setLoadState("no-org"); return; }
        const org = orgs[0].organisation;
        return getOrganisationDashboard(org.id).then((dashboard) => {
          if (!alive) return;
          setOrgData({ org, dashboard });
          setLoadState("ready");
        });
      })
      .catch(() => alive && setLoadState("error"));
    return () => { alive = false; };
  }, []);

  async function handleSignOut() {
    await signOut();
    navigate("/");
  }

  const orgName = orgData?.dashboard?.organisation?.name
    ?? orgData?.org?.name
    ?? null;

  const displayName = orgName
    ?? profile?.full_name
    ?? user?.user_metadata?.full_name
    ?? user?.email
    ?? "Partner";

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", fontFamily: "Inter, system-ui, sans-serif" }}>
      {/* Sidebar */}
      <aside style={{ width: 240, background: "#111", color: "#fff", display: "flex", flexDirection: "column", flexShrink: 0 }}>
        {/* Brand */}
        <div style={{ padding: "28px 24px 24px" }}>
          <div style={{ fontFamily: '"Bricolage Grotesque", Inter, system-ui', fontWeight: 800, fontSize: 22, color: "#fff", letterSpacing: "-0.02em" }}>
            FROMO
          </div>
          <div style={{ color: "#777", fontSize: 12, marginTop: 3 }}>Partner</div>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: "0 12px" }}>
          <SideNavLink to="/partner" end icon={<ListIcon />} label="My Listings" />
          <SideNavLink to="/partner/analytics" icon={<BarIcon />} label="Analytics" />
          <SideNavLink to="/partner/settings" icon={<GearIcon />} label="Settings" />
        </nav>

        {/* Venue name */}
        <div style={{ padding: "16px 24px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
          <div style={{ fontSize: 12, color: "#666", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {displayName}
          </div>
          <button
            onClick={handleSignOut}
            style={{ background: "none", border: "none", cursor: "pointer", color: "#555", fontSize: 11, marginTop: 6, padding: 0 }}
          >
            Log out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main style={{ flex: 1, overflowY: "auto", background: "#f7f2eb" }}>
        {loadState === "loading" && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#888", fontSize: 14 }}>
            Loading…
          </div>
        )}
        {loadState === "no-org" && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 12, textAlign: "center", padding: 48 }}>
            <div style={{ fontSize: 32, marginBottom: 4 }}>🏢</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: "#111", fontFamily: '"Bricolage Grotesque", Inter, system-ui' }}>
              No organisation linked yet
            </div>
            <div style={{ fontSize: 14, color: "#888", maxWidth: 360, lineHeight: 1.6 }}>
              Your account isn't connected to a venue or organisation. Ask your team admin to add you, or create one to get started.
            </div>
          </div>
        )}
        {loadState === "error" && (
          <div style={{ padding: 48, color: "#888", fontSize: 14 }}>
            Couldn't load dashboard — is the backend running?
          </div>
        )}
        {loadState === "ready" && <Outlet context={{ orgData }} />}
      </main>
    </div>
  );
}

function SideNavLink({ to, end, icon, label }) {
  return (
    <NavLink
      to={to}
      end={end}
      style={({ isActive }) => ({
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "10px 12px",
        paddingLeft: isActive ? 10 : 12,
        marginBottom: 2,
        borderRadius: 7,
        borderLeft: isActive ? "2px solid #F5A623" : "2px solid transparent",
        color: isActive ? "#fff" : "#777",
        textDecoration: "none",
        fontSize: 14,
        fontWeight: isActive ? 600 : 500,
        transition: "color 0.12s",
      })}
    >
      {icon}
      {label}
    </NavLink>
  );
}

function ListIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="currentColor">
      <rect x="0" y="1" width="3" height="2" rx="0.5" />
      <rect x="5" y="1" width="10" height="2" rx="0.5" />
      <rect x="0" y="6.5" width="3" height="2" rx="0.5" />
      <rect x="5" y="6.5" width="10" height="2" rx="0.5" />
      <rect x="0" y="12" width="3" height="2" rx="0.5" />
      <rect x="5" y="12" width="10" height="2" rx="0.5" />
    </svg>
  );
}

function BarIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="currentColor">
      <rect x="0" y="9" width="3" height="6" rx="0.5" />
      <rect x="6" y="5" width="3" height="10" rx="0.5" />
      <rect x="12" y="1" width="3" height="14" rx="0.5" />
    </svg>
  );
}

function GearIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

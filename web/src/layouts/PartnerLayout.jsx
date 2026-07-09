import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate, useLocation, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getMyOrganisations, getOrganisationDashboard, createOrganisation, updateMyProfile } from "../lib/api";
import { USER_TYPE } from "../lib/config";

export default function PartnerLayout() {
  const { signOut, user, profile, reloadProfile, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const isSettings = pathname === "/partner/settings";
  const [orgData, setOrgData] = useState(null);
  const [loadState, setLoadState] = useState("loading");
  const [orgName, setOrgName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState(null);

  useEffect(() => {
    let alive = true;
    getMyOrganisations()
      .then((orgs) => {
        if (!alive) return;
        if (!orgs.length) { setLoadState("no-org"); return; }
        const org = orgs[0].organisation;
        return getOrganisationDashboard(org.id).then(async (dashboard) => {
          if (!alive) return;
          setOrgData({ org, dashboard });
          setLoadState("ready");
          // Fix stale user_type — if they have an org they ARE an organiser
          if (profile?.user_type !== USER_TYPE.ORGANISER) {
            await updateMyProfile({ user_type: USER_TYPE.ORGANISER });
          }
          reloadProfile();
        });
      })
      .catch(() => alive && setLoadState("error"));
    return () => { alive = false; };
  }, []);

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  async function handleSignOut() {
    await signOut();
    navigate("/");
  }

  async function handleCreateOrg(e) {
    e.preventDefault();
    if (!orgName.trim()) return;
    setCreating(true);
    setCreateError(null);
    try {
      const { organisation } = await createOrganisation(orgName.trim());
      const dashboard = await getOrganisationDashboard(organisation.id);
      setOrgData({ org: organisation, dashboard });
      setLoadState("ready");
      await reloadProfile(); // updates user_type → "organiser" so Dashboard button appears
    } catch (err) {
      setCreateError(err?.response?.data?.detail ?? "Couldn't create organisation.");
    } finally {
      setCreating(false);
    }
  }

  const orgDisplayName = orgData?.dashboard?.organisation?.name
    ?? orgData?.org?.name
    ?? null;

  const displayName = orgDisplayName
    ?? profile?.full_name
    ?? user?.user_metadata?.full_name
    ?? user?.email
    ?? "Partner";

  // Not logged in → send to login
  if (!authLoading && !user) return <Navigate to="/login" replace />;

  // Gate: only confirmed organisers see the dashboard layout.
  // Everyone else (null profile, student, admin) is blocked here.
  if (profile?.user_type !== USER_TYPE.ORGANISER) {
    // org check finished with no org → definitely not an organiser, go home
    if (loadState === "no-org") return <Navigate to="/" replace />;
    // still loading (or org found but user_type stale — reloadProfile in flight) → spinner
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#888", fontSize: 14 }}>
        Loading…
      </div>
    );
  }

  const sidebarContent = (
    <>
      {/* Brand */}
      <div style={{ padding: "28px 24px 24px" }}>
        <NavLink to="/" onClick={() => setMobileMenuOpen(false)} style={{ fontFamily: '"Bricolage Grotesque", Inter, system-ui', fontWeight: 800, fontSize: 22, color: "#fff", letterSpacing: "-0.02em", textDecoration: "none" }}>
          FROMO
        </NavLink>
        <div style={{ color: "#777", fontSize: 12, marginTop: 3 }}>Partner</div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "0 12px" }}>
        <SideNavLink to="/partner" end icon={<ListIcon />} label="My Listings" onClick={() => setMobileMenuOpen(false)} />
        <SideNavLink to="/partner/analytics" icon={<BarIcon />} label="Analytics" onClick={() => setMobileMenuOpen(false)} />
        <SideNavLink to="/partner/settings" icon={<GearIcon />} label="Settings" onClick={() => setMobileMenuOpen(false)} />

        <div style={{ marginTop: 16, borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 12 }}>
          <NavLink
            to="/"
            style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", borderRadius: 7, color: "#555", textDecoration: "none", fontSize: 13, fontWeight: 500 }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "#aaa"; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "#555"; }}
          >
            <HomeIcon />
            Back to Discover
          </NavLink>
        </div>
      </nav>

      {/* User info */}
      <div style={{ padding: "16px 24px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
        <div style={{ fontSize: 13, color: "#fff", fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {displayName}
        </div>
        <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
          {profile?.user_type
            ? profile.user_type.charAt(0).toUpperCase() + profile.user_type.slice(1) + " Account"
            : "Account"}
        </div>
        <button onClick={handleSignOut} style={{ background: "none", border: "none", cursor: "pointer", color: "#555", fontSize: 11, marginTop: 8, padding: 0 }}>
          Log out
        </button>
      </div>
    </>
  );

  return (
    <div className="flex h-screen overflow-hidden" style={{ fontFamily: "Inter, system-ui, sans-serif" }}>

      {/* Desktop sidebar — hidden on mobile */}
      <aside className="hidden lg:flex flex-col flex-shrink-0" style={{ width: 240, background: "#111", color: "#fff" }}>
        {sidebarContent}
      </aside>

      {/* Mobile drawer overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          style={{ background: "rgba(0,0,0,0.5)" }}
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={`fixed top-0 left-0 h-full z-50 flex flex-col lg:hidden transition-transform duration-200 ${mobileMenuOpen ? "translate-x-0" : "-translate-x-full"}`}
        style={{ width: 240, background: "#111", color: "#fff" }}
      >
        {/* Close button */}
        <button
          onClick={() => setMobileMenuOpen(false)}
          style={{ position: "absolute", top: 16, right: 16, background: "none", border: "none", color: "#777", cursor: "pointer", fontSize: 20, lineHeight: 1 }}
        >
          ✕
        </button>
        {sidebarContent}
      </aside>

      {/* Right side: mobile topbar + main content */}
      <div className="flex flex-col flex-1 overflow-hidden">

        {/* Mobile top bar — hidden on desktop */}
        <header className="flex lg:hidden items-center justify-between px-4 py-3 flex-shrink-0" style={{ background: "#111", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
          <NavLink to="/" style={{ fontFamily: '"Bricolage Grotesque", Inter, system-ui', fontWeight: 800, fontSize: 20, color: "#fff", letterSpacing: "-0.02em", textDecoration: "none" }}>
            FROMO
          </NavLink>
          <button
            onClick={() => setMobileMenuOpen(true)}
            style={{ background: "none", border: "none", color: "#fff", cursor: "pointer", padding: 4 }}
            aria-label="Open menu"
          >
            <HamburgerIcon />
          </button>
        </header>

      {/* Main */}
      <main style={{ flex: 1, overflowY: "auto", background: "var(--color-paper)" }}>
        {loadState === "loading" && !isSettings && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#888", fontSize: 14 }}>
            Loading…
          </div>
        )}
        {loadState === "no-org" && !isSettings && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 16, textAlign: "center", padding: 48 }}>
            <div style={{ fontSize: 36, marginBottom: 4 }}>🏢</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: "var(--color-ink)", fontFamily: '"Bricolage Grotesque", Inter, system-ui', letterSpacing: "-0.02em" }}>
              Set up your organisation
            </div>
            <div style={{ fontSize: 14, color: "#888", maxWidth: 360, lineHeight: 1.6 }}>
              Create your organisation to start listing events and tracking bookings.
            </div>

            <form
              onSubmit={handleCreateOrg}
              style={{ display: "flex", flexDirection: "column", gap: 12, width: "100%", maxWidth: 360, marginTop: 8 }}
            >
              <input
                required
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                placeholder="Organisation name (e.g. Blue Note Jazz Club)"
                style={{
                  border: "1px solid #e0dbd2", borderRadius: 10, padding: "12px 16px",
                  fontSize: 14, outline: "none", width: "100%", boxSizing: "border-box",
                  fontFamily: "Inter, system-ui, sans-serif", background: "var(--color-surface)",
                  color: "var(--color-ink)",
                }}
              />
              {createError && (
                <div style={{ fontSize: 13, color: "#E53935" }}>{createError}</div>
              )}
              <button
                type="submit"
                disabled={creating}
                style={{
                  background: creating ? "#888" : "#111", color: "#fff", border: "none",
                  borderRadius: 10, padding: "13px", fontSize: 14, fontWeight: 700,
                  cursor: creating ? "wait" : "pointer", fontFamily: "Inter, system-ui, sans-serif",
                }}
              >
                {creating ? "Creating…" : "Create Organisation"}
              </button>
            </form>
          </div>
        )}
        {loadState === "error" && !isSettings && (
          <div style={{ padding: 48, color: "#888", fontSize: 14 }}>
            Couldn't load dashboard — is the backend running?
          </div>
        )}
        {(loadState === "ready" || isSettings) && <Outlet context={{ orgData }} />}
      </main>
      </div>
    </div>
  );
}

function HamburgerIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

function SideNavLink({ to, end, icon, label, onClick }) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onClick}
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

function HomeIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
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

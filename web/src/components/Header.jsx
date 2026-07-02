import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { USER_TYPE } from "../lib/config.js";

export default function Header() {
  const { user, profile, signOut } = useAuth();
  const navigate = useNavigate();

  async function handleSignOut() {
    await signOut();
    navigate("/");
  }

  return (
    <header
      className="sticky top-0 z-[2000] flex items-center justify-between backdrop-blur-md"
      style={{ padding: "clamp(10px, 1.5vh, 14px) clamp(16px, 3vw, 32px)", background: "var(--color-paper)", borderBottom: "1px solid var(--color-line)" }}
    >
      <Link
        to="/"
        className="flex items-center gap-2 font-display font-extrabold tracking-tight"
        style={{ fontSize: "clamp(18px, 2.2vw, 26px)", lineHeight: 1, color: "var(--color-ink)" }}
      >
        FROMO<span className="live-dot" aria-hidden="true" />
      </Link>

      <nav className="flex items-center" style={{ gap: "clamp(16px, 2.5vw, 24px)" }} aria-label="Primary">
        <Link to="/" className="font-medium" style={{ fontSize: "clamp(13px, 1.4vw, 16px)", color: "var(--color-ink)" }}>
          Discover
        </Link>
        {(!user || profile?.user_type === USER_TYPE.ORGANISER) && (
          <Link to="/partner" className="font-medium" style={{ fontSize: "clamp(13px, 1.4vw, 16px)", color: "var(--color-muted)", textDecoration: "none" }}>For organisers</Link>
        )}
      </nav>

      <div className="flex items-center" style={{ gap: "clamp(8px, 1vw, 12px)" }}>
        {user ? (
          <>
            <span className="hidden sm:inline" style={{ fontSize: "clamp(12px, 1.3vw, 15px)", color: "var(--color-muted)" }}>
              {profile?.full_name || user?.user_metadata?.full_name || user.email}
            </span>
            {profile?.user_type === USER_TYPE.ORGANISER ? (
              <Link
                to="/partner"
                className="bg-amber font-semibold text-[#231a09] hover:bg-amber-press"
                style={{ fontSize: "clamp(12px, 1.3vw, 15px)", padding: "6px clamp(12px, 1.5vw, 16px)", borderRadius: "10px" }}
              >
                Dashboard
              </Link>
            ) : (
              <Link
                to="/settings"
                title="Settings"
                style={{
                  width: 30, height: 30, borderRadius: "50%",
                  background: "#F5A623", display: "flex", alignItems: "center",
                  justifyContent: "center", flexShrink: 0, textDecoration: "none",
                }}
              >
                <span style={{ fontSize: 12, fontWeight: 700, color: "#231a09", lineHeight: 1 }}>
                  {(profile?.full_name || user?.user_metadata?.full_name || user.email || "?")
                    .split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase()}
                </span>
              </Link>
            )}
            <button
              onClick={handleSignOut}
              className="font-semibold"
              style={{ fontSize: "clamp(12px, 1.3vw, 15px)", padding: "6px clamp(12px, 1.5vw, 16px)", borderRadius: "10px", border: "1px solid var(--color-line)", color: "var(--color-ink)", background: "none", cursor: "pointer" }}
            >
              Sign out
            </button>
          </>
        ) : (
          <>
            <Link
              to="/login"
              className="font-semibold"
              style={{ fontSize: "clamp(12px, 1.3vw, 15px)", padding: "6px clamp(12px, 1.5vw, 16px)", borderRadius: "10px", border: "1px solid var(--color-line)", color: "var(--color-ink)", textDecoration: "none" }}
            >
              Log in
            </Link>
            <Link
              to="/signup"
              className="bg-amber font-semibold text-[#231a09] hover:bg-amber-press"
              style={{ fontSize: "clamp(12px, 1.3vw, 15px)", padding: "6px clamp(12px, 1.5vw, 16px)", borderRadius: "10px" }}
            >
              Sign up
            </Link>
          </>
        )}
      </div>
    </header>
  );
}

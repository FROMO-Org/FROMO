import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Header() {
  const { user, profile, signOut } = useAuth();
  const navigate = useNavigate();

  async function handleSignOut() {
    await signOut();
    navigate("/");
  }

  return (
    <header
      className="sticky top-0 z-[1000] flex items-center justify-between border-b border-line bg-paper/85 backdrop-blur"
      style={{ padding: "clamp(1rem, 1.5vh, 1.4rem) clamp(1.6rem, 3vw, 3.2rem)" }}
    >
      <Link
        to="/"
        className="flex items-center gap-2 font-display font-extrabold tracking-tight"
        style={{ fontSize: "clamp(1.8rem, 2.2vw, 2.6rem)", lineHeight: 1 }}
      >
        FROMO<span className="live-dot" aria-hidden="true" />
      </Link>

      <nav className="hidden items-center md:flex" style={{ gap: "clamp(1.6rem, 2.5vw, 2.4rem)" }} aria-label="Primary">
        <Link to="/" className="font-medium text-ink" style={{ fontSize: "clamp(1.3rem, 1.4vw, 1.6rem)" }}>
          Discover
        </Link>
        <Link to="/partner" className="font-medium text-muted hover:text-ink" style={{ fontSize: "clamp(1.3rem, 1.4vw, 1.6rem)" }}>For organisers</Link>
      </nav>

      <div className="flex items-center" style={{ gap: "clamp(0.8rem, 1vw, 1.2rem)" }}>
        {user ? (
          <>
            <span className="hidden text-muted sm:inline" style={{ fontSize: "clamp(1.2rem, 1.3vw, 1.5rem)" }}>
              {profile?.full_name || user?.user_metadata?.full_name || user.email}
            </span>
            <button
              onClick={handleSignOut}
              className="border border-line font-semibold hover:border-ink"
              style={{ fontSize: "clamp(1.2rem, 1.3vw, 1.5rem)", padding: "0.6rem clamp(1.2rem, 1.5vw, 1.6rem)", borderRadius: "10px" }}
            >
              Sign out
            </button>
          </>
        ) : (
          <>
            <Link
              to="/login"
              className="border border-line font-semibold hover:border-ink"
              style={{ fontSize: "clamp(1.2rem, 1.3vw, 1.5rem)", padding: "0.6rem clamp(1.2rem, 1.5vw, 1.6rem)", borderRadius: "10px" }}
            >
              Log in
            </Link>
            <Link
              to="/signup"
              className="bg-amber font-semibold text-[#231a09] hover:bg-amber-press"
              style={{ fontSize: "clamp(1.2rem, 1.3vw, 1.5rem)", padding: "0.6rem clamp(1.2rem, 1.5vw, 1.6rem)", borderRadius: "10px" }}
            >
              Sign up
            </Link>
          </>
        )}
      </div>
    </header>
  );
}

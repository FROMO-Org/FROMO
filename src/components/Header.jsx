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
      style={{ padding: "2.5rem 5rem" }}
    >
      <Link
        to="/"
        className="flex items-center gap-3 font-display font-extrabold tracking-tight"
        style={{ fontSize: "5.5rem", lineHeight: 1 }}
      >
        FROMO<span className="live-dot" aria-hidden="true" />
      </Link>

      <nav className="hidden items-center md:flex" style={{ gap: "4rem" }} aria-label="Primary">
        <Link to="/" className="font-medium text-ink" style={{ fontSize: "2.8rem" }}>
          Discover
        </Link>
        <span className="font-medium text-muted" style={{ fontSize: "2.8rem" }}>For organisers</span>
      </nav>

      <div className="flex items-center" style={{ gap: "1.5rem" }}>
        {user ? (
          <>
            <span className="hidden text-muted sm:inline" style={{ fontSize: "2rem" }}>
              {profile?.full_name || user.email}
            </span>
            <button
              onClick={handleSignOut}
              className="border border-line font-semibold hover:border-ink"
              style={{ fontSize: "2rem", padding: "1rem 2.5rem", borderRadius: "14px" }}
            >
              Sign out
            </button>
          </>
        ) : (
          <>
            <Link
              to="/login"
              className="border border-line font-semibold hover:border-ink"
              style={{ fontSize: "2rem", padding: "1rem 2.5rem", borderRadius: "14px" }}
            >
              Log in
            </Link>
            <Link
              to="/signup"
              className="bg-amber font-semibold text-[#231a09] hover:bg-amber-press"
              style={{ fontSize: "2rem", padding: "1rem 2.5rem", borderRadius: "14px" }}
            >
              Sign up
            </Link>
          </>
        )}
      </div>
    </header>
  );
}

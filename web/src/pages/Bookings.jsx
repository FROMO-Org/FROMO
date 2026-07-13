import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getMyBookings, cancelBooking } from "../lib/api.js";
import { useAuth } from "../context/AuthContext.jsx";
import { formatPrice } from "../lib/format.js";

function formatEventDate(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString(undefined, {
    weekday: "short", month: "short", day: "numeric", year: "numeric",
  });
}

function formatEventTime(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

function isPast(event) {
  const end = event.ends_at ? new Date(event.ends_at) : new Date(event.starts_at);
  return end <= new Date();
}

export default function Bookings() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState("loading");
  const [cancellingId, setCancellingId] = useState(null);

  useEffect(() => {
    if (!user) { navigate("/login"); return; }
    getMyBookings()
      .then((data) => { setRows(data ?? []); setStatus("ready"); })
      .catch(() => setStatus("error"));
  }, [user]);

  async function handleCancel(bookingId) {
    setCancellingId(bookingId);
    try {
      await cancelBooking(bookingId);
      setRows((prev) =>
        prev.map((r) =>
          r.booking.id === bookingId
            ? { ...r, booking: { ...r.booking, status: "cancelled" } }
            : r
        )
      );
    } finally {
      setCancellingId(null);
    }
  }

  const upcoming  = rows.filter((r) => r.booking.status === "confirmed" && !isPast(r.event));
  const past      = rows.filter((r) => r.booking.status === "confirmed" && isPast(r.event));
  const cancelled = rows.filter((r) => r.booking.status === "cancelled");

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "40px 24px" }}>
      <h1 style={{ fontSize: 26, fontWeight: 800, fontFamily: '"Bricolage Grotesque", Inter, system-ui', letterSpacing: "-0.02em", margin: "0 0 28px", color: "var(--color-ink)" }}>
        My Bookings
      </h1>

      {status === "loading" && <p style={{ fontSize: 14, color: "var(--color-muted)" }}>Loading your bookings…</p>}
      {status === "error"   && <p style={{ fontSize: 14, color: "var(--color-muted)" }}>Couldn't load bookings. Try refreshing.</p>}

      {status === "ready" && rows.length === 0 && (
        <div style={{ borderRadius: 14, border: "1px solid var(--color-line)", background: "var(--color-surface)", padding: "40px 24px", textAlign: "center" }}>
          <p style={{ fontSize: 14, color: "var(--color-muted)", marginBottom: 16 }}>You haven't reserved any events yet.</p>
          <button
            onClick={() => navigate("/")}
            style={{ background: "#F5A623", color: "#231a09", border: "none", borderRadius: 9999, padding: "8px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer" }}
          >
            Browse events
          </button>
        </div>
      )}

      {status === "ready" && rows.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
          {upcoming.length  > 0 && <BookingSection title="Upcoming"  rows={upcoming}  onCancel={handleCancel} cancellingId={cancellingId} navigate={navigate} />}
          {past.length      > 0 && <BookingSection title="Past"      rows={past}      onCancel={handleCancel} cancellingId={cancellingId} navigate={navigate} dimmed />}
          {cancelled.length > 0 && <BookingSection title="Cancelled" rows={cancelled} onCancel={handleCancel} cancellingId={cancellingId} navigate={navigate} dimmed />}
        </div>
      )}
    </div>
  );
}

function BookingSection({ title, rows, onCancel, cancellingId, navigate, dimmed }) {
  return (
    <div>
      <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--color-muted)", marginBottom: 10 }}>
        {title}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {rows.map((r) => (
          <BookingCard key={r.booking.id} row={r} onCancel={onCancel} cancellingId={cancellingId} navigate={navigate} dimmed={dimmed} />
        ))}
      </div>
    </div>
  );
}

function BookingCard({ row, onCancel, cancellingId, navigate, dimmed }) {
  const { booking, event, venue } = row;
  const dateStr  = formatEventDate(event.starts_at);
  const timeStr  = [formatEventTime(event.starts_at), formatEventTime(event.ends_at)].filter(Boolean).join(" – ");
  const canCancel = booking.status === "confirmed" && !isPast(event);

  return (
    <div style={{
      display: "flex", gap: 14, alignItems: "flex-start", padding: 16, borderRadius: 14,
      border: "1px solid var(--color-line)",
      background: dimmed ? "transparent" : "rgba(245,166,35,0.04)",
      opacity: dimmed ? 0.65 : 1,
    }}>
      <div
        onClick={() => navigate(`/events/${event.id}`, { state: { event } })}
        style={{ width: 76, height: 76, borderRadius: 10, overflow: "hidden", flexShrink: 0, cursor: "pointer", background: "rgba(245,166,35,0.1)" }}
      >
        {event.image_url
          ? <img src={event.image_url} alt={event.title} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top" }} />
          : <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}><span style={{ fontSize: 26, opacity: 0.4 }}>📅</span></div>
        }
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
          <h3
            onClick={() => navigate(`/events/${event.id}`, { state: { event } })}
            style={{ fontWeight: 700, fontSize: 15, color: "var(--color-ink)", cursor: "pointer", margin: 0, lineHeight: 1.3 }}
          >
            {event.title}
          </h3>
          <StatusBadge status={booking.status} past={isPast(event)} />
        </div>
        <p style={{ fontSize: 12, color: "var(--color-muted)", margin: "4px 0 2px" }}>{venue.name}</p>
        {dateStr && <p style={{ fontSize: 12, color: "var(--color-muted)", margin: 0 }}>{dateStr}{timeStr ? ` · ${timeStr}` : ""}</p>}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 10 }}>
          <span style={{ fontSize: 12, color: "var(--color-muted)" }}>
            {booking.quantity} ticket{booking.quantity !== 1 ? "s" : ""} · <strong style={{ color: "var(--color-ink)" }}>{formatPrice(booking.total_price_cents)}</strong>
          </span>
          {canCancel && (
            <button
              onClick={() => onCancel(booking.id)}
              disabled={cancellingId === booking.id}
              style={{ fontSize: 12, fontWeight: 600, color: "#E53935", background: "none", border: "1px solid #E53935", borderRadius: 8, padding: "4px 12px", cursor: cancellingId === booking.id ? "not-allowed" : "pointer", opacity: cancellingId === booking.id ? 0.5 : 1 }}
            >
              {cancellingId === booking.id ? "Cancelling…" : "Cancel"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status, past }) {
  if (status === "cancelled") return <span style={{ fontSize: 11, fontWeight: 700, background: "rgba(229,57,53,0.1)", color: "#E53935", borderRadius: 6, padding: "2px 8px", whiteSpace: "nowrap", flexShrink: 0 }}>Cancelled</span>;
  if (past) return <span style={{ fontSize: 11, fontWeight: 700, background: "rgba(100,100,100,0.1)", color: "var(--color-muted)", borderRadius: 6, padding: "2px 8px", whiteSpace: "nowrap", flexShrink: 0 }}>Attended</span>;
  return <span style={{ fontSize: 11, fontWeight: 700, background: "rgba(245,166,35,0.15)", color: "#F5A623", borderRadius: 6, padding: "2px 8px", whiteSpace: "nowrap", flexShrink: 0 }}>Confirmed</span>;
}

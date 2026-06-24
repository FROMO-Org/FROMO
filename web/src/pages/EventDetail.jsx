import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getEvent } from "../lib/api";
import { formatTime, formatPrice } from "../lib/format";
import { googleMapsUrl } from "../lib/directions";

const HERO_GRADIENTS = {
  music: "linear-gradient(160deg, #1a110a 0%, #2d1a08 55%, #0f0905 100%)",
  arts: "linear-gradient(160deg, #0f0a1a 0%, #1a0f2d 55%, #050a1a 100%)",
  food: "linear-gradient(160deg, #1a0e00 0%, #2d1800 55%, #110900 100%)",
  sports: "linear-gradient(160deg, #061a10 0%, #0a2d1a 55%, #031109 100%)",
  default: "linear-gradient(160deg, #111014 0%, #1e1a12 55%, #0a0806 100%)",
};

function heroGradient(category) {
  const key = (category ?? "").toLowerCase();
  return HERO_GRADIENTS[key] ?? HERO_GRADIENTS.default;
}

function countdown(iso) {
  if (!iso) return null;
  const diff = new Date(iso) - Date.now();
  if (diff <= 0) return "Ended";
  const h = Math.floor(diff / 3_600_000);
  const m = Math.floor((diff % 3_600_000) / 60_000);
  if (h >= 48) return `${Math.floor(h / 24)}d`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export default function EventDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [status, setStatus] = useState("loading");
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    let alive = true;
    getEvent(id)
      .then((data) => {
        if (!alive) return;
        setEvent(data);
        setStatus("ready");
      })
      .catch(() => alive && setStatus("error"));
    return () => { alive = false; };
  }, [id]);

  if (status === "loading") {
    return (
      <main className="flex-1 flex items-center justify-center" style={{ minHeight: "60vh", color: "#888", fontSize: 15 }}>
        Loading event…
      </main>
    );
  }

  if (status === "error" || !event) {
    return (
      <main className="flex-1" style={{ padding: "48px 48px", color: "#888", fontSize: 15 }}>
        Event not found.{" "}
        <button onClick={() => navigate(-1)} style={{ color: "#F5A623", background: "none", border: "none", cursor: "pointer", fontSize: 15, padding: 0 }}>
          Go back
        </button>
      </main>
    );
  }

  const venue = event.venue ?? {};
  const category = event.category ?? venue.category;
  const ends = countdown(event.ends_at);
  const price = formatPrice(event.price_cents);
  const accessible = venue.is_accessible;

  function handleDirections() {
    if (venue.lat && venue.lng) {
      window.open(googleMapsUrl({ lat: venue.lat, lng: venue.lng }), "_blank", "noopener");
    }
  }

  return (
    <main className="flex-1">
      {/* Hero */}
      <div
        style={{
          height: 300,
          background: heroGradient(category),
          position: "relative",
          overflow: "hidden",
        }}
      >
        {category && (
          <div
            style={{
              position: "absolute",
              bottom: 32,
              left: 48,
              fontFamily: '"Space Mono", monospace',
              fontSize: 12,
              letterSpacing: "0.15em",
              textTransform: "uppercase",
              color: "rgba(255,255,255,0.5)",
            }}
          >
            {category}
          </div>
        )}
      </div>

      {/* Content */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 340px",
          gap: 64,
          padding: "40px 48px 80px",
          maxWidth: 1100,
          margin: "0 auto",
        }}
      >
        {/* Left: details */}
        <div>
          {category && (
            <div style={{ fontFamily: '"Space Mono", monospace', fontSize: 12, letterSpacing: "0.12em", textTransform: "uppercase", color: "#888", marginBottom: 12 }}>
              {category}
            </div>
          )}
          <h1
            style={{
              fontFamily: '"Bricolage Grotesque", Inter, system-ui',
              fontSize: 38,
              fontWeight: 800,
              letterSpacing: "-0.02em",
              lineHeight: 1.08,
              margin: "0 0 20px",
              color: "#111",
            }}
          >
            {event.title}
          </h1>

          {event.description ? (
            <p style={{ fontSize: 15, color: "#666", lineHeight: 1.7, maxWidth: "60ch", margin: "0 0 28px" }}>
              {event.description}
            </p>
          ) : (
            venue.name && (
              <p style={{ fontSize: 15, color: "#666", lineHeight: 1.7, maxWidth: "60ch", margin: "0 0 28px" }}>
                Join us for an exciting event at {venue.name}
                {venue.address ? `, ${venue.address}` : ""}.
                {formatTime(event.starts_at) ? ` Starts ${formatTime(event.starts_at)}.` : ""}
              </p>
            )
          )}

          <div style={{ borderTop: "1px solid #eae4d9", paddingTop: 20, display: "flex", flexWrap: "wrap", gap: "6px 16px" }}>
            {accessible && (
              <span style={{ fontSize: 13, color: "#2E9E6B", fontWeight: 500 }}>
                Wheelchair accessible
              </span>
            )}
            <span style={{ fontSize: 13, color: "#2E9E6B", fontWeight: 500 }}>
              All ages welcome
            </span>
          </div>
        </div>

        {/* Right: pricing + CTAs */}
        <div style={{ paddingTop: 4 }}>
          {/* Price */}
          <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 14 }}>
            <span style={{ fontSize: 38, fontWeight: 800, fontFamily: '"Bricolage Grotesque", Inter, system-ui', letterSpacing: "-0.02em", color: "#111" }}>
              {price ?? "Free"}
            </span>
          </div>

          {/* Countdown */}
          {ends && ends !== "Ended" && (
            <div style={{ fontSize: 13, color: "#888", marginBottom: 24 }}>
              Ends in {ends}
            </div>
          )}
          {ends === "Ended" && (
            <div style={{ fontSize: 13, color: "#E53935", marginBottom: 24 }}>Event has ended</div>
          )}

          {/* CTA buttons */}
          <button
            onClick={handleDirections}
            style={{
              display: "block",
              width: "100%",
              background: "#111",
              color: "#fff",
              border: "none",
              padding: "15px",
              borderRadius: 10,
              fontSize: 15,
              fontWeight: 700,
              cursor: "pointer",
              marginBottom: 12,
              letterSpacing: "0.01em",
            }}
          >
            Get Directions
          </button>

          <button
            onClick={() => setShowModal(true)}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              width: "100%",
              background: "#fff",
              color: "#111",
              border: "1.5px solid #111",
              padding: "14px",
              borderRadius: 10,
              fontSize: 15,
              fontWeight: 600,
              cursor: "pointer",
              boxSizing: "border-box",
            }}
          >
            <HeartIcon /> Save Activity
          </button>
        </div>
      </div>

      {/* App download modal */}
      {showModal && <AppModal onClose={() => setShowModal(false)} />}
    </main>
  );
}

function AppModal({ onClose }) {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.45)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
      }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "#fff",
          borderRadius: 16,
          padding: "40px 44px",
          width: 420,
          maxWidth: "90vw",
          textAlign: "center",
          position: "relative",
          boxShadow: "0 24px 64px rgba(0,0,0,0.18)",
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: 16,
            right: 18,
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: 20,
            color: "#888",
            lineHeight: 1,
          }}
        >
          ×
        </button>

        <div style={{ fontSize: 15, fontWeight: 800, color: "#F5A623", letterSpacing: "0.04em", marginBottom: 16 }}>
          FROMO
        </div>

        <h2
          style={{
            fontFamily: '"Bricolage Grotesque", Inter, system-ui',
            fontSize: 26,
            fontWeight: 800,
            letterSpacing: "-0.02em",
            color: "#111",
            margin: "0 0 10px",
          }}
        >
          Open in the FROMO App
        </h2>

        <p style={{ fontSize: 14, color: "#888", lineHeight: 1.5, margin: "0 0 28px" }}>
          Get directions, save activities, and unlock exclusive student deals
        </p>

        <div
          style={{
            display: "inline-block",
            padding: 12,
            border: "1px solid #e8e2da",
            borderRadius: 10,
            marginBottom: 12,
          }}
        >
          <QrCode />
        </div>

        <p style={{ fontSize: 12.5, color: "#aaa", margin: 0 }}>Scan with your camera</p>
      </div>
    </div>
  );
}

function QrCode() {
  const rows = [
    "1111111011000011111110",
    "1000001001101010000010",
    "1011101011010110111010",
    "1011101000100010111010",
    "1011101001001010111010",
    "1000001010011010000010",
    "1111111010101011111111",
    "0000000101010100000000",
    "0111011011101101101011",
    "1100100100010010110010",
    "1011011010101100101101",
    "0011000101101000011001",
    "0101111011010110101110",
    "0000000101011011000101",
    "1111111000101100101011",
    "1000001011011010001100",
    "1011101010100100111011",
    "1011101001101100110011",
    "1011101011010011010101",
    "1000001010101000111001",
    "1111111001010110010111",
  ];
  const cell = 4;
  const W = rows[0].length * cell;
  const H = rows.length * cell;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ display: "block" }}>
      <rect width={W} height={H} fill="white" />
      {rows.map((row, r) =>
        row.split("").map((c, col) =>
          c === "1" ? (
            <rect key={`${r}-${col}`} x={col * cell} y={r * cell} width={cell} height={cell} fill="#111" />
          ) : null
        )
      )}
    </svg>
  );
}

function HeartIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  );
}

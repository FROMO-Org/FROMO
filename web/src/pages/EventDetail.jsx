import { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { MapContainer, TileLayer, Marker, GeoJSON } from "react-leaflet";
import L from "leaflet";
import { getEvent, getVenue } from "../lib/api.js";
import { fetchEventImage } from "../lib/ticketmaster.js";
import { fetchRoute, getUserLocation } from "../lib/directions.js";
import { formatPrice } from "../lib/format.js";
import { useTheme } from "../context/ThemeContext.jsx";

const MODES = [
  { key: "walk", label: "Walk", profile: "foot-walking" },
  { key: "drive", label: "Drive", profile: "driving-car" },
  { key: "wheelchair", label: "Wheelchair", profile: "wheelchair" },
];

function userLocationIcon() {
  const svg = `<div style="filter:drop-shadow(0 2px 5px rgba(0,0,0,0.45));">
    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22">
      <circle cx="11" cy="11" r="9" fill="#1D4ED8" fill-opacity="0.25"/>
      <circle cx="11" cy="11" r="6" fill="#1D4ED8" stroke="white" stroke-width="2.5"/>
    </svg>
  </div>`;
  return L.divIcon({ className: "", iconSize: [22, 22], iconAnchor: [11, 11], html: svg });
}

function venueLocationIcon() {
  const svg = `<div style="filter:drop-shadow(0 3px 4px rgba(0,0,0,0.4));">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 56" width="30" height="42">
      <path d="M20 0C9 0 0 9 0 20c0 13 20 36 20 36S40 33 40 20C40 9 31 0 20 0z" fill="#F5A623" stroke="white" stroke-width="2.5"/>
      <circle cx="20" cy="19" r="8" fill="white"/>
    </svg>
  </div>`;
  return L.divIcon({ className: "", iconSize: [30, 42], iconAnchor: [15, 42], html: svg });
}

function formatDuration(seconds) {
  if (seconds == null) return null;
  const mins = Math.round(seconds / 60);
  if (mins < 60) return `${mins} min`;
  return `${Math.floor(mins / 60)} hr ${mins % 60} min`;
}

function formatDistanceMetres(metres) {
  if (metres == null) return null;
  const mi = metres / 1609.34;
  return `${mi < 0.1 ? "0.1" : mi.toFixed(1)} mi`;
}

const MOBILE_APP_URL = "https://fromomobile.netlify.app/?v=api-fix#/map";
const QR_CODE_SRC = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(MOBILE_APP_URL)}`;

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

function BackIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 12H5M12 5l-7 7 7 7" />
    </svg>
  );
}

export default function EventDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { state: locationState } = useLocation();
  const { isDark } = useTheme();

  const preloaded = locationState?.event;

  const [event, setEvent] = useState(preloaded ?? null);
  const [venue, setVenue] = useState(preloaded?.venue ?? null);
  const [imageUrl, setImageUrl] = useState(preloaded?.image_url ?? null);
  const [loading, setLoading] = useState(true);

  const [userLoc, setUserLoc] = useState(null);
  const [mode, setMode] = useState("walk");
  const [route, setRoute] = useState(null);
  const [routeSummary, setRouteSummary] = useState(null);
  const [routeError, setRouteError] = useState(null);
  const [routeLoading, setRouteLoading] = useState(false);

  useEffect(() => {
    let alive = true;

    async function load() {
      try {
        const fresh = await getEvent(id);
        if (!alive) return;
        setEvent(fresh);

        const img =
          fresh.image_url ??
          preloaded?.image_url ??
          (await fetchEventImage(fresh.title, fresh.category));
        if (alive) setImageUrl(img);

        if (preloaded?.venue) {
          setVenue(preloaded.venue);
        } else if (fresh.venue_id) {
          try {
            const v = await getVenue(fresh.venue_id);
            if (alive) setVenue(v);
          } catch {}
        }
      } catch {
        if (alive && !preloaded) navigate("/", { replace: true });
      } finally {
        if (alive) setLoading(false);
      }
    }

    load();
    return () => { alive = false; };
  }, [id]);

  useEffect(() => {
    getUserLocation().then(setUserLoc);
  }, []);

  useEffect(() => {
    if (venue?.is_accessible) setMode("wheelchair");
  }, [venue?.id]);

  useEffect(() => {
    if (!venue || userLoc == null) return;
    let alive = true;
    const modeInfo = MODES.find((m) => m.key === mode);
    setRouteLoading(true);
    setRouteError(null);
    fetchRoute({ from: userLoc, to: { lat: venue.lat, lng: venue.lng }, profile: modeInfo.profile })
      .then(({ geojson, summary }) => {
        if (!alive) return;
        setRoute(geojson);
        setRouteSummary(summary);
      })
      .catch(() => {
        if (!alive) return;
        setRoute(null);
        setRouteSummary(null);
        setRouteError("Couldn't load a route for this mode.");
      })
      .finally(() => alive && setRouteLoading(false));
    return () => { alive = false; };
  }, [venue?.id, venue?.lat, venue?.lng, userLoc, mode]);

  if (loading && !preloaded) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "var(--color-muted)", fontSize: 14 }}>
        Loading…
      </div>
    );
  }

  const ev = event ?? preloaded;
  if (!ev) return null;

  const dateStr = formatEventDate(ev.starts_at);
  const startTime = formatEventTime(ev.starts_at);
  const endTime = formatEventTime(ev.ends_at);
  const timeStr = [startTime, endTime].filter(Boolean).join(" – ");
  const hasDiscount = ev.original_price_cents != null && ev.original_price_cents > ev.price_cents;
  const tileUrl = isDark
    ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
    : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";

  return (
    <main style={{ minHeight: "100vh", background: "var(--color-paper)", paddingBottom: 60 }}>
      <div style={{
        position: "sticky", top: 0, zIndex: 100,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "12px 16px",
        background: "var(--color-paper)",
        borderBottom: "1px solid var(--color-line)",
      }}>
        <button
          onClick={() => navigate(-1)}
          style={{ display: "flex", alignItems: "center", gap: 6, background: "none", border: "none", cursor: "pointer", color: "var(--color-ink)", fontWeight: 600, fontSize: 14, padding: "4px 0" }}
        >
          <BackIcon /> Back
        </button>
        <span style={{ fontWeight: 700, fontSize: 14, color: "var(--color-ink)", maxWidth: "55%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {ev.title}
        </span>
        <div style={{ width: 52 }} />
      </div>

      <div style={{ maxWidth: 680, margin: "0 auto", padding: "20px 16px 0" }}>
        <div style={{ width: "100%", height: "clamp(200px, 50vw, 280px)", borderRadius: 16, overflow: "hidden", background: "rgba(245,166,35,0.08)" }}>
          {imageUrl ? (
            <img src={imageUrl} alt={ev.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ fontSize: 64, opacity: 0.25 }}>📅</span>
            </div>
          )}
        </div>
      </div>

      <div
        className="grid grid-cols-1 lg:grid-cols-[1fr_320px]"
        style={{ maxWidth: 680, margin: "0 auto", gap: 32, padding: "20px 16px 0" }}
      >
        {/* LEFT — event info & summary */}
        <div>
          {ev.category && (
            <div style={{ display: "inline-block", background: "rgba(245,166,35,0.15)", color: "#F5A623", borderRadius: 6, padding: "3px 10px", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 12 }}>
              {ev.category}
            </div>
          )}

          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16, marginBottom: 12 }}>
            <h1 style={{ fontFamily: '"Bricolage Grotesque", Inter, system-ui', fontWeight: 800, fontSize: "clamp(22px, 5vw, 38px)", lineHeight: 1.1, letterSpacing: "-0.02em", color: "var(--color-ink)", margin: 0 }}>
              {ev.title}
            </h1>
            <div style={{ flexShrink: 0, textAlign: "right" }}>
              {hasDiscount && (
                <div style={{ fontSize: 14, color: "var(--color-muted)", textDecoration: "line-through" }}>
                  {formatPrice(ev.original_price_cents)}
                </div>
              )}
              <div style={{ fontSize: 26, fontWeight: 800, color: "#F5A623", lineHeight: 1.2 }}>
                {formatPrice(ev.price_cents)}
              </div>
            </div>
          </div>

          {ev.description && (
            <p style={{ fontSize: 14, lineHeight: 1.7, color: "var(--color-muted)", margin: "0 0 20px" }}>
              {ev.description}
            </p>
          )}

          {(dateStr || timeStr) && (
            <div style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 16 }}>
              <span style={{ fontSize: 20, flexShrink: 0, marginTop: 1 }}>📅</span>
              <div>
                {dateStr && <div style={{ fontWeight: 600, fontSize: 15, color: "var(--color-ink)" }}>{dateStr}</div>}
                {timeStr && <div style={{ fontSize: 13, color: "var(--color-muted)", marginTop: 2 }}>{timeStr}</div>}
              </div>
            </div>
          )}

          {venue && (
            <div style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 16 }}>
              <span style={{ fontSize: 20, flexShrink: 0, marginTop: 1 }}>📍</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 15, color: "var(--color-ink)" }}>{venue.name}</div>
                {venue.address && <div style={{ fontSize: 13, color: "var(--color-muted)", marginTop: 2 }}>{venue.address}</div>}
              </div>
            </div>
          )}

          {ev.spots_remaining != null && (
            <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
              <span style={{ fontSize: 20, flexShrink: 0 }}>👥</span>
              <div>
                <span style={{ fontWeight: 600, fontSize: 15, color: ev.spots_remaining < 10 ? "#E53935" : "var(--color-ink)" }}>
                  {ev.spots_remaining} spots left
                </span>
                {ev.capacity != null && (
                  <span style={{ fontSize: 13, color: "var(--color-muted)" }}> of {ev.capacity} total</span>
                )}
              </div>
            </div>
          )}

          {ev.ai_summary && (
            <>
              <div style={{ borderTop: "1px solid var(--color-line)", margin: "22px 0" }} />
              <div style={{ marginBottom: 24 }}>
                <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--color-ink)", marginBottom: 12, letterSpacing: "-0.01em" }}>
                  AI Summary
                </h2>
                <div style={{
                  background: "rgba(245,166,35,0.08)",
                  border: "1px solid rgba(245,166,35,0.25)",
                  borderRadius: 14,
                  padding: "16px 18px",
                  fontSize: 14,
                  lineHeight: 1.7,
                  color: "var(--color-ink)",
                }}>
                  {ev.ai_summary}
                </div>
              </div>
            </>
          )}
        </div>

        {/* RIGHT — reserve via mobile app */}
        <aside style={{ marginBottom: 32 }}>
          <div style={{
            background: "rgba(245,166,35,0.1)",
            border: "1px solid rgba(245,166,35,0.3)",
            borderRadius: 16,
            padding: "18px 20px",
            marginBottom: 16,
          }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: "var(--color-ink)", marginBottom: 6 }}>
              How reserving works
            </div>
            <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--color-muted)" }}>
              Scan the QR code with your phone to reserve your spot or proceed to payment in the FROMO app.
            </div>
          </div>

          <div style={{
            background: "var(--color-surface)",
            border: "1px solid var(--color-line)",
            borderRadius: 16,
            padding: "28px 20px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 14,
          }}>
            <div style={{
              width: 180,
              height: 180,
              borderRadius: 12,
              border: "1px solid var(--color-line)",
              overflow: "hidden",
            }}>
              <img src={QR_CODE_SRC} alt="Scan to open FROMO on mobile" width={180} height={180} style={{ display: "block" }} />
            </div>

            <div style={{ textAlign: "center" }}>
              <div style={{ fontWeight: 700, fontSize: 15, color: "var(--color-ink)" }}>Reserve on Mobile</div>
              <div style={{ fontSize: 13, color: "var(--color-muted)", marginTop: 2 }}>
                Scan to reserve your spot
              </div>
            </div>
          </div>

          {venue && (
            <div style={{ marginTop: 16 }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                {MODES.filter((m) => m.key !== "wheelchair" || venue.is_accessible).map((m) => (
                  <button
                    key={m.key}
                    onClick={() => setMode(m.key)}
                    style={{
                      border: mode === m.key ? "1.5px solid #F5A623" : "1px solid var(--color-line)",
                      background: mode === m.key ? "rgba(245,166,35,0.12)" : "none",
                      color: "var(--color-ink)",
                      borderRadius: 8,
                      padding: "6px 14px",
                      fontSize: 13,
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    {m.label}
                  </button>
                ))}
              </div>

              <div style={{ position: "relative", height: 260, borderRadius: 14, overflow: "hidden", border: "1px solid var(--color-line)" }}>
                <MapContainer
                  center={[venue.lat, venue.lng]}
                  zoom={14}
                  scrollWheelZoom={false}
                  zoomControl={true}
                  style={{ height: "100%", width: "100%" }}
                >
                  <TileLayer
                    key={tileUrl}
                    url={tileUrl}
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    subdomains="abcd"
                    maxZoom={20}
                  />
                  <Marker position={[venue.lat, venue.lng]} icon={venueLocationIcon()} />
                  {userLoc && <Marker position={[userLoc.lat, userLoc.lng]} icon={userLocationIcon()} />}
                  {route && (
                    <GeoJSON
                      key={JSON.stringify(route).slice(0, 64)}
                      data={route}
                      style={{ color: isDark ? "#F5F0E8" : "#14110E", weight: 4, opacity: 0.8 }}
                    />
                  )}
                </MapContainer>

                {(routeLoading || routeSummary || routeError) && (
                  <div style={{
                    position: "absolute", bottom: 8, left: 8, zIndex: 1000,
                    background: "var(--color-paper)", border: "1px solid var(--color-line)",
                    borderRadius: 8, padding: "6px 12px",
                    fontSize: 12.5, fontWeight: 600, color: "var(--color-ink)",
                  }}>
                    {routeLoading
                      ? "Loading route…"
                      : routeError
                        ? routeError
                        : `${formatDuration(routeSummary.duration)} · ${formatDistanceMetres(routeSummary.distance)}`}
                  </div>
                )}
              </div>
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}

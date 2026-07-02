import { useEffect, useMemo, useState } from "react";
import EventCard from "../components/EventCard.jsx";
import EventMap from "../components/EventMap.jsx";
import { getDiscoverFeed, getBusynessNearby } from "../lib/api.js";
import { fetchRoute, googleMapsUrl } from "../lib/directions.js";
import { DEFAULT_CENTER } from "../lib/config.js";

export default function Home() {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("loading");
  const [selectedId, setSelectedId] = useState(null);
  const [route, setRoute] = useState(null);
  const [busynessAreas, setBusynessAreas] = useState([]);
  const [activeCategory, setActiveCategory] = useState("all");

  useEffect(() => {
    let alive = true;
    getDiscoverFeed()
      .then((data) => {
        if (!alive) return;
        setEvents(data);
        setStatus(data.length ? "ready" : "empty");
      })
      .catch(() => alive && setStatus("error"));
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    getBusynessNearby({
      lat: DEFAULT_CENTER.lat,
      lng: DEFAULT_CENTER.lng,
      radius_km: 20,
    })
      .then((data) => setBusynessAreas(data.areas ?? []))
      .catch(() => {});
  }, []);

  const categories = useMemo(() => {
    const seen = new Set();
    events.forEach((e) => {
      const cat = e.category || e.venue?.category;
      if (cat) seen.add(cat.toLowerCase());
    });
    return Array.from(seen).sort();
  }, [events]);

  const filteredEvents = useMemo(() => {
    if (activeCategory === "all") return events;
    return events.filter((e) => {
      const cat = (e.category || e.venue?.category || "").toLowerCase();
      return cat === activeCategory;
    });
  }, [events, activeCategory]);

  const focus = useMemo(() => {
    const e = events.find((x) => x.id === selectedId);
    return e?.venue ? { lat: e.venue.lat, lng: e.venue.lng } : null;
  }, [selectedId, events]);

  async function handleDirections(event) {
    const v = event.venue || {};
    const dest = { lat: v.lat, lng: v.lng };
    setSelectedId(event.id);
    try {
      const from = await getUserLocation();
      const profile = v.is_accessible ? "wheelchair" : "foot-walking";
      const { geojson } = await fetchRoute({ from, to: dest, profile });
      setRoute(geojson);
    } catch {
      window.open(googleMapsUrl(dest), "_blank", "noopener");
    }
  }

  return (
    <main className="flex-1">
      {/* Hero */}
      <section className="flex flex-wrap items-end justify-between gap-6 px-10 pb-6 pt-10 xl:px-16">
        <div>
          <h1 className="font-display text-[clamp(36px,4vw,64px)] font-extrabold leading-[1.02] tracking-tight">
            What's <span className="text-amber">alive</span> on your block,
            right now.
          </h1>
          <p className="mt-3 max-w-[52ch] text-[15px] leading-relaxed text-muted xl:text-base">
            Skip the scroll-and-miss. FROMO shows you what's actually happening
            near you — as it happens.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-line bg-surface px-4 py-2.5 font-mono text-[13px] text-muted">
          <span className="live-dot" aria-hidden="true" />
          MANHATTAN · LIVE
          {status === "ready" ? ` · ${events.length} NEARBY` : ""}
        </div>
      </section>

      {/* Map */}
      <div className="px-10 pb-8 xl:px-16">
        <div className="relative h-[50vh] min-h-[400px] overflow-hidden rounded-2xl border border-line">
          <EventMap
            events={events}
            busynessAreas={busynessAreas}
            focus={focus}
            route={route}
            onSelect={setSelectedId}
          />
          {(
            <div style={{
              position: "absolute", bottom: 8, left: 8, zIndex: 1000,
              background: "var(--color-paper)", border: "1px solid var(--color-line)",
              borderRadius: 8, padding: "6px 12px",
              display: "flex", alignItems: "center", gap: 14,
              fontSize: 11, fontWeight: 700, letterSpacing: "0.07em",
              textTransform: "uppercase", color: "var(--color-ink)",
            }}>
              BUSYNESS:
              <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#2E9E6B", display: "inline-block" }} /> Low
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#F5A623", display: "inline-block" }} /> Medium
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#E53935", display: "inline-block" }} /> High
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Events list */}
      <section aria-label="Events near you" className="px-10 pb-14 xl:px-16">
        <div className="mb-4">
          <h2 className="font-display text-[18px] font-semibold tracking-tight">
            Discover what's happening nearby
          </h2>
        </div>

        {/* Category filter tabs */}
        {status === "ready" && categories.length > 0 && (
          <div className="mb-5 flex flex-wrap gap-2">
            <CategoryTab
              label="All"
              active={activeCategory === "all"}
              onClick={() => setActiveCategory("all")}
            />
            {categories.map((cat) => (
              <CategoryTab
                key={cat}
                label={cat.charAt(0).toUpperCase() + cat.slice(1)}
                active={activeCategory === cat}
                onClick={() => setActiveCategory(cat)}
              />
            ))}
          </div>
        )}

        {status === "loading" && <FeedNote>Loading what's nearby…</FeedNote>}
        {status === "error" && <FeedNote>Couldn't reach the server.</FeedNote>}
        {status === "empty" && (
          <FeedNote>Nothing nearby yet. Once events are active, they'll show up here.</FeedNote>
        )}

        {status === "ready" && filteredEvents.length === 0 && (
          <FeedNote>No {activeCategory} events nearby right now.</FeedNote>
        )}

        {status === "ready" && filteredEvents.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredEvents.map((e) => (
              <EventCard
                key={e.id}
                event={e}
                active={e.id === selectedId}
                onSelect={setSelectedId}
                onDirections={handleDirections}
              />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

function CategoryTab({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-4 py-1.5 text-[13px] font-semibold transition-colors ${
        active
          ? "border-ink bg-ink text-paper"
          : "border-line bg-surface text-muted hover:border-ink hover:text-ink"
      }`}
    >
      {label}
    </button>
  );
}

function FeedNote({ children }) {
  return (
    <div className="rounded-[14px] border border-line bg-surface p-5 text-sm text-muted">
      {children}
    </div>
  );
}

function getUserLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(DEFAULT_CENTER);
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(DEFAULT_CENTER),
      { timeout: 5000 }
    );
  });
}

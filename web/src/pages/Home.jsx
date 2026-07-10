import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import EventCard from "../components/EventCard.jsx";
import EventMap from "../components/EventMap.jsx";
import { getDiscoverFeed, getBusynessNearby, getSavedEvents, saveEvent, unsaveEvent } from "../lib/api.js";
import { fetchRoute, googleMapsUrl } from "../lib/directions.js";
import { DEFAULT_CENTER } from "../lib/config.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Home() {
  const { user, profile } = useAuth();
  const isStudent = !profile || profile.user_type === "student";
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("loading");
  const [selectedId, setSelectedId] = useState(null);
  const [route, setRoute] = useState(null);
  const [busynessAreas, setBusynessAreas] = useState([]);
  const [activeCategory, setActiveCategory] = useState("all");
  const [savedIds, setSavedIds] = useState(new Set());
  const [savePrompt, setSavePrompt] = useState(false);
  const [feedMode, setFeedMode] = useState("all");
  const [userLoc, setUserLoc] = useState(null);

  useEffect(() => {
    if (feedMode === "nearby" && userLoc === null) return;
    let alive = true;
    setStatus("loading");
    const params = feedMode === "nearby"
      ? { lat: userLoc.lat, lng: userLoc.lng, radius_km: 1 }
      : { all: true };
    getDiscoverFeed(params)
      .then((data) => {
        if (!alive) return;
        setEvents(data);
        setStatus(data.length ? "ready" : "empty");
      })
      .catch(() => alive && setStatus("error"));
    return () => { alive = false; };
  }, [feedMode, userLoc]);

  useEffect(() => {
    getBusynessNearby({
      lat: DEFAULT_CENTER.lat,
      lng: DEFAULT_CENTER.lng,
      radius_km: 15,
    })
      .then((data) => setBusynessAreas(data.areas ?? []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!user) return;
    getSavedEvents()
      .then((data) => {
        const ids = (data ?? []).map((s) => s.event?.id ?? s.event_id ?? s.id).filter(Boolean);
        setSavedIds(new Set(ids));
      })
      .catch(() => {});
  }, [user]);

  function scoreToLevel(score) {
    if (score == null) return null;
    if (score < 0.33) return "not busy";
    if (score < 0.66) return "as usual";
    return "busier";
  }

  const getNearestBusynessLevel = useMemo(() => {
    const areas = busynessAreas
      .filter((item) => item.area?.lat != null && item.score != null)
      .map((item) => ({
        lat: Number(item.area.lat),
        lng: Number(item.area.lng),
        level: item.score.level ?? scoreToLevel(item.score.score),
      }))
      .filter((item) => item.level != null);

    return (venueLat, venueLng) => {
      if (!areas.length || venueLat == null || venueLng == null) return null;
      let nearest = null;
      let minDist = Infinity;
      for (const area of areas) {
        const d = Math.hypot(area.lat - Number(venueLat), area.lng - Number(venueLng));
        if (d < minDist) { minDist = d; nearest = area.level; }
      }
      return nearest;
    };
  }, [busynessAreas]);

  async function handleSave(eventId) {
    if (!user) {
      setSavePrompt(true);
      setTimeout(() => setSavePrompt(false), 3000);
      return;
    }
    const wasSaved = savedIds.has(eventId);
    setSavedIds((prev) => {
      const next = new Set(prev);
      if (wasSaved) next.delete(eventId);
      else next.add(eventId);
      return next;
    });
    try {
      if (wasSaved) await unsaveEvent(eventId);
      else await saveEvent(eventId);
    } catch {
      setSavedIds((prev) => {
        const next = new Set(prev);
        if (wasSaved) next.add(eventId);
        else next.delete(eventId);
        return next;
      });
    }
  }

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

  async function handleNearbyMode() {
    if (feedMode === "nearby") return;
    setActiveCategory("all");
    setFeedMode("nearby");
    if (userLoc) return;
    setStatus("loading");
    const loc = await getUserLocation();
    setUserLoc(loc);
  }

  function handleAllMode() {
    if (feedMode === "all") return;
    setActiveCategory("all");
    setFeedMode("all");
  }

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
          {feedMode === "nearby" ? "NEARBY · LIVE · 1KM" : "MANHATTAN · LIVE · ALL"}
          {status === "ready" ? ` · ${events.length} EVENTS` : ""}
        </div>
      </section>

      <div className="px-10 pb-8 xl:px-16">
        <div className="relative h-[50vh] min-h-[400px] overflow-hidden rounded-2xl border border-line">
          <EventMap
            events={events}
            busynessAreas={busynessAreas}
            getNearestBusynessLevel={getNearestBusynessLevel}
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
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#2E9E6B", display: "inline-block" }} /> Not Busy
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#F5A623", display: "inline-block" }} /> As Usual
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#E53935", display: "inline-block" }} /> Busier
              </span>
            </div>
          )}
        </div>
      </div>

      <section aria-label="Events near you" className="px-10 pb-14 xl:px-16">
        <div className="mb-4">
          <h2 className="font-display text-[18px] font-semibold tracking-tight">
            {feedMode === "nearby" ? "Events near you" : "Discover what's happening nearby"}
          </h2>
        </div>

        <div className="mb-5 flex flex-wrap items-center gap-2">
          <CategoryTab label="Nearby" active={feedMode === "nearby"} onClick={handleNearbyMode} />
          <CategoryTab label="All events" active={feedMode === "all"} onClick={handleAllMode} />
          {status === "ready" && categories.length > 0 && (
            <>
              <span className="h-4 w-px bg-line mx-1" />
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
            </>
          )}
        </div>

        {status === "loading" && <FeedNote>Loading what's nearby…</FeedNote>}
        {status === "error" && <FeedNote>Couldn't reach the server.</FeedNote>}
        {status === "empty" && (
          feedMode === "nearby" ? (
            <div className="rounded-[14px] border border-line bg-surface p-5">
              <p className="text-sm text-muted">No events within 1km of your location.</p>
              <p className="mt-1 text-sm text-muted">All FROMO events are currently in Manhattan.</p>
              <button
                onClick={handleAllMode}
                className="mt-3 rounded-full border border-ink bg-ink px-4 py-1.5 text-[13px] font-semibold text-paper"
              >
                Show all Manhattan events →
              </button>
            </div>
          ) : (
            <FeedNote>Nothing nearby yet. Once events are active, they'll show up here.</FeedNote>
          )
        )}

        {status === "ready" && filteredEvents.length === 0 && (
          <FeedNote>No {activeCategory} events {feedMode === "nearby" ? "near you" : "in Manhattan"} right now.</FeedNote>
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
                saved={isStudent && savedIds.has(e.id)}
                onSave={isStudent ? handleSave : undefined}
                busynessLevel={getNearestBusynessLevel(e.venue?.lat, e.venue?.lng)}
              />
            ))}
          </div>
        )}
      </section>

      {savePrompt && (
        <div
          className="fixed bottom-6 left-1/2 z-[9999] -translate-x-1/2 rounded-[12px] border border-line bg-paper px-5 py-3 shadow-lg"
          style={{ display: "flex", alignItems: "center", gap: 12 }}
        >
          <span className="text-[13.5px] font-medium text-ink">
            Log in to save events
          </span>
          <button
            onClick={() => navigate("/login")}
            className="rounded-[8px] bg-amber px-3 py-1.5 text-[12.5px] font-semibold text-[#231a09] hover:bg-amber-press"
          >
            Log in
          </button>
        </div>
      )}
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
      (pos) => {
        const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        const distDeg = Math.hypot(loc.lat - DEFAULT_CENTER.lat, loc.lng - DEFAULT_CENTER.lng);
        resolve(distDeg > 1.0 ? DEFAULT_CENTER : loc);
      },
      () => resolve(DEFAULT_CENTER),
      { timeout: 5000 }
    );
  });
}

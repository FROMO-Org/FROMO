import { useEffect, useMemo, useState } from "react";
import EventCard from "../components/EventCard.jsx";
import EventMap from "../components/EventMap.jsx";
import { getDiscoverFeed } from "../lib/api.js";
import { fetchRoute, googleMapsUrl } from "../lib/directions.js";
import { DEFAULT_CENTER } from "../lib/config.js";

export default function Home() {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | empty | error
  const [selectedId, setSelectedId] = useState(null);
  const [route, setRoute] = useState(null);

  useEffect(() => {
    let alive = true;
    getDiscoverFeed()
      .then((data) => {
        if (!alive) return;
        setEvents(data);
        setStatus(data.length ? "ready" : "empty");
      })
      .catch(() => alive && setStatus("error"));
    return () => {
      alive = false;
    };
  }, []);

  const focus = useMemo(() => {
    const e = events.find((x) => x.id === selectedId);
    return e?.venue ? { lat: e.venue.lat, lng: e.venue.lng } : null;
  }, [selectedId, events]);

  async function handleDirections(event) {
    const v = event.venue || {};
    const dest = { lat: v.lat, lng: v.lng };
    setSelectedId(event.id);
    // Prefer in-app routing (ORS); fall back to Google Maps if no key / failure.
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
        <div className="h-[50vh] min-h-[400px] overflow-hidden rounded-2xl border border-line">
          <EventMap
            events={events}
            focus={focus}
            route={route}
            onSelect={setSelectedId}
          />
        </div>
      </div>

      {/* Events list */}
      <section aria-label="Events near you" className="px-10 pb-14 xl:px-16">
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="font-display text-[18px] font-semibold tracking-tight">
            Happening near you
          </h2>
          <span className="font-mono text-xs text-muted">
            sorted by distance
          </span>
        </div>

        {status === "loading" && <FeedNote>Loading what's nearby…</FeedNote>}
        {status === "error" && (
          <FeedNote>
            Couldn't reach the server. 
          </FeedNote>
        )}
        {status === "empty" && (
          <FeedNote>
            Nothing nearby yet. Once events are active, they'll show up here.
          </FeedNote>
        )}

        {status === "ready" && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {events.map((e) => (
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

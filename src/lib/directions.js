import { ORS_API_KEY } from "./config";

// Google Maps deep link — the fallback when there's no ORS key.
export function googleMapsUrl({ lat, lng, mode = "transit" }) {
  return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&travelmode=${mode}`;
}

// OpenRouteService directions → GeoJSON LineString to draw on the map.
// profile: "foot-walking" | "wheelchair" | "cycling-regular" | "driving-car"
//
// NOTE: free tier is 2000 calls/day. For production, proxy this through the
// backend and cache by (from, to, profile) instead of calling on every click.
export async function fetchRoute({ from, to, profile = "foot-walking" }) {
  if (!ORS_API_KEY) throw new Error("NO_ORS_KEY");

  const res = await fetch(
    `https://api.openrouteservice.org/v2/directions/${profile}/geojson`,
    {
      method: "POST",
      headers: {
        Authorization: ORS_API_KEY,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        coordinates: [
          [from.lng, from.lat],
          [to.lng, to.lat],
        ],
      }),
    }
  );

  if (!res.ok) throw new Error(`ORS_${res.status}`);
  const geojson = await res.json();
  const summary = geojson?.features?.[0]?.properties?.summary ?? {};
  // summary.distance (metres), summary.duration (seconds)
  return { geojson, summary };
}

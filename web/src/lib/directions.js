import { ORS_API_KEY, DEFAULT_CENTER } from "./config";

export function googleMapsUrl({ lat, lng, mode = "transit" }) {
  return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&travelmode=${mode}`;
}

export function getUserLocation() {
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

export async function geocodeAddress(address) {
  if (!ORS_API_KEY) throw new Error("NO_ORS_KEY");

  const res = await fetch(
    `https://api.openrouteservice.org/geocode/search?api_key=${ORS_API_KEY}&text=${encodeURIComponent(address)}&size=1`
  );
  if (!res.ok) throw new Error(`ORS_${res.status}`);

  const geojson = await res.json();
  const feature = geojson?.features?.[0];
  if (!feature) throw new Error("NO_MATCH");

  const [lng, lat] = feature.geometry.coordinates;
  return { lat, lng, label: feature.properties?.label ?? address };
}

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
  return { geojson, summary };
}

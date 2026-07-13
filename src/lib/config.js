// One place for everything tied to your backend contract.
// Confirmed against schemas.py + main.py.

// main.py mounts routers with app.include_router(router) and NO global prefix,
// so the API lives at the server root.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// EventStatus = Literal["draft","active","cancelled","completed"].
// "active" is the publicly visible state for the discover feed.
export const PUBLIC_EVENT_STATUS = "active";

// UserType = Literal["student","organiser","admin"].
// Students discover; organisers run events (the B2B side); admin is internal.
export const USER_TYPE = {
  STUDENT: "student",
  ORGANISER: "organiser",
  ADMIN: "admin",
};

// OpenRouteService — directions key. Set VITE_ORS_API_KEY to draw routes in-app;
// without it, the Directions button falls back to Google Maps.
export const ORS_API_KEY = import.meta.env.VITE_ORS_API_KEY ?? "";

// Map view before we have the user's location (Manhattan).
export const DEFAULT_CENTER = { lat: 40.738, lng: -73.995 };
export const DEFAULT_RADIUS_KM = 5;
export const FEED_LIMIT = 30;

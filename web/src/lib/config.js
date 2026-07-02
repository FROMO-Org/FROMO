export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const PUBLIC_EVENT_STATUS = "active";

export const USER_TYPE = {
  STUDENT: "student",
  ORGANISER: "organiser",
  ADMIN: "admin",
};

// ORS key is optional — without it, Directions falls back to Google Maps.
export const ORS_API_KEY = import.meta.env.VITE_ORS_API_KEY ?? "";

export const DEFAULT_CENTER = { lat: 40.738, lng: -73.995 };
export const DEFAULT_RADIUS_KM = 5;
export const FEED_LIMIT = 30;

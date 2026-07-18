export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "/api";

export const PUBLIC_EVENT_STATUS = "active";

export const USER_TYPE = {
  STUDENT: "student",
  ORGANISER: "organiser",
  ADMIN: "admin",
};

// ORS key is optional — without it, Directions falls back to Google Maps.
export const ORS_API_KEY = import.meta.env.VITE_ORS_API_KEY ?? "";

export const TICKETMASTER_KEY = import.meta.env.VITE_TICKETMASTER_KEY ?? "";
export const UNSPLASH_KEY = import.meta.env.VITE_UNSPLASH_KEY ?? "";

export const DEFAULT_CENTER = { lat: 40.7580, lng: -73.9855 };
export const DEFAULT_RADIUS_KM = 1;
export const FEED_LIMIT = 30;

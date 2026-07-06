import axios from "axios";
import { supabase } from "./supabase";
import {
  API_BASE_URL,
  PUBLIC_EVENT_STATUS,
  DEFAULT_CENTER,
  DEFAULT_RADIUS_KM,
  FEED_LIMIT,
} from "./config";

export const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Profiles (all auth-required) ──
export const getMyProfile = () => api.get("/profiles/me").then((r) => r.data);
export const createMyProfile = (full_name) =>
  api.post("/profiles/me", { full_name }).then((r) => r.data);
// patch = { full_name?, user_type? }
export const updateMyProfile = (patch) =>
  api.patch("/profiles/me", patch).then((r) => r.data);

// ── Events ──
export const listEvents = (params = {}) =>
  api.get("/events/", { params }).then((r) => r.data);
export const getEvent = (id) => api.get(`/events/${id}`).then((r) => r.data);

// ── Venues ──
export const listVenues = (params = {}) =>
  api.get("/venues/", { params }).then((r) => r.data);
export const getVenue = (id) => api.get(`/venues/${id}`).then((r) => r.data);

// ── Busyness ──
export const getBusynessNearby = (params = {}) =>
  api.get("/busyness/nearby", { params }).then((r) => r.data);

// ── Events (write) ──
export const createEvent = (body) =>
  api.post("/events/", body).then((r) => r.data);

// ── Organisations / Partner ──
export const getMyOrganisations = () =>
  api.get("/organisations/me").then((r) => r.data);
export const getOrganisationDashboard = (orgId) =>
  api.get(`/organisations/${orgId}/dashboard`).then((r) => r.data);
export const createOrganisation = (name) =>
  api.post("/organisations/", { name }).then((r) => r.data);

// ── Discover feed ──
export async function getDiscoverFeed({
  lat = DEFAULT_CENTER.lat,
  lng = DEFAULT_CENTER.lng,
  radius_km = DEFAULT_RADIUS_KM,
  limit = FEED_LIMIT,
} = {}) {
  const [items, venues] = await Promise.all([
    listEvents({ status: PUBLIC_EVENT_STATUS, lat, lng, radius_km, limit }),
    listVenues({ limit: 100 }),
  ]);

  const venuesById = Object.fromEntries(venues.map((v) => [v.id, v]));

  return items.map(({ event, distance_km, venue }) => {
    const full = venuesById[venue.id] ?? {};
    return {
      ...event,
      distance_km,
      venue: {
        ...venue,
        category: full.category ?? null,
        address: full.address ?? null,
        is_accessible: full.is_accessible ?? null,
        busyness_area_id: full.busyness_area_id ?? null,
      },
    };
  });
}

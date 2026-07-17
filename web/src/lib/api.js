import axios from "axios";
import { supabase } from "./supabase";
import {
  API_BASE_URL,
  PUBLIC_EVENT_STATUS,
  DEFAULT_CENTER,
  DEFAULT_RADIUS_KM,
  FEED_LIMIT,
} from "./config";
import { fetchEventImage } from "./ticketmaster";

export const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const getMyProfile = () => api.get("/profiles/me").then((r) => r.data);
export const createMyProfile = (full_name) =>
  api.post("/profiles/me", { full_name }).then((r) => r.data);
export const updateMyProfile = (patch) =>
  api.patch("/profiles/me", patch).then((r) => r.data);

export const listEvents = (params = {}) =>
  api.get("/events/", { params }).then((r) => r.data);
export const getEvent = (id) => api.get(`/events/${id}`).then((r) => r.data);

export const listVenues = (params = {}) =>
  api.get("/venues/", { params }).then((r) => r.data);
export const getVenue = (id) => api.get(`/venues/${id}`).then((r) => r.data);

export const getBusynessNearby = (params = {}) =>
  api.get("/busyness/nearby", { params }).then((r) => r.data);

export const createEvent = (body) =>
  api.post("/events/", body).then((r) => r.data);

export const getMyOrganisations = () =>
  api.get("/organisations/me").then((r) => r.data);
export const getOrganisationDashboard = (orgId) =>
  api.get(`/organisations/${orgId}/dashboard`).then((r) => r.data);
export const createOrganisation = (name) =>
  api.post("/organisations/", { name }).then((r) => r.data);

export const getSavedEvents = () => api.get("/saved-events/me").then((r) => r.data);
export const saveEvent = (event_id) =>
  api.post("/saved-events/", { event_id }).then((r) => r.data);
export const unsaveEvent = (event_id) =>
  api.delete(`/saved-events/${event_id}`).then((r) => r.data);

export const getMyBookings = () => api.get("/bookings/me").then((r) => r.data);
export const createBooking = (event_id, quantity = 1) =>
  api.post("/bookings/", { event_id, quantity }).then((r) => r.data);
export const cancelBooking = (booking_id) =>
  api.patch(`/bookings/${booking_id}`).then((r) => r.data);

export async function getDiscoverFeed({
  lat = DEFAULT_CENTER.lat,
  lng = DEFAULT_CENTER.lng,
  radius_km = DEFAULT_RADIUS_KM,
  limit = FEED_LIMIT,
  all = false,
} = {}) {
  // Non-geo /events/ query sorts by starts_at ascending with a hard limit — without
  // this, long-past seed events can fill the whole page before any current one appears.
  const locationParams = all
    ? { starts_after: new Date().toISOString() }
    : { lat, lng, radius_km };
  const [items, venues] = await Promise.all([
    listEvents({ status: PUBLIC_EVENT_STATUS, ...locationParams, limit }),
    listVenues({ limit: 100 }),
  ]);

  const venuesById = Object.fromEntries(venues.map((v) => [v.id, v]));

  const BATCH = 4;
  const enriched = [];
  for (let i = 0; i < items.length; i += BATCH) {
    const batch = items.slice(i, i + BATCH);
    const results = await Promise.all(
      batch.map(async ({ event, distance_km, venue }) => {
        const full = venuesById[venue.id] ?? {};
        const category = event.category || full.category || null;
        const image_url = event.image_url || await fetchEventImage(event.title, category) || null;
        return {
          ...event,
          image_url,
          distance_km,
          venue: {
            ...venue,
            category: full.category ?? null,
            address: full.address ?? null,
            is_accessible: full.is_accessible ?? null,
            busyness_area_id: full.busyness_area_id ?? null,
          },
        };
      })
    );
    enriched.push(...results);
  }

  return enriched;
}

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { googleMapsUrl, fetchRoute } from "../directions.js";

// Mock config so ORS_API_KEY is controllable per test
vi.mock("../config.js", () => ({
  API_BASE_URL: "/api",
  PUBLIC_EVENT_STATUS: "active",
  USER_TYPE: { STUDENT: "student", ORGANISER: "organiser", ADMIN: "admin" },
  ORS_API_KEY: "test-ors-key",
  DEFAULT_CENTER: { lat: 40.738, lng: -73.995 },
  DEFAULT_RADIUS_KM: 5,
  FEED_LIMIT: 30,
}));

describe("googleMapsUrl", () => {
  it("builds a Google Maps deep link with lat/lng", () => {
    const url = googleMapsUrl({ lat: 40.74, lng: -73.99 });
    expect(url).toContain("40.74,-73.99");
    expect(url).toContain("google.com/maps/dir");
  });

  it("includes the travel mode", () => {
    const url = googleMapsUrl({ lat: 40.74, lng: -73.99, mode: "walking" });
    expect(url).toContain("travelmode=walking");
  });

  it("defaults to transit mode", () => {
    const url = googleMapsUrl({ lat: 40.74, lng: -73.99 });
    expect(url).toContain("travelmode=transit");
  });
});

describe("fetchRoute", () => {
  const from = { lat: 40.73, lng: -73.99 };
  const to = { lat: 40.75, lng: -74.0 };

  const mockGeoJson = {
    features: [
      {
        properties: {
          summary: { distance: 1200, duration: 900 },
        },
      },
    ],
  };

  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns geojson and summary on success", async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockGeoJson),
    });

    const result = await fetchRoute({ from, to });
    expect(result.geojson).toEqual(mockGeoJson);
    expect(result.summary).toEqual({ distance: 1200, duration: 900 });
  });

  it("passes correct coordinates to ORS API", async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockGeoJson),
    });

    await fetchRoute({ from, to, profile: "wheelchair" });

    const [, options] = global.fetch.mock.calls[0];
    const body = JSON.parse(options.body);
    expect(body.coordinates).toEqual([
      [-73.99, 40.73],
      [-74.0, 40.75],
    ]);
    expect(global.fetch.mock.calls[0][0]).toContain("wheelchair");
  });

  it("throws ORS_{status} error on non-ok response", async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 429 });
    await expect(fetchRoute({ from, to })).rejects.toThrow("ORS_429");
  });
});

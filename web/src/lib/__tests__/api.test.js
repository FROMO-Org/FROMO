import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock supabase before importing api
vi.mock("../supabase.js", () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
    },
  },
}));

// Capture the axios mock instance so tests can control responses
const mockGet = vi.fn();
vi.mock("axios", () => ({
  default: {
    create: vi.fn(() => ({
      get: mockGet,
      post: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      interceptors: { request: { use: vi.fn() } },
    })),
  },
}));

// Import after mocks are registered
const { getDiscoverFeed, listEvents, listVenues, getEvent } = await import("../api.js");

const sampleEvent = {
  id: "evt-1",
  title: "Jazz Night",
  category: "Music",
  price_cents: 0,
  starts_at: "2025-07-04T20:00:00Z",
  status: "active",
  venue_id: "venue-1",
};

const sampleVenueSummary = { id: "venue-1", name: "Blue Note", lat: 40.73, lng: -73.99 };

const sampleVenueFull = {
  id: "venue-1",
  name: "Blue Note",
  lat: 40.73,
  lng: -73.99,
  category: "Jazz Club",
  address: "131 W 3rd St",
  is_accessible: true,
  busyness_area_id: "area-1",
};

describe("getDiscoverFeed", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("merges full venue data into event items", async () => {
    mockGet
      .mockResolvedValueOnce({
        data: [{ event: sampleEvent, distance_km: 0.5, venue: sampleVenueSummary }],
      })
      .mockResolvedValueOnce({ data: [sampleVenueFull] });

    const feed = await getDiscoverFeed({ lat: 40.73, lng: -73.99 });

    expect(feed).toHaveLength(1);
    expect(feed[0].title).toBe("Jazz Night");
    expect(feed[0].venue.category).toBe("Jazz Club");
    expect(feed[0].venue.address).toBe("131 W 3rd St");
    expect(feed[0].venue.is_accessible).toBe(true);
    expect(feed[0].distance_km).toBe(0.5);
  });

  it("falls back to null fields when venue is missing from venues list", async () => {
    mockGet
      .mockResolvedValueOnce({
        data: [{ event: sampleEvent, distance_km: 1.2, venue: sampleVenueSummary }],
      })
      .mockResolvedValueOnce({ data: [] }); // no venues returned

    const feed = await getDiscoverFeed({ lat: 40.73, lng: -73.99 });

    expect(feed[0].venue.category).toBeNull();
    expect(feed[0].venue.address).toBeNull();
    expect(feed[0].venue.is_accessible).toBeNull();
  });

  it("calls events and venues endpoints concurrently", async () => {
    mockGet
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: [] });

    await getDiscoverFeed({ lat: 40.73, lng: -73.99 });

    expect(mockGet).toHaveBeenCalledTimes(2);
    const [eventsCall, venuesCall] = mockGet.mock.calls;
    expect(eventsCall[0]).toContain("/events/");
    expect(venuesCall[0]).toContain("/venues/");
  });

  it("returns an empty array when no events are found", async () => {
    mockGet
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: [sampleVenueFull] });

    const feed = await getDiscoverFeed();
    expect(feed).toEqual([]);
  });
});

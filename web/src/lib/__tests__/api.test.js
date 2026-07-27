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
const { getDiscoverFeed } = await import("../api.js");

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
      .mockResolvedValueOnce({ data: sampleVenueFull });

    const feed = await getDiscoverFeed({ lat: 40.73, lng: -73.99 });

    expect(feed.items).toHaveLength(1);
    expect(feed.items[0].title).toBe("Jazz Night");
    expect(feed.items[0].venue.category).toBe("Jazz Club");
    expect(feed.items[0].venue.address).toBe("131 W 3rd St");
    expect(feed.items[0].venue.is_accessible).toBe(true);
    expect(feed.items[0].distance_km).toBe(0.5);
  });

  it("falls back to null fields when the venue lookup fails", async () => {
    mockGet
      .mockResolvedValueOnce({
        data: [{ event: sampleEvent, distance_km: 1.2, venue: sampleVenueSummary }],
      })
      .mockRejectedValueOnce(new Error("not found")); // individual getVenue() call fails

    const feed = await getDiscoverFeed({ lat: 40.73, lng: -73.99 });

    expect(feed.items[0].venue.category).toBeNull();
    expect(feed.items[0].venue.address).toBeNull();
    expect(feed.items[0].venue.is_accessible).toBeNull();
  });

  it("fetches only the specific venues referenced by the returned events", async () => {
    mockGet
      .mockResolvedValueOnce({
        data: [{ event: sampleEvent, distance_km: 0.5, venue: sampleVenueSummary }],
      })
      .mockResolvedValueOnce({ data: sampleVenueFull });

    await getDiscoverFeed({ lat: 40.73, lng: -73.99 });

    expect(mockGet).toHaveBeenCalledTimes(2);
    const [eventsCall, venueCall] = mockGet.mock.calls;
    expect(eventsCall[0]).toContain("/events/");
    expect(venueCall[0]).toBe("/venues/venue-1");
  });

  it("returns an empty items array and hasMore=false when no events are found", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });

    const feed = await getDiscoverFeed();
    expect(feed).toEqual({ items: [], hasMore: false });
  });

  it("reports hasMore=true when a full page of results comes back", async () => {
    const fullPage = Array.from({ length: 3 }, (_, i) => ({
      event: { ...sampleEvent, id: `evt-${i}` },
      distance_km: 0.1,
      venue: sampleVenueSummary,
    }));
    mockGet
      .mockResolvedValueOnce({ data: fullPage })
      .mockResolvedValue({ data: sampleVenueFull });

    const feed = await getDiscoverFeed({ lat: 40.73, lng: -73.99, limit: 3 });
    expect(feed.hasMore).toBe(true);
  });

  it("reports hasMore=false when fewer results than the limit come back", async () => {
    mockGet
      .mockResolvedValueOnce({
        data: [{ event: sampleEvent, distance_km: 0.5, venue: sampleVenueSummary }],
      })
      .mockResolvedValueOnce({ data: sampleVenueFull });

    const feed = await getDiscoverFeed({ lat: 40.73, lng: -73.99, limit: 30 });
    expect(feed.hasMore).toBe(false);
  });
});

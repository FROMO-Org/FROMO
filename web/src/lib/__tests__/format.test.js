import { describe, it, expect } from "vitest";
import { kmToMi, formatDistance, formatPrice, formatTime } from "../format.js";

describe("kmToMi", () => {
  it("converts kilometres to miles", () => {
    expect(kmToMi(1)).toBeCloseTo(0.621371);
  });
  it("returns null for null input", () => {
    expect(kmToMi(null)).toBeNull();
  });
  it("converts 0 to 0", () => {
    expect(kmToMi(0)).toBe(0);
  });
});

describe("formatDistance", () => {
  it("formats a normal distance", () => {
    expect(formatDistance(1)).toBe("0.6 mi");
  });
  it("clamps very small distances to 0.1 mi", () => {
    expect(formatDistance(0.01)).toBe("0.1 mi");
  });
  it("returns null for null input", () => {
    expect(formatDistance(null)).toBeNull();
  });
  it("rounds to one decimal place", () => {
    expect(formatDistance(2)).toBe("1.2 mi");
  });
});

describe("formatPrice", () => {
  it("returns 'Free' for 0 cents", () => {
    expect(formatPrice(0)).toBe("Free");
  });
  it("formats cents as dollars", () => {
    expect(formatPrice(1299)).toBe("$12.99");
  });
  it("omits .00 for whole dollar amounts", () => {
    expect(formatPrice(1000)).toBe("$10");
  });
  it("returns null for null input", () => {
    expect(formatPrice(null)).toBeNull();
  });
});

describe("formatTime", () => {
  it("returns null for falsy input", () => {
    expect(formatTime(null)).toBeNull();
    expect(formatTime("")).toBeNull();
    expect(formatTime(undefined)).toBeNull();
  });
  it("returns null for an invalid date string", () => {
    expect(formatTime("not-a-date")).toBeNull();
  });
  it("returns a formatted string for a valid ISO date", () => {
    const result = formatTime("2025-07-04T14:30:00Z");
    expect(result).toMatch(/·/);
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });
});

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import EventCard from "../EventCard.jsx";

vi.mock("../../context/AuthContext.jsx", () => ({
  useAuth: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, useNavigate: () => mockNavigate };
});

import { useAuth } from "../../context/AuthContext.jsx";

const baseEvent = {
  id: "evt-1",
  title: "Jazz Night",
  category: "Music",
  price_cents: 1500,
  starts_at: "2025-07-04T20:00:00Z",
  distance_km: 0.8,
  venue: {
    id: "venue-1",
    name: "Blue Note",
    address: "131 W 3rd St",
    is_accessible: true,
  },
};

function renderCard(props = {}) {
  return render(
    <MemoryRouter>
      <EventCard
        event={baseEvent}
        active={false}
        onSelect={vi.fn()}
        onDirections={vi.fn()}
        {...props}
      />
    </MemoryRouter>
  );
}

describe("EventCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuth.mockReturnValue({ user: { id: "user-1" } });
  });

  it("renders the event title", () => {
    renderCard();
    expect(screen.getByText("Jazz Night")).toBeInTheDocument();
  });

  it("renders the venue name and address", () => {
    renderCard();
    expect(screen.getByText(/Blue Note/)).toBeInTheDocument();
    expect(screen.getByText(/131 W 3rd St/)).toBeInTheDocument();
  });

  it("renders the event category", () => {
    renderCard();
    expect(screen.getByText(/Music/i)).toBeInTheDocument();
  });

  it("renders formatted price", () => {
    renderCard();
    expect(screen.getByText("$15")).toBeInTheDocument();
  });

  it("renders 'Free' for zero-price events", () => {
    renderCard({ event: { ...baseEvent, price_cents: 0 } });
    expect(screen.getByText("Free")).toBeInTheDocument();
  });

  it("shows step-free badge when venue is accessible", () => {
    renderCard();
    expect(screen.getByText(/Step-free entrance/i)).toBeInTheDocument();
  });

  it("shows steps badge when venue is not accessible", () => {
    renderCard({
      event: { ...baseEvent, venue: { ...baseEvent.venue, is_accessible: false } },
    });
    expect(screen.getByText(/Steps at entrance/i)).toBeInTheDocument();
  });

  it("navigates to the event detail page when card is clicked", () => {
    renderCard();
    fireEvent.click(screen.getByRole("article"));
    expect(mockNavigate).toHaveBeenCalledWith("/events/evt-1", { state: { event: baseEvent } });
  });

  it("navigates to /login when a signed-out user clicks the card", () => {
    useAuth.mockReturnValue({ user: null });
    renderCard();
    fireEvent.click(screen.getByRole("article"));
    expect(mockNavigate).toHaveBeenCalledWith("/login");
  });

  it("calls onDirections when Directions button is clicked", () => {
    const onDirections = vi.fn();
    renderCard({ onDirections });
    fireEvent.click(screen.getByRole("button", { name: /directions/i }));
    expect(onDirections).toHaveBeenCalledWith(baseEvent);
  });

  it("does not navigate when Directions button is clicked", () => {
    const onDirections = vi.fn();
    renderCard({ onDirections });
    fireEvent.click(screen.getByRole("button", { name: /directions/i }));
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("applies active border styles when active is true", () => {
    renderCard({ active: true });
    expect(screen.getByRole("article").className).toContain("border-amber");
  });
});

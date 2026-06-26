import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import EventCard from "../EventCard.jsx";

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

  it("calls onSelect when card is clicked", () => {
    const onSelect = vi.fn();
    renderCard({ onSelect });
    fireEvent.click(screen.getByRole("article"));
    expect(onSelect).toHaveBeenCalledWith("evt-1");
  });

  it("calls onDirections when Directions button is clicked", () => {
    const onDirections = vi.fn();
    renderCard({ onDirections });
    fireEvent.click(screen.getByRole("button", { name: /directions/i }));
    expect(onDirections).toHaveBeenCalledWith(baseEvent);
  });

  it("does not propagate card click when Directions button is clicked", () => {
    const onSelect = vi.fn();
    const onDirections = vi.fn();
    renderCard({ onSelect, onDirections });
    fireEvent.click(screen.getByRole("button", { name: /directions/i }));
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("applies active border styles when active is true", () => {
    renderCard({ active: true });
    expect(screen.getByRole("article").className).toContain("border-amber");
  });
});

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Header from "../Header.jsx";

// Mock AuthContext so Header can be tested in isolation
vi.mock("../../context/AuthContext.jsx", () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from "../../context/AuthContext.jsx";

function renderHeader() {
  return render(
    <MemoryRouter>
      <Header />
    </MemoryRouter>
  );
}

describe("Header — logged out", () => {
  beforeEach(() => {
    useAuth.mockReturnValue({ user: null, profile: null, signOut: vi.fn() });
  });

  it("renders the FROMO brand link", () => {
    renderHeader();
    expect(screen.getByText(/FROMO/)).toBeInTheDocument();
  });

  it("shows Log in and Sign up buttons", () => {
    renderHeader();
    expect(screen.getByRole("link", { name: /log in/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /sign up/i })).toBeInTheDocument();
  });

  it("does not show Sign out button", () => {
    renderHeader();
    expect(screen.queryByRole("button", { name: /sign out/i })).not.toBeInTheDocument();
  });

  it("has the FROMO brand link pointing to /", () => {
    renderHeader();
    expect(screen.getByRole("link", { name: /fromo/i })).toHaveAttribute("href", "/");
  });
});

describe("Header — logged in as student", () => {
  const mockSignOut = vi.fn();

  beforeEach(() => {
    useAuth.mockReturnValue({
      user: { email: "student@test.com", user_metadata: { full_name: "Alex T" } },
      profile: { full_name: "Alex T", user_type: "student" },
      signOut: mockSignOut,
    });
  });

  it("shows the user's name", () => {
    renderHeader();
    expect(screen.getByText("Alex T")).toBeInTheDocument();
  });

  it("shows the Sign out button", () => {
    renderHeader();
    expect(screen.getByRole("button", { name: /sign out/i })).toBeInTheDocument();
  });

  it("does not show Log in / Sign up links", () => {
    renderHeader();
    expect(screen.queryByRole("link", { name: /log in/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /sign up/i })).not.toBeInTheDocument();
  });

  it("shows settings avatar link for students", () => {
    renderHeader();
    // Avatar link has title="Settings" but accessible name is the initials "AT"
    const avatarLink = screen.getByTitle("Settings");
    expect(avatarLink).toHaveAttribute("href", "/settings");
  });

  it("calls signOut when Sign out button is clicked", async () => {
    renderHeader();
    fireEvent.click(screen.getByRole("button", { name: /sign out/i }));
    expect(mockSignOut).toHaveBeenCalled();
  });
});

describe("Header — logged in as organiser", () => {
  beforeEach(() => {
    useAuth.mockReturnValue({
      user: { email: "org@test.com", user_metadata: { full_name: "Org User" } },
      profile: { full_name: "Org User", user_type: "organiser" },
      signOut: vi.fn(),
    });
  });

  it("does not show the settings avatar link for organisers", () => {
    renderHeader();
    expect(screen.queryByRole("link", { name: /settings/i })).not.toBeInTheDocument();
  });
});

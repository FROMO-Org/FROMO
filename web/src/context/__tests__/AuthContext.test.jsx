import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "../AuthContext.jsx";

// Mock supabase
vi.mock("../../lib/supabase.js", () => ({
  supabase: {
    auth: {
      getSession: vi.fn(),
      onAuthStateChange: vi.fn(),
      signUp: vi.fn(),
      signInWithPassword: vi.fn(),
      signOut: vi.fn(),
    },
  },
}));

// Mock API functions
vi.mock("../../lib/api.js", () => ({
  getMyProfile: vi.fn(),
  createMyProfile: vi.fn(),
  updateMyProfile: vi.fn(),
}));

import { supabase } from "../../lib/supabase.js";
import { getMyProfile, createMyProfile, updateMyProfile } from "../../lib/api.js";

const sampleProfile = {
  id: "user-1",
  email: "test@test.com",
  full_name: "Test User",
  user_type: "student",
};

function TestConsumer() {
  const auth = useAuth();
  if (auth.loading) return <div>loading</div>;
  return (
    <div>
      <div data-testid="user">{auth.user?.email ?? "no-user"}</div>
      <div data-testid="profile">{auth.profile?.full_name ?? "no-profile"}</div>
      <button onClick={() => auth.signOut()}>Sign Out</button>
    </div>
  );
}

function renderWithAuth() {
  return render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    supabase.auth.onAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe: vi.fn() } },
    });
  });

  it("starts in loading state then settles with no user when no session", async () => {
    supabase.auth.getSession.mockResolvedValue({ data: { session: null } });

    renderWithAuth();
    expect(screen.getByText("loading")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("user")).toHaveTextContent("no-user");
    });
    expect(screen.getByTestId("profile")).toHaveTextContent("no-profile");
  });

  it("loads profile when session exists on mount", async () => {
    supabase.auth.getSession.mockResolvedValue({
      data: { session: { user: { email: "test@test.com" }, access_token: "tok" } },
    });
    getMyProfile.mockResolvedValue(sampleProfile);

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByTestId("user")).toHaveTextContent("test@test.com");
    });
    await waitFor(() => {
      expect(screen.getByTestId("profile")).toHaveTextContent("Test User");
    });
  });

  it("sets profile to null when getMyProfile returns 404", async () => {
    supabase.auth.getSession.mockResolvedValue({
      data: { session: { user: { email: "new@test.com" }, access_token: "tok" } },
    });
    getMyProfile.mockRejectedValue(Object.assign(new Error("Not found"), { status: 404 }));

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByTestId("profile")).toHaveTextContent("no-profile");
    });
  });

  it("clears profile on sign out", async () => {
    supabase.auth.getSession.mockResolvedValue({ data: { session: null } });
    supabase.auth.signOut.mockResolvedValue({});

    renderWithAuth();
    await waitFor(() => screen.getByTestId("user"));

    await act(async () => {
      screen.getByRole("button", { name: /sign out/i }).click();
    });

    expect(supabase.auth.signOut).toHaveBeenCalled();
    expect(screen.getByTestId("profile")).toHaveTextContent("no-profile");
  });
});

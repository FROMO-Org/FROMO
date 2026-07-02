import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Login from "../Login.jsx";

vi.mock("../../context/AuthContext.jsx", () => ({
  useAuth: vi.fn(),
}));

// react-router-dom navigate mock
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, useNavigate: () => mockNavigate };
});

import { useAuth } from "../../context/AuthContext.jsx";

function renderLogin() {
  return render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>
  );
}

describe("Login page", () => {
  const mockSignIn = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    useAuth.mockReturnValue({ signIn: mockSignIn });
  });

  it("renders email and password fields", () => {
    renderLogin();
    expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
  });

  it("renders Student and Partner role tabs", () => {
    renderLogin();
    expect(screen.getByRole("button", { name: /student/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /partner/i })).toBeInTheDocument();
  });

  it("renders Sign In button", () => {
    renderLogin();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("renders a link to the signup page", () => {
    renderLogin();
    expect(screen.getByRole("link", { name: /sign up/i })).toHaveAttribute("href", "/signup");
  });

  it("calls signIn with email and password on submit", async () => {
    mockSignIn.mockResolvedValue({});
    renderLogin();

    await userEvent.type(screen.getByPlaceholderText(/email/i), "user@test.com");
    await userEvent.type(screen.getByPlaceholderText(/password/i), "secret123");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith({
        email: "user@test.com",
        password: "secret123",
      });
    });
  });

  it("navigates to / after successful student login", async () => {
    mockSignIn.mockResolvedValue({});
    renderLogin();

    await userEvent.type(screen.getByPlaceholderText(/email/i), "student@test.com");
    await userEvent.type(screen.getByPlaceholderText(/password/i), "pass123");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/");
    });
  });

  it("navigates to /partner after successful partner login", async () => {
    mockSignIn.mockResolvedValue({});
    renderLogin();

    fireEvent.click(screen.getByRole("button", { name: /partner/i }));
    await userEvent.type(screen.getByPlaceholderText(/email/i), "org@test.com");
    await userEvent.type(screen.getByPlaceholderText(/password/i), "pass123");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/partner");
    });
  });

  it("shows an error message when sign-in fails", async () => {
    mockSignIn.mockRejectedValue(new Error("Invalid credentials"));
    renderLogin();

    await userEvent.type(screen.getByPlaceholderText(/email/i), "bad@test.com");
    await userEvent.type(screen.getByPlaceholderText(/password/i), "wrong");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it("disables the button while sign-in is in progress", async () => {
    let resolveSignIn;
    mockSignIn.mockReturnValue(new Promise((r) => { resolveSignIn = r; }));
    renderLogin();

    await userEvent.type(screen.getByPlaceholderText(/email/i), "user@test.com");
    await userEvent.type(screen.getByPlaceholderText(/password/i), "pass123");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /signing in/i })).toBeDisabled();
    });

    resolveSignIn({});
  });
});

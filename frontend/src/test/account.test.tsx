import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AccountScreen } from "@/routes/account";
import { services } from "@/services";
import { SESSION_LIFETIME_MS, createAuthService } from "@/services/auth";

const jsonResponse = (body: unknown, status = 200) =>
  ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  }) as unknown as Response;

const tokenResponse = () => jsonResponse({ accessToken: "signed-token", tokenType: "bearer" });

function fillCredentials(username = "reader", password = "long-enough-password") {
  fireEvent.change(screen.getByLabelText("Username"), { target: { value: username } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: password } });
}

describe("account access", () => {
  beforeEach(() => {
    act(() => services.auth.signOut());
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    act(() => services.auth.signOut());
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("registers through the auth service and confirms the in-memory session", async () => {
    const fetchMock = vi.mocked(fetch).mockResolvedValue(tokenResponse());
    render(<AccountScreen />);
    fireEvent.click(screen.getByRole("button", { name: "Create an account" }));
    fillCredentials("new-reader");
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByText("You're signed in")).toBeInTheDocument();
    expect(screen.getByText("new-reader")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/register",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ username: "new-reader", password: "long-enough-password" }),
      }),
    );
    expect(services.auth.getAccessToken()).toBe("signed-token");
  });

  it("signs in and shows actionable messages for duplicate and invalid credentials", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(tokenResponse());
    const { rerender } = render(<AccountScreen />);
    fillCredentials();
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("You're signed in")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({ method: "POST" }),
    );

    act(() => services.auth.signOut());
    rerender(<AccountScreen />);
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "private backend text" }, 401));
    fillCredentials("reader", "incorrect-password");
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("don't match");
    expect(screen.queryByText("private backend text")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Create an account" }));
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "private backend text" }, 409));
    fillCredentials("reader");
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("already registered");
    expect(screen.queryByText("private backend text")).not.toBeInTheDocument();
  });

  it("turns validation failures into guidance without showing raw response details", async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ detail: [{ msg: "private validation detail" }] }, 422),
    );
    render(<AccountScreen />);
    fillCredentials();
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "password between 8 and 200 characters",
    );
    expect(screen.queryByText("private validation detail")).not.toBeInTheDocument();
  });

  it("signs out and a fresh app instance starts signed out after a reload", async () => {
    const request = vi.fn().mockResolvedValue(tokenResponse());
    const authBeforeReload = createAuthService({ fetcher: request });
    await authBeforeReload.login({ username: "reader", password: "long-enough-password" });
    expect(authBeforeReload.getAccessToken()).toBe("signed-token");

    const authAfterReload = createAuthService({ fetcher: request });
    expect(authAfterReload.getSnapshot()).toMatchObject({ isAuthenticated: false, username: null });
    expect(authAfterReload.getAccessToken()).toBeNull();

    services.auth.getSnapshot();
    const fetchMock = vi.mocked(fetch).mockResolvedValue(tokenResponse());
    render(<AccountScreen />);
    fillCredentials();
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await screen.findByText("You're signed in");
    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(services.auth.getAccessToken()).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    authBeforeReload.signOut();
    authAfterReload.signOut();
  });

  it("expires within 24 hours and shares the same notice for unauthorized responses", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T00:00:00Z"));
    const request = vi.fn().mockResolvedValue(tokenResponse());
    const auth = createAuthService({ fetcher: request });
    await auth.login({ username: "reader", password: "long-enough-password" });
    expect(auth.getSnapshot().expiresAt).toBe(Date.now() + SESSION_LIFETIME_MS);

    vi.advanceTimersByTime(SESSION_LIFETIME_MS);
    expect(auth.getAccessToken()).toBeNull();
    expect(auth.getSnapshot().notice).toBe("Your session expired. Sign in again to continue.");

    await auth.login({ username: "reader", password: "long-enough-password" });
    auth.handleUnauthorized();
    expect(auth.getAccessToken()).toBeNull();
    expect(auth.getSnapshot().notice).toBe("Your session expired. Sign in again to continue.");
  });

  it("shows the expiration sign-in notice after a shared unauthorized action", async () => {
    vi.mocked(fetch).mockResolvedValue(tokenResponse());
    render(<AccountScreen />);
    fillCredentials();
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await screen.findByText("You're signed in");

    act(() => services.auth.handleUnauthorized());

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Your session expired. Sign in again to continue.",
    );
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
  });
});

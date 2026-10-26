import { QueryClient } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";

import { handleSessionTransition } from "@/lib/session-cache";
import {
  createAuthService,
  SESSION_LIFETIME_MS,
  type AccountSessionSnapshot,
} from "@/services/auth";

const signedOut: AccountSessionSnapshot = {
  isAuthenticated: false,
  username: null,
  expiresAt: null,
  notice: null,
};

afterEach(() => {
  vi.useRealTimers();
});

describe("private journal cache", () => {
  it("clears cached journal data on sign-out and account changes", () => {
    const client = new QueryClient();
    const signedIn: AccountSessionSnapshot = {
      isAuthenticated: true,
      username: "first-user",
      expiresAt: 10_000,
      notice: null,
    };
    const secondUser: AccountSessionSnapshot = { ...signedIn, username: "second-user" };

    client.setQueryData(["reviews"], [{ id: "first-users-review" }]);
    handleSessionTransition(client, signedIn, secondUser, "/history", vi.fn());
    expect(client.getQueryData(["reviews"])).toBeUndefined();

    client.setQueryData(["reviews"], [{ id: "second-users-review" }]);
    handleSessionTransition(client, secondUser, signedOut, "/account", vi.fn());
    expect(client.getQueryData(["reviews"])).toBeUndefined();

    client.setQueryData(["reviews"], [{ id: "same-users-old-session" }]);
    handleSessionTransition(
      client,
      signedIn,
      { ...signedIn, expiresAt: 20_000 },
      "/history",
      vi.fn(),
    );
    expect(client.getQueryData(["reviews"])).toBeUndefined();
  });

  it("publishes delayed expiry on focus so the private cache clears and the router returns to account", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T00:00:00Z"));
    const auth = createAuthService({
      fetcher: vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ accessToken: "fake-token", tokenType: "bearer" }),
      } as Response),
    });
    const queryClient = new QueryClient();
    const navigateToAccount = vi.fn();
    await auth.login({ username: "reader", password: "long-enough-password" });
    const previous = auth.getSnapshot();
    queryClient.setQueryData(["reviews"], [{ id: "private-review" }]);

    let previousSnapshot = previous;
    auth.subscribe(() => {
      const current = auth.getSnapshot();
      handleSessionTransition(
        queryClient,
        previousSnapshot,
        current,
        "/history",
        navigateToAccount,
      );
      previousSnapshot = current;
    });

    // Simulate a suspended tab: wall time advances, while the scheduled expiry callback does not run.
    vi.setSystemTime(new Date(Date.now() + SESSION_LIFETIME_MS + 1));
    expect(auth.getSnapshot().isAuthenticated).toBe(true);
    auth.refreshSession();

    expect(auth.getSnapshot()).toMatchObject({ isAuthenticated: false, username: null });
    expect(auth.getAccessToken()).toBeNull();
    expect(queryClient.getQueryData(["reviews"])).toBeUndefined();
    expect(navigateToAccount).toHaveBeenCalledOnce();
  });
});

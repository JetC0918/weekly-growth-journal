import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { services } from "@/services";

const jsonResponse = (body: unknown, status = 200) =>
  ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  }) as unknown as Response;

describe("app-wide journal service", () => {
  beforeEach(() => {
    services.auth.signOut();
  });

  afterEach(() => {
    services.auth.signOut();
    vi.unstubAllGlobals();
  });

  it("uses the HTTP service and attaches the active in-memory bearer token", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({ accessToken: "active-token", tokenType: "bearer" }, 201),
      )
      .mockResolvedValueOnce(jsonResponse([]));
    vi.stubGlobal("fetch", fetchMock);

    await services.auth.login({ username: "reader", password: "long-enough-password" });
    await expect(services.listReviews()).resolves.toEqual([]);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/auth/login",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/reviews",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ Authorization: "Bearer active-token" }),
      }),
    );
  });
});

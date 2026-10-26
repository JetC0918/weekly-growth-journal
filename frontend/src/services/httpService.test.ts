import { describe, expect, it, vi } from "vitest";

import { ApiError, createHttpService } from "./httpService";
import type { Commitment, Report, Review, SaveReviewInput } from "./types";

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response;
}

function emptyResponse(status = 204): Response {
  return { ok: status >= 200 && status < 300, status } as Response;
}

const sampleReview: Review = {
  id: "rev-1",
  weekStart: "2026-10-19",
  answers: {
    wentWell: "A good week.",
    didntGoWell: "",
    handledBetter: "",
    learned: "",
    doDifferently: "",
  },
  freeWriting: "",
  followUps: [],
  status: "draft",
  createdAt: "2026-10-19T00:00:00Z",
  updatedAt: "2026-10-19T00:00:00Z",
};

const sampleReport: Report = {
  id: "rep-1",
  reviewId: sampleReview.id,
  takeaways: [],
  strengths: [],
  challenges: [],
  patterns: [],
  proposedAction: "",
  generatedAt: "2026-10-19T00:00:00Z",
};

const sampleCommitment: Commitment = {
  id: "com-1",
  reviewId: sampleReview.id,
  weekStart: sampleReview.weekStart,
  text: "Keep going",
  measure: "Once",
  createdAt: "2026-10-19T00:00:00Z",
};

const sampleInput: SaveReviewInput = {
  weekStart: sampleReview.weekStart,
  answers: sampleReview.answers,
  freeWriting: sampleReview.freeWriting,
  followUps: [],
};

function setup() {
  const getAccessToken = vi.fn(() => "current-token");
  const handleUnauthorized = vi.fn();
  const fetcher = vi.fn<typeof fetch>();
  const service = createHttpService(
    { getAccessToken, handleUnauthorized },
    { baseUrl: "https://journal.example/api/", fetcher },
  );
  return { service, fetcher, getAccessToken, handleUnauthorized };
}

describe("HTTP GrowthService", () => {
  it("maps every GrowthService operation to its OpenAPI request and response", async () => {
    const { service, fetcher, getAccessToken } = setup();
    const bodyResponses = [
      jsonResponse([]),
      jsonResponse(null),
      jsonResponse(null),
      jsonResponse(sampleReview),
      emptyResponse(),
      jsonResponse(["A follow-up?"]),
      jsonResponse(sampleReport),
      jsonResponse(null),
      jsonResponse(sampleReport),
      jsonResponse(sampleCommitment),
      jsonResponse(null),
      jsonResponse(null),
      emptyResponse(),
    ];
    bodyResponses.forEach((response) => fetcher.mockResolvedValueOnce(response));

    expect(await service.listReviews()).toEqual([]);
    expect(await service.getReview("review/one")).toBeNull();
    expect(await service.getReviewForWeek(sampleReview.weekStart)).toBeNull();
    expect(await service.saveReview(sampleInput)).toEqual(sampleReview);
    await expect(service.deleteReview("review/one")).resolves.toBeUndefined();
    expect(await service.suggestFollowUps(sampleInput)).toEqual(["A follow-up?"]);
    expect(await service.completeReview("review/one")).toEqual(sampleReport);
    expect(await service.getReport("review/one")).toBeNull();
    expect(
      await service.updateInsight("review/one", "takeaways", "insight/one", { status: "accepted" }),
    ).toEqual(sampleReport);
    expect(
      await service.setCommitment("review/one", { text: "Keep going", measure: "Once" }),
    ).toEqual(sampleCommitment);
    expect(await service.getCommitment("review/one")).toBeNull();
    expect(await service.getCommitmentBefore(sampleReview.weekStart)).toBeNull();
    await expect(service.deleteAllData()).resolves.toBeUndefined();

    const requests = fetcher.mock.calls;
    expect(requests.map(([url, init]) => [url, init?.method ?? "GET"])).toEqual([
      ["https://journal.example/api/reviews", "GET"],
      ["https://journal.example/api/reviews/review%2Fone", "GET"],
      ["https://journal.example/api/reviews/by-week/2026-10-19", "GET"],
      ["https://journal.example/api/reviews", "POST"],
      ["https://journal.example/api/reviews/review%2Fone", "DELETE"],
      ["https://journal.example/api/reviews/suggest-follow-ups", "POST"],
      ["https://journal.example/api/reviews/review%2Fone/complete", "POST"],
      ["https://journal.example/api/reviews/review%2Fone/report", "GET"],
      [
        "https://journal.example/api/reviews/review%2Fone/report/takeaways/insights/insight%2Fone",
        "PATCH",
      ],
      ["https://journal.example/api/reviews/review%2Fone/commitment", "PUT"],
      ["https://journal.example/api/reviews/review%2Fone/commitment", "GET"],
      ["https://journal.example/api/commitments/before?weekStart=2026-10-19", "GET"],
      ["https://journal.example/api/data", "DELETE"],
    ]);
    expect(getAccessToken).toHaveBeenCalledTimes(13);

    for (const [, init] of requests) {
      expect(init?.headers).toMatchObject({
        Accept: "application/json",
        Authorization: "Bearer current-token",
      });
    }
    expect(requests[3]?.[1]?.body).toBe(JSON.stringify(sampleInput));
    expect(requests[5]?.[1]?.body).toBe(JSON.stringify(sampleInput));
    expect(requests[8]?.[1]?.body).toBe(JSON.stringify({ status: "accepted" }));
    expect(requests[9]?.[1]?.body).toBe(JSON.stringify({ text: "Keep going", measure: "Once" }));
    expect(requests[0]?.[1]?.headers).not.toHaveProperty("Content-Type");
  });

  it("reads a fresh bearer token per request and encodes query parameters", async () => {
    const { service, fetcher, getAccessToken } = setup();
    getAccessToken.mockReturnValueOnce("first-token").mockReturnValueOnce("second-token");
    fetcher.mockResolvedValueOnce(jsonResponse(null)).mockResolvedValueOnce(jsonResponse(null));

    await service.getReview("id with space/and?query");
    await service.getCommitmentBefore("2026-10-19&admin=true");

    expect(fetcher.mock.calls[0]?.[0]).toBe(
      "https://journal.example/api/reviews/id%20with%20space%2Fand%3Fquery",
    );
    expect(fetcher.mock.calls[1]?.[0]).toBe(
      "https://journal.example/api/commitments/before?weekStart=2026-10-19%26admin%3Dtrue",
    );
    expect(fetcher.mock.calls[0]?.[1]?.headers).toMatchObject({
      Authorization: "Bearer first-token",
    });
    expect(fetcher.mock.calls[1]?.[1]?.headers).toMatchObject({
      Authorization: "Bearer second-token",
    });
  });

  it("expires the shared session on 401 and rejects with its safe detail", async () => {
    const { service, fetcher, handleUnauthorized } = setup();
    fetcher.mockResolvedValueOnce(jsonResponse({ detail: "Bearer token required" }, 401));

    await expect(service.listReviews()).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      detail: "Bearer token required",
      message: "401: Bearer token required",
    });
    expect(handleUnauthorized).toHaveBeenCalledOnce();
  });

  it("keeps status and fallback detail for non-JSON and empty errors", async () => {
    const { service, fetcher } = setup();
    fetcher
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: vi.fn().mockRejectedValue(new SyntaxError("invalid JSON")),
      } as unknown as Response)
      .mockResolvedValueOnce(emptyResponse(404));

    await expect(service.getReview("missing")).rejects.toMatchObject({
      status: 500,
      detail: "The request failed (HTTP 500).",
      message: "500: The request failed (HTTP 500).",
    });
    await expect(service.getReport("missing")).rejects.toMatchObject({
      status: 404,
      detail: "The request failed (HTTP 404).",
    });
  });

  it("includes a safe server detail when provided and handles network failures", async () => {
    const { service, fetcher } = setup();
    fetcher
      .mockResolvedValueOnce(jsonResponse({ detail: "Review not found" }, 404))
      .mockRejectedValueOnce(new TypeError("private network detail"));

    await expect(service.completeReview("missing")).rejects.toMatchObject({
      status: 404,
      detail: "Review not found",
      message: "404: Review not found",
    });
    await expect(service.listReviews()).rejects.toMatchObject({
      status: 0,
      detail: "Unable to reach the journal service. Check your connection and try again.",
    });
  });
});

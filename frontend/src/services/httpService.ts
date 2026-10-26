import type { GrowthService } from "./api";
import type { AuthService } from "./auth";
import type { Commitment, Report, Review, SaveReviewInput } from "./types";

type RequestAuth = Pick<
  AuthService,
  "getAccessToken" | "getSessionGeneration" | "handleUnauthorized"
>;

export interface HttpServiceOptions {
  baseUrl?: string;
  fetcher?: typeof fetch;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(`${status ? `${status}: ` : ""}${detail}`);
    this.name = "ApiError";
  }
}

const configuredBaseUrl = import.meta.env["VITE_API_BASE_URL"] || "/api";

function joinUrl(baseUrl: string, path: string): string {
  return `${baseUrl.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;
}

function safeDetail(body: unknown): string | null {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = body.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  return null;
}

export function createHttpService(
  auth: RequestAuth,
  { baseUrl = configuredBaseUrl, fetcher }: HttpServiceOptions = {},
): GrowthService {
  const sendRequest = fetcher ?? ((...args: Parameters<typeof fetch>) => fetch(...args));

  const request = async <T>(
    path: string,
    { method = "GET", body }: { method?: string; body?: unknown } = {},
  ): Promise<T> => {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    const token = auth.getAccessToken();
    const sessionGeneration = auth.getSessionGeneration();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    let response: Response;
    try {
      response = await sendRequest(joinUrl(baseUrl, path), {
        method,
        headers,
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
    } catch {
      throw new ApiError(
        0,
        "Unable to reach the journal service. Check your connection and try again.",
      );
    }

    const isCurrentSession = () => auth.getSessionGeneration() === sessionGeneration;
    if (!isCurrentSession()) {
      throw new ApiError(
        0,
        "The session changed while the request was in progress. Please try again.",
      );
    }

    if (response.status === 401) auth.handleUnauthorized(sessionGeneration);
    if (!response.ok) {
      let detail: string | null = null;
      try {
        detail = safeDetail(await response.json());
      } catch {
        // Keep the HTTP status even when the server returns an empty or invalid body.
      }
      throw new ApiError(
        response.status,
        detail ?? `The request failed (HTTP ${response.status}).`,
      );
    }

    if (response.status === 204) return undefined as T;
    let result: T;
    try {
      result = (await response.json()) as T;
    } catch {
      throw new ApiError(response.status, "The journal service returned an invalid response.");
    }
    if (!isCurrentSession()) {
      throw new ApiError(
        0,
        "The session changed while the request was in progress. Please try again.",
      );
    }
    return result;
  };

  return {
    listReviews: () => request<Review[]>("reviews"),
    getReview: (id) => request<Review | null>(`reviews/${encodeURIComponent(id)}`),
    getReviewForWeek: (weekStart) =>
      request<Review | null>(`reviews/by-week/${encodeURIComponent(weekStart)}`),
    saveReview: (input: SaveReviewInput) =>
      request<Review>("reviews", { method: "POST", body: input }),
    deleteReview: async (id) => {
      await request<void>(`reviews/${encodeURIComponent(id)}`, { method: "DELETE" });
    },
    suggestFollowUps: (input: SaveReviewInput) =>
      request<string[]>("reviews/suggest-follow-ups", { method: "POST", body: input }),
    completeReviewWithoutFeedback: (id) =>
      request<Review>(
        `reviews/${encodeURIComponent(id)}/complete-without-feedback`,
        { method: "POST" },
      ),
    completeReview: (id) =>
      request<Report>(`reviews/${encodeURIComponent(id)}/complete`, { method: "POST" }),
    getReport: (reviewId) =>
      request<Report | null>(`reviews/${encodeURIComponent(reviewId)}/report`),
    updateInsight: (reviewId, section, insightId, patch) =>
      request<Report>(
        `reviews/${encodeURIComponent(reviewId)}/report/${encodeURIComponent(section)}/insights/${encodeURIComponent(insightId)}`,
        { method: "PATCH", body: patch },
      ),
    setCommitment: (reviewId, input) =>
      request<Commitment>(`reviews/${encodeURIComponent(reviewId)}/commitment`, {
        method: "PUT",
        body: input,
      }),
    getCommitment: (reviewId) =>
      request<Commitment | null>(`reviews/${encodeURIComponent(reviewId)}/commitment`),
    getCommitmentBefore: (weekStart) => {
      const query = new URLSearchParams({ weekStart });
      return request<Commitment | null>(`commitments/before?${query.toString()}`);
    },
    deleteAllData: async () => {
      await request<void>("data", { method: "DELETE" });
    },
  };
}

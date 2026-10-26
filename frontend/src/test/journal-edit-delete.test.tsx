import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DraftDeleteButton } from "@/routes/history";
import { ReviewEditor } from "@/routes/review";
import { Toaster } from "@/components/ui/sonner";
import { qk } from "@/services/queries";
import { services, type Commitment, type Review, type SaveReviewInput } from "@/services";

const WEEK = "2025-01-06";

const reviewFor = (status: Review["status"] = "draft"): Review => ({
  id: "rev-existing",
  weekStart: WEEK,
  answers: {
    wentWell: "A useful start",
    didntGoWell: "I waited too long",
    handledBetter: "I could ask sooner",
    learned: "Planning helps",
    doDifferently: "Ask on Monday",
  },
  freeWriting: "A saved thought",
  followUps: [{ question: "What helped?", answer: "A short plan" }],
  previousAction: {
    commitmentId: "com-prior",
    attempted: "partly",
    whatHappened: "I tried once",
    learned: "Start small",
  },
  status,
  createdAt: "2025-01-13T10:00:00Z",
  updatedAt: "2025-01-13T10:00:00Z",
});

const priorCommitment: Commitment = {
  id: "com-prior",
  reviewId: "rev-previous",
  weekStart: "2024-12-30",
  text: "Ask one question early",
  measure: "At Monday check-in",
  createdAt: "2025-01-06T10:00:00Z",
};

function clientWrapper(queryClient = new QueryClient()) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster />
    </QueryClientProvider>
  );
}

function mockReviews(initialReviews: Review[]) {
  let reviews = initialReviews.map((review) => ({ ...review }));
  const saveReview = vi
    .spyOn(services, "saveReview")
    .mockImplementation(async (input: SaveReviewInput) => {
      const existing = reviews.find(
        (review) => (input.id && review.id === input.id) || review.weekStart === input.weekStart,
      );
      if (existing) {
        const updated = {
          ...existing,
          ...input,
          id: existing.id,
          updatedAt: "2025-01-14T10:00:00Z",
        };
        reviews = reviews.map((review) => (review.id === existing.id ? updated : review));
        return updated;
      }
      const created = { ...reviewFor(), ...input, id: `rev-created-${reviews.length}` };
      reviews = [...reviews, created];
      return created;
    });
  const listReviews = vi
    .spyOn(services, "listReviews")
    .mockImplementation(async () => [...reviews]);
  const getReviewForWeek = vi
    .spyOn(services, "getReviewForWeek")
    .mockImplementation(
      async (weekStart) => reviews.find((review) => review.weekStart === weekStart) ?? null,
    );
  const deleteReview = vi.spyOn(services, "deleteReview").mockImplementation(async (id) => {
    reviews = reviews.filter((review) => review.id !== id);
  });
  return { saveReview, listReviews, getReviewForWeek, deleteReview, reviews: () => reviews };
}

describe("journal edit and deletion flows", () => {
  beforeEach(() => {
    act(() => services.auth.signOut());
    vi.stubGlobal(
      "confirm",
      vi.fn(() => true),
    );
  });

  afterEach(() => {
    act(() => services.auth.signOut());
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("updates the selected review ID and week without creating a duplicate", async () => {
    const state = mockReviews([reviewFor()]);
    const queryClient = new QueryClient();
    render(
      <ReviewEditor
        week={WEEK}
        existing={reviewFor()}
        previousCommitment={priorCommitment}
        onCompleted={vi.fn()}
      />,
      { wrapper: clientWrapper(queryClient) },
    );

    expect(screen.getByLabelText("1. What went well this week?")).toHaveValue("A useful start");
    expect(screen.getByLabelText("Anything else on your mind? (free writing)")).toHaveValue(
      "A saved thought",
    );
    expect(screen.getByLabelText("What happened?")).toHaveValue("I tried once");
    expect(screen.getByLabelText("What did you learn from it?")).toHaveValue("Start small");

    fireEvent.change(screen.getByLabelText("4. What did I learn about myself?"), {
      target: { value: "Planning helps me begin sooner" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));

    expect(await screen.findByText("Draft saved")).toBeInTheDocument();
    expect(state.saveReview).toHaveBeenCalledWith(
      expect.objectContaining({ id: "rev-existing", weekStart: WEEK }),
    );
    const reopened = await services.getReviewForWeek(WEEK);
    const listed = await services.listReviews();
    expect(reopened?.answers.learned).toBe("Planning helps me begin sooner");
    expect(reopened?.followUps).toEqual([{ question: "What helped?", answer: "A short plan" }]);
    expect(listed).toHaveLength(1);
    expect(state.reviews()).toHaveLength(1);
  });

  it("confirms draft deletion, retains it after failure, and removes its cached history entry on success", async () => {
    const saved = reviewFor();
    const state = mockReviews([saved]);
    const queryClient = new QueryClient();
    queryClient.setQueryData(qk.reviews, [saved]);
    state.deleteReview.mockRejectedValueOnce(new Error("private backend error"));
    render(<DraftDeleteButton review={saved} />, { wrapper: clientWrapper(queryClient) });

    fireEvent.click(screen.getByRole("button", { name: /Delete draft/ }));
    expect(confirm).toHaveBeenCalled();
    expect(
      await screen.findByText("This draft couldn't be deleted. Please try again."),
    ).toBeInTheDocument();
    expect(state.reviews()).toHaveLength(1);
    expect(queryClient.getQueryData(qk.reviews)).toEqual([saved]);

    fireEvent.click(screen.getByRole("button", { name: /Delete draft/ }));
    expect(await screen.findByText("Draft deleted")).toBeInTheDocument();
    expect(state.reviews()).toHaveLength(0);
    expect(queryClient.getQueryData(qk.reviews)).toEqual([]);
  });

  it("saves completed edits or completes a review without AI feedback", async () => {
    const state = mockReviews([reviewFor("completed")]);
    const onCompleted = vi.fn();
    vi.spyOn(services, "completeReviewWithoutFeedback").mockResolvedValue(reviewFor("completed"));
    render(
      <ReviewEditor
        week={WEEK}
        existing={reviewFor("completed")}
        previousCommitment={priorCommitment}
        onCompleted={onCompleted}
      />,
      { wrapper: clientWrapper() },
    );

    expect(screen.getByRole("button", { name: "Complete review" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save changes" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("4. What did I learn about myself?"), {
      target: { value: "Save without refreshing" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("Changes saved")).toBeInTheDocument();
    expect(services.completeReviewWithoutFeedback).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("4. What did I learn about myself?"), {
      target: { value: "Regenerate from the edited reflection" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Complete review" }));
    await waitFor(() => {
      expect(state.saveReview).toHaveBeenLastCalledWith(
        expect.objectContaining({ id: "rev-existing", weekStart: WEEK }),
      );
      expect(services.completeReviewWithoutFeedback).toHaveBeenCalledWith("rev-existing");
      expect(onCompleted).toHaveBeenCalledWith("rev-existing");
    });
  });
});

import type { Commitment, Insight, Report, ReportSection, Review, SaveReviewInput } from "./types";

/**
 * The single contract for every backend call in the app.
 * UI code must only talk to the backend through an implementation of this interface.
 */
export interface GrowthService {
  listReviews(): Promise<Review[]>;
  getReview(id: string): Promise<Review | null>;
  getReviewForWeek(weekStart: string): Promise<Review | null>;
  saveReview(input: SaveReviewInput): Promise<Review>;
  deleteReview(id: string): Promise<void>;

  /** AI: suggest follow-up questions for a draft */
  suggestFollowUps(input: SaveReviewInput): Promise<string[]>;
  /** Marks the review completed and generates (or regenerates) its feedback report */
  completeReview(id: string): Promise<Report>;
  getReport(reviewId: string): Promise<Report | null>;
  updateInsight(
    reviewId: string,
    section: ReportSection,
    insightId: string,
    patch: Partial<Pick<Insight, "status" | "correction">>,
  ): Promise<Report>;

  setCommitment(reviewId: string, input: { text: string; measure: string }): Promise<Commitment>;
  getCommitment(reviewId: string): Promise<Commitment | null>;
  /** Most recent commitment made in a week strictly before `weekStart` */
  getCommitmentBefore(weekStart: string): Promise<Commitment | null>;

  deleteAllData(): Promise<void>;
}

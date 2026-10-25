import { queryOptions } from "@tanstack/react-query";
import { services } from "./index";

export const qk = {
  reviews: ["reviews"] as const,
  review: (id: string) => ["review", id] as const,
  week: (w: string) => ["week", w] as const,
  report: (id: string) => ["report", id] as const,
  commitment: (id: string) => ["commitment", id] as const,
  commitmentBefore: (w: string) => ["commitmentBefore", w] as const,
};

export const reviewsQuery = () =>
  queryOptions({ queryKey: qk.reviews, queryFn: () => services.listReviews() });
export const reviewQuery = (id: string) =>
  queryOptions({ queryKey: qk.review(id), queryFn: () => services.getReview(id) });
export const weekReviewQuery = (w: string) =>
  queryOptions({ queryKey: qk.week(w), queryFn: () => services.getReviewForWeek(w) });
export const reportQuery = (id: string) =>
  queryOptions({ queryKey: qk.report(id), queryFn: () => services.getReport(id) });
export const commitmentQuery = (id: string) =>
  queryOptions({ queryKey: qk.commitment(id), queryFn: () => services.getCommitment(id) });
export const commitmentBeforeQuery = (w: string) =>
  queryOptions({
    queryKey: qk.commitmentBefore(w),
    queryFn: () => services.getCommitmentBefore(w),
  });

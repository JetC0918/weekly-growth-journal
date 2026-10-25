import { describe, expect, it } from "vitest";
import { createMockService } from "./mockService";
import { emptyAnswers, type SaveReviewInput } from "../types";
import { weekStartOf } from "../week";

const input = (weekStart: string, over: Partial<SaveReviewInput["answers"]> = {}): SaveReviewInput => ({
  weekStart,
  answers: { ...emptyAnswers(), ...over },
  freeWriting: "",
  followUps: [],
});

describe("weekStartOf", () => {
  it("returns the Monday of the week", () => {
    expect(weekStartOf(new Date(2026, 9, 25))).toBe("2026-10-19"); // Sunday
    expect(weekStartOf(new Date(2026, 9, 19))).toBe("2026-10-19"); // Monday
  });
});

describe("mock GrowthService", () => {
  it("keeps one review per week (saving again updates it)", async () => {
    const s = createMockService();
    const a = await s.saveReview(input("2026-10-19", { wentWell: "Ran twice." }));
    const b = await s.saveReview(input("2026-10-19", { wentWell: "Ran three times." }));
    expect(b.id).toBe(a.id);
    expect(await s.listReviews()).toHaveLength(1);
  });

  it("completing a review produces a report with evidence from the user's own words", async () => {
    const s = createMockService();
    const r = await s.saveReview(
      input("2026-10-19", { wentWell: "Shipped the release.", doDifferently: "Plan Monday mornings." }),
    );
    const report = await s.completeReview(r.id);
    expect((await s.getReview(r.id))?.status).toBe("completed");
    expect(report.strengths[0].evidence).toBe("Shipped the release.");
    expect(report.proposedAction).toBe("Plan Monday mornings.");
  });

  it("flags recurring themes from previous weeks only as hypotheses", async () => {
    const s = createMockService();
    const old = await s.saveReview(input("2026-10-12", { didntGoWell: "Poor sleep all week." }));
    await s.completeReview(old.id);
    const now = await s.saveReview(input("2026-10-19", { didntGoWell: "Sleep was bad again." }));
    const report = await s.completeReview(now.id);
    const p = report.patterns.find((x) => x.text.includes('"sleep"'));
    expect(p?.kind).toBe("hypothesis");
  });

  it("does not find patterns on the very first review", async () => {
    const s = createMockService();
    const r = await s.saveReview(input("2026-10-19", { didntGoWell: "Sleep was bad." }));
    expect((await s.completeReview(r.id)).patterns).toEqual([]);
  });

  it("lets the user reject or correct an AI insight", async () => {
    const s = createMockService();
    const r = await s.saveReview(input("2026-10-19", { wentWell: "Good talk with Sam." }));
    const rep = await s.completeReview(r.id);
    const id = rep.strengths[0].id;
    await s.updateInsight(r.id, "strengths", id, { status: "rejected" });
    const after = await s.updateInsight(r.id, "strengths", id, { correction: "It was with Alex." });
    expect(after.strengths[0]).toMatchObject({ status: "rejected", correction: "It was with Alex." });
  });

  it("keeps a single primary commitment per review and surfaces it the next week", async () => {
    const s = createMockService();
    const r = await s.saveReview(input("2026-10-12"));
    await s.setCommitment(r.id, { text: "Walk daily", measure: "" });
    await s.setCommitment(r.id, { text: "Walk 5 days", measure: "Count walks" });
    expect((await s.getCommitmentBefore("2026-10-19"))?.text).toBe("Walk 5 days");
    expect(await s.getCommitmentBefore("2026-10-12")).toBeNull();
  });

  it("rejects an empty commitment", async () => {
    const s = createMockService();
    const r = await s.saveReview(input("2026-10-12"));
    await expect(s.setCommitment(r.id, { text: "  ", measure: "" })).rejects.toThrow();
  });

  it("deleting a review removes its report and commitment; delete all wipes everything", async () => {
    const s = createMockService();
    const r = await s.saveReview(input("2026-10-12", { wentWell: "Fine." }));
    await s.completeReview(r.id);
    await s.setCommitment(r.id, { text: "X", measure: "" });
    await s.deleteReview(r.id);
    expect(await s.getReport(r.id)).toBeNull();
    expect(await s.getCommitment(r.id)).toBeNull();
    await s.saveReview(input("2026-10-19"));
    await s.deleteAllData();
    expect(await s.listReviews()).toEqual([]);
  });

  it("suggests at most three follow-up questions", async () => {
    const s = createMockService();
    const qs = await s.suggestFollowUps(input("2026-10-19", { didntGoWell: "Missed deadlines." }));
    expect(qs.length).toBeGreaterThan(0);
    expect(qs.length).toBeLessThanOrEqual(3);
    expect(qs[0]).toContain("Missed deadlines.");
  });
});

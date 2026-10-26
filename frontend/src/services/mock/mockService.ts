import type { GrowthService } from "../api";
import type { Commitment, Report, Review } from "../types";
import { generateReport, suggestFollowUps } from "./ai";

export interface KeyValueStore {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export function memoryStore(): KeyValueStore {
  const m = new Map<string, string>();
  return {
    getItem: (k) => m.get(k) ?? null,
    setItem: (k, v) => void m.set(k, v),
    removeItem: (k) => void m.delete(k),
  };
}

interface DB {
  reviews: Review[];
  reports: Report[];
  commitments: Commitment[];
}

const KEY = "growth-tool:v1";
let n = 0;
const uid = (p: string) => `${p}_${Date.now().toString(36)}_${(n++).toString(36)}`;

export function createMockService(
  store: KeyValueStore = memoryStore(),
  opts: { latencyMs?: number } = {},
): GrowthService {
  const wait = () =>
    opts.latencyMs ? new Promise((r) => setTimeout(r, opts.latencyMs)) : Promise.resolve();
  const load = (): DB => {
    const raw = store.getItem(KEY);
    return raw ? (JSON.parse(raw) as DB) : { reviews: [], reports: [], commitments: [] };
  };
  const save = (db: DB) => store.setItem(KEY, JSON.stringify(db));
  const clone = <T>(x: T): T => structuredClone(x);
  const byWeekDesc = (a: Review, b: Review) => b.weekStart.localeCompare(a.weekStart);

  return {
    async listReviews() {
      await wait();
      return clone(load().reviews.sort(byWeekDesc));
    },
    async getReview(id) {
      await wait();
      return clone(load().reviews.find((r) => r.id === id) ?? null);
    },
    async getReviewForWeek(weekStart) {
      await wait();
      return clone(load().reviews.find((r) => r.weekStart === weekStart) ?? null);
    },
    async saveReview(input) {
      await wait();
      const db = load();
      const now = new Date().toISOString();
      const existing =
        db.reviews.find((r) => r.id === input.id) ??
        db.reviews.find((r) => r.weekStart === input.weekStart);
      if (existing) {
        Object.assign(existing, { ...input, id: existing.id, updatedAt: now });
        save(db);
        return clone(existing);
      }
      const r: Review = {
        ...input,
        id: uid("rev"),
        status: "draft",
        createdAt: now,
        updatedAt: now,
      };
      db.reviews.push(r);
      save(db);
      return clone(r);
    },
    async deleteReview(id) {
      await wait();
      const db = load();
      db.reviews = db.reviews.filter((r) => r.id !== id);
      db.reports = db.reports.filter((r) => r.reviewId !== id);
      db.commitments = db.commitments.filter((c) => c.reviewId !== id);
      save(db);
    },
    async suggestFollowUps(input) {
      await wait();
      return suggestFollowUps(input);
    },
    async completeReview(id) {
      await wait();
      const db = load();
      const review = db.reviews.find((r) => r.id === id);
      if (!review) throw new Error("Review not found");
      review.status = "completed";
      review.updatedAt = new Date().toISOString();
      const history = db.reviews.filter((r) => r.weekStart < review.weekStart);
      const report = generateReport(review, history);
      db.reports = db.reports.filter((r) => r.reviewId !== id).concat(report);
      save(db);
      return clone(report);
    },
    async getReport(reviewId) {
      await wait();
      return clone(load().reports.find((r) => r.reviewId === reviewId) ?? null);
    },
    async updateInsight(reviewId, section, insightId, patch) {
      await wait();
      const db = load();
      const report = db.reports.find((r) => r.reviewId === reviewId);
      const ins = report?.[section].find((i) => i.id === insightId);
      if (!report || !ins) throw new Error("Insight not found");
      Object.assign(ins, patch);
      save(db);
      return clone(report);
    },
    async setCommitment(reviewId, { text, measure }) {
      await wait();
      if (!text.trim()) throw new Error("Commitment cannot be empty");
      const db = load();
      const review = db.reviews.find((r) => r.id === reviewId);
      if (!review) throw new Error("Review not found");
      const existing = db.commitments.find((c) => c.reviewId === reviewId);
      if (existing) {
        Object.assign(existing, { text: text.trim(), measure: measure.trim() });
        save(db);
        return clone(existing);
      }
      const c: Commitment = {
        id: uid("com"),
        reviewId,
        weekStart: review.weekStart,
        text: text.trim(),
        measure: measure.trim(),
        createdAt: new Date().toISOString(),
      };
      db.commitments.push(c);
      save(db);
      return clone(c);
    },
    async getCommitment(reviewId) {
      await wait();
      return clone(load().commitments.find((c) => c.reviewId === reviewId) ?? null);
    },
    async getCommitmentBefore(weekStart) {
      await wait();
      const list = load()
        .commitments.filter((c) => c.weekStart < weekStart)
        .sort((a, b) => b.weekStart.localeCompare(a.weekStart));
      return clone(list[0] ?? null);
    },
    async deleteAllData() {
      await wait();
      store.removeItem(KEY);
    },
  };
}

import type { GrowthService } from "../api";
import { emptyAnswers, type Review } from "../types";
import {
  createMockService,
  memoryStore,
  MOCK_SERVICE_STORAGE_KEY,
  type KeyValueStore,
} from "./mockService";

const DEMO_PREFIX = "weekly-growth-journal:demo:";

function demoStore(): KeyValueStore {
  const fallback = memoryStore();
  const browserStorage = () =>
    typeof window === "undefined" ? null : window.localStorage;

  return {
    getItem(key) {
      try {
        return browserStorage()?.getItem(`${DEMO_PREFIX}${key}`) ?? fallback.getItem(key);
      } catch {
        return fallback.getItem(key);
      }
    },
    setItem(key, value) {
      try {
        const storage = browserStorage();
        if (storage) {
          storage.setItem(`${DEMO_PREFIX}${key}`, value);
          return;
        }
      } catch {
        // Keep the demo usable in private browsing modes that block storage.
      }
      fallback.setItem(key, value);
    },
    removeItem(key) {
      try {
        browserStorage()?.removeItem(`${DEMO_PREFIX}${key}`);
      } catch {
        // The in-memory fallback is still cleared below.
      }
      fallback.removeItem(key);
    },
  };
}

function weekStartWeeksAgo(weeksAgo: number): string {
  const date = new Date();
  date.setHours(12, 0, 0, 0);
  const daysSinceMonday = (date.getDay() + 6) % 7;
  date.setDate(date.getDate() - daysSinceMonday - weeksAgo * 7);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function sampleReviews(): Review[] {
  const createdAt = new Date().toISOString();
  return [
    {
      id: "demo-review-three-weeks-ago",
      weekStart: weekStartWeeksAgo(3),
      answers: {
        ...emptyAnswers(),
        wentWell: "I planned two short study sessions and finished both.",
        didntGoWell: "I postponed the first session until late evening and felt tired.",
        handledBetter: "I waited until I felt completely ready instead of starting small.",
        learned: "Starting with ten minutes helped me build momentum.",
        doDifferently: "Study for ten minutes at 9:00 on Monday, Wednesday, and Friday.",
      },
      freeWriting: "A smaller plan felt easier to begin than an ambitious one.",
      followUps: [{ question: "What helped you start?", answer: "I put my notes on the desk." }],
      status: "draft",
      createdAt,
      updatedAt: createdAt,
    },
    {
      id: "demo-review-two-weeks-ago",
      weekStart: weekStartWeeksAgo(2),
      answers: {
        ...emptyAnswers(),
        wentWell: "I started studying before dinner and kept the sessions short.",
        didntGoWell: "I missed one session when a meeting ran late.",
        handledBetter: "I treated one missed session as a reason to abandon the whole plan.",
        learned: "Returning to a routine matters more than completing every planned session.",
        doDifferently: "Move a missed study session to the next open evening.",
      },
      freeWriting: "The plan worked best when it could bend around a busy day.",
      followUps: [],
      previousAction: {
        commitmentId: "demo-commitment-three-weeks-ago",
        attempted: "yes",
        whatHappened: "I completed two short sessions and started more easily.",
        learned: "A clear start time helped.",
      },
      status: "draft",
      createdAt,
      updatedAt: createdAt,
    },
    {
      id: "demo-review-last-week",
      weekStart: weekStartWeeksAgo(1),
      answers: {
        ...emptyAnswers(),
        wentWell: "I moved a missed session instead of giving up on the week.",
        didntGoWell: "I still waited until late on two evenings.",
        handledBetter: "I made the next step harder by leaving my notes packed away.",
        learned: "Visible reminders make it easier to return to a habit.",
        doDifferently: "Put my notes on the desk before finishing work on Monday.",
      },
      freeWriting: "I want the routine to feel forgiving and easy to restart.",
      followUps: [],
      previousAction: {
        commitmentId: "demo-commitment-two-weeks-ago",
        attempted: "partly",
        whatHappened: "I moved one session but did not make up the other.",
        learned: "I need a specific backup time.",
      },
      status: "draft",
      createdAt,
      updatedAt: createdAt,
    },
  ];
}

function createSeededDemoService(): GrowthService {
  const store = demoStore();
  const service = createMockService(store);
  let initialization: Promise<void> | null = null;

  const ensureSeeded = () => {
    if (store.getItem("initialized") === "true") return Promise.resolve();
    if (initialization) return initialization;

    initialization = (async () => {
      const reviews = sampleReviews();
      const commitments = [
        {
          id: "demo-commitment-three-weeks-ago",
          reviewId: reviews[0].id,
          weekStart: reviews[0].weekStart,
          text: "Study for ten minutes before dinner.",
          measure: "Three short sessions",
          createdAt: reviews[0].createdAt,
        },
        {
          id: "demo-commitment-two-weeks-ago",
          reviewId: reviews[1].id,
          weekStart: reviews[1].weekStart,
          text: "Move a missed session to the next open evening.",
          measure: "Write down the backup time",
          createdAt: reviews[1].createdAt,
        },
        {
          id: "demo-commitment-last-week",
          reviewId: reviews[2].id,
          weekStart: reviews[2].weekStart,
          text: "Put my notes on the desk before finishing work.",
          measure: "Ready before Monday evening",
          createdAt: reviews[2].createdAt,
        },
      ];
      store.setItem(
        MOCK_SERVICE_STORAGE_KEY,
        JSON.stringify({ reviews, reports: [], commitments }),
      );

      for (const review of reviews) await service.completeReview(review.id);

      store.setItem("initialized", "true");
    })().finally(() => {
      initialization = null;
    });
    return initialization;
  };

  return new Proxy(service, {
    get(target, property, receiver) {
      const value = Reflect.get(target, property, receiver) as unknown;
      if (typeof value !== "function") return value;
      return async (...args: unknown[]) => {
        await ensureSeeded();
        return value.apply(target, args);
      };
    },
  }) as GrowthService;
}

export const demoService = createSeededDemoService();

import type { GrowthService } from "./api";
import { createMockService, memoryStore } from "./mock/mockService";

/**
 * The app-wide service instance. Swap the mock for a real implementation
 * of GrowthService here — nothing else in the UI needs to change.
 */
export const services: GrowthService = createMockService(
  typeof window !== "undefined" ? window.localStorage : memoryStore(),
  { latencyMs: 150 },
);

export type { GrowthService } from "./api";
export * from "./types";
export * from "./week";

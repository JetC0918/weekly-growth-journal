import type { GrowthService } from "./api";
import { createAuthService, type AuthService } from "./auth";
import { createHttpService } from "./httpService";

const auth = createAuthService();

/** The app-wide API client; all journal requests share the volatile auth session. */
export const services: GrowthService & { auth: AuthService } = Object.assign(
  createHttpService(auth),
  { auth },
);

export type { GrowthService } from "./api";
export { ApiError, createHttpService } from "./httpService";
export type { HttpServiceOptions } from "./httpService";
export { AuthRequestError, SESSION_LIFETIME_MS } from "./auth";
export type { AuthCredentials, AuthService, AccountSessionSnapshot } from "./auth";
export * from "./types";
export * from "./week";

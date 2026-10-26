import type { GrowthService } from "./api";
import { createAuthService, type AuthService } from "./auth";
import { createHttpService } from "./httpService";
import { demoService } from "./mock/demoService";

const auth = createAuthService();
const httpService = createHttpService(auth);

/** The app-wide API client; all journal requests share the volatile auth session. */
const serviceRouter = new Proxy(httpService, {
  get(target, property, receiver) {
    if (property === "auth") return auth;
    const source = auth.isDemo() ? demoService : target;
    return Reflect.get(source, property, source ?? receiver);
  },
});

export const services = Object.assign(serviceRouter, { auth }) as GrowthService & {
  auth: AuthService;
};

export type { GrowthService } from "./api";
export { ApiError, createHttpService } from "./httpService";
export type { HttpServiceOptions } from "./httpService";
export { AuthRequestError, SESSION_LIFETIME_MS } from "./auth";
export type { AuthCredentials, AuthService, AccountSessionSnapshot } from "./auth";
export * from "./types";
export * from "./week";

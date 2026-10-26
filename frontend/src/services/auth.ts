export const SESSION_LIFETIME_MS = 24 * 60 * 60 * 1000;

export interface AuthCredentials {
  username: string;
  password: string;
}

export interface AccountSessionSnapshot {
  isAuthenticated: boolean;
  username: string | null;
  expiresAt: number | null;
  notice: string | null;
}

export class AuthRequestError extends Error {
  constructor(readonly status: number) {
    super(`Authentication request failed with status ${status}`);
    this.name = "AuthRequestError";
  }
}

export interface AuthService {
  register(credentials: AuthCredentials): Promise<AccountSessionSnapshot>;
  login(credentials: AuthCredentials): Promise<AccountSessionSnapshot>;
  enterDemo(): AccountSessionSnapshot;
  isDemo(): boolean;
  signOut(): void;
  getSnapshot(): AccountSessionSnapshot;
  refreshSession(): void;
  subscribe(listener: () => void): () => void;
  getAccessToken(): string | null;
  getSessionGeneration(): number;
  handleUnauthorized(expectedGeneration?: number): void;
}

interface AuthResponse {
  accessToken: string;
  tokenType: string;
}

interface AuthServiceOptions {
  baseUrl?: string;
  fetcher?: typeof fetch;
  now?: () => number;
}

const configuredBaseUrl = import.meta.env["VITE_API_BASE_URL"] || "/api";

const signedOutSnapshot = (): AccountSessionSnapshot => ({
  isAuthenticated: false,
  username: null,
  expiresAt: null,
  notice: null,
});

export function createAuthService({
  baseUrl = configuredBaseUrl,
  fetcher,
  now = Date.now,
}: AuthServiceOptions = {}): AuthService {
  const sendRequest = fetcher ?? ((...args: Parameters<typeof fetch>) => fetch(...args));
  const authUrl = (path: string) => `${baseUrl.replace(/\/+$/, "")}/auth/${path}`;
  let snapshot = signedOutSnapshot();
  let accessToken: string | null = null;
  let demoSession = false;
  let sessionGeneration = 0;
  let expiryTimer: ReturnType<typeof setTimeout> | undefined;
  const listeners = new Set<() => void>();

  const publish = (next: AccountSessionSnapshot) => {
    snapshot = next;
    listeners.forEach((listener) => listener());
  };

  const clearTimer = () => {
    if (expiryTimer !== undefined) {
      clearTimeout(expiryTimer);
      expiryTimer = undefined;
    }
  };

  const expireSession = () => {
    sessionGeneration += 1;
    clearTimer();
    accessToken = null;
    demoSession = false;
    publish({
      isAuthenticated: false,
      username: null,
      expiresAt: null,
      notice: "Your session expired. Sign in again to continue.",
    });
  };

  const expireIfNeeded = () => {
    if (snapshot.isAuthenticated && snapshot.expiresAt !== null && now() >= snapshot.expiresAt) {
      sessionGeneration += 1;
      clearTimer();
      accessToken = null;
      demoSession = false;
      publish({
        isAuthenticated: false,
        username: null,
        expiresAt: null,
        notice: "Your session expired. Sign in again to continue.",
      });
    }
  };

  const authenticate = async (path: string, credentials: AuthCredentials) => {
    const requestGeneration = ++sessionGeneration;
    const requestStartedAt = now();
    let response: Response;
    try {
      response = await sendRequest(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });
    } catch {
      throw new AuthRequestError(0);
    }
    if (!response.ok) throw new AuthRequestError(response.status);

    let result: AuthResponse;
    try {
      result = (await response.json()) as AuthResponse;
    } catch {
      throw new AuthRequestError(0);
    }
    if (typeof result.accessToken !== "string" || result.tokenType?.toLowerCase() !== "bearer") {
      throw new AuthRequestError(0);
    }

    if (sessionGeneration !== requestGeneration) throw new AuthRequestError(0);

    clearTimer();
    demoSession = false;
    accessToken = result.accessToken;
    const expiresAt = requestStartedAt + SESSION_LIFETIME_MS;
    publish({ isAuthenticated: true, username: credentials.username, expiresAt, notice: null });
    expiryTimer = setTimeout(expireSession, Math.max(0, expiresAt - now()));
    return snapshot;
  };

  return {
    register: (credentials) => authenticate(authUrl("register"), credentials),
    login: (credentials) => authenticate(authUrl("login"), credentials),
    enterDemo: () => {
      sessionGeneration += 1;
      clearTimer();
      accessToken = null;
      demoSession = true;
      const expiresAt = now() + SESSION_LIFETIME_MS;
      publish({ isAuthenticated: true, username: "demo", expiresAt, notice: null });
      expiryTimer = setTimeout(expireSession, Math.max(0, expiresAt - now()));
      return snapshot;
    },
    isDemo: () => demoSession,
    signOut: () => {
      sessionGeneration += 1;
      clearTimer();
      accessToken = null;
      demoSession = false;
      publish(signedOutSnapshot());
    },
    getSnapshot: () => {
      return snapshot;
    },
    refreshSession: () => expireIfNeeded(),
    subscribe: (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    getAccessToken: () => {
      expireIfNeeded();
      return accessToken;
    },
    getSessionGeneration: () => sessionGeneration,
    handleUnauthorized: (expectedGeneration) => {
      if (expectedGeneration !== undefined && expectedGeneration !== sessionGeneration) return;
      expireSession();
    },
  };
}

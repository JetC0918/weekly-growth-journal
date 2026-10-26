import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, useSyncExternalStore } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthRequestError, services } from "@/services";

export const Route = createFileRoute("/account")({
  ssr: false,
  head: () => ({
    meta: [
      { title: "Weekly — Account access" },
      { name: "description", content: "Create an account or sign in to Weekly." },
    ],
  }),
  component: AccountRoute,
});

type AccessMode = "register" | "login";

export function accountErrorMessage(error: unknown, mode: AccessMode): string {
  if (!(error instanceof AuthRequestError)) {
    return "We couldn't connect right now. Please try again.";
  }
  if (error.status === 409) {
    return "That username is already registered. Try signing in instead.";
  }
  if (error.status === 401) {
    return "That username and password don't match. Check them and try again.";
  }
  if (error.status === 422) {
    return mode === "register"
      ? "Enter a username up to 100 characters and a password between 8 and 200 characters."
      : "Check your username and use a password between 8 and 200 characters.";
  }
  return "We couldn't complete that request. Please try again in a moment.";
}

function AccountRoute() {
  const navigate = useNavigate();
  return <AccountScreen onDemoEntered={() => void navigate({ to: "/" })} />;
}

export function AccountScreen({ onDemoEntered }: { onDemoEntered?: () => void } = {}) {
  const session = useSyncExternalStore(
    services.auth.subscribe,
    services.auth.getSnapshot,
    services.auth.getSnapshot,
  );
  const [mode, setMode] = useState<AccessMode>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const refreshSession = () => services.auth.refreshSession();
    window.addEventListener("focus", refreshSession);
    document.addEventListener("visibilitychange", refreshSession);
    return () => {
      window.removeEventListener("focus", refreshSession);
      document.removeEventListener("visibilitychange", refreshSession);
    };
  }, []);

  const isRegistering = mode === "register";
  const title = isRegistering ? "Create your account" : "Sign in";

  return (
    <div className="mx-auto max-w-lg space-y-6 pt-6">
      <div>
        <p className="text-sm uppercase tracking-widest text-muted-foreground">
          Your private space
        </p>
        <h1 className="mt-2 font-serif text-4xl font-semibold">Account access</h1>
      </div>

      {session.notice && (
        <p
          role="status"
          aria-live="polite"
          className="rounded-lg border border-accent/40 bg-secondary px-4 py-3 text-sm"
        >
          {session.notice} You can sign in below.
        </p>
      )}

      {session.isAuthenticated ? (
        <Card>
          <CardHeader>
            <h2 className="font-serif text-2xl font-semibold">You're signed in</h2>
            <CardDescription>
              {services.auth.isDemo()
                ? "You're exploring a browser-local demo account with sample journal history."
                : "Your account is ready for a private reflection session."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p role="status" className="text-sm text-muted-foreground">
              Signed in as <strong className="text-foreground">{session.username}</strong>
            </p>
            <p className="text-sm text-muted-foreground">
              Your session stays in memory while this app is open and expires within 24 hours.
            </p>
            <Button variant="outline" onClick={() => services.auth.signOut()}>
              Sign out
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <h2 className="font-serif text-2xl font-semibold">{title}</h2>
            <CardDescription>
              {isRegistering
                ? "Start a private space for your weekly reflections."
                : "Welcome back. Sign in to your account."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-5"
              onSubmit={async (event) => {
                event.preventDefault();
                setBusy(true);
                setError(null);
                try {
                  const credentials = { username, password };
                  if (isRegistering) await services.auth.register(credentials);
                  else await services.auth.login(credentials);
                } catch (requestError) {
                  setError(accountErrorMessage(requestError, mode));
                } finally {
                  setBusy(false);
                }
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="account-username">Username</Label>
                <Input
                  id="account-username"
                  name="username"
                  autoComplete="username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  maxLength={100}
                  required
                  disabled={busy}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="account-password">Password</Label>
                <Input
                  id="account-password"
                  name="password"
                  type="password"
                  autoComplete={isRegistering ? "new-password" : "current-password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  minLength={8}
                  maxLength={200}
                  required
                  disabled={busy}
                />
                {isRegistering && (
                  <p className="text-xs text-muted-foreground">Use at least 8 characters.</p>
                )}
              </div>

              {error && (
                <p role="alert" aria-live="polite" className="text-sm text-destructive">
                  {error}
                </p>
              )}

              <Button type="submit" className="w-full" disabled={busy}>
                {busy ? "Please wait…" : isRegistering ? "Create account" : "Sign in"}
              </Button>
            </form>

            <div className="mt-5 border-t pt-4 text-center text-sm text-muted-foreground">
              {isRegistering ? "Already have an account?" : "New to Weekly?"}{" "}
              <Button
                type="button"
                variant="link"
                className="h-auto p-0"
                disabled={busy}
                onClick={() => {
                  setMode(isRegistering ? "login" : "register");
                  setError(null);
                }}
              >
                {isRegistering ? "Sign in" : "Create an account"}
              </Button>
            </div>

            {!isRegistering && (
              <div className="mt-5 space-y-3 rounded-lg border bg-secondary/50 p-4">
                <div>
                  <h3 className="font-medium text-foreground">Look around first</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    The demo includes three past reviews and sample feedback. Any changes stay in
                    this browser.
                  </p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    services.auth.enterDemo();
                    onDemoEntered?.();
                  }}
                >
                  Explore the demo account
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

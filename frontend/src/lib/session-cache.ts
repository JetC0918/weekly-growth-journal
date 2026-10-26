import type { QueryClient } from "@tanstack/react-query";
import type { AccountSessionSnapshot } from "@/services";

export function handleSessionTransition(
  queryClient: QueryClient,
  previous: AccountSessionSnapshot,
  current: AccountSessionSnapshot,
  pathname: string,
  navigateToAccount: () => void,
) {
  const identityChanged =
    previous.isAuthenticated !== current.isAuthenticated ||
    previous.username !== current.username ||
    previous.expiresAt !== current.expiresAt;
  if (identityChanged) queryClient.clear();

  if (previous.isAuthenticated && !current.isAuthenticated && pathname !== "/account") {
    navigateToAccount();
  }
}

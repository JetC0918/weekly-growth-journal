import { redirect } from "@tanstack/react-router";
import { services } from "@/services";

export function requireAuthenticated() {
  if (!services.auth.getSnapshot().isAuthenticated) {
    throw redirect({ to: "/account" });
  }
}

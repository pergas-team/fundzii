import type { UserRole } from "@/types/auth";

export function canAccess(role: UserRole | undefined, allowed: UserRole[]) {
  if (!role) return false;
  return allowed.includes(role);
}

export function isAdminRole(role?: UserRole) {
  return role === "admin";
}

export function isOperatorRole(role?: UserRole) {
  return role === "admin" || role === "operator";
}

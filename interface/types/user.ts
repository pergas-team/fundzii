import type { CurrentUser } from "./auth";

export type FundziUser = CurrentUser & {
  is_active?: boolean;
  date_joined?: string;
  groups?: string[];
  requests_count?: number;
};

export type UserRole = "admin" | "operator" | "investor" | "vendor" | "applicant";

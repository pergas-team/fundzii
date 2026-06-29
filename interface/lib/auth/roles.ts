import type { UserRole } from "@/types/auth";

export const roleLabels: Record<UserRole, string> = {
  guest: "مهمان",
  applicant: "متقاضی",
  investor: "سرمایه‌گذار",
  vendor: "همکار مالی",
  operator: "اپراتور",
  admin: "مدیر",
};

export function translateRole(role?: UserRole) {
  return role ? roleLabels[role] : "مهمان";
}

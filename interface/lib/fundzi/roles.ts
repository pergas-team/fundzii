import type { UserRole } from "@/types/user";

export type RoleOption = {
  value: UserRole;
  label: string;
  description: string;
};

export const ROLE_OPTIONS: RoleOption[] = [
  { value: "admin", label: "ادمین", description: "دسترسی کامل به مدیریت سیستم" },
  { value: "operator", label: "اپراتور", description: "بررسی و مدیریت درخواست‌ها" },
  { value: "investor", label: "سرمایه‌گذار", description: "دسترسی به بخش سرمایه‌گذاری" },
  { value: "vendor", label: "همکار / Vendor", description: "همکار تجاری و تأمین‌کننده" },
  { value: "applicant", label: "متقاضی", description: "کاربر عادی متقاضی تأمین مالی" },
];

export function roleLabel(role?: string): string {
  return ROLE_OPTIONS.find((option) => option.value === role)?.label || role || "—";
}

type BadgeVariant = "default" | "success" | "warning" | "info" | "accent" | "destructive" | "outline";

export function roleBadgeVariant(role?: string): BadgeVariant {
  switch (role) {
    case "admin":
      return "accent";
    case "operator":
      return "info";
    case "investor":
      return "success";
    case "vendor":
      return "warning";
    default:
      return "default";
  }
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentType } from "react";
import { BriefcaseBusiness, ClipboardList, Gauge, Landmark, UsersRound } from "lucide-react";
import { cn } from "@/lib/utils";

type Item = {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
};

const adminItems: Item[] = [
  { href: "/admin", label: "داشبورد مدیریتی", icon: Gauge },
  { href: "/admin/requests", label: "درخواست‌ها", icon: ClipboardList },
  { href: "/admin/services", label: "خدمات", icon: Landmark },
  { href: "/admin/users", label: "کاربران", icon: UsersRound },
  { href: "/admin/vendors", label: "وندورها", icon: BriefcaseBusiness },
];

const userItems: Item[] = [
  { href: "/dashboard", label: "داشبورد", icon: Gauge },
  { href: "/services", label: "خدمات تأمین مالی", icon: Landmark },
  { href: "/dashboard/requests", label: "درخواست‌های من", icon: ClipboardList },
];

export function AppSidebar({ mode = "user", className }: { mode?: "user" | "admin" | "operator"; className?: string }) {
  const pathname = usePathname();
  const baseItems =
    mode === "user"
      ? userItems
      : adminItems.filter((item) => mode === "admin" || item.href.includes("requests") || item.href === "/admin");

  const items = baseItems.map((item) => ({
    ...item,
    href: mode === "operator" ? item.href.replace("/admin", "/operator") : item.href,
  }));

  const isActive = (href: string) =>
    pathname === href || (href !== "/admin" && href !== "/operator" && href !== "/dashboard" && pathname.startsWith(`${href}/`));

  return (
    <aside className={cn("rounded-xl border bg-card p-3 shadow-card", className)}>
      <nav className="grid gap-1">
        {items.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {active ? (
                <span className="absolute inset-y-2 right-0 w-1 rounded-full bg-accent" aria-hidden />
              ) : null}
              <span
                className={cn(
                  "grid h-8 w-8 place-items-center rounded-lg transition-colors",
                  active ? "bg-primary/15 text-primary" : "bg-muted text-muted-foreground group-hover:text-foreground",
                )}
              >
                <item.icon className="h-4 w-4" />
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

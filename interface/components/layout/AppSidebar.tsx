"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentType } from "react";
import { BriefcaseBusiness, ClipboardList, Gauge, Landmark, ShieldCheck, UsersRound } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

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

export function AppSidebar({ mode = "user" }: { mode?: "user" | "admin" | "operator" }) {
  const pathname = usePathname();

  const baseItems =
    mode === "user"
      ? userItems
      : adminItems.filter(
          (item) =>
            mode === "admin" || item.href.includes("requests") || item.href === "/admin"
        );

  const items = baseItems.map((item) => ({
    ...item,
    href: mode === "operator" ? item.href.replace("/admin", "/operator") : item.href,
  }));

  const isActive = (href: string) =>
    pathname === href ||
    (href !== "/admin" &&
      href !== "/operator" &&
      href !== "/dashboard" &&
      pathname.startsWith(`${href}/`));

  const groupLabel = mode === "user" ? "منوی کاربری" : mode === "admin" ? "مدیریت" : "اپراتور";

  return (
    <Sidebar side="right" collapsible="icon">
      <SidebarHeader className="border-b px-4 py-3">
        <div className="flex items-center gap-2.5 font-extrabold text-foreground">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-primary text-primary-foreground shadow-soft">
            <ShieldCheck className="h-4 w-4" />
          </span>
          <span className="text-base">فاندزی</span>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>{groupLabel}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => {
                const active = isActive(item.href);
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton asChild isActive={active} tooltip={item.label}>
                      <Link href={item.href}>
                        <item.icon className="h-4 w-4" />
                        <span>{item.label}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}

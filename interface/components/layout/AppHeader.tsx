"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { LogOut, Menu, ShieldCheck, UserRound, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useCurrentUser } from "@/hooks/useCurrentUser";

type NavLink = { href: string; label: string };

export function AppHeader() {
  const { user, logout } = useCurrentUser();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const links: NavLink[] = [
    { href: "/services", label: "خدمات فاندزی" },
    ...(user ? [{ href: "/dashboard", label: "داشبورد" }] : []),
    ...(user?.role === "admin" ? [{ href: "/admin", label: "مدیریت" }] : []),
    ...(user?.role === "operator" || user?.role === "admin"
      ? [{ href: "/operator", label: "اپراتور" }]
      : []),
  ];

  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);
  const initials = (user?.first_name || user?.phone_number || user?.username || "؟").trim().charAt(0);

  return (
    <header className="sticky top-0 z-40 border-b border-border/70 glass">
      <div className="container flex min-h-16 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2.5 font-extrabold text-foreground">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-primary text-primary-foreground shadow-soft">
            <ShieldCheck className="h-5 w-5" />
          </span>
          <span className="text-lg">فاندزی</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive(link.href)
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          {user ? (
            <div className="flex items-center gap-2.5">
              <span className="grid h-9 w-9 place-items-center rounded-full bg-secondary text-sm font-bold text-secondary-foreground">
                {initials}
              </span>
              <span className="hidden text-sm font-medium text-muted-foreground sm:inline-flex">
                {user.phone_number || user.username}
              </span>
              <Button variant="ghost" size="icon" onClick={logout} aria-label="خروج">
                <LogOut className="h-5 w-5" />
              </Button>
            </div>
          ) : (
            <Button asChild size="sm">
              <Link href="/auth/login">
                <UserRound className="h-4 w-4" />
                ورود
              </Link>
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="منو"
            aria-expanded={open}
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {/* Mobile drawer */}
      {open ? (
        <nav className="border-t border-border/70 bg-card animate-fade-in md:hidden">
          <div className="container grid gap-1 py-3">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive(link.href)
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </nav>
      ) : null}
    </header>
  );
}

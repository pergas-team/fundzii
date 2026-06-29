"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import type { UserRole } from "@/types/auth";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export function RoleGuard({ roles, children }: { roles: UserRole[]; children: React.ReactNode }) {
  const router = useRouter();
  const { user, isReady } = useCurrentUser();

  useEffect(() => {
    if (isReady && !user) router.replace("/auth/login");
  }, [isReady, router, user]);

  if (!isReady)
    return (
      <div className="container flex items-center justify-center gap-3 py-20 text-muted-foreground">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-primary/30 border-t-primary" />
        در حال بررسی دسترسی...
      </div>
    );
  if (!user) return null;
  if (!roles.includes(user.role)) {
    return (
      <main className="container py-16">
        <Alert className="mx-auto max-w-lg border-destructive/30 bg-destructive/5">
          <AlertTitle className="text-destructive">دسترسی غیرمجاز</AlertTitle>
          <AlertDescription>شما به این بخش دسترسی ندارید.</AlertDescription>
        </Alert>
      </main>
    );
  }

  return <>{children}</>;
}

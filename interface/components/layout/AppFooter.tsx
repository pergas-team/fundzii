import Link from "next/link";
import { ShieldCheck } from "lucide-react";

export function AppFooter() {
  return (
    <footer className="mt-16 border-t bg-card">
      <div className="container flex flex-col items-center justify-between gap-4 py-8 text-sm text-muted-foreground md:flex-row">
        <Link href="/" className="flex items-center gap-2 font-bold text-foreground">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-primary text-primary-foreground">
            <ShieldCheck className="h-4 w-4" />
          </span>
          فاندزی
        </Link>
        <p className="order-last text-xs md:order-none">
          © {new Date().getFullYear()} فاندزی — هسته عملیاتی خدمات تأمین مالی
        </p>
        <nav className="flex items-center gap-5">
          <Link href="/services" className="transition-colors hover:text-foreground">
            خدمات
          </Link>
          <Link href="/dashboard" className="transition-colors hover:text-foreground">
            داشبورد
          </Link>
        </nav>
      </div>
    </footer>
  );
}

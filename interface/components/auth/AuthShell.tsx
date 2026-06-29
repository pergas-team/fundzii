import { CheckCircle2, ShieldCheck } from "lucide-react";

const points = [
  "ثبت و پیگیری درخواست‌های تأمین مالی",
  "فرم‌های اختصاصی برای هر سرویس",
  "بررسی مرحله‌به‌مرحله توسط کارشناسان",
];

export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="container py-8 md:py-14">
      <div className="mx-auto grid max-w-5xl overflow-hidden rounded-3xl border bg-card shadow-lift md:grid-cols-2">
        {/* Brand panel */}
        <div className="relative hidden flex-col justify-between bg-gradient-hero p-10 text-primary-foreground md:flex">
          <div className="absolute inset-0 bg-dotted opacity-60" aria-hidden />
          <div className="relative">
            <div className="flex items-center gap-2.5 text-lg font-extrabold">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-white/15 backdrop-blur">
                <ShieldCheck className="h-5 w-5" />
              </span>
              فاندزی
            </div>
            <h2 className="mt-10 text-2xl font-extrabold leading-relaxed">
              به پلتفرم خدمات تأمین مالی خوش آمدید
            </h2>
          </div>
          <ul className="relative grid gap-3.5">
            {points.map((point) => (
              <li key={point} className="flex items-center gap-3 text-sm text-primary-foreground/90">
                <CheckCircle2 className="h-5 w-5 shrink-0 text-accent" />
                {point}
              </li>
            ))}
          </ul>
        </div>

        {/* Form panel */}
        <div className="flex items-center justify-center p-6 sm:p-10">
          <div className="w-full max-w-sm animate-slide-up">{children}</div>
        </div>
      </div>
    </main>
  );
}

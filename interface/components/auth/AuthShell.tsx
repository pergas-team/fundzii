import { cn } from "@/lib/utils";
import {
  ClipboardList,
  Landmark,
  ShieldCheck,
  TrendingUp,
  UploadCloud,
  type LucideIcon,
} from "lucide-react";

const features: { icon: LucideIcon; label: string }[] = [
  { icon: Landmark, label: "خدمات تأمین مالی" },
  { icon: ClipboardList, label: "ثبت درخواست" },
  { icon: UploadCloud, label: "بارگذاری مدارک" },
  { icon: TrendingUp, label: "پیگیری وضعیت" },
];

function FeatureCell({ icon: Icon, label }: { icon: LucideIcon; label: string }) {
  return (
    <div className="flex flex-col items-center gap-2.5 rounded-xl border bg-background px-3 py-4 text-center">
      <Icon className="h-7 w-7 text-emerald-500" strokeWidth={1.5} />
      <span className="text-xs font-medium leading-[1.35] text-foreground">{label}</span>
    </div>
  );
}

export function AuthShell({
  children,
  formTitle = "ورود به حساب کاربری",
  formSubtitle = "با شماره موبایل وارد شوید",
}: {
  children: React.ReactNode;
  formTitle?: string;
  formSubtitle?: string;
}) {
  return (
    <main className="container py-8 md:py-10">
      {/* Page header — exact same pattern as services page */}
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-extrabold tracking-tight md:text-3xl">ورود به فاندزی</h1>
        <p className="mt-2 text-sm text-muted-foreground">دسترسی به پلتفرم خدمات تأمین مالی</p>
      </div>

      {/* Two panels — exact same pattern as services page */}
      <div className="mb-5 grid gap-5 md:grid-cols-2">
        {/* Features panel — emerald (like سرمایه‌گذاری panel) */}
        <div className="rounded-2xl border-2 border-emerald-400 bg-card p-6 dark:border-emerald-500">
          <div className="mb-5 text-center">
            <h2 className="text-lg font-bold text-emerald-600 dark:text-emerald-400">امکانات پلتفرم</h2>
            <p className="mt-1 text-xs text-muted-foreground">آنچه پس از ورود در دسترس خواهد بود</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {features.map((f) => (
              <FeatureCell key={f.label} icon={f.icon} label={f.label} />
            ))}
          </div>
        </div>

        {/* Form panel — blue (like تامین مالی panel) */}
        <div className="rounded-2xl border-2 border-blue-400 bg-card p-6 dark:border-blue-500">
          <div className="mb-5 text-center">
            <h2 className="text-lg font-bold text-blue-600 dark:text-blue-400">{formTitle}</h2>
            <p className="mt-1 text-xs text-muted-foreground">{formSubtitle}</p>
          </div>
          <div className="animate-slide-up">{children}</div>
        </div>
      </div>

      {/* Bottom notice — same pattern as vendor tools section */}
      <div className="rounded-2xl border bg-card p-5">
        <div className="flex items-center gap-3">
          <ShieldCheck className="h-5 w-5 shrink-0 text-muted-foreground" strokeWidth={1.5} />
          <span className="text-sm text-muted-foreground">
            ورود امن با کد یکبار مصرف — بدون نیاز به رمز عبور
          </span>
        </div>
      </div>
    </main>
  );
}

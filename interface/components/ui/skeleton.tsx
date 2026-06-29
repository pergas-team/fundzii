import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-lg bg-muted",
        "before:absolute before:inset-0 before:animate-[shimmer_1.6s_infinite] before:bg-gradient-to-l before:from-transparent before:via-card/70 before:to-transparent",
        className,
      )}
    />
  );
}

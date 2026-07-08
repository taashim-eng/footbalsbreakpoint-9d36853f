import { cn } from "@/lib/utils";

export function StatBadge({
  significant,
  className,
}: {
  significant: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-widest",
        significant
          ? "bg-primary/15 text-primary border border-primary/30"
          : "bg-muted/40 text-muted-foreground border border-border",
        className
      )}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          significant ? "bg-primary shadow-[0_0_6px_var(--primary)]" : "bg-muted-foreground"
        )}
      />
      {significant ? "Significant" : "Not Significant"}
    </span>
  );
}

export function LevelDot({ level }: { level: "high" | "moderate" | "normal" }) {
  const color = level === "high" ? "bg-red-500" : level === "moderate" ? "bg-amber-500" : "bg-emerald-500";
  const glow = level === "high" ? "shadow-[0_0_8px_#ef4444]" : level === "moderate" ? "shadow-[0_0_8px_#f59e0b]" : "";
  return <span className={cn("inline-block h-2 w-2 rounded-full", color, glow)} />;
}

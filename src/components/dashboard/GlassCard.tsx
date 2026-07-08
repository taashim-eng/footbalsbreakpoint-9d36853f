import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

export function GlassCard({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <div
      className={cn(
        "glass rounded-2xl p-6 transition-all duration-300",
        "hover:border-primary/40 hover:shadow-[0_0_30px_-10px_var(--primary)]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

import { Link, useRouterState } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

const NAV = [
  { to: "/", label: "Overview" },
  { to: "/historical", label: "Historical Analysis" },
  { to: "/monitor", label: "2026 Monitor" },
  { to: "/betting", label: "Betting Intelligence" },
  { to: "/explorer", label: "Match Explorer" },
  { to: "/methodology", label: "Methodology" },
] as const;

export function SiteHeader() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [light, setLight] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    if (light) root.classList.add("light");
    else root.classList.remove("light");
  }, [light]);

  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 md:px-6">
        <Link to="/" className="flex items-center gap-2 shrink-0">
          <FractureBall />
          <span className="font-display text-lg font-extrabold tracking-tight">
            THE BREAK <span className="text-gradient">POINT</span>
          </span>
        </Link>
        <nav className="hidden md:flex items-center gap-1">
          {NAV.map((item) => {
            const active =
              item.to === "/"
                ? pathname === "/"
                : pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "relative px-3 py-2 text-sm font-medium transition-colors",
                  active ? "text-foreground" : "text-muted-foreground hover:text-foreground"
                )}
              >
                {item.label}
                {active && (
                  <span className="absolute inset-x-2 -bottom-[13px] h-[2px] bg-primary shadow-[0_0_10px_var(--primary)]" />
                )}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-3">
          <span className="hidden lg:inline-flex items-center rounded-full border border-border/60 bg-card/60 px-3 py-1 text-xs text-muted-foreground font-mono-num">
            Last updated: 2026-07-03
          </span>
          <button
            aria-label="Toggle theme"
            onClick={() => setLight((v) => !v)}
            className="rounded-md border border-border/60 bg-card/60 p-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            {light ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </header>
  );
}

function FractureBall() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6 text-primary" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M12 2v6l-4 3 2 5 4-1 3 3"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M12 8l-4 3 2 5 4-1" stroke="#ef4444" strokeWidth="1.2" strokeLinecap="round" strokeDasharray="1 2" />
    </svg>
  );
}

import { cn } from "@/lib/utils";

export function AnomalyGauge({
  score,
  size = 120,
  label,
}: {
  score: number;
  size?: number;
  label?: string;
}) {
  const clamped = Math.max(0, Math.min(100, score));
  const color =
    clamped > 70 ? "#ef4444" : clamped > 45 ? "#f59e0b" : "#10b981";
  const level = clamped > 70 ? "HIGH" : clamped > 45 ? "MODERATE" : "NORMAL";
  const radius = size / 2 - 8;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped / 100);
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(148,163,184,0.15)"
            strokeWidth={8}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={8}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{
              transition: "stroke-dashoffset 1s ease-out",
              filter: `drop-shadow(0 0 6px ${color}80)`,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono-num text-2xl font-bold" style={{ color }}>
            {clamped}
          </span>
          <span className="text-[10px] tracking-widest text-muted-foreground">{level}</span>
        </div>
      </div>
      {label && <div className={cn("text-xs text-muted-foreground")}>{label}</div>}
    </div>
  );
}

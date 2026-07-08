import { animate, useInView, useMotionValue, useTransform } from "framer-motion";
import { useEffect, useRef } from "react";

export function AnimatedCounter({
  value,
  duration = 1.6,
  suffix = "",
  className = "",
  decimals = 0,
}: {
  value: number;
  duration?: number;
  suffix?: string;
  className?: string;
  decimals?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const mv = useMotionValue(0);
  const rounded = useTransform(mv, (v) =>
    v.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  );

  useEffect(() => {
    if (!inView) return;
    const controls = animate(mv, value, { duration, ease: "easeOut" });
    return controls.stop;
  }, [inView, value, duration, mv]);

  useEffect(() => {
    return rounded.on("change", (v) => {
      if (ref.current) ref.current.textContent = `${v}${suffix}`;
    });
  }, [rounded, suffix]);

  return <span ref={ref} className={className}>0{suffix}</span>;
}

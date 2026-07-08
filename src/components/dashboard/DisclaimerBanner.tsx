import { useEffect, useState } from "react";
import { AlertTriangle, X } from "lucide-react";

export function DisclaimerBanner() {
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (sessionStorage.getItem("bp-disclaimer-dismissed") === "1") setVisible(false);
  }, []);
  if (!visible) return null;
  return (
    <div className="border-b border-amber-500/40 bg-amber-500/10 text-amber-100">
      <div className="mx-auto flex max-w-7xl items-start gap-3 px-4 py-2 md:px-6">
        <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-400" />
        <p className="flex-1 text-xs md:text-sm leading-relaxed">
          This dashboard presents statistical analysis for research and educational purposes.
          Anomaly indicators measure statistical deviation from expected patterns and are not evidence of wrongdoing.
          Unusual patterns may have legitimate explanations.
        </p>
        <button
          onClick={() => {
            sessionStorage.setItem("bp-disclaimer-dismissed", "1");
            setVisible(false);
          }}
          className="shrink-0 rounded p-1 text-amber-200 hover:text-white hover:bg-amber-500/20"
          aria-label="Dismiss"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

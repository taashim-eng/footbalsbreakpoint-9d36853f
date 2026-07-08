import { Link } from "@tanstack/react-router";

export function SiteFooter() {
  return (
    <footer className="border-t border-border/60 bg-card/30 mt-16">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 md:px-6 md:grid-cols-3">
        <div>
          <div className="font-display text-lg font-bold">THE BREAK POINT</div>
          <p className="mt-2 text-xs text-muted-foreground max-w-xs">
            Following the data. Following the money. An open, pre-registered investigation into FIFA World Cup hydration break anomalies.
          </p>
        </div>
        <div>
          <div className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Data Sources</div>
          <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
            <li>Fjelstul World Cup Database</li>
            <li>StatsBomb Open Data</li>
            <li>World Bank WDI</li>
            <li>FIFA Rankings</li>
          </ul>
        </div>
        <div className="text-xs text-muted-foreground">
          <div className="font-semibold uppercase tracking-widest">Meta</div>
          <ul className="mt-3 space-y-1">
            <li><Link to="/methodology" className="hover:text-foreground">Methodology</Link></li>
            <li className="font-mono-num">v0.4.1 · updated 2026-07-03</li>
          </ul>
        </div>
      </div>
    </footer>
  );
}

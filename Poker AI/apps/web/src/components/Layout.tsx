import { NavLink, Outlet } from "react-router-dom";
import { getCachedHealthResult } from "../hooks/useHealthCheck";
import { MAIN_NAV_LINKS } from "../lib/navLinks";
import ComplianceFooter from "./ComplianceFooter";
import SetupNavBadge from "./SetupNavBadge";
import StatusNavDot from "./StatusNavDot";

const links = MAIN_NAV_LINKS;

/** Small status dot in the header linking to /health. */
function HealthDot() {
  const cached = getCachedHealthResult();
  // No cache = never checked (grey)
  // all_passed = green
  // has_warnings = amber
  const color = !cached
    ? "bg-slate-600"
    : cached.all_passed
      ? "bg-emerald-500"
      : "bg-amber-400";
  const title = !cached
    ? "System not checked — click to run health check"
    : cached.all_passed
      ? "All systems OK"
      : "System warnings — click to view";

  return (
    <NavLink
      to="/health"
      title={title}
      className="flex items-center gap-1.5 ml-auto text-xs text-slate-500 hover:text-slate-300 transition-colors"
    >
      <span className={`inline-block h-2 w-2 rounded-full ${color}`} />
      <span className="hidden sm:inline">System</span>
    </NavLink>
  );
}

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-700 bg-slate-900/80 px-4 py-3">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center gap-4">
          <h1 className="text-lg font-semibold text-emerald-400">Poker AI</h1>
          <nav className="flex flex-wrap gap-2 text-sm items-center">
            <StatusNavDot />
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) =>
                  `px-3 py-1 rounded-md inline-flex items-center ${isActive ? "bg-emerald-700 text-white" : "text-slate-300 hover:bg-slate-800"}`
                }
                end={l.end ?? l.to === "/"}
              >
                {l.label}
                {"badge" in l && l.badge ? <SetupNavBadge /> : null}
              </NavLink>
            ))}
          </nav>
          <HealthDot />
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto p-4">
        <Outlet />
      </main>
      <ComplianceFooter />
    </div>
  );
}

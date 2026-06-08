import { NavLink } from "react-router-dom";
import { useSystemStatus } from "../hooks/useSystemStatus";
import {
  computeReadiness,
  readinessDotClass,
  readinessTitle,
} from "../lib/systemReadiness";

/** Nav link to /status with green / amber / red readiness dot. */
export default function StatusNavDot() {
  const { data } = useSystemStatus({ pollMs: 45_000 });
  const level = computeReadiness(data);
  const color = readinessDotClass(level);
  const title = readinessTitle(level);

  return (
    <NavLink
      to="/status"
      title={title}
      className={({ isActive }) =>
        `flex items-center gap-1.5 px-3 py-1 rounded-md text-sm transition-colors ${
          isActive
            ? "bg-emerald-700 text-white"
            : "text-slate-300 hover:bg-slate-800"
        }`
      }
    >
      <span className={`inline-block h-2 w-2 rounded-full shrink-0 ${color}`} />
      <span className="hidden sm:inline">Status</span>
    </NavLink>
  );
}

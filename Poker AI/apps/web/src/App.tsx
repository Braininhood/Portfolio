import { lazy, Suspense, useEffect } from "react";
import { Route, Routes, useNavigate } from "react-router-dom";
import Layout from "./components/Layout";
import { getCachedHealthResult } from "./hooks/useHealthCheck";

const BlueprintPage = lazy(() => import("./pages/BlueprintPage"));
const DriftPage = lazy(() => import("./pages/DriftPage"));
const ModelsPage = lazy(() => import("./pages/ModelsPage"));
const DrillPage = lazy(() => import("./pages/DrillPage"));
const EquityPage = lazy(() => import("./pages/EquityPage"));
const HealthCheckPage = lazy(() => import("./pages/HealthCheckPage"));
const LeaguePage = lazy(() => import("./pages/LeaguePage"));
const LiveSimPage = lazy(() => import("./pages/LiveSimPage"));
const PlayPage = lazy(() => import("./pages/PlayPage"));
const PlayerProfilesPage = lazy(() => import("./pages/PlayerProfilesPage"));
const ReplayerPage = lazy(() => import("./pages/ReplayerPage"));
const ImportPage = lazy(() => import("./pages/ImportPage"));
const SetupPage = lazy(() => import("./pages/SetupPage"));
const JobsPage = lazy(() => import("./pages/JobsPage"));
const StatusPage = lazy(() => import("./pages/StatusPage"));
const SolverSpotsPage = lazy(() => import("./pages/SolverSpotsPage"));
const LicensesPage = lazy(() => import("./pages/LicensesPage"));
const DatasheetPage = lazy(() => import("./pages/DatasheetPage"));

function PageFallback() {
  return (
    <div className="flex items-center justify-center py-16 text-slate-400 text-sm" aria-busy="true">
      Loading…
    </div>
  );
}

/**
 * On first load, redirect to /health if:
 *  - No cached result, OR
 *  - Last result had failures/warnings
 * Skip the redirect if the user navigated directly to /health already.
 */
function FirstLoadGuard() {
  const navigate = useNavigate();
  useEffect(() => {
    const isHealthPage = window.location.pathname === "/health";
    if (isHealthPage) return;
    const cached = getCachedHealthResult();
    if (!cached) {
      void navigate("/health?auto=1", { replace: true });
    }
    // If cached + all_passed → stay on current page (normal navigation)
  }, [navigate]);
  return null;
}

export default function App() {
  return (
    <>
      <FirstLoadGuard />
      <Suspense fallback={<PageFallback />}>
        <Routes>
          {/* Health check — full-screen, no layout shell */}
          <Route path="health" element={<HealthCheckPage />} />

          {/* Main app with nav layout */}
          <Route element={<Layout />}>
            <Route index element={<ReplayerPage />} />
            <Route path="status" element={<StatusPage />} />
            <Route path="import" element={<ImportPage />} />
            <Route path="setup" element={<SetupPage />} />
            <Route path="sim" element={<LiveSimPage />} />
            <Route path="play" element={<PlayPage />} />
            <Route path="profiles" element={<PlayerProfilesPage />} />
            <Route path="solver" element={<SolverSpotsPage />} />
            <Route path="equity" element={<EquityPage />} />
            <Route path="drill" element={<DrillPage />} />
            <Route path="league" element={<LeaguePage />} />
            <Route path="drift" element={<DriftPage />} />
            <Route path="models" element={<ModelsPage />} />
            <Route path="licenses" element={<LicensesPage />} />
            <Route path="datasheet" element={<DatasheetPage />} />
            <Route path="blueprint" element={<BlueprintPage />} />
            <Route path="jobs" element={<JobsPage />} />
          </Route>
        </Routes>
      </Suspense>
    </>
  );
}

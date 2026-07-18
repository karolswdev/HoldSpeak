// HS-95-08 — one shell. Three real routes (Desk, Welcome, Presence); every
// demoted product path walks home and opens its desk window at the right
// scope (Constitution, Article I: features do not own routes).
import { Suspense, useEffect } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Skeleton } from "./components/signal/Signal";
import { DEMOTED_ROUTES, PRODUCT_ROUTES, type DemotedRoute } from "./routes";
import { openSurfaceWhenReady, setShellNavigator } from "./desk/shell";
import {
  decodeWorkroomContext,
  workroomSubjectId,
} from "./workrooms/context";

/** A demoted route: queue the window open (it fires the moment the desk
 * registers the surface), then land on the desk. */
function SurfaceRedirect({ route }: { route: DemotedRoute }) {
  useEffect(() => {
    const search = window.location.search;
    let scope: string | undefined;
    if (route.subjectKind) {
      const workroom = decodeWorkroomContext(search);
      const id =
        workroomSubjectId(workroom, route.subjectKind) ??
        (route.legacyParam
          ? new URLSearchParams(search).get(route.legacyParam)
          : null);
      if (id) scope = `${route.subjectKind}:${id}`;
    }
    openSurfaceWhenReady(route.surface, scope);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [route.path]);
  return <Navigate to="/" replace />;
}

export function App() {
  const navigate = useNavigate();
  useEffect(() => {
    setShellNavigator((href) => navigate(href));
  }, [navigate]);
  return (
    <AppShell>
      <ErrorBoundary>
        <Suspense fallback={<Skeleton rows={5} />}>
          <Routes>
            {PRODUCT_ROUTES.map(({ path, component: Component }) => (
              <Route key={path} path={path} element={<Component />} />
            ))}
            {DEMOTED_ROUTES.map((route) => (
              <Route
                key={route.path}
                path={route.path}
                element={<SurfaceRedirect route={route} />}
              />
            ))}
            <Route path="/desk" element={<Navigate to="/" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </AppShell>
  );
}

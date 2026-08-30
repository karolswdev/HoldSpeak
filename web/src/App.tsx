// HS-95-08 — one shell. Three real routes (Desk, Welcome, Presence); every
// demoted product path walks home and opens its desk window at the right
// scope (Constitution, Article I: features do not own routes).
import { Suspense, useEffect, useState } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { SurfaceState } from "./desk/surface/Surface";
import { DEMOTED_ROUTES, PRODUCT_ROUTES, type DemotedRoute } from "./routes";
import { setShellNavigator, stageSurfaceOpen } from "./desk/shell";
import {
  decodeWorkroomContext,
  workroomSubjectId,
} from "./workrooms/context";
import { deskQueryClient } from "./lib/queryClient";

/** A demoted route: queue the window open (it fires the moment the desk
 * registers the surface), then land on the desk. */
function SurfaceRedirect({ route }: { route: DemotedRoute }) {
  // Queue the in-world open in one committed render before Navigate is allowed
  // to unmount this route. Rendering Navigate immediately made its own effect
  // win occasionally, so /meetings could leave before it had queued its open.
  const [queued, setQueued] = useState(false);
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
    stageSurfaceOpen(route.surface, scope);
    setQueued(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [route.path]);
  // Preserve the one URL token/context through the demotion; the surface's
  // lazy core still needs the same authenticated browser request context.
  return queued ? <Navigate to={{ pathname: "/", search: window.location.search }} replace /> : null;
}

export function App() {
  const navigate = useNavigate();
  useEffect(() => {
    setShellNavigator((href) => navigate(href));
  }, [navigate]);
  return (
    <QueryClientProvider client={deskQueryClient}>
      <AppShell>
        <ErrorBoundary>
          <Suspense fallback={<SurfaceState loading />}>
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
    </QueryClientProvider>
  );
}

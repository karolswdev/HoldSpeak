import { Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Skeleton } from "./components/signal/Signal";
import { PRODUCT_ROUTES } from "./routes";

export function App() {
  const location = useLocation();
  const route = PRODUCT_ROUTES.find((item) => item.path === location.pathname);
  const immersive = route?.immersive ?? false;
  return (
    <AppShell immersive={immersive}>
      <ErrorBoundary>
        <Suspense
          fallback={
            <div className="page-wrap">
              <Skeleton rows={5} />
            </div>
          }
        >
          <Routes>
            {PRODUCT_ROUTES.map(({ path, component: Component }) => (
              <Route key={path} path={path} element={<Component />} />
            ))}
            <Route path="/desk" element={<Navigate to="/" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </AppShell>
  );
}

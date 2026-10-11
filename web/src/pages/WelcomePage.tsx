import { useEffect } from "react";
import { Navigate } from "react-router-dom";
import { openFirstRun } from "../desk/firstrun/reopen";

/** PHILO-17 U17: the old /welcome address opens the SAME Get ready cards
 * the fresh desk shows (its First words card is the sentence this page
 * had). The separate page is parked in pages/_parked/WelcomePage.tsx. */
export default function WelcomePage() {
  useEffect(() => {
    openFirstRun();
  }, []);
  // Keep the URL token/context through the hand-off, as demoted routes do.
  return <Navigate to={{ pathname: "/", search: window.location.search }} replace />;
}

import { useNavigate } from "react-router-dom";
import { FirstWords } from "../desk/components/FirstWords";

/** Compatibility arrival route: the first-value surface now lives on the Desk,
 * but old bookmarks land on the same one-step experience instead of a wizard. */
export default function WelcomePage() {
  const navigate = useNavigate();
  return (
    <main className="welcome-shell" id="main" tabIndex={-1}>
      <div className="welcome-mark">◍ HoldSpeak</div>
      <section className="welcome-card">
        <FirstWords onDismiss={() => navigate("/", { replace: true })} />
      </section>
    </main>
  );
}

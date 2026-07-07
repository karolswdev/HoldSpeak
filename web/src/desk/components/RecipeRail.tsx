// The recipe rail (HS-73-07 → HS-83-02): personas run FROM the world and
// their results land IN the world. A slim right-edge rail of avatars (the
// iPad's Agents rail); tap → the persona's CONVERSATION (PersonaChat — a
// persistent multi-turn thread; the old anchored single-prompt is retired).
// Personas ONLY — a coder is a live session, never railed (the Primitive
// Framework rule).
import { useDesk } from "../store";

export function RecipeRail() {
  const agents = useDesk((s) => s.items.recipe);
  const profiles = useDesk((s) => s.profiles);
  const chatPersonaId = useDesk((s) => s.chatPersonaId);
  const { openChat, closeChat } = useDesk.getState();

  if (!agents.length) return null;

  const egressDot = (a: any) => {
    const p = profiles.find((x) => x.id === a.profileId);
    if (!p) return null;
    const cloud = (p.kind || "onDevice") !== "onDevice";
    return (
      <span
        className={`desk-rail-egress is-${cloud ? "cloud" : "local"}`}
        title={cloud ? `☁ ${String(p.base_url || "endpoint")}` : "⌂ On device"}
      />
    );
  };

  return (
    <div className="desk-rail">
      {agents.map((a: any) => (
        <div key={a.id} className="desk-rail-slot">
          <button
            type="button"
            className={"desk-rail-avatar" + (chatPersonaId === a.id ? " open" : "")}
            title={String(a.name || a.id)}
            onClick={() => (chatPersonaId === a.id ? closeChat() : openChat(a.id))}
          >
            <span aria-hidden="true">{String(a.avatar || "🤖")}</span>
            {egressDot(a)}
          </button>
        </div>
      ))}
    </div>
  );
}

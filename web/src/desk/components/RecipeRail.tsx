// The recipe rail (HS-73-07 → HS-83-02): personas run FROM the world and
// their results land IN the world. A slim right-edge rail of avatars (the
// iPad's Agents rail); tap → the persona's CONVERSATION (PersonaChat — a
// persistent multi-turn thread; the old anchored single-prompt is retired).
// Personas ONLY — a coder is a live session, never railed (the Primitive
// Framework rule).
import { useDesk } from "../store";
import { modelChatId } from "../chat";

export function RecipeRail() {
  const agents = useDesk((s) => s.items.recipe);
  const profiles = useDesk((s) => s.profiles);
  const models = useDesk((s) => s.models);
  const chatPersonaId = useDesk((s) => s.chatPersonaId);
  const { openChat, closeChat } = useDesk.getState();

  if (!agents.length && !models.length) return null;

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
      {/* HS-83-03 — the models front door: every model the hub can run is a
          chat you can open (the /api/models allow-list; hub row first). */}
      {models.length > 0 && agents.length > 0 && <div className="desk-rail-rule" aria-hidden="true" />}
      {models.map((m) => {
        const id = modelChatId(m.name);
        // HS-85-04: a mesh model shows LIVENESS, not existence
        const mesh = (m as any).node
          ? (m as any).live
            ? ` — mesh · ${(m as any).node}`
            : ` — mesh · ${(m as any).node} (offline)`
          : "";
        const offline = Boolean((m as any).node) && !(m as any).live;
        return (
          <div key={id} className="desk-rail-slot">
            <button
              type="button"
              className={
                "desk-rail-avatar desk-rail-model" +
                (chatPersonaId === id ? " open" : "") +
                (offline ? " is-offline" : "")
              }
              title={m.name + mesh}
              onClick={() => (chatPersonaId === id ? closeChat() : openChat(id))}
            >
              <span aria-hidden="true">🖥️</span>
            </button>
          </div>
        );
      })}
    </div>
  );
}

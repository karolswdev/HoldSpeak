// HS-83-02 — the persona's home on the web desk: a LIVING CONVERSATION
// (the iPad's DioRecipeChat posture). Docked pullout, desk alive behind;
// turns accumulate and persist device-local; each reply wears the turn's
// honest egress and can be harvested to the desk; the HSM-15-12 grounding
// picker rides the composer, per conversation.
import { useEffect, useMemo, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { useDesk } from "../store";
import {
  clearThread,
  isModelChat,
  keepReply,
  loadChatGrounding,
  loadThread,
  modelChatName,
  runChatTurn,
  runModelChatTurn,
  saveChatGrounding,
  saveThread,
  type ChatTurn,
} from "../chat";
import { keepAsk } from "../ask";
import {
  groundingIsEmpty,
  groundingTokens,
  type GroundingSelection,
} from "../grounding";
import { GroundingSection } from "./GroundingSection";
import { MicButton } from "./MicButton";
import { RunsOnPicker } from "./RunsOnPicker";
import { DeskWindowFrame } from "./DeskWindow";
import { useDurableDraft } from "../../lib/durableDraft";

const turnId = () =>
  `t_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;

export function PersonaChat(props: { personaId: string }) {
  const reducedMotion = useReducedMotion();
  const { personaId } = props;
  const items = useDesk((s) => s.items);
  const profiles = useDesk((s) => s.profiles);
  const inferenceTargets = useDesk((s) => s.inferenceTargets);
  const { closeChat, refresh, markNew } = useDesk.getState();

  // HS-83-03: a model chat is one of THESE threads — a synthetic persona
  // pinned to one of the hub's runnable models (no recipe record behind it).
  const persona = useMemo(() => {
    if (isModelChat(personaId)) {
      const name = modelChatName(personaId);
      return {
        id: personaId,
        name,
        avatar: "🖥️",
        role: "hub model",
        profileId: "",
      } as any;
    }
    return (items.recipe || []).find((a: any) => a.id === personaId) as any;
  }, [items, personaId]);

  const [turns, setTurns] = useState<ChatTurn[]>(() => loadThread(personaId));
  const [grounding, setGrounding] = useState<GroundingSelection>(() =>
    loadChatGrounding(personaId),
  );
  const {
    value: input,
    setDraft: setInput,
    recovered: inputRecovered,
  } = useDurableDraft(`persona-chat:${personaId}`);
  const [thinking, setThinking] = useState(false);
  const [savedId, setSavedId] = useState<string | null>(null);
  const [inferenceTargetId, setInferenceTargetId] = useState("this_machine");
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setTurns(loadThread(personaId));
    setGrounding(loadChatGrounding(personaId));
    setInferenceTargetId(String(persona?.profileId || "this_machine"));
  }, [personaId, persona?.profileId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, thinking]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !thinking) closeChat();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [thinking]);

  if (!persona) return null;

  const limitTokens = (() => {
    const p = profiles.find((x) => x.id === persona.profileId);
    return Number(p?.context_limit) > 0 ? Number(p?.context_limit) : 16_384;
  })();
  const overBudget = groundingTokens(grounding) > limitTokens;

  const setAndSaveGrounding = (s: GroundingSelection) => {
    setGrounding(s);
    saveChatGrounding(personaId, s);
  };

  const send = async () => {
    const q = input.trim();
    if (!q || thinking || overBudget) return;
    const history = turns;
    const mine: ChatTurn = { id: turnId(), role: "you", text: q };
    const withMine = [...history, mine];
    setTurns(withMine);
    saveThread(personaId, withMine);
    setInput("");
    setThinking(true);
    const r = isModelChat(personaId)
      ? await runModelChatTurn(
          modelChatName(personaId),
          q,
          history,
          grounding,
          inferenceTargetId,
        )
      : await runChatTurn(personaId, q, history, grounding, inferenceTargetId);
    const reply: ChatTurn = r.ok
      ? {
          id: turnId(),
          role: "agent",
          text: r.output,
          egress: r.egress,
          model: r.model,
          actualPlacement: r.actualPlacement,
        }
      : { id: turnId(), role: "agent", text: r.output, error: true };
    const done = [...withMine, reply];
    setThinking(false);
    setTurns(done);
    saveThread(personaId, done);
  };

  const harvest = async (t: ChatTurn) => {
    if (savedId) return;
    setSavedId(t.id);
    const question =
      [...turns].reverse().find((x) => x.role === "you")?.text || "";
    const artifactId = isModelChat(personaId)
      ? await keepAsk({
          lens: modelChatName(personaId),
          prompt: question,
          output: t.text,
          context: [],
        })
      : await keepReply(personaId, question, t.text);
    if (artifactId) {
      await refresh();
      markNew(artifactId);
      setTimeout(() => setSavedId(null), 1600);
    } else {
      setSavedId(null);
    }
  };

  const clear = () => {
    clearThread(personaId);
    setTurns([]);
  };

  const badge = (t: ChatTurn) =>
    t.egress
      ? t.egress.scope === "local"
        ? {
            scope: "local",
            text: t.model ? `⌂ This device · ${t.model}` : "⌂ This device",
          }
        : t.egress.scope === "mesh"
          ? {
              scope: "mesh",
              text: `⇄ ${["Paired", t.egress.host, t.model].filter(Boolean).join(" · ")}`,
            }
          : {
              scope: "cloud",
              text: `→ ${["Leaves device", t.egress.host, t.model].filter(Boolean).join(" · ")}`,
            }
      : null;

  return (
    <DeskWindowFrame
      id="chat"
      glyph="💬"
      label={String(persona.name || personaId)}
      className="desk-pullout desk-chat"
      icon={
        <span className="desk-chat-avatar" aria-hidden="true">
          {String(persona.avatar || "🤖")}
        </span>
      }
      title={
        <>
          {String(persona.name || personaId)}
          {persona.role ? (
            <span className="desk-chat-role"> · {String(persona.role)}</span>
          ) : null}
        </>
      }
      actions={
        turns.length > 0 ? (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={clear}
            disabled={thinking}
          >
            Clear
          </button>
        ) : null
      }
      open={Boolean(persona)}
      onClose={() => {
        if (!thinking) closeChat();
      }}
    >

      <div className="desk-pullout-body desk-chat-scroll">
        {turns.length === 0 && !thinking && (
          <div className="desk-chat-hello">
            <span className="desk-chat-hello-avatar" aria-hidden="true">
              {String(persona.avatar || "🤖")}
            </span>
            <strong className="surface-primary">
              {String(persona.name || "This agent")}
            </strong>
            {persona.role ? (
              <small>{String(persona.role)}</small>
            ) : null}
          </div>
        )}
        {turns.map((t) => (
          <div
            key={t.id}
            className={
              "desk-chat-turn is-" + t.role + (t.error ? " is-error" : "")
            }
          >
            <div className="desk-chat-bubble">{t.text}</div>
            {t.role === "agent" && !t.error && (
              <div className="desk-chat-meta">
                {badge(t) && (
                  <span className={`egress-badge is-${badge(t)!.scope}`}>
                    {badge(t)!.text}
                  </span>
                )}
                {t.actualPlacement && (
                  <span className="quiet">
                    Ran on{" "}
                    {String(
                      t.actualPlacement.target_name ||
                        t.actualPlacement.target_id,
                    )}
                    {t.actualPlacement.boundary
                      ? ` · ${String(t.actualPlacement.boundary)}`
                      : ""}
                  </span>
                )}
                <button
                  type="button"
                  className="desk-chip quiet"
                  onClick={() => void harvest(t)}
                >
                  {savedId === t.id ? "Saved to Desk" : "Keep as Artifact"}
                </button>
              </div>
            )}
          </div>
        ))}
        {thinking && (
          <div className="desk-chat-turn is-agent">
            <div className="desk-chat-bubble desk-chat-thinking">· · ·</div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <footer className="desk-chat-foot">
        <GroundingSection
          meetings={(items.meeting || []).map((m: any) => ({
            id: m.id,
            title: String(m.title || "Untitled meeting"),
            startedAt: m.startedAt,
          }))}
          selection={grounding}
          onChange={setAndSaveGrounding}
          limitTokens={limitTokens}
        />
        <div className="desk-chat-well">
          <div className="desk-chat-composer">
            <MicButton
              draftScope={`persona-chat:${personaId}`}
              onText={(t) => setInput((v) => (v ? v + " " + t : t))}
            />
            <input
              autoFocus
              value={input}
              placeholder={"Message " + String(persona.name || "")}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void send();
              }}
            />
            <button
              type="button"
              className="desk-chip"
              disabled={!input.trim() || thinking || overBudget}
              title={
                overBudget
                  ? "Grounding exceeds the context limit. Remove material."
                  : undefined
              }
              onClick={() => void send()}
            >
              {thinking ? "…" : "Send"}
            </button>
          </div>
          <div className="desk-chat-well-foot">
            <RunsOnPicker
              targets={inferenceTargets}
              selectedId={inferenceTargetId}
              onChange={setInferenceTargetId}
              disabled={thinking}
            />
          </div>
        </div>
        {inputRecovered ? (
          <span className="quiet">Recovered local message draft.</span>
        ) : null}
        {!groundingIsEmpty(grounding) && overBudget && (
          <p className="desk-run-warning">
            Grounding exceeds the context limit. Remove material.
          </p>
        )}
      </footer>
    </DeskWindowFrame>
  );
}

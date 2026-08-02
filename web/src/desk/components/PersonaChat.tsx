// HS-83-02 — the agent's home on the web desk: a LIVING CONVERSATION.
// Docked pullout, desk alive behind; turns accumulate and persist
// device-local; each reply wears the turn's honest egress and can be
// harvested to the desk; the HSM-15-12 grounding picker rides the
// composer, per conversation.
// HS-111-04 — the personnel record (audit §3.2): a record head (glyph
// tile, name, role token, facts line, the ONE EgressChip species) over
// a transmission log — prefixed mono `YOU>` / `<NAME>>` turns in the
// sunken well, no bubbles, no hello card, no slide-in.
import { useEffect, useMemo, useRef, useState } from "react";
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
import { AgentAvatar } from "./AgentAvatar";
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
import {
  SurfaceFacts,
  SurfaceTraffic,
  SurfaceTrafficTurn,
} from "../surface/Surface";
import { EgressChip, LedMeter, TransportKey } from "../surface/gadgets";
import { Button } from "../../components/signal/Signal";

const turnId = () =>
  `t_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;

export function PersonaChat(props: { personaId: string }) {
  const { personaId } = props;
  const items = useDesk((s) => s.items);
  const profiles = useDesk((s) => s.profiles);
  const inferenceTargets = useDesk((s) => s.inferenceTargets);
  const { closeChat, refresh, markNew } = useDesk.getState();

  // HS-83-03: a model chat is one of THESE threads — a synthetic agent
  // pinned to one of the hub's runnable models (no recipe record behind it).
  const persona = useMemo(() => {
    if (isModelChat(personaId)) {
      const name = modelChatName(personaId);
      return {
        id: personaId,
        name,
        // HS-111-09 — no emoji: empty avatar wears the cartridge sprite
        // (the model family) via AgentAvatar.
        avatar: "",
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
    endRef.current?.scrollIntoView({ block: "end" });
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

  // The ONE egress species (EgressChip): the turn's honest boundary as
  // a token, never a second hand-rolled badge.
  const egressChip = (t: ChatTurn) => {
    if (!t.egress) return null;
    if (t.egress.scope === "local") {
      return (
        <EgressChip
          label={t.model ? `⌂ This device · ${t.model}` : "⌂ This device"}
        />
      );
    }
    if (t.egress.scope === "mesh") {
      return (
        <EgressChip
          label={`⇄ ${["Paired", t.egress.host, t.model].filter(Boolean).join(" · ")}`}
          title="This reply ran on a paired device on your network."
        />
      );
    }
    return (
      <EgressChip
        label={`→ ${["Leaves device", t.egress.host, t.model].filter(Boolean).join(" · ")}`}
        title="This reply left the device for the named service."
      />
    );
  };

  const name = String(persona.name || personaId);
  const handle = name.toUpperCase();
  const target = inferenceTargets.find((t: any) => t.id === inferenceTargetId);
  const lastEgress = [...turns]
    .reverse()
    .find((t) => t.role === "agent" && !t.error && t.egress);

  return (
    <DeskWindowFrame
      id="chat"
      glyph="❝"
      label={name}
      className="desk-pullout desk-chat"
      icon={
        <span className="desk-chat-avatar" aria-hidden="true">
          <AgentAvatar
            avatar={persona.avatar}
            id={personaId}
            kind={isModelChat(personaId) ? "model" : "agent"}
            size={16}
          />
        </span>
      }
      title={name}
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
        <header className="surface-record-head">
          <span className="surface-record-glyph" aria-hidden="true">
            <AgentAvatar
              avatar={persona.avatar}
              id={personaId}
              kind={isModelChat(personaId) ? "model" : "agent"}
              size={32}
            />
          </span>
          <span className="surface-record-id">
            <strong className="surface-primary">{name}</strong>
            {persona.role ? (
              <span className="gadget-chip">{String(persona.role)}</span>
            ) : null}
          </span>
          {lastEgress ? egressChip(lastEgress) : <EgressChip />}
        </header>
        <SurfaceFacts
          value={{
            runs_on: String(target?.name || "This device"),
            ctx: `${Math.round(limitTokens / 1000)}K`,
            turns: turns.length || "",
          }}
        />
        <SurfaceTraffic
          head={`TRAFFIC · ${turns.length} TURNS`}
          showEmpty={turns.length === 0 && !thinking}
        >
          {turns.map((t) => (
            <SurfaceTrafficTurn
              key={t.id}
              prefix={t.role === "you" ? "YOU>" : `${handle}>`}
              error={t.error}
              meta={
                t.role === "agent" && !t.error ? egressChip(t) : undefined
              }
              verbs={
                t.role === "agent" && !t.error ? (
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => void harvest(t)}
                  >
                    {savedId === t.id ? "Kept" : "Keep"}
                  </Button>
                ) : undefined
              }
            >
              {t.text}
            </SurfaceTrafficTurn>
          ))}
          {thinking ? (
            <SurfaceTrafficTurn prefix={`${handle}>`}>
              <LedMeter label="RX" value={0} scanning />
            </SurfaceTrafficTurn>
          ) : null}
          <div ref={endRef} />
        </SurfaceTraffic>
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
              aria-label={"Message " + name}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void send();
              }}
            />
            <TransportKey
              compact
              label="SEND"
              glyph="▸"
              disabled={!input.trim() || thinking || overBudget}
              title={
                overBudget
                  ? "Grounding exceeds the context limit. Remove material."
                  : undefined
              }
              onClick={() => void send()}
            />
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

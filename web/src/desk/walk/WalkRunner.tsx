/** Local app help and linked question walks share the window's guide note. */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { GuideNote, PadGadget } from "../surface";
import { captureScale, captureViewportPng } from "../feedback/capture";
import { requestUiFeedback, useUiFeedbackState } from "../feedback/runtime";
import { executeDeskRequest, findDeskWindow } from "../compositor/requests";
import { isDrawn, selectorFor } from "../compositor/dom";
import { speak, stop as stopVoice } from "../../lib/tts";
import { borrowGuideView } from "./viewState";
import {
  clearWalkFromLocation,
  onLocalWalk,
  postWalkAnswer,
  readWalk,
  walkAgent,
  walkTokenFromLocation,
  type LocalWalk,
  type WalkPage,
  type WalkStep,
} from "./walk";
import { guideVoice, subscribeGuideVoice } from "./voice";

/** A guide may select only kit rows, rail rows and tabs. A role alone
 * cannot turn an action, form control or menu item into a safe press. */
export function canGuidePress(target: HTMLElement): boolean {
  if (
    target.matches(
      ":disabled,input,select,textarea,[contenteditable=true],[role^=menuitem]",
    ) ||
    target.closest("[data-guide-layer]")
  )
    return false;
  return (
    target.matches(
      '.object-list--selection > .object-list-rows > .object-list-row[role="row"][data-object-id]',
    ) ||
    target.matches('.surface-rail-row[role="option"][data-rail-id]') ||
    target.matches('.surface-segmented-tabs [role="tab"][data-tab]')
  );
}

/** Find a part in one window. If a verb folded at phone width, point to
 * its Actions menu instead; the guide never opens or presses that menu. */
export function guideTarget(
  root: HTMLElement,
  target: string,
): HTMLElement | null {
  const all = [...root.querySelectorAll<HTMLElement>(selectorFor(target))];
  const drawn = all.find(isDrawn);
  if (drawn) return drawn;
  const toolbar = target.match(/^\[data-testid="([^"]+)"\] /)?.[1];
  return toolbar
    ? ([
        ...root.querySelectorAll<HTMLElement>(
          `[data-testid="${toolbar}"] button[aria-haspopup="menu"]`,
        ),
      ].find(isDrawn) ?? null)
    : null;
}

export function WalkRunner() {
  const [linked] = useState(walkTokenFromLocation);
  const [local, setLocal] = useState<LocalWalk | null>(null);
  useEffect(() => onLocalWalk(setLocal), []);
  if (local) return <WalkSession key={local.run} local={local} />;
  return linked ? <WalkSession token={linked} /> : null;
}

function WalkSession({ local, token }: { local?: LocalWalk; token?: string }) {
  const [page, setPage] = useState<WalkPage | null>(() =>
    local ? { ...local.script, answers: {} } : null,
  );
  const [index, setIndex] = useState(0);
  const [closed, setClosed] = useState(false);
  const [part, setPart] = useState<{
    owner: HTMLElement;
    target: HTMLElement | null;
  } | null>(null);
  const [ready, setReady] = useState(false);
  const [failure, setFailure] = useState("");
  const [words, setWords] = useState("");
  const [more, setMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState(false);
  const [saved, setSaved] = useState(false);
  const feedbackSlot = useRef<HTMLDivElement>(null);
  const capability = useUiFeedbackState();
  const lastApp = useRef(local?.origin);
  const empty = useRef(false);
  const restore = useRef<(() => void) | null>(null);
  const generation = useRef(0);
  const [voice, setVoice] = useState(guideVoice);
  useEffect(() => subscribeGuideVoice(() => setVoice(guideVoice())), []);
  useEffect(() => {
    if (local || !token) return;
    let alive = true;
    readWalk(token).then(
      (value) => {
        if (alive) setPage(value);
      },
      () => {
        if (alive) {
          clearWalkFromLocation();
          setClosed(true);
        }
      },
    );
    return () => {
      alive = false;
    };
  }, [local, token]);
  const finish = useCallback(() => {
    generation.current++;
    stopVoice();
    restore.current?.();
    restore.current = null;
    if (token) clearWalkFromLocation();
    setClosed(true);
  }, [token]);
  useEffect(
    () => () => {
      generation.current++;
      stopVoice();
      restore.current?.();
      restore.current = null;
    },
    [],
  );
  useEffect(() => {
    if (closed) return;
    const key = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || feedback || busy) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      finish();
    };
    const click = (event: PointerEvent) => {
      if (
        feedback ||
        busy ||
        !(event.target instanceof Element) ||
        event.target.closest("[data-guide-layer],[data-ui-feedback]")
      )
        return;
      if (part?.owner.contains(event.target)) finish();
    };
    document.addEventListener("keydown", key, true);
    document.addEventListener("pointerdown", click, true);
    return () => {
      document.removeEventListener("keydown", key, true);
      document.removeEventListener("pointerdown", click, true);
    };
  }, [closed, feedback, busy, part, finish]);
  const step = page?.steps[index];
  const advance = useCallback(() => {
    setReady(false);
    setSaved(false);
    setWords("");
    setMore(false);
    setFailure("");
    setIndex((i) => i + 1);
  }, []);
  useEffect(() => {
    if (!step || closed) return;
    const run = ++generation.current;
    setReady(false);
    if (local && empty.current && index < page!.steps.length - 1) {
      advance();
      return;
    }
    void (async () => {
      if (!local && step.open) {
        lastApp.current = step.open.app;
        await executeDeskRequest({ op: "open", args: step.open });
      }
      if (!local && step.verb)
        await executeDeskRequest({ op: "verb", args: step.verb });
      if (run !== generation.current) return;
      const app =
        step.highlight?.window ?? step.press?.window ?? lastApp.current;
      let owner = app
        ? findDeskWindow(app)
        : document.querySelector<HTMLElement>(
            '.desk-window-shell.is-front[data-layer="window"]',
          );
      // A linked open waits for the same compositor window as other requests.
      for (
        let attempt = 0;
        !owner && attempt < 60 && run === generation.current;
        attempt++
      ) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        owner = app ? findDeskWindow(app) : null;
      }
      if (run !== generation.current) return;
      if (!owner) {
        advance();
        return;
      }
      if (local && !restore.current) {
        const giveBack = borrowGuideView(owner.id);
        const scroll = [...owner.querySelectorAll<HTMLElement>("*")]
          .filter((el) => el.scrollTop || el.scrollLeft)
          .map((el) => ({ el, top: el.scrollTop, left: el.scrollLeft }));
        const tabs = [
          ...owner.querySelectorAll<HTMLElement>(
            '.surface-segmented-tabs [role="tab"][aria-selected="true"]',
          ),
        ].map((el) => ({
          tab: el.dataset.tab,
          label: el.closest('[role="tablist"]')?.getAttribute("aria-label"),
        }));
        const focus =
          document.activeElement instanceof HTMLElement
            ? document.activeElement
            : null;
        restore.current = () => {
          giveBack();
          requestAnimationFrame(() => {
            tabs.forEach((saved) => {
              const group = [
                ...owner!.querySelectorAll('[role="tablist"]'),
              ].find((el) => el.getAttribute("aria-label") === saved.label);
              const tab = group?.querySelector<HTMLElement>(
                `[data-tab="${CSS.escape(saved.tab ?? "")}"]`,
              );
              if (
                tab &&
                canGuidePress(tab) &&
                tab.getAttribute("aria-selected") !== "true"
              )
                tab.click();
            });
            scroll.forEach(({ el, top, left }) => {
              el.scrollTop = top;
              el.scrollLeft = left;
            });
            if (focus?.isConnected) focus.focus({ preventScroll: true });
          });
        };
      }
      await new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)),
      );
      if (run !== generation.current) return;
      if (step.press) {
        const selected =
          guideTarget(owner, step.press.target) ??
          owner.querySelector<HTMLElement>(selectorFor(step.press.target));
        if (!selected) {
          empty.current = true;
          advance();
          return;
        }
        if (!canGuidePress(selected)) {
          setFailure("Show me cannot press this control.");
          setPart({ owner, target: selected });
          setReady(true);
          return;
        }
        selected.click();
        await new Promise((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)),
        );
      }
      if (run !== generation.current) return;
      const targetName =
        step.highlight?.target ?? step.press?.target ?? step.scroll?.target;
      let target = targetName ? guideTarget(owner, targetName) : null;
      const hiddenTarget = targetName
        ? owner.querySelector<HTMLElement>(selectorFor(targetName))
        : null;
      if (!target && hiddenTarget?.closest(".surface-rail")) {
        hiddenTarget.dispatchEvent(
          new CustomEvent("hs:guide-reveal", { bubbles: true }),
        );
        await new Promise((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)),
        );
        target = targetName ? guideTarget(owner, targetName) : null;
      }
      // The selected pane can read after the press. Do not narrate its old state.
      for (
        let attempt = 0;
        targetName && !target && attempt < 15 && run === generation.current;
        attempt++
      ) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        target = guideTarget(owner, targetName);
      }
      if (run !== generation.current) return;
      if (targetName && !target) {
        advance();
        return;
      }
      target?.scrollIntoView?.({
        block: "nearest",
        inline: "nearest",
        behavior: "instant",
      });
      setPart({ owner, target });
      setReady(true);
    })().catch(() => {
      if (run === generation.current) {
        setFailure("This step did not open.");
        setReady(true);
      }
    });
    return () => {
      generation.current++;
    };
  }, [step, local, closed, advance]);
  const caption =
    step?.highlight?.words ??
    step?.press?.words ??
    step?.say?.words ??
    step?.ask?.question ??
    "";
  useEffect(() => {
    if (!ready || !voice || feedback || !caption) return;
    if (local) {
      if (typeof speechSynthesis !== "undefined")
        speechSynthesis.speak(new SpeechSynthesisUtterance(caption));
    } else void speak(caption);
    return () => stopVoice();
  }, [ready, voice, feedback, caption, local]);
  useEffect(() => {
    if (page && index >= page.steps.length && !closed) finish();
  }, [page, index, closed, finish]);
  if (closed || !page || !part || !step) return null;
  const answer = async (choice: string) => {
    if (!token || !step.ask || busy) return;
    setBusy(true);
    setFailure("");
    try {
      const image = await captureViewportPng();
      const rect = part.target?.getBoundingClientRect();
      await postWalkAnswer(token, {
        ref: step.ask.ref,
        choice,
        ...(words.trim() ? { words: words.trim() } : {}),
        ...(image ? { window_png: image } : {}),
        view: {
          width: innerWidth,
          height: innerHeight,
          dpr: devicePixelRatio || 1,
          scale: captureScale(),
          agent: walkAgent(navigator.userAgent),
          ...(rect
            ? {
                rect: {
                  left: rect.left,
                  top: rect.top,
                  width: rect.width,
                  height: rect.height,
                },
              }
            : {}),
        },
      });
      advance();
    } catch {
      setFailure("Answer not saved. Try again.");
    } finally {
      setBusy(false);
    }
  };
  const startFeedback = () => {
    if (!part.target || !feedbackSlot.current) return;
    stopVoice();
    requestUiFeedback(part.target, {
      guide: {
        app: page.title,
        step: index + 1,
        of: page.steps.length,
        target: step.highlight?.target ?? step.press?.target ?? "",
        words: caption,
      },
      mount: feedbackSlot.current,
      onFinish: (wasSaved) => {
        setFeedback(false);
        if (wasSaved) setSaved(true);
      },
    });
    setFeedback(true);
  };
  return (
    <GuideNote
      owner={part.owner}
      target={part.target}
      words={caption}
      count={saved ? "Saved." : `${index + 1} of ${page.steps.length}`}
      last={index === page.steps.length - 1}
      onStop={finish}
      onNext={index === page.steps.length - 1 ? finish : advance}
      busy={!ready || busy}
      onFeedback={local && capability.enabled ? startFeedback : undefined}
      focusNext={!feedback && !step.ask}
      actions={
        feedback ? (
          <></>
        ) : step.ask && token ? (
          <div className="guide-bar">
            <span className="guide-count">
              {index + 1} of {page.steps.length}
            </span>
            {step.ask.choices.map((choice, i) => (
              <Button
                key={choice}
                dense
                variant={i ? "secondary" : "primary"}
                disabled={busy}
                onClick={() => void answer(choice)}
                data-testid={`walk-choice-${i}`}
              >
                {choice}
              </Button>
            ))}
            <Button
              dense
              variant="secondary"
              onClick={() => setMore((v) => !v)}
              disabled={busy}
            >
              Say more
            </Button>
            {more ? (
              <Button
                dense
                variant="secondary"
                disabled={busy || !words.trim()}
                onClick={() => void answer("words")}
              >
                Send
              </Button>
            ) : null}
            <Button
              dense
              variant="secondary"
              disabled={busy}
              onClick={() => void answer("skip")}
              data-testid="walk-skip"
            >
              Skip
            </Button>
          </div>
        ) : undefined
      }
    >
      {step.ask ? (
        <span data-testid="walk-question">{step.ask.question}</span>
      ) : null}
      {more ? (
        <PadGadget label="Say more" value={words} onChange={setWords} />
      ) : null}
      {failure ? (
        <span role="alert" data-testid="walk-failure">
          {failure}
        </span>
      ) : null}
      <div ref={feedbackSlot} data-guide-capture-slot />
    </GuideNote>
  );
}

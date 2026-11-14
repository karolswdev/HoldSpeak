/** Local app help and linked question walks share the window's guide note. */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { GuideNote, PadGadget } from "../surface";
import { captureScale, captureViewportPng } from "../feedback/capture";
import { requestUiFeedback, useUiFeedbackState } from "../feedback/runtime";
import { executeDeskRequest, findDeskWindow } from "../compositor/requests";
import { isDrawn, selectorFor, loadingIn } from "../compositor/dom";
import { speak, stop as stopVoice } from "../../lib/tts";
import { borrowGuideView } from "./viewState";
import {
  clearWalkFromLocation,
  WALK_WINDOW_VERBS,
  onLocalWalk,
  postWalkAnswer,
  readWalk,
  walkAgent,
  walkTokenFromLocation,
  waitForDeskReady,
  READY_BEAT_MS,
  type LocalWalk,
  type WalkPage,
  type WalkStep,
} from "./walk";
import { guideVoice, subscribeGuideVoice } from "./voice";

/** A guide may press only kit rows, rail rows, tabs and disclosures. A role alone
 * cannot turn an action, form control or menu item into a safe press. */
export function canGuidePress(target: HTMLElement): boolean {
  if (
    target.matches(
      ":disabled,[href],[type=submit],input,select,textarea,[contenteditable=true],[role^=menuitem]",
    ) ||
    target.closest("[data-guide-layer]")
  )
    return false;
  return (
    target.matches(
      '.object-list--selection > .object-list-rows > .object-list-row[role="row"][data-object-id], .object-list--selection > .object-list-rows > .object-list-group > .object-list-row[role="row"][data-object-id]',
    ) ||
    target.matches('.surface-rail-row[role="option"][data-rail-id]') ||
    target.matches('.surface-segmented-tabs [role="tab"][data-tab]') ||
    target.matches('.object-list-toolbar-strip > button[aria-haspopup="menu"],.surface-strip-menu[aria-haspopup="menu"]')
  );
}

/** A folded verb has the same label in the one declared menu. */
export function guideTarget(root: HTMLElement, target: string): HTMLElement | null {
  return [...root.querySelectorAll<HTMLElement>(selectorFor(target))].find(isDrawn) ?? null;
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
  const feedbackAbort = useRef<AbortController | null>(null);
  const capability = useUiFeedbackState();
  const lastApp = useRef(local?.origin);
  const empty = useRef(false);
  const restore = useRef<(() => void) | null>(null);
  const generation = useRef(0);
  const deskSettled = useRef(false);
  const activeOwner = useRef<HTMLElement | null>(null);
  const guideMenu = useRef<HTMLElement | null>(null);
  const lastSelection = useRef<HTMLElement | null>(null);
  const closeGuideMenu = () => {
    const disclosure = guideMenu.current;
    guideMenu.current = null;
    if (disclosure?.isConnected && disclosure.getAttribute("aria-expanded") === "true" && canGuidePress(disclosure)) disclosure.click();
  };
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
    feedbackAbort.current?.abort();
    closeGuideMenu();
    activeOwner.current?.removeAttribute("data-guide-running");
    stopVoice();
    restore.current?.();
    restore.current = null;
    if (token) clearWalkFromLocation();
    setClosed(true);
  }, [token]);
  useEffect(
    () => () => {
      generation.current++;
      feedbackAbort.current?.abort();
      closeGuideMenu();
      activeOwner.current?.removeAttribute("data-guide-running");
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
    closeGuideMenu();
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
      if (!local && !deskSettled.current) {
        while (!(await waitForDeskReady())) {
          if (run !== generation.current) return;
        }
        await new Promise(resolve => setTimeout(resolve, READY_BEAT_MS));
        if (run !== generation.current) return;
        deskSettled.current = true;
      }
      if (!local && step.open) {
        lastApp.current = step.open.app;
        await executeDeskRequest({ op: "open", args: step.open });
      }
      if (!local && step.verb) {
        if (WALK_WINDOW_VERBS.has(step.verb.verb))
          await executeDeskRequest({ op: "verb", args: step.verb });
        else setFailure("This walk cannot run that verb.");
      }
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
      if (activeOwner.current !== owner) {
        activeOwner.current?.removeAttribute("data-guide-running");
        activeOwner.current = owner;
        owner.setAttribute("data-guide-running", "");
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
      // A linked opener may mount before its first app read completes.
      while (loadingIn(owner)) {
        await new Promise(resolve => setTimeout(resolve, 100));
        if (run !== generation.current) return;
      }
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
        if (selected.matches('.surface-rail-row,.object-list-row')) lastSelection.current = selected;
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
      if (!target && hiddenTarget && !hiddenTarget.closest(".surface-rail")) {
        const row = lastSelection.current ?? owner.querySelector<HTMLElement>('.surface-rail-row[aria-selected="true"]');
        if (row && isDrawn(row) && canGuidePress(row)) {
          row.click();
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          target = targetName ? guideTarget(owner, targetName) : null;
        }
      }
      const folded = targetName?.match(/^\[data-testid="([^"]+)"\] button\[aria-label="([^"]+)"\]$/);
      if (!target && folded) {
        const disclosure = owner.querySelector<HTMLElement>(`[data-testid="${folded[1]}"] [data-list-overflow]`);
        if (disclosure && isDrawn(disclosure) && canGuidePress(disclosure)) {
          if (disclosure.getAttribute("aria-expanded") !== "true") disclosure.click();
          guideMenu.current = disclosure;
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          const menu = document.querySelector<HTMLElement>(`[role="menu"][data-menu-owner="${CSS.escape(owner.id)}"]`);
          target = [...(menu?.querySelectorAll<HTMLElement>('[role^="menuitem"]') ?? [])]
            .find(item => item.querySelector('.desk-menu-label')?.textContent === folded[2]) ?? null;
        }
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
      for (let attempt = 0; target && [...target.querySelectorAll("option")].some(option => option.textContent === "Reading…") && attempt < 100 && run === generation.current; attempt++) {
        await new Promise(resolve => setTimeout(resolve, 100));
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
    void speak(caption, local ? { localOnly: true } : undefined);
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
    feedbackAbort.current?.abort();
    feedbackAbort.current = new AbortController();
    requestUiFeedback(part.target, {
      signal: feedbackAbort.current.signal,
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
      capture={feedback}
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

/* The shared setup of the Programs app tests (programs.*.app.test.tsx).
 *
 * The Programs app (T2; PROGRAMS-DESIGN-2026-10-28 §4, §6, §9, §9b; canvas
 * docs/internal/betterment/programs/canvases/programs-2026-10-28.html,
 * direction C "the ledger").
 *
 * Every answer is a RECORDED hub answer (web/src/desk/programs/__fixtures__/,
 * recorded through the real routes by scripts/record_program_fixtures.py).
 * The answer to a press is the recorded Program with the change the hub
 * makes applied to it (the item leaves `your_turn_items`, the decision gets
 * its `overturned_at`), so each press is driven through to the rendered
 * outcome: the row leaves the well, the status bar count drops, the row
 * reads Overturned. */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { lazy, useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import listFixture from "../__fixtures__/programs.list.json";
import runningFixture from "../__fixtures__/program.running.json";
import yourTurnFixture_ from "../__fixtures__/program.your_turn.json";
import doneFixture from "../__fixtures__/program.done.json";
import parkedFixture from "../__fixtures__/program.parked.json";
import draftingFixture from "../__fixtures__/program.drafting.json";
import limitedFixture from "../__fixtures__/program.limited.json";
import raceFixture from "../__fixtures__/program.race.json";
import needsFixture_ from "../__fixtures__/needs_you.program.json";
import roomFixture_ from "../__fixtures__/room.programs.json";
import personFixture_ from "../__fixtures__/person.programs.json";
import skipDecisionFixture_ from "../__fixtures__/program.skip_decision.json";
import roomProposedFixture_ from "../__fixtures__/room.decisions.proposed.json";
import startFromFixture_ from "../__fixtures__/program.start_from.json";
import historyFixture_ from "../__fixtures__/program.history.json";
import historyListFixture_ from "../__fixtures__/programs.history.list.json";
import sinceMorningPrograms_ from "../../__tests__/fixtures/today-hub/since-morning.programs.json";
// PG-REQ (PROGRAMS-REQUIREMENTS-2026-10-31): recorded through the real routes,
// with the hub's answers to his presses on the same records.
import filteredListFixture_ from "../__fixtures__/programs.filtered.list.json";
import requirementsFixture from "../__fixtures__/program.requirements.json";
import sendBackFixture_ from "../__fixtures__/program.requirements.send_back.json";
import waivedFixture_ from "../__fixtures__/program.requirements.waived.json";
import waiveRefusedFixture_ from "../__fixtures__/program.requirements.waive_refused.json";
import addedFixture_ from "../__fixtures__/program.requirements.added.json";
import evidenceFixture_ from "../__fixtures__/program.requirements.evidence.json";
import wordFixture_ from "../__fixtures__/program.requirement_word.json";
import wordMetFixture_ from "../__fixtures__/program.requirement_word.met.json";
import needsRequirementsFixture_ from "../__fixtures__/needs_you.requirements.json";
import adjustFixture from "../__fixtures__/program.adjust.json";
import movedFixture_ from "../__fixtures__/program.adjust.moved.json";
import insertedFixture_ from "../__fixtures__/program.adjust.inserted.json";
import amendedFixture_ from "../__fixtures__/program.adjust.amended.json";
import titledFixture_ from "../__fixtures__/program.adjust.titled.json";
import proposalsFixture_ from "../__fixtures__/program.proposals.json";
import proposalsAddedFixture_ from "../__fixtures__/program.proposals.added.json";
// PG-DIRECTION DIR3: recorded by tests/integration/test_desk_reach.py.
import pageNoneFixture_ from "../__fixtures__/program.page_none.json";
import pageOpenFixture_ from "../__fixtures__/program.page_open.json";
import revokeOpenFixture_ from "../__fixtures__/program.revoke_open.json";
import pageRevokedFixture_ from "../__fixtures__/program.page_revoked.json";
import reachPackageFixture_ from "../__fixtures__/reach.package.json";
import reachRevokedFixture_ from "../__fixtures__/reach.revoked.json";
// PG-LANG LANG2: the Program text (GET) and a preview then an apply of a
// changed text (a refused brief, control up the ladder, a new step, a merge
// on his press, a + line), recorded through the real routes.
import textFixture_ from "../__fixtures__/program.text.json";
import dreamingFixture_ from "../__fixtures__/program.dreaming.json";
import planningFixture_ from "../__fixtures__/program.plan_goal.planning.json";
import plannedFixture_ from "../__fixtures__/program.plan_goal.planned.json";
import notPlannedFixture_ from "../__fixtures__/program.plan_goal.not_planned.json";
import deliveryFailedFixture_ from "../__fixtures__/program.delivery_failed.json";
import deliveryMergeFixture_ from "../__fixtures__/program.delivery_merge.json";
import deliveryMergedFixture_ from "../__fixtures__/program.delivery_merged.json";
import deliveryCheckFixture_ from "../__fixtures__/program.delivery_check.json";
import deliveryCheckedOpenFixture_ from "../__fixtures__/program.delivery_checked_open.json";
import deliveryUnknownFixture_ from "../__fixtures__/program.delivery_unknown.json";
import deliveryQueuedFixture_ from "../__fixtures__/program.delivery_queued.json";
import deliveryLegacyFixture_ from "../__fixtures__/program.delivery_legacy_blocked.json";
import textApplyFixture_ from "../__fixtures__/program.text_apply.json";
// PG-IMPORT IMP2: the to-do row and his Done, the ending word (scripts/record_program_fixtures.py).
import todoFixture_ from "../__fixtures__/program.todo.json";
import todoDoneFixture_ from "../__fixtures__/program.todo.done.json";
// PG-IMPORT IMP6: Take it over, Hand it back (scripts/record_program_fixtures.py).
import laneFixture_ from "../__fixtures__/program.lane.json";
import laneTakenFixture_ from "../__fixtures__/program.lane.taken.json";
import laneBackFixture_ from "../__fixtures__/program.lane.back.json";
// PG-IMPORT IMP7: an audit and the two Programs it made (scripts/record_program_fixtures.py).
import familyFixture_ from "../__fixtures__/family.row.json";
// PG-LANG LANG3/4: a sentence shaped by the REAL qwen3.8-27b replies
// (tests/fixtures/program_shape_reply.json) replayed through the hub's runner,
// recorded through the real routes (tests/integration/test_desk_program_shape.py).
import shapeFixture_ from "../__fixtures__/program.shape.json";
// PG-LANG LANG6/7: a goal drafted by the REAL qwen3.8-27b replies
// (tests/fixtures/program_plan_reply.json) replayed through the hub's runner,
// recorded through the real routes (tests/integration/test_desk_program_plan.py).
import planFixture_ from "../__fixtures__/program.plan_draft.json";
import splitFixture_ from "../__fixtures__/program.plan_programs.json";
// PG-LANG LANG9/10: J1's interview rounds asked and shaped by the REAL
// qwen3.8-27b replies (tests/fixtures/program_round_reply.json) replayed
// through the hub's runner, recorded through the real routes
// (tests/integration/test_desk_program_rounds.py), in the face's own walk.
import roundsFixture_ from "../__fixtures__/program.rounds.json";
// HS-S11: one scenario through the real route and resolver, recorded as
// {request, response} (tests/integration/test_desk_programs.py
// test_creation_context_project_create_records_real_wire).
import createProjectsFixture_ from "../__fixtures__/program.create_projects.json";
import createProjectFixture_ from "../__fixtures__/program.create_project.json";
import createNoRepositoryFixture_ from "../__fixtures__/program.create_no_repository.json";
import createRepositoryRequiredFixture_ from "../__fixtures__/program.create_repository_required.json";
import createPersonFixture_ from "../__fixtures__/program.create_person.json";
import { resetScreenMembers as resetScreenMembers_ } from "../../screen/members";
// The desk's Control mode, as the hub answered GET /api/authority/policy on the recorded rig.
import needsYouRecorded_ from "../../__tests__/fixtures/needsYou.recorded.json";
// HS-S13 + HS-S11 (the creation-to-Room gate): the full hub's create for a
// project and that project's Room, recorded by
// tests/integration/test_desk_project_room.py::test_project_program_continuity_records_scope_and_reads.
import roomPrograms13_ from "../../../features/project-room/__tests__/room-wires/programs13.json";
// HS-S21: a Program made from an action, before and after the Add that binds
// a row to it (tests/integration/test_desk_program_from_action.py
// test_action_binding_wire, through the real routes).
import bindingUnboundFixture_ from "../__fixtures__/program.action_binding.unbound.json";
import bindingBoundFixture_ from "../__fixtures__/program.action_binding.bound.json";
// PG-LANG JRN8 to JRN10: the audit, recorded through the real engine and
// routes (tests/integration/test_desk_program_audit.py).
import auditDraftingFixture_ from "../__fixtures__/audit.drafting.json";
import auditBoardFixture_ from "../__fixtures__/audit.board.json";
// PG-JOURNEYS J5 "The race", recorded through the real engine and routes
// (tests/integration/test_program_race.py).
import raceParkedFixture_ from "../__fixtures__/program.race_parked.json";
import raceResumedFixture_ from "../__fixtures__/program.race_resumed.json";
import raceWonFixture_ from "../__fixtures__/program.race_won.json";
import raceRoundFixture_ from "../__fixtures__/program.race_round.json";
import raceRoundAnsweredFixture_ from "../__fixtures__/program.race_round.answered.json";
import raceRoundNextFixture_ from "../__fixtures__/program.race_round.next.json";
// PG-LANG JRN9 to JRN11: the audit's two rows and the lesson row, recorded
// through the real routes (test_desk_program_audit.py, test_desk_program_lessons.py).
import auditSecureFixture_ from "../__fixtures__/audit.secure.json";
import auditFiledFixture_ from "../__fixtures__/audit.filed.json";
import auditFixFixture_ from "../__fixtures__/audit.fix.json";
import lessonProgramFixture_ from "../__fixtures__/program.lesson.json";
import lessonKeptFixture_ from "../__fixtures__/program.lesson.kept.json";
// The owner's ruling of 2026-11-01: park stops the steps (recorded:
// tests/integration/test_program_park_steps.py).
import parkedStepsFixture_ from "../__fixtures__/program.parked_steps.json";
// JRN1 (the walk, 2026-11-01): a chained Program says which one it starts
// after (recorded: test_desk_program_plan.py, programs.chained.list.json).
import chainedListFixture_ from "../__fixtures__/programs.chained.list.json";

type Frame = { type: string; data: unknown };
type Answer = unknown | ((init?: { method?: string; json?: unknown }) => unknown);

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
  apiFetch: vi.fn(),
  apiBlob: vi.fn(),
  openRef: vi.fn(),
  openSurfaceOr: vi.fn(),
  openProjectRoom: vi.fn(),
  openPullout: vi.fn(),
  openDecisionRecord: vi.fn(),
}));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
  apiBlob: mocks.apiBlob,
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useOptionalRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));
vi.mock("../../openObject", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../openObject")>()),
  openRef: mocks.openRef,
  openDecisionRecord: mocks.openDecisionRecord,
}));
vi.mock("../../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../shell")>()),
  openSurfaceOr: mocks.openSurfaceOr,
  openProjectRoom: mocks.openProjectRoom,
}));
vi.mock("../open", () => ({ openProgram: (id: string) => mocks.openPullout(`program:${id}`) }));
// LANG5: the bar's mic. Off (as jsdom is) unless a test turns it on; then a
// capture's end answers the words the test speaks.
const mic = vi.hoisted(() => ({ supported: false, startStreamSession: vi.fn() }));
vi.mock("../../../lib/speakToFill", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/speakToFill")>()),
  speakToFillSupported: () => mic.supported,
  speakToFillUnsupportedReason: () => (mic.supported ? null : "No microphone in this browser"),
  subscribeCaptureLevel: () => () => undefined,
}));
vi.mock("../../../lib/micStreamSession", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/micStreamSession")>()),
  micStreamSupported: () => mic.supported,
  startStreamSession: mic.startStreamSession,
}));

import { ApiError as ApiError_ } from "../../../lib/api";
import { ProgramsCore as ProgramsCore_ } from "../ProgramsWindow";
import { ProgramBody as ProgramBody_ } from "../ProgramWindow";
import { RoomPrograms as RoomPrograms_, type RoomProgram } from "../RoomPrograms";
import { RoomDecisions as RoomDecisions_ } from "../RoomDecisions";
import { decodeRoomSnapshot as decodeRoomSnapshot_ } from "../../../features/project-room/model";
import { PersonPrograms as PersonPrograms_, personProgramsOf as personProgramsOf_ } from "../PersonPrograms";
import { ProgramStepLine as ProgramStepLine_, flightProgramOf as flightProgramOf_ } from "../StepLine";
import { programsLampOf as programsLampOf_, programsTodayLine as programsTodayLine_, worseLamp as worseLamp_ } from "../lamp";
import { runNoteAsProgram as runNoteAsProgram_ } from "../fromNote";
import { stationsOf as stationsOf_ } from "../model";
import type { Program, ProgramList, ProgramStep } from "../types";
import { needFace as needFace_ } from "../../needs/needsFace";
import type { NeedsYouRoomItem } from "../../needsYou";
import { DESK_APPLICATIONS as DESK_APPLICATIONS_ } from "../../applications";
import { BackSlotContext, TitleSlotContext, WingSlotContext, type WindowBack } from "../../surface";
import { SurfaceWindowHost as SurfaceWindowHost_, type SurfaceRow } from "../../components/SurfaceWindows";
import { useDesk as useDesk_ } from "../../store";
import { EMPTY_ITEMS as EMPTY_ITEMS_ } from "../../api";
import programsCss_ from "../programs.css?raw";

function subscribe(type: string, listener: (frame: Frame) => void) {
  const set = mocks.listeners.get(type) ?? new Set<(frame: Frame) => void>();
  set.add(listener);
  mocks.listeners.set(type, set);
  return () => set.delete(listener);
}
function emit(type: string, data: unknown) {
  act(() => {
    for (const listener of [...(mocks.listeners.get(type) ?? [])]) listener({ type, data });
  });
}

const clone = <T,>(value: T): T => structuredClone(value);
const list = listFixture as unknown as ProgramList;
const running = runningFixture as unknown as Program;
const yourTurn = yourTurnFixture_ as unknown as Program;
const done = doneFixture as unknown as Program;
const parked = parkedFixture as unknown as Program;
const drafting = draftingFixture as unknown as Program;
const limited = limitedFixture as unknown as Program;
const raced = raceFixture as unknown as Program;
const calls: string[] = [];

function hub(table: Record<string, Answer>) {
  mocks.apiFetch.mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
    const key = `${(init?.method ?? "GET").toUpperCase()} ${path}`;
    calls.push(init?.json !== undefined ? `${key} ${JSON.stringify(init.json)}` : key);
    if (!(key in table)) throw new ApiError_(404, "Not Found", { detail: "Not Found" });
    const answer = table[key];
    return clone(typeof answer === "function" ? (answer as (i?: typeof init) => unknown)(init) : answer);
  });
}

beforeEach(() => {
  mic.supported = false;
  mic.startStreamSession.mockReset();
  calls.length = 0;
  mocks.listeners.clear();
  mocks.apiFetch.mockReset();
  mocks.apiBlob.mockReset();
  mocks.openRef.mockReset();
  mocks.openSurfaceOr.mockReset();
  mocks.openProjectRoom.mockReset();
  mocks.openPullout.mockReset();
  mocks.openDecisionRecord.mockReset();
});
afterEach(() => cleanup());

const status = () => screen.getByTestId(/program(s)?-status$/);
/** The language, 2026-11-08: Earlier steps (the plate's right-hand verb)
 *  opens the step list under the plate; a Drafting Program shows it open. */
const openSteps = () => {
  const earlier = screen.queryByTestId("program-earlier");
  if (earlier && earlier.getAttribute("aria-expanded") !== "true") fireEvent.click(earlier);
};
/** The step list, once the Program has drawn: Earlier steps pressed open. */
const board = async () => {
  await screen.findByTestId("programs-mast");
  openSteps();
  return screen.findByTestId("programs-board");
};
const stepRow = (ordinal: number) => (openSteps(), screen.getAllByTestId("programs-step"))
  .find((row) => within(row).getByTestId("programs-step-select").textContent?.startsWith(String(ordinal)))!;
/** PG-WINDOW W3: open a step under its row (a press on the open one closes it). */
const openStep = (ordinal: number) => {
  const row = stepRow(ordinal);
  if (!row.hasAttribute("data-selected")) fireEvent.click(within(row).getByTestId("programs-step-select"));
  return screen.getByTestId("programs-step-fold");
};
const doneWhen = () => screen.getByTestId("programs-done-when");

/** The window's head as the desk host draws it: the narrow Back (the
 *  core's step word), the title slot and the wing slot. */
function InWindow({ children }: { children: ReactNode }) {
  const [title, setTitle] = useState<string | null>(null);
  const [wings, setWings] = useState<ReactNode>(null);
  const [back, setBack] = useState<WindowBack | null>(null);
  return (
    <>
      <header data-testid="window-head">
        <button type="button" data-testid="window-back" onClick={() => back?.onBack()}>{back?.label ?? "Back"}</button>
        <span data-testid="window-title">{title ?? "Programs"}</span>
        {wings}
      </header>
      <BackSlotContext.Provider value={setBack}>
        <TitleSlotContext.Provider value={setTitle}>
          <WingSlotContext.Provider value={setWings}>{children}</WingSlotContext.Provider>
        </TitleSlotContext.Provider>
      </BackSlotContext.Provider>
    </>
  );
}
const renderWindow = (ui: ReactNode) => render(<InWindow>{ui}</InWindow>);

/* ── PG-REQ: requirements, browse and adjust (REQ9 to REQ12) ─────────── */

const reqProgram = requirementsFixture as unknown as Program;
const adjust = (adjustFixture as unknown as Program);
type Answered = { program: Program; requirement_id?: string };
const reqRow = (label: string) => screen.getAllByTestId("programs-req").find((row) => row.getAttribute("data-label") === label)!;
const allRequirements = (program: Program) => [...(program.requirements ?? []), ...program.steps.flatMap((step) => step.requirements ?? [])];
const idOf = (program: Program, label: string) => allRequirements(program).find((row) => row.label === label)!.id;
const decidePath = (program: Program, label: string) => `POST /api/programs/${program.id}/requirements/${idOf(program, label)}/decide`;
/** The open menu's items (a WorkMenu radio is checked only on its choice). */
const menuWords = () => [...document.querySelectorAll("[role=menuitem],[role=menuitemradio]")].map((node) => node.textContent);
const menuItem = (name: string) => [...document.querySelectorAll<HTMLElement>("[role=menuitem],[role=menuitemradio]")].find((node) => node.textContent === name)!;

export const yourTurnFixture = yourTurnFixture_;
export const needsFixture = needsFixture_;
export const roomFixture = roomFixture_;
export const personFixture = personFixture_;
export const skipDecisionFixture = skipDecisionFixture_;
export const roomProposedFixture = roomProposedFixture_;
export const startFromFixture = startFromFixture_;
export const historyFixture = historyFixture_;
export const historyListFixture = historyListFixture_;
export const sinceMorningPrograms = sinceMorningPrograms_;
export const filteredListFixture = filteredListFixture_;
export const sendBackFixture = sendBackFixture_;
export const waivedFixture = waivedFixture_;
export const waiveRefusedFixture = waiveRefusedFixture_;
export const addedFixture = addedFixture_;
export const evidenceFixture = evidenceFixture_;
export const wordFixture = wordFixture_;
export const wordMetFixture = wordMetFixture_;
export const needsRequirementsFixture = needsRequirementsFixture_;
export const movedFixture = movedFixture_;
export const insertedFixture = insertedFixture_;
export const amendedFixture = amendedFixture_;
export const titledFixture = titledFixture_;
export const proposalsFixture = proposalsFixture_;
export const proposalsAddedFixture = proposalsAddedFixture_;
export const pageNoneFixture = pageNoneFixture_;
export const pageOpenFixture = pageOpenFixture_;
export const revokeOpenFixture = revokeOpenFixture_;
export const pageRevokedFixture = pageRevokedFixture_;
export const reachPackageFixture = reachPackageFixture_;
export const reachRevokedFixture = reachRevokedFixture_;
export const textFixture = textFixture_;
export const dreamingFixture = dreamingFixture_;
export const planningFixture = planningFixture_;
export const plannedFixture = plannedFixture_;
export const notPlannedFixture = notPlannedFixture_;
export const deliveryFailedFixture = deliveryFailedFixture_;
export const deliveryMergeFixture = deliveryMergeFixture_;
export const deliveryMergedFixture = deliveryMergedFixture_;
export const deliveryCheckFixture = deliveryCheckFixture_;
export const deliveryCheckedOpenFixture = deliveryCheckedOpenFixture_;
export const deliveryUnknownFixture = deliveryUnknownFixture_;
export const deliveryQueuedFixture = deliveryQueuedFixture_;
export const deliveryLegacyFixture = deliveryLegacyFixture_;
export const textApplyFixture = textApplyFixture_;
export const todoFixture = todoFixture_;
export const todoDoneFixture = todoDoneFixture_;
export const laneFixture = laneFixture_;
export const laneTakenFixture = laneTakenFixture_;
export const laneBackFixture = laneBackFixture_;
export const familyFixture = familyFixture_;
export const shapeFixture = shapeFixture_;
export const planFixture = planFixture_;
export const splitFixture = splitFixture_;
export const roundsFixture = roundsFixture_;
export const createProjectsFixture = createProjectsFixture_;
export const createProjectFixture = createProjectFixture_;
export const createNoRepositoryFixture = createNoRepositoryFixture_;
export const createRepositoryRequiredFixture = createRepositoryRequiredFixture_;
export const createPersonFixture = createPersonFixture_;
export const resetScreenMembers = resetScreenMembers_;
export const needsYouRecorded = needsYouRecorded_;
export const roomPrograms13 = roomPrograms13_;
export const bindingUnboundFixture = bindingUnboundFixture_;
export const bindingBoundFixture = bindingBoundFixture_;
export const auditDraftingFixture = auditDraftingFixture_;
export const auditBoardFixture = auditBoardFixture_;
export const raceParkedFixture = raceParkedFixture_;
export const raceResumedFixture = raceResumedFixture_;
export const raceWonFixture = raceWonFixture_;
export const raceRoundFixture = raceRoundFixture_;
export const raceRoundAnsweredFixture = raceRoundAnsweredFixture_;
export const raceRoundNextFixture = raceRoundNextFixture_;
export const auditSecureFixture = auditSecureFixture_;
export const auditFiledFixture = auditFiledFixture_;
export const auditFixFixture = auditFixFixture_;
export const lessonProgramFixture = lessonProgramFixture_;
export const lessonKeptFixture = lessonKeptFixture_;
export const parkedStepsFixture = parkedStepsFixture_;
export const chainedListFixture = chainedListFixture_;
export const ApiError = ApiError_;
export const ProgramsCore = ProgramsCore_;
export const ProgramBody = ProgramBody_;
export const RoomPrograms = RoomPrograms_;
export const RoomDecisions = RoomDecisions_;
export const decodeRoomSnapshot = decodeRoomSnapshot_;
export const PersonPrograms = PersonPrograms_;
export const personProgramsOf = personProgramsOf_;
export const ProgramStepLine = ProgramStepLine_;
export const flightProgramOf = flightProgramOf_;
export const programsLampOf = programsLampOf_;
export const programsTodayLine = programsTodayLine_;
export const worseLamp = worseLamp_;
export const runNoteAsProgram = runNoteAsProgram_;
export const stationsOf = stationsOf_;
export const needFace = needFace_;
export const DESK_APPLICATIONS = DESK_APPLICATIONS_;
export const SurfaceWindowHost = SurfaceWindowHost_;
export const useDesk = useDesk_;
export const EMPTY_ITEMS = EMPTY_ITEMS_;
export const programsCss = programsCss_;
export {
  mocks,
  mic,
  emit,
  clone,
  list,
  running,
  yourTurn,
  done,
  parked,
  drafting,
  limited,
  raced,
  calls,
  hub,
  status,
  stepRow,
  openStep,
  openSteps,
  board,
  doneWhen,
  renderWindow,
  reqProgram,
  adjust,
  reqRow,
  allRequirements,
  decidePath,
  menuWords,
  menuItem,
};
export type {
  Answer,
  Answered,
  NeedsYouRoomItem,
  Program,
  ProgramList,
  ProgramStep,
  RoomProgram,
  SurfaceRow,
};

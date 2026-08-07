// HS-100-07 — Speak: the application opens ON the job.
// Composed from InstrumentStrip, AimRow, UtteranceWell, ResultPanel
// and the useSpeakDeck hook.
import { useAnnounce } from "./shared";
import { useSpeakDeck } from "./useSpeakDeck";
import { InstrumentStrip } from "./InstrumentStrip";
import { AimRow } from "./AimRow";
import { UtteranceWell } from "./UtteranceWell";
import { ResultPanel } from "./ResultPanel";

export function SpeakFace() {
  const announce = useAnnounce();
  const deck = useSpeakDeck(announce);

  return (
    <div className="speak-face">
      <InstrumentStrip
        micState={deck.micState}
        onMicState={deck.setMicState}
        level={deck.level}
        onLevel={deck.setLevel}
        onReleased={deck.onReleased}
        onFailure={() => {}}
        releasedAt={deck.releasedAt}
        phase={deck.phase}
        setPhase={deck.setPhase}
        setLandedMs={deck.setLandedMs}
        setRefusal={deck.setRefusal}
        announce={announce}
        openMic={deck.openMic}
        toggleOpenMic={deck.toggleOpenMic}
        captureSupported={deck.captureSupported}
        captureReason={deck.captureReason}
        micPhase={deck.micPhase}
        pipelineOn={deck.pipelineOn}
        readinessTarget={deck.readinessTarget}
        readinessConfig={deck.readinessConfig}
        landedMs={deck.landedMs}
        refusal={deck.refusal}
        activeState={deck.activeState}
      />
      <AimRow
        aim={deck.aim}
        onAimChange={deck.pickAim}
        rehearse={deck.rehearse}
        onRehearseChange={deck.setRehearse}
      />
      <UtteranceWell
        utterance={deck.utterance}
        setUtterance={deck.setUtterance}
        projectRoot={deck.projectRoot}
        setProjectRoot={deck.setProjectRoot}
        busy={deck.busy}
        error={deck.error}
        previewOnly={deck.previewOnly}
        actions={deck.actions}
        targets={deck.targets}
        targetId={deck.targetId}
        onRun={() => void deck.run()}
        onDeliver={(text) => void deck.deliver(text)}
        onRunElsewhere={(id) => void deck.runElsewhere(id)}
        onKeepDraft={() => void deck.keepDraft()}
      />
      {deck.result ? (
        <ResultPanel
          result={deck.result}
          verdict={deck.verdict}
          setVerdict={deck.setVerdict}
          correctionKind={deck.correctionKind}
          setCorrectionKind={deck.setCorrectionKind}
          correctionValue={deck.correctionValue}
          setCorrectionValue={deck.setCorrectionValue}
          busy={deck.busy}
          onTeach={() => void deck.teach()}
          announce={announce}
        />
      ) : null}
    </div>
  );
}

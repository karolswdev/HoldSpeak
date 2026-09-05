import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { renderHeroSlot } from "./core-layout";
import { FoldGadget } from "../../desk/surface/gadgets";
import { SurfaceRow, SurfaceRows, SurfaceSection } from "../../desk/surface/Surface";

export function RuntimeDocsCore({ hero }: CoreProps) {
  return (
    <>
      {renderHeroSlot(hero, null)}
      <SurfaceSection label="Runtime reference">
        <FoldGadget title="Basic voice typing" open>
          <SurfaceRows>
            <SurfaceRow title="INSTALL" detail="uv pip install -e '.[whisper]'" />
            <SurfaceRow title="PIPELINE" detail="LOCAL TRANSCRIBE" />
          </SurfaceRows>
        </FoldGadget>
        <FoldGadget title="Apple Silicon with MLX">
          <SurfaceRows>
            <SurfaceRow title="INSTALL" detail="uv pip install -e '.[dictation-mlx]'" />
            <SurfaceRow title="MODEL PATH" detail="~/Models/mlx/" />
            <SurfaceRow title="SELECT" detail="DICTATION · RUNTIME" />
          </SurfaceRows>
        </FoldGadget>
        <FoldGadget title="Local GGUF with llama.cpp">
          <SurfaceRows>
            <SurfaceRow title="INSTALL" detail="uv pip install -e '.[dictation-llama]'" />
            <SurfaceRow title="MODEL PATH" detail="~/Models/gguf/" />
            <SurfaceRow title="VALUE" detail="FULL MODEL PATH" />
          </SurfaceRows>
        </FoldGadget>
        <FoldGadget title="OpenAI-compatible endpoint">
          <SurfaceRows>
            <SurfaceRow title="INSTALL" detail="uv pip install -e '.[dictation-openai]'" />
            <SurfaceRow title="DESTINATION" detail="SERVER URL · MODEL" />
            <SurfaceRow title="KEY ENV" detail="HOLDSPEAK_PROFILE_<ID>_KEY" />
          </SurfaceRows>
        </FoldGadget>
      </SurfaceSection>
      <SurfaceSection label="Verify">
        <SurfaceRows>
          <SurfaceRow
            title="SETUP"
            detail={<Button dense variant="ghost" onClick={() => openSurfaceOr("configure-setup", "/setup")}>Run runtime test</Button>}
          />
          <SurfaceRow
            title="DICTATION"
            detail={<Button dense variant="ghost" onClick={() => openSurfaceOr("dictate", "/dictation")}>Check readiness</Button>}
          />
          <SurfaceRow title="TRY IT" detail="NO-TYPE DRY TEST" />
          <SurfaceRow title="REWRITE" detail="ENABLE AFTER VERIFY" />
        </SurfaceRows>
      </SurfaceSection>
      <SurfaceFooter />
    </>
  );
}

// HS-95-08 — the runtime setup guide, hosted anywhere.
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import { Disclosure, InlineMessage } from "../../components/signal/Signal";
import { SurfaceCode, SurfaceSection } from "../../desk/surface/Surface";

export function RuntimeDocsCore({ hero }: CoreProps) {
  return (
    <>
      {hero ? hero(null) : null}
      <InlineMessage tone="info">
        API keys are environment variables on the hub. They never belong in a
        browser field or profile response.
      </InlineMessage>
      <SurfaceSection label="Choose a runtime">
        <Disclosure title="Basic voice typing" open>
          <p>
            Install HoldSpeak and a Whisper backend. Leave the dictation LLM
            pipeline disabled to transcribe and type locally.
          </p>
          <SurfaceCode>uv pip install -e '.[whisper]'</SurfaceCode>
        </Disclosure>
        <Disclosure title="Apple Silicon with MLX">
          <p>
            Put an MLX model under <code>~/Models/mlx/</code>, then choose it
            during arrival or in Dictation → Runtime.
          </p>
          <SurfaceCode>uv pip install -e '.[dictation-mlx]'</SurfaceCode>
        </Disclosure>
        <Disclosure title="Local GGUF with llama.cpp">
          <p>
            Put a GGUF file under <code>~/Models/gguf/</code> and select its
            full path.
          </p>
          <SurfaceCode>uv pip install -e '.[dictation-llama]'</SurfaceCode>
        </Disclosure>
        <Disclosure title="OpenAI-compatible endpoint">
          <p>
            Create a Runs on destination with the server URL and model. If it
            needs a key, set <code>HOLDSPEAK_PROFILE_&lt;ID&gt;_KEY</code> on the
            hub.
          </p>
          <SurfaceCode>uv pip install -e '.[dictation-openai]'</SurfaceCode>
        </Disclosure>
      </SurfaceSection>
      <SurfaceSection label="Verify">
        <ol>
          <li>
            Open{" "}
            <button
              type="button"
              className="btn-link"
              onClick={() => openSurfaceOr("configure-setup", "/setup")}
            >
              Setup
            </button>{" "}
            and run the runtime test.
          </li>
          <li>
            Open{" "}
            <button
              type="button"
              className="btn-link"
              onClick={() => openSurfaceOr("dictate", "/dictation")}
            >
              Dictation
            </button>{" "}
            and check Readiness.
          </li>
          <li>Use Try it to run one no-type dry test.</li>
          <li>Only then enable rewrite stages for daily dictation.</li>
        </ol>
      </SurfaceSection>
    </>
  );
}

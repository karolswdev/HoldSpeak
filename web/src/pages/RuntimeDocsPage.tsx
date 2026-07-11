import { Link } from "react-router-dom";
import { Disclosure, InlineMessage, Panel } from "../components/signal/Signal";
import { PageHero } from "./pageSupport";

export default function RuntimeDocsPage() {
  return (
    <article className="page-wrap docs-page">
      <PageHero eyebrow="Local guide" title="Dictation runtime setup">
        Choose one intelligence path. Basic voice typing works without an LLM;
        rewrites and routing depth need a runtime.
      </PageHero>
      <InlineMessage tone="info">
        API keys are environment variables on the hub. They never belong in a
        browser field or profile response.
      </InlineMessage>
      <Panel
        title="Choose a runtime"
        eyebrow="One Runs on destination, explicit reach"
      >
        <Disclosure title="Basic voice typing" open>
          <p>
            Install HoldSpeak and a Whisper backend. Leave the dictation LLM
            pipeline disabled to transcribe and type locally.
          </p>
          <pre className="code-block">uv pip install -e '.[whisper]'</pre>
        </Disclosure>
        <Disclosure title="Apple Silicon with MLX">
          <p>
            Put an MLX model under <code>~/Models/mlx/</code>, then choose it
            during arrival or in Dictation → Runtime.
          </p>
          <pre className="code-block">uv pip install -e '.[dictation-mlx]'</pre>
        </Disclosure>
        <Disclosure title="Local GGUF with llama.cpp">
          <p>
            Put a GGUF file under <code>~/Models/gguf/</code> and select its
            full path.
          </p>
          <pre className="code-block">
            uv pip install -e '.[dictation-llama]'
          </pre>
        </Disclosure>
        <Disclosure title="OpenAI-compatible endpoint">
          <p>
            Create a Runtime Profile with the server URL and model. If it needs
            a key, set <code>HOLDSPEAK_PROFILE_&lt;ID&gt;_KEY</code> on the hub.
          </p>
          <pre className="code-block">
            uv pip install -e '.[dictation-openai]'
          </pre>
        </Disclosure>
      </Panel>
      <Panel title="Verify" eyebrow="Honest health">
        <ol>
          <li>
            Open <Link to="/setup">Setup</Link> and run the runtime test.
          </li>
          <li>
            Open <Link to="/dictation">Dictation</Link> and check Readiness.
          </li>
          <li>Use Try it to run one no-type dry test.</li>
          <li>Only then enable rewrite stages for daily dictation.</li>
        </ol>
      </Panel>
    </article>
  );
}

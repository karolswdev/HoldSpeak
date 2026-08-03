import type { VoiceGrammar, VoiceIntentDef } from "../grammar";

const selected = ({ hasSelection }: { hasSelection: boolean }) =>
  hasSelection ? null : "Select text first";

const editorIntent = (
  id: string,
  patterns: RegExp[],
  verbId: string | null,
  requiresLLM = false,
  ghost = selected,
): VoiceIntentDef => ({
  id,
  patterns,
  requiresLLM,
  verbId,
  extract: () => ({}),
  ghost,
});

export const editorVoiceGrammar: VoiceGrammar = {
  surfaceKind: "editor",
  intents: [
    editorIntent("bold", [/\bbold\s+(that|this|it)\b/i], "editor.bold"),
    editorIntent("italic", [/\bitalic\s+(that|this|it)\b/i], "editor.italic"),
    editorIntent("heading", [/\b(new\s+)?heading\b/i], "editor.heading", false, () => null),
    editorIntent("list", [/\bbullet\s+list\b/i], "editor.list", false, () => null),
    editorIntent("rewrite", [/\b(make|rewrite)\b.*\b(concise|shorter|better|clearer)\b/i], "editor.rewrite", true),
    editorIntent("expand", [/\bexpand\b/i], "editor.expand", true),
    editorIntent("continue", [/\bcontinue\b/i], "editor.continue", true, () => null),
    editorIntent("readback", [/\bread\s+(this|it|that)\s+back\b/i], "editor.readback"),
  ],
  dictationFallback: true,
};

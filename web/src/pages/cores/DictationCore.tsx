import type { CoreProps } from "./core-types";
import { SpeakFace } from "./dictation/SpeakFace";

/** Speak is one working object; preferences live in Settings › Speak. */
export function DictationCore(_props: CoreProps) {
  return <SpeakFace />;
}

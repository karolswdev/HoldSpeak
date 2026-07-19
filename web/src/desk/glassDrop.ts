// HS-101 B7 — drag-and-drop is a system verb (DESIGN_SYSTEM.md, "The
// interior canon", OS territory §4). The decision table for files
// dropped through the glass: what imports, what refuses BY NAME.
// Mirrors the hub's own suffix routing (holdspeak/transcript_parse.py
// TRANSCRIPT_SUFFIXES + holdspeak/meeting_import.py FFMPEG_SUFFIXES).

export const TRANSCRIPT_SUFFIXES = [".vtt", ".srt", ".txt"] as const;
export const AUDIO_SUFFIXES = [
  ".wav",
  ".mp3",
  ".m4a",
  ".aac",
  ".ogg",
  ".oga",
  ".opus",
  ".flac",
  ".webm",
  ".mp4",
] as const;

export type GlassFileKind = "transcript" | "audio";

export function glassFileKind(name: string): GlassFileKind | null {
  const dot = name.lastIndexOf(".");
  if (dot < 0) return null;
  const suffix = name.slice(dot).toLowerCase();
  if ((TRANSCRIPT_SUFFIXES as readonly string[]).includes(suffix)) {
    return "transcript";
  }
  if ((AUDIO_SUFFIXES as readonly string[]).includes(suffix)) {
    return "audio";
  }
  return null;
}

/** A refused drop names why (canon rule 4) — never a silent no-op. */
export function glassFileRefusal(name: string): string {
  const dot = name.lastIndexOf(".");
  const suffix = dot >= 0 ? name.slice(dot).toLowerCase() : "";
  return suffix
    ? `Can't import ${suffix} — transcript (.vtt .srt .txt) or audio only`
    : "Can't import a file without a type — transcript or audio only";
}

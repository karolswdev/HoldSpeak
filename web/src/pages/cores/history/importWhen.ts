/* Capture C3: "When was this?" for an imported file.
 *
 * The form fills the meeting's start from the file itself, in this order:
 * a date in a VTT or SRT header, a date in the file name, then the file's
 * modified time (`File.lastModified`). The owner sees the value and can
 * change it before Import (HS-201-10: a hidden guess dated a June copy of a
 * WAV in June; a shown, editable value does not). */

const DATE_RE =
  /((?:19|20)\d\d)[-_.]?(0[1-9]|1[0-2])[-_.]?(0[1-9]|[12]\d|3[01])(?:[T _-]+([01]\d|2[0-3])[:.h-]?([0-5]\d))?/;

/** A local Date from the first date (and optional time) in `text`. */
export function dateIn(text: string): Date | null {
  const m = DATE_RE.exec(text);
  if (!m) return null;
  const [, y, mo, d, h, mi] = m;
  const when = new Date(Number(y), Number(mo) - 1, Number(d), h ? Number(h) : 9, mi ? Number(mi) : 0);
  // 2026-02-31 rolls into March: not a date the file said.
  return when.getMonth() === Number(mo) - 1 && when.getDate() === Number(d) ? when : null;
}

/** The text before the first cue of a VTT or SRT file: its header. */
export function cueHeader(text: string): string {
  const arrow = text.indexOf("-->");
  const head = arrow < 0 ? text : text.slice(0, arrow);
  // The cue's own timing line starts the cue; drop it from the header.
  return head.replace(/[^\n]*$/, "");
}

async function readHead(file: File): Promise<string> {
  const blob = file.slice(0, 4096);
  if (typeof blob.text === "function") return blob.text();
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => resolve("");
    reader.readAsText(blob);
  });
}

/** When the file says it was: header date, then name date, then modified time. */
export async function whenFromFile(file: File): Promise<Date | null> {
  if (/\.(vtt|srt)$/i.test(file.name)) {
    try {
      const fromHeader = dateIn(cueHeader(await readHead(file)));
      if (fromHeader) return fromHeader;
    } catch {
      /* an unreadable header falls through to the name */
    }
  }
  const fromName = dateIn(file.name);
  if (fromName) return fromName;
  return file.lastModified > 0 ? new Date(file.lastModified) : null;
}

/** A Date as the value of a `datetime-local` input (local time, minutes). */
export function toDatetimeLocal(when: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${when.getFullYear()}-${pad(when.getMonth() + 1)}-${pad(when.getDate())}T${pad(when.getHours())}:${pad(when.getMinutes())}`;
}

/** The `started_at_ms` the hub takes, or null for an empty or bad value. */
export function startedAtMs(value: string): number | null {
  if (!value) return null;
  const ms = new Date(value).getTime();
  return Number.isFinite(ms) ? ms : null;
}

/** The kinds the import takes (the file picker's filter). */
export const IMPORT_ACCEPT = "audio/*,.wav,.mp3,.m4a,.ogg,.flac,.vtt,.srt,.txt";

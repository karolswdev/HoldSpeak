/** The kit's words (STATECHIP, 2026-10-29): every drawn state, token and
 *  fold title reads in sentence case. The kit species (StateChip, Token,
 *  FoldGadget, StatusStrip, StatusBar) send their text through
 *  `stateWords`, so a caller that still passes a caps token draws sentence
 *  case. Acronyms, units and product short names in `KEEP_CAPS` keep their
 *  capitals; ids and codes opt out at the species (`code`). */
import { Children, isValidElement, type ReactNode } from "react";

export const KEEP_CAPS: ReadonlySet<string> = new Set([
  "PR", "CI", "AI", "ID", "OK", "LAN", "MCP", "API", "CLI", "URL", "PDF", "ADR", "UI",
  "MLX", "GGUF", "GB", "MB", "KB", "TB", "SSH", "HTTP", "HTTPS", "PCI-DSS", "LLM", "CPU", "GPU", "RAM", "OS",
  "UTC", "JSON", "CSV", "MD", "HTML", "SQL", "DB", "USB", "VPN", "DNS", "IP", "TLS", "ASR", "TTS",
  "STT", "SDK", "CC", "TODO", "MVP", "QA", "UX", "PM", "AM", "GMT", "KPI", "SLA",
  "SLO", "OKR", "SSO", "JWT", "MLX-LM", "ONNX", "WAV", "MP3",
]);

/** Proper names a caps token may carry: they draw in their own spelling
 *  wherever they stand (`CLONES FROM GITHUB` → `Clones from GitHub`,
 *  `OCT 28` → `Oct 28`). */
const NAMES: Record<string, string> = {
  HOLDSPEAK: "HoldSpeak", GITHUB: "GitHub", GH: "gh", JIRA: "Jira", CONFLUENCE: "Confluence", SLACK: "Slack",
  CLAUDE: "Claude", CODEX: "Codex", OLLAMA: "Ollama", WHISPER: "Whisper", TMUX: "tmux", OPENAI: "OpenAI",
  ANTHROPIC: "Anthropic", GEMINI: "Gemini", MACOS: "macOS", ICLOUD: "iCloud", GOOGLE: "Google",
  TAILSCALE: "Tailscale", TELNYX: "Telnyx", PYNPUT: "pynput", PYTHON: "Python", KEYCHAIN: "Keychain", ACLI: "acli", GIT: "git", MLXLM: "mlx-lm", LMSTUDIO: "LM Studio",
  QWEN: "Qwen", LLAMA: "Llama", MISTRAL: "Mistral", PARAKEET: "Parakeet", OUTLOOK: "Outlook", GMAIL: "Gmail",
  ...Object.fromEntries(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "SEPT", "OCT", "NOV", "DEC",
      "MON", "TUE", "TUES", "WED", "THU", "THUR", "THURS", "FRI", "SAT", "SUN",
      "JANUARY", "FEBRUARY", "MARCH", "APRIL", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
      "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"].map((w) => [w, w.charAt(0) + w.slice(1).toLowerCase()]),
  ),
};

/** A citation's kind plate keeps its capitals before the cited date
 *  (`DEC 10-11`, `MTG 09-07 · 11:31`): the plate is an id, not a word. */
const REF_KINDS = new Set(["DEC", "MTG", "ACT", "CMT", "REF"]);
const REF_TAIL = /^\s+\d\d-\d\d\b/;

const CLIPPED: Record<string, string> = { CANT: "CANNOT", DONT: "DO NOT", WONT: "WILL NOT", ISNT: "IS NOT" };

const LINK_WORDS = new Set(["ON", "FOR", "WITH", "BY", "FROM"]);
const COMMON_AFTER_LINK = new Set(["YOUR", "YOU", "THE", "A", "AN", "IT", "THIS", "THAT", "ME", "HIM", "HER", "THEM", "REVIEW", "TRACK", "HOLD", "TIME", "OWNER", "AGENT", "HUB", "SYSTEM", "DEFAULT", "SCHEDULE", "NOW", "NAME", "DATE", "HAND", "DEVICE", "DISK", "FILE", "BRIEF", "PAPER", "THIS", "EACH", "EVERY", "ALL", "ANY"]);

/** A wire state word in sentence case, per ` · ` part: the part's first
 *  word keeps a capital, every later ALL-CAPS word of two letters or
 *  more is lower case; mixed-case words (names), acronyms (`PR`, `CI`,
 *  `LAN`), numbers, times and ids stay as they are (`OVERDUE · 23 DAYS` →
 *  `Overdue · 23 days`, `PR OPEN` → `PR open`, `PROPOSED · Standup` →
 *  `Proposed · Standup`). With `lead: false` the text continues a token
 *  (it follows a number or words), so its first part takes no capital. */
export function stateWords(label: string, keep: ReadonlySet<string> = KEEP_CAPS, lead = true): string {
  return label
    .split(" · ")
    .map((part, index) => {
      let first = lead || index > 0;
      let afterLink = false;
      let prev = "";
      return part.replace(/[^\s]+/g, (word, offset: number) => {
        const prevWord = prev;
        prev = word;
        const leadWord = first;
        const named = afterLink && !COMMON_AFTER_LINK.has(word);
        first = false;
        afterLink = LINK_WORDS.has(word);
        // Punctuation around a word stays (`(PR)`, `FAILED,`, `“NOW”`).
        const m = /^([^A-Za-z0-9]*)([A-Z][A-Z'’-]*[A-Z])([^A-Za-z0-9]*)$/.exec(word);
        if (!m) return word;
        const [, before, wire, after] = m;
        // A wire's clipped word (`CANT CHECK`) reads in full (`Cannot check`).
        const core = CLIPPED[wire] ?? wire;
        if (keep.has(core)) return word;
        if (REF_KINDS.has(core) && !before && !after && REF_TAIL.test(part.slice(offset + word.length))) return word;
        if (core === "CODE" && prevWord === "CLAUDE") return before + "Code" + after;
        if (NAMES[core]) return before + NAMES[core] + after;
        // `PRS` → `PRs`: an acronym's plural keeps the acronym.
        if (core.endsWith("S") && keep.has(core.slice(0, -1))) return `${before}${core.slice(0, -1)}s${after}`;
        // `WAITING ON PRIYA`: the word after a link word is a name; it keeps
        // its capital (`Waiting on Priya`, `Waiting on your review`).
        const low = core.toLowerCase();
        return before + (leadWord || named ? core.charAt(0) + low.slice(1) : low) + after;
      });
    })
    .join(" · ");
}

/** The species' children in sentence case: each run of plain text (strings
 *  and numbers, joined) goes through `stateWords`; elements stay as they
 *  are. A run that follows other text takes no lead capital (`3 MORE` →
 *  `3 more`); a run after an element (a glyph, a lamp) leads. */
export function sentenceChildren(children: ReactNode, keep: ReadonlySet<string> = KEEP_CAPS): ReactNode {
  if (typeof children === "string") return stateWords(children, keep);
  if (children == null || typeof children !== "object") return children;
  const out: ReactNode[] = [];
  let run: string | null = null;
  let sawText = false;
  const flush = () => {
    if (run == null) return;
    out.push(stateWords(run, keep, !sawText));
    sawText = true;
    run = null;
  };
  for (const child of Children.toArray(children)) {
    if (typeof child === "string" || typeof child === "number") {
      run = (run ?? "") + String(child);
    } else {
      flush();
      out.push(child);
      if (!isValidElement(child)) sawText = true;
    }
  }
  flush();
  return out;
}

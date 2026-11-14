/** PHILO-15 lane 12 (B30, Astra r1): how an object's name is set in a
 *  label of `perLine` characters (the desk label is monospaced) and at most
 *  `lines` lines.
 *
 *  Break priority: between words (spaces) first. A word that cannot fit on
 *  a line breaks after a join (`_ - . / :`). Paths break at separators and
 *  keep their basename and extension together. Other words never split a run of
 *  letters. When the name needs more lines than the label has, it is cut in
 *  the MIDDLE: the start stays, then `…`, then the end (the last word, or
 *  the last part of a single long word). Two names that differ only at the
 *  end ("Payments ledger cutover v2" / "… v3") stay different on the glass.
 *  A word with no join that is longer than a line is never split: it is cut
 *  with `…`. Returns the lines, each at most `perLine` characters. */
export function fitName(
  name: string,
  perLine: number,
  lines: number,
  /** The label's real measure (a proportional face): true when the line
   *  fits. Absent: a line fits at `perLine` characters (monospaced). */
  fits: (line: string) => boolean = (line) => line.length <= perLine,
  /** `end` (the floor, owner 2026-11-08): whole words, then ONE ellipsis at
   *  the end; never a cut in the middle. Default `middle`, as above. */
  cut: "middle" | "end" | "path" = "middle",
): string[] {
  const text = name.replace(/\s+/g, " ").trim();
  if (!text || perLine < 4 || lines < 1) return [text];
  const whole = layout(text, fits);
  if (whole && whole.length <= lines) return whole;
  if (cut === "end") return endCut(text, lines, fits);

  // The end that must stay: the last word, or the end of one long word.
  const words = text.split(" ");
  const last = words[words.length - 1];
  const capTail = Math.max(2, perLine - 2);
  let tail: string;
  let joiner: string;
  if (words.length > 1 && last.length <= capTail && fits(`… ${last}`)) {
    tail = last;
    joiner = " ";
  } else {
    // One long word (or a last word too long to keep whole): keep its last
    // join-piece when it fits, else its last characters.
    const pieces = joinPieces(last);
    const lastPiece = pieces[pieces.length - 1];
    tail = (lines > 1 || lastPiece.length >= Math.min(8, capTail)) && lastPiece.length <= capTail && pieces.length > 1 && fits(`…${lastPiece}`) ? lastPiece : last.slice(-Math.max(2, Math.floor(perLine / 2)));
    joiner = "";
  }
  if (cut === "path" && joiner === "" && joinPieces(last).length > 1) {
    const wanted = last.length - tail.length;
    // A middle cut may keep a suffix of a long basename. Its word joins
    // differ from line breaks, which keep the basename and extension together.
    const starts = [0, ...Array.from(last.matchAll(/[_\-./:\\](?=.)/g), match => match.index + 1)];
    const start = starts.find(start => start >= wanted);
    if (start !== undefined) tail = last.slice(start);
  }
  const headSource = text.slice(0, text.length - tail.length).replace(/\s+$/, "");
  for (let k = cut === "path" ? headSource.length : 0; k >= 1; k--) {
    if (!/[\s_\-./:]/.test(headSource[k - 1])) continue;
    const candidate = `${headSource.slice(0,k)}…${joiner}${tail}`;
    const set = layout(candidate, fits);
    if (set && set.length <= lines) return set;
  }
  const middle = longest(headSource.length, (k) => {
    const head = headSource.slice(0, k).replace(/[\s]+$/, "");
    if (!head) return null;
    const set = layout(`${head}…${joiner}${tail}`, fits);
    return set && set.length <= lines ? set : null;
  });
  if (middle) return middle;
  // Nothing of the start fits beside the end: the end alone, cut.
  let endOnly = `…${tail}`.slice(0, perLine);
  while (endOnly.length > 2 && !fits(endOnly)) endOnly = endOnly.slice(0, -1);
  return [endOnly];
}

/** The longest start that fits, by halving: a 4,000-character name took
 *  4,000 measured layouts per fit when every length was tried in turn, and
 *  the page stopped answering. A shorter start never fits worse, so the
 *  halving finds the same cut. */
function longest(max: number, at: (length: number) => string[] | null): string[] | null {
  let low = 1, high = max, best: string[] | null = null;
  while (low <= high) {
    const mid = (low + high) >> 1, set = at(mid);
    if (set) { best = set; low = mid + 1; } else high = mid - 1;
  }
  return best;
}

/** A word's pieces: it may break after each `_ - . / :` join (the join stays
 *  at the end of its piece). */
function joinPieces(word: string): string[] {
  // A path keeps its basename and extension together on the next line.
  if (/[/\\]/.test(word)) return word.split(/(?<=[/\\])(?=.)/);
  if (nameIsFile(word) && word.includes(".")) return [word];
  return word.split(/(?<=[_\-./:])(?=.)/);
}

/** Greedy layout with the break priority above; null when a piece with no
 *  join is longer than a line (it would have to split inside letters). */
function layout(text: string, fits: (line: string) => boolean): string[] | null {
  const out: string[] = [];
  let line = "";
  const push = () => {
    if (line) out.push(line);
    line = "";
  };
  for (const word of text.split(" ")) {
    const spaced = line ? `${line} ${word}` : word;
    if (fits(spaced)) {
      line = spaced;
      continue;
    }
    if (fits(word)) {
      push();
      line = word;
      continue;
    }
    // A word longer than a line: it starts its own line and breaks at its joins.
    push();
    for (const piece of joinPieces(word)) {
      if (!fits(piece)) return null;
      if (fits(line + piece)) line += piece;
      else {
        push();
        line = piece;
      }
    }
  }
  push();
  return out;
}

/** The end cut: the most whole words that fit `lines` lines with `…` after
 *  the last one. A first word too long for every line is cut by letters.
 *  A name is never only `…` (owner's live desk 2026-11-13: three Needs you
 *  rows read "…" because their first word was a long path): when no letter
 *  fits beside the ellipsis, the first letter still stands before it. */
function endCut(text: string, lines: number, fits: (line: string) => boolean): string[] {
  const words = text.split(" ");
  for (let k = words.length - 1; k >= 1; k--) {
    const head = words.slice(0, k).join(" ").replace(/[\s,;:·–—-]+$/, "");
    if (!head) continue;
    const set = layout(`${head}…`, fits);
    if (set && set.length <= lines) return set;
  }
  // Prefer a join on the final available line before cutting a run of letters.
  for (let n = text.length - 1; n >= 1; n--) {
    if (!/[_\-./:]/.test(text[n - 1])) continue;
    const set = layout(`${text.slice(0, n)}…`, fits);
    if (set && set.length === lines) return set;
  }
  const byLetters = longest(text.length - 1, (n) => {
    const set = layout(`${text.slice(0, n).trimEnd()}…`, fits);
    return set && set.length <= lines ? set : null;
  });
  if (byLetters) return byLetters;
  return [`${text.slice(0, 1)}…`];
}

interface TextMeasure {
  /** One average character's width (the heuristic line length). */
  average: number;
  width(text: string): number;
}
const measures = new Map<string, TextMeasure>();
let noCanvas = false;
/** The label font's measure; null when there is no canvas to measure with
 *  (jsdom), and the CSS break priority sets the label instead. */
export function textMeasure(st: CSSStyleDeclaration): TextMeasure | null {
  const font = `${st.fontStyle || "normal"} ${st.fontWeight} ${st.fontSize} ${st.fontFamily}`;
  const cached = measures.get(font);
  if (cached) return cached;
  if (noCanvas) return null;
  let measure: TextMeasure | null = null;
  try {
    const ctx = document.createElement("canvas").getContext("2d");
    if (!ctx) noCanvas = true;
    if (ctx) {
      ctx.font = font;
      const sample = "Payments ledger cutover";
      const average = ctx.measureText(sample).width / sample.length;
      if (average > 0) measure = { average, width: (text) => ctx.measureText(text).width };
    }
  } catch {
    noCanvas = true;
    measure = null;
  }
  // Keep a measure only once the faces are in (a fallback face measures wrong).
  if (measure && (!document.fonts || document.fonts.status === "loaded")) measures.set(font, measure);
  return measure;
}

/** Recognize path/code text for name fitting and the initials fallback, never object kind. */
export function nameIsFile(name: string): boolean {
  const first = name.trim().split(/\s/, 1)[0];
  // A dot counts only as a file extension at the end of the word ("node.js",
  // "RoomList.tsx:"): "J.R." and "St.John" are people.
  return first.startsWith("`") || /^~|[/\\]|[a-z0-9]_[a-z0-9]|[a-z0-9_-]{2,}\.[a-z][a-z0-9]{0,4}[:,]?$/i.test(first) && !/^[A-Z][a-z]+\.[A-Z]/.test(first);
}

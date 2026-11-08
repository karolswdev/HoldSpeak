/** PHILO-15 lane 12 (B30, Astra r1): how an object's name is set in a
 *  label of `perLine` characters (the desk label is monospaced) and at most
 *  `lines` lines.
 *
 *  Break priority: between words (spaces) first. A word that cannot fit on
 *  a line breaks after one of its joins (`_ - . /`), never inside a run of
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
  cut: "middle" | "end" = "middle",
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
    tail = lastPiece.length <= capTail && pieces.length > 1 && fits(`…${lastPiece}`) ? lastPiece : last.slice(-Math.max(2, Math.floor(perLine / 2)));
    joiner = "";
  }
  const headSource = text.slice(0, text.length - tail.length).replace(/\s+$/, "");
  for (let k = headSource.length; k >= 1; k--) {
    const head = headSource.slice(0, k).replace(/[\s]+$/, "");
    if (!head) continue;
    const candidate = `${head}…${joiner}${tail}`;
    const set = layout(candidate, fits);
    if (set && set.length <= lines) return set;
  }
  // Nothing of the start fits beside the end: the end alone, cut.
  let endOnly = `…${tail}`.slice(0, perLine);
  while (endOnly.length > 2 && !fits(endOnly)) endOnly = endOnly.slice(0, -1);
  return [endOnly];
}

/** A word's pieces: it may break after each `_ - . /` join (the join stays
 *  at the end of its piece). */
function joinPieces(word: string): string[] {
  return word.split(/(?<=[_\-./])(?=.)/);
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
 *  the last one. A first word too long for every line is cut by letters. */
function endCut(text: string, lines: number, fits: (line: string) => boolean): string[] {
  const words = text.split(" ");
  for (let k = words.length - 1; k >= 1; k--) {
    const head = words.slice(0, k).join(" ").replace(/[\s,;:·–—-]+$/, "");
    if (!head) continue;
    const set = layout(`${head}…`, fits);
    if (set && set.length <= lines) return set;
  }
  for (let n = text.length - 1; n >= 1; n--) {
    const set = layout(`${text.slice(0, n).trimEnd()}…`, fits);
    if (set && set.length <= lines) return set;
  }
  return ["…"];
}

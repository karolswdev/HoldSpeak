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
export function fitName(name: string, perLine: number, lines: number): string[] {
  const text = name.replace(/\s+/g, " ").trim();
  if (!text || perLine < 4 || lines < 1) return [text];
  const whole = layout(text, perLine);
  if (whole && whole.length <= lines) return whole;

  // The end that must stay: the last word, or the end of one long word.
  const words = text.split(" ");
  const last = words[words.length - 1];
  const capTail = Math.max(2, perLine - 2);
  let tail: string;
  let joiner: string;
  if (words.length > 1 && last.length <= capTail) {
    tail = last;
    joiner = " ";
  } else {
    // One long word (or a last word too long to keep whole): keep its last
    // join-piece when it fits, else its last characters.
    const pieces = joinPieces(last);
    const lastPiece = pieces[pieces.length - 1];
    tail = lastPiece.length <= capTail && pieces.length > 1 ? lastPiece : last.slice(-Math.max(2, Math.floor(perLine / 2)));
    joiner = "";
  }
  const headSource = text.slice(0, text.length - tail.length).replace(/\s+$/, "");
  for (let k = headSource.length; k >= 1; k--) {
    const head = headSource.slice(0, k).replace(/[\s]+$/, "");
    if (!head) continue;
    const candidate = `${head}…${joiner}${tail}`;
    const set = layout(candidate, perLine);
    if (set && set.length <= lines) return set;
  }
  // Nothing of the start fits beside the end: the end alone, cut.
  return [`…${tail}`.slice(0, perLine)];
}

/** A word's pieces: it may break after each `_ - . /` join (the join stays
 *  at the end of its piece). */
function joinPieces(word: string): string[] {
  return word.split(/(?<=[_\-./])(?=.)/);
}

/** Greedy layout with the break priority above; null when a piece with no
 *  join is longer than a line (it would have to split inside letters). */
function layout(text: string, perLine: number): string[] | null {
  const out: string[] = [];
  let line = "";
  const push = () => {
    if (line) out.push(line);
    line = "";
  };
  for (const word of text.split(" ")) {
    const spaced = line ? `${line} ${word}` : word;
    if (spaced.length <= perLine) {
      line = spaced;
      continue;
    }
    if (word.length <= perLine) {
      push();
      line = word;
      continue;
    }
    // A word longer than a line: it starts its own line and breaks at its joins.
    push();
    for (const piece of joinPieces(word)) {
      if (piece.length > perLine) return null;
      if ((line + piece).length <= perLine) line += piece;
      else {
        push();
        line = piece;
      }
    }
  }
  push();
  return out;
}

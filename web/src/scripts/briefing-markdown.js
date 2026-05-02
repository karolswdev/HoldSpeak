// HS-13-08 + HS-13-09: shared inline renderer for the
// `meeting_context` pipeline's deterministic markdown body.
// Two surfaces consume it: the runtime dashboard's pre-meeting
// briefing panel (`/`) and the /history Projects-tab timeline.
//
// Supports the exact subset the synthesizer emits — `# / ##`
// headings, `- ` bullets, `**bold**`, and bare http(s) URLs
// (auto-linked with target=_blank rel=noopener noreferrer).
// `escapeHtml` runs first so untrusted annotation content
// cannot inject markup. Anything richer than this is a
// synthesizer-side concern, not a renderer-side one.

export function renderBriefingMarkdown(input) {
  if (!input) return "";
  const lines = String(input).split(/\r?\n/);
  const html = [];
  let inList = false;
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (line.startsWith("## ")) {
      if (inList) { html.push("</ul>"); inList = false; }
      html.push(`<h2>${escapeHtml(line.slice(3))}</h2>`);
    } else if (line.startsWith("# ")) {
      if (inList) { html.push("</ul>"); inList = false; }
      html.push(`<h1>${escapeHtml(line.slice(2))}</h1>`);
    } else if (line.startsWith("- ")) {
      if (!inList) { html.push("<ul>"); inList = true; }
      html.push(`<li>${formatInline(line.slice(2))}</li>`);
    } else if (line.length === 0) {
      if (inList) { html.push("</ul>"); inList = false; }
    } else {
      if (inList) { html.push("</ul>"); inList = false; }
      html.push(`<p>${formatInline(line)}</p>`);
    }
  }
  if (inList) html.push("</ul>");
  return html.join("");
}

export function briefingFirstLine(markdown) {
  if (!markdown) return "";
  const lines = String(markdown).split(/\r?\n/);
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    if (line.startsWith("#")) continue;
    if (line.startsWith("- ")) return line.slice(2);
    return line;
  }
  return "";
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatInline(value) {
  let out = escapeHtml(value);
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(
    /(https?:\/\/[^\s<>"'()]+)([.,;:!?])?/g,
    (_m, url, trailing) =>
      `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>${trailing || ""}`
  );
  return out;
}

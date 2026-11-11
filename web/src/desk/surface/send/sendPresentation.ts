import type { Destination, Preview } from "../../../features/channels/channels";

/** A read-only face must not turn a credential pasted into a document or a
 * destination name into visible text, a title, or a link attribute. */
export function safeSendText(value: string): string {
  return value
    .replace(/"((?:access[_ -]?)?token|api[_ -]?key|secret|password|authorization)"\s*:\s*"[^"\n]*"/gi, '"$1": "[secret hidden]"')
    .replace(/https?:\/\/[^\s<>"')]+/gi, (url) => {
      try {
        const parsed = new URL(url);
        const secretQuery = [...parsed.searchParams.keys()].some((key) =>
          /token|secret|key|signature|password|credential|auth/i.test(key),
        );
        return secretQuery ||
          parsed.username ||
          parsed.password ||
          /hooks\.slack\.com\/services\/|\/bot\d+:/i.test(url)
          ? "[secret hidden]"
          : url;
      } catch {
        return "[link hidden]";
      }
    })
    .replace(/\bhooks\.slack\.com\/services\/[^\s<>"')]+/gi, "[secret hidden]")
    .replace(
      /\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|xox[baprs]-[A-Za-z0-9-]+|sk-(?:proj-)?[A-Za-z0-9_-]{12,}|\d{6,}:[A-Za-z0-9_-]{20,})\b/g,
      "[secret hidden]",
    )
    .replace(
      /\b((?:access[_ -]?)?token|api[_ -]?key|secret|password|authorization)\s*[:=]\s*(?:Bearer\s+)?[^\s,;]+/gi,
      "$1: [secret hidden]",
    );
}

export function safeSendPreview(preview: Preview): Preview {
  return {
    ...preview,
    // Hosts are named only at the final Send action. Account identity is
    // still readable without repeating its host in another field.
    fields: preview.fields
      .filter((field) => field.label !== "Webhook")
      .map((field) => ({
        label: safeSendText(field.label),
        value: safeSendText(
          field.label === "Account" ? field.value.split(" · ")[0] : field.value,
        ),
      })),
    body: safeSendText(preview.body),
  };
}

/** A saved destination can change without changing its id. A preview of
 * the former target/account is never a preview of this revision. */
export const destinationRevision = (destination: Destination): string =>
  JSON.stringify([
    (destination as Destination & { target_digest?: string }).target_digest,
  destination.target,
    destination.account,
    destination.synced,
    destination.state,
  ]);

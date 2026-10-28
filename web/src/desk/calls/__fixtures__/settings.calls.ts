// from CALLS-DESIGN §6; replace with a recording when the hub slice lands.
// The `calls` section of GET /api/settings (the passphrase is write only:
// the read says passphrase_set).
import type { CallsSettings } from "../types";

export const settingsCalls: CallsSettings = {
  enabled: true,
  aiphone_dir: "~/dev/ai-phone",
  greeting: "Hello. What can I do?",
  allowed_numbers: ["+15550100142"],
  passphrase_set: true,
};

export const settingsCallsFresh: CallsSettings = {
  enabled: false,
  aiphone_dir: "",
  greeting: "Hello. What can I do?",
  allowed_numbers: [],
  passphrase_set: false,
};

import {expect,it} from "vitest";
import {safeSendText} from "../sendPresentation";
it.each(["https://example.com?token=abc", "https://user:pass@example.com/path", "123456789:abcdefghijklmnopqrstuv"])("hides a credential in %s",value=>{expect(safeSendText(value)).not.toContain(value);});

it.each(['"token": "opaque-private-value"','"password": "a private phrase"','hooks.slack.com/services/T/B/private-key'])("hides a quoted credential or bare webhook in %s",value=>{expect(safeSendText(value)).not.toContain(value);expect(safeSendText(value)).toContain("secret hidden");});

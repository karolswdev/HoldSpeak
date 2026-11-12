/** Phone/SIP identities remain whole in operation arguments, masked on the face. */
export function phoneDigits(value: string): string {
  return value.replace(/^sips?:/i, "").split("@", 1)[0].replace(/[^\d+]/g, "");
}

export function maskedAddress(value: string): string {
  if (!value.trim()) return "";
  const number = phoneDigits(value);
  const tail = number.replace(/\D/g, "").slice(-4);
  const prefix = number.startsWith("+1")
    ? "+1"
    : !tail && (/^sips?:/i.test(value) || value.includes("@")) ? "SIP" : "";
  return [prefix, "···", tail].filter(Boolean).join(" ");
}

/** Only structured address values, never arbitrary task or transcript words. */
export function addressFact(value: string): string {
  return /^sips?:/i.test(value) || /^\+[\d\s().-]+$/.test(value)
    ? maskedAddress(value) : value;
}

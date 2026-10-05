// STATUS: "Product word list lacks decision, workbench and thread (Get Info
// falls back; other callers can still throw)". The registry names them now.
import { describe, expect, it } from "vitest";
import { productLabel } from "./productLanguage";
import { kindLabel } from "../desk/infoContract";

describe("the Desk's own objects are product words", () => {
  it("names decision, thread and workbench without a throw", () => {
    expect(productLabel("decision")).toBe("Decision");
    expect(productLabel("decision", true)).toBe("Decisions");
    expect(productLabel("thread")).toBe("Thread");
    expect(productLabel("thread", true)).toBe("Threads");
    expect(productLabel("workbench")).toBe("Workbench");
    expect(productLabel("workbench", true)).toBe("Workbenches");
  });

  it("Get Info reads the registry word for them", () => {
    expect(kindLabel("decision")).toBe("Decision");
    expect(kindLabel("thread")).toBe("Thread");
    expect(kindLabel("workbench")).toBe("Workbench");
  });
});

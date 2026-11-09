// PARKED 20261109 (lane subtract/mission-control): from desk/__tests__/grounding.test.ts.
describe("rails grounding (HS-88-02)", () => {
  afterEach(() => vi.unstubAllGlobals());

  const pick = (over: Partial<RailsPick> = {}): RailsPick => ({
    repo: "code",
    project: "holdspeak",
    kind: "story",
    id: "HS-88-02",
    title: "HS-88-02 The picker",
    chars: 400,
    ...over,
  });

  it("railsRefs strips the view fields down to the wire ref", () => {
    expect(railsRefs([pick()])).toEqual([
      { repo: "code", project: "holdspeak", kind: "story", id: "HS-88-02" },
    ]);
  });

  it("railsTokens prices real file size + header weight", () => {
    // (400 + title.length + 32) / 4
    const t = railsTokens([pick({ chars: 400 })]);
    expect(t).toBeGreaterThan(100);
  });

  it("buildGrounding merges desk objects and rails into one wire object", () => {
    const sel = emptyGrounding();
    const wire = buildGrounding(sel, [pick()]);
    expect(wire).toEqual({
      meeting_ids: [],
      artifact_ids: [],
      expand: "summary",
      rails: [
        { repo: "code", project: "holdspeak", kind: "story", id: "HS-88-02" },
      ],
    });
  });

  it("buildGrounding is null only when BOTH are empty", () => {
    expect(buildGrounding(emptyGrounding(), [])).toBeNull();
    expect(buildGrounding(emptyGrounding(), [pick()])).not.toBeNull();
  });

  it("the SAME rails picks build the SAME wire for ask and steer (parity)", () => {
    const picks = [
      pick(),
      pick({ kind: "phase", id: "88", title: "Phase 88" }),
    ];
    const askWire = buildGrounding(emptyGrounding(), picks);
    const steerWire = buildGrounding(emptyGrounding(), picks);
    expect(askWire).toEqual(steerWire); // one hydration, both surfaces
  });

  it("fetchRailsSizes maps the hub's hydrated sizes by kind:id", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            sizes: [{ kind: "story", id: "HS-88-02", chars: 512 }],
          }),
      }),
    );
    const sizes = await fetchRailsSizes([
      { repo: "code", project: "holdspeak", kind: "story", id: "HS-88-02" },
    ]);
    expect(sizes["story:HS-88-02"]).toBe(512);
  });

  it("fetchRailsSizes is empty (not thrown) on a hub error", async () => {
    vi.stubGlobal("fetch", () => Promise.reject(new Error("down")));
    expect(
      await fetchRailsSizes([
        { repo: "x", project: "y", kind: "story", id: "z" },
      ]),
    ).toEqual({});
  });
});

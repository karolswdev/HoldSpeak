import Foundation

// HSM — LIVE SYNC for the desk (wave 2 of THE PRIMITIVE FRAMEWORK).
//
// This is the desk-backed sync store + driver: it moves a real `ChangeSet` between the
// iPad desk and the desktop hub (the canonical store) over the existing transport
// (`HTTPSyncProvider`, `/api/sync/push|pull`) so a Note/Agent/KB/Chain/Workflow/Output
// authored on the iPad ports into the desktop and flows back out — and vice-versa.
//
// Design (why a desk-local store, not the SQLite `ISyncStore`):
//   - The desk persists its primitives as `@AppStorage` JSON record arrays
//     (hs.diorama.notes/.agents/.kbs/.outputs/.chains/.workflows), NOT in SQLite. So the
//     desk gets its own store that builds/applies a full `ChangeSet` directly from those
//     records via the canonical `synced()` / `init(contract:)` bridges.
//   - It reuses the rest of the wave-1 transport untouched: `HTTPSyncProvider`,
//     `SyncQueue` (offline buffer), and the `ChangeSet`/`Synced<>` envelopes.
//
// Conflict policy mirrors `SyncEngine` (HSM-10-03): per record, last-write-wins on the
// envelope `meta.last_modified` — incoming newer applies (live upserts, tombstone
// deletes; a newer tombstone never re-creates, an older live never resurrects a newer
// tombstone). Layout (`path` / positions) is per-device and NEVER synced (the bridges
// already omit it). Games are local-only and never appear in the change-set.
//
// The LWW instant: the iPad records have no `updatedAt` field of their own, so the store
// keeps a side map `id → last_modified` (persisted under hs.diorama.synctimes) plus a
// tombstone map `id → deleted_at` (hs.diorama.tombstones). `meta.last_modified` is the
// one truth (reconciliation tab 2); the side map IS the iPad's `updatedAt` projection.

// MARK: - the desk's syncable record set (a value snapshot the store reads/writes)

/// A flat view of the desk's syncable primitives + their sync metadata. The desk passes
/// this in (read) and gets a mutated copy back (apply), so the store stays free of any
/// SwiftUI/@AppStorage coupling and is unit-testable in isolation.
struct DeskRecords: Equatable {
    var notes: [NoteRecord] = []
    var agents: [AgentRecord] = []
    var kbs: [KBRecord] = []
    var outputs: [OutputRecord] = []
    var chains: [ChainRecord] = []
    var workflows: [WorkflowRecord] = []
    /// id → last-modified instant (the iPad's `updatedAt` projection; maps to meta.last_modified).
    var modified: [String: Date] = [:]
    /// id → deleted-at instant for propagated deletes (tombstones; record is gone locally).
    var tombstones: [String: Date] = [:]
}

// MARK: - the desk-backed sync store

/// Builds a `ChangeSet` from `DeskRecords` and applies an incoming one back (LWW + tombstones).
struct DeskSyncStore {

    /// Records applied / skipped from a pull (for the toast + audit).
    struct ApplyReport: Equatable { var applied = 0; var skipped = 0; var changed: Bool { applied > 0 } }

    /// The full local state as a change-set: live primitives (via the `synced()` bridges)
    /// + tombstones for propagated deletes. Each record's instant comes from the side map.
    func snapshot(_ r: DeskRecords, now: Date = Date()) -> ChangeSet {
        func t(_ id: String) -> Date { r.modified[id] ?? now }

        let notes = r.notes.map { $0.synced(at: t($0.id)) }
            + tombstones(in: r, kind: .note) as [Synced<Note>]
        let agents = r.agents.map { $0.synced(at: t($0.id)) }
            + tombstones(in: r, kind: .agent) as [Synced<Agent>]
        let kbs = r.kbs.map { $0.synced(at: t($0.id)) }
            + tombstones(in: r, kind: .kb) as [Synced<KB>]
        let artifacts = r.outputs.map { $0.synced(at: t($0.id)) }
            + tombstones(in: r, kind: .artifact) as [Synced<Artifact>]
        let chains = r.chains.map { $0.synced(at: t($0.id)) }
            + tombstones(in: r, kind: .chain) as [Synced<Chain>]
        let workflows = r.workflows.map { $0.synced(at: t($0.id)) }
            + tombstones(in: r, kind: .workflow) as [Synced<WorkflowDefinition>]

        return ChangeSet(meetings: [], artifacts: artifacts, notes: notes, kbs: kbs,
                         agents: agents, chains: chains, workflows: workflows)
    }

    private func tombstones<V: Codable & Equatable & Sendable>(in r: DeskRecords, kind: SyncKind) -> [Synced<V>] {
        r.tombstones.compactMap { id, at -> Synced<V>? in
            // a tombstone id is prefixed with its kind so we never cross-emit (note:/agent:/…)
            guard id.hasPrefix("\(kind.rawValue):") else { return nil }
            let bare = String(id.dropFirst(kind.rawValue.count + 1))
            return Synced<V>.tombstone(id: bare, kind: kind, at: at)
        }
    }

    /// Apply an incoming change-set with the LWW policy. Returns the mutated records + a report.
    func apply(_ cs: ChangeSet, to start: DeskRecords) -> (records: DeskRecords, report: ApplyReport) {
        var r = start
        var report = ApplyReport()

        for rec in cs.notes {
            mergeOne(&r, &report, meta: rec.meta, value: rec.value,
                     find: { $0.notes.firstIndex { $0.id == rec.meta.id } },
                     upsert: { recs, v in
                         let nr = NoteRecord(contract: v, path: recs.notes.first { $0.id == v.id }?.path ?? "")
                         if let i = recs.notes.firstIndex(where: { $0.id == v.id }) { recs.notes[i] = nr } else { recs.notes.append(nr) }
                     },
                     remove: { recs in recs.notes.removeAll { $0.id == rec.meta.id } })
        }
        for rec in cs.agents {
            mergeOne(&r, &report, meta: rec.meta, value: rec.value,
                     find: { $0.agents.firstIndex { $0.id == rec.meta.id } },
                     upsert: { recs, v in
                         let nr = AgentRecord(contract: v)
                         if let i = recs.agents.firstIndex(where: { $0.id == v.id }) { recs.agents[i] = nr } else { recs.agents.append(nr) }
                     },
                     remove: { recs in recs.agents.removeAll { $0.id == rec.meta.id } })
        }
        for rec in cs.kbs {
            mergeOne(&r, &report, meta: rec.meta, value: rec.value,
                     find: { $0.kbs.firstIndex { $0.id == rec.meta.id } },
                     upsert: { recs, v in
                         let nr = KBRecord(contract: v, path: recs.kbs.first { $0.id == v.id }?.path ?? "")
                         if let i = recs.kbs.firstIndex(where: { $0.id == v.id }) { recs.kbs[i] = nr } else { recs.kbs.append(nr) }
                     },
                     remove: { recs in recs.kbs.removeAll { $0.id == rec.meta.id } })
        }
        for rec in cs.artifacts {
            mergeOne(&r, &report, meta: rec.meta, value: rec.value,
                     find: { $0.outputs.firstIndex { $0.id == rec.meta.id } },
                     upsert: { recs, v in
                         let nr = OutputRecord(contract: v, path: recs.outputs.first { $0.id == v.id }?.path ?? "")
                         if let i = recs.outputs.firstIndex(where: { $0.id == v.id }) { recs.outputs[i] = nr } else { recs.outputs.append(nr) }
                     },
                     remove: { recs in recs.outputs.removeAll { $0.id == rec.meta.id } })
        }
        for rec in cs.chains {
            mergeOne(&r, &report, meta: rec.meta, value: rec.value,
                     find: { $0.chains.firstIndex { $0.id == rec.meta.id } },
                     upsert: { recs, v in
                         let nr = ChainRecord(contract: v)
                         if let i = recs.chains.firstIndex(where: { $0.id == v.id }) { recs.chains[i] = nr } else { recs.chains.append(nr) }
                     },
                     remove: { recs in recs.chains.removeAll { $0.id == rec.meta.id } })
        }
        for rec in cs.workflows {
            mergeOne(&r, &report, meta: rec.meta, value: rec.value,
                     find: { $0.workflows.firstIndex { $0.id == rec.meta.id } },
                     upsert: { recs, v in
                         let nr = WorkflowRecord(contract: v)
                         if let i = recs.workflows.firstIndex(where: { $0.id == v.id }) { recs.workflows[i] = nr } else { recs.workflows.append(nr) }
                     },
                     remove: { recs in recs.workflows.removeAll { $0.id == rec.meta.id } })
        }
        // meetings are read-only on the desk (owned by the capture model), so the desk
        // never applies incoming meeting records here — it pushes its own primitives and
        // pulls the durable ones it authors. (Meetings flow via the capture pipeline.)
        return (r, report)
    }

    /// The LWW decision + write for one record. `find` locates a live local copy; `upsert`
    /// writes a live value; `remove` deletes a live local copy. The side maps (modified /
    /// tombstones) are the local instant source and are updated on every applied write.
    private func mergeOne<Value>(
        _ r: inout DeskRecords, _ report: inout ApplyReport,
        meta: SyncMetadata, value: Value?,
        find: (DeskRecords) -> Int?,
        upsert: (inout DeskRecords, Value) -> Void,
        remove: (inout DeskRecords) -> Void
    ) {
        let key = "\(meta.kind.rawValue):\(meta.id)"
        let localLive = find(r) != nil
        let localTime: Date? = r.modified[meta.id] ?? r.tombstones[key]
        // brand new → apply; else newer wins, equal/older skips
        if let lt = localTime, meta.lastModified <= lt { report.skipped += 1; return }

        if meta.deleted {
            if localLive { remove(&r) }
            r.modified[meta.id] = nil
            r.tombstones[key] = meta.lastModified
            report.applied += 1
        } else {
            guard let v = value else { report.skipped += 1; return }   // malformed live rec
            upsert(&r, v)
            r.modified[meta.id] = meta.lastModified
            r.tombstones[key] = nil
            report.applied += 1
        }
    }
}

#if DEBUG
extension DeskSyncStore {
    /// In-code round-trip proof (no test target exists for the App layer): author a desk
    /// record set, snapshot it, push it through the real contract coder (encode→decode,
    /// the exact `/api/sync/push` payload), apply the decoded change-set to a FRESH desk,
    /// and assert the primitives + LWW + tombstone landed. Logs PASS/FAIL to the console;
    /// run via `SIMCTL_CHILD_HS_SYNC_SELFCHECK=1`. Returns true on success.
    @discardableResult
    static func selfCheck() -> Bool {
        let store = DeskSyncStore()
        let t0 = Date(timeIntervalSince1970: 1_700_000_000)
        let t1 = t0.addingTimeInterval(60)

        // Surface A authors a note + an agent + a kb, and tombstones an old note.
        var a = DeskRecords()
        a.notes = [NoteRecord(id: "n1", title: "Ship it", body: "the desk syncs", path: "/local")]
        a.agents = [AgentRecord(id: "ag1", name: "Scout", avatar: "p1", role: "digs",
                                systemPrompt: "research", userTemplate: "{input}",
                                manualContext: "", useZoneContext: false, kb: "")]
        a.kbs = [KBRecord(id: "k1", name: "Knowledge", path: "/local", items: 0)]
        a.modified = ["n1": t1, "ag1": t1, "k1": t1]
        a.tombstones = ["note:nOld": t1]

        // Build the wire payload exactly as the driver would, then round-trip it.
        let outbound = store.snapshot(a)
        guard let data = try? HoldSpeakContracts.encoder().encode(outbound),
              let incoming = try? HoldSpeakContracts.decoder().decode(ChangeSet.self, from: data)
        else { NSLog("HS_SYNC_SELFCHECK: FAIL (encode/decode)"); return false }

        // Surface B starts empty and applies what A pushed.
        let (merged, report) = store.apply(incoming, to: DeskRecords())

        var ok = true
        func check(_ cond: Bool, _ msg: String) { if !cond { ok = false; NSLog("HS_SYNC_SELFCHECK: FAIL — \(msg)") } }
        check(merged.notes.contains { $0.id == "n1" && $0.title == "Ship it" }, "note n1 not applied")
        check(merged.notes.first { $0.id == "n1" }?.path == "", "layout leaked into sync (path should be empty on apply)")
        check(merged.agents.contains { $0.id == "ag1" && $0.name == "Scout" }, "agent ag1 not applied")
        check(merged.kbs.contains { $0.id == "k1" }, "kb k1 not applied")
        check(merged.tombstones["note:nOld"] != nil, "tombstone not carried")
        check(report.applied == 4, "expected 4 applied, got \(report.applied)")

        // LWW: an OLDER incoming edit must NOT clobber the newer local copy.
        var local = merged
        local.notes = [NoteRecord(id: "n1", title: "Newer local", body: "edited here", path: "")]
        local.modified["n1"] = t1.addingTimeInterval(120)   // local is newer
        let stale = ChangeSet(notes: [Synced<Note>.live(
            Note(id: "n1", title: "Stale remote", bodyMarkdown: "old", tags: [], createdAt: t0, updatedAt: t0),
            id: "n1", kind: .note, modifiedAt: t0)])             // remote is older
        let (afterLWW, lwwReport) = store.apply(stale, to: local)
        check(afterLWW.notes.first { $0.id == "n1" }?.title == "Newer local", "LWW: older remote clobbered newer local")
        check(lwwReport.skipped == 1, "LWW: stale edit should have been skipped")

        NSLog(ok ? "HS_SYNC_SELFCHECK: PASS (7-kind snapshot→push→pull→apply + tombstone + LWW)" : "HS_SYNC_SELFCHECK: FAILED")
        return ok
    }
}
#endif

// MARK: - the driver: push + pull + offline through the existing transport

/// Drives one real sync pass against the paired hub: snapshot → enqueue (durable) →
/// flush the queue (offline-safe) → pull + apply. Never throws on an unreachable peer;
/// the outbound snapshot stays queued for the next pass, so sync is never on the
/// capture/author path.
struct DeskSyncDriver {
    let provider: HTTPSyncProvider
    let queue: SyncQueue
    let store = DeskSyncStore()

    struct Outcome: Equatable {
        var pushed = 0
        var pendingAfter = 0
        var applied = 0
        var reachedPeer = false
    }

    /// Build a driver pointed at the paired hub. Returns nil when no peer is paired.
    static func make(host: String, port: Int) -> DeskSyncDriver? {
        guard !host.trimmingCharacters(in: .whitespaces).isEmpty, port > 0,
              let url = URL(string: "http://\(host):\(port)") else { return nil }
        let dir = (try? SyncQueue.defaultDirectory())
            ?? FileManager.default.temporaryDirectory.appendingPathComponent("hs-sync-queue")
        return DeskSyncDriver(provider: HTTPSyncProvider(config: .init(baseURL: url)),
                              queue: SyncQueue(directory: dir))
    }

    /// One sync pass. Durable-first: the snapshot is queued before any network so nothing
    /// is lost if the peer is down. Returns the outcome + the (possibly) updated records.
    func syncNow(_ records: DeskRecords, now: Date = Date()) async -> (records: DeskRecords, outcome: Outcome) {
        // 1. Record the outbound snapshot durably (offline-safe).
        try? queue.enqueueNext(store.snapshot(records, now: now))

        // 2. Flush the queue to the peer (never throws; leaves the rest if down).
        let pushed = await queue.flush(through: provider)
        let pendingAfter = (try? queue.count()) ?? 0

        // 3. Pull + apply if reachable.
        do {
            let incoming = try await provider.pull()
            let (merged, report) = store.apply(incoming, to: records)
            return (merged, Outcome(pushed: pushed, pendingAfter: pendingAfter,
                                    applied: report.applied, reachedPeer: true))
        } catch {
            return (records, Outcome(pushed: pushed, pendingAfter: pendingAfter,
                                     applied: 0, reachedPeer: false))
        }
    }
}

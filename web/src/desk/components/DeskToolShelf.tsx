import { useEffect, useMemo, useRef, useState } from "react";
import { openSurface } from "../shell";
import { qualifiedRef } from "../api";
import { modelChatId } from "../chat";
import {
  contextualCapabilityActions,
  contextualCoderSessions,
  contextualIntegrationActions,
} from "../contextual";
import { useDesk } from "../store";
import { allObjects } from "../world";

export const DESK_TOOLS = [
  {
    href: "/workbench",
    label: "Workflow editor",
    description: "Build and edit Workflows.",
    glyph: "◇",
    action: "build-workflow",
    subjectRef: undefined,
  },
  {
    href: "/companion",
    label: "Agents and coder sessions",
    description: "Use saved behavior and inspect live sessions.",
    glyph: "◉",
    action: "inspect-personas-and-coders",
    subjectRef: undefined,
  },
  {
    href: "/profiles",
    label: "Runs on",
    description: "Configure model and runtime destinations.",
    glyph: "▣",
    action: "configure-runs-on",
    subjectRef: undefined,
  },
  {
    href: "/settings",
    label: "Integrations",
    description: "Configure connected destinations and credentials.",
    glyph: "↗",
    action: "configure-integrations",
    subjectRef: "integration:destinations",
  },
  {
    href: "/commands",
    label: "Commands",
    description: "Map spoken phrases to registered actions.",
    glyph: "⌘",
    action: "configure-commands",
    subjectRef: undefined,
  },
  {
    href: "/cadence",
    label: "Cadence",
    description: "Configure scheduled background work.",
    glyph: "◷",
    action: "configure-cadence",
    subjectRef: undefined,
  },
  {
    href: "/activity",
    label: "Activity",
    description: "Inspect work context and source records.",
    glyph: "≋",
    action: "inspect-activity",
    subjectRef: undefined,
  },
] as const;

export const KIND_LABEL: Record<string, string> = {
  artifact: "Artifact",
  chain: "Workflow",
  coder: "Coder session",
  kb: "Knowledge",
  meeting: "Meeting",
  note: "Note",
  recipe: "Persona",
  workflow: "Workflow",
};

export function DeskToolShelf() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const rootRef = useRef<HTMLElement | null>(null);
  const launchRef = useRef<HTMLButtonElement | null>(null);
  const searchRef = useRef<HTMLInputElement | null>(null);
  const items = useDesk((state) => state.items);
  const projects = useDesk((state) => state.projects);
  const targets = useDesk((state) => state.inferenceTargets);
  const models = useDesk((state) => state.models);
  const setup = useDesk((state) => state.setup);
  const selectedIds = useDesk((state) => state.selectedIds);
  const openPullout = useDesk((state) => state.openPullout);
  const openChat = useDesk((state) => state.openChat);
  const openToolInspector = useDesk((state) => state.openToolInspector);
  const diveInto = useDesk((state) => state.diveInto);
  const integrations = setup?.trust?.destinations ?? [];

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
        return;
      }
      if (event.key === "Escape" && open) {
        setOpen(false);
        launchRef.current?.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open]);

  useEffect(() => {
    if (open) searchRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node;
      if (
        !rootRef.current?.contains(target) &&
        !launchRef.current?.contains(target)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  const normalized = query.trim().toLocaleLowerCase();
  const matchingTools = DESK_TOOLS.filter((tool) =>
    `${tool.label} ${tool.description}`
      .toLocaleLowerCase()
      .includes(normalized),
  );
  const objectMatches = useMemo(() => {
    if (!normalized) return [];
    return allObjects(items)
      .filter((item) =>
        `${item.title} ${KIND_LABEL[item.kind] ?? item.kind}`
          .toLocaleLowerCase()
          .includes(normalized),
      )
      .slice(0, 8);
  }, [items, normalized]);
  const zoneMatches = useMemo(() => {
    if (!normalized) return [];
    return items.directory
      .filter((zone) =>
        `${String(zone.name ?? zone.title ?? "Zone")} Zone`
          .toLocaleLowerCase()
          .includes(normalized),
      )
      .slice(0, 8);
  }, [items.directory, normalized]);
  const projectMatches = useMemo(
    () =>
      projects
        .filter((project) =>
          `${project.name} ${project.description} Project`
            .toLocaleLowerCase()
            .includes(normalized),
        )
        .slice(0, normalized ? 8 : 4),
    [normalized, projects],
  );
  const integrationMatches = useMemo(
    () =>
      integrations
        .filter(
          (integration) =>
            (normalized ? true : integration.enabled) &&
            `${integration.name} ${integration.destination} ${integration.operation}`
              .toLocaleLowerCase()
              .includes(normalized),
        )
        .slice(0, normalized ? 8 : 4),
    [integrations, normalized],
  );
  const targetMatches = useMemo(
    () =>
      targets
        .filter((target) =>
          `${target.name} ${target.kind} ${target.boundary} ${target.model}`
            .toLocaleLowerCase()
            .includes(normalized),
        )
        .slice(0, normalized ? 8 : 4),
    [normalized, targets],
  );
  const modelMatches = useMemo(
    () =>
      models
        .filter((model) =>
          `${model.name} Model`.toLocaleLowerCase().includes(normalized),
        )
        .slice(0, normalized ? 8 : 4),
    [models, normalized],
  );
  const capabilityActions = contextualCapabilityActions(items, selectedIds);
  const integrationActions = contextualIntegrationActions(
    integrations,
    items,
    selectedIds,
  );
  const coderActions = contextualCoderSessions(items, selectedIds);
  const contextualCount =
    capabilityActions.length + integrationActions.length + coderActions.length;

  const close = () => {
    setOpen(false);
    setQuery("");
  };

  // Keyboard-only navigation (HS-93-01): ArrowDown/ArrowUp move focus from
  // the search field through every result (tool links and Desk-item
  // buttons), the standard search-shelf pattern. Without this the shelf was
  // Tab-only, which buried distant results behind many keystrokes.
  const moveFocus = (event: React.KeyboardEvent<HTMLElement>) => {
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
    const root = rootRef.current;
    if (!root) return;
    const focusables = Array.from(
      root.querySelectorAll<HTMLElement>(
        "input[type='search'], .desk-tool-list a, .desk-tool-list button",
      ),
    );
    if (!focusables.length) return;
    event.preventDefault();
    const current = focusables.indexOf(document.activeElement as HTMLElement);
    const next =
      event.key === "ArrowDown"
        ? Math.min(current + 1, focusables.length - 1)
        : Math.max(current - 1, 0);
    focusables[next]?.focus();
  };

  return (
    <>
      <button
        ref={launchRef}
        type="button"
        className="desk-chip desk-tools-launch"
        aria-expanded={open}
        aria-controls="desk-tool-shelf"
        aria-keyshortcuts="Control+K Meta+K"
        onClick={() => setOpen((value) => !value)}
      >
        Tools <kbd>⌘K</kbd>
      </button>
      {open ? (
        <aside
          ref={rootRef}
          id="desk-tool-shelf"
          className="desk-tool-shelf"
          role="region"
          aria-label="Tools and Desk search"
          onKeyDown={moveFocus}
        >
          <header className="desk-panel-head">
            <div>
              <h2 className="desk-panel-title" id="desk-tool-shelf-title">
                Tools and Desk search
              </h2>
              <p>Open a tool or find an item without leaving the Desk.</p>
            </div>
            <button
              type="button"
              className="desk-pullout-close"
              onClick={close}
              aria-label="Close Tools"
            >
              ✕
            </button>
          </header>
          <label className="desk-tool-search">
            <span className="sr-only">Search tools and Desk items</span>
            <input
              ref={searchRef}
              type="search"
              value={query}
              placeholder="Search tools and Desk items"
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          {selectedIds.length ? (
            <section aria-labelledby="desk-context-actions-heading">
              <h3 id="desk-context-actions-heading">
                For{" "}
                {selectedIds.length === 1
                  ? "selection"
                  : `${selectedIds.length} selected`}
              </h3>
              {contextualCount ? (
                <ul className="desk-tool-list">
                  {capabilityActions.map((action) => (
                    <li key={`${action.kind}:${action.id}`}>
                      <button
                        type="button"
                        onClick={() => {
                          close();
                          openPullout(qualifiedRef(action.kind, action.id));
                        }}
                      >
                        <span aria-hidden="true">◇</span>
                        <span>
                          <strong>{action.label}</strong>
                          <small>
                            Result returns as an Artifact and Receipt
                          </small>
                        </span>
                      </button>
                    </li>
                  ))}
                  {integrationActions.map((action) => (
                    <li key={`integration:${action.id}`}>
                      <button
                        type="button"
                        onClick={() => {
                          close();
                          openToolInspector("integration", action.id);
                        }}
                      >
                        <span aria-hidden="true">↗</span>
                        <span>
                          <strong>{action.label}</strong>
                          <small>Review exact effect and destination</small>
                        </span>
                      </button>
                    </li>
                  ))}
                  {coderActions.map((action) => (
                    <li key={`coder:${action.id}`}>
                      <button
                        type="button"
                        onClick={() => {
                          close();
                          openPullout(qualifiedRef("coder", action.id));
                        }}
                      >
                        <span aria-hidden="true">◉</span>
                        <span>
                          <strong>{action.label}</strong>
                          <small>Review selected text before sending</small>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="desk-tool-empty">
                  No ready tool accepts this selection.
                </p>
              )}
            </section>
          ) : null}
          <section aria-labelledby="desk-tools-heading">
            <h3 id="desk-tools-heading">Tools</h3>
            <ul className="desk-tool-list">
              {matchingTools.map((tool) => (
                <li key={tool.href}>
                  <button
                    type="button"
                    className="desk-tool-link"
                    onClick={() => {
                      close();
                      // The shelf is a pure dispatcher (HS-95-08): every
                      // tool is a desk surface; nothing navigates.
                      openSurface(tool.action, tool.subjectRef);
                    }}
                  >
                    <span aria-hidden="true">{tool.glyph}</span>
                    <span>
                      <strong>{tool.label}</strong>
                      <small>{tool.description}</small>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
          {projectMatches.length ||
          integrationMatches.length ||
          targetMatches.length ||
          modelMatches.length ? (
            <section aria-labelledby="desk-resources-heading">
              <h3 id="desk-resources-heading">Desk resources</h3>
              <ul className="desk-tool-list">
                {projectMatches.map((project) => (
                  <li key={`project:${project.id}`}>
                    <button
                      type="button"
                      onClick={() => {
                        close();
                        openToolInspector("project", project.id);
                      }}
                    >
                      <span aria-hidden="true">▤</span>
                      <span>
                        <strong>{project.name}</strong>
                        <small>
                          Project · {project.meeting_count} Meetings
                        </small>
                      </span>
                    </button>
                  </li>
                ))}
                {integrationMatches.map((integration) => (
                  <li key={`integration:${integration.id}`}>
                    <button
                      type="button"
                      onClick={() => {
                        close();
                        openToolInspector("integration", integration.id);
                      }}
                    >
                      <span aria-hidden="true">↗</span>
                      <span>
                        <strong>{integration.name}</strong>
                        <small>
                          Integration ·{" "}
                          {integration.enabled
                            ? integration.destination
                            : "Not configured"}
                        </small>
                      </span>
                    </button>
                  </li>
                ))}
                {targetMatches.map((target) => (
                  <li key={`target:${target.id}`}>
                    <button
                      type="button"
                      onClick={() => {
                        close();
                        openToolInspector("target", target.id);
                      }}
                    >
                      <span aria-hidden="true">▣</span>
                      <span>
                        <strong>{target.name}</strong>
                        <small>
                          Runs on ·{" "}
                          {target.readiness.available ? "Ready" : "Unavailable"}
                        </small>
                      </span>
                    </button>
                  </li>
                ))}
                {modelMatches.map((model) => (
                  <li key={`model:${model.name}`}>
                    <button
                      type="button"
                      onClick={() => {
                        close();
                        openChat(modelChatId(model.name));
                      }}
                    >
                      <span aria-hidden="true">◈</span>
                      <span>
                        <strong>{model.name}</strong>
                        <small>Model · Ready</small>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
          {normalized ? (
            <section aria-labelledby="desk-items-heading">
              <h3 id="desk-items-heading">Desk items</h3>
              {objectMatches.length || zoneMatches.length ? (
                <ul className="desk-tool-list">
                  {zoneMatches.map((zone) => (
                    <li key={`zone:${zone.id}`}>
                      <button
                        type="button"
                        onClick={() => {
                          close();
                          diveInto(String(zone.id));
                        }}
                      >
                        <span aria-hidden="true">□</span>
                        <span>
                          <strong>
                            {String(zone.name ?? zone.title ?? "Zone")}
                          </strong>
                          <small>Zone</small>
                        </span>
                      </button>
                    </li>
                  ))}
                  {objectMatches.map((item) => (
                    <li key={`${item.kind}:${item.id}`}>
                      <button
                        type="button"
                        onClick={() => {
                          close();
                          openPullout(qualifiedRef(item.kind, item.id));
                        }}
                      >
                        <span aria-hidden="true">○</span>
                        <span>
                          <strong>{item.title}</strong>
                          <small>{KIND_LABEL[item.kind] ?? item.kind}</small>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="desk-tool-empty">
                  No matching tools or Desk items.
                </p>
              )}
            </section>
          ) : null}
        </aside>
      ) : null}
    </>
  );
}

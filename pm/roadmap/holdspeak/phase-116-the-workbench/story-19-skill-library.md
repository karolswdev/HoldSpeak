# HS-116-19 — The skill library

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-06, HS-116-16
- **Unblocks:** HS-116-15
- **Owner:** unassigned

## The thesis (the bar)

Workbenches ship with REAL skills — not empty skill slots. A curated
library of production-quality procedural skills, adapted from the
Hermes Agent ecosystem (MIT-licensed), ships with every HoldSpeak
installation. When the user creates a TODO workbench, it comes with
skills for systematic task processing, grounded citations, and
action-item extraction. When they create a Meeting Prep workbench,
it comes with skills for transcript summarization, action-item
tracking, and agenda preparation. The skills are the difference
between "an LLM with a system prompt" and "an agent that knows how
to work."

**Articles served:** VI (honest by construction — skills state what
the agent knows how to do, not what it claims), IX (proof — skill
procedures are auditable documents the owner can read).

**Source:** The Hermes Agent project (NousResearch/hermes-agent,
MIT license) ships a rich skill library under `skills/` and
`optional-skills/`. These are high-quality, versioned, procedural
documents covering software development, research, productivity,
and operations. We adapt and curate from this library — not copy
blindly. Each skill is rewritten to work within HoldSpeak's prompt
stack, grounding system, and constitutional context.

## The skill library

### Core skills (ship with every installation)

| Skill | Adapted from | What it teaches the agent |
|-------|-------------|--------------------------|
| **Systematic task processing** | Hermes `plan` | Break a task into steps, execute in order, verify each step before proceeding |
| **Grounded citations** | Hermes `grounded-citations` | Every claim from a source gets an inline citation with verifiable provenance |
| **Action item extraction** | Original | Parse meeting notes, documents, or threads for concrete action items with owners and deadlines |
| **Structured summarization** | Original | Summarize content with sections: key points, decisions, action items, open questions |
| **Systematic debugging** | Hermes `systematic-debugging` | 4-phase root cause debugging: reproduce → isolate → diagnose → verify fix. NO fixes without root cause |
| **Code review** | Hermes `requesting-code-review` | Security scan, quality gates, independent reviewer perspective. No agent verifies its own work |
| **Test-driven approach** | Hermes `test-driven-development` | Write the test first, watch it fail, write minimal code to pass |
| **Research with sources** | Hermes `research-paper-writing` + `grounded-citations` | Systematic research: define question → gather sources → synthesize → cite |
| **OCR and document reading** | Hermes `ocr-and-documents` | Extract text from PDFs, scans, images — pymupdf/marker-pdf pipeline |
| **Meeting preparation** | Hermes `teams-meeting-pipeline` + original | Prep pack assembly: prior meeting summary, open action items, likely topics, decisions needed |

### Template-specific skill bindings

| Template | Pre-attached skills |
|----------|-------------------|
| **TODO Agent** | Systematic task processing, Grounded citations, Action item extraction |
| **Triage Agent** | Structured summarization, Action item extraction |
| **Meeting Prep Agent** | Meeting preparation, Structured summarization, Action item extraction |
| **Morning Brief** | Structured summarization, Action item extraction |

### Skill format

Each skill is a markdown file with YAML front matter (the Hermes
convention, adapted for HoldSpeak):

```markdown
---
name: systematic-debugging
description: "4-phase root cause debugging: understand before fixing."
version: 1.0.0
source: "Adapted from Hermes Agent (MIT), obra/superpowers"
tags: [debugging, troubleshooting, root-cause]
---

# Systematic Debugging

## Core principle

ALWAYS find root cause before attempting fixes.

## Phase 1: Reproduce
...
```

Skills are stored as DB records (SkillRecord) with the full
markdown body. They are also mirrored to the workspace filesystem
for human readability. The YAML front matter is parsed for metadata
(name, description, version, tags) and stored in the DB fields.

## Deliverables

1. **Built-in skill library.** A `holdspeak/skills_library/`
   directory containing 10 skill markdown files, each adapted from
   Hermes or written original. These ship with the Python package.

2. **Skill seeding on first run.** When the hub starts and the
   skills table is empty, the built-in library is seeded into the
   DB as active, owner-authored skills. This runs once — after
   seeding, the owner owns the skills and can edit/delete them.

3. **Template skill binding.** The template registry
   (`workbench_templates.py`) gains a `skill_ids` field per
   template. When a template is instantiated, the listed skills
   are attached to the created recipe.

4. **Skill import.** An API endpoint `POST /api/skills/import`
   accepts a markdown file (with YAML front matter) and creates
   a skill record. This is how users add community skills or
   their own.

5. **Skill browsing in the workbench.** The configuration panel's
   skills section (HS-116-10) shows the library skills with
   one-line descriptions. Unattached skills are shown in a
   "Library" subsection with an "Attach" chip.

6. **Attribution.** Each adapted skill carries its source
   attribution in the YAML front matter (`source:` field) and a
   `## Attribution` section at the bottom crediting the Hermes
   project and original authors per the MIT license.

## Test plan

- `uv run pytest -q` — skill seeding creates 10 records on fresh
  DB, template instantiation attaches the correct skills, import
  endpoint parses YAML front matter correctly.
- Visual: create a TODO workbench from template. Open the skills
  section. Verify 3 skills are pre-attached with titles,
  descriptions, and body previews.

# Relationship-aware memory

HoldSpeak memory retrieves evidence in two bounded, local passes:

1. SQLite FTS recalls lexical matches independently from extracted Decisions,
   Artifacts, Meeting transcript segments, Notes, and Thread message parts. A
   bounded canonical-store pass applies the same ranking contract to durable
   Decision Records, authored Decisions, Actions, Project items, Workbench
   items/results, and Cadence loops. A child match returns its coherent parent
   Meeting or Thread instead of an isolated row.
2. Up to 32 lexical parent objects seed one authoritative one-hop traversal.
   The traversal follows only relationships HoldSpeak already persisted:
   Meeting–Artifact, Meeting–Decision, Decision–source, supersession, Decision
   Record sources and affected work, Action source Meetings/commitments,
   Workbench grounding/results, Cadence evidence, and frozen Thread references.
   It can add at most two neighbours per lexical seed and 64 related parents
   overall, so one highly connected Meeting cannot crowd every other direct
   match out of a bounded model context.

Model prompts are reduced to at most 24 unique lexical terms while retaining
terms from both the beginning and end of long prompts. This bounds SQLite FTS
grammar and canonical-store scans without dropping a trailing user question.

There is no model call, embedding request, network access, entity extraction, or
inferred edge in either pass. Project-scoped search checks every lexical and
related result against Project membership, Meeting membership, or a Thread's
frozen references before returning it.

Each hit says how it was found:

- `retrieval_origin: lexical` means its own child or body matched the query.
- `retrieval_origin: relationship` means a lexical seed reached it over a
  durable edge; `related_to`, `relationship`, and `graph_score` name that edge.

## Ecosystem boundary

The same retrieval and hydration contract is used at each model-context
boundary, before the request is admitted and frozen:

| Surface | Integration |
| --- | --- |
| Ask and Thought refinement | Query-relevant memory joins explicit/frozen context. Routed Thoughts reserve and dispatch the exact same bytes. |
| Threads and Agent chat | Relevant sources are frozen on the user message; current-thread self-recall is excluded and the visible set is bounded. |
| Agent/Recipe runs | Memory is prefixed to the rendered input and recorded in grounding metadata. |
| Sequences and Workflows | Every model-bearing step/node retrieves independently from its current input. |
| Workbenches | Every item retrieves from its title/body in addition to explicit item grounding and private Workbench memory. |
| Coder steering | Previewed and executed steer text receives the same bounded source blocks. |
| HTTP, MCP, and Thread tools | `/api/memory/search` and `memory.search` expose the identical hit contract. |
| Web Desk and Project Room | The unscoped window searches the whole Desk; a Project scope applies the Project membership fence. |

Raw People records, credentials, settings, kernel receipts, and unfiltered
activity are intentionally not generic memory sources. Dictation's correction
memory also remains a separate privacy/typing subsystem; Dictation-originated
Notes, Meetings, Actions, and other durable outputs become searchable through
their canonical object types. These are security boundaries, not missing
integration claims.

## Design provenance

This is an original HoldSpeak adaptation of two Apache-2.0 RAGFlow retrieval
ideas: parent/child recall and the zero-LLM compiled-product expansion that
searches seeds, follows adjacent graph relations, and loads the neighbours'
source passages. HoldSpeak uses its canonical object graph in place of
RAGFlow's compiled entity rows.

No RAGFlow source file was copied or modified, and this work has not been
submitted to RAGFlow. It is a local HoldSpeak contribution implemented against
HoldSpeak's own repositories, admission system, UI, and tests.

- RAGFlow repository: <https://github.com/infiniflow/ragflow>
- Compiled expansion reference inspected at commit
  `2af732d6072f050ead758edaf23dd4ebfec5526a`:
  <https://github.com/infiniflow/ragflow/blob/2af732d6072f050ead758edaf23dd4ebfec5526a/rag/advanced_rag/harness/tools/compiled_expansion.py>
- RAGFlow license: <https://github.com/infiniflow/ragflow/blob/main/LICENSE>

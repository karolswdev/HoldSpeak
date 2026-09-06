# Meeting output schema

Technical reference retained from the Models guide.
For owner setup, read [Models](../MODELS.md).

## Structured output for meeting intelligence

Meeting intelligence sends a request-level `response_format` with a JSON Schema
derived from the one `INTEL_SCHEMA` constant in `holdspeak/intel/parsing.py`.
The schema shape is:

```json
{
  "topics": ["<short topic>"],
  "action_items": [
    {
      "task": "<task>",
      "owner": "<person's name as spoken>|Me|Remote|null",
      "due": "<date or null>"
    }
  ],
  "summary": "<short summary>"
}
```

`owner` is a literal person name as spoken in the transcript, or one of two
reserved tokens: `Me` (the speaker or leader) and `Remote` (the counterpart).
`null` means the transcript did not name an owner. Every other string is a
literal name the model heard. `Me` and `Remote` are the only reserved tokens.

The prompt stringifies `INTEL_SCHEMA`, the `response_format` wraps
`INTEL_JSON_SCHEMA` (the formal JSON Schema derived from it), and the semantic
adapter references the same constant. If the endpoint returns a 400 naming
`response_format` or `json_schema`, the dispatch treats the rejection as a
dialect mismatch (like the `max_completion_tokens` compatibility pattern),
records the endpoint's dialect, and raises a named signal for a second admitted
child that omits `response_format`. The fallback is never a silent retry: the
runner admits one physical request per child, and the prompt's "Return ONLY a
single valid JSON object" instruction plus the `_extract_json` line-recovery
heuristic remain the safety net.

### The schema-pinned-server gotcha

A llama.cpp server launched with a server-level `--json-schema` flag pins every
response to that schema regardless of what the request asks for. A prompt-level
JSON plea or a request-level `response_format` override is silently swallowed,
and the response conforms to the pinned schema instead. The product now sends
request-level structured output, which overrides the server pin cleanly on
llama.cpp builds that support it. If you run a llama.cpp server with
`--json-schema`, verify that the model responds to the product's schema and not
the server pin by checking the shape of the response (it should contain
`topics`, `action_items`, and `summary`, not the pinned shape).


## See also

- [Models](../MODELS.md): current setup controls.
- [Parsing contract](../../holdspeak/intel/parsing.py): schema constants and response handling.

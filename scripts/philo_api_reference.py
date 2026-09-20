#!/usr/bin/env python3
"""Enrich the existing API manifest with inspectable static transport evidence.

The existing real-app generator owns route membership. This script does not
import HoldSpeak or infer authority/idempotency from an HTTP method. Raw Request
handlers and helper-derived contracts stay explicitly unresolved.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return ast.unparse(node)


def inspect_module(path: Path):
    if not path.is_file():
        return []
    source = path.read_text()
    tree = ast.parse(source)
    handlers = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute) or not dec.args:
                continue
            method = dec.func.attr.upper()
            if method not in {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'WEBSOCKET', 'API_ROUTE'}:
                continue
            route = literal(dec.args[0])
            if not isinstance(route, str):
                continue
            keywords = {k.arg: literal(k.value) for k in dec.keywords if k.arg}
            body = ast.get_source_segment(source, node) or ''
            params = [{'name':a.arg,'annotation':ast.unparse(a.annotation) if a.annotation else None} for a in node.args.args]
            calls = sorted({ast.unparse(c.func) for c in ast.walk(node) if isinstance(c, ast.Call)})
            errors = sorted({int(c.value) for n in ast.walk(node) if isinstance(n, ast.Call) for c in [k.value for k in n.keywords if k.arg == 'status_code'] if isinstance(c, ast.Constant) and isinstance(c.value,int) and c.value >= 400})
            methods = keywords.get('methods', [method]) if method == 'API_ROUTE' else ['WS' if method == 'WEBSOCKET' else method]
            handlers.append({'path':route,'methods':methods,'symbol':node.name,'line':node.lineno,'parameters':params,'return_annotation':ast.unparse(node.returns) if node.returns else None,'declared_response_model':keywords.get('response_model'),'declared_responses':keywords.get('responses',{}),'literal_error_statuses':errors,'calls':calls,'body_access_keys':sorted(set(re.findall(r'''\b(?:body|payload|data)\s*(?:\[|\.get\()\s*["']([^"']+)["']''',body))),'raw_request':any(p['annotation']=='Request' for p in params),'docstring':ast.get_docstring(node)})
    return handlers


def generate(root:Path=ROOT):
    manifest=json.loads((root/'docs/api-surface.json').read_text())
    snapshot=json.loads((root/'docs/internal/philo/snapshot.json').read_text())['commit']
    modules={}
    test_paths=sorted((root/'tests').rglob('test_*.py'))
    test_text={str(p.relative_to(root)):p.read_text(errors='replace') for p in test_paths}
    rows=[]
    for route in manifest['routes']:
        path='holdspeak/'+route['module'].replace('.','/')+'.py'
        if not (root/path).is_file():
            path=path[:-3]+'/__init__.py'
        if path not in modules:
            modules[path]=inspect_module(root/path)
        matches=[h for h in modules[path] if h['path']==route['path'] and set(h['methods']) & set(route['methods'])]
        # Literal matching intentionally misses prefix-composed/decorated aliases.
        prefix=route['path'].split('{',1)[0]
        mentions=[p for p,t in test_text.items() if len(prefix)>9 and prefix in t]
        rows.append({**route,'source':path if (root/path).exists() else None,'handler_evidence':matches,'test_candidates':mentions,'test_candidate_meaning':'literal route mentions, not inspected assertion or passing-test evidence','contract_review':{'request_schema':'See handler parameters/body keys and called validators; extraction is incomplete for raw Request and helpers.','response_schema':'Declared annotation/model only; Any/Response and helper results require semantic review.','auth':'Application authentication plus route/service principal checks; inspect calls. Not certified per endpoint.','errors':'Literal/decorator statuses only; helpers/middleware add responses.','side_effects':'Not inferred from method. Consult mapped capability and service.','idempotency':'Not established by this mechanical census.','approval':'Operation-specific; no universal confirmation rule.','boundary':'Transport boundary does not establish downstream data/compute placement.','stability':'Internal application surface unless a linked contract states otherwise.'}})
    counts=Counter(r['module'] for r in rows)
    data={'schema_version':1,'snapshot':snapshot,'route_owner':'scripts/gen_api_surface.py','generator':'scripts/philo_api_reference.py','limits':'Complete membership from committed API manifest; static handler evidence is not full semantic endpoint verification. Test candidates are search leads only.','routes':rows}
    lines=['# API reference','','This reference supplements [API surface](API_SURFACE.md). The existing real-app','generator owns the route roster; this census adds static handler evidence.','It does not invent request/response schemas for raw `Request` handlers.','',f'Source snapshot: `{snapshot}`. **{len(rows)} method/route entries**.','', '**Verification boundary:** inspect the [full endpoint ledger](generated/api-reference.json)', 'and the [declared OpenAPI schemas](generated/openapi.json) for transport models.', 'The ledger records parameters, body-key reads, declared responses, literal errors,', 'service calls, source line, client tags and candidate tests. Candidate tests are', 'text matches, not assertion evidence. Helper validators, middleware, dynamically', 'composed paths and semantic authority/idempotency still require source review.', '', '## Read an endpoint', '', '1. Find its method and route in the ledger or existing API surface.', '2. Open the defining source and handler evidence. Follow raw-body validators.', '3. Follow service calls into authority, dispatch, persistence and receipt.', '4. Match the operation to the capability registry and inspect test assertions.', '5. Run the scoped tests with isolated HOME; record the actual result.', '', 'The hub transport, owner/principal checks, proposal decisions and kernel', 'execution authority are distinct. A POST can be a preview; a GET is not by', 'itself proof of safe information disclosure. See [Authority](AUTHORITY_MODEL.md)', 'and [Security](SECURITY_MODEL.md). The browser uses `web/src/lib/api.ts` and', 'the shared RuntimeBus. Companion client tags come from the existing generator.', '', '## Route groups', '', '| Defining module | Entries |', '| --- | ---: |']
    lines += [f'| `{m}` | {n} |' for m,n in sorted(counts.items())]
    lines += ['', '## Regenerate and check', '', 'Run the existing `scripts/gen_api_surface.py` when routes or client calls change,', 'then `python scripts/philo_api_reference.py`. Use `--check` to detect ledger drift.', 'The existing `tests/unit/test_api_surface.py` compares membership with the real', 'assembled application. This supplementary ledger must not replace that check.', '', 'No OpenAPI field is treated as a complete contract when the handler parses its', 'own request. The unresolved semantic fields are visible in every endpoint row', 'and count as coverage gaps, rather than receiving a default “approved” value.', '']
    return {'docs/generated/api-reference.json':json.dumps(data,indent=2,ensure_ascii=False)+'\n','docs/API_REFERENCE.md':'\n'.join(lines)}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    bad=[]
    for rel,text in generate().items():
        path=ROOT/rel
        if args.check:
            if not path.exists() or path.read_text()!=text: bad.append(rel)
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    if bad: raise SystemExit('API reference drift: '+', '.join(bad))
    print('API reference '+('checked' if args.check else 'generated'))

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Export OpenAPI through the canonical API census assembly, with no live DB."""
import argparse
import json
from pathlib import Path
from gen_api_surface import build_reference_app
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    schema=build_reference_app().openapi()
    schema['info']['x-philo-note']='Declared FastAPI schemas only; raw Request validation, authorization and WS contracts are not fully represented. Do not infer approval from OpenAPI.'
    schema['info']['x-source-snapshot']=json.loads((ROOT/'docs/internal/philo/snapshot.json').read_text())['commit']
    text=json.dumps(schema,indent=2,sort_keys=True)+'\n';out=ROOT/'docs/generated/openapi.json'
    if a.check:
        if not out.exists() or out.read_text()!=text:raise SystemExit('OpenAPI drift')
    else:out.write_text(text)
    print(f'OpenAPI: {len(schema["paths"])} paths')
if __name__=='__main__':main()

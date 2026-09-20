#!/usr/bin/env python3
"""Extract doctor checks and their result branches without probing a machine."""
from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def extract(path:Path):
    text=path.read_text();tree=ast.parse(text);rows=[]
    for fn in tree.body:
        if not isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef)) or not (fn.name.startswith('_check_') or fn.name=='check_observer'):continue
        outcomes=[]
        for node in ast.walk(fn):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in {'DoctorCheck','DoctorResult'}:
                outcomes.append({'line':node.lineno,'constructor':node.func.id,'args':[ast.unparse(a) for a in node.args],'fields':{k.arg:ast.unparse(k.value) for k in node.keywords if k.arg}})
        rows.append({'path':str(path.relative_to(ROOT)),'symbol':fn.name,'line':fn.lineno,'condition_source':ast.get_source_segment(text,fn),'outcomes':outcomes})
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    rows=extract(ROOT/'holdspeak/commands/doctor.py')+extract(ROOT/'holdspeak/doctor.py')
    obj={'snapshot':json.loads((ROOT/'docs/internal/philo/snapshot.json').read_text())['commit'],'generator':'scripts/philo_doctor_reference.py','limits':'Static branches, not executed checks. Runtime status, platform applicability and dynamic repair interpolation depend on the condition_source. Some helpers supply additional results.','checks':rows}
    text=json.dumps(obj,indent=2)+'\n';out=ROOT/'docs/generated/doctor-checks.json'
    if args.check:
        if not out.exists() or out.read_text()!=text:raise SystemExit('doctor reference drift')
    else:out.write_text(text)
    print(f'Doctor reference: {len(rows)} check functions')
if __name__=='__main__':main()

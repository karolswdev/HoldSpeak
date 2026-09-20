#!/usr/bin/env python3
"""Find boundary review candidates without executing product code.

This is a deliberately conservative lexical census. A hit is not an egress
claim; a miss does not prove the absence of dynamic or native effects.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
'http_client':r'\b(?:requests|httpx|aiohttp|urllib\.request)\b|\b(?:fetch|apiFetch|apiRequest|apiBlob|URLSession)\s*\(',
'websocket':r'\b(?:WebSocket|websockets|websocket_connect)\b',
'process_or_shell':r'\b(?:subprocess|Popen|create_subprocess_exec|create_subprocess_shell|os\.system|NSTask)\b|\bProcess\s*\(',
'url_or_application':r'\b(?:webbrowser|openURL|openUrl|NSWorkspace|osascript|xdg-open)\b',
'input_injection':r'\b(?:pyperclip|pynput|CGEventPost|keyboard\.type|keyboard\.press|paste_text|type_text)\b',
'credential_store':r'\b(?:keyring|SecItemAdd|SecItemCopyMatching|secret_store|write_secret|read_secret)\b',
'model_transport':r'\b(?:OpenAI|AsyncOpenAI|Anthropic|chat\.completions|mesh_relay)\b',
}


def collect(root=ROOT):
    tree=json.loads((root/'docs/generated/repository-tree.json').read_text())
    # The census artifact is an object with the classified files as `files`.
    paths=tree['files'] if isinstance(tree,dict) else tree
    rows=[]
    for entry in paths:
        rel=entry['path'];p=root/rel
        if not rel.startswith(('holdspeak/','web/src/','apple/','aipi-lite/','extensions/')) or p.suffix not in {'.py','.ts','.tsx','.js','.swift','.cpp','.h','.yaml'} or not p.is_file():continue
        for line,text in enumerate(p.read_text(errors='replace').splitlines(),1):
            kinds=[k for k,pattern in PATTERNS.items() if re.search(pattern,text)]
            if kinds:
                rows.append({'path':rel,'line':line,'kinds':kinds,'excerpt':text.strip()[:260],'line_sha256':hashlib.sha256(text.encode()).hexdigest(),'review':'candidate_only'})
    return {'schema_version':1,'snapshot':json.loads((root/'docs/internal/philo/snapshot.json').read_text())['commit'],'scope':'tracked implementation files in the snapshot census baseline, read from the current working tree at generation','limitations':['Lexical candidates include imports, comments and fixtures.','Aliases, dynamic calls and native indirect effects can be missed.','This does not certify authority, egress, privacy or complete security coverage.'],'candidates':rows}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    out=ROOT/'docs/generated/boundary-candidates.json';text=json.dumps(collect(),indent=2,ensure_ascii=False)+'\n'
    if args.check:
        if not out.exists() or out.read_text()!=text:raise SystemExit('boundary census drift')
    else:out.write_text(text)
    print('Boundary candidate census '+('checked' if args.check else 'generated'))
if __name__=='__main__':main()
